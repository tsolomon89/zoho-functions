# v6 Activity Lifecycle Deployment Manifest

Date: 2026-06-25
Branch: `main`
Target org: Jurnii.io, `org20114906201`

This manifest separates repository changes from live CRM configuration. The user published the
updated functions on 2026-06-25; selected deployed behavior was then verified with synthetic
records. Do not treat untested paths, layout changes, field deletion, or source-body parity as
complete until the corresponding row below has CRM metadata or record evidence.

## Repository Changes

| File | Change |
| --- | --- |
| `v6/activity/handleTaskCompletion.deluge` | Removed `Task_Outcome` routing; ordinary Tasks now route from `Task_State`; Activation Tasks route from `Task_Sequence_Type`; missing Lost Reasons reopen the Task as `Open`/`Working`; successful terminal paths derive `Task_Status=Closed` and native `Status=Completed`; blocked commercial transitions reopen instead of leaving false success. |
| `v6/activity/handleCallOutcome.deluge` | Verifies `Call_Task_State` is the lifecycle command; terminal Won/Lost paths now derive `Call_Task_Status=Closed`; missing `Call_Task_Lost_Reasons` reopens the Call as `Open`/`Working`; no `Call_Outcome` fallback exists. Added reschedule idempotency logic to reuse/collapse an existing scheduled replacement Call before creating a new one; published behavior was verified with `V6_RESCHEDULE_IDEMP_20260625_1232`. |
| `v6/activity/handleMeetingEvent.deluge` | Verifies `Meeting_Task_State` is the result command; terminal paths derive `Meeting_Task_Status=Closed`; missing `Meeting_Task_Lost_Reasons` reopens as `Open`/`Working`; commercial Meeting loss no longer routes directly to Deal loss. Added fix to close Lost Events before downstream recovery routing; published behavior was verified with `V6_MEETING_LOST_RETEST_20260625_1232`. |
| `v6/activity/createAuxTask.deluge` | Created auxiliary Tasks always initialize `Task_State=Open` and `Task_Status=New`. |
| `v6/activity/routeContactSequence.deluge` | Comment terminology clarified so router inputs are described as internal route/activity tokens, not CRM Outcome fields. |
| `v6/processContact.deluge` | Activation Task instructions now tell reps to set only `Task_Sequence_Type`; no native Status or `Task_Outcome` instruction remains. |
| `spec.md` | Activation exception rewritten around `Task_Sequence_Type`; `Task_Outcome` documented as non-command. |
| `docs/v6/PRE_CHANGE_FIELD_AUTHORITY_AUDIT.md` | Added pre-change field-authority audit and lifecycle drift list. |
| `docs/v6/SINGLE_FIELD_AUTOMATION_AUDIT.md` | Rewritten so "single field" means lifecycle command fields, not commercial evidence fields. |
| `docs/v6/SINGLE_FIELD_E2E_TEST_PLAN.md` | Rewritten around canonical activity lifecycle command tests and negative legacy-field tests. |
| `docs/v6/FINAL_CANONICAL_FIELD_MATRIX.md` | Added final canonical field matrix and field disposition list. |
| `docs/v6/ACTIVITY_LIFECYCLE_E2E_REPORT.md` | Added end-to-end test report with synthetic record IDs, observed transitions, cleanup, WF006 reschedule retest evidence, and post-publish handler retest evidence. |
| `docs/v6/LIVE_WORKFLOW_READBACK.md` | Added live workflow and field metadata evidence for WF006/WF007/WF008, WF004, native Task Status, `Call_Task_State`, and `Commercials_Status`; updated after WF006 criteria/description changes. |

## Live CRM Changes

| Area | Status | Evidence / blocker |
| --- | --- | --- |
| Function deployment | Published by user; behavior partially verified | The connector does not expose Deluge source bodies, so source parity is not directly provable. Synthetic tests verified activation Manual/Call, ordinary Task Won/Lost, native Status negatives, Call Won, Call Lost bad-data, Call reschedule idempotency, Meeting create/Won, and Meeting Lost no-show status derivation. |
| Workflow descriptions | Updated live | WF008 and WF007 descriptions were updated and read back at `2026-06-25T08:47+01:00`; WF006 was updated again and read back at `2026-06-25T11:56:44+01:00` after the reschedule criteria fix. Legacy `Task_Outcome` / `Meeting_Outcome` wording was removed. |
| Workflow criteria update | Partially complete | WF006 now has a second condition for `Next_Follow_Up_Date != ${EMPTY}` and `Sequence_Managed = Yes`, verified by replacement Call creation. WF008 duplicate native `Status = Completed` condition was deleted live and read back at `2026-06-25T12:03:16+01:00`; native Status negative smoke test still passed. WF007 remains broad create/edit with no criteria but passed create and state smoke tests. |
| Active workflow legacy-field audit | Partially complete | Active workflow readback on `2026-06-25` found no active workflow criteria on `Task_Outcome`, `Call_Outcome`, `Meeting_Outcome`, or `Demo_Outcome`. `WF004` still actively depends on Deal `Commercials_Status`. Layout, validation, report/view, blueprint, formula, and history dependency checks remain pending. |
| Handler idempotency update | Published behavior verified | `V6_RESCHEDULE_IDEMP_20260625_1232` edited the same source Call's `Next_Follow_Up_Date` twice. The first edit created replacement Call `991103000002014001`; the second edit updated that same replacement to `2026-06-27T10:00:00+01:00` and did not create a duplicate. |
| Meeting Lost status update | Published behavior verified | `V6_MEETING_LOST_RETEST_20260625_1232` set only `Meeting_Task_State=Lost` and `Meeting_Task_Lost_Reasons=No Meeting / Demo`; Event `991103000001946020` derived `Meeting_Task_Status=Closed`, while Contact and Deal stayed Open. |
| Layout/conditional rules | Not updated | Field metadata readback shows native Task `Status` and deprecated `Commercials_Status` are still visible/read-write for standard profiles. No conditional layout rule editor was exposed. |
| Field deletion | Not deleted | Safe deletion requires live dependency checks for workflows, layouts, validation, reports, views, blueprints, and history. Those checks are not complete. |
| End-to-end tests | Partially run | See `docs/v6/ACTIVITY_LIFECYCLE_E2E_REPORT.md`. Activation Manual, Activation Call, ordinary Task Won/Lost, native Status negatives, Call Won, Call Lost bad-data, Call reschedule idempotency, Meeting create/Won, Meeting Lost no-show, legacy Outcome negatives, and custom activity Status-only negatives have live evidence. All known synthetic records were deleted and post-delete searches were empty. |

## Required Manual Deployment Steps

1. Verify each deployed function body matches this branch where Zoho UI/source access allows it.
2. Update workflow criteria and function associations:
   - Tasks: current live rule `WF008` is `create_or_edit` with one broad condition and no native-Status-specific branch. Keep `handleTaskCompletion` idempotency guards; do not trigger from `Task_Outcome`.
   - Calls: current live rule `WF006` is active with condition 1 `Call_Task_State != ${EMPTY}` and `Sequence_Managed = Yes`, plus condition 2 `Next_Follow_Up_Date != ${EMPTY}` and `Sequence_Managed = Yes`. Do not trigger from `Call_Outcome`. Repeated source date edits now update the existing scheduled replacement; continue the remaining Call Lost reason matrix.
   - Events: current live rule `WF007` is broad `create_or_edit` with no criteria. Description is now canonical; narrow where possible to creation, `Start_DateTime`, and `Meeting_Task_State` changes. Do not trigger from `Meeting_Outcome`.
   - Retire Deal `Demo_Outcome` workflow only after Event-driven booking/result behavior is deployed and verified.
   - Retire Deal `Commercials_Status` workflow only after Quote/activity commercial evidence behavior is deployed and verified.
4. Update layouts and validation:
   - Show `Task_State`, `Call_Task_State`, and `Meeting_Task_State` as the user command fields.
   - Make custom Status mirrors read-only or hidden for ordinary users.
   - Hide or clearly mark native Task/Call status as automation-owned.
   - Require Lost Reason only when the corresponding Activity State is `Lost`.
   - Show `Task_Sequence_Type` only for Sequence Activation Tasks where possible.
   - Remove legacy Outcome fields from active layouts before deletion.
5. Continue the end-to-end tests in `docs/v6/SINGLE_FIELD_E2E_TEST_PLAN.md`, starting with the remaining Task/Call/Meeting Lost reason matrices and commercial Task/Meeting evidence paths.
6. Record all new synthetic record IDs, observed transitions, duplicate checks, and cleanup evidence in `docs/v6/ACTIVITY_LIFECYCLE_E2E_REPORT.md`.
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
| `WF008 Task Completion Handler` | Active `create_or_edit`; one condition only, with no criteria; duplicate native `Status = Completed` condition removed; description updated to canonical fields. | Retain broad rule only with handler idempotency guards, or narrow later if Zoho can express `Task_State` / `Task_Sequence_Type` change criteria without losing create behavior. |
| `WF006 Handle Call Outcome` | Active `anyaction`; condition 1 uses `Call_Task_State != ${EMPTY}` and `Sequence_Managed = Yes`; condition 2 uses `Next_Follow_Up_Date != ${EMPTY}` and `Sequence_Managed = Yes`; description updated. Date-only reschedule creates replacement Calls, and repeated edits now update the existing replacement instead of duplicating. | Continue the remaining Call Lost reason matrix and keep handler idempotency guards. |
| `WF007 Event Meeting Handler` | Active `create_or_edit`; no criteria; description updated to canonical fields. | Narrow criteria where safe, or explicitly retain broad rule with handler idempotency rationale. |
| `WF004 Commercials Status Handler` | Active field-update rule on `Commercials_Status`. | Retain until replacement commercial path is deployed and verified, then disable before field deletion. |

## Untested / Unproven Items

The user has published the functions, but the connector cannot compare live source bodies to the
repository. The following remain unproven:

- Activation Email route.
- Remaining Task Lost reasons and commercial Task valid/blocked paths.
- Call Lost reason matrix beyond `Invalid / Bad Data`.
- Meeting Lost reason matrix beyond `No Meeting / Demo`.
- Deal `Commercial_Outcome` / `Commercials_Status` negatives after the commercial replacement path is ready; `Commercials_Status` is intentionally still active through WF004.
- Layout/validation behavior and safe field deletion.
- Non-workflow dependency checks for legacy fields: layouts, validation rules, reports/views, blueprints, formulas, and historical value migration.

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
