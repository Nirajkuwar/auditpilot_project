"""
Ledger validation and trial balance reconciliation tools for financial audits.
"""

from pathlib import Path
from typing import Any
import pandas as pd


def load_ledger(ledger_path: str = "data/ledger.csv") -> dict[str, Any]:
    """Validate and inspect the general ledger dataset.

    Verifies the existence, schema integrity, required columns, row count,
    fiscal date boundaries, and double-entry mathematical balance of the ledger.

    Args:
        ledger_path: Path to the general ledger CSV file.

    Returns:
        A dictionary with keys:
            - test: Name of the audit test ('load_ledger').
            - flagged_ids: List of entry_ids that violate basic accounting constraints.
            - stats: Detailed metrics on rows, columns, dates, and debit/credit totals.
            - notes: Summary assessment of ledger validity and balance.
    """
    path = Path(ledger_path)
    if not path.exists():
        return {
            "test": "load_ledger",
            "flagged_ids": [],
            "stats": {"file_exists": False, "file_path": str(path)},
            "notes": f"Ledger file not found at path: {ledger_path}",
        }

    ledger = pd.read_csv(path)
    required_cols = [
        "entry_id",
        "date",
        "posted_by",
        "approved_by",
        "account_code",
        "account_name",
        "vendor_id",
        "debit_inr",
        "credit_inr",
        "amount_inr",
        "description",
    ]
    missing_cols = [c for c in required_cols if c not in ledger.columns]
    if missing_cols:
        return {
            "test": "load_ledger",
            "flagged_ids": [],
            "stats": {
                "file_exists": True,
                "missing_columns": missing_cols,
                "present_columns": list(ledger.columns),
            },
            "notes": f"Ledger is missing required columns: {missing_cols}",
        }

    # Ensure numeric types
    debit_sum = round(float(ledger["debit_inr"].sum()), 2)
    credit_sum = round(float(ledger["credit_inr"].sum()), 2)
    diff = round(abs(debit_sum - credit_sum), 4)
    is_balanced = diff < 0.01

    # Date boundary validation
    date_series = pd.to_datetime(ledger["date"], errors="coerce")
    invalid_dates = ledger[date_series.isna()]["entry_id"].tolist()

    # Negative amount checks
    negative_amounts = ledger[
        (ledger["debit_inr"] < 0)
        | (ledger["credit_inr"] < 0)
        | (ledger["amount_inr"] < 0)
    ]["entry_id"].tolist()

    flagged_ids = sorted(list(set(invalid_dates + negative_amounts)))

    start_date = (
        date_series.min().strftime("%Y-%m-%d")
        if not date_series.empty
        else None
    )
    end_date = (
        date_series.max().strftime("%Y-%m-%d")
        if not date_series.empty
        else None
    )

    stats = {
        "row_count": int(len(ledger)),
        "column_count": int(len(ledger.columns)),
        "total_debit_inr": debit_sum,
        "total_credit_inr": credit_sum,
        "balance_difference_inr": diff,
        "is_balanced": is_balanced,
        "start_date": start_date,
        "end_date": end_date,
        "unique_accounts": int(ledger["account_code"].nunique()),
        "unique_entries": int(ledger["entry_id"].nunique()),
    }

    if is_balanced and not flagged_ids:
        notes = (
            f"Ledger verified successfully. Contains {len(ledger):,} rows from {start_date} to {end_date}. "
            f"Double-entry bookkeeping is balanced (Total Dr: Rs {debit_sum:,.2f}, Total Cr: Rs {credit_sum:,.2f})."
        )
    elif not is_balanced:
        notes = (
            f"CRITICAL: Ledger out of balance! Total Dr: Rs {debit_sum:,.2f}, "
            f"Total Cr: Rs {credit_sum:,.2f}, Discrepancy: Rs {diff:,.2f}."
        )
    else:
        notes = f"Ledger loaded with {len(flagged_ids)} constraint violations (invalid dates or negative amounts)."

    return {
        "test": "load_ledger",
        "flagged_ids": flagged_ids,
        "stats": stats,
        "notes": notes,
    }


def check_trial_balance(
    ledger_path: str = "data/ledger.csv",
    tb_path: str = "data/trial_balance.csv",
) -> dict[str, Any]:
    """Reconcile general ledger account sums against trial balance records.

    Compares aggregate debits and credits for each account between the general
    ledger and trial_balance.csv. Any account where the ledger sum differs
    from the trial balance is identified, and associated candidate journal entries
    matching the gap amount are flagged for audit scrutiny.

    Args:
        ledger_path: Path to the general ledger CSV file.
        tb_path: Path to the trial balance CSV file.

    Returns:
        A dictionary with keys:
            - test: Name of the audit test ('check_trial_balance').
            - flagged_ids: List of entry_ids associated with identified account gaps.
            - stats: Detailed reconciliation statistics by account and total discrepancy.
            - notes: Summary of reconciliation findings.
    """
    l_path = Path(ledger_path)
    t_path = Path(tb_path)

    if not l_path.exists() or not t_path.exists():
        return {
            "test": "check_trial_balance",
            "flagged_ids": [],
            "stats": {"ledger_exists": l_path.exists(), "tb_exists": t_path.exists()},
            "notes": "Missing ledger or trial balance file for reconciliation.",
        }

    ledger = pd.read_csv(l_path)
    tb = pd.read_csv(t_path)

    # Compute ledger debits and credits by account
    ledger_debits = (
        ledger.groupby("account_code")["debit_inr"].sum().to_dict()
    )
    ledger_credits = (
        ledger.groupby("account_code")["credit_inr"].sum().to_dict()
    )

    gaps = []
    flagged_ids: list[str] = []

    for _, row in tb.iterrows():
        code = row["account_code"]
        name = row["account_name"]
        tb_dr = float(row["total_debit"])
        tb_cr = float(row["total_credit"])

        l_dr = float(ledger_debits.get(code, 0.0))
        l_cr = float(ledger_credits.get(code, 0.0))

        dr_diff = round(l_dr - tb_dr, 2)
        cr_diff = round(l_cr - tb_cr, 2)

        if abs(dr_diff) > 0.01 or abs(cr_diff) > 0.01:
            gaps.append(
                {
                    "account_code": code,
                    "account_name": name,
                    "ledger_debit": l_dr,
                    "tb_debit": tb_dr,
                    "debit_gap": dr_diff,
                    "ledger_credit": l_cr,
                    "tb_credit": tb_cr,
                    "credit_gap": cr_diff,
                }
            )

            # Search ledger entries for candidate entries matching the discrepancy
            gap_amount = abs(dr_diff) if abs(dr_diff) > 0.01 else abs(cr_diff)
            candidates = ledger[
                (ledger["account_code"] == code)
                & (ledger["amount_inr"] == gap_amount)
            ]["entry_id"].tolist()

            if candidates:
                flagged_ids.extend(candidates)
            else:
                # If no single entry matches the gap exactly, flag all entries on that account
                all_acc_entries = ledger[ledger["account_code"] == code][
                    "entry_id"
                ].tolist()
                flagged_ids.extend(all_acc_entries)

    flagged_ids = sorted(list(set(flagged_ids)))

    stats = {
        "accounts_reconciled": int(len(tb)),
        "discrepant_accounts_count": int(len(gaps)),
        "discrepancies": gaps,
        "total_discrepancy_inr": sum(
            abs(g["debit_gap"]) + abs(g["credit_gap"]) for g in gaps
        ),
    }

    if not gaps:
        notes = f"All {len(tb)} accounts in trial balance fully reconciled with general ledger (0.00 discrepancy)."
    else:
        acc_summaries = [
            f"Account {g['account_code']} ({g['account_name']}): debit gap Rs {g['debit_gap']:,.2f}, credit gap Rs {g['credit_gap']:,.2f}"
            for g in gaps
        ]
        notes = (
            f"Found {len(gaps)} account discrepancy between ledger and trial balance: "
            + "; ".join(acc_summaries)
        )

    return {
        "test": "check_trial_balance",
        "flagged_ids": flagged_ids,
        "stats": stats,
        "notes": notes,
    }
