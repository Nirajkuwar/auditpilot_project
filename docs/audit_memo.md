---
# AUDIT MEMORANDUM
**Status: FINAL** (Signed Off by Audit Partner)
**Entity:** Sahyadri Precision Components Pvt. Ltd.
**Fiscal Period:** FY 2025-26 (April 1, 2025 – March 31, 2026)
---

# Audit Memorandum

## 1. Scope and Data
- **Entity:** Sahyadri Precision Components Pvt. Ltd.
- **Fiscal Period:** April 1, 2025 to March 31, 2026.
- **Total Transactions Analyzed:** 6,000 entries.
- **General Ledger Turnover:** Total Debits INR 17,11,75,194.18 | Total Credits INR 17,11,75,194.18 (Double-entry balanced).
- **Trial Balance Discrepancy:** Account 6020 (Repairs & Maintenance - Machinery) displays an unadjusted variance of INR 125,000.00 (citing entry JE-2025-2767).

## 2. Executive Summary
The audit has revealed a highly deteriorated control environment at Sahyadri Precision Components Pvt. Ltd. Analysis of the fiscal 2025-26 period identified systemic breaches of corporate SOPs, including acute segregation of duties failures, structured evasion of approval thresholds, and significant conflict of interest violations where employees share bank accounts with active vendors. Furthermore, financial ratio analysis confirms the company is experiencing severe financial distress, with negative operating margins and deteriorating liquidity throughout the fiscal year. Immediate remedial action is required to address these governance and control failures.

## 3. Ranked Findings (Confirmed)

| Finding ID | Title & Category | Cited Entry IDs | Amount at Risk (INR) | Risk Score |
| :--- | :--- | :--- | :--- | :--- |
| FIND-001 | Vendor Conflict of Interest & Ghost Vendor Disbursements (VENDOR_INTEGRITY) | [Multiple] | 1,507,000.00 | 25 |
| FIND-002 | Prohibited Self-Approval of Journal Entries (SEGREGATION_OF_DUTIES) | [Multiple] | 312,000.00 | 25 |
| FIND-003 | Structured Split-Payment Evasion of Approval Thresholds (SPLIT_PAYMENTS) | [Multiple] | 866,600.00 | 20 |
| FIND-004 | Unauthorized Weekend Round-Amount Postings (UNAUTHORIZED_POSTING) | [Multiple] | 900,000.00 | 16 |
| FIND-006 | Unreconciled Trial Balance Variance (TRIAL_BALANCE) | JE-2025-2767 | 125,000.00 | 9 |

### Detailed Findings
- **FIND-001:** Systemic conflict of interest (shared bank accounts) and non-compliant vendor onboarding (ghost vendors) per SOP Clause 3.2 and 5.1.
- **FIND-002:** Acute control breach where preparers approved their own journal entries per SOP Clause 3.1.
- **FIND-003:** Systematic evasion of Tier 1 approval threshold (INR 50,000) via structured split-payments per SOP Clause 4.2.
- **FIND-004:** Recurring unauthorized weekend manual postings with round-amounts, violating SOP Clause 5.2/5.3.
- **FIND-006:** Unadjusted trial balance discrepancy in 'Repairs & Maintenance - Machinery'.

## 4. Recommended Actions for Management
- **ERP Remediation:** Implement mandatory maker-checker blocks to prevent any journal voucher where `posted_by` equals `approved_by`.
- **Vendor Governance:** Execute an immediate audit of vendor master files; automate cross-matching between vendor and employee bank accounts.
- **Threshold Monitoring:** Implement rolling 48-hour automated monitoring for payments to the same vendor to prevent threshold evasion.
- **Trial Balance:** Post an adjusting journal entry to account 6020 to resolve the identified INR 125,000 variance.

## 5. Limitations
This analysis is based solely on the provided electronic ledger datasets and financial schedules. The scope excludes physical inventory verification and external banking circularization.

## 6. Appendix: Dropped Findings
| Finding ID | Category & Title | Cited Entry IDs | Review Note / Justification |
| :--- | :--- | :--- | :--- |
| FIND-005 | DUPLICATE_PAYMENTS: Duplicate Vendor Payments | [Multiple] | Ledger records show these are original disbursements and subsequent manual corrections/reversals, not fraudulent duplicates. |

## 7. Partner Sign-Off Block

| Field | Value |
|---|---|
| **Reviewer** | Audit Partner |
| **Decision** | **APPROVED** |
| **Timestamp** | 2026-11-17T06:47:05Z |
| **Partner Commentary** | Audit memorandum finalized and approved for issue. |
| **Sign-Off Status** | **FINALIZED** |
