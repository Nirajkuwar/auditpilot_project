"""
Deterministic Audit Reporting and Sign-Off Tools for AuditPilot.
Provides structured memorandum writing, status management, and
human-in-the-loop audit partner sign-off controls.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_audit_memo(
    markdown_content: str,
    status: str = "DRAFT",
    output_path: str = "docs/audit_memo.md",
) -> dict[str, Any]:
    """Deterministically write formatted audit memorandum to markdown file.

    Enforces status validation ('DRAFT' or 'FINAL') and ensures standard
    formal header banner formatting.

    Args:
        markdown_content: The full markdown body of the audit memorandum.
        status: Status of the memorandum ('DRAFT' or 'FINAL', default: 'DRAFT').
        output_path: Target file path (default: 'docs/audit_memo.md').

    Returns:
        A dictionary with keys:
            - test: 'write_audit_memo'
            - path: File path written
            - status: Normalized status string ('DRAFT' or 'FINAL')
            - bytes_written: Byte size of the output file
            - notes: Summary of the write operation.
    """
    clean_status = status.strip().upper()
    if clean_status not in ("DRAFT", "FINAL"):
        raise ValueError(f"Invalid status '{status}'. Must be either 'DRAFT' or 'FINAL'.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    header_banner = (
        "---\n"
        "# AUDIT MEMORANDUM\n"
        f"**Status: {clean_status}** ({'Awaiting Partner Sign-Off' if clean_status == 'DRAFT' else 'Signed Off by Audit Partner'})\n"
        "**Entity:** Sahyadri Precision Components Pvt. Ltd.\n"
        "**Fiscal Period:** FY 2025-26 (April 1, 2025 – March 31, 2026)\n"
        "---\n\n"
    )

    clean_content = markdown_content.strip()
    if not clean_content.startswith("---") and "# AUDIT MEMORANDUM" not in clean_content:
        full_content = header_banner + clean_content
    else:
        if clean_status == "FINAL":
            clean_content = clean_content.replace("Status: DRAFT", "Status: FINAL")
            clean_content = clean_content.replace("**Status: DRAFT**", "**Status: FINAL**")
            clean_content = clean_content.replace(
                "(Awaiting Partner Sign-Off)",
                "(Signed Off by Audit Partner)",
            )
        elif clean_status == "DRAFT":
            clean_content = clean_content.replace("Status: FINAL", "Status: DRAFT")
            clean_content = clean_content.replace("**Status: FINAL**", "**Status: DRAFT**")
            clean_content = clean_content.replace(
                "(Signed Off by Audit Partner)",
                "(Awaiting Partner Sign-Off)",
            )
        full_content = clean_content

    with open(path, "w", encoding="utf-8") as f:
        f.write(full_content)

    return {
        "test": "write_audit_memo",
        "path": str(path),
        "status": clean_status,
        "bytes_written": len(full_content.encode("utf-8")),
        "notes": f"Audit memorandum successfully written to {path} with Status: {clean_status}.",
    }


def sign_off_memo(
    decision: str,
    reviewer_name: str = "Audit Partner",
    comments: str = "",
    memo_path: str = "docs/audit_memo.md",
) -> dict[str, Any]:
    """Execute human-in-the-loop audit partner sign-off decision.

    If decision is 'APPROVE', flips memorandum status from 'DRAFT' to 'FINAL',
    and appends a formal sign-off verification block with reviewer identity
    and ISO 8601 timestamp. If 'REJECT' or 'REQUEST_CHANGES', records feedback
    and preserves 'DRAFT' status.

    Args:
        decision: Partner decision ('APPROVE', 'REJECT', or 'REQUEST_CHANGES').
        reviewer_name: Identity of the reviewing partner (default: 'Audit Partner').
        comments: Review commentary, feedback, or sign-off notes.
        memo_path: Path to the audit memorandum file (default: 'docs/audit_memo.md').

    Returns:
        A dictionary with keys:
            - test: 'sign_off_memo'
            - decision: Normalized decision string
            - status: Resulting status ('FINAL' if approved, else 'DRAFT')
            - path: Path to the memorandum file
            - notes: Summary of the sign-off action.
    """
    clean_decision = decision.strip().upper()
    path = Path(memo_path)

    if not path.exists():
        return {
            "test": "sign_off_memo",
            "decision": clean_decision,
            "status": "NOT_FOUND",
            "path": str(path),
            "notes": f"Error: Audit memorandum not found at {path}.",
        }

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if clean_decision == "APPROVE":
        updated_content = content.replace("Status: DRAFT", "Status: FINAL")
        updated_content = updated_content.replace("**Status: DRAFT**", "**Status: FINAL**")
        updated_content = updated_content.replace(
            "(Awaiting Partner Sign-Off)",
            "(Signed Off by Audit Partner)",
        )

        signoff_block = (
            f"\n\n## 7. Partner Sign-Off Block\n\n"
            f"| Field | Value |\n"
            f"|---|---|\n"
            f"| **Reviewer** | {reviewer_name} |\n"
            f"| **Decision** | **APPROVED** |\n"
            f"| **Timestamp** | {now_iso} |\n"
            f"| **Partner Commentary** | {comments or 'Approved as final audit memorandum for stakeholder issuance.'} |\n"
            f"| **Sign-Off Status** | **FINALIZED** |\n"
        )

        if "## 7. Partner Sign-Off Block" in updated_content:
            parts = updated_content.split("## 7. Partner Sign-Off Block")
            updated_content = parts[0].rstrip() + signoff_block
        else:
            updated_content = updated_content.rstrip() + signoff_block

        with open(path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        return {
            "test": "sign_off_memo",
            "decision": "APPROVED",
            "status": "FINAL",
            "path": str(path),
            "notes": f"Audit memorandum successfully signed off and finalized by {reviewer_name}.",
        }

    else:
        feedback_block = (
            f"\n\n> [!WARNING] **Partner Review Feedback ({clean_decision} at {now_iso})**\n"
            f"> **Reviewer:** {reviewer_name}\n"
            f"> **Commentary:** {comments or 'Changes requested prior to final approval.'}\n"
        )
        updated_content = content.rstrip() + feedback_block

        with open(path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        return {
            "test": "sign_off_memo",
            "decision": clean_decision,
            "status": "DRAFT",
            "path": str(path),
            "notes": f"Sign-off decision '{clean_decision}' recorded by {reviewer_name}. Memorandum remains in Status: DRAFT.",
        }
