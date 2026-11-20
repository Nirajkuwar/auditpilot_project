"""
Comprehensive test suite for ADK security guardrails, bank account PII masking,
tamper-evident audit_trail.jsonl logging, and prompt-injection resilience.
"""

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import tempfile
import pytest

from google.adk.models.llm_request import LlmRequest
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from auditpilot.agent import ALL_AUDIT_LLM_AGENTS, audit_lead
from auditpilot.callbacks import (
    after_tool_audit_logger,
    before_model_guardrail,
    log_audit_trail_event,
    mask_bank_accounts,
    sanitize_dict_secrets,
)


# ==============================================================================
# 1. Bank Account Masking Unit Tests
# ==============================================================================

def test_mask_bank_accounts_vendor_and_employee():
    """Verify that 14-digit vendor and employee bank accounts are redacted to [REDACTED_ACCOUNT_****XXXX]."""
    text = (
        "Vendor VND-001 bank account is 50200000100291. "
        "Employee EMP-01 account is 91201004567801. "
        "Another account 123456789012345 was credited."
    )
    masked = mask_bank_accounts(text)

    # Raw bank numbers must NOT appear anywhere in the sanitized text
    assert "50200000100291" not in masked
    assert "91201004567801" not in masked
    assert "123456789012345" not in masked

    # Redacted tokens preserving last 4 digits MUST appear
    assert "[REDACTED_ACCOUNT_****0291]" in masked
    assert "[REDACTED_ACCOUNT_****7801]" in masked
    assert "[REDACTED_ACCOUNT_****2345]" in masked


def test_mask_bank_accounts_preserves_legitimate_figures():
    """Ensure financial figures, ledger entry IDs, dates, account codes, and tax IDs are NOT masked."""
    legitimate_text = (
        "Fiscal Period: 2025-04-01 to 2026-03-31. "
        "Entry ID: JE-2025-0855 and JE-2025-2767. "
        "Total Turnover: INR 171175194.18 (Balanced). "
        "Exposure Amount: INR 1507000.00 and gap 125000.0. "
        "Account Code: 6020 Repairs & Maintenance. "
        "Vendor GSTIN: 27CURCB1071D1ZF and PAN: CURCB1071D."
    )
    masked = mask_bank_accounts(legitimate_text)

    # Must remain byte-for-byte identical (no false-positive redaction)
    assert masked == legitimate_text
    assert "171175194.18" in masked
    assert "1507000.00" in masked
    assert "125000.0" in masked
    assert "JE-2025-0855" in masked
    assert "JE-2025-2767" in masked
    assert "6020" in masked
    assert "27CURCB1071D1ZF" in masked
    assert "CURCB1071D" in masked


def test_mask_bank_accounts_empty_and_none():
    """Verify handling of empty or None inputs."""
    assert mask_bank_accounts("") == ""
    assert mask_bank_accounts(None) == ""


# ==============================================================================
# 2. Audit Trail Logging Unit Tests
# ==============================================================================

def test_audit_trail_logging_model_call():
    """Verify log_audit_trail_event records model calls with ISO-8601 timestamp and SHA-256."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_path = os.path.join(tmp_dir, "test_audit_trail.jsonl")

        log_audit_trail_event(
            agent_name="anomaly_agent",
            event_type="model_call",
            tool_name=None,
            args_summary={"turns": 2},
            result_data="Prompt with instructions and context",
            log_path=log_path,
        )

        assert os.path.exists(log_path)
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 1
        record = json.loads(lines[0])

        assert record["agent_name"] == "anomaly_agent"
        assert record["event_type"] == "model_call"
        assert record["tool_name"] == ""
        assert record["args_summary"] == {"turns": 2}

        # Timestamp must be valid ISO-8601
        dt = datetime.fromisoformat(record["timestamp"])
        assert dt is not None

        # SHA-256 must match the hashed result string
        expected_hash = hashlib.sha256("Prompt with instructions and context".encode("utf-8")).hexdigest()
        assert record["result_sha256"] == expected_hash


def test_audit_trail_logging_tool_call():
    """Verify log_audit_trail_event records tool executions with input args and SHA-256 of result."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_path = os.path.join(tmp_dir, "test_audit_trail.jsonl")

        tool_args = {"ledger_path": "data/ledger.csv"}
        tool_result = {"status": "FLAGGED", "duplicate_count": 10}

        log_audit_trail_event(
            agent_name="anomaly_agent",
            event_type="tool_call",
            tool_name="find_duplicates",
            args_summary=tool_args,
            result_data=tool_result,
            log_path=log_path,
        )

        with open(log_path, "r", encoding="utf-8") as f:
            record = json.loads(f.readline())

        assert record["agent_name"] == "anomaly_agent"
        assert record["event_type"] == "tool_call"
        assert record["tool_name"] == "find_duplicates"
        assert record["args_summary"] == tool_args

        # Verify deterministic JSON SHA-256
        expected_bytes = json.dumps(tool_result, sort_keys=True, default=str).encode("utf-8")
        assert record["result_sha256"] == hashlib.sha256(expected_bytes).hexdigest()


def test_audit_trail_never_logs_api_keys_or_secrets():
    """Verify sanitize_dict_secrets redacts API keys, tokens, and passwords from logs."""
    raw_args = {
        "api_key": "AIzaSyD-SecretKey123456",
        "gemini_secret": "super_secret_token",
        "auth_token": "bearer_jwt_xyz",
        "password": "my_password",
        "ledger_path": "data/ledger.csv",
        "nested": {
            "credential_key": "internal_creds",
            "safe_param": 42,
        },
    }

    sanitized = sanitize_dict_secrets(raw_args)

    assert sanitized["api_key"] == "[REDACTED_SECRET]"
    assert sanitized["gemini_secret"] == "[REDACTED_SECRET]"
    assert sanitized["auth_token"] == "[REDACTED_SECRET]"
    assert sanitized["password"] == "[REDACTED_SECRET]"
    assert sanitized["ledger_path"] == "data/ledger.csv"
    assert sanitized["nested"]["credential_key"] == "[REDACTED_SECRET]"
    assert sanitized["nested"]["safe_param"] == 42


# ==============================================================================
# 3. ADK Callback Integration Tests
# ==============================================================================

def test_before_model_guardrail_mutates_request():
    """Verify before_model_guardrail redacts bank accounts directly inside llm_request.contents."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_log = os.path.join(tmp_dir, "audit_trail.jsonl")
        os.environ["AUDIT_TRAIL_LOG_PATH"] = test_log

        try:
            req = LlmRequest(
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(
                                text="Investigate vendor VND-001 with account 50200000100291."
                            )
                        ],
                    )
                ]
            )

            class MockContext:
                agent_name = "vendor_agent"

            ret = before_model_guardrail(MockContext(), req)
            assert ret is None  # Must allow model request to proceed

            # Text part inside request must be redacted
            sanitized_text = req.contents[0].parts[0].text
            assert "50200000100291" not in sanitized_text
            assert "[REDACTED_ACCOUNT_****0291]" in sanitized_text

            # Must have written a model_call event
            assert os.path.exists(test_log)
            with open(test_log, "r", encoding="utf-8") as f:
                entry = json.loads(f.readline())
            assert entry["event_type"] == "model_call"
            assert entry["agent_name"] == "vendor_agent"
        finally:
            os.environ.pop("AUDIT_TRAIL_LOG_PATH", None)


def test_after_tool_audit_logger_hashes_and_preserves_result():
    """Verify after_tool_audit_logger records tool execution and preserves response."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_log = os.path.join(tmp_dir, "audit_trail.jsonl")
        os.environ["AUDIT_TRAIL_LOG_PATH"] = test_log

        try:
            class DummyTool(BaseTool):
                pass

            dummy_tool = DummyTool(name="check_trial_balance", description="Checks trial balance")
            tool_args = {"ledger_path": "data/ledger.csv"}
            tool_response = {
                "test": "check_trial_balance",
                "is_balanced": True,
                "trial_balance_gap_inr": 125000.0,
            }

            class MockToolContext:
                agent_name = "intake_agent"

            ret = after_tool_audit_logger(
                tool=dummy_tool,
                args=tool_args,
                tool_context=MockToolContext(),
                tool_response=tool_response,
            )

            # Must return None to preserve the tool's original dictionary
            assert ret is None

            # Verify log entry
            assert os.path.exists(test_log)
            with open(test_log, "r", encoding="utf-8") as f:
                entry = json.loads(f.readline())
            assert entry["event_type"] == "tool_call"
            assert entry["tool_name"] == "check_trial_balance"
            assert entry["agent_name"] == "intake_agent"
            assert entry["args_summary"] == tool_args
            assert len(entry["result_sha256"]) == 64
        finally:
            os.environ.pop("AUDIT_TRAIL_LOG_PATH", None)


def test_all_agents_have_guardrails_attached():
    """Verify that all 8 LLM agents in the pipeline have security guardrails attached."""
    assert len(ALL_AUDIT_LLM_AGENTS) == 8
    expected_names = {
        "intake_agent",
        "anomaly_agent",
        "vendor_agent",
        "ratio_agent",
        "policy_agent",
        "risk_agent",
        "skeptic_agent",
        "report_agent",
    }
    actual_names = {a.name for a in ALL_AUDIT_LLM_AGENTS}
    assert actual_names == expected_names

    for agent in ALL_AUDIT_LLM_AGENTS:
        assert (
            agent.before_model_callback == before_model_guardrail
        ), f"Agent {agent.name} missing before_model_guardrail"
        assert (
            agent.after_tool_callback == after_tool_audit_logger
        ), f"Agent {agent.name} missing after_tool_audit_logger"
