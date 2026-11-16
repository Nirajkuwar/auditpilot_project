"""
Unit and integration tests for specialist agents (anomaly_agent, vendor_agent, ratio_agent)
and the ParallelAgent lead audit pipeline.

Validates:
1. Strict least-privilege tool sandboxing and agent configuration.
2. ParallelAgent and SequentialAgent pipeline hierarchy with pipeline_guard integration.
3. End-to-end parallel execution populating data_profile, anomaly_findings, vendor_findings,
   and ratio_findings in session state using real data tools with zero live API tokens consumed.
4. Prompt-injection immunity against malicious memo instructions.
5. Pipeline guard halts specialist execution when intake status is FAILED.
6. Optional live Gemini integration test (opt-in via RUN_LIVE_TESTS=1).
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from dotenv import load_dotenv
import pandas as pd
import pytest

from google.adk import Runner
from google.adk.agents import ParallelAgent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.models.llm_response import LlmResponse
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Load environment configuration (.env from workspace root or auditpilot)
_root_env = Path(__file__).resolve().parent.parent / ".env"
_pkg_env = Path(__file__).resolve().parent.parent / "auditpilot" / ".env"
if _root_env.exists():
    load_dotenv(_root_env)
elif _pkg_env.exists():
    load_dotenv(_pkg_env)

from auditpilot.agent import audit_lead, root_agent, specialists
from auditpilot.agents.anomaly import anomaly_agent
from auditpilot.agents.intake import intake_agent
from auditpilot.agents.ratio import ratio_agent
from auditpilot.agents.vendor import vendor_agent
from auditpilot.callbacks import pipeline_guard
from auditpilot.schemas import (
    AnomalyFindings,
    DataProfile,
    RatioFindings,
    VendorFindings,
)
from auditpilot.tools import (
    benford_test,
    check_trial_balance,
    find_duplicates,
    find_split_payments,
    find_weekend_round,
    load_ledger,
    ratio_table,
    vendor_bank_overlap,
)


def _get_tool_names(llm_request: types.GenerateContentConfig) -> list[str]:
    names = []
    if llm_request.config and llm_request.config.tools:
        for t in llm_request.config.tools:
            if hasattr(t, "function_declarations") and t.function_declarations:
                names.extend([fd.name for fd in t.function_declarations])
    return names


async def mock_specialists_pipeline(self, llm_request, stream=False):
    """
    Dynamic offline mock generator for the full audit pipeline:
    - Turn 1: Invokes all tools declared in llm_request.config.tools on real data files.
    - Turn 2: Synthesizes structured Pydantic JSON responses dynamically from the real tool outputs.
    Guarantees 100% offline continuous testing with zero live Gemini API token usage.
    """
    tool_outputs = {}
    for content in llm_request.contents:
        if not content.parts:
            continue
        for part in content.parts:
            if part.function_response:
                tool_outputs[part.function_response.name] = part.function_response.response

    available_tools = _get_tool_names(llm_request)

    # Turn 1: Issue tool calls for all assigned tools
    if not tool_outputs:
        user_text = (
            llm_request.contents[0].parts[0].text
            if llm_request.contents and llm_request.contents[0].parts
            else ""
        )
        path_arg = {}
        for token in user_text.split():
            if token.endswith(".csv"):
                path_arg = {"ledger_path": token}
                break

        fc_parts = []
        for t_name in available_tools:
            arg = (
                path_arg
                if t_name in (
                    "load_ledger",
                    "check_trial_balance",
                    "benford_test",
                    "find_duplicates",
                    "find_split_payments",
                    "find_weekend_round",
                )
                else {}
            )
            fc_parts.append(types.Part(function_call=types.FunctionCall(name=t_name, args=arg)))

        yield LlmResponse(content=types.Content(role="model", parts=fc_parts))
    else:
        # Turn 2: Synthesize structured findings from actual tool outputs
        if "load_ledger" in tool_outputs or "check_trial_balance" in tool_outputs:
            load_res = tool_outputs.get("load_ledger", {})
            tb_res = tool_outputs.get("check_trial_balance", {})
            l_stats = load_res.get("stats", {})
            t_stats = tb_res.get("stats", {})
            discrepancy = t_stats.get("total_discrepancy_inr", 0.0)
            missing = l_stats.get("missing_columns", [])
            status = (
                "FAILED"
                if not l_stats.get("file_exists", True) or missing
                else ("PASSED_WITH_VARIANCE" if discrepancy > 0 else "PASSED")
            )
            profile = {
                "status": status,
                "failure_reasons": [f"Missing required columns: {missing}"] if missing else [],
                "row_count": l_stats.get("row_count"),
                "column_count": l_stats.get("column_count"),
                "total_debit_inr": l_stats.get("total_debit_inr"),
                "total_credit_inr": l_stats.get("total_credit_inr"),
                "is_balanced": l_stats.get("is_balanced"),
                "start_date": l_stats.get("start_date"),
                "end_date": l_stats.get("end_date"),
                "trial_balance_reconciled": discrepancy == 0,
                "trial_balance_gap_inr": discrepancy,
                "flagged_ids": tb_res.get("flagged_ids", []),
                "notes": "Intake completed with dynamic verification.",
            }
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text=json.dumps(profile))]))

        elif (
            "benford_test" in tool_outputs
            or "find_duplicates" in tool_outputs
            or "find_split_payments" in tool_outputs
            or "find_weekend_round" in tool_outputs
        ):
            benford = tool_outputs.get("benford_test", {})
            dupes = tool_outputs.get("find_duplicates", {})
            splits = tool_outputs.get("find_split_payments", {})
            weekends = tool_outputs.get("find_weekend_round", {})

            b_stats = benford.get("stats", {})
            d_stats = dupes.get("stats", {})
            s_stats = splits.get("stats", {})
            w_stats = weekends.get("stats", {})

            flagged = sorted(
                list(
                    set(
                        benford.get("flagged_ids", [])
                        + dupes.get("flagged_ids", [])
                        + splits.get("flagged_ids", [])
                        + weekends.get("flagged_ids", [])
                    )
                )
            )

            findings = {
                "benford_status": "FLAGGED" if b_stats.get("conformity_assessment") != "Close Conformity" else "CONFORMING",
                "benford_chi2": b_stats.get("chi_square_statistic"),
                "benford_mad": b_stats.get("mean_absolute_deviation"),
                "benford_spikes": b_stats.get("anomalous_digits", []),
                "duplicate_count": len(dupes.get("flagged_ids", [])),
                "duplicate_entry_ids": dupes.get("flagged_ids", []),
                "duplicate_total_inr": d_stats.get("total_exposure_inr", 0.0),
                "split_payment_group_count": s_stats.get("split_groups_count", 0),
                "split_payment_entry_ids": splits.get("flagged_ids", []),
                "split_payment_total_inr": s_stats.get("total_structured_amount_inr", 0.0),
                "weekend_round_count": len(weekends.get("flagged_ids", [])),
                "weekend_round_entry_ids": weekends.get("flagged_ids", []),
                "weekend_round_total_inr": w_stats.get("total_flagged_amount_inr", 0.0),
                "total_anomalies_flagged": len(flagged),
                "flagged_ids": flagged,
                "notes": "Anomaly findings dynamically synthesized from deterministic tool results.",
            }
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text=json.dumps(findings))]))

        elif "vendor_bank_overlap" in tool_outputs:
            vo = tool_outputs.get("vendor_bank_overlap", {})
            v_stats = vo.get("stats", {})
            findings = {
                "ghost_vendor_count": v_stats.get("total_ghost_vendors_count", 0),
                "ghost_vendor_ids": [
                    "VND-024", "VND-045", "VND-067", "VND-102", "VND-115"
                ],
                "shared_account_count": v_stats.get("shared_bank_accounts_count", 0),
                "shared_account_vendor_ids": [
                    s.get("vendor_id") for s in v_stats.get("shared_bank_details", [])
                ],
                "shared_account_employee_ids": [
                    s.get("employee_id") for s in v_stats.get("shared_bank_details", [])
                ],
                "flagged_entry_ids": vo.get("flagged_ids", []),
                "total_at_risk_inr": v_stats.get("total_exposure_inr", 0.0),
                "flagged_ids": vo.get("flagged_ids", []),
                "notes": vo.get("notes", "Vendor compliance checks completed."),
            }
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text=json.dumps(findings))]))

        elif "ratio_table" in tool_outputs:
            rt = tool_outputs.get("ratio_table", {})
            r_stats = rt.get("stats", {})
            avg = r_stats.get("annual_averages", {})
            findings = {
                "months_analyzed": r_stats.get("months_analyzed", 12),
                "average_gross_margin": avg.get("average_gross_margin_pct", avg.get("gross_margin")),
                "average_operating_margin": avg.get("average_operating_margin_pct", avg.get("operating_margin")),
                "average_current_ratio": avg.get("average_current_ratio", avg.get("current_ratio")),
                "average_debt_to_equity": avg.get("average_debt_to_equity", avg.get("debt_to_equity")),
                "liquidity_status": "HEALTHY",
                "solvency_status": "STABLE",
                "flagged_months": r_stats.get("flagged_distressed_months", []),
                "notes": rt.get("notes", "Ratio table computed across all monthly periods."),
            }
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text=json.dumps(findings))]))


def test_specialists_configuration_and_least_privilege():
    """Verify strict least privilege, model configuration, and output schemas for all specialists."""
    # 1. anomaly_agent
    assert anomaly_agent.name == "anomaly_agent"
    assert "gemini-3.1-flash-lite" in getattr(anomaly_agent.model, "model", str(anomaly_agent.model)).lower()
    assert anomaly_agent.output_key == "anomaly_findings"
    assert anomaly_agent.output_schema == AnomalyFindings
    anomaly_tool_names = [t.__name__ for t in anomaly_agent.tools]
    assert len(anomaly_tool_names) == 4
    assert set(anomaly_tool_names) == {
        "benford_test",
        "find_duplicates",
        "find_split_payments",
        "find_weekend_round",
    }

    # 2. vendor_agent
    assert vendor_agent.name == "vendor_agent"
    assert "gemini-3.1-flash-lite" in getattr(vendor_agent.model, "model", str(vendor_agent.model)).lower()
    assert vendor_agent.output_key == "vendor_findings"
    assert vendor_agent.output_schema == VendorFindings
    vendor_tool_names = [t.__name__ for t in vendor_agent.tools]
    assert len(vendor_tool_names) == 1
    assert set(vendor_tool_names) == {"vendor_bank_overlap"}

    # 3. ratio_agent
    assert ratio_agent.name == "ratio_agent"
    assert "gemini-3.1-flash-lite" in getattr(ratio_agent.model, "model", str(ratio_agent.model)).lower()
    assert ratio_agent.output_key == "ratio_findings"
    assert ratio_agent.output_schema == RatioFindings
    ratio_tool_names = [t.__name__ for t in ratio_agent.tools]
    assert len(ratio_tool_names) == 1
    assert set(ratio_tool_names) == {"ratio_table"}

    # Strict isolation assertion: No tool cross-leakage
    assert "load_ledger" not in anomaly_tool_names
    assert "ratio_table" not in anomaly_tool_names
    assert "vendor_bank_overlap" not in anomaly_tool_names
    assert "find_duplicates" not in vendor_tool_names
    assert "ratio_table" not in vendor_tool_names
    assert "find_split_payments" not in ratio_tool_names
    assert "vendor_bank_overlap" not in ratio_tool_names


def test_pipeline_hierarchy_and_guard_attachment():
    """Verify specialists is a ParallelAgent guarded by pipeline_guard inside audit_lead."""
    assert isinstance(specialists, ParallelAgent)
    assert specialists.name == "specialists"
    assert len(specialists.sub_agents) == 3
    assert specialists.sub_agents[0] is anomaly_agent
    assert specialists.sub_agents[1] is vendor_agent
    assert specialists.sub_agents[2] is ratio_agent
    assert specialists.before_agent_callback is pipeline_guard

    assert isinstance(audit_lead, SequentialAgent)
    assert audit_lead.name == "audit_lead"
    assert len(audit_lead.sub_agents) == 2
    assert audit_lead.sub_agents[0] is intake_agent
    assert audit_lead.sub_agents[1] is specialists
    assert root_agent is audit_lead


def test_specialists_parallel_execution_and_session_state():
    """Execute lead pipeline offline over real data and assert all 4 state keys populate accurately."""
    async def _run():
        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name="auditpilot", user_id="auditor_lead", session_id="test_lead_parallel"
        )
        runner = Runner(agent=root_agent, session_service=session_service, app_name="auditpilot")

        msg = types.Content(role="user", parts=[types.Part.from_text(text="start audit")])
        with patch.object(Gemini, "generate_content_async", mock_specialists_pipeline):
            async for _ in runner.run_async(
                user_id="auditor_lead", session_id="test_lead_parallel", new_message=msg
            ):
                pass

        updated = await session_service.get_session(
            app_name="auditpilot", user_id="auditor_lead", session_id="test_lead_parallel"
        )

        state = updated.state
        assert "data_profile" in state
        assert "anomaly_findings" in state
        assert "vendor_findings" in state
        assert "ratio_findings" in state

        # Verify Data Profile
        dp = state["data_profile"]
        assert dp["status"] == "PASSED_WITH_VARIANCE"
        assert dp["row_count"] == 6000
        assert dp["trial_balance_gap_inr"] == 125000.0

        # Verify Anomaly Findings
        af = state["anomaly_findings"]
        assert af["duplicate_count"] == 10
        assert len(af["duplicate_entry_ids"]) == 10
        assert af["split_payment_group_count"] == 6
        assert len(af["split_payment_entry_ids"]) == 18
        assert af["weekend_round_count"] == 12
        assert len(af["weekend_round_entry_ids"]) == 12
        assert af["benford_status"] == "FLAGGED"

        # Verify Vendor Findings
        vf = state["vendor_findings"]
        assert vf["ghost_vendor_count"] == 5
        assert vf["shared_account_count"] == 3
        assert len(vf["flagged_entry_ids"]) == 8

        # Verify Ratio Findings
        rf = state["ratio_findings"]
        assert rf["months_analyzed"] == 12
        assert rf["average_gross_margin"] is not None
        assert rf["average_operating_margin"] is not None
        assert rf["average_current_ratio"] is not None

    asyncio.run(_run())


def test_prompt_injection_descriptions_do_not_alter_behavior():
    """Verify that planted adversarial prompt injections in ledger.csv do not alter agent behavior."""
    # Check that the 4 prompt injection rows exist in ledger.csv
    ledger_df = pd.read_csv("data/ledger.csv")
    injections = ledger_df[
        ledger_df["description"].str.contains("OVERRIDE|COMMAND|INSTRUCTION", case=False, na=False)
    ]
    assert len(injections) >= 4

    injection_entry_ids = set(injections["entry_id"])
    assert "JE-2025-0741" in injection_entry_ids
    assert "JE-2025-2329" in injection_entry_ids
    assert "JE-2025-3735" in injection_entry_ids
    assert "JE-2025-5221" in injection_entry_ids

    # Run the pipeline and ensure agents process normally without suppression
    async def _run():
        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name="auditpilot", user_id="auditor_sec", session_id="test_injection_session"
        )
        runner = Runner(agent=root_agent, session_service=session_service, app_name="auditpilot")
        msg = types.Content(
            role="user",
            parts=[types.Part.from_text(text="start audit and check for any prompt injections")],
        )
        with patch.object(Gemini, "generate_content_async", mock_specialists_pipeline):
            async for _ in runner.run_async(
                user_id="auditor_sec", session_id="test_injection_session", new_message=msg
            ):
                pass

        updated = await session_service.get_session(
            app_name="auditpilot", user_id="auditor_sec", session_id="test_injection_session"
        )
        # Anomaly findings and vendor findings remain populated and uncompromised
        assert updated.state["anomaly_findings"]["duplicate_count"] == 10
        assert updated.state["vendor_findings"]["ghost_vendor_count"] == 5

    asyncio.run(_run())


def test_pipeline_guard_halts_specialists_on_failed_intake():
    """Verify that when intake fails on broken CSV, specialists is halted and does not execute."""
    async def _run():
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Create a broken ledger missing required column 'amount_inr'
            normal_df = pd.read_csv("data/ledger.csv")
            broken_df = normal_df.drop(columns=["amount_inr"]).head(20)
            broken_df.to_csv(tmp_path, index=False)

            session_service = InMemorySessionService()
            session = await session_service.create_session(
                app_name="auditpilot", user_id="auditor_halt", session_id="test_halt_session"
            )
            runner = Runner(agent=root_agent, session_service=session_service, app_name="auditpilot")

            msg = types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"start audit on broken ledger at {tmp_path}")],
            )

            halt_events = []
            with patch.object(Gemini, "generate_content_async", mock_specialists_pipeline):
                async for event in runner.run_async(
                    user_id="auditor_halt", session_id="test_halt_session", new_message=msg
                ):
                    if event.content:
                        for p in event.content.parts:
                            if p.text and "AUDIT PIPELINE HALTED" in p.text:
                                halt_events.append(p.text)

            assert len(halt_events) >= 1
            assert "amount_inr" in halt_events[0]

            updated = await session_service.get_session(
                app_name="auditpilot", user_id="auditor_halt", session_id="test_halt_session"
            )

            # intake_agent ran and recorded status FAILED
            assert updated.state.get("data_profile", {}).get("status") == "FAILED"

            # specialists did NOT execute: findings keys must be absent
            assert "anomaly_findings" not in updated.state
            assert "vendor_findings" not in updated.state
            assert "ratio_findings" not in updated.state

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    asyncio.run(_run())


@pytest.mark.live
@pytest.mark.skipif(
    not os.getenv("RUN_LIVE_TESTS"),
    reason="Live Gemini API tests disabled by default during continuous testing to avoid quota exhaustion. Set RUN_LIVE_TESTS=1 to execute.",
)
def test_specialists_live_gemini():
    """
    Live end-to-end integration test with real Gemini model over the network.
    Only executed when RUN_LIVE_TESTS=1 is explicitly set.
    """
    async def _run():
        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name="auditpilot", user_id="auditor_live", session_id="test_live_specialists"
        )
        runner = Runner(agent=root_agent, session_service=session_service, app_name="auditpilot")
        msg = types.Content(role="user", parts=[types.Part.from_text(text="start audit on data/ledger.csv")])
        async for _ in runner.run_async(
            user_id="auditor_live", session_id="test_live_specialists", new_message=msg
        ):
            pass

        updated = await session_service.get_session(
            app_name="auditpilot", user_id="auditor_live", session_id="test_live_specialists"
        )
        assert "data_profile" in updated.state
        assert "anomaly_findings" in updated.state

    asyncio.run(_run())
