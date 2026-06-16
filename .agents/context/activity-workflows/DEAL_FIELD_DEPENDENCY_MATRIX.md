# Deal Sequence-Field Dependency & Deletion Matrix

Disposition of legacy Deal-level automation fields after the Contact-centric
refactor. **No field is deleted by this work** — deletion is a separate,
user-approved step once all references are gone and live dependencies (workflows,
layouts, templates) are confirmed clear.

Status legend: **MIGRATED** (state moved to Contact; no new function references it)
· **RETAIN** (still valid Deal commercial/demo data) · **DELETION CANDIDATE**
(no remaining function reference; verify workflow/layout/template before deletion).

| Deal field (API) | New code refs? | Contact replacement | Disposition | Blockers to deletion |
|---|---|---|---|---|
| `Sequence_Status` | none | `Contact.Sequence_State` | DELETION CANDIDATE | WF002/WF003/WF010 criteria; layouts |
| `Active_Sequence_Stage` | none | `Contact.Sequence_Stage` (+ Stage) | DELETION CANDIDATE | old router only |
| `Active_Sequence_Attempt` | none | `Contact.Sequence_Step` | DELETION CANDIDATE | old router only |
| `Active_Email_Chain_Step` | none | `Contact.Sequence_Step` (postcall) | DELETION CANDIDATE | old router only |
| `Sequence_Action_Mode` | none | `Contact.Sequence_Type` | DELETION CANDIDATE | old router/resolveSequenceRoute |
| `Next_Action_Type` | none | implicit in `Sequence_Stage` | DELETION CANDIDATE | old router |
| `Next_Action_Due_Date` | none | native Task/Call/Meeting dates | DELETION CANDIDATE | WF010 date trigger |
| `Sequence_Paused_Until` | none | none (no Paused; native dates) | DELETION CANDIDATE | WF010 date trigger |
| `Sequence_Superseded_At` | none | per-Contact supersede (no stamp) | DELETION CANDIDATE | old supersede only |
| `Last_Email_Template` / `Last_Email_Sent_At` / `Last_Email_Message_ID` / `Seq_Thread_Message_ID` | none | audit Task `Description` (SendKey + message id) per Contact | DELETION CANDIDATE | reply/thread tooling, if any |
| `Suppression_Reason` | none | `Contact.Sequence_State=Stopped` | DELETION CANDIDATE | layouts |
| `Automation_Suppressed` | read-guard in `handleDemoOutcome` / `handleCommercialsStatusChange` / `handleEmailEvent` / `sendDemoReminder` | (Deal-level kill switch retained) | RETAIN | — |
| `Opportunity_Stage` | none in new engine; **still written by `process*` (flagged polish)** | `Deal.Opportunity_Stage` (rolls up from Primary Contact) | MIGRATE → DELETION CANDIDATE after process* polish + live confirm | process* still writes it |
| `Opportunity_Stage` / `Opportunity_State` / `Opportunity_Status` | written by `routeContactSequence` rollup | — (these ARE the rollup) | RETAIN | — |
| `Stage` (Opportunity Type) | `_util_deriveOpportunityType` | — | RETAIN | — |
| `Contact_Name` | Primary Contact lookup everywhere | — | RETAIN | — |
| `Deal_Primary_Contact` | none | `Contact_Name` | DELETION CANDIDATE | confirm no workflow/template/layout use |
| `Commercials_Status` + `Commercials_Sent_At` / `Commercials_Discussed_At` / `Signed_At` / `Intent_To_Sign` | `handleCommercialsStatusChange` | — | RETAIN | — |
| `Demo_*` (Status/Outcome/Meeting_ID/Start/End/Reminder_Send_At) | `handleMeetingEvent` / `handleDemoOutcome` / `sendDemoReminder` | — | RETAIN | — |
| `Deal_Key` / `Amount` / `Product_Interest_Staging` / contract fields | `process*` | — | RETAIN | — |
| `Lost_Reasons` | loss paths | `Contact.Lost_Reasons` for per-Contact loss | RETAIN (Deal-level loss) | — |

## Known metadata issues to report (do not repair by creating metadata)
- **Duplicate `Commercials_Status` API name** in the Deals export (row 17
  Pick List + row 18 "Connected To" MultiModuleLookup). Report to Zoho admin.
- `Deal.Modified_By` typed "Single Line" in the export (should be Ownerlookup) —
  likely an export artifact; verify live.
- Contact `Sequence_*` fields exported with blank data types — confirm they are
  typed picklists live (values in `Jurnii Zoho API - Contact Pick List Values.csv`).

## Deletion gate
Before proposing deletion of any DELETION CANDIDATE: confirm (live) zero
references in workflow-rule criteria/actions, layouts, email templates, reports,
and any external integration. Then present a deletion proposal for explicit
approval. The old Deal router (WF002/WF003/WF010) must be disabled first.
