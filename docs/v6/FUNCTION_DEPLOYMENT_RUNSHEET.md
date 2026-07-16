# v6 Function Deployment Runsheet

## Guardrails
- Do not commit, push, open a PR, delete functions, delete fields, or change API names.
- Use Zoho MCPs for all live CRM workflow and field metadata work.
- Keep `WF021` disabled until every gate below passes.
- Keep `WF020` and `WF004` active during staging.

## Preflight
1. Read workflow state with `mcp__zoho_crm_automation_workflow.ZohoCRM_getWorkflowRuleById`.
   - `WF021` `991103000001699034`: must be inactive.
   - `WF020` `991103000001581243`: must be active.
   - `WF004` `991103000000800001`: must be active.
2. Read Quote fields with `mcp__zoho_field_crud.ZohoCRM_getFieldsWithID`.
   - `Quote_Product` `991103000001699003`
   - `Opportunity_Type` `991103000001699015`
   - `Quote_Last_Deal_ID` `991103000001699025`
   - `Quote_Applied_Activity_Keys` `991103000001702768`
3. Read activity Product fields and confirm they are multi-select picklists, not lookups.
   - Tasks `Task_Contract_Products`
   - Calls `Call_Task_Contract_Products`
   - Events `Meeting_Task_Contract_Products`
4. Confirm Cortex actual values are `Jurnii Cortex - Fixed` and `Jurnii Cortex - Flex` in all three activity modules.
5. Confirm Events has `Meeting_Task_Stage`. If absent, create it as an Events picklist with the v6 stage values and re-read.

## Publish Set

> **2026-07-16 — this list is the original cutover set and is stale.** For the current
> push (activation gate + quote-naming + connection fix + consolidation) the authoritative
> publish set and the Zoho-side actions live in the plan and in `DELETE_IN_ZOHO.md`.
> In particular: the new `activity/_util_buildQuoteSubject` must be created; `_util_resolveDealPipeline`
> and `_util_normalizeToProductQuoteTuples` must be republished; the `.ORPHANED` files must
> NOT be published; and all 27 `invokeurl` calls use `connection: "zoho_crm"` (underscore).

Publish the v6 functions after local edits are complete:
- `processDeal`
- `activity/routeContactSequence`
- `activity/handleTaskCompletion`
- `activity/handleCallOutcome`
- `activity/handleMeetingEvent`
- `activity/handleQuoteStageChange`
- `activity/handleCommercialsStatusChange`
- `activity/applyCommercialTransition`
- `activity/createAuxTask`
- `activity/sendCommercialFollowUp`
- `activity/sendDemoReminder`
- `activity/sendScheduledEmailFromTask`
- `activity/sendSequencedEmail`
- `activity/_util_resolveQuoteLinePrice`
- `activity/_util_logAutomationEvent`
- `activity/_util_calculateBusinessDate`

Do not publish the orphaned quote helpers as active v6 functions:
- `ensureDealQuote`
- `syncConfirmedQuoteToDeal`
- `_util_resolveQuotePlanSummary`

## Signature Proof
- `processDeal` signature is `string automation.processDeal(string deal_id, string contextJson)`.
- Activity handlers pass `contextJson.products` as Product-name strings.
- Activity callers pass Product-name arrays only.
- Callers rely on ledger keys and structural idempotency.
- No function writes `Commercials_Sent_At`, `Signed_At`, `Commercials_Discussed_At`, or `Intent_To_Sign`.

## Atomic Quote Write Proof
Before enabling `WF021`, prove in a disposable Quote that one create/update request can write:
- Quote header fields, including `Quote_Product`, `Opportunity_Type`, and `Quote_Last_Deal_ID`.
- `Quoted_Items` with the same Product.
- `Quote_Applied_Activity_Keys`.

Re-read the Quote and verify the exact key, header Product, and line Product. If Zoho requires separate requests, stop and choose a different idempotency design before enabling WF021.

## Cutover
1. Run legacy Quote migration and resolve blockers.
2. Publish functions.
3. Capture signature proof.
4. Capture atomic Quote write proof.
5. Run T1-T50 from `docs/v6/E2E_TEST_HARNESS.md`.
6. Enable `WF021`.
7. Re-read `WF021` and confirm active.
8. Disable `WF020`.
9. Disable `WF004`.
10. Re-read all three workflows and confirm final state.

## Final State
- `WF021`: active.
- `WF020`: inactive.
- `WF004`: inactive.
- DEP labels remain label-only changes; API names are unchanged.
- Docs and mermaid reference WF021, Product-name activity picklists, and Quote ledger idempotency.
