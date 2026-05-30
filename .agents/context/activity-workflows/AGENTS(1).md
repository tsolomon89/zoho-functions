# AGENTS.md — Zoho CRM Automation Agent Context

## Project Summary

This is a Zoho CRM automation/refactor project.

The goal is to build an idempotent CRM automation system that:

1. Processes Leads, Contacts, Accounts, Deals, and Products.
2. Converts or updates Leads into the correct Contact / Account / Deal graph.
3. Associates Deals with Products and derives Deal value.
4. Runs a Stage-specific, call-gated activity sequence.
5. Sends automated emails only after safe triggers.
6. Prevents stale workflows from continuing after a Stage change.
7. Preserves the distinction between `Opportunity` and `Stage`.

This is not a generic nurture system. It is a commercial state machine.

---

## Core Ontology

### Contact

The Contact represents the person.

Contacts hold identity/profile data: name, email, phone, job title, role, consent, source context, profile completion, and enrichment state.

Contacts do **not** own the pipeline state.

### Account

The Account represents the company, tenant, customer, or commercial entity.

Accounts hold company name, website/domain, industry, company size, account status, and customer/client classification.

Contacts should be linked to Accounts.

### Deal

The Deal is the commercial motion.

The Deal owns Opportunity, Stage, product interest, product associations, Deal value, sequence state, meeting/demo state, commercial status, next action state, and suppression/manual-only state.

The Deal is the state machine.

---

## Critical Field Semantics

The default Zoho Deal `Stage` field has been renamed in the UI to something like `Opportunity`.

In this project:

```text
Opportunity = broad commercial qualification/revenue state
Stage       = current goal inside that commercial motion
```

### Opportunity values

```text
MQL
SQL
FTP
RTP
```

### Stage values

```text
Marketing Consent
Demo Booking
Demo Booked
Demo Attended
Commercials Sent
Commercials Signed
Onboarding
Renewal
```

### Stage → Opportunity mapping

| Stage | Opportunity |
|---|---|
| Marketing Consent | MQL |
| Demo Booking | SQL |
| Demo Booked | SQL |
| Demo Attended | SQL |
| Commercials Sent | FTP |
| Commercials Signed | RTP / Onboarding |
| Onboarding | RTP |
| Renewal | RTP |

### Stage rank order

| Rank | Stage |
|---:|---|
| 1 | Marketing Consent |
| 2 | Demo Booking |
| 3 | Demo Booked |
| 4 | Demo Attended |
| 5 | Commercials Sent |
| 6 | Commercials Signed |
| 7 | Onboarding |
| 8 | Renewal |

---

## Non-Negotiable Sequence Rule

Every Stage sequence starts with a call.

```text
First activity in every Stage = Call 1
```

Automated emails must not be sent merely because a record was created, imported, converted, assigned a Stage, assigned an Opportunity, or moved into a pipeline.

Automated emails can only be sent after a safe trigger.

Safe triggers include:

- Call outcome recorded.
- Call marked no answer.
- Call marked already handled.
- Call marked not relevant.
- Meeting outcome recorded.
- Scheduled reminder date reached.
- Commercials actually sent.
- Commercial follow-up date reached.
- Explicit manual/system-safe trigger.

---

## Stage Goal Rule

Each Stage sells its own goal.

Emails should not sell the whole product by default.

| Stage | Goal being sold |
|---|---|
| Marketing Consent | Complete profile/qualification data |
| Demo Booking | Book the demo |
| Demo Booked | Attend the demo |
| Demo Attended | Complete post-demo/commercial handoff |
| Commercials Sent | Discuss/accept commercial terms |
| Commercials Signed | Start onboarding |
| Onboarding | Complete onboarding |
| Renewal | Renew/expand/retain |

---

## Lead / Record Processing Rule

The lead processor must be idempotent.

It should:

1. Find or create Contact.
2. Find or create Account.
3. Find or create Deal.
4. Link Contact to Account.
5. Link Contact to Deal.
6. Link Deal to Account.
7. Resolve product interest.
8. Associate Products to Deal.
9. Calculate/update Deal value.
10. Assign Stage and Opportunity.
11. Initialize the correct Stage sequence.

Do not create duplicate records.

Do not fail the whole process because Product resolution fails. If Product resolution fails, leave the Deal repairable and log the issue.

---

## Sequence Rule

Only one Stage sequence should be active per Deal at a time.

When Stage changes:

1. Supersede old sequence.
2. Stop old pending actions where possible.
3. Mark old sequence as superseded.
4. Reset attempt counter for the new Stage.
5. Start new Stage sequence.
6. Preserve historical activities.

Do not allow old MQL/SQL/FTP emails or activities to continue after the record has moved to a new Stage.

---

## Commercial Boundary Rule

`Commercials Sent` is the boundary condition for FTP.

SQL ends by sending commercial terms.

FTP begins by chasing a decision on commercial terms already sent.

Do not start FTP chase until commercial terms have actually been sent.

---

## Demo Boundary Rule

`Demo Attended` is not complete when the meeting ends.

It is complete only after:

1. Demo outcome is recorded.
2. Post-demo email is sent.
3. Commercial drafting/sending process is started.
4. Commercials are sent.

Only after commercial terms are sent should the record move to:

```text
Stage = Commercials Sent
Opportunity = FTP
```

---

## Preferred Architecture

Use:

```text
Deals    = state machine trigger
Calls    = activity-outcome trigger
Events   = meeting/demo trigger
Tasks    = manual/non-call work trigger
Emails   = interruption/reply/bounce trigger
Leads    = conversion trigger only
Contacts = profile/consent trigger only
```

### Primary functions

- `processLeadOrRecord`
- `upsertContact`
- `upsertAccount`
- `upsertDeal`
- `resolveProducts`
- `syncDealProductsAndValue`
- `sequenceRouter`
- `createStageCall`
- `handleCallOutcome`
- `sendSequencedEmail`
- `handleDemoOutcome`
- `handleCommercialsStatusChange`
- `supersedeOldSequence`
- `calculateBusinessDate`
- `logAutomationEvent`

---

## Coding Constraints

- Do not guess Zoho API names.
- Verify field API names using Zoho metadata or current org API-name export.
- Use module API names, not UI labels.
- Meetings are `Events` in the Zoho API.
- Be idempotent.
- Avoid duplicate Contacts, Accounts, Deals, Calls, Tasks, Meetings, Emails, and Product associations.
- Return useful debug output from functions.
- Log every failure path clearly.
- Product failures must not block Contact/Account/Deal creation.
- Template lookup failures must not corrupt the Deal.
- Stage changes must supersede old sequences.

---

## Minimum Viable Flow

1. Lead/import/form/calendar event enters CRM.
2. Processor creates or repairs Contact/Account/Deal/Product graph.
3. Deal receives Stage and Opportunity.
4. Deal workflow calls `sequenceRouter(deal_id)`.
5. `sequenceRouter` creates `Call 1` for the current Stage.
6. Rep completes/classifies Call.
7. Call workflow calls `handleCallOutcome(call_id)`.
8. `handleCallOutcome` sends the correct Stage-specific email, creates the next call, advances Stage, defers, pauses, or marks Lost.
9. Stage change triggers new sequence.
10. Old sequence is superseded.
