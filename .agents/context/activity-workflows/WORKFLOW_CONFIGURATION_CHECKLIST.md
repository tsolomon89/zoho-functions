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

## WF009 — Email Event Handler (5 sub-rules, wrapper-function architecture)

**Status:** The five workflow rule skeletons have already been created
via MCP. Each currently has an `assign_owner` no-op placeholder action
that needs to be swapped for the matching wrapper function.

| Rule | Rule ID | Trigger | Wrapper to attach |
|---|---|---|---|
| WF009a | `991103000000790073` | `mail_sent_replied` | `handleEmailReplied` |
| WF009b | `991103000000806019` | `mail_sent_bounced` | `handleEmailBounced` |
| WF009c | `991103000000789167` | `mail_sent_notreplied` (3d) | `handleEmailNotReplied` |
| WF009d | `991103000000796107` | `mail_sent_opened_notreplied` (3d) | `handleEmailOpenedNotReplied` |
| WF009e | `991103000000799022` | `mail_sent_clicked` | `handleEmailClicked` |

**Architecture note (why wrappers):** the Zoho UI makes argument
mappings immutable after save, and the Emails module exposes no Id
merge field — so binding `eventType` as a UI static literal forces
typo-prone hand-typing in five places and is unfixable post-save. The
wrappers move `eventType` into code; each WF009 sub-rule calls a
purpose-built wrapper that has no static-literal args, only two
auto-mappable merge fields.

The five wrapper Deluge files live in
[v4/activity/](../../../v4/activity/):
[handleEmailReplied.deluge](../../../v4/activity/handleEmailReplied.deluge),
[handleEmailBounced.deluge](../../../v4/activity/handleEmailBounced.deluge),
[handleEmailNotReplied.deluge](../../../v4/activity/handleEmailNotReplied.deluge),
[handleEmailOpenedNotReplied.deluge](../../../v4/activity/handleEmailOpenedNotReplied.deluge),
[handleEmailClicked.deluge](../../../v4/activity/handleEmailClicked.deluge).
Each is ~10 lines and delegates to
[handleEmailEvent.deluge](../../../v4/activity/handleEmailEvent.deluge)
(the shared core, unchanged).

### Step 1 — Publish the 5 wrapper functions

- [ ] Setup → Functions → New Function (×5). For each wrapper file
      above, create a function with the matching name and paste the
      file body verbatim. Leave the existing `handleEmailEvent`
      function as-is.
- [ ] Setup → Functions → `handleEmailEvent`: if you previously created
      any `handleEmailEvent (replied)` / `(bounced)` / etc.
      configurations, **delete them** — they're now unreachable.

### Step 2 — Configure each wrapper for workflow

For each of the 5 wrappers, open the function and click **Configure
for Workflow**. Same recipe every time — no static literals:

- [ ] **Module to be associated:** Deal
- [ ] **Configuration name:** match the wrapper name (e.g.
      `handleEmailReplied`)
- [ ] **Argument mapping** (both auto-mapped, no manual typing):
      - `relatedDealIdStr` ← `Deals - Deal Id`
      - `relatedContactIdStr` ← `Contacts - Contact Id`
- [ ] Save and Associate.

### Step 3 — Swap the placeholder action on each WF009 rule

For each rule in the table above:

- [ ] Setup → Automation → Workflow Rules → open the rule (`Emails`
      module).
- [ ] Edit the Instant Actions, remove the `assign_owner` action
      (assigned to Timothy Solomon as a no-op placeholder), and add a
      Functions action pointing at the matching wrapper configuration
      from Step 2.
- [ ] Save.

### Step 4 — Triggers and criteria (already set, verify only)

These were configured when the rule skeletons were created via MCP.
Spot-check each rule matches:

| Sub-rule | Trigger (set by MCP) | Criteria (set by MCP) |
|---|---|---|
| WF009a | `Outgoing email` → `Replied` | `Related Deal` not empty |
| WF009b | `Outgoing email` → `Bounced` | `Related Deal` not empty |
| WF009c | `Outgoing email` → `Unreplied` within 3 days | `Related Deal` not empty |
| WF009d | `Outgoing email` → `Open and Unreplied` within 3 days | `Related Deal` not empty |
| WF009e | `Outgoing email` → `Clicked` | `Related Deal` not empty |

Adjust the WF009c / WF009d thresholds in the UI if your sequence
cadence differs from 3 business days.

### Other Outgoing trigger options (not wired by WF009)

The `Outgoing email` picker also exposes `Sent`, `Opened`, and
`Unopened`. None of these are part of WF009 — `Sent` is too noisy
(fires on every send), `Opened` / `Unopened` are redundant with the
engagement-aware branches above. Skip unless adding a new signal.

### Incoming Email triggers (out of scope for WF009)

The `Incoming email` branch exposes `Received`, `Unreplied`, and
`Opened and Unreplied`. None of these map to WF009 — inbound email
handling would need a separate handler function and a new WF.

### Adding a new event type later

1. Add a new wrapper file in `v4/activity/`, e.g.
   `handleEmailUnopened.deluge`, calling
   `automation.handleEmailEvent("0", "<new_event_type>", ...)`.
2. Add a matching branch in `handleEmailEvent.deluge`.
3. Publish + Configure for Workflow per Steps 1–2.
4. Create a new workflow rule on the Emails module wired to the
   wrapper.

No edits to existing wrapper configurations or rules required.

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
