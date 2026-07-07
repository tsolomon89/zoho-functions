# Import Contract / Zoho Schema-Alignment Report (v6)

**Template (the recurring import contract):** `Jurnii LTD Pipeline - Copy of Contact.csv`
(111 columns, 260 rows). The CSV header shape is the contract — **adapt Zoho to it**; do not reshape the
CSV. `…- CLEANED.csv` is a throwaway dry-run artifact, NOT the template.

**Guiding principle:** a CSV column existing does **not** mean a Zoho field must exist. Only columns the
v6 engine actually needs become fields. Source/helper columns stay in the template, intentionally unmapped.

The template already resolves the earlier value problems: **no `Contract Signed` Stage**, **no `ERROR`
cells**, `Product Interest` values already canonical. **No CSV value corrections outstanding.**

## Column classification (111)
- **A — maps directly to an existing Lead field by label (92).** Core, geography (Contact AOR / Company
  AOO / Company Expansion), 8 completion timestamps, every A/E/R quote input
  (`Stage / Plan Products / Plan Type / Plan Brands / Plan Frequency / Contract Date Start/End/Renewal /
  ACV`). No action.
- **B — map via manual import mapping (2):** `Company Employee Count → No_of_Employees`,
  `Jurnii Report → Jurnii_Report_Created`.
- **C — Zoho schema change (1):** `Product Interest` — align picklist options to canonical (below).
- **D — preserved in template, intentionally UNMAPPED / not system-required (16):**
  - `State` — informational lifecycle column. Loss is **inferred** (see below), NOT stored in a State
    field. **No State field created** (Zoho also reserves the label "State" for the address field).
  - `Current Job`, `Email Guess`, `Last Contact` — source/helper columns; do not drive the engine → **no
    fields created**.
  - 12 computed quote columns `{Acquisition|Renewal|Expansion} Quote {Target ACV | ACV Gap |
    Contract Date End Days Remaining | Contract Date Renewal Days Remaining}` — engine/formulas are
    authoritative (Target ACV from Company Tier; ACV Gap = Target − Contract ACV; Days Remaining = date
    math). Keep in template, leave unmapped.
- **E — CSV value correction:** none.
- **F — rejected from model:** none.

## Loss / lifecycle (how the engine infers it — verified in code)
processLead does NOT read a `State` field. Loss is inferred from:
1. **Lead `Lost_Reasons`** (`processLead` L57): if set → Contact `State=Lost`/`Status=Closed` and the
   seeded Product Deal `Opportunity_State=Lost`/`Opportunity_Status=Closed` (L452-457, L579-584).
2. **`Renewal Quote Stage = Closed Lost`** → Phase-3 churn sets the Deal Lost +
   `Lost_Reasons="Churned / Did Not Renew"` automatically.

Implication for THIS template (no `Lost_Reasons` column):
- `45 Group - RVBet`(jaime@) + `River Tech` → have `Renewal Quote = Closed Lost` → **auto-churn to Lost**.
- `45 Group - RVBet`(mike@, joao@) + `BoyleSports ×3` → `State=Lost` but no `Lost_Reasons` / no closing
  quote → would import **Open**.
- **Decision (final):** the 5 evidence-less `State=Lost` rows (`45 Group` mike@/joao@, `BoyleSports ×3`)
  **import Open for this load** — `State` alone is NOT an operational loss signal. `State` stays
  preserved-but-unmapped; the engine never infers a reason from it.
- **Future-template rule:** a row imports Lost only with an operational signal —
  (a) `Renewal Quote Stage = Closed Lost` (→ Phase-3 churn stamps `Lost_Reasons = "Churned / Did Not
  Renew"`), or (b) `Lost_Reasons` populated with an approved existing value. Never guess a reason.

## The only Zoho change required
**`Product_Interest` picklist → canonical options** (owner does manually in Zoho UI; no field-metadata
API available). Remove the 6 variant options; final set = `Jurnii UX, Jurnii 360, Jurnii Cortex,
Partnership`. Import setting "automatically add new picklist values" **OFF**. (CSV values already canonical.)

## Guardrails held
No `State`/`Lead State`/`Current Job`/`Email Guess`/`Last Contact` fields created; no new Stage value; no
`Churn / Not Renewed`; no variant `Product_Interest` values; no product+plan Product identities; no
template columns dropped.

## Dry run (after owner fixes Product_Interest)
5 template-shaped rows (FTP Acq, RTP Renewal, churned Renewal-CL, Expansion, multi-product). Validate:
canonical Product_Interest imports with no auto-added values; canonical Account×Product Deals;
`Quote_Product` canonical; plan detail on `Quote_Plan_*`; Closed-Lost Renewal drives churn +
`Lost_Reasons="Churned / Did Not Renew"`; `Current Job`/`Email Guess`/`Last Contact` unmapped (no fields
created); computed columns unmapped; `Account_Status` ≠ `Status`. Clean up, then full 260-row load.
