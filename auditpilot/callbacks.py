"""
Lifecycle callbacks and pipeline guards for AuditPilot agents.
"""

from google.adk.agents.callback_context import CallbackContext
from google.genai import types


def pipeline_guard(callback_context: CallbackContext) -> types.Content | None:
    """Pre-execution pipeline guard for downstream audit agents.

    Inspects session state for 'data_profile'. If data intake failed (e.g. missing
    files, unreadable CSVs, or missing required columns), short-circuits downstream
    agent execution and returns an informative diagnostic message.

    Args:
        callback_context: The invocation context containing session state.

    Returns:
        types.Content containing the halt diagnostic if data intake failed,
        or None to permit downstream agent execution.
    """
    data_profile = callback_context.state.get("data_profile")
    if not data_profile:
        return None

    status = (
        data_profile.get("status")
        if isinstance(data_profile, dict)
        else getattr(data_profile, "status", None)
    )

    if status == "FAILED":
        raw_reasons = (
            data_profile.get("failure_reasons", [])
            if isinstance(data_profile, dict)
            else getattr(data_profile, "failure_reasons", [])
        )
        reasons_str = "; ".join(raw_reasons) if raw_reasons else "Data intake validation failed"
        notes = (
            data_profile.get("notes", "")
            if isinstance(data_profile, dict)
            else getattr(data_profile, "notes", "")
        )

        diagnostic_text = (
            f"AUDIT PIPELINE HALTED: Data intake validation failed.\n"
            f"Failure Reasons: {reasons_str}\n"
            f"Notes: {notes}\n"
            f"Downstream audit procedures cannot proceed on invalid or corrupted datasets. "
            f"Please rectify the data files before restarting the audit."
        )

        return types.Content(
            role="model",
            parts=[types.Part.from_text(text=diagnostic_text)],
        )

    return None

