# Import Contract / Zoho Schema-Alignment Report (v6)

**Template (the recurring import contract):** `Jurnii LTD Pipeline - Copy of Contact.csv`
(111 columns, 260 rows). The CSV header shape is the contract — **adapt Zoho to it**, do not
reshape the CSV. `…- CLEANED.csv` from the earlier pass is a throwaway dry-run artifact, NOT the template.

The template already resolves the earlier value problems: **no `Contract Signed` Stage**, **no `ERROR`
cells**, and `Product Interest` values are already canonical. So there are **no CSV value corrections**
outstanding — the work is Zoho-side.

## Column classification (111 cols)
- **A — maps directly to an existing Lead field by label (92 cols).** All core, geography (Contact AOR /
  Company AOO / Company Expansion), 8 completion timestamps, and every A/E/R quote input
  (`Stage / Plan Products / Plan Type / Plan Brands / Plan Frequency / Contract Date Start/End/Renewal /
  ACV`). Import maps these 1:1; no action.
- **B — map via manual import mapping (2 cols):** `Company Employee Count → No_of_Employees`
  (Zoho label "Company Employees Count"); `Jurnii Report → Jurnii_Report_Created` (Zoho label
  "Jurnii Report Created"). Optional: rename the Zoho **labels** to the CSV headers for auto-map.
- **C — Zoho schema change / decision (see "Actions"):** `Product Interest`, `State`, `Current Job`,
  `Email Guess`, `Last Contact`.
- **D — preserve in template, DO NOT map (system-computed) (12 cols):** `{Acquisition|Renewal|Expansion}
  Quote {Target ACV | ACV Gap | Contract Date End Days Remaining | Contract Date Renewal Days Remaining}`.
  These Lead fields exist and are technically writable, but the **engine/formulas are authoritative**
  (Target ACV from Company Tier; ACV Gap = Target − Contract ACV; Days Remaining = date math). Keep the
  columns in the template; leave them **unmapped** at import.
- **E — CSV value correction:** none.
- **F — rejected from model:** none.

## Loss handling (State = Lost)
CSV `State` (Open/Lost) is lifecycle data; there is **no** Lead field labelled "State" (the standard
address field's label is "Address - State / Province", which the `Address - State / Province` column maps
to). 7 rows are `State=Lost`:
- **Renewal churn (auto-handled):** `45 Group - RVBet` (jaime@) and `River Tech` carry
  `Renewal Quote Stage = Closed Lost` → the Phase-3 lifecycle churns the Deal to Lost + stamps
  `Lost_Reasons = "Churned / Did Not Renew"` automatically. No column needed for these.
- **Lost with no quote (needs an explicit path):** `45 Group - RVBet` (mike@, joao@) and
  `BoyleSports ×3` (Proposal Preparation) have `State=Lost` but no Closed-Lost quote → nothing drives
  the loss. These import as **Open** unless the contract carries loss info.

## Proposed minimal Zoho changes (nothing done yet — awaiting sign-off)
1. **`Product_Interest` picklist → canonical options** (manual UI; no API tool for this).
   Remove the 6 variant options; final set = `Jurnii UX, Jurnii 360, Jurnii Cortex, Partnership`.
   Import setting: "automatically add new picklist values" **OFF**. (CSV values already canonical.)
2. **State lifecycle path** — recommended:
   (a) create Lead field **`Lead_State`** (picklist `Open/Lost`) and map CSV `State` → it (captures
   lifecycle on the Lead; header maps cleanly), **and**
   (b) add a **`Lost_Reasons`** column to the template contract (map → `Lost_Reasons`) so any `State=Lost`
   row is deterministically Lost. Populate: renewal-churn → `Churned / Did Not Renew`; ambiguous → report.
   (`Lost_Reasons` picklist already has `Churned / Did Not Renew`.)
3. **Create Lead fields for the 3 no-target columns** (so the template maps fully; `createFields` is
   available): `Current Job` (4 filled), `Email Guess` (27), `Last Contact` (52). Suggested types: text,
   text, date. Or leave unmapped if you'd rather not store them.
4. **B-columns:** either map manually each import, or align the two Zoho labels to the CSV headers.

## Guardrails held
No new Stage value, no `Churn / Not Renewed`, no variant `Product_Interest` values, no product+plan
Product identities, no dropped template columns.

## Then
Dry-run 5 representative rows **from the template shape** (FTP Acq, RTP Renewal, churned Renewal-CL,
Expansion, multi-product) after (1)-(2) land; validate no auto-added picklist values, canonical
Account×Product Deals, `Quote_Product` canonical, plan detail on `Quote_Plan_*`, churn `Lost_Reasons`,
`Account_Status` ≠ `Status`. Clean up, then full 260-row load.
