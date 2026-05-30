# FUNCTION_SPEC.md — Zoho CRM Automation Function Specifications

## Purpose

This document defines the intended Deluge/API function boundaries.

Use this to guide implementation.

Do not build one giant function that does everything.

---

## Global Rules

All functions must be idempotent.

All functions must:

- avoid duplicate creation;
- verify API names;
- log errors clearly;
- return useful debug output;
- gracefully handle missing data;
- preserve existing records where possible;
- not send customer-facing emails unless a safe trigger occurred.

---

# 1. `processLeadOrRecord(record_id, module_name)`

## Purpose

Entry point for Leads, imports, or records requiring graph processing.

## Inputs

```text
record_id
module_name
```

## Reads

- Source record fields.
- Existing Contact by email.
- Existing Account by domain/company.
- Existing Deal by Contact/Account/Stage/Product context.
- Products by product interest/mapping.

## Writes

- Contact
- Account
- Deal
- Product associations
- Deal value
- Lead processing status
- error/status fields

## Responsibilities

1. Read source record.
2. Normalize email, phone, company, domain.
3. Upsert Contact.
4. Upsert Account.
5. Upsert Deal.
6. Link Contact ↔ Account.
7. Link Contact ↔ Deal.
8. Link Deal ↔ Account.
9. Resolve Products.
10. Sync Deal value.
11. Assign Stage/Opportunity.
12. Call `sequenceRouter(deal_id)` if sequence not started.

## Must not

- Create duplicates.
- Fail whole graph because product resolution fails.
- Send email directly unless explicitly delegated by a safe trigger.

---

# 2. `upsertContact(source_record)`

## Purpose

Find or create/update Contact.

## Matching rules

Preferred:

```text
Email
```

Fallback:

```text
Phone + Name
```

Only use weak matching with caution.

## Writes

- Contact identity fields.
- Contact source classification.
- Marketing consent status.
- Profile completion status.

## Return

```json
{
  "contact_id": "...",
  "created": true,
  "matched_by": "email|phone_name|manual"
}
```

---

# 3. `upsertAccount(source_record, contact)`

## Purpose

Find or create/update Account.

## Matching rules

Preferred:

```text
Explicit Account ID
Domain
Website
Company name exact/normalized
```

## Writes

- Account name.
- Website/domain.
- industry/size if available.
- source classification.
- enrichment status.

---

# 4. `upsertDeal(source_record, contact_id, account_id)`

## Purpose

Find or create/update Deal.

## Matching rules

Use a combination of:

- Account
- Contact
- active/open status
- Stage/Opportunity context
- product interest
- source record reference if available

## Writes

- Account lookup.
- Contact lookup/related list.
- Stage.
- Opportunity.
- Amount.
- Lead Source.
- Product Resolution Status.
- Sequence Status if empty.

---

# 5. `resolveProducts(deal_id, source_record)`

## Purpose

Resolve product interest to Products.

## Reads

- Product Interest.
- Product mapping aliases.
- Products module.
- Active for Deal Automation flag.

## Writes

- Product Resolution Status.
- Associated Product IDs.
- Deal/Product related list, if available.
- error/debug fields if unresolved.

## Failure behavior

If unresolved:

```text
Product Resolution Status = Failed or Missing Product Interest
```

Do not block Contact/Account/Deal creation.

---

# 6. `syncDealProductsAndValue(deal_id)`

## Purpose

Calculate Deal Amount from associated Products.

## Reads

- Associated Products.
- Default Deal Value.
- Value Calculation Method.
- Needs Manual Pricing.

## Writes

- Deal Amount.
- Deal Value Source.
- Product Resolution Status.

## Rules

If Product value is ambiguous:

```text
Deal Value Source = Manual or Estimated
Product Resolution Status = Manual Review
```

---

# 7. `sequenceRouter(deal_id)`

## Purpose

Main Deal state-machine router.

## Reads

- Deal Stage.
- Opportunity.
- Sequence Status.
- Active Sequence Stage.
- Active Sequence Attempt.
- Automation Suppressed.
- Suppression Reason.
- Commercials Status.
- Demo Outcome.
- Next Action Due Date.
- Sequence Paused Until.

## Writes

- Sequence Status.
- Active Sequence Stage.
- Active Sequence Attempt.
- Next Action Type.
- Next Action Due Date.
- Call/Task/Event records as required.

## Logic

```text
if Automation Suppressed = true:
    do nothing

if Stage is empty:
    create manual review task
    return

if Sequence Status in Paused/Manual Only/Suppressed:
    do nothing unless resume date reached

if Stage changed from Active Sequence Stage:
    supersedeOldSequence(deal_id)

if Sequence Status is empty or Not Started:
    createStageCall(deal_id, Stage, 1)
```

## Key rule

Every Stage starts with Call 1.

---

# 8. `createStageCall(deal_id, stage, attempt)`

## Purpose

Create a sequence-managed Call record.

## Inputs

```text
deal_id
stage
attempt
```

## Writes

Call record with:

- Subject
- Related Deal
- Contact/Account where possible
- Sequence Managed = true
- Sequence Stage
- Sequence Attempt
- Blocks Email Until Completed = true
- Call Purpose Detail
- Call Start Time / Due date according to Zoho requirements

## Duplicate prevention

Before creating, search for existing open call where:

```text
Related Deal = deal_id
Sequence Managed = true
Sequence Stage = stage
Sequence Attempt = attempt
Call Outcome is empty
```

If found, reuse/return it.

---

# 9. `handleCallOutcome(call_id)`

## Purpose

Primary gate for emails and next actions.

## Reads

- Call.
- Related Deal.
- Call Outcome.
- Sequence Stage.
- Sequence Attempt.
- Next Follow-Up Date.
- Active Deal Stage.
- Sequence Status.

## Logic

```text
if call not sequence managed:
    return

if Related Deal missing:
    log error
    return

if call.Sequence Stage != deal.Stage:
    ignore or mark stale

if Call Outcome = Positive:
    handlePositiveCallOutcome()

if Call Outcome = Neutral:
    sendSequencedEmail()
    create next Call

if Call Outcome = No Answer:
    sendSequencedEmail()
    create next Call

if Call Outcome = Deferred:
    set Sequence Status = Deferred
    set Sequence Paused Until = Next Follow-Up Date

if Call Outcome = Bad Data:
    pause sequence
    create data repair task

if Call Outcome = Already Handled:
    mark current step complete or advance

if Call Outcome = Not Relevant:
    create manual review or skip

if Call Outcome = Manual Only:
    pause automation

if Call Outcome = Do Not Contact:
    suppress automation
```

## Attempt handling

Attempts 1-5:

```text
Call attempt
→ outcome-based email
→ next call
```

After Call 5:

```text
Start 7-email post-call chain
```

Do not send email if the Stage changed or sequence was superseded.

---

# 10. `sendSequencedEmail(deal_id, stage, attempt_or_chain_step, trigger_context)`

## Purpose

Send the correct email template.

## Reads

- Deal.
- Contact.
- Sequence Thread Message ID.
- Last Email Message ID.
- Stage.
- attempt/chain step.
- trigger outcome.
- template mapping.

## Writes

- Last Email Template.
- Last Email Sent At.
- Last Email Message ID.
- Sequence Thread Message ID if first email.
- Active Email Chain Step.

## Template resolution

Template naming convention should use Stage names:

```text
{Stage} Email {Attempt}
{Stage} Post-Call Email Chain {Step}
```

Examples:

```text
Demo Booking Email 1
Commercials Sent Email 3
Renewal Post-Call Email Chain 7
```

---

# 11. `handleDemoOutcome(deal_id)`

## Purpose

Handle Demo Outcome transitions.

## Rules

```text
Attended - Qualified:
    Stage = Demo Attended
    send post-demo email
    Commercials Status = Drafting
    create task: Draft Commercials

Attended - Needs Follow-up:
    Stage = Demo Attended
    create call or task

Attended - Not Qualified:
    move Lost / Disqualified

No Show:
    create recovery call
    optionally move to Demo Booking

Rescheduled:
    update meeting/reminder state

Cancelled:
    move to Demo Booking or Lost based on context
```

---

# 12. `handleCommercialsStatusChange(deal_id)`

## Purpose

Handle commercial transitions.

## Rules

```text
Commercials Status = Sent:
    Stage = Commercials Sent
    Opportunity = FTP
    Commercials Sent At = now if empty
    Sequence Status = Not Started
    create Commercials Sent Call 1
```

```text
Commercials Status = Signed:
    Stage = Commercials Signed
    Opportunity = RTP
    Signed At = now if empty
```

```text
Commercials Status = Deferred:
    Sequence Status = Deferred
    Sequence Paused Until = Next Commercial Follow-Up Date
```

---

# 13. `handleMeetingEvent(event_id)`

## Purpose

Handle Event/Meeting updates.

## Rules

Meeting date changed:

```text
recalculate Demo Reminder Send At
```

Meeting cancelled:

```text
Demo Status = Cancelled
create recovery call or manual review
```

Meeting rescheduled:

```text
Demo Status = Rescheduled
recalculate reminder
```

---

# 14. `handleTaskCompletion(task_id)`

## Purpose

Handle non-call manual work completion.

Examples:

Task Type = Draft Commercials:

```text
if completed and Commercials Status = Ready to Send:
    send commercials or create send-commercials task
```

Task Type = Data Repair:

```text
if completed:
    resume sequenceRouter
```

---

# 15. `supersedeOldSequence(deal_id)`

## Purpose

Prevent stale sequences.

## Writes

- Sequence Superseded At.
- Sequence Status.
- Active Sequence Stage.
- Active Sequence Attempt.

## Rule

Never delete historical activities unless explicitly required.

---

# 16. `calculateBusinessDate(start_date, offset, mode)`

## Purpose

Calculate dates like:

- +2 business days
- +5 business days
- one business day before in AM

---

# 17. `logAutomationEvent(context)`

## Purpose

Create reliable debugging output.

Should log:

- function name
- module
- record ID
- action attempted
- outcome
- error
- fields read/written
- duplicate prevention result
