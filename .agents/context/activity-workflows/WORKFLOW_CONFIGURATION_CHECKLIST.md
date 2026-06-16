# WORKFLOW_CONFIGURATION_CHECKLIST.md — Zoho UI configuration (V5 Contact-Centric)

Step-by-step checklist for the **17-rule** Contact-centric architecture. Pair with
`WORKFLOW_TRIGGER_MAP.md` (triggers), `docs/v5/FUNCTION_CUTOVER_AND_ROLLBACK.md`
(phased cutover), and `V5_CONTACT_CENTRIC_MIGRATION.md` (publish order, dry-run).

Each workflow invokes a Deluge function from `v5/activity/` (or `v5/`); publish the
function (Setup → Developer Hub → Functions) as `automation.<functionName>` before
enabling its rule.

## Pre-flight (metadata — confirm against LIVE Zoho)

- [ ] **`Sequence_Type` renamed** to `Email` / `Call` / `Manual` and existing data
      migrated (was `Email First`/`Call First`/`Manual`). Code targets the new values.
- [ ] `Contact.Stage` first value = **`Marketing Consent`** (the 8 stage values).
- [ ] `Contact.Sequence_State` = Not Activated / Running / Stopped / Complete;
      `Sequence_Stage` = Email / Call / Meeting / Task (+ None);
      `Sequence_Step` = None / 1–10 — confirm these picklists are typed.
- [ ] `Deal.Opportunity_Stage` holds the 8 stage values; `Stage` (labelled
      "Opportunity Type") holds MQL/SQL/FTP/RTP.
- [ ] Task picklists reused (no new values): `Task_Type` includes `Email Sent`,
      `Sequence Activation`, `Data Repair`, `Review Reply`, `Manual Review`,
      `Draft Commercials`, `Send Commercials`, `Onboarding Setup`; `Task_Outcome`
      includes `Activate Email First`, `Activate Call First`, `Manual Only`,
      `Suppress`, `Already Handled`, `Stage Incorrect`.
- [ ] Connection `zoho_crm` exists (scopes: contacts UPDATE, READ, send_mail).
- [ ] Email templates exist with exact names (TEMPLATE_NAMING_MATRIX.md).
- [ ] **24 functions published** (see docs/v5/FUNCTION_CONSOLIDATION_MATRIX.md).
      Do NOT publish the 15 absorbed/dead functions.

## Publish order
utils (`_util_logAutomationEvent`, `_util_calculateBusinessDate`,
`_util_resolveContactAction`) → `createAuxTask` → `sendSequencedEmail` →
`routeContactSequence` → `sendScheduledEmailFromTask`, `sendDemoReminder`,
`sendCommercialFollowUp` → handlers (`handleEmailEvent` + 5 wrappers,
`handleCallOutcome`, `handleTaskCompletion`, `handleMeetingEvent`,
`handleDemoOutcome`, `handleCommercialsStatusChange`) → `processDeal` →
`processAccount` → `processContact` → `processLead`.

---

## Graph rules

### WF001 — Lead Processor
- [ ] Module Leads · On Create or Edit
- [ ] Criteria: `Lead_Processing_Status` empty OR `Not Processed`; `Ready_for_Conversion`=true; `Email` not empty; `Automation_Suppressed`!=true
- [ ] Function `processLead`, arg `lead_id` ← `${Leads.id}`

### WFC-Contact — Contact Processor  *(narrowed trigger — Phase 3)*
- [ ] Module Contacts · On Create **OR** Edit → **Specific field(s) get modified**
- [ ] Watched fields: `Stage`, `State`, `Status`, `Sequence_Type`, `Sequence_State`, `Sequence_Stage`, `Sequence_Step`, `Account_Name`, `Contact_Role1`
- [ ] Repeat: ON (re-fire on subsequent qualifying edits)
- [ ] Function `processContact`, arg `contact_id` ← `${Contacts.id}`
- [ ] **Do NOT** trigger on every Contact edit — only the fields above. Processor writes are workflow-suppressed; `processContact` is idempotent.

### WFC-Account — Account Processor
- [ ] Module Accounts · On Create or Edit · Function `processAccount`, arg `account_id` ← `${Accounts.id}`

### WFC-Deal — Deal Processor (sole rollup owner)
- [ ] Module Deals · On Create or Edit (All Records) · Function `processDeal`, arg `deal_id` ← `${Deals.id}`

---

## Commercial / demo handlers
### WF004 — Commercial Status · Deals · Field Update `Commercials_Status` · `handleCommercialsStatusChange(deal_id)`
### WF005 — Demo Outcome · Deals · Field Update `Demo_Outcome` · `handleDemoOutcome(deal_id)`

## Activity handlers
### WF006 — Call Outcome · Calls · Create/Edit · criteria `Sequence_Managed`=Yes, `$se_module`=Deals & `What_Id` set, `Call_Outcome` not empty, `Stale`!=Yes · `handleCallOutcome(call_id)`
### WF007 — Meeting · Events · Create/Edit · criteria `Sequence_Managed`=Yes, `$se_module`=Deals & `What_Id` set · `handleMeetingEvent(event_id)`
### WF008 — Task Completion · Tasks · Field Update `Status`=Completed OR `Task_Outcome` not empty · criteria `Sequence_Managed`=Yes, `$se_module`=Deals & `What_Id` set · `handleTaskCompletion(task_id)`

## Email events (5 rules — keep separate)
For each WF009a–e: Module Emails, Outgoing trigger (Replied / Bounced / Unreplied 3d
/ Opened&Unreplied 3d / Clicked), criteria `Related Deal` not empty, bound to its
wrapper (`handleEmailReplied/Bounced/NotReplied/OpenedNotReplied/Clicked`), args
`relatedDealIdStr` ← Deals-Deal Id, `relatedContactIdStr` ← Contacts-Contact Id.
- [ ] Publish the 5 wrappers + `handleEmailEvent`. Do not collapse into one rule.

## Date-based rules
### WF010c — Demo Reminder · Deals · Date `Demo_Reminder_Send_At` · `sendDemoReminder(deal_id)`
### WF010d — Commercial Follow-Up (NEW) · Deals · Date `Next_Comm_Follow_Up_Date` · `sendCommercialFollowUp(deal_id)`
### WFC-SchedEmail — Scheduled Email · Tasks · Date `Due_Date` · criteria `Sequence_Managed`=Yes, `Status`=Not Started, `Description` contains `ScheduledSend` · `sendScheduledEmailFromTask(task_id)`

---

## Migration dry-run gate (Phase 3 — REQUIRED before enabling WFC-Contact)

Before enabling WFC-Contact on the live base, produce a **read-only** report over
existing Contacts and get explicit approval. No existing Contact may be moved to
`Running` automatically.

Report columns: total Contacts; with existing `Sequence_*` data; with open Tasks;
with open Calls; with future Meetings; linked to an open Deal; that **would** receive
an Activation Task (Open + `Sequence_State` blank/Not Activated); unmappable.
Classify each: safe-auto-map / requires-Activation-Task / already-handled /
stopped-or-suppressed / ambiguous / test-or-duplicate. Ambiguous + imported/historical
default to **no customer-facing activity** until an owner completes an Activation Task.

## Activation / cutover order
1. Pre-flight metadata. 2. Publish the 24 functions. 3. Create WFC-SchedEmail,
WF010c, WF010d (date rules) **disabled**. 4. Run the dry-run; get approval.
5. Enable date rules. 6. Enable WFC-Contact (narrowed). 7. Verify WF004–WF009 bound
to the published functions. 8. **Disable WF002, WF003, WF010a, WF010b.** 9. Run E2E.

## Retire (only after replacement verified)
- [ ] Disable **WF002** (Deal Sequence Router)
- [ ] Disable **WF003** (Deal Stage Change Router)
- [ ] Disable **WF010a** (Next Action Due Date) and **WF010b** (Sequence Paused Until)

Do not delete any rule/field during cutover. Field deletion candidates
(`Sequence_Status`, `Next_Action_Due_Date`, `Sequence_Paused_Until`) are a separate
approved step (Phase 7). `Opportunity_Stage` is NOT a field — it's a stale identifier for
`Opportunity_Stage`.
