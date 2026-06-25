# v6 Activity Lifecycle E2E Report

Date: 2026-06-25
Status: Partially executed against deployed functions

Run key: `V6_LIFECYCLE_20260625_0848`
Target org: Jurnii.io, `org20114906201`

The user published the updated functions before this run. These tests prove selected deployed
behavior, not full source parity. Full commercial/Product/Quote tests and all legacy-field
negative tests remain pending.

## Synthetic Records

| Module | IDs |
| --- | --- |
| Accounts | `991103000001933007` |
| Contacts | `991103000001934001`, `991103000001943001` |
| Deals | `991103000001935001`, `991103000001944001` |
| Tasks | `991103000001936001`, `991103000001945001`, `991103000001966001`, `991103000001972001`, `991103000001973001` |
| Calls | `991103000001949001`, `991103000001949004` |
| Events | `991103000001963001` |

## Results

| Case | Command changed | Evidence | Result |
| --- | --- | --- | --- |
| Activation Manual | Only `Task_Sequence_Type = Manual` on Task `991103000001936001` | Before: blank `Task_Sequence_Type`, `Task_State=Open`, `Task_Status=New`, native `Status=Not Started`. After: `Task_State=Won`, `Task_Status=Closed`, native `Status=Completed`; Contact `991103000001934001` became `Sequence_Type=Manual`, `Sequence_State=Stopped`. | Pass |
| Native Status negative | Only native `Status = Completed` on Task `991103000001945001` | Task stayed `Task_State=Open`, `Task_Status=New`, blank `Task_Sequence_Type`; Contact `991103000001943001` stayed `Sequence_State=Not Activated`, blank `Sequence_Type`. | Pass |
| Call Won | Only `Call_Task_State = Won` on Call `991103000001949001` | Call returned `Call_Task_State=Won`, `Call_Task_Status=Closed`. Immediate duplicate check found one Call and one Task on the Deal at that point. | Pass |
| Call reschedule | Only `Next_Follow_Up_Date = 2026-06-26T10:00:00+01:00` on Call `991103000001949004`, with `Call_Task_State=Open` already present | Field persisted, but WF006 `last_executed_time` did not move after the update and no replacement/stale Call was created. | Fail: workflow criteria gap |
| Meeting booking/create | Created Event `991103000001963001` with `Meeting_Task_State=Open`, `Start_DateTime`, Contact, and Deal | WF007 set `Meeting_Task_Status=New`, set `Reminder_Send_At=2026-06-24T08:00:00+01:00`, and backfilled context mirrors. | Pass |
| Meeting Won | Only `Meeting_Task_State = Won` on Event `991103000001963001` | Event returned `Meeting_Task_State=Won`, `Meeting_Task_Status=Closed`; Contact/Deal advanced through demo progression. | Pass |

## Side Effects

The Meeting path advanced the synthetic Contact/Deal and created expected sequence side effects:
an email audit Task `991103000001966001`, a Manual Review Task `991103000001972001` for a
send-mail failure against the synthetic `example.invalid` contact, and Draft Commercials Task
`991103000001973001`. These were test-only records and were deleted.

## Cleanup

All known synthetic records were deleted successfully:

| Module | Deleted IDs |
| --- | --- |
| Tasks | `991103000001973001`, `991103000001972001`, `991103000001966001`, `991103000001936001`, `991103000001945001` |
| Calls | `991103000001949004`, `991103000001949001` |
| Events | `991103000001963001` |
| Deals | `991103000001935001`, `991103000001944001` |
| Contacts | `991103000001934001`, `991103000001943001` |
| Accounts | `991103000001933007` |

Post-delete word searches for `V6_LIFECYCLE_20260625_0848` returned empty responses in
Tasks, Calls, Events, Deals, Contacts, and Accounts.

## Remaining Required Tests

| Area | Status |
| --- | --- |
| Activation Email / Call | Not run. Use synthetic contacts with explicit consent/test-safe email handling before exercising customer-facing dispatch. |
| Ordinary Task Won / Lost | Not run. |
| Call Lost reason matrix | Not run. |
| Call reschedule | Failed live due WF006 criteria gap; rerun after workflow criteria is fixed. |
| Meeting Lost matrix | Not run. |
| Commercial Task / Meeting valid and blocked evidence | Not run. |
| Legacy outcome negatives | Native Task Status negative passed; `Task_Outcome`, `Call_Outcome`, `Meeting_Outcome`, `Demo_Outcome`, and custom Status-only negatives remain. |
| Safe field deletion | Not attempted. WF004 and layout/dependency checks still block deletion claims. |
