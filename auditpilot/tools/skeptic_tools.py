"""
Skeptic and Verification Tools for AuditPilot.
Provides deterministic ledger/financial record existence verification and
loop escalation controls for adversarial skeptic review.
"""

from pathlib import Path
from typing import Any
import pandas as pd
from google.adk.tools import ToolContext


def verify_entry_ids(
    entry_ids: list[str],
    ledger_path: str = "data/ledger.csv",
    tb_path: str = "data/trial_balance.csv",
    fin_path: str = "data/financials.csv",
) -> dict[str, Any]:
    """Deterministically verify whether cited identifiers exist in audit datasets.

    Validates every identifier against:
    1. General Ledger transaction entries (entry_id in ledger.csv)
    2. Trial Balance account codes (account_code in trial_balance.csv, e.g. '6020' or 'Account 6020')
    3. Monthly Financial statements (month in financials.csv, e.g. '2025-11')
    4. Recognized ledger-wide aggregate identifiers (e.g. 'ALL-GL-2025', 'GL-ALL', 'LEDGER')

    Any ID not located across these datasets is flagged as invalid.

    Args:
        entry_ids: List of identifier strings cited by an audit finding.
        ledger_path: Path to the general ledger CSV file (default: 'data/ledger.csv').
        tb_path: Path to the trial balance CSV file (default: 'data/trial_balance.csv').
        fin_path: Path to the financial statements CSV file (default: 'data/financials.csv').

    Returns:
        A dictionary with keys:
            - test: 'verify_entry_ids'
            - valid_ids: List of confirmed existing identifiers.
            - invalid_ids: List of unverified / nonexistent identifiers.
            - records: List of detailed record dictionaries retrieved for valid identifiers.
            - notes: Summary of the verification outcome.
    """
    # 1. Normalize input list
    if isinstance(entry_ids, str):
        ids_to_check = [e.strip() for e in entry_ids.split(",") if e.strip()]
    elif isinstance(entry_ids, list):
        ids_to_check = [str(e).strip() for e in entry_ids if str(e).strip()]
    else:
        ids_to_check = []

    valid_ids: list[str] = []
    invalid_ids: list[str] = []
    records: list[dict[str, Any]] = []

    # System-wide recognized tags for ledger-wide or macro findings
    SYSTEM_AGGREGATE_TAGS = {"ALL-GL-2025", "GL-ALL", "LEDGER", "ALL", "ALL-GL"}

    # 2. Load Ledger Dataset
    ledger_df = None
    l_path = Path(ledger_path)
    if l_path.exists():
        try:
            ledger_df = pd.read_csv(l_path)
            if "entry_id" in ledger_df.columns:
                ledger_df["entry_id_str"] = ledger_df["entry_id"].astype(str)
                ledger_df = ledger_df.set_index("entry_id_str", drop=False)
            else:
                ledger_df = None
        except Exception:
            ledger_df = None

    # 3. Load Trial Balance Dataset
    tb_df = None
    t_path = Path(tb_path)
    if t_path.exists():
        try:
            tb_df = pd.read_csv(t_path)
            if "account_code" in tb_df.columns:
                tb_df["account_code_str"] = tb_df["account_code"].astype(str)
                tb_df = tb_df.set_index("account_code_str", drop=False)
            else:
                tb_df = None
        except Exception:
            tb_df = None

    # 4. Load Financials Dataset
    fin_df = None
    f_path = Path(fin_path)
    if f_path.exists():
        try:
            fin_df = pd.read_csv(f_path)
            if "month" in fin_df.columns:
                fin_df["month_str"] = fin_df["month"].astype(str)
                fin_df = fin_df.set_index("month_str", drop=False)
            else:
                fin_df = None
        except Exception:
            fin_df = None

    # 5. Check each identifier
    for raw_id in ids_to_check:
        clean_id = raw_id.strip()

        # Check General Ledger
        if ledger_df is not None and clean_id in ledger_df.index:
            row = ledger_df.loc[clean_id]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            valid_ids.append(clean_id)
            records.append({
                "id": clean_id,
                "source": "ledger",
                "date": str(row.get("date", "")),
                "account_code": str(row.get("account_code", "")),
                "account_name": str(row.get("account_name", "")),
                "vendor_id": str(row.get("vendor_id", "")) if pd.notna(row.get("vendor_id")) else None,
                "amount_inr": round(float(row.get("amount_inr", 0.0)), 2),
                "posted_by": str(row.get("posted_by", "")),
                "approved_by": str(row.get("approved_by", "")),
                "description": str(row.get("description", "")),
            })
            continue

        # Check Trial Balance Account Code (supports '6020' or 'Account 6020')
        tb_lookup_id = clean_id.replace("Account", "").replace("account", "").strip()
        if tb_df is not None and tb_lookup_id in tb_df.index:
            tb_row = tb_df.loc[tb_lookup_id]
            if isinstance(tb_row, pd.DataFrame):
                tb_row = tb_row.iloc[0]
            valid_ids.append(clean_id)
            records.append({
                "id": clean_id,
                "source": "trial_balance",
                "account_code": str(tb_row.get("account_code", "")),
                "account_name": str(tb_row.get("account_name", "")),
                "closing_balance": round(float(tb_row.get("closing_balance", 0.0)), 2),
            })
            continue

        # Check Financials Month
        if fin_df is not None and clean_id in fin_df.index:
            fin_row = fin_df.loc[clean_id]
            if isinstance(fin_row, pd.DataFrame):
                fin_row = fin_row.iloc[0]
            valid_ids.append(clean_id)
            records.append({
                "id": clean_id,
                "source": "financials",
                "month": str(fin_row.get("month", "")),
                "revenue_inr": round(float(fin_row.get("revenue_inr", 0.0)), 2),
                "cash_inr": round(float(fin_row.get("cash_inr", 0.0)), 2),
            })
            continue

        # Check System-Wide Aggregate Tag
        if clean_id.upper() in SYSTEM_AGGREGATE_TAGS:
            valid_ids.append(clean_id)
            records.append({
                "id": clean_id,
                "source": "system_aggregate",
                "notes": "General ledger-wide or corporate portfolio aggregate reference.",
            })
            continue

        # Nonexistent Identifier
        invalid_ids.append(clean_id)

    # 6. Generate Forensic Summary
    if not ids_to_check:
        notes = "No entry identifiers provided for verification."
    elif not invalid_ids:
        notes = f"Verified {len(valid_ids)} of {len(ids_to_check)} identifiers successfully. All entries confirmed."
    else:
        notes = (
            f"Verification alert: {len(invalid_ids)} of {len(ids_to_check)} cited identifiers do not exist: "
            f"{invalid_ids}."
        )

    return {
        "test": "verify_entry_ids",
        "valid_ids": valid_ids,
        "invalid_ids": invalid_ids,
        "records": records,
        "notes": notes,
    }


def exit_review(
    tool_context: ToolContext,
    reason: str = "All findings evaluated and verified.",
) -> dict[str, Any]:
    """Signals completion of the skeptic review loop when no findings remain in 'needs_evidence'.

    Call this tool once all findings have been categorized as either 'confirmed' or 'dropped'.
    Sets loop escalation action to break out of the LoopAgent.

    Args:
        tool_context: The ADK tool execution context injected automatically by the runtime.
        reason: Justification for exiting the review loop.

    Returns:
        A dictionary with keys 'status' ('REVIEW_COMPLETED') and 'reason'.
    """
    if tool_context and hasattr(tool_context, "actions") and tool_context.actions:
        tool_context.actions.escalate = True
        tool_context.actions.skip_summarization = True
    return {"status": "REVIEW_COMPLETED", "reason": reason}
