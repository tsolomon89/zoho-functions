# v6 Flow Reference

## Current Architecture
- Leads remain intake/staging. Contacts, Accounts, Deals, Products, and Quotes are the durable graph.
- Activity Product evidence comes from multi-select picklist values on Tasks, Calls, and Events.
- Activity handlers pass Product-name strings in `contextJson.products`.
- `processDeal` resolves Product names, links Contact and Deal Product related lists, creates or updates per-Product Quotes, recomputes Amount, rebuilds ledgers, and gates commercial transitions.
- `handleQuoteStageChange` is a thin WF021 adapter. It coordinates Quote reassignment and calls `processDeal` for the exact Deal(s) involved.

## Workflow State
| Workflow | Module | Current cutover role |
| --- | --- | --- |
| WF021 Quotes Create/Edit | Quotes | New unified Quote workflow. Keep disabled until all gates pass. |
| WF020 Quotes | Quotes | Legacy Quote_Stage field-update workflow. Keep active until WF021 is verified. |
| WF004 Commercials Status Handler | Deals | Legacy back-compat wrapper. Keep active until WF021 is verified, then disable. |
| WF006 Calls | Calls | Keep. Adapter reads Product-name picklist values and passes `products`. |
| WF007 Events | Events | Keep. Adapter infers meeting type from `Meeting_Task_Stage` and passes `products`. |
| WF008 Tasks | Tasks | Keep. Adapter reads Product-name picklist values and passes `products`. |

## Activity Product Fields
| Module | Field | Data type | Meaning |
| --- | --- | --- | --- |
| Tasks | `Task_Contract_Products` | Multi-select picklist | Product-name strings selected by the rep. |
| Calls | `Call_Task_Contract_Products` | Multi-select picklist | Product-name strings selected by the rep. |
| Events | `Meeting_Task_Contract_Products` | Multi-select picklist | Product-name strings selected by the rep. |

Required actual values must equal `Products.Product_Name`, including:
- `Jurnii 360 - Fixed`
- `Jurnii 360 - Flex`
- `Jurnii UX - Fixed`
- `Jurnii UX - Flex`
- `Jurnii Cortex - Fixed`
- `Jurnii Cortex - Flex`

## Activity Context
```json
{
  "source": "activity",
  "sourceModule": "Tasks|Calls|Events",
  "sourceActivityId": "991103...",
  "contactId": "991103...",
  "activityState": "Won",
  "products": ["Jurnii UX - Fixed"],
  "numberOfBrands": 5,
  "contractDateStart": "2027-01-01",
  "contractDateEnd": "2027-12-31"
}
```

Activity contexts carry Product names only.

## Product Resolution
- `processDeal` loads active Products and indexes by normalized `Product_Name` and `Product_Code`.
- Exact Product-name match wins.
- Product-code fallback is allowed only when no Product-name match exists.
- Duplicate active names or codes are ambiguous and raise Manual Review.
- Unresolved Product strings raise Manual Review and do not create a Quote for that Product.

## Quote Ownership
- One Product Quote is keyed by Deal, `Quote_Product`, and `Opportunity_Type`.
- The Quote header `Quote_Product` must match the single distinct Product in `Quoted_Items.Product_Name`.
- Activity-updatable Quote stages are Draft, Negotiation, Delivered, and On Hold.
- Confirmed, Closed Won, and Closed Lost Quotes are not overwritten by activity evidence.
- `Quote_Applied_Activity_Keys` is the idempotency ledger. Keys are exact newline-delimited values like `Calls:991103...`.

## Quote Reconciliation
- `WF021` fires on Quote create/edit after cutover.
- `handleQuoteStageChange` reads `Quote_Last_Deal_ID` and current `Deal_Name`.
- No move: call `processDeal(currentDeal, {"source":"quote","reconciliationRole":"current"})` and verify marker.
- Move A to B: call old-role reconciliation for A, then new-role reconciliation for B, then stamp and verify `Quote_Last_Deal_ID=B`.
- Unlink: call old-role reconciliation for the old Deal, then clear the marker.
- Quote deletion is not part of the automation path; use Closed Lost.

## Commercial State
- Quote lifecycle and `processDeal` are commercial authority.
- Delivered Quotes can route `commercial:sent` after all relevant Quotes are ready.
- Confirmed Quotes require both contract dates before term ledger and signed transition logic.
- Signed commercial state keeps Deal `Opportunity_State` Open; Deals are not persistently Won.
- Closed Lost Quotes are excluded from active amount and do not automatically close the Deal while other viable evidence remains.

## Retired Or Legacy Behavior
- `Commercials_Status` is DEP-labeled and legacy-only while WF004 is active.
- `handleCommercialsStatusChange` maps legacy values to a safe wrapper. It does not write phantom fields.
- Do not write `Commercials_Sent_At`, `Signed_At`, `Commercials_Discussed_At`, or `Intent_To_Sign`.
- `Meeting_Type` is DEP-labeled and unused. Events use `Meeting_Task_Stage`, `Meeting_Task_State`, and `Meeting_Task_Lost_Reasons`.
- v6 idempotency is owned by ledger keys, related links, and re-fire guards.

## Cutover Acceptance
- Metadata readback confirms Quote fields, activity Product picklists, and Events `Meeting_Task_Stage`.
- Atomic Quote write proof confirms header, `Quoted_Items`, and `Quote_Applied_Activity_Keys` can be written and read back together.
- T1-T50 pass.
- Final workflow readback confirms `WF021` active, `WF020` inactive, and `WF004` inactive.
