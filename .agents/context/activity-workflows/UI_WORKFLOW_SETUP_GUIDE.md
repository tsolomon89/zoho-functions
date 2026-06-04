# UI_WORKFLOW_SETUP_GUIDE.md — Final wiring of workflow rules

## Status after API skeleton creation

12 of 13 workflow rules were created via MCP with **no-op placeholder actions** that you swap out in the UI. WF006 (Calls) could not be created via API because the Calls module rejects every placeholder action type — it must be built in the UI.

### Skeleton rules already in Zoho (just swap the action)

| Rule | Zoho ID | Module | Trigger | Placeholder action |
|---|---|---|---|---|
| WF002 Deal Sequence Router | `991103000000796079` | Deals | Create/Edit, Sequence_Status=Not Started, Automation_Suppressed!=true | field_updates → `WF Placeholder Marker Deals` |
| WF003 Deal Stage Change Router | `991103000000784137` | Deals | Field Update on Stage1 (${ANYVALUE}), Automation_Suppressed!=true | field_updates → `WF Placeholder Marker Deals` |
| WF004 Commercials Status Handler | `991103000000800001` | Deals | Field Update on Commercials_Status | field_updates → `WF Placeholder Marker Deals` |
| WF005 Demo Outcome Handler | `991103000000801001` | Deals | Field Update on Demo_Outcome | field_updates → `WF Placeholder Marker Deals` |
| WF007 Event Meeting Handler | `991103000000782052` | Events | Create/Edit | assign_owner (no-op merge_field) |
| WF008 Task Completion Handler | `991103000000784145` | Tasks | Create/Edit, Status=Completed | assign_owner (no-op merge_field) |
| WF010a Date Router (Next Action Due) | `991103000000800007` | Deals | Date — Next_Action_Due_Date | field_updates → `WF Placeholder Marker Deals` |
| WF010b Date Router (Sequence Paused Until) | `991103000000800016` | Deals | Date — Sequence_Paused_Until | field_updates → `WF Placeholder Marker Deals` |
| WF010c Date Router (Demo Reminder) | `991103000000802001` | Deals | Date — Demo_Reminder_Send_At | field_updates → `WF Placeholder Marker Deals` |
| WF010d Date Router (Comm Follow-Up) | `991103000000790038` | Deals | Date — Next_Comm_Follow_Up_Date | field_updates → `WF Placeholder Marker Deals` |

### Rule to create from scratch in UI

| Rule | Module | Trigger | Function |
|---|---|---|---|
| WF006 Call Outcome Handler | Calls | On scheduled call create/edit | `handleCallOutcome(callId=${Calls.id})` |

---

## How to swap the placeholder for the real function (per rule)

1. Setup → Automation → Workflow Rules → click the rule by name.
2. Click the existing **Instant Action** (the assign_owner or field_updates placeholder).
3. **Delete** that action.
4. Click **+ Instant Actions → Function → Custom Function**.
5. Pick the function from the dropdown (it knows the function by name — no IDs needed):

| Rule | Function | Arg mapping |
|---|---|---|
| WF002, WF003 | `sequenceRouter` | `dealId` ← `${Deals.id}` |
| WF004 | `handleCommercialsStatusChange` | `dealId` ← `${Deals.id}` |
| WF005 | `handleDemoOutcome` | `dealId` ← `${Deals.id}` |
| WF007 | `handleMeetingEvent` | `eventId` ← `${Events.id}` |
| WF008 | `handleTaskCompletion` | `taskId` ← `${Tasks.id}` |
| WF010a, b, c, d | `sequenceRouter` | `dealId` ← `${Deals.id}` |

6. **Save & Activate** the rule.

The placeholder rules already exist in **active** state — they'll just write a no-op value until you swap the action. Recommended order: swap WF002 first (so new Deals get sequenced), then WF006 (after you create it), then the rest.

---

## Creating WF006 from scratch (Calls module)

The Calls module rejects every placeholder action via the workflow API, so this rule must be set up entirely in the UI.

1. Setup → Automation → Workflow Rules → **+ Create Rule**.
2. **Module:** Calls.
3. **Rule Name:** `WF006 Call Outcome Handler`.
4. **When do you want to execute this rule?** → On Record Action → Created or Edited.
   - If the UI shows multiple Call-trigger variants, pick **Scheduled Call (Create/Edit)** — these are the Calls created by the activity layer's `createStageCall` function.
5. **Criteria (match ALL):**
   - `Sequence_Managed` = `Yes`
   - `What_Id` is not empty (in UI: "Related To is not empty")
   - `Call_Outcome` is not empty
   - `Stale` is not equal to `Yes`
6. **Instant Actions → Add → Function → Custom Function:** `handleCallOutcome`.
7. **Arg mapping:** `callId` ← `${Calls.id}`.
8. Save & Activate.

The `$se_module=Deals` check is handled inside `handleCallOutcome` itself — no need to filter it in the criteria.

---

## After all rules are wired

Run the smoke test from [VERIFICATION_PLAN.md §1](VERIFICATION_PLAN.md):

1. Create a fresh test Lead in your sandbox.
2. The Lead Processor (existing) → `processLead` → creates Deal → hooks into `sequenceRouter`.
3. Watch the function log for:
   - `sequenceRouter hook (processLead): canonicalDealId=...`
   - `automation_event func=sequenceRouter ... action=bootstrap outcome=success`
   - `automation_event func=createStageCall ... action=create outcome=success`
4. Confirm a `Marketing Qualification Call 1` Call appears with `Sequence_Managed=Yes`, `Sequence_Stage=Marketing Qualification`, `Sequence_Attempt=1`.

If any step fails, check the rule's Audit Log in Zoho UI.

## Credential hygiene reminder

Rotate the **Client Secret** for the Self Client OAuth app at https://api-console.zoho.com — the secret was shared in chat earlier in this session.
