# V5 Contact-Centric Migration & Cutover

**Status:** uncommitted implementation. No Zoho publication or runtime test was
performed in the authoring session (no Zoho MCP/API available). The user must
publish, configure workflows, run the dry-run, and test before any commit.

This document is the publish / enable / disable / rollback runbook for moving
individual sequence state from Deals to Contacts. Read it with:
- `SEQUENCE_TRANSITION_MATRIX.md` (behaviour, single source of truth)
- `V5_CONTACT_CENTRIC_FUNCTIONS.md` (new/changed function inventory)
- `DEAL_FIELD_DEPENDENCY_MATRIX.md` (legacy Deal field disposition)

---

## 0. Metadata prerequisites (user action, before cutover)

These are **picklist/value** decisions only — no new fields are required by the
code beyond what the repo exports already list. Confirm each against LIVE Zoho:

1. **`Contact.Sequence_Type`** — rename live values to **`Email` / `Call` /
   `Manual`** and migrate existing `Email First` / `Call First` data. Code targets
   the renamed values. (Until renamed, activation will write values that don't
   exist → fail. Do this first.)
2. **`Contact.Stage`** first value confirmed as **`Marketing Consent`**. The code
   writes this value; the completion field API name stays
   `Contact_Completed_Marketing_Qualification_At` (no rename). Email template
   prefix stays "Marketing Qualification".
3. **`Contact.Sequence_State`** = `Not Activated / Running / Stopped / Complete`,
   **`Sequence_Stage`** = `Email / Call / Meeting / Task` (+ `None`),
   **`Sequence_Step`** = `None / 1..10` — confirm these picklists exist & are typed
   (the API-name export showed blank types).
4. **`Deal.Opportunity_Stage`** picklist mirrors the 8 Contact stages; confirm
   `Opportunity_Stage` and the legacy `Active_*` / `Sequence_Action_Mode` / `Next_Action_Type`
   Deal fields are truly gone live (see DEAL_FIELD_DEPENDENCY_MATRIX.md).
5. **Task picklists** unchanged and reused: `Task_Type` must already contain
   `Email Sent`, `Sequence Activation`, `Data Repair`, `Review Reply`,
   `Manual Review`, `Draft Commercials`, `Send Commercials`, `Onboarding Setup`;
   `Task_Outcome` must contain `Activate Email First`, `Activate Call First`,
   `Manual Only`, `Suppress`, `Already Handled`, `Stage Incorrect`. Report any gap;
   do **not** add values without approval.

If any prerequisite cannot be met with existing metadata, STOP and report it.

---

## 1. Functions to publish (deluge)

New: `routeContactSequence`, `_util_resolveContactAction`, `_util_resolveContactEntry`,
`_util_deriveOpportunityType`, `_util_buildSendKey`, `_util_sendTemplateToContact`,
`scheduleSequencedEmail`, `sendScheduledEmailFromTask`, `createStageTask`,
`createAuxTask`, `createActivationTask`, `advancePrimaryContactStage`,
`lossPrimaryContact`, `sendDemoReminder`.

Rewritten (same public name): `sequenceRouter`, `sendSequencedEmail`,
`createStageCall`, `_util_resolveTemplate`, `_util_resolveSequenceRoute`,
`supersedeOldSequence`, `handleTaskCompletion`, `handleCallOutcome`,
`handleMeetingEvent`, `handleDemoOutcome`, `handleCommercialsStatusChange`,
`handleEmailEvent`, `processLead`, `processContact`, `processAccount`, `processDeal`.

Unchanged: `_util_calculateBusinessDate`, `_util_logAutomationEvent`, the
`handleEmail*` wrappers.

**Publish order:** utils first (`_util_*`, `createAuxTask`, `createStageCall`,
`createStageTask`, `createActivationTask`, `sendTemplateToContact`,
`scheduleSequencedEmail`, `sendSequencedEmail`, `advancePrimaryContactStage`,
`lossPrimaryContact`, `supersedeOldSequence`), then `routeContactSequence`, then
`sequenceRouter`, then `sendScheduledEmailFromTask` / `sendDemoReminder`, then the
handlers, then the four `process*`.

---

## 2. Workflow rules

### New (Contacts / Tasks)
- **WFC-Router (Contacts):** on Contact edit where **`Sequence_State` OR
  `Sequence_Stage` OR `Sequence_Step` changed** → `sequenceRouter(Contact.id)`.
  Use specific field-change criteria — never "every Contact edit" (recursion).
  Reserved for approved manual / scheduled re-entry only; activity handlers do
  NOT rely on this rule.
- **WFC-SchedEmail (Tasks, date-based):** execute on `Due_Date` where
  `Sequence_Managed = Yes` AND `Description contains "ScheduledSend"` AND
  `Status = Not Started` → `sendScheduledEmailFromTask(Task.id)`.
- **WFC-DemoReminder (Deals, date-based):** execute on `Demo_Reminder_Send_At` →
  `sendDemoReminder(Deal.id)`. (Replaces the WF010 reminder branch.)

### Rebound (same functions, Contact-derived inside)
- WF005 Demo Outcome → `handleDemoOutcome(deal_id)` (acts on Primary Contact).
- WF004 Commercials Status → `handleCommercialsStatusChange(deal_id)`.
- WF006 Call outcome → `handleCallOutcome(call_id)` (Contact from `Who_Id`).
- WF007 Meeting → `handleMeetingEvent(event_id)`.
- WF008 Task completed/outcome → `handleTaskCompletion(task_id)`.
- WF009* Email events → `handleEmail*` wrappers (unchanged).
- WF001 Lead → `processLead(lead_id)` (now creates Activation Task, no auto-start).

### Disable AFTER the replacement is published & verified
- **WF002 Deal Sequence Router**, **WF003 Deal Stage Change Router**, **WF010
  Date-Based Follow-Up Router** (Deal sequence machine). The old Deal router and
  the new Contact router must never both control one Contact's sequence.

---

## 3. Cutover order
1. Apply metadata prerequisites (§0).
2. Publish all functions (§1).
3. Create the new workflows (§2 New) **disabled**.
4. Run the **dry-run report** (§4) on existing Contacts; get user approval.
5. Enable WFC-SchedEmail + WFC-DemoReminder.
6. Enable WFC-Router.
7. Rebind WF004–WF009 to the published functions (already same names → no rebind
   needed unless argument bindings changed; none did).
8. **Disable WF002 / WF003 / WF010.**
9. Run the runtime E2E tests (§5).

## 4. Dry-run before touching existing records (REQUIRED, no auto-activation)
Produce, for all existing Contacts (read-only): total affected; Contacts with
existing sequence data; with open Tasks; with open Calls; with future Meetings;
linked to active Deals; that would receive an Activation Task; that cannot be
mapped safely. **No existing Contact is auto-activated.** Imported/historical
Contacts default to **no customer-facing activity** until an owner completes an
Activation Task. Do not migrate until the user approves the dry-run.

Existing-record classification: safe automatic mapping / requires Activation Task
/ already manually handled / stopped or suppressed / ambiguous / test or
duplicate. Ambiguous records are never auto-activated.

## 5. Runtime tests (controlled test records only)
Recipient `tlcsolomon@gmail.com`; sender `timothy.jurnii.io@viafreezohocrm.eu`.
- Lead converts → Contact + Account + canonical Deal + Roles/Products; **one**
  Activation Task; no email/Call/Meeting before activation.
- Activation outcomes set `Sequence_Type` (Email/Call/Manual) and start the
  sequence without manual Contact editing.
- Two Contacts on one Deal progress independently; only the Primary updates Deal
  Opportunity_* rollup.
- Cadence: Call neutral → `{stage} Email N` audit Task + Call N+1; after Call 5 →
  scheduled Post-Call Follow-Up via future-dated Task; positive → advance Stage,
  reset Step.
- Email success → exactly one Completed `Email Sent` audit Task with SendKey +
  message ID; failed send → no successful audit Task; re-invocation → no duplicate.
- Audit Task never advances the sequence (handleTaskCompletion audit guard).
- Delayed email: future-dated Task fires `sendScheduledEmailFromTask` on Due_Date.

## 6. Rollback
Re-enable WF002/WF003/WF010; disable WFC-Router / WFC-SchedEmail /
WFC-DemoReminder. The legacy Deal sequence fields are not deleted during cutover,
so the old machine resumes. No function is deleted. Contact sequence fields
written during the test remain but are inert once WFC-Router is disabled.

## 7. Do not
- Do not delete any field or workflow during cutover (separate approval).
- Do not commit until: full diff shown → functions/templates published →
  runtime tests pass → tested source matches working tree → user confirms.
