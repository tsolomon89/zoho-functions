# v6 Single-Field E2E Test Plan

This document is now a focused companion to `E2E_TEST_HARNESS.md`. The old single-field plan referenced retired Meeting fields, WF020-only Quote handling, `Commercials_Status` as an authority, and orphaned helper functions. Those paths are no longer valid for v6 cutover.

## Active Single-Field Surfaces
| Surface | User-facing field | Automation owner | Expected behavior |
| --- | --- | --- | --- |
| Task commercial evidence | `Task_Contract_Products`, brands, dates | `handleTaskCompletion` -> `routeContactSequence` -> `processDeal` | Product-name strings resolve to Products and per-Product Quotes. |
| Call commercial evidence | `Call_Task_Contract_Products`, brands, dates | `handleCallOutcome` -> `routeContactSequence` -> `processDeal` | Same Product-name path as Tasks. |
| Event commercial evidence | `Meeting_Task_Contract_Products`, brands, dates | `handleMeetingEvent` -> `processDeal` | Same Product-name path as Tasks. |
| Event stage/type | `Meeting_Task_Stage` | `handleMeetingEvent` | Infers demo, commercial, or renewal path. |
| Event state | `Meeting_Task_State` | `handleMeetingEvent` | Open schedules/reminds; Won promotes evidence; Lost applies scoped loss. |
| Event loss | `Meeting_Task_Lost_Reasons` | `handleMeetingEvent` / router | Applies module-relative loss without accidental upward cascade. |
| Quote lifecycle | `Quote_Stage` | `WF021` -> `handleQuoteStageChange` -> `processDeal` | Recomputes exact Deal, amount, ledger, and commercial gates. |
| Quote reassignment | `Deal_Name` plus `Quote_Last_Deal_ID` | `handleQuoteStageChange` | Reconciles old and new Deals, then verifies marker. |

## Tests
- SF1: Task Won with one Product-name value creates Contact Product link, Deal Product link, and one Quote.
- SF2: Call Won with multiple Product-name values creates one Quote per Product.
- SF3: Event Won uses `Meeting_Task_Stage` to choose demo/commercial/renewal behavior.
- SF4: Event Lost applies scoped loss and does not close a Deal with remaining viable Contacts.
- SF5: Quote Delivered routes `commercial:sent` only after relevant Quote readiness checks.
- SF6: Quote Confirmed requires both contract dates before signed transition and ledger updates.
- SF7: Quote Closed Lost is excluded from active amount and does not erase other active Quote evidence.
- SF8: Quote moved between Deals recomputes both exact Deals and verifies `Quote_Last_Deal_ID`.
- SF9: Cortex Product values resolve only when picklist actual values exactly match Product names.
- SF10: No single-field test asserts retired activity markers, numeric Product identifiers from activity fields, or phantom Deal timestamp writes.

## Acceptance
- Single-field tests use the same run-key isolation and cleanup policy as the main harness.
- Final workflow state is validated in the main T1-T50 harness.
