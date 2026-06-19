# v6 Function Deployment Runsheet — Quote + Product + Contract Model

This runsheet covers ONLY the new Quote/Product/contract automation added in v6. The v5 contact-centric functions (processLead/Contact/Deal/Account, activity handlers, email senders) are unchanged and deploy per `docs/v5/FUNCTION_DEPLOYMENT_RUNSHEET.md`.

> MCP cannot publish Deluge source or create/edit Workflow Rules or fields. Every step below is a **manual Zoho Developer Hub / Setup** action. MCP is used only to create fields/records and to read metadata for verification.

---

## 0. Schema prerequisites (must exist before publishing functions)

See plan `we-are-working-on-pure-codd.md` Phase 1. In brief:
- **Quotes** custom fields: `Contract_Date_Start`, `Contract_Date_End`, `Contract_Type`, `Contract_ACV`, `Previous_Contract_Credit`, `Net_Order_Value`, `Contract_Signed_Date`.
- **Products** custom fields: `Product_Plan_Brands`, `Product_Plan_Products`, `Product_Plan_Type`.
- **Quoted Items** subform fields: `Quoted_Item_Plan_Brands`, `Quoted_Item_Pricing_Tier`, `Quoted_Item_Pricing_Band`, `Quoted_Item_Frequency` (A8 — confirm createFields vs manual UI).
- Product catalogue rows (A7 HARD GATE) and the pricing basis/rounding (A2/A9 HARD GATES) — see §4.

---

## 1. Function publish order (helpers before callers)

| # | Function (`automation.*`) | File | Depends on |
|---|---|---|---|
| 1 | `resolveQuoteLinePrice` | `v6/activity/_util_resolveQuoteLinePrice.deluge` | — (Products read) |
| 2 | `resolveQuotePlanSummary` | `v6/activity/_util_resolveQuotePlanSummary.deluge` | 1 |
| 3 | `syncConfirmedQuoteToDeal` | `v6/activity/syncConfirmedQuoteToDeal.deluge` | 2, `createAuxTask`, `handleCommercialsStatusChange` |
| 4 | `handleQuoteStageChange` | `v6/activity/handleQuoteStageChange.deluge` | 3, `handleCommercialsStatusChange` |
| 5 | `ensureDealQuote` *(Phase 3)* | `v6/activity/ensureDealQuote.deluge` | 1, `createAuxTask` |

`processDeal.deluge` is re-published with the **Amount-authority handoff** edit (skips the product-sum `Amount` write once a Confirmed Quote exists for the Deal).

---

## 2. Workflow Rule wiring

| Workflow | Module | Trigger | Function | Arg mapping |
|---|---|---|---|---|
| **WF020 Quote Stage Change** | Quotes | `field_update` on `Quote_Stage` | `handleQuoteStageChange` | `quoteIdStr ← ${Quotes.id}` |

No WF021: `ensureDealQuote` (Phase 3) is called inline from `processDeal` when `Opportunity_Stage = Proposal Preparation`, avoiding a second workflow round-trip. (If a workflow trigger is preferred later: Deals `field_update Opportunity_Stage = Proposal Preparation` → `ensureDealQuote`, arg `dealIdStr ← ${Deals.id}`.)

`handleTaskCompletion` (WF008) is re-published with the Phase-3 extension (Send Commercials → Quote Delivered; signed outcome → Quote Confirmed → `syncConfirmedQuoteToDeal`).

---

## 3. Behaviour summary (handleQuoteStageChange branches)

| Quote_Stage | Outcome |
|---|---|
| Delivered | Deal `Commercials_Status = Sent` (suppressed) + `handleCommercialsStatusChange` → follow-up eligible |
| Confirmed | `syncConfirmedQuoteToDeal` → validate, price, supersede prior Confirmed, write Deal Initial/Current + Amount, ≤1 Confirmed |
| Closed Lost | commercial loss only if no other active Quote remains; else log `replacement_possible` |
| Draft / Negotiation / On Hold / Closed Won | log only |

All cross-module writes use `{"trigger": List()}` suppression to prevent WF020 ↔ WF004 / Deal-workflow loops. `syncConfirmedQuoteToDeal` validates before any write, demotes the prior Confirmed Quote **before** promoting, and keys first-vs-later off the Deal's populated `Contract_Initial_*` fields (idempotent re-fire).

---

## 4. Gate status (resolved 2026-06-18)

- **A2 pricing basis = PPB × brand-markets** + **A9 rounding = 2 dp**: implemented in `_util_resolveQuoteLinePrice` (`line_acv = band PPB × brand-markets`, rounded to 2 dp). Pricing is live.
- **A3 Cortex**: no pricing rows → Cortex lines return `valid=false` and route to Manual Review (unchanged).
- **A7 catalogue = Option A**: six Products UX/360/Cortex × Fixed/Flex; Jurnii 360 frequency is per line (`Quoted_Item_Frequency`), not separate SKUs. `Unit_Price` is indicative only.

- **A8 RESOLVED**: `createFields(module="Quoted_Items")` adds subform fields directly — all 4 Quoted Item fields are live.

Still open:
- **A5** — which Task outcome carries "signed" + `Contract_Type` for later versions. Blocks the signed→Confirmed branch of `handleTaskCompletion`; the manual `Quote_Stage→Confirmed` path via WF020 works regardless.

## 5. Live schema status (created/verified 2026-06-18)

- Quotes: `Contract_Date_Start`, `Contract_Date_End`, `Contract_Type`, `Contract_ACV`, `Previous_Contract_Credit`, `Net_Order_Value`, `Contract_Signed_Date` — created.
- Products: `Product_Plan_Brands`, `Product_Plan_Products`, `Product_Plan_Type` — created. Catalogue = 6 quote-ready SKUs (UX/360/Cortex × Fixed/Flex) with codes `JUX/J360/JCX -FIX/-FLX`.
- Quoted_Items subform: `Quoted_Item_Plan_Brands`, `Quoted_Item_Pricing_Tier`, `Quoted_Item_Pricing_Band`, `Quoted_Item_Frequency` — created.

## 6. Remaining manual Zoho steps (no MCP path)

1. Publish the 6 Deluge functions (§1 order) in Developer Hub.
2. Re-publish `processDeal` and `handleTaskCompletion` with the v6 edits.
3. Create Workflow Rule **WF020** (§2).
4. Catalogue side-effect: the 3 base Products were renamed `Jurnii UX/360/Cortex` → `… - Fixed`, so `processDeal`'s Product-Interest name match no longer hits them. Add `Product_Mapping_Aliases` (e.g. `Jurnii UX`) to the Fixed SKUs, or update lead Product-Interest text, if provisional pre-Quote Deal.Amount matters.

See the plan file for the full assumption list and testing matrix.
