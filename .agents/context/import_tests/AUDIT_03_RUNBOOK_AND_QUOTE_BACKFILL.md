# Pre-Import Audit, Part 3: Manual Import Runbook + Quote Backfill Plan

This is the procedure **you** run manually. Nothing here has been executed against production data. The governing fact: **`WF001a` auto-converts every Lead on create/edit**, so the single most important control is the **"Trigger workflows" toggle** during import.

---

## 20. How Zoho import interacts with this automation

| Question | Answer for this org |
|---|---|
| Do **workflow rules** run during CSV import? | **Only if you tick "Trigger workflows" in the import wizard.** If ticked, `WF001a` fires `processLead` on each new Lead → **auto-conversion cascade** (Account+Contact+Deal+Roles+activation tasks). If unticked, Leads land inert. |
| Do **custom functions** run? | Yes — they run **as part of** their workflow. No workflow trigger ⇒ no functions. |
| Do **validation / mandatory** checks run? | Yes. `Last_Name` (mandatory) and **picklist/data-type validity** are enforced at import. Restricted picklists (`Job_Title`, `Industry`, `Lead_Source`, geographic State/Country) will **reject or require "auto-add picklist values"**. |
| Do **duplicate rules** run? | The import wizard's own matching applies (you choose the match field + create/skip/overwrite). |
| Do **assignment rules** run? | Only if you opt in (leave off; owners are handled separately). |
| Can imported records trigger **conversion / activity / Quote creation**? | Conversion: yes, indirectly, via `WF001a` if workflows are triggered. Activities/Quotes: **no** — those need a Task/Call/Meeting with product evidence (and Quote creation is currently impaired — defect D2). |
| Do **blank CSV cells overwrite** existing values? | On **Add**: no existing record. On **Update**: enable "skip empty values" so blanks don't wipe data. |
| Can **lookups / multi-selects** be populated? | Multi-select picklists: yes (`;` separator). Lookups: only by matching an existing record; the Lead module needs few. |
| Is a **post-import update required to trigger automation**? | Yes if you import with workflows off (recommended) — you then trigger `processLead` deliberately (Phase 2). |
| Should each Opportunity Type import to **Leads**? | **Yes** — all four import to Leads; the CRM has no existing customers, so FTP/RTP also build their Accounts/Deals fresh via conversion. None should "update existing Contacts/Deals" (there are none). |
| Enable or disable automation during import? | **Disable (workflows off) for the raw Lead import; enable in a controlled Phase 2.** |

---

## H. Manual import runbook

### Phase 0 — Prerequisites (before any import)
1. **Purge leftover test data:** delete the team's E2E artefacts so they don't pollute matching — Account `CODX_V6_E2E_20260622_094810` (id 991103000001694012) + its Deal/Quote/Contacts. (Keep "Solomon Corp" = your org.)
2. **Decide the four data fixes (apply to *corrected copies*, never the originals):**
   - **Last_Name:** fill every blank (MQL 1, SQL 4, FTP 19, RTP 6). Single-name people → put the single name in Last_Name.
   - **Stage:** FTP "Contract Signed" (2) → **Commercial Agreement** (and tag for Quote backfill).
   - **Lead_Source:** "Trade Show / Event" → **Event** (SQL 8, RTP 1); "Google" → add option or → Website.
   - **Email:** RTP row 94 `sergio.poves vidal@…` → remove the space.
   - **Lost rows:** add `Lost_Reasons` (FTP 3 → e.g. "No Commercial Interest"; RTP 5 → "Churned / Did Not Renew") so conversion marks them Lost; `Status` is already Closed.
   - **Industry:** **drop the column from the mapping** (Gaming/etc. aren't valid and Industry isn't used by automation). Or add the values to the picklist if you want them.
   - **Product Interest:** either **drop** for the Lead import and handle at Quote backfill, **or** transform line→SKU with a default plan type (UX needs a Fixed/Flex decision — £12k vs £8.4k).
   - **Imported_Record_Type:** set per file — MQL/SQL → "Existing Database" (or "Bulk Import"); FTP → "Bulk Import"; RTP → **"Existing Client"**.
3. **(Recommended) fix defects D1, D2, D4 and re-sync repo** *before* Phase 2 conversion, or explicitly accept the dup-activation-task cleanup. D1/D2/D4 do **not** block Phase 1.
4. **Trial expiry:** the org trial ends **2026-06-25** — ensure the plan is extended/paid before committing a large import.

### Phase 1 — Import Leads, automation OFF (reversible)
For each file, **in order MQL → SQL → FTP → RTP**:

| Setting | Value |
|---|---|
| Target module | **Leads** |
| Mode | **Add** (Create) |
| Match/duplicate field | **Email** (handles the 1 cross-file dup; safe re-runs). Rows without email → create. |
| Field mapping | per Part 2 §D; **unmap** Drop columns, the 35 blank SQL columns, and `Full Name`(dup) |
| **Trigger workflows** | **OFF** ⛔ |
| Assignment rules | OFF |
| Skip empty values | ON |
| Auto-add picklist values | your call — ON only if you intend to keep CSV picklist values; otherwise pre-clean and leave OFF |

**Checkpoints after each file:** imported count == expected data rows; spot-check 5 rows for Stage/Status/Company/Email landing; confirm **0 Accounts/Contacts/Deals were created** (proves workflows stayed off). **Stop condition:** any unexpected Account/Contact/Deal appears (workflows leaked on) → halt, disable WF001a, investigate.

### Phase 2 — Controlled conversion (automation ON, batched)
Only after Phase 1 validates. Convert **one file's leads at a time**, in small batches (e.g. 25–50):
1. Ensure `WF001a` is active.
2. Trigger `processLead` by **mass-updating a trivial field** (e.g. set `Imported_Record_Type`) on a batch **with workflows enabled** → `WF001a` fires → conversion cascade.
3. After each batch: check `getAutomationFunctionFailures`; verify Accounts (by `Account_Key`/domain), Deals (`Deal_Key`), Contacts, and Contact Roles.
4. **Settling pass (fixes D3 lag):** after a file's batches complete, **re-touch the resulting Deals once** (mass-edit a no-op field with workflows on) so multi-contact Deals roll up to the furthest-stage contact + correct primary.
5. **De-dup activation tasks (D1):** until D1 is fixed, expect ~2 "Activate sequence…" tasks per Contact — delete the duplicates (keep one per Contact+Stage).

**Checkpoints:** one Account + one Deal per domain; Deal `Stage` (Opportunity Type) = furthest contact's; Lost rows → Contact/Deal Lost; Account_Status reflects RTP = existing client. **Stop condition:** function failures > 0, or duplicate Accounts/Deals per domain.

### Phase 3 — Reconciliation
- Counts: Accounts ≈ distinct domains across all files; Deals == Accounts (one principal each); Contacts == sum of unique people; Contact Roles == Contacts.
- Verify the **15 cross-file companies** collapsed to single Accounts/Deals with multiple Contacts (e.g. `flutter uk & ireland`).
- Verify Opportunity Types: MQL/SQL Deals at SQL-or-below; FTP at FTP; RTP at RTP (never-regressed by earlier-stage siblings).
- Export a post-import snapshot for audit.

### Recommended order & rationale
**MQL → SQL → FTP → RTP.** Order is **not correctness-critical** (the RTP floor + never-regress logic guarantee the Deal ends at the furthest contact's stage regardless of arrival order), but chronological order keeps the audit trail clean and means later, higher-stage files visibly *advance* Deals rather than appearing to "fix" them. One file at a time with a settling pass is the real control.

---

## 22. Post-import Quote backfill plan (separate, supervised — do NOT run during this task)

**Why separate:** Quotes are FTP/RTP-only, require non-derivable inputs (plan type, brand count, contract dates), and the durable activity→Quote path is currently impaired (**D2**). So Quotes must be created in a **supervised** pass, **after** the import + conversion are reconciled.

**Eligible population:** Deals at **FTP** (Proposal Preparation / Commercial Agreement, incl. the 2 remapped "Contract Signed") and **RTP** (Renewal). MQL/SQL Deals are **excluded** (not quote-eligible).

**Procedure (per eligible Deal):**
1. Resolve the graph: Deal → Account, primary Contact, Opportunity_Type (FTP/RTP).
2. Resolve **Product(s)**: from `Product Interest` where present (line→SKU via the agreed default plan type / `Product_Mapping_Aliases`); where absent (all FTP rows) **supply explicitly** — do not guess.
3. Gather non-derivable inputs: **plan type** (Fixed/Flex — confirm UX), **number of brands** (price band), **contract Start/End** (required only to move a Quote to *Confirmed*).
4. Create the Quote **idempotently**, keyed by **Deal + `Quote_Product` + `Opportunity_Type`**:
   - **Option A (preferred once D2 is fixed):** drive a "Draft Commercials" Task with `Task_Contract_Products` + `Task_Contract_Brands` → `processDeal` builds the Quote + Quoted_Items + pricing + ledger natively.
   - **Option B (direct, until D2 fixed):** create the Quote via API with the `Quoted_Items` subform, set `Quote_Stage`=Draft, `Opportunity_Type`, `Quote_Product`, `Quoted_Item_Plan_Brands`, and seed `Quote_Applied_Activity_Keys` with a synthetic key (e.g. `Backfill:<dealId>`) to block later duplication; then let `processDeal` recompute Deal Amount/ledger.
5. **Confirmed/contract terms:** only set `Quote_Stage`=Confirmed when both `Contract_Date_Start`/`End` exist (else `processDeal` demotes to On Hold + Manual Review). For RTP renewals with a known live contract, populate the dates; otherwise leave Draft.
6. **Exceptions:** rows missing product/plan-type/brands → **report, do not fabricate** values.

**Classification of Quote work:**
| Class | Population | Action |
|---|---|---|
| Created by durable workflow | future activity-driven deals (after D2 fixed) | none (automatic) |
| **One-time backfill** | imported FTP + RTP Deals | supervised create (Option A/B) |
| Existing-quote update | none today (no real quotes exist) | n/a |
| Insufficient data | FTP rows (no product interest), rows lacking brands/plan type | report + collect data first |
| Duplicate-Quote risk | re-running backfill | mitigated by Deal+Product+OppType key + `Quote_Applied_Activity_Keys` |

**Backfill exit criteria:** every eligible Deal has exactly one Draft+ Quote per intended Product/OppType; Deal `Amount` = Σ non-Closed-Lost quote totals; no duplicate Quotes; exceptions logged.

---

## Open items to confirm with you
1. **Default plan type for "Jurnii UX"** interest (Fixed £12k vs Flex £8.4k) — needed for deterministic SKU resolution.
2. **Industry column** — drop, or add Gaming/Ecommerce/OTT/Fintech/UX to `Leads.Industry`?
3. **SQL blank emails (57)** — import as-is (website-keyed) or enrich first?
4. **Fix defects D1/D2/D4 before Phase 2**, or proceed and clean up duplicates manually?
5. **RTP "Renewal" vs "Onboarding"** — all 172 RTP rows are tagged Renewal; confirm none are first-term onboarding.
