---
# AUDIT MEMORANDUM
**Status: FINAL** (Signed Off by Audit Partner)
**Entity:** Sahyadri Precision Components Pvt. Ltd.
**Fiscal Period:** FY 2025-26 (April 1, 2025 – March 31, 2026)
---

# Audit Memorandum: Sahyadri Precision Components Pvt. Ltd.

## 1. Scope and Data
- **Entity:** Sahyadri Precision Components Pvt. Ltd.
- **Fiscal Period:** April 1, 2025 to March 31, 2026.
- **Total Transactions Analyzed:** 6,000 entries.
- **General Ledger Turnover:** Total Debits INR 171,175,194.18 | Total Credits INR 171,175,194.18 (Double-entry balanced).
- **Trial Balance Discrepancy:** Account 6020 (Repairs & Maintenance - Machinery) displays an unadjusted variance of INR 125,000.00 (citing entry JE-2025-2767).

## 2. Executive Summary
The audit has uncovered significant internal control deficiencies within the financial reporting and disbursement processes. Systemic risks include critical conflicts of interest between employees and vendors, widespread circumvention of segregation of duties through self-approval, and structured transaction patterns designed to evade established approval thresholds. These control failures, combined with sustained operational financial distress, pose a material risk to the company's integrity and financial stability.

## 3. Ranked Findings (Confirmed)
| Finding ID | Title & Category | Cited Entry IDs | Amount at Risk (INR) | Risk Score |
| :--- | :--- | :--- | :--- | :--- |
| FIND-001 | Vendor-Employee Banking Conflicts | JE-2025-0855, et al. | 1,507,000.00 | 25 |
| FIND-002 | Segregation of Duties Self-Approval | JE-2025-0945, et al. | 312,000.00 | 25 |
| FIND-003 | Structured Split-Payment Evasion | JE-2025-0455, et al. | 866,600.00 | 20 |
| FIND-004 | Unauthorized Weekend Postings | JE-2025-0439, et al. | 900,000.00 | 16 |
| FIND-006 | Trial Balance Reconciliation | JE-2025-2767 | 125,000.00 | 9 |

- **FIND-001 (VENDOR_INTEGRITY):** Confirmed systemic conflict; shared bank accounts between high-risk vendors and procurement/finance/operations staff. Violation of SOP Clauses 3.2 and 5.1.
- **FIND-002 (SEGREGATION_OF_DUTIES):** Confirmed self-approval of journal entries (maker == checker). Violation of SOP Clause 3.1.
- **FIND-003 (SPLIT_PAYMENTS):** Confirmed structured payment clusters within 48-hour windows to evade Tier 1 authority. Violation of SOP Clause 4.2.
- **FIND-004 (UNAUTHORIZED_POSTING):** Confirmed manual weekend entries with round-amount anomalies. Violation of SOP Clauses 5.2/5.3.
- **FIND-006 (TRIAL_BALANCE):** Confirmed variance between ledger and trial balance.

## 4. Recommended Actions for Management
- **Immediate Remediation:** Implement automated ERP validation to block all journal vouchers where `posted_by == approved_by`.
- **Vendor Controls:** Perform an immediate audit of the vendor master file; automate cross-matching of vendor bank accounts against employee payroll records to identify and neutralize conflicts.
- **Approval Monitoring:** Configure automated alerts for transaction clusters exceeding thresholds within a rolling 48-hour window.
- **Reconciliation:** Adjusting journal entry required to reconcile the INR 125,000.00 variance in Account 6020.

## 5. Limitations
This analysis was performed on provided electronic ledger datasets and financial schedules. The scope did not include physical inventory verification or external banking circularization.

## 6. Appendix: Dropped Findings and Reasons
| Finding ID | Category & Title | Cited Entry IDs | Review Note |
| :--- | :--- | :--- | :--- |
| FIND-005 | DUPLICATE_PAYMENTS | JE-2025-0249, et al. | Dropped: Clusters verified as legitimate sequential payment cycles; not duplicates. |

## 7. Partner Sign-Off Block

| Field | Value |
|---|---|
| **Reviewer** | Audit Partner |
| **Decision** | **APPROVED** |
| **Timestamp** | 2026-11-17T07:10:37Z |
| **Partner Commentary** | Approved as final audit memorandum for stakeholder issuance. |
| **Sign-Off Status** | **FINALIZED** |
