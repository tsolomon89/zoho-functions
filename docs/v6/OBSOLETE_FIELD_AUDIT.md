# v6 Obsolete-Field Audit

Date: 2026-06-25
Branch: `codex/v6-lifecycle-closeout`
Target org: Jurnii.io, `org20114906201`

Read-only live field audit of the eight named obsolete candidates plus the duplicate/divergent
findings surfaced during the readback, across Contacts, Deals, Accounts, Tasks, Calls, Events.

> **NEVER delete native fields.** All deletes are GATED actions requiring explicit authorization and a
> separate Deluge/workflow dependency check before action. In particular, **Task_Outcome holds
> production data and its deletion is BLOCKED.** No fields were created, modified, hidden, renamed, or
> deleted in this pass.

## Field Disposition Table

| Module | apiName | liveExists | disposition | rationale |
| --- | --- | --- | --- | --- |
| Tasks | `Task_Outcome` | yes | **blocked** | LIVE picklist, active label 'Task Outcome' (NOT DEP-prefixed). COQL confirms it HOLDS DATA (>=1 record value 'Completed', id 991103000001651001). Highest-risk candidate. No active WF criteria reference it (live ruleset has no `*_Outcome` trigger), but Deluge dependency (handleCallOutcome/processContact/handleTaskCompletion) was NOT analysed and data is not migrated. Blocked from delete: DEP-rename + hide first, remove any dependency, migrate/archive data, then delete. NEVER delete in a read-only pass. |
| Calls | `Call_Outcome` | no | already-absent | No field with api_name Call_Outcome in Calls or any audited module. Unrelated Outcome_Notes (textarea) and native Call_Result exist but are not this field. No action. |
| Events | `Meeting_Outcome` | no | already-absent | Not present in Events or any audited module. Event outcome modeled via Meeting_Task_State/Meeting_Task_Status/Meeting_Task_Lost_Reasons. No action. |
| Events | `Meeting_Status` | no | already-absent | Not present in Events or any audited module. Superseded by custom Meeting_Task_Status (Open\|Working\|Closed). No action. |
| Deals | `Demo_Outcome` | no | already-absent | No Demo_Outcome field in any of the six audited modules. Demo lifecycle lives in `*_Stage` picklists. No action. |
| Deals | `Demo_Status` | no | already-absent | No Demo_Status field in any of the six audited modules. No action. (Docs reference Deals Demo_Outcome/Demo_Status as candidates; live readback finds neither present.) |
| Deals | `Commercial_Outcome` | yes | **safe-to-delete** | LIVE but already DEP-renamed (label 'DEP - Commercial Outcome'). COQL 'is not null' returned 0 records (EMPTY, no data to migrate). Matches memory v6-state-centric-outcome-cleanup. Safe to delete AFTER a Deluge/workflow dependency check confirms no reference. Recommend keep DEP-hidden one release then delete. Do NOT delete in a read-only pass; the delete itself is a gated action. |
| Deals | `Commercials_Status` | yes | **blocked** | LIVE, DEP-renamed (label 'DEP - Commercials Status'), COQL EMPTY (0 records). BUT still bound to ACTIVE WF004 (handleCommercialsStatusChange, field_update trigger), the live legacy cutover bridge. BLOCKED from delete until WF004 is deactivated and the wrapper functions retired/guarded. After WF004 disable + dependency check it becomes safe-to-delete (no data). The WF004 deactivation and field delete are gated live actions. |
| Tasks | `Task_Status` | yes | retain | Intentional v6 topology (custom Status workflow-phase mirror Open\|Working\|Closed), distinct from native Tasks.Status and custom Task_State. Not obsolete. Retain. |
| Tasks | `Task_Sequence_Stage` | yes | retain | LIVE; uses a DIVERGENT stage vocabulary (Demo Confirmation/Demo Hosted/Proposal Preparation/Commercial Agreement) unlike all other `*_Stage` fields (Demo Booked/Demo Attended/Commercials Sent/Commercials Signed). Not a clear delete — REVIEW to reconcile vocabulary or confirm intentional. Retain pending reconciliation; do not delete. |
| Tasks/Calls/Events/Contacts/Deals/Accounts | `Stage` (Renewall typo) | yes | retain | Contacts.Stage, Task_Stage, Call_Task_Stage, Meeting_Task_Stage, Deals.Opportunity_Stage all carry final picklist value misspelled 'Renewall' (double-L); Calls.Sequence_Stage and Events.Follow_Up_Stage spell 'Renewal' correctly. Retain the fields; recommend a separate data-quality picklist correction Renewall->Renewal (not a delete). |
| Tasks/Calls/Events | `Status` / `State` (native activity fields) | yes | retain | Native Zoho activity fields (Tasks.Status native picklist; Calls/Events native State/Status). Coexist by design with custom `*_State`/`*_Status`. NEVER delete native fields. Retain. |

## Additional Live Naming/Vocabulary Findings

- **`Sequence_Stage` cross-module naming collision:** `Contacts.Sequence_Stage` = `-None-|Email|Call|Meeting|Task`, but `Calls.Sequence_Stage` reuses the same api_name with the lifecycle-stage vocabulary (`-None-|Marketing Consent|Demo Booking|Demo Booked|Demo Attended|Commercials Sent|Commercials Signed|Onboarding|Renewal`). Two different fields share the api_name across modules with different meanings — flag for naming clarity; likely retain.
- **`Task_Sequence_Stage` divergent vocabulary** (see table) — uses canonical stage labels (Demo Confirmation/Demo Hosted/Proposal Preparation/Commercial Agreement) where every other `*_Stage` field uses the Booked/Attended/Sent/Signed labels. Possible stale sequence-stage vocabulary needing reconciliation.

## Disposition Summary

| Disposition | Count | Items |
| --- | --- | --- |
| already-absent | 5 | Call_Outcome, Meeting_Outcome, Meeting_Status, Demo_Outcome, Demo_Status |
| retain | 4 | Task_Status, Task_Sequence_Stage, Stage (Renewall typo — 5 fields), native Status/State |
| safe-to-delete | 1 | Commercial_Outcome (after dependency check; empty) |
| blocked | 2 | Task_Outcome (holds data), Commercials_Status (WF004-bound) |

## Gate Before Any Delete

1. No delete may proceed without a Deluge/workflow dependency check (which functions/rules/field-updates reference the field) — NOT performed in this read-only pass.
2. Task_Outcome additionally requires data migration/archive before delete (holds >=1 record).
3. Commercials_Status delete is blocked until WF004 (id 991103000000800001) is deactivated and handleCommercialsStatusChange + applyCommercialTransition are retired/guarded.
4. Native fields are NEVER deleted.
