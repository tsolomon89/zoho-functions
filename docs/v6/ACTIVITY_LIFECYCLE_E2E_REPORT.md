# v6 Activity Lifecycle E2E Report

Date: 2026-06-25
Status: Partially executed against deployed functions

Run keys: `V6_LIFECYCLE_20260625_0848`, `V6_RESCHEDULE_20260625_1151`,
`V6_WF008_NATIVE_STATUS_20260625_1204`, `V6_LEGACY_NEG_20260625_1210`,
`V6_ACT_CALL_20260625_1218`, `V6_MEETING_LOST_20260625_1224`,
`V6_CALL_LOST_BAD_DATA_20260625_1231`, `V6_RESCHEDULE_IDEMP_20260625_1232`,
`V6_MEETING_LOST_RETEST_20260625_1232`, `V6_TASK_STATE_20260625_1245`
Target org: Jurnii.io, `org20114906201`

The user published the updated functions before this run. These tests prove selected deployed
behavior, not full source parity. Full commercial/Product/Quote tests and the remaining
legacy/commercial negative tests remain pending.

## Synthetic Records

| Module | IDs |
| --- | --- |
| Accounts | `991103000001933007` |
| Contacts | `991103000001934001`, `991103000001943001` |
| Deals | `991103000001935001`, `991103000001944001` |
| Tasks | `991103000001936001`, `991103000001945001`, `991103000001966001`, `991103000001972001`, `991103000001973001` |
| Calls | `991103000001949001`, `991103000001949004` |
| Events | `991103000001963001` |

Additional WF006 reschedule retest records created after the live workflow criteria update:

| Module | IDs |
| --- | --- |
| Accounts | `991103000001963009` |
| Contacts | `991103000001945003` |
| Deals | `991103000001931014` |
| Calls | `991103000001963011`, `991103000001982001`, `991103000001985001` |

Additional WF008 post-cleanup native Status negative records:

| Module | IDs |
| --- | --- |
| Accounts | `991103000001984005` |
| Contacts | `991103000001962009` |
| Deals | `991103000001950009` |
| Tasks | `991103000001975007` |

Additional legacy Outcome / custom Status negative records:

| Module | IDs |
| --- | --- |
| Accounts | `991103000001949007` |
| Contacts | `991103000001950015` |
| Deals | `991103000001977025` |
| Tasks | `991103000001984007` |
| Calls | `991103000001935007` |
| Events | `991103000001944008` |

Additional Activation Call records:

| Module | IDs |
| --- | --- |
| Accounts | `991103000001931027` |
| Contacts | `991103000001962016` |
| Deals | `991103000001934012` |
| Tasks | `991103000001962019` |
| Calls | `991103000002000001` |

Additional Meeting Lost records:

| Module | IDs |
| --- | --- |
| Accounts | `991103000001958005` |
| Contacts | `991103000001945007` |
| Deals | `991103000001930008` |
| Events | `991103000001962021` |

Additional Call Lost bad-data records:

| Module | IDs |
| --- | --- |
| Accounts | `991103000001934016` |
| Contacts | `991103000001975018` |
| Deals | `991103000001963016` |
| Calls | `991103000001937017` |
| Tasks | `991103000001954006` |

Additional Call reschedule idempotency retest records after handler publish:

| Module | IDs |
| --- | --- |
| Accounts | `991103000001989011` |
| Contacts | `991103000001945011` |
| Deals | `991103000001943011`, `991103000001983002` |
| Calls | `991103000001946014`, `991103000002014001` |

Additional Meeting Lost retest records after handler publish:

| Module | IDs |
| --- | --- |
| Accounts | `991103000001944011` |
| Contacts | `991103000001930014` |
| Deals | `991103000001981006`, `991103000001990005` |
| Tasks | `991103000001993004`, `991103000002013003` |
| Calls | `991103000002016001` |
| Events | `991103000001946020` |

Additional ordinary Task State records:

| Module | IDs |
| --- | --- |
| Accounts | `991103000001943020` |
| Contacts | `991103000001949009`, `991103000001949010` |
| Deals | `991103000001981018`, `991103000001981019` |
| Tasks | `991103000001981030`, `991103000001981031`, `991103000001952005` |
| Calls | `991103000002010005` |

## Results

| Case | Command changed | Evidence | Result |
| --- | --- | --- | --- |
| Activation Manual | Only `Task_Sequence_Type = Manual` on Task `991103000001936001` | Before: blank `Task_Sequence_Type`, `Task_State=Open`, `Task_Status=New`, native `Status=Not Started`. After: `Task_State=Won`, `Task_Status=Closed`, native `Status=Completed`; Contact `991103000001934001` became `Sequence_Type=Manual`, `Sequence_State=Stopped`. | Pass |
| Activation Call | Only `Task_Sequence_Type = Call` on Task `991103000001962019` | Task became `Task_State=Won`, `Task_Status=Closed`, native `Status=Completed`; Contact `991103000001962016` became `Sequence_Type=Call`, `Sequence_State=Running`, `Sequence_Stage=Call`, `Sequence_Step=1`; Deal stayed `Opportunity_State=Open`, `Opportunity_Status=Working`; one new Call `991103000002000001` was created with `Sequence_Managed=Yes`, `Sequence_Stage=Marketing Consent`, `Sequence_Attempt=1`, `Call_Task_State=Open`, `Call_Task_Status=New`. | Pass |
| Native Status negative | Only native `Status = Completed` on Task `991103000001945001` | Task stayed `Task_State=Open`, `Task_Status=New`, blank `Task_Sequence_Type`; Contact `991103000001943001` stayed `Sequence_State=Not Activated`, blank `Sequence_Type`. | Pass |
| Native Status negative after WF008 condition cleanup | Only native `Status = Completed` on Task `991103000001975007` | WF008 had only one broad create/edit condition after deleting the duplicate native-Status condition. The Task stayed `Task_State=Open`, `Task_Status=New`, blank `Task_Sequence_Type`; Contact `991103000001962009` stayed `Sequence_State=Not Activated`, blank `Sequence_Type`. | Pass |
| Ordinary Task Won | Only `Task_State=Won` on Data Repair Task `991103000001981030`. | Task became `Task_State=Won`, `Task_Status=Closed`, native `Status=Completed`; Contact `991103000001949009` stayed `State=Open`, `Status=Working`, `Sequence_State=Running`, `Sequence_Stage=Call`, `Sequence_Step=1`; Deal `991103000001981018` stayed `Opportunity_State=Open`, `Opportunity_Status=Working`; one downstream Call `991103000002010005` was created. | Pass |
| Task Lost - Invalid / Bad Data | Set only `Task_State=Lost` and `Task_Lost_Reasons=Invalid / Bad Data` on Enrichment Task `991103000001981031`. | Task became `Task_State=Lost`, `Task_Status=Closed`, native `Status=Completed`; Data Repair Task `991103000001952005` was created with `Task_State=Open`, `Task_Status=New`, native `Status=Not Started`, `Blocks_Sequence=Yes`; Contact `991103000001949010` stayed `State=Open`, `Sequence_State=Running`; Deal `991103000001981019` stayed `Opportunity_State=Open`, `Opportunity_Status=Working`. | Pass |
| Call Won | Only `Call_Task_State = Won` on Call `991103000001949001` | Call returned `Call_Task_State=Won`, `Call_Task_Status=Closed`. Immediate duplicate check found one Call and one Task on the Deal at that point. | Pass |
| Call reschedule | Only `Next_Follow_Up_Date = 2026-06-26T10:00:00+01:00` on Call `991103000001949004`, with `Call_Task_State=Open` already present | Field persisted, but WF006 `last_executed_time` did not move after the update and no replacement/stale Call was created. | Fail: workflow criteria gap |
| Call reschedule after WF006 criteria update | Only `Next_Follow_Up_Date` on source Call `991103000001963011`, with `Call_Task_State=Open` and `Sequence_Managed=Yes` | WF006 condition 2 created replacement Call `991103000001982001` for `2026-06-26T10:00:00+01:00`; a second date-only edit created `991103000001985001` for `2026-06-27T10:00:00+01:00`. The workflow criteria gap was fixed live, but this run exposed a handler idempotency gap that was later fixed and retested in `V6_RESCHEDULE_IDEMP_20260625_1232`. | Superseded by post-publish pass below |
| Call reschedule idempotency after handler publish | On source Call `991103000001946014`, set only `Next_Follow_Up_Date` first to `2026-06-26T10:00:00+01:00`, then to `2026-06-27T10:00:00+01:00`; `Call_Task_State=Open` and `Sequence_Managed=Yes` were already present. | First edit created replacement Call `991103000002014001`. Second edit updated the same replacement to `Call_Start_Time=2026-06-27T10:00:00+01:00`; related-list readback showed only the source Call and one replacement Call, with no duplicate replacement. | Pass |
| Call Lost - Invalid / Bad Data | Set only `Call_Task_State=Lost` and `Call_Task_Lost_Reasons=Invalid / Bad Data` on Call `991103000001937017` | Call became `Call_Task_Status=Closed`; a Data Repair Task `991103000001954006` was created with `Task_State=Open`, `Task_Status=New`, native `Status=Not Started`, `Blocks_Sequence=Yes`; Contact stayed `State=Open`, `Sequence_State=Running`; Deal stayed `Opportunity_State=Open`, `Opportunity_Status=Working`. | Pass |
| Meeting booking/create | Created Event `991103000001963001` with `Meeting_Task_State=Open`, `Start_DateTime`, Contact, and Deal | WF007 set `Meeting_Task_Status=New`, set `Reminder_Send_At=2026-06-24T08:00:00+01:00`, and backfilled context mirrors. | Pass |
| Meeting Won | Only `Meeting_Task_State = Won` on Event `991103000001963001` | Event returned `Meeting_Task_State=Won`, `Meeting_Task_Status=Closed`; Contact/Deal advanced through demo progression. | Pass |
| Meeting Lost - no meeting/demo | Set `Meeting_Task_State=Lost` and `Meeting_Task_Lost_Reasons=No Meeting / Demo` on Event `991103000001962021` | WF007 ran local recovery: Contact stayed `State=Open`, moved to `Stage=Demo Booking`, `Sequence_State=Running`, `Sequence_Stage=Call`; Deal stayed `Opportunity_State=Open`, `Opportunity_Status=Working`. No related Tasks or Calls were found by related-list/search. This run exposed an Event status derivation defect: Event stayed `Meeting_Task_Status=New` instead of deriving `Closed`. The fix was later published and retested in `V6_MEETING_LOST_RETEST_20260625_1232`. | Superseded by post-publish pass below |
| Meeting Lost - no meeting/demo after handler publish | Set only `Meeting_Task_State=Lost` and `Meeting_Task_Lost_Reasons=No Meeting / Demo` on Event `991103000001946020`. | Event became `Meeting_Task_State=Lost`, `Meeting_Task_Status=Closed`; Contact stayed `State=Open`, `Stage=Demo Booking`, `Sequence_State=Running`, `Sequence_Stage=Call`; Deal stayed `Opportunity_State=Open`, `Opportunity_Status=Working`. Recovery created Call `991103000002016001`, email audit Task `991103000002013003`, and Manual Review Task `991103000001993004` for synthetic send-mail failure. | Pass |
| Legacy Outcome negatives | Changed only `Task_Outcome=Activate Email First`, `Call_Outcome=Positive`, `Meeting_Outcome=Attended - Qualified`, and Deal `Demo_Outcome=Commercials Requested` on the synthetic records. | Contact stayed `Stage=Demo Confirmation`, `State=Open`, `Sequence_State=Not Activated`, blank `Sequence_Type`; Deal stayed `Stage=MQL`, `Opportunity_Stage=Demo Confirmation`, `Opportunity_State=Open`, `Opportunity_Status=New`; Task/Call/Event stayed `*_State=Open`; related lists showed exactly one Task, one Call, and one Event. The Event handler did compute scheduling mirrors (`Reminder_Send_At`) from `Start_DateTime`, which is scheduling behavior, not legacy outcome routing. | Pass |
| Custom activity Status-only negatives | Changed only `Task_Status=Closed`, `Call_Task_Status=Closed`, and `Meeting_Task_Status=Closed` while the corresponding State fields stayed `Open`. | No sequence advancement, no Contact activation, no Deal lifecycle change, and no duplicate activity creation. The edited custom Status values persisted, confirming the remaining UX/config requirement to hide or make Status mirrors read-only. | Pass for no advancement; layout hardening still required |

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

Additional WF006 reschedule retest cleanup:

| Module | Deleted IDs |
| --- | --- |
| Calls | `991103000001963011`, `991103000001982001`, `991103000001985001` |
| Deals | `991103000001931014` |
| Contacts | `991103000001945003` |
| Accounts | `991103000001963009` |

Additional WF008 native Status retest cleanup:

| Module | Deleted IDs |
| --- | --- |
| Tasks | `991103000001975007` |
| Deals | `991103000001950009` |
| Contacts | `991103000001962009` |
| Accounts | `991103000001984005` |

Additional legacy Outcome / custom Status negative cleanup:

| Module | Deleted IDs |
| --- | --- |
| Tasks | `991103000001984007` |
| Calls | `991103000001935007` |
| Events | `991103000001944008` |
| Deals | `991103000001977025` |
| Contacts | `991103000001950015` |
| Accounts | `991103000001949007` |

Additional Activation Call cleanup:

| Module | Deleted IDs |
| --- | --- |
| Calls | `991103000002000001` |
| Tasks | `991103000001962019` |
| Deals | `991103000001934012` |
| Contacts | `991103000001962016` |
| Accounts | `991103000001931027` |

Additional Meeting Lost cleanup:

| Module | Deleted IDs |
| --- | --- |
| Events | `991103000001962021` |
| Deals | `991103000001930008` |
| Contacts | `991103000001945007` |
| Accounts | `991103000001958005` |

Additional Call Lost bad-data cleanup:

| Module | Deleted IDs |
| --- | --- |
| Tasks | `991103000001954006` |
| Calls | `991103000001937017` |
| Deals | `991103000001963016` |
| Contacts | `991103000001975018` |
| Accounts | `991103000001934016` |

Additional Call reschedule idempotency cleanup:

| Module | Deleted IDs |
| --- | --- |
| Calls | `991103000001946014`, `991103000002014001` |
| Deals | `991103000001943011`, `991103000001983002` |
| Contacts | `991103000001945011` |
| Accounts | `991103000001989011` |

Additional Meeting Lost retest cleanup:

| Module | Deleted IDs |
| --- | --- |
| Tasks | `991103000001993004`, `991103000002013003` |
| Calls | `991103000002016001` |
| Events | `991103000001946020` |
| Deals | `991103000001981006`, `991103000001990005` |
| Contacts | `991103000001930014` |
| Accounts | `991103000001944011` |

Additional ordinary Task State cleanup:

| Module | Deleted IDs |
| --- | --- |
| Tasks | `991103000001981030`, `991103000001981031`, `991103000001952005` |
| Calls | `991103000002010005` |
| Deals | `991103000001981018`, `991103000001981019` |
| Contacts | `991103000001949009`, `991103000001949010` |
| Accounts | `991103000001943020` |

Post-delete word searches for `V6_LIFECYCLE_20260625_0848` returned empty responses in
Tasks, Calls, Events, Deals, Contacts, and Accounts.
Post-delete word searches for `V6_RESCHEDULE_20260625_1151` also returned empty responses in
Tasks, Calls, Events, Deals, Contacts, and Accounts.
Post-delete word searches for `V6_WF008_NATIVE_STATUS_20260625_1204` returned empty
responses in Tasks, Deals, Contacts, and Accounts.
Post-delete word searches for `V6_LEGACY_NEG_20260625_1210` returned empty responses in
Tasks, Calls, Events, Deals, Contacts, and Accounts.
Post-delete word searches for `V6_ACT_CALL_20260625_1218` returned empty responses in
Tasks, Calls, Deals, Contacts, and Accounts.
Post-delete word searches for `V6_MEETING_LOST_20260625_1224` returned empty responses in
Tasks, Calls, Events, Deals, Contacts, and Accounts.
Post-delete word searches for `V6_CALL_LOST_BAD_DATA_20260625_1231` returned empty
responses in Tasks, Calls, Deals, Contacts, and Accounts.
Post-delete word searches for `V6_RESCHEDULE_IDEMP_20260625_1232` returned empty
responses in Tasks, Calls, Events, Deals, Contacts, and Accounts.
Post-delete word searches for `V6_MEETING_LOST_RETEST_20260625_1232` returned empty
responses in Tasks, Calls, Events, Deals, Contacts, and Accounts.
Post-delete word searches for `V6_TASK_STATE_20260625_1245` returned empty responses in
Tasks, Calls, Events, Deals, Contacts, and Accounts.

## Remaining Required Tests

| Area | Status |
| --- | --- |
| Activation Email / Call | Activation Manual and Activation Call passed. Activation Email is not run yet; use synthetic contacts with explicit consent/test-safe email handling before exercising customer-facing dispatch. |
| Ordinary Task Won / Lost | Ordinary Task Won and Task Lost (`Invalid / Bad Data`) passed. Remaining Task Lost reasons and commercial Task variants are not run. |
| Call Lost reason matrix | `Invalid / Bad Data` passed. `No Response`, `No Authority`, and `Duplicate / Test Record` not run. |
| Call reschedule | Workflow criteria and published handler idempotency both passed live; repeated edits to the same source Call updated the existing scheduled replacement instead of creating a duplicate. |
| Meeting Lost matrix | `No Meeting / Demo` passed on retest after handler publish. `No Response` and `Invalid / Bad Data` not run. |
| Commercial Task / Meeting valid and blocked evidence | Not run. |
| Legacy outcome negatives | Native Task Status, legacy Outcome-only, and custom activity Status-only negatives passed. Deal `Commercial_Outcome` and `Commercials_Status` negatives remain blocked by the active WF004 legacy bridge / commercial replacement work. |
| Safe field deletion | Not attempted. WF004 and layout/dependency checks still block deletion claims. |
