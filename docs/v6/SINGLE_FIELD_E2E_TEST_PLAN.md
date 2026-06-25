# v6 Single-Field E2E Test Plan

This plan verifies the activity lifecycle invariant. Commercial evidence is included only
to prove that downstream automation can complete after the single lifecycle command is set.

Use fresh synthetic records with a unique run key. Record every created ID and delete all
synthetic records after the run.

## Workflow Preconditions

| Module | Required trigger |
| --- | --- |
| Tasks | `Task_State` changes and `Task_Sequence_Type` changes for Activation Tasks |
| Calls | `Call_Task_State` changes and `Next_Follow_Up_Date` changes for rescheduling |
| Events | `Meeting_Task_State` changes, creation, and `Start_DateTime` changes |

Negative preconditions:

- No workflow may require the user to update native `Tasks.Status`.
- No workflow may trigger lifecycle routing from `Task_Outcome`, `Call_Outcome`,
  `Meeting_Outcome`, or `Demo_Outcome`.

## Tests

| ID | Scenario | User changes exactly | Expected result |
| --- | --- | --- | --- |
| SF-A1 | Activation Email | `Task_Sequence_Type = Email` | Email-first route activates; Task becomes `Task_State=Won`, `Task_Status=Closed`, native `Status=Completed`; exactly one next action is created |
| SF-A2 | Activation Call | `Task_Sequence_Type = Call` | Call-first route activates; activation Task closes automatically; no native Status user edit required |
| SF-A3 | Activation Manual | `Task_Sequence_Type = Manual` | Automated dispatch stops/manual mode applies; activation Task still closes as Won |
| SF-T1 | Ordinary Task Won | `Task_State = Won` | Task closes; Task Type success behavior runs once; Contact/Deal rollup is correct; no duplicate transition |
| SF-T2 | Task Lost | `Task_State = Lost`, `Task_Lost_Reasons = No Response` | Local loss behavior runs; Task closes; Deal is not automatically closed |
| SF-T3 | Task Lost missing reason | `Task_State = Lost` only | Task is restored to `Open`/`Working`; Manual Review is created; no terminal transition |
| SF-C1 | Call Won | `Call_Task_State = Won` | Call closes; correct next sequence/stage action occurs |
| SF-C2 | Call Lost no response | `Call_Task_State = Lost`, `Call_Task_Lost_Reasons = No Response` | Local cadence/recovery behavior occurs; Deal remains open unless Contact viability separately closes it |
| SF-C3 | Call Lost bad data | `Call_Task_State = Lost`, `Call_Task_Lost_Reasons = Invalid / Bad Data` | Data Repair task is created; Deal is not closed |
| SF-C4 | Call Lost no authority | `Call_Task_State = Lost`, `Call_Task_Lost_Reasons = No Authority` | Manual Review/find decision-maker task is created; Deal is not closed |
| SF-C5 | Call reschedule | `Call_Task_State = Open`, `Next_Follow_Up_Date = <datetime>` | Replacement/scheduled Call is created; no custom State/Status value such as Deferred or Rescheduled is introduced |
| SF-M1 | Meeting booking | Create Event or update `Start_DateTime` while state is Open/blank | Reminder/context mirrors are set; first-booking progression occurs once |
| SF-M2 | Meeting Won demo | `Meeting_Task_State = Won` | Demo route advances correctly; `Meeting_Task_Status=Closed` |
| SF-M3 | Meeting Lost demo | `Meeting_Task_State = Lost`, `Meeting_Task_Lost_Reasons = No Meeting / Demo` | Local recovery/reschedule behavior occurs; Deal is not automatically closed |
| SF-M4 | Commercial Meeting Won valid | `Meeting_Task_State = Won` with required Product/contract evidence | Product/Quote evidence applies; Event closes; Deal/Quote rollup is correct |
| SF-M5 | Commercial Meeting Won blocked | `Meeting_Task_State = Won` with missing/invalid evidence | Event is restored to `Open`/`Working`; Manual Review is created |
| SF-Q1 | Commercial Task valid | `Task_State = Won` with required Product/contract evidence | Quote/Deal processing completes; Task closes |
| SF-Q2 | Commercial Task blocked | `Task_State = Won` with missing/invalid evidence | Task is restored to `Open`/`Working`; Manual Review is created |
| SF-N1 | Legacy Task outcome ignored | Change only `Task_Outcome` | No sequence advancement |
| SF-N2 | Legacy Call outcome ignored | Change only `Call_Outcome` | No call routing |
| SF-N3 | Legacy Meeting/Demo outcomes ignored | Change only `Meeting_Outcome` or Deal `Demo_Outcome` | No meeting lifecycle routing |
| SF-N4 | Native Task Status ignored | Change only native `Tasks.Status` | No activation or ordinary Task advancement |
| SF-N5 | Custom Status ignored | Change only `Task_Status`, `Call_Task_Status`, or `Meeting_Task_Status` | No lifecycle advancement |

## Evidence To Capture

- Synthetic Account, Contact, Deal, Task, Call, Event, Quote IDs.
- Before/after field snapshots for State, Status, Lost Reason, native Status, stage, sequence, and related next activities.
- Automation log entries for each handler.
- Duplicate checks for Tasks, Calls, Events, Quotes, and next sequence actions.
- Cleanup confirmation for all synthetic records.

## Acceptance

- The lifecycle command field alone is sufficient for each positive path.
- Status fields are derived by automation.
- Lost Reason has no effect unless State is Lost.
- Activity Lost remains local by default and does not directly close the Deal.
- Legacy Outcome fields and native Status-only edits do not advance automation.
