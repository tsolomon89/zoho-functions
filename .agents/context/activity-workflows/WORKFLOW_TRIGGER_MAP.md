# WORKFLOW_TRIGGER_MAP.md — Zoho Workflow Rules and Function Triggers

## Purpose

This document defines the workflows required to run the CRM automation.

Workflows are the trigger layer.

Functions are the logic layer.

---

## Architecture Summary

```text
Deals  -> sequence/state machine routing
Calls  -> outcome-driven email/call/stage transitions
Events -> meeting/demo scheduling and outcome handling
Tasks  -> non-call manual work completion
Emails -> reply/bounce/no-reply interruption handling
Leads  -> conversion/upsert trigger only
Contacts -> consent/profile update trigger only
```

---

# WF001 — Lead Processor

## Module

Leads

## Trigger

Created or Edited

## Criteria

```text
Lead Processing Status is empty OR Lead Processing Status = Not Processed
Ready for Conversion = true
```

Optional criteria:

```text
Email is not empty
Automation Suppressed != true
```

## Function

```text
processLeadOrRecord(lead_id, "Leads")
```

## Purpose

Convert or upsert Contact, Account, Deal, Product associations, Deal value, Stage, and Opportunity. Then initialize Deal sequence.

## Notes

Leads are not the long-term state machine. After a Deal exists, the Deal owns the process.

---

# WF002 — Deal Sequence Router

## Module

Deals

## Trigger

Created or Edited

## Criteria

```text
Stage is not empty
Sequence Status = Not Started
Automation Suppressed != true
```

Optional extra criteria:

```text
Opportunity is not empty
```

## Function

```text
sequenceRouter(deal_id)
```

## Purpose

Initialize the correct Stage sequence. In every Stage, the first action should be `Call 1`.

## Expected behavior

```text
Stage = Demo Booking
→ create Demo Booking Call 1
→ Sequence Status = Waiting on Call
```

```text
Stage = Commercials Sent
→ create Commercials Sent Call 1
→ Sequence Status = Waiting on Call
```

---

# WF003 — Deal Stage Change Router

## Module

Deals

## Trigger

Edited

## Criteria

```text
Stage changed
Automation Suppressed != true
```

## Function

```text
sequenceRouter(deal_id)
```

## Purpose

When Stage changes:

1. Supersede old sequence.
2. Stop stale scheduled actions where possible.
3. Reset sequence state for new Stage.
4. Create Call 1 for the new Stage.

Only one active Stage sequence is allowed per Deal.

---

# WF004 — Deal Commercial Status Handler

## Module

Deals

## Trigger

Edited

## Criteria

```text
Commercials Status changed
```

## Function

```text
handleCommercialsStatusChange(deal_id)
```

## Purpose

Important transition:

```text
Commercials Status = Sent
→ Stage = Commercials Sent
→ Opportunity = FTP
→ Commercials Sent At = now if empty
→ create Commercials Sent Call 1
```

FTP begins only after commercial terms have actually been sent.

---

# WF005 — Deal Demo Outcome Handler

## Module

Deals

## Trigger

Edited

## Criteria

```text
Demo Outcome changed
```

## Function

```text
handleDemoOutcome(deal_id)
```

## Purpose

Handle demo outcome transitions.

Examples:

```text
Demo Outcome = Attended - Qualified
→ Stage = Demo Attended
→ send post-demo email
→ Commercials Status = Drafting
→ create task: Draft Commercials
```

```text
Demo Outcome = No Show
→ create recovery Call
→ keep/return Stage to Demo Booking or Demo Booked depending on process
```

---

# WF006 — Call Outcome Handler

## Module

Calls

## Trigger

Created or Edited / Field update

## Criteria

```text
Sequence Managed = true
Related Deal is not empty
Call Outcome is not empty
```

## Function

```text
handleCallOutcome(call_id)
```

## Purpose

The call outcome is the primary gate for emails.

The function should:

1. Read Call.
2. Read Related Deal.
3. Confirm Call belongs to active sequence.
4. Confirm Stage matches.
5. Interpret Call Outcome.
6. Decide next action.

## Outcome rules

| Call Outcome | Action |
|---|---|
| Positive | Advance Stage or perform positive transition |
| Neutral | Send current-stage email, create next Call |
| No Answer | Send no-answer email, create next Call |
| Negative | Move Lost / Disqualified |
| Deferred | Pause sequence until Next Follow-Up Date |
| Bad Data | Pause and create data repair Task |
| Already Handled | Mark step complete or advance |
| Not Relevant | Skip/pause/manual review |
| Manual Only | Pause automation |
| Do Not Contact | Suppress automation |

---

# WF007 — Event / Meeting Handler

## Module

Events

## Trigger

Created or Edited

## Criteria

```text
Sequence Managed = true
Related Deal is not empty
```

## Function

```text
handleMeetingEvent(event_id)
```

## Purpose

Handle meeting creation, rescheduling, cancellation, and reminder recalculation.

Meetings are `Events` in Zoho API.

The decisive commercial outcome should be stored on the Deal as `Demo Outcome`, even if mirrored on the Event.

---

# WF008 — Task Completion Handler

## Module

Tasks

## Trigger

Edited

## Criteria

```text
Sequence Managed = true
Related Deal is not empty
Task Outcome is not empty
```

or:

```text
Status = Completed
Sequence Managed = true
Related Deal is not empty
```

## Function

```text
handleTaskCompletion(task_id)
```

## Purpose

Handle non-call manual work, including enrichment, data repair, commercial drafting, reply review, onboarding setup, and suppression review.

---

# WF009 — Email Event Handler (5 sub-rules)

WF009 fans out one workflow rule per Outgoing-email event type. The Zoho
UI's Email Notifications trigger fires per event (`Replied`,
`Bounced`, `Not Replied`, `Opened and Unreplied`, `Clicked`) and lets you
choose only one event-type per rule, so the Zoho-side configuration is a
1-to-1 mapping: one sub-rule = one event-type → one function call with
the matching `eventType` static string passed to `handleEmailEvent`.

`Sequence_Managed`, `Stale`, and consent gating are validated *inside*
`handleEmailEvent`; the criteria below are deliberately minimal so the
function is reached for every relevant event and can short-circuit
itself.

## Module

All five sub-rules use the **Emails** module (Outgoing Email events).

## Function (all sub-rules)

```text
handleEmailEvent(email_id, eventType, related_deal_id, related_contact_id)
```

The Zoho UI lets you set static argument values per function action. Each
sub-rule passes a different literal for `eventType`; the other three
arguments come from merge fields on the Email record.

## Sub-rules

### WF009a — Outgoing Email Replied

| Field | Value |
|---|---|
| Trigger | `Execute this workflow rule based on` → `Outgoing email` → `Replied` |
| Criteria | `Related Deal` is not empty |
| Function arg `eventType` | `replied` |
| Behavior | Pause sequence (`Sequence_Status = Paused`), create `Review Reply` Task. Reply does **not** auto-advance the Deal. |

### WF009b — Outgoing Email Bounced

| Field | Value |
|---|---|
| Trigger | `Execute this workflow rule based on` → `Outgoing email` → `Bounced` |
| Criteria | `Related Deal` is not empty |
| Function arg `eventType` | `bounced` |
| Behavior | Pause sequence, create `Data Repair` Task, flag Contact `Profile_Completion_Status = Needs Enrichment`. |

### WF009c — Outgoing Email Unreplied

| Field | Value |
|---|---|
| Trigger | `Execute this workflow rule based on` → `Outgoing email` → `Unreplied` (Zoho prompts for a threshold window; set per sequence cadence, suggested 3 business days) |
| Criteria | `Related Deal` is not empty |
| Function arg `eventType` | `not replied` |
| Behavior | Passive event. Log only. No state change; the regular call/email cadence continues to drive the sequence. |

### WF009d — Outgoing Email Opened and Unreplied

| Field | Value |
|---|---|
| Trigger | `Execute this workflow rule based on` → `Outgoing email` → `Open and Unreplied` (note: Zoho UI says "Open", not "Opened") |
| Criteria | `Related Deal` is not empty |
| Function arg `eventType` | `opened but not replied` |
| Behavior | Passive event. Log only. Reserved for future engagement-aware branching. |

### WF009e — Outgoing Email Clicked

| Field | Value |
|---|---|
| Trigger | `Execute this workflow rule based on` → `Outgoing email` → `Clicked` |
| Criteria | `Related Deal` is not empty |
| Function arg `eventType` | `clicked` |
| Behavior | Passive event. Log only. Reserved for future engagement-aware branching. |

## Purpose

Interrupt or pause sequences on adverse email signals (reply, bounce).
Passive events (opened, clicked, not replied) are recorded so the
automation log captures engagement without auto-advancing Stage.

`handleEmailEvent` is the single source of truth for the per-event
behavior; WF009a–e are dumb fanouts to it. Add a new sub-rule when a
new Zoho Outgoing email-event type is needed.

---

# WF010 — Date-Based Follow-Up Router

## Module

Deals

## Trigger

Scheduled/date-time

## Criteria

One of these fields reached:

- Next Action Due Date
- Sequence Paused Until
- Demo Reminder Send At
- Next Commercial Follow-Up Date

## Function

```text
sequenceRouter(deal_id)
```

## Purpose

Resume or trigger scheduled actions.

Examples:

```text
Demo Reminder Send At reached
→ send demo reminder email if call-gated conditions are satisfied
```

```text
Next Commercial Follow-Up Date reached
→ create Commercials Sent Call
```

---

## Minimum Workflow Set

Start with these if time is limited:

1. WF001 — Lead Processor
2. WF002 — Deal Sequence Router
3. WF003 — Deal Stage Change Router
4. WF006 — Call Outcome Handler
5. WF004 — Deal Commercial Status Handler
6. WF005 — Deal Demo Outcome Handler
