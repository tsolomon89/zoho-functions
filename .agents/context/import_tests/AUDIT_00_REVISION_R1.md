# Pre-Import Audit — REVISION R1 (2026-06-22)

**This document supersedes the pricing conclusions in AUDIT_01/02/03 and records the defect fixes, retest evidence, revised decisions, and the go/no-go.** It was produced after the reviewer correctly flagged that the original audit conflated `Product.Unit_Price` with the actual **banded pricing matrix**.

Authoritative sources re-read: `.agents/context/pricing/price_model.csv`, `v6/activity/_util_resolveQuoteLinePrice.deluge`, `docs/v6/jurnii_zoho_quote_product_contract_spec_v2.md`.

**Hard status (unchanged): NO CSV imported. NO production records created from CSVs. NO production conversion. NO Quote backfill.** Live retest used synthetic `ZZE2E…` records, all deleted (verified).

---

## 1. Pricing model — corrected understanding

The Quote line price is **NOT** `Product.Unit_Price`. It comes from the banded, market-sensitive matrix in `price_model.csv`, resolved by `_util_resolveQuoteLinePrice`:

> **Line ACV = PPB(at the selected band) × actual brand-market count**, rounded to 2dp. (`pricing_basis = ppb_x_brands`.)

Per-family required dimensions (the resolver returns `valid=false` otherwise):

| Family | Required pricing inputs | Bands | If missing |
|---|---|---|---|
| **Jurnii UX** | **plan type (Fixed/Flex)** + pricing tier + brand count | 5,7,10,15,20,50,100 | `ux_missing_plan_type` / `missing_brand_count` → Manual Review |
| **Jurnii 360** | **frequency (4x/2x/1x per day)** + pricing tier + brand count | 5,10,20,50 | `360_missing_frequency` / `missing_brand_count` → Manual Review |
| **Jurnii Cortex** | **none — not in the matrix** | — | `no_pricing_for_product` → **Manual Review (manual price)** |
| All | exact Product resolution; band = exact or next-highest (above max → Manual Review) | | |

**Worked examples (correcting the original "£12k vs £8.4k" framing):**
- UX **Fixed** Base @5 brands → PPB £2,100 × 5 = **£10,500**; @8 brands → band 10 → £1,848 × 8 = **£14,784**.
- UX **Flex** Base @5 brands → £1,680 × 5 = **£8,400**; @8 → £1,478.40 × 8 = **£11,827.20**.
- Tier escalation (UX, band 5, Base→Markup→Agency): £2,100 → £2,730 (+30%) → £3,549 (+69%).
- Jurnii 360 **4x/day** Base @5 → £15,360 × 5 = **£76,800**. (360 2x/1x are tier-invariant: Base=Markup=Agency.)

So **Fixed vs Flex is material at every band** (Flex ≈ 80% of Fixed), and tier (Base/Markup/Agency) materially changes price. The `£12,000 / £8,400` Unit_Price figures in the original AUDIT_01 §A.3 / §G are **wrong as "quote price"** — `Unit_Price` is only a catalogue list price, not the computed line ACV.

### Corrected Product mapping conclusions (supersedes AUDIT_01 §G)
- `Product Interest` is sufficient for **Product selection only** — and only when the value is an **exact SKU** (`Jurnii UX - Fixed`, `Jurnii UX - Flex`, …). The generic family value `Jurnii UX` is **ambiguous** (Fixed vs Flex are different commercial products at every band) → it is **not Product-resolution-ready**.
- **Do NOT default `Jurnii UX` → `Jurnii UX - Fixed`, and do NOT add it as a `Product_Mapping_Aliases` alias** — that would silently fabricate a commercial term. (Withdrawing the original §G "preferred alias" recommendation.)
- Correct options for the historical CSV `Jurnii UX` values: (a) change to the exact SKU where the plan is known; (b) populate an explicit plan-type field; (c) leave unresolved for supervised enrichment.
- For **future** CRM use, `Leads.Product_Interest` is already restricted to exact SKUs, so Product Interest alone *is* sufficient for selection going forward — the gap is only the historical CSV granularity.

### Corrected minimum-data-to-quote (supersedes AUDIT_01 §C.7 / §9)
The original "plan type + brand count" was only correct for UX. Corrected, per family:
- **UX:** plan type (Fixed/Flex) + pricing tier + brand count.
- **360:** frequency + pricing tier + brand count.
- **Cortex:** no auto price → Manual Review (manual price) or a new pricing matrix.
- **All:** exact Product resolution; contract Start/End dates only to move a Quote to *Confirmed*.

### Corrected Quote-readiness — now FOUR classes (supersedes the binary "Quote-ready" in AUDIT_02 §F)
Per the contract spec, pricing failure is **non-fatal when an exact Product resolved** (Draft Quote created + Manual Review, unpriced); but an **ambiguous/unresolved Product creates NO Quote**. So classify each row as:

1. **Product-resolution ready** — an exact SKU can be selected. (`Jurnii UX` alone is NOT — ambiguous.)
2. **Draft-Quote-creation ready** — exact Product resolved; a Draft Quote can be created even if unpriced (→ Manual Review).
3. **Auto-pricing ready** — all family-specific pricing inputs present (UX: plan+tier+brands; 360: freq+tier+brands; Cortex: never).
4. **Confirmation ready** — also has contract Start + End dates.

A row with an exact Product but no brand count → supports a **Draft Quote in Manual Review** (class 2, not 3). A row containing only `Jurnii UX` → **does not support Quote creation** (fails class 1).

### CSV `Type` column — PRESERVE, do not drop (supersedes AUDIT_02 §D row 21)
`Type` (Brand/Agency/Platform) is **likely** the source of `Quoted_Item_Pricing_Tier` (Base/Markup/Agency), which materially changes price. **But this mapping is NOT established** in the repo or spec: `processDeal` currently **hardcodes tier="Base"** (processDeal.deluge:774,854) and never reads `Type`; the spec does not document the mapping. Therefore:
- **Preserve the `Type` column** through cleanup; do not drop it.
- **Hypothesised** mapping to confirm with the business: `Brand → Base`, `Agency → Agency`, `Platform → Markup`.
- Distinct values + counts in the CSVs (mostly blank): MQL Brand 7 / Agency 2; SQL Brand 19 / Platform 1 / Agency 1; FTP Brand 16 / Agency 2; RTP Brand 36.
- It carries a **principal pricing input** — resolve the mapping before relying on auto-pricing, and (separately) before dropping it.

---

## 2. Defect fixes applied (repository) + deployment limitation

**Tooling limitation discovered:** the available MCP function tools (`getAutomationFunctions`, `putAutomationFunctions`, `postAutomationFunctions`) expose only function **metadata** (name, module, arguments) — **none carries the Deluge source body**. I therefore **cannot read or write deployed function code via MCP**. Fixes were applied to the **repository** (the deployable source of truth); they must be deployed to the org via your normal path (paste into the Zoho function editor / your deploy tooling). I could not run a post-fix live retest of the *deployed* code because I could not deploy it.

**Deployment drift also confirmed:** the repo `processContact` already contains a duplicate-activation **self-heal (§6b)**, yet the live org still produced two un-deferred activation tasks → the deployed function predates/omits the repo logic (or the race defeats it). Several deployed functions were last modified 2026-06-20/21/22, around/after the last repo commit. **Before relying on any fix, reconcile deployed functions to the current repo.**

| Defect | Root cause (confirmed/most-likely) | Repo fix applied | File |
|---|---|---|---|
| **D2** activity→Quote produced no Quote | `ctx.get("products")` round-trips as a **String** (not List) via `Map.toString()→toMap()`; `for each … in <String>` iterated characters → `productNames` empty → Quote skipped (handler still returned success) | Parse products robustly: strip brackets/quotes, split on comma (works for List "[a, b]" and String forms) | `v6/processDeal.deluge` §5 |
| **D4** Product Interest not propagated | fragile single-line `.toString()` munge + phantom `Product_Interest1` read left `Contact.Product_Interest_Staging` empty | Robust List-or-String parse → clean comma-joined staging string; dropped phantom read | `v6/processLead.deluge` §1 |
| **D1** duplicate activation Task | two concurrent `processContact` runs (inline call + WF001b2) each create one before either §6b sweep sees the other | Race-proof backstop in the **consumption** path: on completing a Sequence Activation task, defer every other open activation task for the same Contact+Stage (only one activates) | `v6/activity/handleTaskCompletion.deluge` activation branch |
| D3 rollup lag | eventual consistency on Account→Contacts related list on bulk create | (no code change) settling re-touch pass in runbook remains; deterministic option noted | — |
| Drift | `processLead` reads non-existent legacy Lead fields; **`Deals.Product_Interest_Staging` does not exist** (COQL rejects it) so processDeal/processLead writes of it to the Deal are silent no-ops | documented; repointing/removal recommended in a follow-up sync | `processLead.deluge`, `processDeal.deluge` §8 |

**These repo edits are untested in deployment** (could not deploy). They follow existing idioms and were written to be syntactically correct Deluge, but must be deployed and retested per §3.

---

## 3. Retest evidence (current deployed behaviour) + the post-deploy retest plan

**Re-confirmation run (synthetic, deleted):** Lead "ZZE2E Delta" (FTP, Proposal Preparation, Job_Title CCO, `Product_Interest=["Jurnii UX - Fixed"]`, domain `zze2e-delta.example`) auto-converted → Account `…683007` / Contact `…741001` / Deal `…692006` (Stage **FTP**, Opp_Stage Proposal Preparation ✓). Then a fully-formed "Draft Commercials" Task (Won/Completed, `Task_Contract_Products=["Jurnii UX - Fixed"]`, `Task_Contract_Brands=5`, `Task_Sequence_Stage=Proposal Preparation`).

| Check | Result | Verdict |
|---|---|---|
| Conversion + Opportunity-Type derivation | FTP / Proposal Preparation | ✅ |
| `Contact.Product_Interest_Staging` after convert | **null** | ❌ D4 reproduced |
| Activation tasks on the Deal | **2 × "Not Started"** (no Deferred) | ❌ D1 reproduced (deployed lacks/loses §6b) |
| Quote after Draft Commercials activity | **none**; no Product linked to Deal | ❌ D2 reproduced (handler ran, success, no Quote) |
| `Deals.Product_Interest_Staging` queryable | COQL "invalid column" | confirms field absent on Deals |

**Post-deploy retest plan (you run after deploying the repo fixes):** create one synthetic Lead per case, drive the activity, assert, then delete. Expected results once fixes are deployed:

| Test | Setup | Expected |
|---|---|---|
| 1 activation task | convert any Lead | exactly 1 active "Sequence Activation" (others Deferred) |
| PI propagation | Lead with `Product_Interest=["Jurnii UX - Fixed"]` | `Contact.Product_Interest_Staging` = "Jurnii UX - Fixed" |
| **UX Fixed** | FTP Deal; activity products=`[Jurnii UX - Fixed]`, brands=5, tier Base | Draft Quote (Opp_Type FTP); Quoted_Item List_Price **£10,500** (2100×5) |
| **UX Flex** | products=`[Jurnii UX - Flex]`, brands=5 | line ACV **£8,400** (1680×5) |
| **360 + frequency** | products=`[Jurnii 360 - Fixed]`, brands=5, `Quoted_Item_Frequency=4x per day` | line ACV **£76,800** (15360×5) |
| **360 missing frequency** | 360 product, no frequency | unpriced Draft Quote + Manual Review (`360_missing_frequency`) |
| **Cortex** | products=`[Jurnii Cortex - Fixed]`, brands=5 | unpriced Draft Quote + Manual Review (`no_pricing_for_product`) |
| **Missing brand count** | exact UX SKU, no brands | Draft Quote created **unpriced** + Manual Review (`missing_brand_count`) |
| **Ambiguous family** | activity product = `Jurnii UX` (no Fixed/Flex) | **no Quote**; Manual Review (`product_name_unresolved`) — ambiguous family is not a SKU |
| Tier from Type | (after Type→tier mapping confirmed) activity tier=Agency | line ACV uses Agency PPB (e.g. UX Fixed band5 £3,549×5) |

(The "ambiguous family" expectation depends on whether you add a `Product_Mapping_Aliases` entry — recommended NOT to, so it correctly raises Manual Review rather than silently picking Fixed.)

---

## 4. Revised decisions on the five open items

1. **UX plan type — no default.** Require exact SKU or explicit plan-type enrichment; never auto-pick Fixed/Flex. Future CRM use is fine because `Product_Interest` values are already exact SKUs.
2. **Industry — preserve useful data.** Add `Gaming`, `Ecommerce`, `OTT`, `Fintech` to `Leads.Industry`; map `Other` to an existing equivalent; **review `UX` rows separately** (UX is a function/interest, not an industry). May remain unmapped for the first import if changing metadata would delay conversion — but do not permanently discard.
3. **SQL rows without email (57) — import as inert Leads only; do NOT auto-convert.** Website matching groups companies but not individuals; converting weakly-identified Contacts harms email automation + future dedup. Enrich emails, convert enriched rows normally, route permanently email-less rows through a separate reviewed conversion with an explicit alternative person key.
4. **Fix + retest D1, D2, D4 before production conversion — gate enforced.** D1 → hundreds of dup tasks; D4 → discards the PI data needed for quoting; D2 → the end-to-end Quote workflow has not passed. D3 may use the settling pass temporarily (deterministic fix preferred). **Production Lead import (workflows OFF) may proceed after CSV cleanup; production conversion must NOT begin until D1/D2/D4 are deployed and pass §3 retests.**
5. **RTP = Renewal default.** Use Onboarding only with affirmative evidence of a newly-signed, not-yet-live customer; missing contract dates ≠ pre-launch.

Lead Quote/Contract Stage field: **still NOT required** (unchanged) — `Opportunity_Stage` + Quotes/Deal cover it; a Lead field would be stale at conversion.

---

## 5. Go / No-Go

| Phase | Status | Gate |
|---|---|---|
| CSV cleanup + **inert Lead import (workflows OFF)** | **Conditionally GO** | apply the AUDIT_02 §E fixes (mandatory Last_Name, malformed email, Stage/Lead-Source remaps, Lost reasons, Industry, Type preserved, PI left to backfill); purge the leftover CODX_V6_E2E test records; confirm trial/plan beyond 2026-06-25 |
| **Production conversion** | **NO-GO** | until D1, D2, D4 are **deployed** (repo fixes pushed via the Zoho editor — MCP cannot) and pass the §3 retests; then batched conversion + settling pass |
| **Quote backfill** | **NO-GO** | until exact Product selection + family-specific pricing inputs (UX plan type, 360 frequency, brand count) and the `Type`→tier mapping are resolved; Cortex routes to Manual Review by design |

**Remaining business decisions for you:** (a) confirm `Type` → tier mapping (Brand=Base/Agency=Agency/Platform=Markup?); (b) UX plan-type enrichment source for historical rows; (c) Cortex pricing (manual vs new matrix); (d) how you want the repo fixes deployed (your function-deploy path), after which I can run the §3 live retests.
