# v6 Final Canonical Field Matrix

Date: 2026-06-25

This matrix describes the intended final field authority after the repository refactor and before
live deployment. Live field presence, layouts, conditional rules, and deletion status still require
CRM verification before this can be treated as a deployed-state matrix.

## Lifecycle Fields To Retain

| Module | Field | Values | User authority | Automation authority | Final purpose |
| --- | --- | --- | --- | --- | --- |
| Tasks | `Task_State` | `Open`, `Won`, `Lost` | Primary command for ordinary Tasks | Defaults to `Open`; may reopen blocked tasks | Sole ordinary Task lifecycle command |
| Tasks | `Task_Status` | `New`, `Working`, `Closed` | None | Derived mirror | Human-readable activity status |
| Tasks | `Task_Lost_Reasons` | Canonical Lost Reasons | Required only when `Task_State=Lost` | Read only with Lost state | Loss context |
| Tasks | `Task_Sequence_Type` | `Email`, `Call`, `Manual` | Sole command for Sequence Activation Tasks | Read to route, then close task | Activation route choice |
| Calls | `Call_Task_State` | `Open`, `Won`, `Lost` | Primary command | Defaults to `Open`; may reopen missing-reason calls | Sole Call lifecycle command |
| Calls | `Call_Task_Status` | `New`, `Working`, `Closed` | None | Derived mirror | Human-readable call status |
| Calls | `Call_Task_Lost_Reasons` | Canonical Lost Reasons | Required only when `Call_Task_State=Lost` | Read only with Lost state | Loss context |
| Events | `Meeting_Task_State` | `Open`, `Won`, `Lost` | Primary result command | May default/backfill and reopen blocked meetings | Sole Meeting/Event lifecycle result command |
| Events | `Meeting_Task_Status` | `New`, `Working`, `Closed` | None | Derived mirror | Human-readable meeting status |
| Events | `Meeting_Task_Lost_Reasons` | Canonical Lost Reasons | Required only when `Meeting_Task_State=Lost` | Read only with Lost state | Loss context |
| Contacts | `State` | `Open`, `Lost` | Explicit viability decisions only | Set by contact-level loss logic | Contact commercial lifecycle |
| Contacts | `Status` | `New`, `Working`, `Closed` | None | Derived | Contact work status |
| Accounts | `State` | `Open`, `Lost` | Explicit account viability decisions only | Rollup from related Deals | Account commercial lifecycle |
| Accounts | `Status` | `New`, `Working`, `Closed` | None | Derived rollup | Account work status |
| Deals | `Opportunity_State` | `Open`, `Lost` | Explicit Deal viability decisions only | Process/rollup logic | Deal commercial lifecycle |
| Deals | `Opportunity_Status` | `New`, `Working`, `Closed` | None | Derived | Deal work status |

## Contextual Fields To Retain

| Module | Fields | Purpose |
| --- | --- | --- |
| Tasks | `Task_Type`, `Task_Sequence_Stage`, `Task_Sequence_Step`, `Blocks_Sequence`, `Task_Pipeline`, `Task_Opportunity`, `Task_Stage` | Task type, sequence context, blocking behavior, and Deal context mirrors. |
| Tasks | `Task_Contract_Products`, `Task_Contract_Brands`, `Task_Contract_Date_Start`, `Task_Contract_Date_End`, `Task_Contract_Frequency` | Commercial evidence, not lifecycle commands. |
| Calls | `Call_Task_Type`, `Call_Task_Stage`, `Call_Task_Pipeline`, `Call_Task_Opportunity`, `Sequence_Stage`, `Sequence_Attempt`, `Next_Follow_Up_Date` | Call context and scheduling. |
| Calls | `Call_Task_Contract_Products`, `Call_Task_Contract_Brands`, `Call_Task_Contract_Date_Start`, `Call_Task_Contract_Date_End`, `Call_Task_Contract_Frequency` | Commercial evidence, not lifecycle commands. |
| Events | `Meeting_Task_Stage`, `Meeting_Task_Pipeline`, `Meeting_Task_Opportunity`, `Start_DateTime`, `Reminder_Send_At` | Meeting context, type inference, and scheduling. |
| Events | `Meeting_Task_Contract_Products`, `Meeting_Task_Contract_Brands`, `Meeting_Task_Contract_Date_Start`, `Meeting_Task_Contract_Date_End`, `Meeting_Task_Contract_Frequency` | Commercial evidence, not lifecycle commands. |
| Contacts | `Stage`, `Sequence_Type`, `Sequence_State`, `Sequence_Stage`, `Sequence_Step`, `Lost_Reasons` | Commercial stage, sequence engine state, and Contact-level loss context. |
| Deals | `Stage`, `Opportunity_Stage`, `Pipeline`, `Lost_Reasons`, Product/Quote/contract fields | Commercial ontology, pipeline context, explicit loss context, and pricing evidence. |

## Zoho-Native Fields To Retain

| Module | Field | Final authority |
| --- | --- | --- |
| Tasks | `Status` | Automation-owned native mechanics. Reps must not update it to advance lifecycle. |
| Calls | `Status` | Automation-owned native mechanics where present. Reps must not update it to advance lifecycle. |
| Events | `Start_DateTime` | User scheduling input, not lifecycle result. |
| Activities | Owner, subject, relation fields | Operational context and relationship linking. |

## Legacy Duplicate Fields

| Module | Field | Final disposition |
| --- | --- | --- |
| Tasks | `Task_Outcome` | Remove from routing/workflows/layouts; delete only after live dependency and history audit. |
| Calls | `Call_Outcome` | Remove from workflows/layouts; delete only after live dependency and history audit. |
| Events | `Meeting_Outcome` | Remove from workflows/layouts; delete only after live dependency and history audit. |
| Events | `Meeting_Status` | Remove from layouts/workflows if unused; delete only after live dependency and history audit. |
| Deals | `Demo_Outcome`, `Demo_Status` | Retire after Event lifecycle replacement is deployed and verified. |
| Deals | `Commercial_Outcome`, `Commercials_Status` | Retire after Quote/activity commercial flow is deployed and verified. |

## Hidden Fields

No live fields were hidden in this session.

Required target hiding/read-only changes:

| Module | Field | Target configuration |
| --- | --- | --- |
| Tasks | `Task_Status`, native `Status` | Read-only or hidden from ordinary users. |
| Calls | `Call_Task_Status`, native `Status` where available | Read-only or hidden from ordinary users. |
| Events | `Meeting_Task_Status` | Read-only or hidden from ordinary users. |
| Tasks/Calls/Events | Lost Reason fields | Visible and required only when Activity State is `Lost`; hidden or optional otherwise. |
| Tasks | `Task_Sequence_Type` | Visible only for Sequence Activation Tasks where layout rules permit. |
| Legacy fields | Outcome/legacy status fields listed above | Remove from active layouts before deletion. |

## Deleted Fields

No custom fields were deleted in this session.

## Fields That Could Not Be Deleted

| Field set | Reason deletion was not performed |
| --- | --- |
| Legacy activity outcome/status fields | Live workflow, layout, validation, report/view, blueprint, formula, and history dependencies were not fully verified. |
| Deal `Demo_Outcome`/`Demo_Status` | Local exports show historical workflow dependency and Event replacement is not deployed/verified. |
| Deal `Commercial_Outcome`/`Commercials_Status` | Legacy handler/workflow path remains until Quote/activity replacement is deployed/verified. |
| Native fields | Native fields must not be deleted; hide or make automation-owned instead. |
