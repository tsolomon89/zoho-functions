# v6 Single-Field Automation Audit

## Current Authority
- Quote lifecycle and `processDeal` own commercial propagation.
- Activity handlers own normalization of Tasks, Calls, and Events into `contextJson`.
- `routeContactSequence` owns Contact stage/sequence transitions.
- `Quote_Applied_Activity_Keys` owns per-Activity Quote idempotency.

## Active User/Edit Fields
| Module | Field | Role |
| --- | --- | --- |
| Tasks | `Task_Contract_Products` | Multi-select picklist of Product names. |
| Calls | `Call_Task_Contract_Products` | Multi-select picklist of Product names. |
| Events | `Meeting_Task_Contract_Products` | Multi-select picklist of Product names. |
| Events | `Meeting_Task_Stage` | Infers demo, commercial, or renewal behavior. |
| Events | `Meeting_Task_State` | Open, Won, Lost lifecycle. |
| Events | `Meeting_Task_Lost_Reasons` | Scoped loss reason. |
| Quotes | `Quote_Stage` | Quote lifecycle command. |
| Quotes | `Deal_Name` | Quote reassignment surface. |

## Non-User Automation Fields
| Module | Field | Owner |
| --- | --- | --- |
| Contacts | `Products_Linked` | `processDeal` related-list linking. |
| Deals | Products related list | `processDeal` related-list linking. |
| Quotes | `Quote_Product` | `processDeal`. |
| Quotes | `Quoted_Items.Product_Name` | `processDeal`. |
| Quotes | `Opportunity_Type` | `processDeal`. |
| Quotes | `Quote_Last_Deal_ID` | `handleQuoteStageChange`. |
| Quotes | `Quote_Applied_Activity_Keys` | `processDeal` activity idempotency. |

## Retired Or Legacy
- `Commercials_Status` is legacy-only until WF004 is disabled.
- `Meeting_Type` is DEP-labeled and unused.
- `Conversion_Outcome` is DEP-labeled.
- No v6 behavior writes `Commercials_Sent_At`, `Signed_At`, `Commercials_Discussed_At`, or `Intent_To_Sign`.
- v6 idempotency uses ledger keys, related links, and re-fire guards.

## Audit Rules
- Activity Product values must be names, not lookup IDs.
- Duplicate Product names/codes are ambiguous and must create Manual Review.
- Quote create/update must read back exact key, header Product, and line Product.
- Quote reassignment must reconcile the exact old and new Deals.
- Workflow cutover is complete only when `WF021` is active and `WF020`/`WF004` are inactive.
