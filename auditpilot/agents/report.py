"""
Audit Reporting and Partner Sign-Off Agent for AuditPilot.
Synthesizes the comprehensive 7-section formal Audit Memorandum, writes docs/audit_memo.md,
and coordinates human-in-the-loop partner review and sign-off.
"""

import json
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.genai import types

from auditpilot.models import get_gemini_model
from auditpilot.tools.report_tools import sign_off_memo, write_audit_memo

DEFAULT_MODEL = get_gemini_model()


def report_pipeline_guard(callback_context: CallbackContext) -> types.Content | None:
    """Pre-execution guard for report_agent: halts cleanly if data intake failed."""
    data_profile = callback_context.state.get("data_profile")
    if not data_profile:
        return None

    status = (
        data_profile.get("status")
        if isinstance(data_profile, dict)
        else getattr(data_profile, "status", None)
    )

    if status == "FAILED":
        diagnostic_text = (
            "AUDIT PIPELINE HALTED: Data intake validation failed.\n"
            "An audit memorandum cannot be issued on invalid or corrupted datasets."
        )
        return types.Content(
            role="model",
            parts=[types.Part.from_text(text=diagnostic_text)],
        )

    return None


def sync_report_state(callback_context: CallbackContext) -> None:
    """Post-agent callback tracking audit memorandum draft and sign-off lifecycle."""
    state = callback_context.state
    # Check if sign-off was completed
    if state.get("audit_memo_status") != "FINAL":
        # If docs/audit_memo.md exists and has Status: FINAL, update state
        try:
            with open("docs/audit_memo.md", "r", encoding="utf-8") as f:
                content = f.read()
            if "Status: FINAL" in content:
                state["audit_memo_status"] = "FINAL"
            elif "Status: DRAFT" in content:
                state["audit_memo_status"] = "DRAFT"
        except Exception:
            pass


def report_instruction_provider(ctx: ReadonlyContext) -> str:
    """Dynamic instruction provider safely assembling all audit data for report synthesis."""
    dp = ctx.state.get("data_profile", {})
    confirmed = (
        ctx.state.get("confirmed_findings")
        or ctx.state.get("reviewed_findings", {}).get("confirmed_findings")
        or [f for f in ctx.state.get("ranked_findings", {}).get("findings", []) if f.get("status") == "confirmed"]
    )
    dropped = (
        ctx.state.get("dropped_findings")
        or ctx.state.get("reviewed_findings", {}).get("dropped_findings")
        or [f for f in ctx.state.get("ranked_findings", {}).get("findings", []) if f.get("status") == "dropped"]
    )
    ranked = ctx.state.get("ranked_findings", {}).get("findings", [])
    memo_status = ctx.state.get("audit_memo_status", "NOT_STARTED")

    dp_json = json.dumps(dp, indent=2) if dp else "{}"
    confirmed_json = json.dumps(confirmed, indent=2) if confirmed else "[]"
    dropped_json = json.dumps(dropped, indent=2) if dropped else "[]"
    ranked_json = json.dumps(ranked, indent=2) if ranked else "[]"

    return f"""You are the Senior Audit Engagement Partner and Lead Reporting Officer for Sahyadri Precision Components Pvt. Ltd.
Your role is to author the definitive, authoritative Audit Memorandum in `docs/audit_memo.md` and manage the human-in-the-loop audit partner sign-off workflow.

You have access to the verified engagement data:
- Data Profile & Reconciliation: {dp_json}
- Confirmed Findings (for Section 3): {confirmed_json}
- Dropped Findings (for Section 6 Appendix): {dropped_json}
- Master Ranked Findings: {ranked_json}
- Current Audit Memo Status: {memo_status}

You have access to two tools:
1. `write_audit_memo(markdown_content, status)`: Writes the formatted audit memorandum to `docs/audit_memo.md`. Status must be 'DRAFT' or 'FINAL'.
2. `sign_off_memo(decision, reviewer_name, comments)`: Executes the partner sign-off gate. 'APPROVE' flips status to 'FINAL' and appends the sign-off block. 'REJECT' / 'REQUEST_CHANGES' preserves 'DRAFT'.

OPERATING MODES:

MODE A: DRAFTING THE AUDIT MEMORANDUM (Initial Audit Turn)
If the user requests an audit or the memo has not been drafted yet:
1. Generate the complete, professional markdown memorandum containing ALL 7 required sections:
   ## 1. Scope and Data
   - Entity: Sahyadri Precision Components Pvt. Ltd.
   - Fiscal Period: April 1, 2025 to March 31, 2026.
   - Total Transactions Analyzed: 6,000 entries.
   - General Ledger Turnover: Total Debits INR 17,11,75,194.18 | Total Credits INR 17,11,75,194.18 (Double-entry balanced).
   - Trial Balance Discrepancy: Account 6020 (Repairs & Maintenance - Machinery) displays an unadjusted variance of INR 125,000.00 (citing entry JE-2025-2767).

   ## 2. Executive Summary
   - Narrative of control environment, key financial distress indicators, and consolidated risk exposure.
   - Summary of high-severity breaches: Segregation of Duties self-approvals, employee-vendor bank account overlap, and near-threshold payment structuring.

   ## 3. Ranked Findings (Confirmed)
   - Detail EVERY confirmed finding from session state.
   - Provide a structured table and subsections with exact fields:
     * Finding ID (e.g. FIND-001)
     * Title & Category
     * Cited Entry IDs
     * Exact Amount at Risk (INR)
     * Risk Score (Likelihood x Impact)
     * Factual evidence from tool outputs and corporate policy clauses (Clause 3.1, Clause 3.2, Clause 4.2, etc.).

   ## 4. Recommended Actions for Management
   - Immediate internal control remediation measures:
     * Implement strict ERP maker-checker validation blocking self-approved journal vouchers.
     * Enforce automated pre-disbursement cross-matching between employee bank accounts and vendor master files.
     * Establish rolling 48-hour automated threshold monitoring for commercial vendor payments.
     * Post adjusting journal entry to eliminate the INR 125,000 variance in Account 6020.

   ## 5. Limitations
   - Analysis performed on available electronic ledger datasets and financial schedules.
   - Scope excludes physical inventory verification and external banking circularization.

   ## 6. Appendix: Dropped Findings and Reasons
   - Transparently list EVERY dropped finding from session state in a table:
     * Finding ID
     * Category & Title
     * Cited Entry IDs (including any non-existent IDs like JE-9999-9999)
     * One-line Review Note / Justification for Dropping.

   ## 7. Partner Sign-Off Block
   - Include the initial pending sign-off table indicating Status: DRAFT (Pending Partner Review).

2. Call `write_audit_memo(markdown_content=..., status="DRAFT")`.
3. In your response to the user, present an executive summary of the memorandum and explicitly prompt the partner:
   "Audit Memorandum drafted successfully and saved to docs/audit_memo.md (Status: DRAFT).
   Please review the memorandum and reply with:
   - 'APPROVE' to finalize and sign off on the audit report.
   - 'REQUEST_CHANGES' with comments to request revisions.
   - 'REJECT' with justification to reject."

MODE B: PARTNER SIGN-OFF GATE (When user responds with sign-off decision)
If the user's message contains 'APPROVE', 'REJECT', or 'REQUEST_CHANGES':
1. Invoke `sign_off_memo(decision=decision, reviewer_name="Audit Partner", comments=user_comments)`.
2. Confirm the resulting status to the user.

STRICT NUMERICAL FIDELITY CONSTRAINT:
- You may ONLY use numerical values (INR amounts, entry counts, dates, entry IDs) present in session state and tool outputs.
- NEVER invent, estimate, or hallucinate figures.
"""


report_agent = LlmAgent(
    name="report_agent",
    description="Synthesizes the comprehensive 7-section Audit Memorandum, writes docs/audit_memo.md, and coordinates human-in-the-loop partner sign-off.",
    model=DEFAULT_MODEL,
    instruction=report_instruction_provider,
    tools=[write_audit_memo, sign_off_memo],
    output_key="audit_memo_output",
    before_agent_callback=report_pipeline_guard,
    after_agent_callback=sync_report_state,
)
