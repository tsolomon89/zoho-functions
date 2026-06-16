# WORKFLOW_TRIGGER_MAP.md — Zoho Workflow Rules and Function Triggers (V5 Contact-Centric)

Workflows are the trigger layer; functions are the logic layer. This reflects the
**consolidated 17-rule / 24-function** architecture. See `docs/v5/` for the
function & workflow consolidation matrices and the cutover/rollback runbook.

## Architecture summary

```text
Leads     -> convert + build Contact/Account/Deal graph (then hand to Contact)
Contacts  -> normalization + activation owner; reconciliation via processDeal
Accounts  -> thin: Account_Key + canonical Deal -> processDeal
Deals     -> sole reconciliation/rollup owner; commercial + demo handlers
Calls     -> outcome -> Contact transition
Tasks     -> completion -> activation / resume; scheduled-email wake-up
Events    -> demo meeting mirror + first-link confirmation
Emails    -> reply/bounce/passive interruption (5 wrapper rules)
```

**The Contact owns its sequence state** (`Sequence_Type/State/Stage/Step`). The
Deal is the shared commercial container; `Deal.Opportunity_Stage/State/Status`
roll up from the Primary Contact (`Deal.Contact_Name`) via `processDeal`. There is
no Deal sequence state machine (WF002/WF003/WF010a/WF010b are retired).

---

## Graph / reconciliation rules

### WF001 — Lead Processor
- Module: **Leads** · Trigger: Created or Edited
- Criteria: `Lead_Processing_Status` empty OR `Not Processed`; `Ready_for_Conversion` = true; `Email` not empty; `Automation_Suppressed` != true
- Function: `processLead(lead_id)` ← `${Leads.id}`
- Result: builds Contact/Account/Deal graph, maps Lead data, then `processContact` → `processDeal`. Creates the Activation Task (no sequence auto-start).

### WFC-Contact — Contact Processor (narrowed)
- Module: **Contacts** · Trigger: Created **OR** Edited and a specific field changed
- Field-change criteria (edit): `Stage`, `State`, `Status`, `Sequence_Type`, `Sequence_State`, `Sequence_Stage`, `Sequence_Step`, `Account_Name`, `Contact_Role1`
- Criteria: `Automation_Suppressed` != true (if present on Contacts)
- Function: `processContact(contact_id)` ← `${Contacts.id}`
- Result: normalize defaults (only fills blanks), resolve canonical Deal, `processDeal`, then create/reuse the Activation Task. Idempotent. **Must not** fire on every Contact edit (recursion safety — processor writes are suppressed).

### WFC-Account — Account Processor
- Module: **Accounts** · Trigger: Created or Edited
- Function: `processAccount(account_id)` ← `${Accounts.id}`
- Result: stamp `Account_Key`, resolve/create canonical Deal, `processDeal`.

### WFC-Deal — Deal Processor (sole rollup owner)
- Module: **Deals** · Trigger: Created or Edited
- Function: `processDeal(deal_id)` ← `${Deals.id}`
- Result: Contacts gather, Contact Roles, Products, Primary Contact, `Opportunity_Stage/State/Status` rollup + `Stage` (Opportunity Type) derivation, Account rollup. All writes suppressed.

---

## Commercial / demo handlers (Deal-driven; act on Primary Contact)

### WF004 — Commercial Status Handler
- Module: **Deals** · Trigger: Field Update — `Commercials_Status` changed
- Function: `handleCommercialsStatusChange(deal_id)` ← `${Deals.id}`
- Tokens: Sent → `commercial:sent`; Signed → `commercial:signed`; Rejected → `commercial:rejected`. Discussed/Intent/Deferred stamp only.

### WF005 — Demo Outcome Handler
- Module: **Deals** · Trigger: Field Update — `Demo_Outcome` changed
- Function: `handleDemoOutcome(deal_id)` ← `${Deals.id}`
- Tokens: Qualified/Commercials Requested → `demo:qualified`; Needs Follow-up → `demo:followup`; Not Qualified → `demo:not_qualified`; No Show → `demo:noshow`; Cancelled → `demo:cancelled`; Rescheduled → `demo:rescheduled`.

---

## Activity handlers (Contact from Who_Id, Deal from What_Id)

### WF006 — Call Outcome Handler
- Module: **Calls** · Trigger: Created or Edited
- Criteria: `Sequence_Managed`=Yes; `What_Id` not empty AND `$se_module`=Deals; `Call_Outcome` not empty; `Stale`!=Yes
- Function: `handleCallOutcome(call_id)` ← `${Calls.id}` → `call:*` tokens.

### WF007 — Meeting Handler
- Module: **Events** · Trigger: Created or Edited
- Criteria: `Sequence_Managed`=Yes (or Meeting_Type=Demo); `What_Id` not empty AND `$se_module`=Deals
- Function: `handleMeetingEvent(event_id)` ← `${Events.id}`. Emits `meeting:created` **only on first link**; mirrors demo fields + reminder otherwise; No Show delegates to `handleDemoOutcome`.

### WF008 — Task Completion Handler
- Module: **Tasks** · Trigger: Field Update — `Status`=Completed OR `Task_Outcome` not empty
- Criteria: `Sequence_Managed`=Yes; `What_Id` not empty AND `$se_module`=Deals
- Function: `handleTaskCompletion(task_id)` ← `${Tasks.id}`
- Guards: `Task_Type`="Email Sent" → return (audit); Description contains `ScheduledSend|` → return. Activation outcomes map to `activate:*`; Data Repair/Review Reply/Enrichment → resume.

---

## Email event rules (5 independent sub-rules — wrapper architecture)

Each outgoing-email event requires its **own** rule bound to a dedicated thin
wrapper. The wrapper hardcodes the event type in code (the Emails module exposes
no Id merge field and UI arg mappings are immutable post-save, so a single shared
function with a static-literal `eventType` is typo-prone and unfixable). Each
wrapper has only the two auto-mappable merge fields and delegates to the shared
`handleEmailEvent`. **Do not collapse WF009a–e into one rule.**

| Rule | Trigger | Wrapper |
|---|---|---|
| WF009a | Outgoing → Replied | `handleEmailReplied` |
| WF009b | Outgoing → Bounced | `handleEmailBounced` |
| WF009c | Outgoing → Unreplied (3d) | `handleEmailNotReplied` |
| WF009d | Outgoing → Opened & Unreplied (3d) | `handleEmailOpenedNotReplied` |
| WF009e | Outgoing → Clicked | `handleEmailClicked` |

- Arg mapping (each): `relatedDealIdStr` ← Deals - Deal Id; `relatedContactIdStr` ← Contacts - Contact Id.
- Criteria (each): `Related Deal` not empty.
- Effect: reply → Review Reply blocking Task; bounce → Data Repair blocking Task + Contact `Profile_Completion_Status`="Needs Enrichment"; passive → log only. Never advances the Deal.

---

## Date-based rules (native scheduled execution, same pattern as the old WF010)

### WF010c — Demo Reminder
- Module: **Deals** · Trigger: Date — `Demo_Reminder_Send_At`
- Criteria: `Automation_Suppressed` != true
- Function: `sendDemoReminder(deal_id)` ← `${Deals.id}` (sends Demo Confirmation Reminder to Primary Contact).

### WF010d — Commercial Follow-Up (NEW)
- Module: **Deals** · Trigger: Date — `Next_Comm_Follow_Up_Date`
- Criteria: `Automation_Suppressed` != true (function also guards `Opportunity_Stage`="Commercial Agreement" AND `Commercials_Status`="Sent")
- Function: `sendCommercialFollowUp(deal_id)` ← `${Deals.id}` → `commercial:followup_due`.

### WFC-SchedEmail — Scheduled Email Send (delayed-email wake-up)
- Module: **Tasks** · Trigger: Date — `Due_Date`
- Criteria: `Sequence_Managed`=Yes; `Status`=Not Started; `Description` contains `ScheduledSend`
- Function: `sendScheduledEmailFromTask(task_id)` ← `${Tasks.id}` (sends the deferred email and turns the wake-up Task into the audit record).

---

## Retired rules (disable AFTER the replacement is published & verified)

| Rule | Reason |
|---|---|
| WF002 — Deal Sequence Router | Deal `Sequence_Status` machine removed; bootstrap is Activation-Task driven |
| WF003 — Deal Stage Change Router | Contact owns Stage; `Opportunity_Stage` is a rollup, not a driver |
| WF010a — Next Action Due Date | no V5 writes to `Next_Action_Due_Date` |
| WF010b — Sequence Paused Until | no V5 writes to `Sequence_Paused_Until` (no Paused state) |

The old Deal router and the new Contact engine must never both control one
Contact's sequence — disable WF002/WF003/WF010a/WF010b only after cutover verifies.
