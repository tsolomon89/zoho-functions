# v6 Live Workflow Readback

Date: 2026-06-25
Target org: Jurnii.io, `org20114906201`

This started as a read-only snapshot from the Zoho workflow and field metadata connector.
After the user published the updated functions on 2026-06-25, workflow descriptions were
updated live, WF006 reschedule criteria were updated live, and partial synthetic lifecycle
smoke tests were executed. The user later published the handler idempotency/status fixes;
post-publish retests are recorded below. This file still does not prove source-code parity;
it records observed deployed behavior.

## Activity Workflow Rules

| Rule | Module | ID | Trigger | Active | Function action | Live criteria / condition notes | Lifecycle assessment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `WF008 Task Completion Handler` | Tasks | `991103000000784145` | `create_or_edit`, repeat false | Yes | `handleTaskCompletion` action `991103000000780448` | Native `Status = Completed` duplicate condition `991103000000797003` was deleted live. Readback at `2026-06-25T12:03:16+01:00` shows one condition only: no criteria, with `handleTaskCompletion` action `991103000000780448` plus owner assignment `991103000000784147`. | Native Status no longer has a separate workflow path. Post-cleanup negative smoke test verified native `Status=Completed` alone did not activate or advance lifecycle. Broad create/edit is only acceptable with the handler idempotency guards. |
| `WFC-SchedEmail` | Tasks | `991103000001499121` | date/datetime on `Due_Date` at 09:00 | Yes | `sendScheduledEmailFromTask` | Date wake-up rule for scheduled email Tasks. | Retain; not a lifecycle command rule. |
| `WF006 Handle Call Outcome` | Calls | `991103000000808046` | `anyaction` | Yes | `handleCallOutcome` action `991103000000780459` | Condition 1: `Call_Task_State != ${EMPTY}` AND `Sequence_Managed = Yes` (`991103000000808047`). Condition 2 added live: `Next_Follow_Up_Date != ${EMPTY}` AND `Sequence_Managed = Yes` (`991103000001977002`). Description updated/read back at `2026-06-25T11:56:44+01:00`. | `Call_Task_State=Won` verified. `Next_Follow_Up_Date`-only reschedule invokes the handler, creates a scheduled replacement Call, and after handler publish, repeated edits update the existing replacement instead of creating duplicates. |
| `WF007 Event Meeting Handler` | Events | `991103000000782052` | `create_or_edit`, repeat false | Yes | `handleMeetingEvent` action `991103000000780415` | Condition has no criteria. Description updated live at `2026-06-25T08:47:20+01:00` to mention `Meeting_Task_State`, `Meeting_Task_Status`, and `Start_DateTime`, not legacy outcomes. | Meeting create, `Meeting_Task_State=Won`, and post-publish `Meeting_Task_State=Lost` no-show status derivation verified. Broad create/edit remains acceptable only because the handler has idempotency guards; narrow criteria where safe. |

## Deal Workflow Rules Relevant To Lifecycle Cleanup

| Rule | Module | ID | Trigger | Active | Function action | Live criteria / condition notes | Lifecycle assessment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `WF001d Process Deal` | Deals | `991103000000663638` | `create_or_edit`, repeat true | Yes | `processDeal` action `991103000000774797` | Condition has no criteria. | Broad processor workflow; not a legacy activity outcome command path. |
| `WF004 Commercials Status Handler` | Deals | `991103000000800001` | field update on `Commercials_Status` any value | Yes | `handleCommercialsStatusChange` action `991103000000780404` | Description says it is a legacy bridge to retain until Quote/activity replacement gates pass. | Blocks deletion of `Commercials_Status`; retire only after activity/Quote commercial replacement is deployed and E2E verified. |
| `WF010c Date Router Demo Reminder` | Deals | `991103000000802001` | date/datetime on `Demo_Reminder_Send_At` | Yes | `sendDemoReminder` action `991103000001499062` | Criteria: `Automation_Suppressed != true`. | Retain while Deal reminder mirror remains. Not a lifecycle command field. |
| `WF010d Date Router Comm Follow-Up` | Deals | `991103000000790038` | date/datetime on `Next_Comm_Follow_Up_Date` | Yes | `sendCommercialFollowUp` action `991103000001499072` | Criteria: `Automation_Suppressed != true`. | Retain while Deal commercial follow-up date router remains. Not an activity lifecycle command field. |

## Active Workflow Legacy Surface Audit

Readback at 2026-06-25 after the WF006/WF008 edits returned 18 active workflow rules across
the org. No active workflow summary or detailed rule readback showed criteria on
`Task_Outcome`, `Call_Outcome`, `Meeting_Outcome`, or `Demo_Outcome`. The remaining active
legacy lifecycle-adjacent workflow dependency found in this pass is `WF004` on Deal
`Commercials_Status`.

This does not clear layouts, validation rules, reports, views, blueprints, formulas, or
historical value migration. It only narrows the live workflow dependency evidence.

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

Run key: `V6_RESCHEDULE_20260625_1151`

| Case | Records | User/API command under test | Observed deployed behavior | Result |
| --- | --- | --- | --- | --- |
| WF006 reschedule criteria retest | Source Call `991103000001963011`, replacement Calls `991103000001982001` and `991103000001985001` | Updated only `Next_Follow_Up_Date` while `Call_Task_State=Open` and `Sequence_Managed=Yes`. First value: `2026-06-26T10:00:00+01:00`; second value: `2026-06-27T10:00:00+01:00`. | Condition 2 fired and created replacement Calls with `Call_Task_State=Open`, `Call_Task_Status=New`, same Contact/Deal/stage/attempt, and matching `Call_Start_Time`. Related-list readback was required because search by `What_Id` lagged/returned empty. Re-editing the original source Call created a second replacement, exposing the handler idempotency gap later fixed and retested in `V6_RESCHEDULE_IDEMP_20260625_1232`. | Superseded by post-publish pass below |

Cleanup verification: deleted Calls `991103000001963011`, `991103000001982001`,
`991103000001985001`; Deal `991103000001931014`; Contact `991103000001945003`;
Account `991103000001963009`. No related Tasks or Events were found. Post-delete word
searches for `V6_RESCHEDULE_20260625_1151` returned empty responses in Tasks, Calls,
Events, Deals, Contacts, and Accounts.

Run key: `V6_RESCHEDULE_IDEMP_20260625_1232`

| Case | Records | User/API command under test | Observed deployed behavior | Result |
| --- | --- | --- | --- | --- |
| WF006 reschedule idempotency after handler publish | Source Call `991103000001946014`, replacement Call `991103000002014001`, Contact `991103000001945011`, Deal `991103000001943011` | Updated only `Next_Follow_Up_Date` twice on the same source Call while `Call_Task_State=Open` and `Sequence_Managed=Yes`. First value: `2026-06-26T10:00:00+01:00`; second value: `2026-06-27T10:00:00+01:00`. | First edit created replacement Call `991103000002014001`. Second edit updated the same replacement to `Call_Start_Time=2026-06-27T10:00:00+01:00`. Related-list readback showed only the source Call and one replacement Call. | Pass |

Cleanup verification: deleted Calls `991103000001946014`, `991103000002014001`;
Deals `991103000001943011`, `991103000001983002`; Contact `991103000001945011`;
and Account `991103000001989011`. Post-delete word searches for
`V6_RESCHEDULE_IDEMP_20260625_1232` returned empty responses in Tasks, Calls,
Events, Deals, Contacts, and Accounts.

Run key: `V6_WF008_NATIVE_STATUS_20260625_1204`

| Case | Records | User/API command under test | Observed deployed behavior | Result |
| --- | --- | --- | --- | --- |
| WF008 native Status negative after condition cleanup | Task `991103000001975007`, Contact `991103000001962009`, Deal `991103000001950009`, Account `991103000001984005` | Updated only native Task `Status = Completed` on a Sequence Activation Task with blank `Task_Sequence_Type`. | WF008 executed once at `2026-06-25T12:04:23+01:00`. Task stayed `Task_State=Open`, `Task_Status=New`, blank `Task_Sequence_Type`; Contact stayed `Sequence_State=Not Activated`, blank `Sequence_Type`. | Pass |

Cleanup verification: deleted Task `991103000001975007`, Deal `991103000001950009`,
Contact `991103000001962009`, and Account `991103000001984005`. Post-delete word
searches for `V6_WF008_NATIVE_STATUS_20260625_1204` returned empty responses in Tasks,
Deals, Contacts, and Accounts.

Run key: `V6_TASK_STATE_20260625_1245`

| Case | Records | User/API command under test | Observed deployed behavior | Result |
| --- | --- | --- | --- | --- |
| Ordinary Task Won | Data Repair Task `991103000001981030`, Contact `991103000001949009`, Deal `991103000001981018`, downstream Call `991103000002010005` | Updated only `Task_State=Won`; native Task `Status` and custom `Task_Status` were not manually changed. | Task became `Task_State=Won`, `Task_Status=Closed`, native `Status=Completed`; Contact stayed Open/Working and Running, with `Sequence_Stage=Call`, `Sequence_Step=1`; Deal stayed Open/Working; one downstream Call was created. | Pass |
| Task Lost - Invalid / Bad Data | Enrichment Task `991103000001981031`, Data Repair Task `991103000001952005`, Contact `991103000001949010`, Deal `991103000001981019` | Updated only `Task_State=Lost` and `Task_Lost_Reasons=Invalid / Bad Data`. | Source Task became `Task_State=Lost`, `Task_Status=Closed`, native `Status=Completed`; a Data Repair Task was created with `Task_State=Open`, `Task_Status=New`, native `Status=Not Started`, `Blocks_Sequence=Yes`; Contact and Deal stayed Open. | Pass |

Cleanup verification: deleted Tasks `991103000001981030`, `991103000001981031`,
`991103000001952005`; Call `991103000002010005`; Deals `991103000001981018`,
`991103000001981019`; Contacts `991103000001949009`, `991103000001949010`; and
Account `991103000001943020`. Post-delete word searches for `V6_TASK_STATE_20260625_1245`
returned empty responses in Tasks, Calls, Events, Deals, Contacts, and Accounts.

Run key: `V6_LEGACY_NEG_20260625_1210`

| Case | Records | User/API command under test | Observed deployed behavior | Result |
| --- | --- | --- | --- | --- |
| Legacy Outcome negatives | Task `991103000001984007`, Call `991103000001935007`, Event `991103000001944008`, Deal `991103000001977025`, Contact `991103000001950015` | Updated only retired fields: `Task_Outcome=Activate Email First`, `Call_Outcome=Positive`, `Meeting_Outcome=Attended - Qualified`, Deal `Demo_Outcome=Commercials Requested`. | Contact stayed Not Activated/Open at Demo Confirmation; Deal stayed Open/New at `Opportunity_Stage=Demo Confirmation`; Task/Call/Event stayed `*_State=Open`; related-list checks showed one Task, one Call, one Event. | Pass |
| Custom activity Status-only negatives | Same synthetic Task/Call/Event | Updated only `Task_Status=Closed`, `Call_Task_Status=Closed`, and `Meeting_Task_Status=Closed` while State fields remained Open. | No sequence advancement, Contact activation, Deal lifecycle change, or duplicate activity creation occurred. The custom Status values persisted as entered, so layout/read-only hardening remains required. | Pass for no advancement; UX hardening pending |

Cleanup verification: deleted Task `991103000001984007`, Call `991103000001935007`,
Event `991103000001944008`, Deal `991103000001977025`, Contact `991103000001950015`,
and Account `991103000001949007`. Post-delete word searches for
`V6_LEGACY_NEG_20260625_1210` returned empty responses in Tasks, Calls, Events, Deals,
Contacts, and Accounts.

Run key: `V6_ACT_CALL_20260625_1218`

| Case | Records | User/API command under test | Observed deployed behavior | Result |
| --- | --- | --- | --- | --- |
| Activation Call | Task `991103000001962019`, Contact `991103000001962016`, Deal `991103000001934012`, Call `991103000002000001` | Updated only `Task_Sequence_Type = Call` on a Sequence Activation Task. Native Task `Status` was not manually changed. | Task became `Task_State=Won`, `Task_Status=Closed`, native `Status=Completed`; Contact became `Sequence_Type=Call`, `Sequence_State=Running`, `Sequence_Stage=Call`, `Sequence_Step=1`; Deal stayed Open and became `Opportunity_Status=Working`; one new managed Call was created for `Marketing Consent Call 1`. | Pass |

Cleanup verification: deleted Call `991103000002000001`, Task `991103000001962019`,
Deal `991103000001934012`, Contact `991103000001962016`, and Account
`991103000001931027`. Post-delete word searches for `V6_ACT_CALL_20260625_1218`
returned empty responses in Tasks, Calls, Deals, Contacts, and Accounts.

Run key: `V6_MEETING_LOST_20260625_1224`

| Case | Records | User/API command under test | Observed deployed behavior | Result |
| --- | --- | --- | --- | --- |
| Meeting Lost - No Meeting / Demo | Event `991103000001962021`, Contact `991103000001945007`, Deal `991103000001930008` | Updated `Meeting_Task_State=Lost` and `Meeting_Task_Lost_Reasons=No Meeting / Demo`. | Recovery behavior ran locally: Contact stayed `State=Open`, moved to `Stage=Demo Booking`, and `Sequence_Stage=Call`; Deal stayed `Opportunity_State=Open`, `Opportunity_Status=Working`. No related Tasks or Calls were found. Defect: Event stayed `Meeting_Task_Status=New` instead of deriving `Closed`. | Partial: no Deal loss; Event status bug found |

Cleanup verification: deleted Event `991103000001962021`, Deal `991103000001930008`,
Contact `991103000001945007`, and Account `991103000001958005`. Post-delete word
searches for `V6_MEETING_LOST_20260625_1224` returned empty responses in Tasks, Calls,
Events, Deals, Contacts, and Accounts.

Run key: `V6_MEETING_LOST_RETEST_20260625_1232`

| Case | Records | User/API command under test | Observed deployed behavior | Result |
| --- | --- | --- | --- | --- |
| Meeting Lost - No Meeting / Demo after handler publish | Event `991103000001946020`, Contact `991103000001930014`, Deal `991103000001981006` | Updated only `Meeting_Task_State=Lost` and `Meeting_Task_Lost_Reasons=No Meeting / Demo`. | Event became `Meeting_Task_Status=Closed`; Contact stayed `State=Open`, `Stage=Demo Booking`, `Sequence_State=Running`, `Sequence_Stage=Call`; Deal stayed `Opportunity_State=Open`, `Opportunity_Status=Working`. Recovery created Call `991103000002016001`, email audit Task `991103000002013003`, and Manual Review Task `991103000001993004` for synthetic send-mail failure. | Pass |

Cleanup verification: deleted Tasks `991103000001993004`, `991103000002013003`;
Call `991103000002016001`; Event `991103000001946020`; Deals `991103000001981006`,
`991103000001990005`; Contact `991103000001930014`; and Account `991103000001944011`.
Post-delete word searches for `V6_MEETING_LOST_RETEST_20260625_1232` returned empty
responses in Tasks, Calls, Events, Deals, Contacts, and Accounts.

## Existing Record Readback Evidence

The examples below were existing records queried before synthetic testing to verify field
presence and current live drift.

| Module | Query | Example records | Evidence |
| --- | --- | --- | --- |
| Tasks | `Task_State = Open` | `991103000001910004`, `991103000001884005`, `991103000001894002` | Existing Sequence Activation Tasks return `Task_State=Open`, `Task_Status=New`, native `Status=Not Started`, and blank `Task_Sequence_Type`. This proves the canonical Task fields are readable on live records. |
| Calls | `Call_Task_State = Open` | `991103000001713008`, `991103000001759004`, `991103000001714006` | Existing sequence Calls return `Call_Task_State=Open`, `Call_Task_Status=New`, `Sequence_Managed=Yes`, and blank `Next_Follow_Up_Date`. This proves the canonical Call fields are readable on live records. |
| Events | `Meeting_Task_State = Won` | `991103000001819008`, `991103000001809001` | Existing historical demo Events return `Meeting_Task_State=Won` while `Meeting_Task_Status=New`. Synthetic Event testing after publish did derive `Meeting_Task_Status=Closed`; old records remain drifted until reprocessed or manually corrected. |

## Required Workflow Follow-Up

1. Continue the remaining activity matrix: remaining Task Lost reasons, remaining Call Lost reasons, remaining Meeting Lost reasons, and commercial Task/Meeting valid/blocked evidence.
2. Clean `WF007` only if supported without losing booking/reminder behavior; otherwise document the idempotency guards that make broad create/edit safe.
3. Keep `WF004` until the Quote/activity commercial replacement path passes E2E; then disable it before deleting `Commercials_Status`.
