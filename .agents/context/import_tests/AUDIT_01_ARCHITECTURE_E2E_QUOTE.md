> **⚠ SUPERSEDED IN PART BY [AUDIT_00_REVISION_R1.md](AUDIT_00_REVISION_R1.md) (2026-06-22).** The pricing statements below are **wrong**: the Quote line price is the banded **matrix** value (Line ACV = PPB × brand count), **not** `Product.Unit_Price`. Ignore the "£12,000 / £8,400" framing in §A.3 and §G and the "plan type + brand count" minimum in §C — see R1 §1. Defects D1/D2/D4 now have repo fixes (R1 §2) but are **not deployed**. Read R1 first.

# Jurnii Zoho CRM — Pre-Import Audit, Part 1: Architecture, E2E Test, Quote Model

**Date:** 2026-06-22 · **Org:** Jurnii.io (org20114906201, GBP £, Europe/London) · **Edition:** CRM Plus **trial, expires 2026-06-25**
**Scope:** Validate the deployed v6 automation end-to-end and reconcile it against the repo before a one-time manual import of MQL/SQL/FTP/RTP commercial data. **No CSV rows were imported. No production records were created from the CSVs.** Live test records were created with synthetic data and fully deleted (see §B).

---

## 0. Executive summary

**The durable Lead→Contact→Account→Deal→Contact-Role lifecycle works.** A controlled live test proved auto-conversion, Account/Deal de-duplication by `Account_Key`, Contact-Role creation, primary-contact selection, Opportunity-Type derivation, and stage roll-up all function. **Four defects** were found, two of which materially affect a bulk import.

| # | Severity | Defect (observed live) | Import impact |
|---|---|---|---|
| D1 | **High** | Every auto-converted Lead creates the activation Task **twice** (explicit `processContact` call *and* the WF001b2 "Contact create" workflow both fire). | ~2× activation Tasks: MQL alone ≈ 348 tasks for 174 leads. |
| D2 | **High** | The activity(Task)→Quote path **did not create a Quote** in test, though the handler ran and `processDeal` reported success. The team's own 09:48 "Atomic Quote Proof" Quote exists, so `processDeal`'s write works — the **Task→`processDeal` product-context handoff** is the suspect. | Durable workflow **cannot be relied on to backfill Quotes**; Quote creation must be an explicit supervised step. |
| D3 | Medium | Deal stage roll-up **lags on bulk create**: when a 2nd contact at a higher stage converts, the Deal did not advance until a re-touch (eventual-consistency on the Account→Contacts related list). | After bulk auto-conversion, Deals need a **settling re-touch pass**. |
| D4 | Medium | `Product Interest` does **not** propagate from Lead → `Contact.Product_Interest_Staging` / `Deal.Product_Interest_Staging` on conversion. | Product-interest signal captured on the Lead/CSV is lost; doesn't seed the quote-product aggregation. |
| Drift | Low | `processLead` reads several **non-existent legacy Lead fields** (`Contract_Start_Date`, `Contract_ACV_Intial`, `Personal_Phone`, `Role_AOR`, `Product_Interest1`); the live Lead schema uses `Contract_Initial_*`, etc. Reads are null-guarded (no crash) but Lead-borne contract data never seeds the Deal. | Low for these CSVs (contract columns are empty), but real drift. |

**Go / No-Go for the import itself:** The CSV→**Leads** import is **safe to run with automation disabled** (see Part 3 runbook). The *auto-conversion cascade* is where D1–D4 bite, so conversion should be a **controlled, post-import, batched** step — not triggered en masse during import.

**Decision on a Lead "Quote/Contract Stage" field (Section 12): NOT required — do not create it.** Rationale in §C.9.

---

## A. Current-state architecture audit

### A.1 Module topology (53 modules; commercial graph)
| Module | API | Role | Notes |
|---|---|---|---|
| Leads | `Leads` | Intake/staging; **convertable** | Auto-converted by `processLead` on create/edit (WF001a). |
| Accounts | `Accounts` | Durable company; 1 principal Deal | `Account_Key` (text) is the dedup key. |
| Contacts | `Contacts` | Durable people | `Stage/State/Status`, `Contact_Role1`, completion timestamps, `Products_Linked`, `Product_Interest_Staging`. |
| Deals | `Deals` | Principal commercial relationship | `Stage`=Opportunity **Type**; `Opportunity_Stage`; `Opportunity_State/Status`; `Deal_Key`. |
| Quotes | `Quotes` | Per-product commercial document | `Quote_Stage`, `Opportunity_Type` (**FTP/RTP only**), `Quote_Product`→Products. |
| Quoted_Items | `Quoted_Items` (**subform** of Quotes) | Line items | `Product_Name`→Products, `Quoted_Item_Pricing_Band/Tier/Frequency/Plan_Brands`. |
| Products | `Products` | Catalogue (6 active SKUs) | `Product_Plan_Products` × `Product_Plan_Type`. |
| Contact Roles | (native Deals related list) | Deal↔Contact roles | Decision Maker / Influencer / End User. |
| Leads_X_Products / Contacts_X_Products | linking | Lead/Contact↔Product M:N | backs `Products_Linked`. |

### A.2 Canonical commercial fields (deployed)
- **Deals.`Stage`** (relabelled **"Opportunity Type"**, mandatory): `Qualification, MQL, Needs Analysis, SQL, Value Proposition, FTP, Identify Decision Makers, RTP, Proposal/Price Quote, Negotiation/Review, Closed Won, Closed Lost, Closed Lost to Competition` (Jurnii uses MQL/SQL/FTP/RTP).
- **Deals.`Opportunity_Stage`** / **Contacts.`Stage`** / **Leads.`Stage`** (identical 8-value picklist): `Marketing Consent, Demo Booking, Demo Confirmation, Demo Hosted, Proposal Preparation, Commercial Agreement, Onboarding, Renewal`.
- **State**: `Open / Won / Lost` — on **Contacts.State, Accounts.State, Deals.Opportunity_State** (Deals use `Opportunity_State`; **Leads have NO commercial State** — `Leads.State` is the geographic address state).
- **Status**: `New / Working / Closed` — Contacts.Status, Accounts.Status, Deals.`Opportunity_Status`, **Leads.Status**.
- **`Pipeline`** (Deals, mandatory): `B2B / Partnership` — defaults to B2B in automation.

> **⚠ Ontology drift vs the task brief.** The brief's canonical table ranks stage 1 as **"Marketing Qualification"** for MQL. The **deployed** picklist's first value is **"Marketing Consent"** — there is **no "Marketing Qualification" option**. The MQL CSV correctly uses **"Marketing Consent"**, which matches the deployed metadata. The completion-timestamp field is still named `…Marketing_Qualification_At` (mapped to the "Marketing Consent" stage in code). **Use "Marketing Consent" for import.** Recommend NOT renaming (per prior decision in repo memory).

### A.3 Products (Deliverable G source) — 6 active SKUs, all `Product_Active=true`, GBP
| Product_Name | Product_Code | `Product_Plan_Products` (line) | `Product_Plan_Type` | Unit_Price | `Active_for_Deal_Auto` | `Product_Mapping_Aliases` |
|---|---|---|---|---|---|---|
| Jurnii 360 - Fixed | J360-FIX | Jurnii 360 | Fixed | £10,000 | false | (none) |
| Jurnii 360 - Flex | J360-FLX | Jurnii 360 | Flex | £10,000 | false | (none) |
| Jurnii UX - Fixed | JUX-FIX | Jurnii UX | Fixed | £12,000 | false | (none) |
| Jurnii UX - Flex | JUX-FLX | Jurnii UX | Flex | £8,400 | false | (none) |
| Jurnii Cortex - Fixed | JCX-FIX | Jurnii Cortex | Fixed | £16,000 | false | (none) |
| Jurnii Cortex - Flex | JCX-FLX | Jurnii Cortex | Flex | £16,000 | false | (none) |

- Product resolution in `processDeal` matches on **exact `Product_Name`** (lowercased), then **`Product_Code`** fallback; duplicates/unresolved → Manual Review. It filters on **`Product_Active`** (true on all 6) — **not** `Active_for_Deal_Auto` (so that flag being false everywhere is harmless/unused).
- `Product_Mapping_Aliases` is **empty on all 6** — so there is **no alias coverage** for the line-level names ("Jurnii UX") the CSVs use. (See G/recommendation.)
- Banded pricing is **materialised on Quoted_Items**, not on Product records: `Quoted_Item_Pricing_Band` = {5,7,10,15,20,50,100}, `Quoted_Item_Pricing_Tier` = {Base, Markup, Agency}, computed by `_util_resolveQuoteLinePrice`. Requires a **brand count** to price.

### A.4 Workflows (19 rules) — cutover state matches intent
| Rule | Module | Trigger | Fn | Active | Note |
|---|---|---|---|---|---|
| WF001a Process Lead | Leads | create_or_edit (repeat) | processLead | ✅ | **auto-converts** |
| WF001b0 Process Contact | Contacts | field_update (Stage/State/Status/Role/Account) | processContact | ✅ | |
| WF001b2 Process Contact | Contacts | **create** | processContact | ✅ | **co-cause of D1 dup task** |
| WF001c Process Account | Accounts | create_or_edit (repeat) | processAccount | ✅ | |
| WF001d Process Deal | Deals | create_or_edit (repeat) | processDeal (`"{}"`) | ✅ | reconcile-only, no quote create |
| WF004 Commercials Status | Deals | field_update Commercials_Status | handleCommercialsStatusChange | ✅ | legacy bridge (keep until WF021 verified) |
| WF006 Call Outcome | Calls | anyaction | handleCallOutcome | ✅ | |
| WF007 Event Meeting | Events | create_or_edit | handleMeetingEvent | ✅ | |
| WF008 Task Completion | Tasks | create_or_edit | handleTaskCompletion | ✅ | |
| WF009a–e Email events | Emails | mail_* | handleEmail* | ✅ | |
| WF010c/WF010d Date routers | Deals | date | sendDemoReminder / sendCommercialFollowUp | ✅ | |
| WFC-SchedEmail | Tasks | date (Due_Date) | sendScheduledEmailFromTask | ✅ | |
| WF020 Quotes | Quotes | field_update Quote_Stage | (legacy) | ✅ | legacy, keep until WF021 verified |
| **WF021 Quotes Create/Edit** | Quotes | create_or_edit | handleQuoteStageChange | **❌ inactive** | **correct** (gated; pre-cutover) |

This matches `docs/v6/FLOW_REFERENCE.md`: WF021 inactive, WF020 + WF004 active. **No workflow drift.**

### A.5 Functions (18 workflow-bound, deluge) — present and associated
processLead, processContact, processAccount, processDeal, handleTaskCompletion, handleCallOutcome, handleMeetingEvent, handleCommercialsStatusChange, handleQuoteStageChange, handleEmail{Replied,Bounced,NotReplied,OpenedNotReplied,Clicked} + core handleEmailEvent, sendDemoReminder, sendCommercialFollowUp, sendScheduledEmailFromTask. Helper functions (`_util_resolveQuoteLinePrice`, `createAuxTask`, `routeContactSequence`, `applyCommercialTransition`, `_util_*`) are invoked via the `automation.*` namespace (standalone, not in the workflow-bound list). Repo `*.ORPHANED.deluge` (ensureDealQuote, syncConfirmedQuoteToDeal, _util_resolveQuotePlanSummary) are correctly **not deployed** (folded into `processDeal`).

> **Note:** `processDeal` (deployed) was modified **2026-06-22 12:47**, *after* the latest repo commit `2f79052` — the deployed copy may be ahead of the repo. Treat the deployed function as source-of-truth for behaviour; reconcile the repo after this work.

### A.6 Repo ↔ deployed drift summary
| Area | Repo | Deployed | Verdict |
|---|---|---|---|
| Workflow cutover state | WF021 off / WF020+WF004 on | same | ✅ aligned |
| `processLead` Lead-field reads | `Contract_Start_Date`, `Contract_ACV_Intial`, `Personal_Phone`, `Role_AOR`, `Product_Interest1` | **none of these exist on Leads** (schema uses `Contract_Initial_*`, no personal phone/role_aor) | ⚠ drift — null-guarded, but Lead contract data never seeds Deal |
| `Product_Interest_Staging` | read on Contacts/Deals; written by processLead | exists on **Contacts** & **Deals**; **not on Leads** | ✅ exists where written; but D4 shows it isn't populated on convert |
| Function timestamps | repo HEAD older | deployed edited 2026-06-21/22 | ⚠ deployed ahead of repo — re-sync repo |
| Products | 6 SKUs expected | 6 SKUs present, active | ✅ |

---

## B. End-to-end test report (live, synthetic data, cleaned up)

All records used clearly-synthetic data (`ZZE2E…`, domains `*.example`) and were **deleted at the end** (verified: 0 `zze2e-%` Accounts remain). Workflows were triggered (`trigger:["workflow"]`) to exercise the real path.

| # | Scenario | Input | Expected | Actual | Result |
|---|---|---|---|---|---|
| T1 | MQL new company | Lead: Company "ZZE2E Alpha", domain `zze2e-jun22a.example`, Stage=Marketing Consent, Job_Title "Head of Product", PI=["Jurnii UX - Fixed"] | Auto-convert → Account+Contact+Deal; role=Decision Maker; Deal MQL/Marketing Consent | Account `…680003` (Account_Key=domain), Contact `…680005` (Decision Maker ✓), Deal `…730001` (Stage=**MQL**, Opp_Stage=Marketing Consent, Pipeline=B2B, primary set, Amount null) | **PASS** (+ D1, D4) |
| T2 | 2nd contact same domain, higher stage | Lead: "ZZE2E Beta", same domain, Stage=Demo Booking, Job_Title "Head of CRM" | Same Account+Deal (no dup); 2 Contacts + 2 Roles; Deal rolls to SQL/Demo Booking; primary→beta | **No dup** Account/Deal ✓; 2 Contacts + 2 Roles ✓; **but Deal stayed MQL/Marketing Consent** until re-touch | **PARTIAL** (D3) |
| T3 | Re-trigger (settling) | Touch Deal (edit) | Deal advances; roles not duplicated | Deal → **SQL / Demo Booking / primary=beta** ✓; still exactly 2 Roles (idempotent) ✓ | **PASS** |
| T4 | FTP derivation | Lead "ZZE2E Gamma", domain `zze2e-gamma.example`, Stage=Proposal Preparation, CCO | Deal=FTP / Proposal Preparation | Deal `…730009` Stage=**FTP**, Opp_Stage=Proposal Preparation ✓ (single-contact, settled at convert) | **PASS** |
| T5 | Activity→Quote | "Draft Commercials" Task on Gamma Deal: Task_State=Won, Outcome=Completed, Task_Contract_Products=["Jurnii UX - Fixed"], Brands=5 | Draft Quote (Opp_Type=FTP) + Quoted_Item + product linked to Deal | Handler ran (Task→Closed, "Send Commercials" task surfaced, success), **but NO Quote, NO Deal-Product link, Amount null** | **FAIL** (D2) |
| T6 | Idempotent roles / no-dup on re-entry | (covered by T3) | re-run doesn't duplicate roles | confirmed no role duplication | **PASS** |

**Confirmed working:** auto-conversion; Account de-dup via `Account_Key` (normalized domain); Deal de-dup via `Deal_Key` (`domain::active`); one Account→one Deal→many Contacts; Contact-Role creation with title→role mapping (Head of Product/CRM/CCO → Decision Maker); primary-contact furthest-open selection with role tiebreak; Opportunity-Type derivation by stage rank (rank≥7 RTP, ≥5 FTP, ≥2 SQL, else MQL); never-regress stage; no premature Quote at MQL/SQL; Pipeline default B2B.

**Failure/retry observations:** No function failures were logged during testing (`getAutomationFunctionFailures` = 0). Re-triggering `processDeal` (T3) is **idempotent** for Contact Roles and stage. The **lag (D3)** means a single settling pass is needed after bulk conversion.

### Defects & corrections
I **did not hot-patch** the deployed functions: D2/D4 root-causes need the execution log to confirm, and editing 1,600-line production functions immediately before a migration is higher-risk than the defects themselves. None of D1–D4 block the **CSV→Leads** import (they bite only on auto-conversion, which the runbook defers and controls). Recommended fixes:

- **D1 (dup activation task):** make activation-task creation idempotent (dedupe on open `Sequence Activation` task per Contact+Stage), **or** drop the explicit `processContact` call in `processLead` and rely solely on WF001b2, **or** disable WF001b2 and keep the explicit call. Lowest-risk: add an idempotency guard in `createAuxTask`/activation. Retest by converting one Lead and asserting exactly 1 activation task.
- **D2 (activity→Quote):** instrument `processDeal` entry to log the received `contextJson` and the parsed `products` list; confirm whether `taskActivityCtx.toString()`→`raw.toMap()` preserves the `products` array. Fix the serialization/handoff, then re-run T5 and assert a Draft Quote with one Quoted_Item.
- **D3 (rollup lag):** add a deterministic settling re-touch (the runbook's post-conversion pass) **or** have `processContact` re-invoke `processDeal` after a short guard when a sibling Contact was just added.
- **D4 (PI propagation):** in `processLead`, the multiselect `Product_Interest` parse yields empty in practice; align it to read the live `Product_Interest` multiselect correctly and write `Contact.Product_Interest_Staging`. Retest by converting a Lead with PI set and asserting `Contact.Product_Interest_Staging` is populated.
- **Drift:** repoint `processLead`'s contract/personal reads to the live field names (`Contract_Initial_Date_Start`, `Contract_Initial_ACV`, …) or remove dead reads; re-sync repo with the deployed functions.

---

## C. Quote architecture report (answers to Section 11/13/14 + the 12 questions)

**How Quotes are created (durable path):** `processDeal` creates Quotes **only** when invoked with `source=="activity"` — i.e. a Task/Call/Meeting carrying **Product picklist values** fires its handler (WF006/7/8) which calls `processDeal(dealId, {source:activity, products:[…], numberOfBrands, contractDate*})`. A plain Deal create/edit (WF001d, context `"{}"`) **reconciles existing Quotes only** (recompute Amount, ledger, roles, stage) and **never creates** a Quote. → **Quote creation is driven by activity product-evidence, gated to FTP/RTP, not by stage alone.**

1. **Is Product Interest sufficient to identify Products?** Partially. The *concept* maps cleanly, but the CSV/Lead-level value is **line-level** ("Jurnii UX") while Products are **SKUs** ("Jurnii UX - Fixed/Flex"). One line → **two** SKUs. Not sufficient alone without a **plan type** (Fixed/Flex).
2. **Does Product Interest resolve deterministically?** **No, not at SKU level.** "Jurnii UX" is ambiguous between `JUX-FIX` (£12,000) and `JUX-FLX` (£8,400). Deterministic only once Fixed/Flex is chosen. The CSVs carry **no** Fixed/Flex signal (`Contract_*_Plan_Type` columns are empty; the `Type` column is Brand/Agency/Platform, not plan type).
3. **Does each Product contain sufficient Quote data?** Yes for the SKU once chosen: `Unit_Price`, `Product_Code`, `Product_Active`, currency (org GBP), taxable. Banded/tiered amounts are computed onto the Quoted_Item from a **brand count** (`_util_resolveQuoteLinePrice`).
4. **Product-derived Quote fields:** `Quote_Product`, line `Product_Name`, `List_Price` (from Unit_Price/banded), tax, code, description.
5. **Calculated:** `Quoted_Items.Total`, Quote `Sub_Total`, `Grand_Total`, `Total_After_Discount` (Zoho formulas); Deal `Amount` (= Σ non-Closed-Lost quote totals, by `processDeal`).
6. **Defaulted:** `Quote_Stage`=Draft (on create), currency=org GBP, `Quoted_Item_Pricing_Tier`=Base, Quantity=1, `Opportunity_Type`=FTP/RTP (from Deal floor), `Account_Name`/`Deal_Name`/`Contact_Name` from the Deal.
7. **Require explicit input (non-derivable):** **plan type (Fixed/Flex)**, **number of brands** (drives price band), **contract Start/End dates** (required to *Confirm*), negotiated/manual price only when it overrides the banded value.
8. **When should a Quote be created?** When **FTP/RTP** product evidence exists. Baseline confirmed: Product Interest → Products selection; a **commercial activity/outcome** (Draft/Send Commercials, or a Demo→commercial outcome) at **Proposal Preparation** onward triggers creation. MQL/SQL are **not** quote-eligible (`Quotes.Opportunity_Type` only allows FTP/RTP).
9. **Does the Lead need a Quote/Contract Stage field? → NO (Section 12 decision).**
   - The Lead is **intake-only and auto-converts immediately**, so any Lead-level quote/contract stage is stale within seconds and is never the authority.
   - `Opportunity_Stage = Proposal Preparation` already means "prepare a quote"; `Commercial Agreement` means "quote sent/closing". Quote lifecycle belongs on **Quotes.Quote_Stage** (authoritative) with the **Deal** aggregating.
   - A Deal can have **multiple** Quotes; a single Lead field can't represent them.
   - The CSV's only quote/contract-ish values are the FTP **"Contract Signed"** stage (2 rows) and the RTP **"Renewal"** stage — both are representable by existing `Opportunity_Stage` (map "Contract Signed"→Commercial Agreement) plus a **post-import Quote backfill**, not a new Lead field.
   - **Recommendation: do not add a Lead Quote/Contract Stage field.** If reporting later needs a coarse "contract state", put it on **Accounts** (`Account_Status` already exists: Prospect/Active Customer/Existing Client/Partner/Churned) or the **Deal**, never the Lead.
10. **Authoritative module after conversion:** **Quotes** for quote lifecycle/amounts; **Deal** for the aggregate commercial state (Amount, Opportunity_Stage/Type, contract ledger); **Account** for customer status. The Lead is discarded (converted).
11. **Multiple Quotes:** keyed by **Deal + `Quote_Product` + `Opportunity_Type`**; `Quote_Last_Deal_ID` + `Quote_Applied_Activity_Keys` provide reconciliation/idempotency; Confirmed/Closed Won/Closed Lost are protected from activity overwrite; Deal Amount = Σ non-Closed-Lost.
12. **Automation changes required before relying on durable Quote creation:** fix **D2** (activity→Quote handoff) and add **alias/΄plan-type resolution** so a line-level interest can resolve to a SKU (see G). Until then, **Quote creation/backfill must be explicit and supervised** (Part 3).

---

## G. Product mapping report (Product Interest → Products)

**Implementation:** `Leads.Product_Interest` = multiselect **picklist** of **SKU names** (matches `Products.Product_Name`). `Contacts` carry interest via `Products_Linked` (multiselect lookup) + `Product_Interest_Staging` (text). Activity evidence carries **Product-name strings**. `processDeal` resolves name→Product (exact, then code), links to Deal/Contact, and upserts one Quote per Product.

**The CSV `Product Interest` values are line-level and do NOT match the SKU picklist:**

| CSV value (token) | Occurrences (SQL+RTP+MQL) | Valid `Leads.Product_Interest` (SKU)? | Matches `Contract_*_Plan_Products` (line)? | Resolves to Product SKU? |
|---|---|---|---|---|
| `Jurnii UX` | 48 | ❌ (needs `- Fixed`/`- Flex`) | ✅ | Ambiguous → `JUX-FIX` (£12k) or `JUX-FLX` (£8.4k) |
| `Jurnii 360` | 18 | ❌ | ✅ | Ambiguous → `J360-FIX`/`J360-FLX` (both £10k → amount identical) |
| `Jurnii Cortex` | 5 | ❌ | ✅ | Ambiguous → `JCX-FIX`/`JCX-FLX` (both £16k → amount identical) |

- **No misspellings, no legacy names, no inactive products, no duplicate product names** in the catalogue. The only issue is **granularity** (line vs SKU) and the resulting **Fixed/Flex ambiguity**.
- For 360 and Cortex the Fixed/Flex price is identical, so the ambiguity is **price-neutral**; for **UX** it is **not** (£12k vs £8.4k) — UX needs an explicit plan type.

**Recommended corrections (pick one; both avoid users re-keying SKUs):**
- **(Preferred) Populate `Product_Mapping_Aliases`** on the SKUs so resolution accepts line-level names, and define a **default plan type** rule (e.g., default "Fixed" unless the row/Deal says Flex). E.g., add alias `Jurnii UX` to **`JUX-FIX`**. Then activity/staging values like "Jurnii UX" resolve deterministically.
- **(Alternative) Transform CSV `Product Interest`** → append the agreed default plan type (`Jurnii UX` → `Jurnii UX - Fixed`) so it is a valid `Leads.Product_Interest` SKU value. Document the default and flag UX rows for confirmation at quote time.

Either way, **do not** require the user to enter price/code/tax on the Lead/CSV — those derive from the Product + org defaults.

---

### Minimum data to create a valid Quote (Section 9) and source of each field
| Quote field | Source | Required up-front? |
|---|---|---|
| Account / Contact / Deal | Deal graph (post-conversion) | derived |
| `Quote_Product` + line `Product_Name` | Product Interest → SKU (needs plan type) | **interest required; plan type required for UX** |
| `Opportunity_Type` (FTP/RTP) | Deal floor (`processDeal`) | derived |
| Quantity / `Quoted_Item_Plan_Brands` | **number of brands** | **required for banded price** (else unpriced + Manual Review) |
| `List_Price` / Sub/Grand Total / Tax | Product Unit_Price + banded calc + Zoho formula | calculated |
| Currency | Org default (GBP) | defaulted |
| `Quote_Stage` / Valid_Till / Owner / Date | defaults | defaulted |
| `Contract_Date_Start` / `Contract_Date_End` | activity/contract data | **required to *Confirm*** a Quote (not to draft) |

**Genuinely non-derivable for these CSVs:** plan type (Fixed/Flex, esp. UX), **number of brands**, contract Start/End. These are the only fields a row can be *Quote-blocked* on — and only at the point of actually creating the commercial quote, not at import.
