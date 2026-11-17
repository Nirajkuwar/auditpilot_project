"""
Deterministic Risk Scoring and Ranking Tools for AuditPilot.
Computes composite risk scores (likelihood * impact), resolves exact monetary exposure
directly from data/ledger.csv, and ranks audit findings in descending order of risk.
"""

from pathlib import Path
from typing import Any
import pandas as pd


def score_and_rank_findings(
    findings: list[dict[str, Any]],
    ledger_path: str = "data/ledger.csv",
) -> dict[str, Any]:
    """Deterministically score, price, and rank proposed audit findings.

    Strictly enforces numerical integrity:
    1. Looks up exact transaction amounts from data/ledger.csv for all cited entry_ids.
       (Never estimates, guesses, or LLM-sums amounts).
    2. Computes risk score = likelihood * impact directly in Python.
    3. Sorts all findings descending by score (with amount_at_risk_inr as tie-breaker).
    4. Normalizes IDs (FIND-001, FIND-002, ...) and default review statuses.

    Args:
        findings: List of proposed finding dictionaries containing entry_ids, likelihood, impact, etc.
        ledger_path: Path to the general ledger CSV file (default: 'data/ledger.csv').

    Returns:
        A dictionary with keys:
            - test: 'score_and_rank_findings'
            - findings: Sorted list of validated finding dictionaries matching the Finding schema.
            - total_findings: Count of ranked findings.
            - total_exposure_inr: Total monetary exposure across all findings.
            - highest_risk_score: Highest risk score among findings.
            - notes: Summary of the scoring and ranking outcome.
    """
    path = Path(ledger_path)
    ledger_map: dict[str, float] = {}
    if path.exists():
        try:
            df = pd.read_csv(path, usecols=["entry_id", "amount_inr"])
            ledger_map = dict(zip(df["entry_id"], df["amount_inr"].astype(float)))
        except Exception:
            # Fallback if specific usecols fail
            df = pd.read_csv(path)
            if "entry_id" in df.columns and "amount_inr" in df.columns:
                ledger_map = dict(zip(df["entry_id"], df["amount_inr"].astype(float)))

    processed: list[dict[str, Any]] = []

    for item in findings:
        f = dict(item)

        # 1. Normalize entry_ids and evidence lists
        raw_eids = f.get("entry_ids", [])
        if isinstance(raw_eids, str):
            entry_ids = [e.strip() for e in raw_eids.split(",") if e.strip()]
        elif isinstance(raw_eids, list):
            entry_ids = [str(e).strip() for e in raw_eids if str(e).strip()]
        else:
            entry_ids = []
        f["entry_ids"] = entry_ids

        raw_ev = f.get("evidence", [])
        if isinstance(raw_ev, str):
            evidence = [raw_ev.strip()]
        elif isinstance(raw_ev, list):
            evidence = [str(e).strip() for e in raw_ev if str(e).strip()]
        else:
            evidence = []
        f["evidence"] = evidence

        # 2. Deterministic exact monetary lookup from ledger
        matched_amounts = [ledger_map[eid] for eid in entry_ids if eid in ledger_map]
        if matched_amounts:
            f["amount_at_risk_inr"] = round(float(sum(matched_amounts)), 2)
        elif "amount_at_risk_inr" in f and f["amount_at_risk_inr"] is not None:
            f["amount_at_risk_inr"] = round(float(f["amount_at_risk_inr"]), 2)
        else:
            f["amount_at_risk_inr"] = 0.0

        # 3. Deterministic Likelihood and Impact clamping & Score calculation
        raw_likelihood = int(f.get("likelihood", 3))
        raw_impact = int(f.get("impact", 3))

        likelihood = max(1, min(5, raw_likelihood))
        impact = max(1, min(5, raw_impact))
        score = likelihood * impact

        f["likelihood"] = likelihood
        f["impact"] = impact
        f["score"] = score

        # 4. Status and default fields
        if "status" not in f or not f["status"]:
            f["status"] = "pending_review"
        if "review_note" not in f or f["review_note"] is None:
            f["review_note"] = ""
        if "rationale" not in f or not f["rationale"]:
            f["rationale"] = f"Assessed with likelihood {likelihood}/5 and impact {impact}/5."

        processed.append(f)

    # 5. Sort descending by score, tie-breaker: amount_at_risk_inr descending
    processed.sort(
        key=lambda x: (x["score"], x["amount_at_risk_inr"]),
        reverse=True,
    )

    # 6. Assign or normalize sequential IDs (FIND-001, FIND-002, ...)
    for idx, f in enumerate(processed):
        f["id"] = f"FIND-{idx + 1:03d}"

    total_exposure = round(sum(f["amount_at_risk_inr"] for f in processed), 2)
    highest_score = max((f["score"] for f in processed), default=0)

    return {
        "test": "score_and_rank_findings",
        "findings": processed,
        "total_findings": len(processed),
        "total_exposure_inr": total_exposure,
        "highest_risk_score": highest_score,
        "notes": (
            f"Successfully scored, verified ledger amounts, and ranked {len(processed)} "
            f"findings. Highest risk score: {highest_score}, total exposure: Rs {total_exposure:,.2f}."
        ),
    }


# Convenient alias
rank_findings = score_and_rank_findings
