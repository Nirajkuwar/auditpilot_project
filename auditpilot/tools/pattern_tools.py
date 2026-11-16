"""
Pattern detection tools for transaction anomalies: duplicates, split payments, and weekend round postings.
"""

from pathlib import Path
from typing import Any
import pandas as pd


def find_duplicates(
    ledger_path: str = "data/ledger.csv",
    window_days: int = 5,
) -> dict[str, Any]:
    """Detect duplicate payments issued to the same vendor with identical amounts.

    Scans general ledger vendor disbursements for occurrences where the same
    vendor_id is paid the exact same amount_inr multiple times within a rolling
    window of window_days calendar days.

    Args:
        ledger_path: Path to the general ledger CSV file.
        window_days: Maximum interval in days between matching payments (default: 5).

    Returns:
        A dictionary with keys:
            - test: Name of the audit test ('find_duplicates').
            - flagged_ids: List of entry_ids involved in duplicate payment events.
            - stats: Detailed metrics on duplicate pairs, affected vendors, and amounts.
            - notes: Summary of duplicate payment findings and exposure.
    """
    path = Path(ledger_path)
    if not path.exists():
        return {
            "test": "find_duplicates",
            "flagged_ids": [],
            "stats": {"file_exists": False},
            "notes": f"Ledger file not found at path: {ledger_path}",
        }

    ledger = pd.read_csv(path)

    # Filter for valid vendor disbursements (debit entries with non-empty vendor_id)
    v_df = ledger[
        ledger["vendor_id"].notna()
        & (ledger["vendor_id"] != "")
        & (ledger["debit_inr"] > 0)
    ].copy()

    if v_df.empty:
        return {
            "test": "find_duplicates",
            "flagged_ids": [],
            "stats": {"vendor_entries_checked": 0, "duplicates_found": 0},
            "notes": "No vendor debit disbursements found in ledger.",
        }

    v_df["date_dt"] = pd.to_datetime(v_df["date"])
    v_df = v_df.sort_values(["vendor_id", "date_dt"])

    flagged_ids: list[str] = []
    duplicate_groups = []

    for (vid, amt), grp in v_df.groupby(["vendor_id", "amount_inr"]):
        if len(grp) > 1:
            grp = grp.sort_values("date_dt")
            matched_indices = set()
            for i in range(len(grp)):
                for j in range(i + 1, len(grp)):
                    diff_days = (
                        grp.iloc[j]["date_dt"] - grp.iloc[i]["date_dt"]
                    ).days
                    if diff_days <= window_days:
                        matched_indices.add(i)
                        matched_indices.add(j)

            if matched_indices:
                matched_rows = grp.iloc[sorted(list(matched_indices))]
                eids = matched_rows["entry_id"].tolist()
                flagged_ids.extend(eids)
                duplicate_groups.append(
                    {
                        "vendor_id": vid,
                        "amount_inr": float(amt),
                        "entry_ids": eids,
                        "dates": matched_rows["date"].tolist(),
                        "descriptions": matched_rows["description"].tolist(),
                    }
                )

    flagged_ids = sorted(list(set(flagged_ids)))
    total_exposure = sum(g["amount_inr"] for g in duplicate_groups)

    stats = {
        "vendor_entries_checked": int(len(v_df)),
        "duplicate_groups_count": int(len(duplicate_groups)),
        "flagged_entries_count": int(len(flagged_ids)),
        "total_exposure_inr": round(float(total_exposure), 2),
        "groups": duplicate_groups,
    }

    if not flagged_ids:
        notes = f"No duplicate vendor disbursements identified within {window_days}-day window across {len(v_df):,} entries."
    else:
        notes = (
            f"Identified {len(duplicate_groups)} duplicate payment clusters ({len(flagged_ids)} total entries) "
            f"with identical vendor and amount within {window_days} days. Total duplicate exposure: Rs {total_exposure:,.2f}."
        )

    return {
        "test": "find_duplicates",
        "flagged_ids": flagged_ids,
        "stats": stats,
        "notes": notes,
    }


def find_split_payments(
    ledger_path: str = "data/ledger.csv",
    lower_limit: float = 45000.0,
    upper_limit: float = 50000.0,
    window_hours: int = 48,
    min_count: int = 2,
) -> dict[str, Any]:
    """Detect structured / split payments designed to circumvent approval limits.

    Scans vendor disbursements for clusters of transactions issued to the same
    vendor within a rolling window_hours window where each transaction amount is
    just below the delegated approval threshold (between lower_limit and upper_limit).

    Args:
        ledger_path: Path to the general ledger CSV file.
        lower_limit: Lower bound of near-threshold transaction amounts (default: 45,000 INR).
        upper_limit: Upper approval threshold limit (default: 50,000 INR).
        window_hours: Maximum hours between split transactions (default: 48 hours).
        min_count: Minimum number of near-threshold transactions to form a group (default: 2).

    Returns:
        A dictionary with keys:
            - test: Name of the audit test ('find_split_payments').
            - flagged_ids: List of entry_ids identified as structured split payments.
            - stats: Detailed breakdown of split payment clusters by vendor.
            - notes: Forensic analysis of structuring activities.
    """
    path = Path(ledger_path)
    if not path.exists():
        return {
            "test": "find_split_payments",
            "flagged_ids": [],
            "stats": {"file_exists": False},
            "notes": f"Ledger file not found at path: {ledger_path}",
        }

    ledger = pd.read_csv(path)

    # Filter vendor debit entries
    v_df = ledger[
        ledger["vendor_id"].notna()
        & (ledger["vendor_id"] != "")
        & (ledger["debit_inr"] > 0)
    ].copy()

    if v_df.empty:
        return {
            "test": "find_split_payments",
            "flagged_ids": [],
            "stats": {"candidate_count": 0},
            "notes": "No vendor debit disbursements found in ledger.",
        }

    v_df["date_dt"] = pd.to_datetime(v_df["date"])

    # Near-threshold candidate entries
    candidates = v_df[
        (v_df["amount_inr"] >= lower_limit) & (v_df["amount_inr"] < upper_limit)
    ].sort_values(["vendor_id", "date_dt"])

    flagged_ids: list[str] = []
    split_clusters = []

    for vid, grp in candidates.groupby("vendor_id"):
        grp = grp.sort_values("date_dt")
        eids = grp["entry_id"].tolist()
        dates = grp["date_dt"].tolist()
        amts = grp["amount_inr"].tolist()

        vendor_flagged_indices = set()

        for i in range(len(grp)):
            cluster_indices = [i]
            for j in range(i + 1, len(grp)):
                span_seconds = (dates[j] - dates[i]).total_seconds()
                if span_seconds <= window_hours * 3600:
                    cluster_indices.append(j)

            if len(cluster_indices) >= min_count:
                vendor_flagged_indices.update(cluster_indices)

        if vendor_flagged_indices:
            idx_list = sorted(list(vendor_flagged_indices))
            c_eids = [eids[k] for k in idx_list]
            c_amts = [amts[k] for k in idx_list]
            c_dates = [dates[k].strftime("%Y-%m-%d") for k in idx_list]
            tot_val = sum(c_amts)

            flagged_ids.extend(c_eids)
            split_clusters.append(
                {
                    "vendor_id": vid,
                    "entry_count": len(c_eids),
                    "total_amount_inr": round(float(tot_val), 2),
                    "entry_ids": c_eids,
                    "amounts": c_amts,
                    "dates": c_dates,
                }
            )

    flagged_ids = sorted(list(set(flagged_ids)))
    total_split_value = sum(c["total_amount_inr"] for c in split_clusters)

    stats = {
        "near_threshold_entries_checked": int(len(candidates)),
        "split_groups_count": int(len(split_clusters)),
        "flagged_entries_count": int(len(flagged_ids)),
        "total_structured_amount_inr": round(float(total_split_value), 2),
        "clusters": split_clusters,
    }

    if not flagged_ids:
        notes = f"No structured split payments identified between Rs {lower_limit:,.2f} and Rs {upper_limit:,.2f} within {window_hours} hours."
    else:
        notes = (
            f"Detected {len(split_clusters)} structured split-payment groups ({len(flagged_ids)} total entries) "
            f"to {len(split_clusters)} vendors within {window_hours} hours near the Rs {upper_limit:,.2f} threshold. "
            f"Total structured amount: Rs {total_split_value:,.2f}."
        )

    return {
        "test": "find_split_payments",
        "flagged_ids": flagged_ids,
        "stats": stats,
        "notes": notes,
    }


def find_weekend_round(
    ledger_path: str = "data/ledger.csv",
    round_base: float = 10000.0,
    sundays_only: bool = True,
) -> dict[str, Any]:
    """Identify off-hour transactions posted on Sundays with exact round INR amounts.

    Enforces Corporate Policy Clause 5.2 & 5.3 prohibiting weekend manual journal entries
    and flagging round-amount disbursements (exact multiples of round_base) posted on non-working days.

    Args:
        ledger_path: Path to the general ledger CSV file.
        round_base: Multiple used to define a round amount (default: 10,000 INR).
        sundays_only: If True, restricts check to Sundays (day_of_week == 6).
                      If False, checks entire weekend (Saturday & Sunday).

    Returns:
        A dictionary with keys:
            - test: Name of the audit test ('find_weekend_round').
            - flagged_ids: List of entry_ids matching weekend round amount criteria.
            - stats: Detailed counts, date breakdown, and total flagged volume.
            - notes: Summary of weekend round-amount findings.
    """
    path = Path(ledger_path)
    if not path.exists():
        return {
            "test": "find_weekend_round",
            "flagged_ids": [],
            "stats": {"file_exists": False},
            "notes": f"Ledger file not found at path: {ledger_path}",
        }

    ledger = pd.read_csv(path)
    ledger["date_dt"] = pd.to_datetime(ledger["date"])

    if sundays_only:
        day_mask = ledger["date_dt"].dt.day_of_week == 6
        target_name = "Sunday"
    else:
        day_mask = ledger["date_dt"].dt.day_of_week >= 5
        target_name = "Weekend"

    round_mask = (ledger["amount_inr"] % round_base == 0) & (
        ledger["amount_inr"] > 0
    )
    flagged_df = ledger[day_mask & round_mask].copy()

    flagged_ids = sorted(flagged_df["entry_id"].tolist())
    total_val = round(float(flagged_df["amount_inr"].sum()), 2)

    by_date = (
        flagged_df.groupby("date")
        .agg(entry_count=("entry_id", "count"), total_inr=("amount_inr", "sum"))
        .reset_index()
        .to_dict("records")
    )

    stats = {
        "total_ledger_rows": int(len(ledger)),
        "weekend_entries_checked": int(day_mask.sum()),
        "flagged_entries_count": int(len(flagged_ids)),
        "total_flagged_amount_inr": total_val,
        "round_base_inr": round_base,
        "by_date": by_date,
    }

    if not flagged_ids:
        notes = f"No {target_name.lower()} round-amount entries (multiples of Rs {round_base:,.2f}) detected in ledger."
    else:
        notes = (
            f"Flagged {len(flagged_ids)} {target_name.lower()} transactions posted with exact round amounts "
            f"(multiples of Rs {round_base:,.2f}) totaling Rs {total_val:,.2f}. Breaches SOP Clause 5.2/5.3."
        )

    return {
        "test": "find_weekend_round",
        "flagged_ids": flagged_ids,
        "stats": stats,
        "notes": notes,
    }
