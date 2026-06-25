# v6 Live Workflow Readback

Date: 2026-06-25
Target org: Jurnii.io, `org20114906201`

This is a read-only snapshot from the Zoho workflow and field metadata connector. It does not
prove the Deluge source in this branch is deployed.

## Activity Workflow Rules

| Rule | Module | ID | Trigger | Active | Function action | Live criteria / condition notes | Lifecycle assessment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `WF008 Task Completion Handler` | Tasks | `991103000000784145` | `create_or_edit`, repeat false | Yes | `handleTaskCompletion` action `991103000000780448` | Condition 1 has no criteria. Condition 2 has criteria `Status = Completed` and repeats the same function action plus owner assignment. Description still says it honors `Task_Outcome`. | Needs cleanup after function deployment: remove native-Status user-command branch/duplicate condition and update description. Broad create/edit is only acceptable with the handler idempotency guards. |
| `WFC-SchedEmail` | Tasks | `991103000001499121` | date/datetime on `Due_Date` at 09:00 | Yes | `sendScheduledEmailFromTask` | Date wake-up rule for scheduled email Tasks. | Retain; not a lifecycle command rule. |
| `WF006 Handle Call Outcome` | Calls | `991103000000808046` | `anyaction` | Yes | `handleCallOutcome` action `991103000000780459` | Criteria: `Call_Task_State != ${EMPTY}` AND `Sequence_Managed = Yes`. | Aligned to `Call_Task_State` for lifecycle routing. Add/verify reschedule coverage for `Next_Follow_Up_Date` after deployment. |
| `WF007 Event Meeting Handler` | Events | `991103000000782052` | `create_or_edit`, repeat false | Yes | `handleMeetingEvent` action `991103000000780415` | Condition has no criteria. Description still says `Meeting_Status + Meeting_Outcome` and `Meeting_Type`. | Needs cleanup after function deployment: update description and, if Zoho supports it safely, narrow criteria to creation, `Start_DateTime`, and `Meeting_Task_State` changes. Broad create/edit is only acceptable with handler idempotency guards. |

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

## Record Readback Evidence

No records were created or mutated for this readback. The examples below are existing records
queried only to verify field presence and current live drift.

| Module | Query | Example records | Evidence |
| --- | --- | --- | --- |
| Tasks | `Task_State = Open` | `991103000001910004`, `991103000001884005`, `991103000001894002` | Existing Sequence Activation Tasks return `Task_State=Open`, `Task_Status=New`, native `Status=Not Started`, and blank `Task_Sequence_Type`. This proves the canonical Task fields are readable on live records. |
| Calls | `Call_Task_State = Open` | `991103000001713008`, `991103000001759004`, `991103000001714006` | Existing sequence Calls return `Call_Task_State=Open`, `Call_Task_Status=New`, `Sequence_Managed=Yes`, and blank `Next_Follow_Up_Date`. This proves the canonical Call fields are readable on live records. |
| Events | `Meeting_Task_State = Won` | `991103000001819008`, `991103000001809001` | Existing demo Events return `Meeting_Task_State=Won` while `Meeting_Task_Status=New`. This confirms live drift: terminal Meeting state is not currently deriving `Meeting_Task_Status=Closed` in the deployed behavior. |

## Required Workflow Follow-Up

1. Deploy this branch's changed Deluge source first.
2. Re-read `WF006`, `WF007`, and `WF008` after deployment to confirm function associations and arguments remain intact.
3. Clean `WF008`:
   - remove or replace the `Status = Completed` condition branch so native Status is not a user gate;
   - keep only one invocation path for `handleTaskCompletion`;
   - update the description to mention `Task_State` and `Task_Sequence_Type`, not `Task_Outcome`.
4. Clean `WF007`:
   - update the description to mention `Meeting_Task_State`, `Meeting_Task_Stage`, and `Start_DateTime`, not `Meeting_Status`, `Meeting_Outcome`, or `Meeting_Type`;
   - narrow the rule if supported without losing booking/reminder behavior, otherwise document the idempotency guards that make broad create/edit safe.
5. Keep `WF006` but verify `Next_Follow_Up_Date` changes still fire the `anyaction` rule for rescheduling.
6. Keep `WF004` until the Quote/activity commercial replacement path passes E2E; then disable it before deleting `Commercials_Status`.
