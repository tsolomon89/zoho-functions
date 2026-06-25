# v6 Activity Lifecycle Deployment Manifest

Date: 2026-06-25
Branch: `lifecycle-state-status-v6`
Target org: Jurnii.io, `org20114906201`

This manifest separates repository changes from live CRM configuration. Do not treat any live
workflow, layout, field deletion, or deployed behavior as complete until the corresponding
verification row below is updated with record IDs or CRM metadata evidence.

## Repository Changes

| File | Change |
| --- | --- |
| `v6/activity/handleTaskCompletion.deluge` | Removed `Task_Outcome` routing; ordinary Tasks now route from `Task_State`; Activation Tasks route from `Task_Sequence_Type`; missing Lost Reasons reopen the Task as `Open`/`Working`; successful terminal paths derive `Task_Status=Closed` and native `Status=Completed`; blocked commercial transitions reopen instead of leaving false success. |
| `v6/activity/handleCallOutcome.deluge` | Verifies `Call_Task_State` is the lifecycle command; terminal Won/Lost paths now derive `Call_Task_Status=Closed`; missing `Call_Task_Lost_Reasons` reopens the Call as `Open`/`Working`; no `Call_Outcome` fallback exists. |
| `v6/activity/handleMeetingEvent.deluge` | Verifies `Meeting_Task_State` is the result command; terminal paths derive `Meeting_Task_Status=Closed`; missing `Meeting_Task_Lost_Reasons` reopens as `Open`/`Working`; commercial Meeting loss no longer routes directly to Deal loss. |
| `v6/activity/createAuxTask.deluge` | Created auxiliary Tasks always initialize `Task_State=Open` and `Task_Status=New`. |
| `v6/activity/routeContactSequence.deluge` | Comment terminology clarified so router inputs are described as internal route/activity tokens, not CRM Outcome fields. |
| `v6/processContact.deluge` | Activation Task instructions now tell reps to set only `Task_Sequence_Type`; no native Status or `Task_Outcome` instruction remains. |
| `spec.md` | Activation exception rewritten around `Task_Sequence_Type`; `Task_Outcome` documented as non-command. |
| `docs/v6/PRE_CHANGE_FIELD_AUTHORITY_AUDIT.md` | Added pre-change field-authority audit and lifecycle drift list. |
| `docs/v6/SINGLE_FIELD_AUTOMATION_AUDIT.md` | Rewritten so "single field" means lifecycle command fields, not commercial evidence fields. |
| `docs/v6/SINGLE_FIELD_E2E_TEST_PLAN.md` | Rewritten around canonical activity lifecycle command tests and negative legacy-field tests. |
| `docs/v6/FINAL_CANONICAL_FIELD_MATRIX.md` | Added final canonical field matrix and field disposition list. |
| `docs/v6/ACTIVITY_LIFECYCLE_E2E_REPORT.md` | Added end-to-end test report placeholder with blocked/not-run status. |
| `docs/v6/LIVE_WORKFLOW_READBACK.md` | Added read-only live workflow and field metadata evidence for WF006/WF007/WF008, WF004, native Task Status, `Call_Task_State`, and `Commercials_Status`. |

## Live CRM Changes

No live CRM changes have been applied in this work session.

| Area | Status | Evidence / blocker |
| --- | --- | --- |
| Function deployment | Not deployed | No deployment action has been executed from this branch. Function association readback is available, but the endpoint does not expose or update Deluge source bodies. |
| Workflow criteria update | Not updated | Live readback completed; see `docs/v6/LIVE_WORKFLOW_READBACK.md`. WF008 still has a native `Status = Completed` condition branch and legacy `Task_Outcome` description; WF007 still has a legacy `Meeting_Status`/`Meeting_Outcome` description; WF006 is aligned to `Call_Task_State`. |
| Layout/conditional rules | Not updated | Field metadata readback shows native Task `Status` and deprecated `Commercials_Status` are still visible/read-write for standard profiles. No conditional layout rule editor was exposed. |
| Field deletion | Not deleted | Safe deletion requires live dependency checks for workflows, layouts, validation, reports, views, blueprints, and history. Those checks are not complete. |
| End-to-end tests | Not run | Requires deployed functions and synthetic records in the target org. |

## Required Manual Deployment Steps

1. Deploy the changed Deluge functions:
   - `handleTaskCompletion`
   - `handleCallOutcome`
   - `handleMeetingEvent`
   - `createAuxTask`
   - `processContact`
2. Verify each deployed function body matches this branch before enabling tests.
3. Update workflow criteria and function associations:
   - Tasks: current live rule `WF008` is `create_or_edit` and has two conditions, including a duplicate `Status = Completed` branch. After deploying the new handler, remove the native-Status branch or replace the rule so `handleTaskCompletion` fires from `Task_State` and `Task_Sequence_Type` without requiring native `Status`. Do not trigger from `Task_Outcome`.
   - Calls: current live rule `WF006` is active with criteria `Call_Task_State != ${EMPTY}` and `Sequence_Managed = Yes`. Verify `Next_Follow_Up_Date` edits still fire for rescheduling. Do not trigger from `Call_Outcome`.
   - Events: current live rule `WF007` is broad `create_or_edit` with no criteria and a legacy description. After deploying the new handler, update the description and narrow where possible to creation, `Start_DateTime`, and `Meeting_Task_State` changes. Do not trigger from `Meeting_Outcome`.
   - Retire Deal `Demo_Outcome` workflow only after Event-driven booking/result behavior is deployed and verified.
   - Retire Deal `Commercials_Status` workflow only after Quote/activity commercial evidence behavior is deployed and verified.
4. Update layouts and validation:
   - Show `Task_State`, `Call_Task_State`, and `Meeting_Task_State` as the user command fields.
   - Make custom Status mirrors read-only or hidden for ordinary users.
   - Hide or clearly mark native Task/Call status as automation-owned.
   - Require Lost Reason only when the corresponding Activity State is `Lost`.
   - Show `Task_Sequence_Type` only for Sequence Activation Tasks where possible.
   - Remove legacy Outcome fields from active layouts before deletion.
5. Run the end-to-end tests in `docs/v6/SINGLE_FIELD_E2E_TEST_PLAN.md`.
6. Record all synthetic record IDs, observed transitions, duplicate checks, and cleanup evidence in `docs/v6/ACTIVITY_LIFECYCLE_E2E_REPORT.md`.
7. Only after tests pass, perform the safe deletion sequence for obsolete custom fields.

## Live Function Association Readback

Read-only function association metadata was available on 2026-06-25. It confirms the workflow
automation functions below exist and are associated, but it does not prove their deployed source
matches this branch.

| Name | Module | Association ID | Function ID | Last modified |
| --- | --- | --- | --- | --- |
| `processContact` | Contacts | `991103000000774779` | `991103000000774692` | `2026-06-24T22:22:34+01:00` |
| `processDeal` | Deals | `991103000000774797` | `991103000000774697` | `2026-06-24T22:22:22+01:00` |
| `processLead` | Leads | `991103000000774791` | `991103000000774702` | `2026-06-24T22:22:12+01:00` |
| `processAccount` | Accounts | `991103000000774785` | `991103000000774687` | `2026-06-24T18:08:57+01:00` |
| `handleTaskCompletion` | Tasks | `991103000000780448` | `991103000000780337` | `2026-06-24T17:09:24+01:00` |
| `handleMeetingEvent` | Events | `991103000000780415` | `991103000000780334` | `2026-06-24T12:08:18+01:00` |
| `handleCallOutcome` | Calls | `991103000000780459` | `991103000000780322` | `2026-06-24T12:08:06+01:00` |

## Live Workflow Readback

See `docs/v6/LIVE_WORKFLOW_READBACK.md` for detailed readback. Summary:

| Rule | Current live state | Required next action |
| --- | --- | --- |
| `WF008 Task Completion Handler` | Active `create_or_edit`; condition 1 has no criteria; condition 2 gates on native `Status = Completed`; description still references `Task_Outcome`. | After function deployment, remove native Status gate/duplicate invocation and update description to `Task_State`/`Task_Sequence_Type`. |
| `WF006 Handle Call Outcome` | Active `anyaction`; criteria `Call_Task_State != ${EMPTY}` and `Sequence_Managed = Yes`. | Verify reschedule edits on `Next_Follow_Up_Date` fire; keep no `Call_Outcome` dependency. |
| `WF007 Event Meeting Handler` | Active `create_or_edit`; no criteria; description still references `Meeting_Status`, `Meeting_Outcome`, and `Meeting_Type`. | After function deployment, update description and narrow criteria where safe. |
| `WF004 Commercials Status Handler` | Active field-update rule on `Commercials_Status`. | Retain until replacement commercial path is deployed and verified, then disable before field deletion. |

## Undeployed Items

All repository changes listed above are undeployed until the manual deployment steps are completed.

## Safe Deletion Status

| Field | Module | Status | Reason |
| --- | --- | --- | --- |
| `Task_Outcome` | Tasks | Not deleted | Code command path removed, but live workflow/layout/report/history dependency check is pending. |
| `Call_Outcome` | Calls | Not deleted | v6 code does not read it, but live workflow/layout/report/history dependency check is pending. |
| `Meeting_Outcome` | Events | Not deleted | v6 code does not read it, but live workflow/layout/report/history dependency check is pending. |
| `Meeting_Status` | Events | Not deleted | Candidate legacy lifecycle field; live dependency check pending. |
| `Demo_Outcome` | Deals | Not deleted | Local exports show WF005 dependency; retire only after Event workflow replacement is verified. |
| `Demo_Status` | Deals | Not deleted | Candidate legacy lifecycle field; live dependency check pending. |
| `Commercial_Outcome` | Deals | Not deleted | Candidate legacy commercial outcome field; live dependency check pending. |
| `Commercials_Status` | Deals | Not deleted | Still has a legacy handler/workflow path; retire only after Quote/activity replacement is verified. |
