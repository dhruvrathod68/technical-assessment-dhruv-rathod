# Task 2: Context Handling - Assessment Answers

**Target Document:** `Meridian_Grid_Internal_Dossier.pdf`  
**Generated On:** 2026-09-11 22:41:14  
**Processing Engine:** `pdfplumber` (Pages 1–12) + Windows Native WinRT OCR (Page 13 Appendix B Scanned Memo)

---

## Executive Summary of Solved Questions

| # | Question Focus | Ground Truth Answer | Source Reference |
|---|----------------|---------------------|------------------|
| **1** | Incident with Highest Reconciled Cost & Engineer | **INC-003** (Cost: **INR 61,00,000**), On-Call Engineer: **Kabir Shah** | Section 4 Incident Log (Page 5) |
| **2** | Compliance Risk Vendor & Annual Contract Cost | Vendor: **CloudSentry API**, Annual Cost: **INR 48,00,000** | Section 8.1 Finding 1 & Section 7 Vendor Inventory (Pages 8–9) |
| **3** | Client Receiving Auto-Validator v2 & Monthly Revenue | Client: **Vantage Retail Group**, Monthly Revenue: **INR 6,75,000** | Section 4 (Page 5) & Section 5 Client Portfolio (Page 6) |
| **4** | Founding Head of Security & Exact Tenure Duration | Head of Security: **Naina Kapoor**, Tenure: **2 years, 4 months (28 months total)** (April 2019 – August 2021) | Section 2 (Page 3) & Section 3.1 (Page 4) |
| **5** | Total Severity-Weighted Cost (Firewall Misconfigurations) | Total Weighted Cost: **INR 2,90,10,000** | Section 4 (Page 5) & Section 6.1 Multiplier Table (Page 7) |
| **6** | SentinelWatch SIEM Renewal Date & Approval Chain | Renewal Date: **15 March 2025**, Approval Chain: **Sign-off from the CEO before the Head of Finance & Operations may execute the renewal** | Appendix B Scanned Memo (Page 13 OCR) |

---

## Detailed Question Breakdowns & Verification

### Question 1: Incident with Highest Reconciled Cost
- **Incident ID:** `INC-003`
- **Date:** 2023-04-08
- **Root Cause:** Misconfigured firewall rule during VPN migration
- **Severity Level:** Critical
- **Reconciled Cost:** `INR 61,00,000` (6100000 INR)
- **On-Call Engineer:** `Kabir Shah`
- **Verification Note:** INC-003 triggered mandatory client notification and remains the costliest incident in company history at INR 61,00,000.

---

### Question 2: Compliance Risk Vendor & Annual Cost
- **Flagged Vendor:** `CloudSentry API`
- **Audit Finding:** 8.1 Finding 1 – Vendor Data Residency Risk (High)
- **Compliance Risk Description:** Processes client telemetry data outside India without an adequate DPA, violating contractual data residency commitments.
- **Annual Contract Cost:** `INR 48,00,000` (4800000 INR)
- **Verification Note:** Cross-referencing Audit Finding 8.1 (Page 9) with the Section 7 Vendor Inventory Table (Page 8) verifies that CloudSentry API has an active annual contract cost of INR 48,00,000.

---

### Question 3: Client Receiving "Firewall Rule Auto-Validator v2" Tool
- **Client Name:** `Vantage Retail Group`
- **Tool Delivered:** `Firewall Rule Auto-Validator v2` (Upgraded November 2023 at no extra license fee as part of INC-003 remediation)
- **Deployment Type:** Full SOC + Pen Test Retainer
- **Monthly Revenue:** `INR 6,75,000` (675000 INR)
- **Verification Note:** Section 4 documents the engineering response to INC-003, and Section 5 explicitly connects Vantage Retail Group to this deployment with INR 6,75,000 monthly retainer.

---

### Question 4: Founding Head of Security & Exact Tenure Duration
- **Founding Year:** 2019 (Company founded April 2019 by Aarav Mehta)
- **Head of Security:** `Naina Kapoor`
- **Tenure Start:** April 2019 (Company incorporation)
- **Tenure End:** August 2021 (Departure to venture-backed startup)
- **Exact Duration:** `2 years, 4 months (28 months total)`
- **Verification Note:** Succeeded by Rohan Bhatt in August 2021 as documented in Section 3.1.

---

### Question 5: Total Severity-Weighted Cost of Firewall Incidents
Methodology from Section 6.1:
$$\text{Severity-Weighted Cost} = \text{Reconciled Cost} \times \text{Severity Multiplier}$$

**Incidents with Root Cause "Misconfigured firewall rule":**

1. **INC-001** (2022-06-02):
   - Root Cause: `Misconfigured firewall rule on client edge router`
   - Reconciled Cost: `INR 22,50,000`
   - Severity Tier: `High` (Multiplier: **2.0x**)
   - Weighted Cost: `INR 45,00,000`

1. **INC-003** (2023-04-08):
   - Root Cause: `Misconfigured firewall rule during VPN migration`
   - Reconciled Cost: `INR 61,00,000`
   - Severity Tier: `Critical` (Multiplier: **4.0x**)
   - Weighted Cost: `INR 2,44,00,000`

1. **INC-005** (2024-02-17):
   - Root Cause: `Misconfigured firewall rule on staging environment`
   - Reconciled Cost: `INR 1,10,000`
   - Severity Tier: `Low` (Multiplier: **1.0x**)
   - Weighted Cost: `INR 1,10,000`

**Mathematical Sum:**
$$\text{Total} = 45,00,000 + 2,44,00,000 + 1,10,000 = \mathbf{2,90,10,000\text{ INR}}$$

- **Final Total Severity-Weighted Cost:** `INR 2,90,10,000`

---

### Question 6: SentinelWatch SIEM Renewal Date & Approval Chain
- **Target Contract:** `SentinelWatch SIEM Vendor Contract`
- **Renewal Date:** `15 March 2025`
- **Required Approval Chain:** `Sign-off from the CEO before the Head of Finance & Operations may execute the renewal`
- **Policy Rule:** Any contract renewal exceeding the prior year's value requires sign-off from the CEO before the Head of Finance & Operations may execute the renewal.
- **Signatory:** Aarav Mehta, CEO (18 September 2024)
- **OCR Processing:** Scanned internal memo extracted from Page 13 (Appendix B) and processed with Windows Native WinRT OCR.

```text
MERIDIAN GRID SECURITY PVT LTD INTERNAL MEMO From: Date : This Finance & Operations Aarav Mehta, CEO 18 September 2024 SentinelWatch SIEM Vendor Contract Renewal memo confirms that the SentinelWatch SIEM contract Vendor Inventory, Section 7) is due for renewal on 15 March 2025 Renewal terms have not...
```
