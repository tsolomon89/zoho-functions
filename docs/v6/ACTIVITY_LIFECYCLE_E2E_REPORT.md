# v6 Activity Lifecycle E2E Report

Date: 2026-06-25
Status: Not executed

The repository refactor is prepared, but the changed functions have not been deployed to the
target Zoho CRM org. No synthetic records were created, mutated, or deleted for this report.

## Execution Blockers

| Area | Status |
| --- | --- |
| Function deployment | Pending manual deployment from `lifecycle-state-status-v6`. |
| Workflow criteria | Pending live readback and update. |
| Layout/validation | Pending live configuration access. |
| Safe field deletion | Pending dependency checks and successful replacement behavior. |

## Synthetic Records

| Test batch | Record IDs | Cleanup |
| --- | --- | --- |
| Activity lifecycle command tests | None created | No cleanup required |

## Required Test Results To Fill After Deployment

| Case | Required evidence |
| --- | --- |
| Activation Email | Activation Task ID; Contact ID; Deal ID; proof that only `Task_Sequence_Type=Email` was edited; resulting `Task_State=Won`, `Task_Status=Closed`, native `Status=Completed`; one next action only. |
| Activation Call | Same evidence for `Task_Sequence_Type=Call`. |
| Activation Manual | Same evidence for `Task_Sequence_Type=Manual`; proof automated dispatch stopped/manual mode applied. |
| Ordinary Task Won | Task ID; only `Task_State=Won` edited; Task closed; expected Contact/Deal transition; duplicate-action check. |
| Task Lost | Task ID; `Task_State=Lost` plus canonical `Task_Lost_Reasons`; local loss behavior; Deal not automatically closed. |
| Call Won | Call ID; only `Call_Task_State=Won` edited; Call closed; expected next action. |
| Call Lost | Call IDs for No Response, Invalid / Bad Data, No Authority, Duplicate / Test Record; local routing evidence; Deal viability unchanged unless separately justified. |
| Call reschedule | Call ID; `Call_Task_State=Open` plus `Next_Follow_Up_Date`; replacement/scheduled Call ID; no custom state/status value such as Deferred or Rescheduled. |
| Meeting booking | Event ID; Start_DateTime; inherited context/reminder evidence; first-booking progression occurs once. |
| Meeting Won | Event ID; only `Meeting_Task_State=Won` edited; correct route for demo/commercial context. |
| Meeting Lost | Event IDs for No Meeting / Demo, No Response, Invalid / Bad Data; local recovery behavior; Deal not automatically closed. |
| Commercial Task valid | Task ID; Product/contract evidence; only `Task_State=Won` lifecycle command; Quote/Deal processing evidence. |
| Commercial Task blocked | Task ID; missing/invalid evidence; Task restored to `Open`/`Working`; Manual Review ID; no false Won/Closed. |
| Legacy negatives | IDs showing changes to `Task_Outcome`, `Call_Outcome`, `Meeting_Outcome`/`Demo_Outcome`, native Status alone, and custom Status alone do not advance lifecycle routing. |
