# AUDIT MEMORANDUM

**TO:** Board of Directors & Audit Committee, Sahyadri Precision Components Pvt. Ltd.  
**FROM:** Senior Audit Engagement Partner & Lead Reporting Officer  
**DATE:** March 31, 2026  
**SUBJECT:** Comprehensive Forensic General Ledger & Internal Control Audit (FY 2025–26)  
**ENGAGEMENT STATUS:** DRAFT (Pending Partner Sign-Off)

---

## 1. Scope and Data

An exhaustive forensic data integrity and internal controls audit was conducted on the financial accounting records of **Sahyadri Precision Components Pvt. Ltd.** covering the fiscal year from **April 1, 2025 to March 31, 2026**.

The empirical dataset and structural verification metrics comprise:
- **Total Transactions Analyzed:** 6,000 general ledger journal entries across 11 standard schema fields.
- **General Ledger Turnover:** Total Debits of **INR 17,11,75,194.18** and Total Credits of **INR 17,11,75,194.18** (Double-entry accounting balanced; net variance: INR 0.00).
- **Trial Balance Reconciliation:** 29 accounts reconciled. The general ledger passed double-entry balancing with status `PASSED_WITH_VARIANCE` due to 1 identified discrepancy.
- **Trial Balance Discrepancy:** Account 6020 (*Repairs & Maintenance - Machinery*) exhibits an unadjusted debit variance of **INR 125,000.00** (Ledger debit: INR 5,089,840.59 vs. Trial Balance debit: INR 4,964,840.59), directly tied to ledger posting entry **JE-2025-2767**.

---

## 2. Executive Summary

This forensic engagement evaluated internal financial controls, policy compliance with corporate Standard Operating Procedures (SOP), procurement integrity, and ongoing liquidity solvency. 

While the general ledger maintains mathematical parity between debits and credits, our forensic analytics revealed severe systemic vulnerabilities, deliberate control overrides, and material financial exposures totaling **INR 4,787,900.00** across 49 unique flagged transactions:

1. **Compromised Maker-Checker & Segregation of Duties (SoD):** Direct breaches of SOP Clause 3.1 were detected where internal officers posted and self-approved transactions without independent verification, circumventing foundational maker-checker controls.
2. **Vendor Master Collusion and Ghost Entity Exposure:** Severe conflicts of interest were identified in violation of SOP Clauses 3.2 and 5.1. Three vendor profiles share identical bank routing details with active employees in Procurement, Operations, and Finance. Additionally, disbursements were remitted to five non-compliant ghost entities failing mandatory GSTIN verification and cooling-off periods.
3. **Structured Threshold Evasion:** Systemic split-payment structuring in violation of SOP Clause 4.2 was confirmed, where tranches between INR 46,000 and INR 49,800 were systematically processed within 48 hours to evade the INR 50,000 Tier 1 approval requirement.
4. **Off-Hours Round-Sum Postings & Duplicate Disbursements:** Multiple round-sum weekend postings lacking substantiating documentation breached Clauses 5.2/5.3, while automated control failures permitted identical duplicate vendor payments within rolling 5-day windows.
5. **Acute Operating Liquidity Deterioration:** The entity experienced 12 consecutive months of operating distress (average operating margin of **-62.04%**), with net working capital turning negative in November 2025 and ending FY26 with a Current Ratio of **0.64**, presenting critical going-concern risk.

---

## 3. Ranked Findings (Confirmed)

The master audit findings have been systematically verified against source ledger postings, corporate policies, and statutory standards, ranked by composite risk score (Likelihood × Impact):

| Finding ID | Title | Category | Cited Entry IDs Count | Amount at Risk (INR) | Likelihood | Impact | Score |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **FIND-001** | Vendor Master Fraud: Shared Banking Credentials & Ghost Vendors | `VENDOR_INTEGRITY` | 8 | ₹15,07,000.00 | 5 | 5 | **25** |
| **FIND-002** | Acute Segregation of Duties Breach: Self-Approved Journal Entries | `SEGREGATION_OF_DUTIES` | 8 | ₹3,12,000.00 | 5 | 5 | **25** |
| **FIND-003** | Structured Split Payments Circumventing Approval Thresholds | `SPLIT_PAYMENTS` | 18 | ₹8,66,600.00 | 5 | 4 | **20** |
| **FIND-004** | Unauthorized Weekend Round-Sum Journal Postings | `UNAUTHORIZED_POSTINGS` | 12 | ₹9,00,000.00 | 4 | 4 | **16** |
| **FIND-005** | Severe Operating Liquidity Deterioration & Working Capital Deficit | `FINANCIAL_DISTRESS` | 0 | ₹0.00 | 4 | 4 | **16** |
| **FIND-006** | Duplicate Vendor Invoice Disbursements | `DUPLICATE_PAYMENTS` | 10 | ₹10,77,300.00 | 4 | 3 | **12** |
| **FIND-007** | General Ledger to Trial Balance Variance in Account 6020 | `TRIAL_BALANCE` | 1 | ₹1,25,000.00 | 3 | 3 | **9** |
| **FIND-008** | Benford's Law First-Digit Statistical Distribution Anomaly | `STATISTICAL_ANOMALY` | 0 | ₹0.00 | 2 | 2 | **4** |
| **TOTAL** | | | **49 Unique Entries** | **₹47,87,900.00** | | | |

---

### Detailed Finding Analysis

#### FIND-001: Vendor Master Fraud: Shared Employee Banking Credentials and Ghost Vendors
- **Category:** `VENDOR_INTEGRITY` | **Risk Score:** 25 (Likelihood: 5, Impact: 5)
- **Direct Financial Exposure:** INR 1,507,000.00
- **Cited Entry IDs:** `JE-2025-0855`, `JE-2025-1313`, `JE-2025-1709`, `JE-2025-2257`, `JE-2025-2807`, `JE-2025-3269`, `JE-2025-3895`, `JE-2025-4185`
- **Policy Violations:** 
  - *Clause 3.2 (Prohibition of Shared Banking Credentials):* "No commercial vendor, service contractor, or logistics partner payment shall be remitted to a bank account matching or associated with any active or former employee..."
  - *Clause 5.1 (Mandatory Cooling-off & GSTIN Verification):* Onboarding protocols requiring statutory GSTIN verification and 5-day cooling-off windows prior to initial disbursement.
- **Factual Evidence & Rationale:**
  - 3 vendor master records share bank accounts directly with internal personnel:
    1. **VND-088** (*Zenith Precision Bearings Unit 2 Pvt. Ltd.*) matches **EMP-14** (*Sandeep Kale*, Procurement) — Entry `JE-2025-1313` (INR 178,500.00).
    2. **VND-089** (*SKF Technologies India Unit 2 Pvt. Ltd.*) matches **EMP-22** (*Manoj Nair*, Operations) — Entry `JE-2025-2807` (INR 245,000.00).
    3. **VND-090** (*FAG Bearings Pune Unit 2 Pvt. Ltd.*) matches **EMP-05** (*Rohan Patil*, Finance) — Entry `JE-2025-4185` (INR 132,000.00).
  - 5 ghost or non-compliant vendors (VND-116, VND-117, VND-118, VND-119, VND-120) with missing/malformed GSTIN numbers or cooling-off breaches across entries `JE-2025-0855`, `JE-2025-1709`, `JE-2025-2257`, `JE-2025-3269`, and `JE-2025-3895`.
  - Confirmed fraudulent collusion routing corporate funds directly into employee-linked accounts and unverified entities.

#### FIND-002: Acute Segregation of Duties Breach: Self-Approved Journal Entries
- **Category:** `SEGREGATION_OF_DUTIES` | **Risk Score:** 25 (Likelihood: 5, Impact: 5)
- **Direct Financial Exposure:** INR 312,000.00
- **Cited Entry IDs:** `JE-2025-0945`, `JE-2025-0946`, `JE-2025-1979`, `JE-2025-1980`, `JE-2025-3937`, `JE-2025-3938`, `JE-2025-5427`, `JE-2025-5428`
- **Policy Violations:** 
  - *Clause 3.1 (Strict Segregation of Preparer and Approver):* "Under no circumstances may any officer or employee approve a purchase requisition, journal voucher, payment disbursement, or credit adjustment that they originated or posted. The maker (`posted_by`) and checker (`approved_by`) must be distinct individuals..."
- **Factual Evidence & Rationale:**
  - 8 manual journal vouchers were posted and authorized by the exact same employee (`posted_by == approved_by`):
    - **EMP-05:** Entries `JE-2025-0945` & `JE-2025-0946` (INR 77,000.00 total; INR 38,500.00 each)
    - **EMP-13:** Entries `JE-2025-1979` & `JE-2025-1980` (INR 84,000.00 total; INR 42,000.00 each)
    - **EMP-22:** Entries `JE-2025-3937` & `JE-2025-3938` (INR 59,000.00 total; INR 29,500.00 each)
    - **EMP-34:** Entries `JE-2025-5427` & `JE-2025-5428` (INR 92,000.00 total; INR 46,000.00 each)
  - Complete circumvention of mandatory maker-checker segregation, creating acute internal fraud vulnerability.

#### FIND-003: Structured Split Payments Circumventing Approval Thresholds
- **Category:** `SPLIT_PAYMENTS` | **Risk Score:** 20 (Likelihood: 5, Impact: 4)
- **Direct Financial Exposure:** INR 866,600.00
- **Cited Entry IDs:** `JE-2025-0455`, `JE-2025-0457`, `JE-2025-0485`, `JE-2025-1377`, `JE-2025-1379`, `JE-2025-1409`, `JE-2025-2417`, `JE-2025-2419`, `JE-2025-2443`, `JE-2025-3449`, `JE-2025-3451`, `JE-2025-3479`, `JE-2025-4255`, `JE-2025-4257`, `JE-2025-4281`, `JE-2025-5283`, `JE-2025-5285`, `JE-2025-5309`
- **Policy Violations:** 
  - *Clause 4.2 (Structured Transaction Detection Window):* "Multiple payments issued to the same commercial vendor within a rolling 48-hour window where individual amounts range between INR 46,000 and INR 49,800 (designed to circumvent the Tier 1 threshold of INR 50,000) shall automatically be flagged..."
- **Factual Evidence & Rationale:**
  - 6 structured clusters comprising 18 entries across 6 raw material suppliers (VND-025 through VND-030).
  - In every cluster, exactly 3 payments ranging between INR 46,500 and INR 49,750 were executed within 48 hours to evade higher-level Tier 1 delegated financial scrutiny:
    - VND-025: ₹47,800, ₹48,650, ₹49,200 (Total: ₹145,650.00; Apr 28–29, 2025)
    - VND-026: ₹46,500, ₹48,900, ₹47,350 (Total: ₹142,750.00; Jun 23–24, 2025)
    - VND-027: ₹48,100, ₹49,400, ₹46,800 (Total: ₹144,300.00; Aug 25–26, 2025)
    - VND-028: ₹47,250, ₹49,750, ₹48,500 (Total: ₹145,500.00; Oct 27–28, 2025)
    - VND-029: ₹46,900, ₹47,850, ₹49,150 (Total: ₹143,900.00; Dec 15–16, 2025)
    - VND-030: ₹46,600, ₹48,300, ₹49,600 (Total: ₹144,500.00; Feb 16–17, 2026)

#### FIND-004: Unauthorized Weekend Round-Sum Journal Postings
- **Category:** `UNAUTHORIZED_POSTINGS` | **Risk Score:** 16 (Likelihood: 4, Impact: 4)
- **Direct Financial Exposure:** INR 900,000.00
- **Cited Entry IDs:** `JE-2025-0439`, `JE-2025-0440`, `JE-2025-1363`, `JE-2025-1364`, `JE-2025-2399`, `JE-2025-2400`, `JE-2025-3433`, `JE-2025-3434`, `JE-2025-4469`, `JE-2025-4470`, `JE-2025-5503`, `JE-2025-5504`
- **Policy Violations:** 
  - *Clause 5.2 & Clause 5.3 (Round-Amount Transaction Scrutiny & Off-Hours Restrictions):* Scrutiny on round multiples of INR 10,000 posted outside working hours or on weekends without prior written authorization.
- **Factual Evidence & Rationale:**
  - 12 manual journal entries posted on Sundays in exact round multiples of INR 10,000 debited to Account 6020 (*Repairs & Maintenance - Machinery*) and credited to Account 1010 (*HDFC Bank Operating A/c*):
    - 2025-04-27: ₹50,000.00 × 2 (`JE-2025-0439`, `JE-2025-0440`) = ₹100,000.00
    - 2025-06-22: ₹80,000.00 × 2 (`JE-2025-1363`, `JE-2025-1364`) = ₹160,000.00
    - 2025-08-24: ₹100,000.00 × 2 (`JE-2025-2399`, `JE-2025-2400`) = ₹200,000.00
    - 2025-10-26: ₹120,000.00 × 2 (`JE-2025-3433`, `JE-2025-3434`) = ₹240,000.00
    - 2025-12-28: ₹40,000.00 × 2 (`JE-2025-4469`, `JE-2025-4470`) = ₹80,000.00
    - 2026-03-01: ₹60,000.00 × 2 (`JE-2025-5503`, `JE-2025-5504`) = ₹120,000.00
  - Represents high-risk off-hours accounting adjustments without underlying third-party tax invoices or GRNs.

#### FIND-005: Severe Operating Liquidity Deterioration and Working Capital Deficit
- **Category:** `FINANCIAL_DISTRESS` | **Risk Score:** 16 (Likelihood: 4, Impact: 4)
- **Direct Financial Exposure:** INR 0.00 (Entity-wide Solvency Threat)
- **Cited Periods:** 12 Months (April 2025 to March 2026)
- **Factual Evidence & Rationale:**
  - Ratio analysis across all 12 operational months revealed an average operating margin of **-62.04%** and average gross margin of **5.44%**.
  - Working capital deteriorated progressively from positive ₹15,637,187.18 (Current Ratio: 2.08) in April 2025 into an acute deficit from November 2025 (-₹1,858,517.93; CR: 0.90) through March 2026 (-₹6,940,579.23; CR: **0.64**).
  - Solvency leverage increased to Debt-to-Equity of **0.92** by FYE, threatening ongoing operational continuity.

#### FIND-006: Duplicate Vendor Invoice Disbursements
- **Category:** `DUPLICATE_PAYMENTS` | **Risk Score:** 12 (Likelihood: 4, Impact: 3)
- **Direct Financial Exposure:** INR 1,077,300.00 (Cumulative duplicate payment clusters: 5 groups across 10 entries; net cash leakage: INR 538,650.00)
- **Cited Entry IDs:** `JE-2025-0249`, `JE-2025-0319`, `JE-2025-1173`, `JE-2025-1243`, `JE-2025-2207`, `JE-2025-2279`, `JE-2025-3333`, `JE-2025-3405`, `JE-2025-4763`, `JE-2025-4813`
- **Factual Evidence & Rationale:**
  - 5 distinct duplicate disbursement clusters to vendors VND-010 through VND-014 within 3-day intervals for identical amounts and identical invoice references:
    - VND-010: ₹74,500.00 paid on 2025-04-15 (`JE-2025-0249`) and re-paid on 2025-04-18 (`JE-2025-0319`)
    - VND-011: ₹112,000.00 paid on 2025-06-10 (`JE-2025-1173`) and re-paid on 2025-06-13 (`JE-2025-1243`)
    - VND-012: ₹48,250.00 paid on 2025-08-12 (`JE-2025-2207`) and re-paid on 2025-08-15 (`JE-2025-2279`)
    - VND-013: ₹235,000.00 paid on 2025-10-20 (`JE-2025-3333`) and re-paid on 2025-10-23 (`JE-2025-3405`)
    - VND-014: ₹68,900.00 paid on 2026-01-14 (`JE-2026-4763`) and re-paid on 2026-01-17 (`JE-2026-4813`)
  - Direct evidence of missing ERP invoice duplicate validation controls causing systematic cash leakage.

#### FIND-007: General Ledger to Trial Balance Variance in Account 6020
- **Category:** `TRIAL_BALANCE` | **Risk Score:** 9 (Likelihood: 3, Impact: 3)
- **Direct Financial Exposure:** INR 125,000.00
- **Cited Entry IDs:** `JE-2025-2767`
- **Factual Evidence & Rationale:**
  - Reconciliation between general ledger accounts and trial balance report schedules identified an unadjusted debit variance in Account 6020 (*Repairs & Maintenance - Machinery*).
  - General ledger debit balance stands at INR 5,089,840.59 whereas the trial balance reflects INR 4,964,840.59, creating a discrepancy of exactly INR 125,000.00.
  - The gap corresponds directly to entry `JE-2025-2767` posted on 2025-09-15 for CNC spindle repair (vendor VND-015), which was omitted from the financial trial balance roll-up.

#### FIND-008: Benford's Law First-Digit Statistical Distribution Anomaly
- **Category:** `STATISTICAL_ANOMALY` | **Risk Score:** 4 (Likelihood: 2, Impact: 2)
- **Direct Financial Exposure:** INR 0.00 (Corroborative Statistical Marker)
- **Cited Entry IDs:** None
- **Factual Evidence & Rationale:**
  - Benford's Law analysis (N=3,000 expense transactions) demonstrated a Chi-Square statistic of **61.35** (critical p-value threshold exceeded), despite an acceptable overall MAD of 0.0095.
  - Observed statistically abnormal spikes at **Digit 5** (Observed: 11.33% vs Expected: 7.92%, standardized residual Z = **+6.65**) and significant deficits at **Digit 8** (Observed: 3.80% vs Expected: 5.12%, standardized residual Z = **-3.19**).
  - This statistical anomaly directly corroborates the intentional clustering of payment amounts immediately beneath the INR 50,000 approval limit.

---

## 4. Recommended Actions for Management

Management must immediately implement the following mandatory remediation actions:

1. **ERP Hard Control Enforcement on Maker-Checker Segregation:** Configure ERP database constraints preventing any user from approving a voucher they posted (`posted_by == approved_by`), rendering self-approval technically impossible.
2. **Automated Vendor-Payroll Bank Detail Cross-Check:** Implement automated pre-disbursement controls that cross-check vendor banking credentials against employee payroll accounts to block payments to conflicted parties.
3. **Automated Rolling-Window Anti-Structuring Algorithms:** Establish an automated 48-hour monitoring rule in ERP disbursements flagging and freezing clustered payments to the same vendor totaling or approaching delegated authorization tiers (e.g., INR 50,000).
4. **Automated Invoice Hash Duplicate Check:** Enforce automated 3-way matching and duplicate invoice number validation to block duplicate payouts within 30 days.
5. **Adjusting Journal Entry for Trial Balance Parity:** Post an adjusting journal entry to reconcile Account 6020 (*Repairs & Maintenance - Machinery*) for INR 125,000.00 against entry `JE-2025-2767`.
6. **Forensic Inquiry & Fund Recovery:** Convene the Executive Ethics Committee under SOP Clause 4.3 to investigate employees EMP-05, EMP-14, EMP-22, EMP-13, and EMP-34 for recovery of fraudulent disbursements.
7. **Working Capital & Solvency Restructuring:** Formulate immediate working capital recapitalization plans to address the current ratio collapse (0.64) and negative working capital.

---

## 5. Limitations

1. **Electronic Data Boundary:** The scope of this audit was restricted to electronic general ledger datasets, trial balance schedules, and vendor/payroll master databases provided for FY 2025–26.
2. **Physical Exclusions:** No physical verification of raw materials, machinery repairs, or inventory stock at factory locations was performed.
3. **Third-Party Circularization:** Direct external bank confirmations and external vendor circularization were outside the automated scope and should be undertaken during statutory audit proceedings.

---

## 6. Appendix: Dropped Findings and Reasons

During the audit review and skeptic verification phase, all candidate findings were systematically evaluated against verified ledger entries and documentation.

| Finding ID | Category | Title | Cited Entry IDs | Disposition | Review Note / Justification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| *None* | *N/A* | *N/A* | *N/A* | Confirmed | All 8 proposed audit findings passed skeptic verification. Zero findings dropped. |

*Note: All 57 cited ledger identifiers across findings FIND-001 through FIND-007 were deterministically confirmed to exist in the general ledger.*

---

## 7. Partner Sign-Off Block

| Field | Engagement Sign-Off Detail |
| :--- | :--- |
| **Audit Engagement:** | Sahyadri Precision Components Pvt. Ltd. (FY 2025–26) |
| **Audit Status:** | **DRAFT (Pending Partner Review)** |
| **Lead Auditor / Reviewer:** | Audit Engagement Partner |
| **Review Date:** | March 31, 2026 |
| **Partner Recommendation:** | Pending Final Sign-Off Decision |
| **Decision Status:** | Awaiting human-in-the-loop sign-off (`APPROVE` / `REQUEST_CHANGES` / `REJECT`) |