# WORKFLOW_CONFIGURATION_CHECKLIST.md — Zoho UI configuration checklist

## Purpose

Step-by-step checklist for configuring the 10 workflow rules from
`WORKFLOW_TRIGGER_MAP.md` in Zoho CRM Setup. Each block maps directly to
one rule. Configure in the order shown — earlier rules are dependencies
of later ones.

Each workflow invokes a Deluge function from `v3/activity/`. Before turning
any workflow on, make sure the function is published (Setup → Developer
Hub → Functions) under the same name (`automation.<functionName>`).

## Pre-flight

- [ ] Every field in `zoho_custom_fields_by_module.csv` is created (all 89 created via MCP — see FIELD_REUSE_NOTES.md for shortened-label decisions and the Yes/No-picklist substitution on Activities).
- [ ] Picklist values match the spec exactly (semicolon-separated values in the CSV).
- [ ] `Stage1` already holds the 8 stage values (no change needed).
- [ ] Default `Stage` is renamed in UI to "Opportunity" and holds MQL/SQL/FTP/RTP.
- [ ] Calls / Events / Tasks modules have all activity custom fields created. **Important:** custom fields on these modules are shared across all three sub-modules; create on Calls and they auto-appear on Events/Tasks. Lookups and Booleans are disallowed there — `What_Id` and Yes/No picklists are used instead.
- [ ] On Deals (which DOES allow Boolean), `Automation_Suppressed` is the real Boolean — criteria can use `!= true`. On Activities, `Sequence_Managed`/`Stale`/`Block_Email_Until_Done`/`Blocks_Sequence`/`Follow_Up_Required` are picklists; criteria use `= "Yes"` / `!= "Yes"`.
- [ ] Email templates from `TEMPLATE_CREATION_CHECKLIST.md` exist with exact names.
- [ ] Connection named `zoho_crm` exists with scopes:
      `ZohoCRM.modules.contacts.UPDATE`, `ZohoCRM.modules.contacts.READ`,
      `ZohoCRM.modules.contacts.send_mail`.
- [ ] All 14 Deluge functions are published:
      `processLead`, `processContact`, `processAccount`, `processDeal`,
      `sequenceRouter`, `createStageCall`, `supersedeOldSequence`,
      `handleCallOutcome`, `sendSequencedEmail`, `handleDemoOutcome`,
      `handleCommercialsStatusChange`, `handleMeetingEvent`,
      `handleTaskCompletion`, `handleEmailEvent` (+ the 4 `_util_*` helpers).

---

## WF001 — Lead Processor

- [ ] **Module:** Leads
- [ ] **Trigger:** On Record Action → Created or Edited
- [ ] **Criteria:**
      - `Lead_Processing_Status` is empty **OR** `Lead_Processing_Status` = `Not Processed`
      - `Ready_for_Conversion` = true
      - `Email` is not empty
      - `Automation_Suppressed` != true
- [ ] **Action:** Function → `processLead(lead_id)`
- [ ] **Arg mapping:** `lead_id` ← `${Leads.id}`
- [ ] **Note:** v3 already in production. New criteria gates protect imported records that haven't been marked ready.

## WF002 — Deal Sequence Router (bootstrap)

- [ ] **Module:** Deals
- [ ] **Trigger:** On Record Action → Created or Edited
- [ ] **Criteria:**
      - `Stage1` is not empty
      - `Sequence_Status` = `Not Started`
      - `Automation_Suppressed` != true
- [ ] **Action:** Function → `sequenceRouter(deal_id)`
- [ ] **Arg mapping:** `deal_id` ← `${Deals.id}`
- [ ] **Expected outcome:** Creates Call 1 for `Stage1`; sets Sequence_Status = Waiting on Call.

## WF003 — Deal Stage Change Router (supersede + re-bootstrap)

- [ ] **Module:** Deals
- [ ] **Trigger:** On Field Update → `Stage1` changed
- [ ] **Criteria:**
      - `Automation_Suppressed` != true
- [ ] **Action:** Function → `sequenceRouter(deal_id)`
- [ ] **Arg mapping:** `deal_id` ← `${Deals.id}`
- [ ] **Note:** Same function as WF002. Inside `sequenceRouter`, the
      `Active_Sequence_Stage != Stage1` branch triggers `supersedeOldSequence`
      then bootstraps the new Stage.

## WF004 — Deal Commercial Status Handler

- [ ] **Module:** Deals
- [ ] **Trigger:** On Field Update → `Commercials_Status` changed
- [ ] **Criteria:** none beyond the field-change trigger
- [ ] **Action:** Function → `handleCommercialsStatusChange(deal_id)`
- [ ] **Arg mapping:** `deal_id` ← `${Deals.id}`
- [ ] **Watch:** `Sent` advances Stage to `Commercials Sent` (Opportunity = FTP)
      and writes `Sequence_Status = Not Started`, which causes WF003 to fire
      `sequenceRouter` and create `Commercials Sent Call 1`. Test for the
      double-fire scenario in Test 10.

## WF005 — Deal Demo Outcome Handler

- [ ] **Module:** Deals
- [ ] **Trigger:** On Field Update → `Demo_Outcome` changed
- [ ] **Criteria:** none beyond the field-change trigger
- [ ] **Action:** Function → `handleDemoOutcome(deal_id)`
- [ ] **Arg mapping:** `deal_id` ← `${Deals.id}`
- [ ] **Watch:** `Attended - Qualified` writes Stage1=Demo Attended and
      Commercials_Status=Drafting; the second write does NOT re-trigger WF004
      because Drafting is not the FTP boundary value.

## WF006 — Call Outcome Handler

- [ ] **Module:** Calls
- [ ] **Trigger:** On Record Action → Created or Edited
- [ ] **Criteria:**
      - `Sequence_Managed` = `Yes` (picklist, not Boolean — Activities disallow Boolean)
      - `What_Id` is not empty AND `$se_module` = `Deals` (Activities disallow custom Lookup; use built-in What_Id)
      - `Call_Outcome` is not empty
      - `Stale` != `Yes`
- [ ] **Action:** Function → `handleCallOutcome(call_id)`
- [ ] **Arg mapping:** `call_id` ← `${Calls.id}`
- [ ] **Watch:** Positive outcome writes Deal Stage1; WF003 then fires
      `sequenceRouter`. Neutral/No Answer writes `Sequence_Status` updates
      with `suppressTrigger`, so WF002/WF003 do NOT fire — but the explicit
      `createStageCall` inside the function still creates Call N+1.

## WF007 — Event / Meeting Handler

- [ ] **Module:** Events
- [ ] **Trigger:** On Record Action → Created or Edited
- [ ] **Criteria:**
      - `Sequence_Managed` = `Yes` (picklist)
      - `What_Id` is not empty AND `$se_module` = `Deals`
- [ ] **Action:** Function → `handleMeetingEvent(event_id)`
- [ ] **Arg mapping:** `event_id` ← `${Events.id}`
- [ ] **Watch:** Sets `Demo_Reminder_Send_At` on the Deal. WF010
      (date-based) reads that field to send the Demo Booked Reminder Email.

## WF008 — Task Completion Handler

- [ ] **Module:** Tasks
- [ ] **Trigger:** On Field Update → `Status` = `Completed` **OR** `Task_Outcome` is not empty
- [ ] **Criteria:**
      - `Sequence_Managed` = `Yes` (picklist)
      - `What_Id` is not empty AND `$se_module` = `Deals`
- [ ] **Action:** Function → `handleTaskCompletion(task_id)`
- [ ] **Arg mapping:** `task_id` ← `${Tasks.id}`

## WF009 — Email Event Handler (5 sub-rules)

**Important:** WF009 cannot be created via the MCP/API. Email-event
triggers (`mail_sent_replied`, `mail_sent_bounced`, `mail_sent_clicked`,
`mail_sent_notreplied`, `mail_sent_opened_notreplied`) are NOT returned
by `GET /workflow_configurations?module=Deals` or `?module=Contacts` on
this org, and `postWorkflowRule` rejects `execute_on=mail_sent_replied`
with `INVALID_DATA`. Additionally the API `functions` action only takes
`{id, type}` — there is no way to pass per-rule static arguments via the
API. Each sub-rule needs its own `handleEmailEvent` *function
configuration* (Setup → Functions → Configure for Workflow) with a
different `eventType` static value, and those config IDs aren't
discoverable via Self Client scope.

Configure each sub-rule in the Zoho UI as below.

### Common setup (do once before the sub-rules)

- [ ] In Setup → Functions, open `handleEmailEvent` and click
      "Configure for Workflow" **five times** — once per sub-rule. Each
      configuration binds a different `eventType` static value (see the
      per-sub-rule sections). The other three function args bind to
      merge fields and are identical across all five:
      - `email_record_id` ← `${Emails.Message_Id}` (or the Email record
        id merge field exposed by your Email module)
      - `related_deal_id` ← Deal record id resolved from the email's
        Related Records context (use the `What_Id` / "Related To" merge
        field where `$se_module == Deals`)
      - `related_contact_id` ← Contact record id from the email's
        Recipient or `Who_Id` merge field
      Record each configuration's display name so you can pick the right
      one in step "Action" below; you'll see five entries like
      `handleEmailEvent (replied)`, `handleEmailEvent (bounced)`, etc.

- [ ] In Setup → Automation → Workflow Rules, choose the module the
      Outgoing email is sent from. In practice this is **Deals** (sales
      emails) or **Contacts** depending on where your sequence emails
      originate. WORKFLOW_TRIGGER_MAP.md lists the trigger module as
      `Emails`; the Zoho UI surfaces these event types when you create
      a rule on the owning record's module via the "Email" trigger
      category — confirm against your org's UI before wiring all five.

### WF009a — Outgoing Email Replied

- [ ] **Module:** Deals (or Contacts — see common setup)
- [ ] **Trigger:** Email Notifications → Outgoing → `Replied`
- [ ] **Criteria:** `Related Deal` is not empty
- [ ] **Action:** Function → `handleEmailEvent (replied)`
- [ ] **Static arg `eventType`:** `replied`
- [ ] **Expected behavior:** Pauses sequence
      (`Sequence_Status = Paused`), creates `Review Reply` Task. Does
      NOT auto-advance the Deal.

### WF009b — Outgoing Email Bounced

- [ ] **Module:** Deals (or Contacts)
- [ ] **Trigger:** Email Notifications → Outgoing → `Bounced`
- [ ] **Criteria:** `Related Deal` is not empty
- [ ] **Action:** Function → `handleEmailEvent (bounced)`
- [ ] **Static arg `eventType`:** `bounced`
- [ ] **Expected behavior:** Pauses sequence, creates `Data Repair`
      Task, flags Contact `Profile_Completion_Status = Needs Enrichment`.

### WF009c — Outgoing Email Unreplied

- [ ] **Module:** Deals (or Contacts)
- [ ] **Trigger:** Email Notifications → Outgoing → `Not Replied`
      (Zoho UI will ask for a window, e.g. "Not replied within N days" —
      set the threshold matching your sequence cadence; suggested 3
      business days)
- [ ] **Criteria:** `Related Deal` is not empty
- [ ] **Action:** Function → `handleEmailEvent (not replied)`
- [ ] **Static arg `eventType`:** `not replied`
- [ ] **Expected behavior:** Passive log only. No state change. Regular
      call/email cadence continues.

### WF009d — Outgoing Email Opened and Unreplied

- [ ] **Module:** Deals (or Contacts)
- [ ] **Trigger:** Email Notifications → Outgoing →
      `Opened and Unreplied` (set the window per WF009c)
- [ ] **Criteria:** `Related Deal` is not empty
- [ ] **Action:** Function → `handleEmailEvent (opened but not replied)`
- [ ] **Static arg `eventType`:** `opened but not replied`
- [ ] **Expected behavior:** Passive log only. Reserved for future
      engagement-aware branching.

### WF009e — Outgoing Email Clicked

- [ ] **Module:** Deals (or Contacts)
- [ ] **Trigger:** Email Notifications → Outgoing → `Clicked`
- [ ] **Criteria:** `Related Deal` is not empty
- [ ] **Action:** Function → `handleEmailEvent (clicked)`
- [ ] **Static arg `eventType`:** `clicked`
- [ ] **Expected behavior:** Passive log only. Reserved for future
      engagement-aware branching.

### WF009 implementation notes

- The `eventType` literal values MUST match `handleEmailEvent`'s branch
  strings exactly: `replied`, `bounced`, `not replied`,
  `opened but not replied`, `clicked`. Mistyping breaks the handler
  silently — it falls through to the `unknown_event_type` log line.
- If your Zoho UI cannot supply Deal+Contact IDs directly in the email
  workflow context, configure a lightweight intermediate function to
  resolve them from `Message_ID` before invoking `handleEmailEvent`.
- Sequence-managed gating, stale-call checks, and consent gating are
  applied inside `handleEmailEvent` — keep the workflow-rule criteria
  minimal (just `Related Deal` not empty) so the function gets reached
  for every relevant event and can short-circuit itself.

## WF010 — Date-Based Follow-Up Router

- [ ] **Module:** Deals
- [ ] **Trigger:** Scheduled (Date/Time) on:
      - `Next_Action_Due_Date` (post-call email chain ticks)
      - `Sequence_Paused_Until` (deferred resumes)
      - `Demo_Reminder_Send_At` (one-business-day-before AM demo reminder)
      - `Next_Commercial_Follow_Up_Date` (deferred commercial chase)
- [ ] **Criteria:** the matching date-time field reached; `Automation_Suppressed` != true
- [ ] **Action:** Function → `sequenceRouter(deal_id)`
- [ ] **Arg mapping:** `deal_id` ← `${Deals.id}`
- [ ] **Watch:** `sequenceRouter` is intentionally generic — it inspects
      `Sequence_Status` and `Sequence_Paused_Until` to decide whether to
      resume a deferred sequence, send the next post-call-chain email
      (delegated to `sendSequencedEmail` after upgrade — see open item below),
      or fire the demo reminder. Consider adding a thin date-aware
      dispatcher between WF010 and `sequenceRouter` if the post-call-chain
      step ever differs from the bootstrap path.

---

## Activation order (minimum viable)

Per the pack's own guidance, turn on in this order so the loop is
testable at each step:

1. WF001 — Lead Processor
2. WF002 — Deal Sequence Router
3. WF003 — Deal Stage Change Router
4. WF006 — Call Outcome Handler
5. WF004 — Deal Commercial Status Handler
6. WF005 — Deal Demo Outcome Handler

Then add:

7. WF007 — Event / Meeting Handler
8. WF008 — Task Completion Handler
9. WF009a–e — Email Event Handler (5 sub-rules: Replied,
   Bounced, Not Replied, Opened and Unreplied, Clicked) — **UI only,
   API does not support email-event triggers**
10. WF010 — Date-Based Follow-Up Router

## Trigger-suppression matrix (workflow cascade safety)

Functions that write Deal fields likely to re-fire WF002/WF003 pass an
empty `triggerMap` to `zoho.crm.updateRecord` so workflows do NOT cascade.

Exceptions — these intentionally let workflows fire:

| Function | Update | Cascading rule that should fire |
|---|---|---|
| `handleCallOutcome` (Positive) | `Stage1` change | WF003 (re-bootstrap next stage) |
| `handleDemoOutcome` (Attended-Qualified) | `Stage1`=Demo Attended + Commercials_Status=Drafting | WF003 (Stage1 change); WF004 does NOT trip because Drafting != Sent |
| `handleCommercialsStatusChange` (Sent / Signed) | `Stage1` change + Sequence_Status=Not Started | WF003 (re-bootstrap) and WF002 (only if Stage1 change didn't already fire WF003 first) |

If you observe duplicate Call 1 creation on transitions, suppress one
side of the cascade — usually the safest fix is to add a trigger map to
the second update and let WF003 own the bootstrap.
