# v6 Pre-Change Field Authority Audit

Date: 2026-06-25
Target org: Jurnii.io, org20114906201
Target implementation: v6

This audit was written before code changes for the canonical activity lifecycle refactor.
It records current repository evidence, local metadata exports, and live-access blockers.

## Evidence Sources

| Source | Evidence | Limitation |
| --- | --- | --- |
| `v6/` repository code | Current implementation references and routing behavior. | Not proof of deployed behavior. |
| `.agents/context/api_field_names/*.csv` | Local API-name exports for Tasks, Calls, Meetings, Contacts, Accounts, Deals. | Canonical activity fields are not present in these exports; exports may be stale or org fields may be missing. |
| `.agents/context/field_mapping/Jurnii Zoho API - Pick List Values.csv` | Shared picklist vocabulary for Pipeline, Opportunity, Stage, Status, State, Lost Reasons, Task Type, Sequence Type. | Generic vocabulary, not per-field live metadata. |
| `.agents/context/zoho-backups/20260615T121415Z/README.md` | Historical workflow/function inventory captured 2026-06-15. | Pre-v6 cutover snapshot; not current live state. |
| `.agents/context/crm_workflow_rules_raw.json` | Intended workflow snapshot path. | Contains only `Connection not authorised`; unusable for workflow detail. |
| Zoho MCP module metadata | Attempted live metadata read. | Blocked by `CRMPLUS_TRIAL_EXPIRED`; no live field/layout/workflow verification available in this run. |
| `mcp__control_plane.analytics_semantic_audit` | Attempted semantic shortcut. | Blocked by missing `public.Account` table. |

Live deletion, layout edits, workflow criteria edits, and deployed behavior claims are therefore
unverified and must remain manual/deployment checklist items until CRM access is restored.

## Canonical Value Sets

| Authority | Values |
| --- | --- |
| Commercial `State` | `Open`, `Lost` only. `Won` is not persistent for Contacts, Accounts, or Deals. |
| Activity `State` | `Open`, `Won`, `Lost`. |
| `Status` | `New`, `Working`, `Closed`. Automation-derived. |
| Lost Reasons | `Invalid / Bad Data`, `No Fit`, `No Response`, `No Meeting / Demo`, `No Commercial Interest`, `No Budget`, `No Authority`, `Terms Rejected`, `Churned / Did Not Renew`, `Duplicate / Test Record`. |
| Activation choice | `Task_Sequence_Type`: `Email`, `Call`, `Manual`. |

Note: the local Deals export uses `Opportunity_State` and `Opportunity_Status`, while the objective
uses generic `State` and `Status` language for Deals. Existing v6 code comments state that Deals
have no bare `State`/`Status` fields in this org. This naming exception must be verified live before
any Deal field migration is attempted.

## Field Authority Matrix

### 1. Canonical Lifecycle Fields

| Module | API name | Label | Type | Allowed values | Custom/native | User or automation controlled | Current code references | Workflow references | Layout references | Current purpose | Canonical purpose | Action | Deletion blockers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Tasks | `Task_State` | Task State | Picklist, inferred | `Open`; `Won`; `Lost` | Not in local API export; expected custom | User command for ordinary Tasks; automation writes defaults and terminal mirrors | `processContact`, `createAuxTask`, `sendSequencedEmail`, `handleEmailEvent`, `handleTaskCompletion`, router comments | Expected WF008 trigger; live unverified | Unverified | Partially primary, but still mixed with `Task_Outcome` and native `Status` | Sole ordinary Task lifecycle command | Keep; verify/create live field | Must verify field exists and workflow watches it |
| Tasks | `Task_Status` | Task Status | Picklist, inferred | `New`; `Working`; `Closed` | Not in local API export; expected custom | Automation-derived | `processContact`, `createAuxTask`, `sendSequencedEmail`, `handleEmailEvent`, `handleTaskCompletion`, router | Expected output only; live unverified | Should be read-only/hidden | Idempotency mirror; not consistently native-close owner | Derived status only | Keep/hide | Must verify field exists; do not let workflows require user edits |
| Tasks | `Task_Lost_Reasons` | Task Lost Reasons | Picklist, inferred | Canonical Lost Reasons | Not in local API export; expected custom | User supplies only when `Task_State = Lost` | `handleTaskCompletion`, `handleEmailEvent` | Expected WF008 with `Task_State`; live unverified | Conditional required only when Lost; unverified | Lost context | Conditional loss context, never independent command | Keep conditional | Must verify field exists and layouts/validation |
| Calls | `Call_Task_State` | Call Task State | Picklist, inferred | `Open`; `Won`; `Lost` | Not in local API export; expected custom | User command | `handleCallOutcome`, `routeContactSequence` | Expected WF006 trigger; live unverified | Unverified | Primary call lifecycle command in code | Sole Call lifecycle command | Keep; verify/create live field | Must verify field exists and workflow watches it |
| Calls | `Call_Task_Status` | Call Task Status | Picklist, inferred | `New`; `Working`; `Closed` | Not in local API export; expected custom | Automation-derived | `handleCallOutcome`, `routeContactSequence` | Expected output only; live unverified | Should be read-only/hidden | Set to `New` on new/rescheduled Calls; not closed on terminal paths | Derived status only | Keep/hide; fix writes | Must verify field exists |
| Calls | `Call_Task_Lost_Reasons` | Call Task Lost Reasons | Picklist, inferred | Canonical Lost Reasons | Not in local API export; expected custom | User supplies only when `Call_Task_State = Lost` | `handleCallOutcome` | Expected WF006 with state; live unverified | Conditional required only when Lost; unverified | Loss context | Conditional loss context, never independent command | Keep conditional | Must verify field exists and layouts/validation |
| Events | `Meeting_Task_State` | Meeting Task State | Picklist, inferred | `Open`; `Won`; `Lost` | Not in local API export; expected custom | User command for result; automation may default Open | `handleMeetingEvent`, docs | Expected WF007 trigger; live unverified | Unverified | Primary Meeting/Event lifecycle command in code | Sole Meeting lifecycle result command | Keep; verify/create live field | Must verify field exists and workflow watches it |
| Events | `Meeting_Task_Status` | Meeting Task Status | Picklist, inferred | `New`; `Working`; `Closed` | Not in local API export; expected custom | Automation-derived | `handleMeetingEvent` | Expected output only; live unverified | Should be read-only/hidden | Only defaulted to `New`; not closed on terminal paths | Derived status only | Keep/hide; fix writes | Must verify field exists |
| Events | `Meeting_Task_Lost_Reasons` | Meeting Task Lost Reasons | Picklist, inferred | Canonical Lost Reasons | Not in local API export; expected custom | User supplies only when `Meeting_Task_State = Lost` | `handleMeetingEvent`, docs | Expected WF007 with state; live unverified | Conditional required only when Lost; unverified | Loss context | Conditional loss context, never independent command | Keep conditional | Must verify field exists and layouts/validation |
| Contacts | `State` | State | Picklist | `Open`; `Lost`; local vocabulary also lists `Won` | Custom in local export | Automation-owned except explicit Contact-level loss decisions | `processLead`, `processContact`, `routeContactSequence` | Contact process workflow historical; live unverified | Unverified | Commercial viability | Open/Lost only; never persistent Won | Keep/hide invalid Won from use | Picklist value cleanup requires live dependency audit |
| Contacts | `Status` | Status | Picklist | `New`; `Working`; `Closed` | Custom in local export | Automation-owned | `processLead`, `processContact`, `routeContactSequence`, `processDeal` reads | Contact process workflow historical; live unverified | Unverified | Commercial derived status | Derived New/Working/Closed | Keep/hide | None for field; validate no user command workflows |
| Contacts | `Lost_Reasons` | Lost Reasons | Picklist | Canonical Lost Reasons | Custom in local export | Explicit Contact-level loss context | `routeContactSequence` via loss routing | Live unverified | Conditional when Contact lost; unverified | Contact loss reason | Contact loss context, not activity loss command | Keep | None |
| Accounts | `State` | State | Picklist | `Open`; `Lost`; local vocabulary also lists `Won` | Custom in local export | Automation rollup | `processAccount`, `processDeal` rollup | Account process workflow historical; live unverified | Unverified | Account viability rollup | Open if any open Deal; Lost only if all relevant Deals lost | Keep/hide invalid Won from use | Picklist value cleanup requires live dependency audit |
| Accounts | `Status` | Status | Picklist | `New`; `Working`; `Closed` | Custom in local export | Automation rollup | `processAccount`, `processDeal` rollup | Account process workflow historical; live unverified | Unverified | Account derived status | Derived New/Working/Closed | Keep/hide | None |
| Accounts | `Lost_Reasons` | Lost Reasons | Picklist | Canonical Lost Reasons | Custom in local export | Explicit Account-level loss context | Sparse/no direct v6 activity refs | Live unverified | Unverified | Account loss context | Account loss context only | Keep | None |
| Deals | `Opportunity_State` | Opportunity State | Picklist | Expected `Open`; `Lost` | Custom in local export | Automation-owned viability | `processLead`, `processContact`, `processAccount`, `processDeal`, `routeContactSequence` | Deal process workflow historical; live unverified | Unverified | Deal viability in this org | Deal commercial State naming exception | Keep unless live org has bare `State` | Do not rename/delete until live metadata confirms |
| Deals | `Opportunity_Status` | Opportunity Status | Picklist | Expected `New`; `Working`; `Closed` | Custom in local export | Automation-owned | v6 commercial processors and router | Deal process workflow historical; live unverified | Unverified | Deal derived status in this org | Deal commercial Status naming exception | Keep unless live org has bare `Status` | Do not rename/delete until live metadata confirms |
| Deals | `Lost_Reasons` | Lost Reasons | Picklist | Canonical Lost Reasons | Custom in local export | Explicit Deal-level loss context | `routeContactSequence`, `processDeal` | Live unverified | Unverified | Deal loss reason | Deal-level loss only; activity loss must not set alone | Keep | None |

### 2. Contextual Fields

| Module | API name | Label | Type | Allowed values | Custom/native | User or automation controlled | Current code references | Workflow references | Layout references | Current purpose | Canonical purpose | Action | Deletion blockers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Tasks | `Task_Sequence_Type` | Task Sequence Type | Picklist | `Email`; `Call`; `Manual` | Custom in local export | User command only for Activation Tasks | `processContact`, `handleTaskCompletion` | Expected WF008 trigger for Activation; live unverified | Should be visible only on Activation Tasks | Primary route selector but currently requires native Status Completed | Sole Activation Task command | Keep; remove native Status dependency | Must verify conditional layout |
| Tasks | `Task_Type` | Task Type | Picklist | Repo doc: `Enrichment`; `Data Repair`; `Draft Commercials`; `Send Commercials`; `Review Reply`; `Onboarding Setup`; `Manual Review`; `Suppression Review`; `Sequence Activation` | Custom in local export | Automation/context; user may inspect | Many v6 activity helpers | Live unverified | Read-only where possible | Task behavior context | Context, not lifecycle command | Keep | None |
| Tasks | `Task_Sequence_Stage` | Task Sequence Stage | Text in local export | Canonical stages expected | Custom in local export | Automation/context | `processContact`, `handleTaskCompletion`, `routeContactSequence`, `sendSequencedEmail` | Live unverified | Read-only/context | Routing stage and activation stage adoption | Context only | Keep | None |
| Tasks | `Task_Sequence_Step` | Task Sequence Step | Unknown | Sequence step values | Not in local export | Automation/context | No v6 reference found | Live unverified | Unverified | Objective lists as possible context | Context if used; otherwise candidate remove after live audit | Investigate | Must verify field existence/history |
| Tasks | `Blocks_Sequence` | Blocks Sequence | Picklist | `Yes`; `No` | Custom in local export | Automation/context | `processContact`, `createAuxTask`, `routeContactSequence` | Live unverified | Read-only/context | Blocks automated dispatch while human task open | Context/gating, not lifecycle | Keep | None |
| Calls | `Next_Follow_Up_Date` | Next Follow-Up Date | DateTime | N/A | Custom in local export | User scheduling command while Call state remains Open | `handleCallOutcome` | Expected WF006/scheduling trigger; live unverified | Visible for Calls | Reschedule signal | Scheduling context, not lifecycle | Keep | None |
| Calls | `Sequence_Managed` | Sequence Managed | Picklist | `Yes`; `No` | Custom in local export | Automation/context | `handleCallOutcome`, `routeContactSequence` | Live unverified | Read-only/context | Guards sequence Calls | Context | Keep | None |
| Calls | `Sequence_Stage` | Sequence Stage | Picklist | Canonical stages expected | Custom in local export | Automation/context | `handleCallOutcome`, `routeContactSequence` | Live unverified | Read-only/context | Routing stage | Context, not lifecycle | Keep | None |
| Calls | `Sequence_Attempt` | Sequence Attempt | Number | Attempt number | Custom in local export | Automation/context | `handleCallOutcome`, `routeContactSequence` | Live unverified | Read-only/context | Call attempt idempotency | Context | Keep | None |
| Calls | `Stale` | Stale | Picklist | `Yes`; `No` | Custom in local export | Automation-owned | `handleCallOutcome`, `routeContactSequence` | Live unverified | Hidden/read-only | Prevents reprocessing old Calls | Internal idempotency | Keep | None |
| Calls | `Call_Task_Stage` | Call Task Stage | Picklist, inferred | Canonical stages | Not in local export | Automation mirror/context | `handleCallOutcome`, `routeContactSequence` | Live unverified | Read-only | Activity mirror | Context | Keep if live; verify | Must verify field exists |
| Calls | `Call_Task_Pipeline` | Call Task Pipeline | Picklist, inferred | `B2B`; `Partnership` | Not in local export | Automation mirror/context | `handleCallOutcome`, `routeContactSequence`, resolver | Live unverified | Read-only | Activity mirror | Context | Keep if live; verify | Must verify field exists |
| Events | `Meeting_Task_Stage` | Meeting Task Stage | Picklist, inferred | Canonical stages | Not in local export | User/context for meeting type inference; automation backfill | `handleMeetingEvent`, docs | Expected WF007/context; live unverified | Visible/editable for meetings where needed | Infers demo/commercial/renewal path | Context, not lifecycle command | Keep; read-only/backfilled where possible | Must verify field exists |
| Events | `Meeting_Task_Pipeline` | Meeting Task Pipeline | Picklist, inferred | `B2B`; `Partnership` | Not in local export | Automation mirror/context | `handleMeetingEvent`, resolver | Live unverified | Read-only | Activity mirror | Context | Keep if live; verify | Must verify field exists |
| Deals | `Pipeline` | Opportunity Pipeline | Picklist | `B2B`; `Partnership` | Native/local export blank custom flag | Automation mirror source; user/deal context | `resolveDealPipeline`, activity handlers | Live unverified | Deal layout | Pipeline context | Context | Keep | None |
| Deals | `Stage` | Opportunity Type | Picklist | `MQL`; `SQL`; `FTP`; `RTP` | Native/local export blank custom flag | Automation-owned commercial context | Broad v6 use | Live unverified | Deal layout | Opportunity type | Commercial context | Keep | None |
| Deals/Contacts | `Opportunity_Stage` / Contact `Stage` | Stage | Picklist | Canonical 8 stages | Custom | Automation-owned progression | Broad v6 use | Live unverified | Should be read-only where route-owned | Commercial stage | Context/progression, not activity command | Keep | None |

### 3. Zoho Native Fields

| Module | API name | Label | Type | Allowed values | Custom/native | User or automation controlled | Current code references | Workflow references | Layout references | Current purpose | Canonical purpose | Action | Deletion blockers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Tasks | `Status` | Status | Picklist | Local native values include `Not Started`, `In Progress`, `Completed`, `Cancelled`, `Deferred` by code usage | Native | Should be automation-owned | `handleTaskCompletion`, `processContact`, `routeContactSequence`, `sendSequencedEmail`, `sendScheduledEmailFromTask`, `createAuxTask` | Historical WF008 create_or_edit; current live unverified | Should be hidden or clearly automation-owned | Currently a user gate for activation and fallback success | Native mechanics only; `Task_State`/`Task_Sequence_Type` are commands | Keep native, hide, refactor command reads | Native cannot be deleted |
| Calls | `Status` | Status | Picklist, inferred | Code writes `Cancelled` | Native or activity standard, not in Calls export | Automation-owned | `handleCallOutcome`, `routeContactSequence` | Live unverified | Hidden/read-only | Cancellation/supersede mechanic | Native mechanics only | Keep native, hide | Native cannot be deleted |
| Calls | `Call_Type` | Call Type | Picklist | e.g. `Outbound` | Native in local export | Automation/context | `handleCallOutcome`, `routeContactSequence` | Live unverified | Context | Call direction/type | Context | Keep | Native cannot be deleted |
| Events | `Start_DateTime` | Start DateTime | DateTime | N/A | Native | User scheduling/context | `handleMeetingEvent` | Expected WF007 scheduling; live unverified | Visible | Meeting booking/reschedule time | Scheduling context, not lifecycle | Keep | Native cannot be deleted |
| Activities | `Who_Id`, `What_Id`, `$se_module` | Contact / Related To | Lookup/native polymorphic | N/A | Native | Automation/user relationship context | All handlers | Live unverified | Visible as needed | Contact/Deal relationship | Context | Keep | Native cannot be deleted |

### 4. Legacy Duplicate Lifecycle Fields

| Module | API name | Label | Type | Allowed values | Custom/native | User or automation controlled | Current code references | Workflow references | Layout references | Current purpose | Canonical purpose | Action | Deletion blockers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Tasks | `Task_Outcome` | Task Outcome | Picklist | `Completed`; `Blocked`; `Not Relevant`; `Already Handled`; `Needs Follow-Up`; `Failed`; `Activate Call First`; `Activate Email First`; `Manual Only`; `Suppress`; `Stage Incorrect` | Custom in local export | Legacy user command | `handleTaskCompletion`, `processContact`, `spec.md`, `docs/zoho_custom_fields_by_module.csv` | Historical WF008 mentioned Status/Task_Outcome; live unverified | Unknown | Parallel command/fallback; activation exceptions | Remove from routing; delete after dependency/historical audit | Code refs, docs refs, historical workflow refs; must verify layouts/rules/reports before deletion |
| Calls | `Call_Outcome` | Call Outcome | Picklist | `Positive`; `Neutral`; `No Answer`; `Negative`; `Deferred`; `Bad Data`; etc. | Custom in local export | Legacy user command | No v6 code read; docs/custom field export; call scripts | Historical WF006 likely; live unverified | Unknown | Retired call command | Delete after live dependency audit | Field export, call scripts, possible workflow criteria |
| Events | `Meeting_Outcome` | Meeting Outcome | Picklist | Scheduled/Attended/No Show/Rescheduled/etc. | Custom in local export | Legacy user command | Not read; only comment in `handleMeetingEvent`; docs/export | Live unverified | Unknown | Retired meeting command | Delete after live dependency audit | Field export, possible layouts/reports/history |
| Events | `Meeting_Status` | Meeting Status | Picklist | Scheduled/Confirmed/Rescheduled/Cancelled/Completed/No Show | Custom in local export | Legacy duplicate status | Only comment in `handleMeetingEvent`; docs/export | Live unverified | Unknown | Retired meeting status | Delete after live dependency audit | Field export, possible layouts/reports/history |
| Deals | `Demo_Outcome` | Demo Outcome | Picklist | Scheduled/Attended/No Show/etc. | Custom in local export | Legacy Deal-level event command | `sendDemoReminder` comments, docs/export | Historical WF005 trigger; local field export says workflow dependency | Unknown | Retired Deal demo command | Delete only after WF005 removal and data audit | Known workflow dependency in local export; live verification required |
| Deals | `Demo_Status` | Demo Status | Picklist | Not Scheduled/Scheduled/Confirmed/Rescheduled/Cancelled/Completed/No Show | Custom in docs export | Legacy Deal demo status | Comments/docs only | Live unverified | Unknown | Legacy status mirror | Candidate hide/delete after audit | Must verify live field, history, layouts |
| Deals | `Commercial_Outcome` | Commercial Outcome | Picklist | Intent/Needs Review/Deferred/Rejected/No Answer/Signed | Custom in local export | Legacy outcome | Comment in `routeContactSequence`, docs/export | Live unverified | Unknown | Legacy commercial command/status | Candidate delete after audit | Must verify no workflows/reports |
| Deals | `Commercials_Status` | Commercials Status | Picklist | Not Started/Drafting/Ready/Sent/Discussed/Intent/Signed/Deferred/Rejected | Custom in local export | Legacy commercial workflow surface | `handleCommercialsStatusChange`, docs/export | Historical WF004 active | Unknown | Legacy Deal commercial surface | Retain until replacement verified; then hide/delete if obsolete | WF004 and handler dependencies |

### 5. Commercial Evidence Fields

| Module | API name | Label | Type | Allowed values | Custom/native | User or automation controlled | Current code references | Workflow references | Layout references | Current purpose | Canonical purpose | Action | Deletion blockers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Tasks | `Task_Contract_Products` | Task Contract Products | Multi-select picklist, inferred | Product name strings | Not in local API export | User evidence on commercial Tasks | `handleTaskCompletion`, docs | Live unverified | Visible on commercial Tasks | Product evidence for Quote/Product linking | Evidence, not lifecycle | Keep; verify live field | Must verify field exists |
| Tasks | `Task_Contract_Brands` | Task Contract Brands | Number, inferred | Positive integer | Not in local API export | User evidence | `handleTaskCompletion` | Live unverified | Visible on commercial Tasks | Quote pricing evidence | Evidence | Keep; verify | Must verify field exists |
| Tasks | `Task_Contract_Date_Start` / `Task_Contract_Date_End` / `Task_Contract_Frequency` | Contract dates/frequency | Date/picklist inferred | Contract terms | Not in local API export | User evidence | `handleTaskCompletion` | Live unverified | Visible on commercial Tasks | Contract term evidence | Evidence | Keep; verify | Must verify field exists |
| Calls | `Call_Task_Contract_Products` | Call Task Contract Products | Multi-select picklist, inferred | Product name strings | Not in local API export | User evidence on commercial Calls | `handleCallOutcome`, docs | Live unverified | Visible where commercial Calls collect terms | Product evidence | Evidence | Keep; verify | Must verify field exists |
| Calls | `Call_Task_Contract_Brands` / dates / frequency | Call contract terms | Number/date/picklist inferred | Contract terms | Not in local API export | User evidence | `handleCallOutcome` | Live unverified | Visible where needed | Contract/Quote evidence | Evidence | Keep; verify | Must verify field exists |
| Events | `Meeting_Task_Contract_Products` | Meeting Task Contract Products | Multi-select picklist, inferred | Product name strings | Not in local API export | User evidence on commercial meetings | `handleMeetingEvent`, docs | Live unverified | Visible where needed | Product evidence | Evidence | Keep; verify | Must verify field exists |
| Events | `Meeting_Task_Contract_Brands` / dates / frequency | Meeting contract terms | Number/date/picklist inferred | Contract terms | Not in local API export | User evidence | `handleMeetingEvent` | Live unverified | Visible where needed | Contract/Quote evidence | Evidence | Keep; verify | Must verify field exists |
| Quotes | `Quote_Stage` | Quote Stage | Picklist | Draft; Negotiation; Delivered; On Hold; Confirmed; Closed Won; Closed Lost | Custom/native not audited here | User/automation quote lifecycle | `handleQuoteStageChange`, `processDeal` | WF021 expected; live unverified | Quote layout | Quote lifecycle, distinct from activity lifecycle | Retain | Not in activity field deletion scope |

## Detected Lifecycle Drift

1. `handleTaskCompletion` still reads `Task_Outcome` as a command field for both activation and ordinary Tasks.
2. Activation currently requires native `Tasks.Status = Completed` before it will process `Task_Sequence_Type`; this violates the activation exception.
3. `processContact` creates Activation Task instructions telling users to set `Task_Sequence_Type` and then mark the Task completed, and also says to use `Task_Outcome` for exceptions.
4. Ordinary Task routing falls back to `Task_Outcome` when `Task_State` is blank.
5. Ordinary Task routing still treats native `Tasks.Status = Completed` as a success signal for commercial and generic stage Tasks.
6. `Task_Status` is used as an idempotency mirror, but native `Tasks.Status` is not consistently derived from `Task_State`.
7. `handleCallOutcome` has mostly moved to `Call_Task_State`, but terminal Won/Lost paths do not write `Call_Task_Status = Closed`; Won does not close/complete a native activity field.
8. `handleMeetingEvent` has moved to `Meeting_Task_State`, but terminal Won/Lost paths do not write `Meeting_Task_Status = Closed`; Open defaults only happen in the upcoming branch.
9. Local API field-name exports contain legacy `Task_Outcome`, `Call_Outcome`, `Meeting_Outcome`, and `Meeting_Status`, but not the canonical activity lifecycle fields used by code.
10. Historical workflow inventory lists WF005 on `Demo_Outcome`, WF006 Call `anyaction`, WF007 Event `create_or_edit`, and WF008 Task `create_or_edit`; current live workflow criteria are unverified.
11. `spec.md` still says Activation transitions with `Task_Outcome`.
12. `docs/v6/SINGLE_FIELD_AUTOMATION_AUDIT.md` and `docs/v6/SINGLE_FIELD_E2E_TEST_PLAN.md` frame single-field behavior around commercial evidence rather than the activity lifecycle command.
13. Deal lifecycle naming is inconsistent between the objective (`State`/`Status`) and local v6 org exports/code (`Opportunity_State`/`Opportunity_Status`).

## Field Decisions Before Refactor

| Decision group | Fields |
| --- | --- |
| Retain as canonical lifecycle | `Task_State`, `Task_Status`, `Task_Lost_Reasons`, `Call_Task_State`, `Call_Task_Status`, `Call_Task_Lost_Reasons`, `Meeting_Task_State`, `Meeting_Task_Status`, `Meeting_Task_Lost_Reasons`, Contact/Account `State`, Contact/Account `Status`, Deal `Opportunity_State`, Deal `Opportunity_Status` pending live naming verification. |
| Retain as activation command | `Task_Sequence_Type`. |
| Retain as context/scheduling | `Task_Type`, `Task_Sequence_Stage`, `Blocks_Sequence`, `Sequence_Managed`, `Sequence_Stage`, `Sequence_Attempt`, `Stale`, `Next_Follow_Up_Date`, `Meeting_Task_Stage`, activity Pipeline/Opportunity/Stage mirrors, `Start_DateTime`, `Who_Id`, `What_Id`, `$se_module`. |
| Retain as commercial evidence | `Task_Contract_*`, `Call_Task_Contract_*`, `Meeting_Task_Contract_*`, Quote/Product/contract fields. |
| Hide/read-only target | All custom activity `*_Status` fields, native `Tasks.Status`, activity context mirrors, sequence metadata, stale/idempotency flags. |
| Candidate deletion after safe sequence | `Task_Outcome`, `Call_Outcome`, `Meeting_Outcome`, `Meeting_Status`, Deal `Demo_Outcome`, Deal `Demo_Status`, Deal `Commercial_Outcome`, possibly `Commercials_Status` after replacement workflows are live and verified. |
| Cannot delete | Native fields such as `Tasks.Status`, `Calls.Status`, `Call_Type`, `Start_DateTime`, `Who_Id`, `What_Id`, `$se_module`. |

## Safe Deletion Blockers

No custom field is safe to delete yet because live dependencies could not be verified.

Minimum blockers to clear for each obsolete field:

1. Restore live CRM metadata/workflow access.
2. Export field details including IDs, picklist values, layout sections, validation rules, blueprint/report/view/formula dependencies.
3. Export or document historical field values where retention matters.
4. Refactor repository code and docs to stop reading/writing the field.
5. Update live workflow criteria and function associations away from obsolete fields.
6. Deploy replacement functions and verify behavior.
7. Remove obsolete fields from layouts.
8. Confirm zero dependencies.
9. Delete the field via CRM UI/API only after dependency checks pass.
10. Re-run end-to-end tests and cleanup synthetic records.

## Workflow Evidence And Required Target State

Historical snapshot only:

| Workflow | Historical trigger | Required target |
| --- | --- | --- |
| WF006 Call | Calls `anyaction` | Trigger from `Call_Task_State` and `Next_Follow_Up_Date` where scheduling is supported; never `Call_Outcome`. |
| WF007 Event | Events `create_or_edit` | Trigger from `Meeting_Task_State`, creation, and `Start_DateTime` changes; never `Meeting_Outcome`. |
| WF008 Task | Tasks `create_or_edit` | Trigger from `Task_State` and `Task_Sequence_Type`; native `Status` must not be required as user command; never `Task_Outcome`. |
| WF005 Demo | Deals `Demo_Outcome` | Retire after Event-driven meeting lifecycle is deployed and verified. |
| WF004 Commercials | Deals `Commercials_Status` | Retain only until Quote/activity commercial evidence path is deployed and verified. |

Current live workflow criteria and function associations are blocked by CRM access and must not be
claimed as changed.
