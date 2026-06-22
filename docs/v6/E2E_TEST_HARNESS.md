# v6 E2E Test Harness

## Purpose
Validate the v6 cutover from legacy Quote-stage and Commercials_Status workflows to the WF021 Quote reconciliation model.

This harness assumes activity Product fields are multi-select picklists containing Product-name strings. Activity handlers pass those names in `contextJson.products`; `processDeal` resolves them to Products, links Contact and Deal related lists, and creates or updates per-Product Quotes.

## Required MCPs
- Workflow reads/updates: `mcp__zoho_crm_automation_workflow`
- Field metadata reads/updates: `mcp__zoho_field_crud`
- Module metadata fallback: `mcp__zoho_crm_data_metadata` or `mcp__zoho_module_crud`
- Record CRUD/harness execution: use the available Zoho record MCPs for the current session.

## Static Gates
- `WF021 Quotes Create/Edit` exists and is inactive before cutover.
- `WF020 Quotes` remains active until WF021 passes the harness.
- `WF004 Commercials Status Handler` remains active until WF021 passes the harness.
- Quote fields exist and are writable: `Quote_Product`, `Opportunity_Type`, `Quote_Last_Deal_ID`, `Quote_Applied_Activity_Keys`.
- Activity Product picklist actual values match live `Products.Product_Name`, including `Jurnii Cortex - Fixed` and `Jurnii Cortex - Flex`.
- Events has `Meeting_Task_Stage`; `Meeting_Type` is DEP-labeled and unused.
- No function writes `Commercials_Sent_At`, `Signed_At`, `Commercials_Discussed_At`, or `Intent_To_Sign`.
- No harness assertion depends on retired per-activity marker fields or numeric Product payloads/lookup relationships.

## Seed Data
- Use disposable Leads, Contacts, Accounts, Deals, Tasks, Calls, Events, and Quotes with a unique run key in names/subjects.
- Use active Product records whose `Product_Name` values exactly match the activity picklists.
- Preferred Product set:
  - `Jurnii 360 - Fixed`
  - `Jurnii 360 - Flex`
  - `Jurnii UX - Fixed`
  - `Jurnii UX - Flex`
  - `Jurnii Cortex - Fixed`
  - `Jurnii Cortex - Flex`

## Test Matrix
- T1 Context snapshot: completed Task/Call/Event with Product picklist values yields `contextJson.products` as Product-name strings.
- T2 Won no Product: stage can advance and no Quote is created.
- T3 Won one Product: Contact `Products_Linked`, Deal Products, `Quote_Product`, and one `Quoted_Items` Product line are created.
- T4 Same Product repeat: exact `Quote_Applied_Activity_Keys` match prevents duplicate Quote creation.
- T5 Same family different plan: Fixed and Flex Product names resolve to distinct Product Quotes.
- T6 Multi-Product activity: each selected Product creates or updates its own Product Quote.
- T7 Lost activity: scoped loss applies to the acting Contact and does not close the Deal unless final loss rules apply.
- T8 Amount recompute: Deal Amount equals sum of non-Closed-Lost active Quote totals.
- T9 Pre-RTP regression: Contact/Deal do not roll backward from activity evidence below the allowed floor.
- T10 RTP floor: completed Onboarding/Renewal state restores at least Onboarding.
- T11 Draft contributes: Draft Quote total contributes to active amount.
- T12 Closed Lost excluded: Closed Lost Quote drops from amount without automatically losing the Deal.
- T13 Confirmed/Closed active cycle: a later Won activity creates a new Draft Quote if only Confirmed/Closed matches exist.
- T14 Confirmed requires dates: Confirmed Quote without both contract dates moves to On Hold and raises Manual Review.
- T15 Blank protection: blank incoming brands/dates never erase nonblank Quote values.
- T16 Idempotency: exact activity key, Product links, amount, ledger, sequence, and email dedup prevent duplicate side effects.
- T17 Opportunity Type normalization: Quote `Opportunity_Type` normalizes to FTP or RTP from the Deal floor.
- T18 Marker init: `Quote_Last_Deal_ID` is set and verified for linked Quotes.
- T19 Reassignment dual recompute: moving a Quote from Deal A to Deal B recomputes both exact Deals and verifies the marker.
- T20 Legacy multi-Product Quote: conflicting `Quote_Product` versus `Quoted_Items` integrity blocks auto-mutation and raises Manual Review.
- T21 Retry after routing: failed Product can be retried after data correction without duplicating successful Products.
- T22 Reopened Quote: active total updates when a Quote moves from Confirmed back to Negotiation with a new total.
- T23 Stopped Contact: structural reconciliation still runs, but no next action dispatch occurs.
- T24 Conflicting term brands: ledger conflict is retained as Manual Review.
- T25 Quote Product integrity: `Quote_Product` must match the single distinct `Quoted_Items.Product_Name`.
- T26 Product-name resolution: selected Product names resolve by `Product_Name`, with `Product_Code` fallback only when no name match exists.
- T27 Inactive Product: inactive Product is rejected with Manual Review and no downstream dispatch.
- T28 Structural idempotency: Quote ledger keys, related links, and re-fire guards prevent duplicate downstream work.
- T29 Missing contract end: Quote can be created, but Confirmed term gate blocks until both dates exist.
- T30 Cortex actual values: Cortex picklist actual values read back as `Jurnii Cortex - Fixed/Flex`.
- T31 Product ambiguity: duplicate active Product names/codes produce Manual Review and no arbitrary Product selection.
- T32 Partial retry: Product A already applied remains untouched while Product B retries after correction.
- T33 Pricing unavailable: Quote is created unpriced, Manual Review is raised, and retry does not loop forever.
- T34 Multiple open Quote anomaly: multiple updatable matching Quotes block mutation and dispatch.
- T35 Reopened only-confirmed term: active amount and ledgers recompute without corrupting Initial identity.
- T36 Activity relationship validation: Who/What mismatch blocks Contact, Product, Quote, and dispatch writes.
- T37 Post-reconciliation blocker refresh: Manual Review or blocking Tasks are re-read before dispatch.
- T38 Nested transition: `processDeal` routing `commercial:sent` or `commercial:signed` suppresses outer dispatch.
- T39 Durable RTP floor: manual regression below Onboarding is restored after reconciliation.
- T40 Partial Product delivery: one Delivered and another Draft does not prematurely route `commercial:sent`.
- T41 Multiple review issues: Manual Review retains all reason codes.
- T42 Non-Activity call: `commercial:signed` with `{}` performs transition logic without activity Product reads.
- T43 Exact Deal reconciliation: Quote reassignment never redirects to a different canonical Deal.
- T44 Older evidence fills blanks: older retried evidence fills blank fields without erasing newer nonblank values.
- T45 Nested transition verification: if routed transition does not produce expected Stage readback, return failure and Manual Review.
- T46 Exact key matching: `Calls:123` never matches existing `Calls:1234`.
- T47 Already-applied key: one Product with the exact key is success; remaining failed Products continue retry.
- T48 Workflow re-fire: repeated Won activity does not create duplicate Quotes, links, Tasks, Calls, or emails.
- T49 Quote write proof: create/update writes header, `Quoted_Items`, and `Quote_Applied_Activity_Keys` in one request, then readback verifies all three.
- T50 Final workflow state: after all gates pass, `WF021` active, `WF020` inactive, and `WF004` inactive.

## Acceptance
- Every live metadata mutation is read back through Zoho MCP.
- Every test record created by the harness is isolated by run key and cleaned up or left clearly marked as disposable test data.
- Final docs, harness, and mermaid reference WF021 and Product-name activity picklists.
