# v6 Live Workflow Readback

Date: 2026-06-25
Target org: Jurnii.io, `org20114906201`

This started as a read-only snapshot from the Zoho workflow and field metadata connector.
After the user published the updated functions on 2026-06-25, the workflow descriptions were
updated live and a partial synthetic lifecycle smoke test was executed. This file still does
not prove source-code parity; it records observed deployed behavior.

## Activity Workflow Rules

| Rule | Module | ID | Trigger | Active | Function action | Live criteria / condition notes | Lifecycle assessment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `WF008 Task Completion Handler` | Tasks | `991103000000784145` | `create_or_edit`, repeat false | Yes | `handleTaskCompletion` action `991103000000780448` | Condition 1 has no criteria. Condition 2 has criteria `Status = Completed` and repeats the same function action plus owner assignment. Description updated live at `2026-06-25T08:47:28+01:00` to mention `Task_State` / `Task_Sequence_Type`, not `Task_Outcome`. | Handler behavior is partially verified, but workflow cleanup remains: remove native-Status duplicate condition. Broad create/edit is only acceptable with the handler idempotency guards. |
| `WFC-SchedEmail` | Tasks | `991103000001499121` | date/datetime on `Due_Date` at 09:00 | Yes | `sendScheduledEmailFromTask` | Date wake-up rule for scheduled email Tasks. | Retain; not a lifecycle command rule. |
| `WF006 Handle Call Outcome` | Calls | `991103000000808046` | `anyaction` | Yes | `handleCallOutcome` action `991103000000780459` | Criteria: `Call_Task_State != ${EMPTY}` AND `Sequence_Managed = Yes`. Description updated live at `2026-06-25T09:01:02+01:00` and explicitly notes date-only edits require criteria coverage. | `Call_Task_State=Won` verified. `Next_Follow_Up_Date`-only reschedule did **not** fire WF006; criteria must be changed to include the scheduling field. |
| `WF007 Event Meeting Handler` | Events | `991103000000782052` | `create_or_edit`, repeat false | Yes | `handleMeetingEvent` action `991103000000780415` | Condition has no criteria. Description updated live at `2026-06-25T08:47:20+01:00` to mention `Meeting_Task_State`, `Meeting_Task_Status`, and `Start_DateTime`, not legacy outcomes. | Meeting create and `Meeting_Task_State=Won` verified. Broad create/edit remains acceptable only because the handler has idempotency guards; narrow criteria where safe. |

## Deal Workflow Rules Relevant To Lifecycle Cleanup

| Rule | Module | ID | Trigger | Active | Function action | Live criteria / condition notes | Lifecycle assessment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `WF004 Commercials Status Handler` | Deals | `991103000000800001` | field update on `Commercials_Status` any value | Yes | `handleCommercialsStatusChange` action `991103000000780404` | Description says it is a legacy bridge to retain until Quote/activity replacement gates pass. | Blocks deletion of `Commercials_Status`; retire only after activity/Quote commercial replacement is deployed and E2E verified. |
| `WF010c Date Router Demo Reminder` | Deals | `991103000000802001` | date/datetime on `Demo_Reminder_Send_At` | Yes | `sendDemoReminder` action `991103000001499062` | Criteria: `Automation_Suppressed != true`. | Retain while Deal reminder mirror remains. Not a lifecycle command field. |

## Field Metadata Evidence

| Module | Field | Field ID | Values / permissions | Assessment |
| --- | --- | --- | --- | --- |
| Calls | `Call_Task_State` | `991103000001702107` | Picklist values: `-None-`, `Open`, `Won`, `Lost`; custom field; visible; read-write for Administrator, Standard, and Team User; associated with Standard layout. | Canonical values exist live. User editability is appropriate for the primary Call command field. |
| Tasks | native `Status` | `991103000000000171` | Native picklist values: `Not Started`, `Deferred`, `In Progress`, `Completed`, `Waiting on someone else`; visible; read-write for Administrator, Standard, and Team User; associated with Standard layout. | Native field cannot be deleted, but current read-write visibility conflicts with the target UX. Hide or make clearly automation-owned after deployment. |
| Deals | `Commercials_Status` | `991103000000783091` | Label is `DEP - Commercials Status`; values include `Not Started`, `Drafting`, `Ready to Send`, `Sent`, `Discussed`, `Intent to Sign`, `Signed`, `Deferred`, `Rejected`; visible/read-write for all profiles; associated with Standard layout. | Deprecated field still live, visible, and workflow-bound by WF004. Not safe to delete. |

## Synthetic Behavior Evidence

Run key: `V6_LIFECYCLE_20260625_0848`

| Case | Records | User/API command under test | Observed deployed behavior | Result |
| --- | --- | --- | --- | --- |
| Activation Manual | Task `991103000001936001`, Contact `991103000001934001`, Deal `991103000001935001` | Updated only `Task_Sequence_Type = Manual` with workflow trigger. | Task became `Task_State=Won`, `Task_Status=Closed`, native `Status=Completed`; Contact became `Sequence_Type=Manual`, `Sequence_State=Stopped`. | Pass |
| Native Task Status negative | Task `991103000001945001`, Contact `991103000001943001`, Deal `991103000001944001` | Updated only native `Status = Completed`. | Task stayed `Task_State=Open`, `Task_Status=New`, blank `Task_Sequence_Type`; Contact stayed `Sequence_State=Not Activated`, blank `Sequence_Type`. Native Status alone did not activate or advance lifecycle. | Pass |
| Call Won | Call `991103000001949001` | Updated only `Call_Task_State = Won`. | Call became `Call_Task_Status=Closed`; duplicate check found no extra Calls/Tasks at that point. | Pass |
| Call reschedule | Call `991103000001949004` | Updated only `Next_Follow_Up_Date` while `Call_Task_State=Open`. | Field persisted, but WF006 `last_executed_time` stayed at the prior Call-state test (`2026-06-25T08:52:31+01:00`); no replacement Call/stale marker was created. | Fail: workflow criteria gap |
| Meeting booking/create | Event `991103000001963001` | Created Event with `Meeting_Task_State=Open`, `Start_DateTime`, Contact, and Deal. | WF007 set `Meeting_Task_Status=New`, set `Reminder_Send_At`, and backfilled context mirrors. | Pass |
| Meeting Won | Event `991103000001963001` | Updated only `Meeting_Task_State = Won`. | Event became `Meeting_Task_Status=Closed`; Contact/Deal progressed through the demo path. | Pass |

Cleanup verification: deleted Tasks `991103000001973001`, `991103000001972001`,
`991103000001966001`, `991103000001936001`, `991103000001945001`; Calls
`991103000001949004`, `991103000001949001`; Event `991103000001963001`; Deals
`991103000001935001`, `991103000001944001`; Contacts `991103000001934001`,
`991103000001943001`; Account `991103000001933007`. Post-delete word searches for
`V6_LIFECYCLE_20260625_0848` returned empty responses in Tasks, Calls, Events, Deals,
Contacts, and Accounts.

## Existing Record Readback Evidence

The examples below were existing records queried before synthetic testing to verify field
presence and current live drift.

| Module | Query | Example records | Evidence |
| --- | --- | --- | --- |
| Tasks | `Task_State = Open` | `991103000001910004`, `991103000001884005`, `991103000001894002` | Existing Sequence Activation Tasks return `Task_State=Open`, `Task_Status=New`, native `Status=Not Started`, and blank `Task_Sequence_Type`. This proves the canonical Task fields are readable on live records. |
| Calls | `Call_Task_State = Open` | `991103000001713008`, `991103000001759004`, `991103000001714006` | Existing sequence Calls return `Call_Task_State=Open`, `Call_Task_Status=New`, `Sequence_Managed=Yes`, and blank `Next_Follow_Up_Date`. This proves the canonical Call fields are readable on live records. |
| Events | `Meeting_Task_State = Won` | `991103000001819008`, `991103000001809001` | Existing historical demo Events return `Meeting_Task_State=Won` while `Meeting_Task_Status=New`. Synthetic Event testing after publish did derive `Meeting_Task_Status=Closed`; old records remain drifted until reprocessed or manually corrected. |

## Required Workflow Follow-Up

1. Clean `WF008`:
   - remove or replace the `Status = Completed` condition branch so native Status is not a user gate;
   - keep only one invocation path for `handleTaskCompletion`;
   - description is already updated.
2. Clean `WF006` reschedule coverage:
   - add `Next_Follow_Up_Date` to the trigger criteria, or add a dedicated field-update rule for it;
   - re-run the reschedule test and verify replacement/stale behavior.
3. Clean `WF007` only if supported without losing booking/reminder behavior; otherwise document the idempotency guards that make broad create/edit safe.
4. Keep `WF004` until the Quote/activity commercial replacement path passes E2E; then disable it before deleting `Commercials_Status`.
