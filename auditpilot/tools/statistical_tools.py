"""
Statistical audit testing tools, including Benford's Law analysis.
"""

from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd


def benford_test(
    ledger_path: str = "data/ledger.csv",
    mad_threshold: float = 0.012,
    residual_threshold: float = 2.5,
) -> dict[str, Any]:
    """Perform first-digit Benford's Law analysis on ledger transaction amounts.

    Extracts the leading significant digit (1-9) from all non-zero transaction amounts
    in the general ledger, compares empirical frequencies against the theoretical
    Benford logarithmic distribution (P(d) = log10(1 + 1/d)), and performs goodness-of-fit
    evaluations using Chi-Square and Mean Absolute Deviation (MAD). Digits with
    standardized residuals exceeding residual_threshold are flagged as anomalies.

    Args:
        ledger_path: Path to the general ledger CSV file.
        mad_threshold: Mean Absolute Deviation threshold for non-conformity (default: 0.012).
        residual_threshold: Z-score residual threshold for flagging an individual digit (default: 2.5).

    Returns:
        A dictionary with keys:
            - test: Name of the audit test ('benford_test').
            - flagged_ids: List of entry_ids associated with anomalous digit spikes.
            - stats: Observed and expected digit counts, chi-square, MAD, and conformity level.
            - notes: Forensic analysis narrative detailing conformity or specific digit spikes.
    """
    path = Path(ledger_path)
    if not path.exists():
        return {
            "test": "benford_test",
            "flagged_ids": [],
            "stats": {"file_exists": False},
            "notes": f"Ledger file not found at path: {ledger_path}",
        }

    ledger = pd.read_csv(path)

    # Use non-zero debit entries (or primary operational entries where debit_inr > 0)
    # to avoid double-counting both legs of every transaction
    pos_entries = ledger[ledger["debit_inr"] > 0].copy()
    if pos_entries.empty:
        pos_entries = ledger[ledger["amount_inr"] > 0].copy()

    # Extract first significant digit
    def extract_first_digit(val: float) -> int:
        s = f"{val:.2f}".replace(".", "").lstrip("0")
        return int(s[0]) if s else 0

    pos_entries["first_digit"] = pos_entries["debit_inr"].apply(
        extract_first_digit
    )
    valid_entries = pos_entries[pos_entries["first_digit"].between(1, 9)]

    total_n = len(valid_entries)
    if total_n == 0:
        return {
            "test": "benford_test",
            "flagged_ids": [],
            "stats": {"total_transactions": 0},
            "notes": "No valid non-zero transaction amounts available for Benford analysis.",
        }

    counts = valid_entries["first_digit"].value_counts().to_dict()

    digit_stats = {}
    chi_square = 0.0
    mad_sum = 0.0
    anomalous_digits = []

    for d in range(1, 10):
        obs = counts.get(d, 0)
        exp_prob = np.log10(1 + 1 / d)
        exp_count = total_n * exp_prob
        obs_prob = obs / total_n
        diff_prob = obs_prob - exp_prob

        # Standardized residual: (O - E) / sqrt(E)
        std_res = (obs - exp_count) / np.sqrt(exp_count) if exp_count > 0 else 0.0
        chi_contrib = ((obs - exp_count) ** 2) / exp_count if exp_count > 0 else 0.0

        chi_square += chi_contrib
        mad_sum += abs(diff_prob)

        if abs(std_res) >= residual_threshold:
            anomalous_digits.append(d)

        digit_stats[str(d)] = {
            "observed_count": int(obs),
            "expected_count": round(float(exp_count), 2),
            "observed_pct": round(float(obs_prob * 100), 2),
            "expected_pct": round(float(exp_prob * 100), 2),
            "diff_pct": round(float(diff_prob * 100), 2),
            "standardized_residual": round(float(std_res), 2),
            "is_anomaly": abs(std_res) >= residual_threshold,
        }

    mad = round(float(mad_sum / 9.0), 4)
    chi_square = round(float(chi_square), 2)

    # Nigrini MAD conformity evaluation
    if mad <= 0.006:
        conformity = "Close conformity"
    elif mad <= 0.012:
        conformity = "Acceptable conformity"
    elif mad <= 0.015:
        conformity = "Marginally acceptable conformity"
    else:
        conformity = "Non-conformity"

    # Flag entry_ids belonging to anomalous digit spikes
    flagged_entries = valid_entries[
        valid_entries["first_digit"].isin(anomalous_digits)
    ]
    flagged_ids = sorted(flagged_entries["entry_id"].tolist())

    stats = {
        "sample_size": total_n,
        "chi_square_statistic": chi_square,
        "degrees_of_freedom": 8,
        "mean_absolute_deviation": mad,
        "conformity_assessment": conformity,
        "anomalous_digits": anomalous_digits,
        "digits": digit_stats,
    }

    if not anomalous_digits:
        notes = (
            f"Benford's Law analysis (N={total_n:,}): Data exhibits {conformity} "
            f"(MAD: {mad:.4f}, Chi-Square: {chi_square:.2f}). No significant digit anomalies detected."
        )
    else:
        spikes = [
            f"Digit {d} (Obs: {digit_stats[str(d)]['observed_pct']}%, Exp: {digit_stats[str(d)]['expected_pct']}%, Z: {digit_stats[str(d)]['standardized_residual']})"
            for d in anomalous_digits
        ]
        notes = (
            f"Benford's Law analysis (N={total_n:,}): Data exhibits {conformity} "
            f"(MAD: {mad:.4f}, Chi-Square: {chi_square:.2f}). Significant statistical spikes detected: "
            + "; ".join(spikes)
            + f". Flagged {len(flagged_ids)} candidate entries."
        )

    return {
        "test": "benford_test",
        "flagged_ids": flagged_ids,
        "stats": stats,
        "notes": notes,
    }
