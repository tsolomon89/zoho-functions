# TEMPLATE_NAMING_MATRIX.md — Email Template Naming and Purpose

## Purpose

This file defines the email template naming convention.

The coding agent should not guess template names.

Templates should be Stage-specific, not generic Opportunity-level emails.

Bad:

```text
SQL Email 1
SQL Email 2
```

Good:

```text
Demo Booking Email 1
Demo Booked Reminder Email
Commercials Sent Email 1
```

Reason: `SQL` contains multiple different goals: Demo Booking, Demo Booked, and Demo Attended.

---

## Naming Rules

### Call-outcome emails

```text
{Stage} Email {Attempt}
```

Examples:

```text
Demo Booking Email 1
Demo Booking Email 2
Commercials Sent Email 1
Renewal Email 3
```

### Post-call chain emails after fifth call

```text
{Stage} Post-Call Email Chain {Step}
```

Examples:

```text
Demo Booking Post-Call Email Chain 1
Demo Booking Post-Call Email Chain 7
Commercials Sent Post-Call Email Chain 3
Renewal Post-Call Email Chain 7
```

### Special meeting/commercial emails

```text
Demo Booked Confirmation Email
Demo Booked Reminder Email
Demo Attended Post-Demo Email
Commercials Sent Terms Email
Commercials Signed Confirmation Email
Onboarding Kickoff Email
```

---

## Template Matrix

| Stage | Trigger | Template Name | Email Type | Purpose |
|---|---|---|---|---|
| Marketing Consent | Call 1 outcome | Marketing Consent Email 1 | Plain-text or HTML | Request missing qualification/profile data |
| Marketing Consent | Call 2 outcome | Marketing Consent Email 2 | Plain-text or HTML | Missing info follow-up |
| Marketing Consent | Call 3 outcome | Marketing Consent Email 3 | Plain-text or HTML | Qualification reminder |
| Marketing Consent | Call 4 outcome | Marketing Consent Email 4 | Plain-text or HTML | Final qualification prompt |
| Marketing Consent | Call 5 outcome | Marketing Consent Email 5 | Plain-text Sales | Final phone-attempt follow-up |
| Marketing Consent | Post-call chain 1-7 | Marketing Consent Post-Call Email Chain 1-7 | Mixed | No-response sequence |
| Demo Booking | Call 1 outcome | Demo Booking Email 1 | Plain-text Sales | Sell booking the demo after failed/neutral call |
| Demo Booking | Call 2 outcome | Demo Booking Email 2 | HTML or Plain-text | Reinforce demo value |
| Demo Booking | Call 3 outcome | Demo Booking Email 3 | Plain-text Sales | Continued demo-booking follow-up |
| Demo Booking | Call 4 outcome | Demo Booking Email 4 | HTML or Plain-text | Final value-led demo prompt |
| Demo Booking | Call 5 outcome | Demo Booking Email 5 | Plain-text Sales | Final phone-attempt follow-up |
| Demo Booking | Post-call chain 1-7 | Demo Booking Post-Call Email Chain 1-7 | Mixed | No-response sequence |
| Demo Booked | Call outcome / meeting created | Demo Booked Confirmation Email | HTML or Plain-text | Confirm demo details and agenda |
| Demo Booked | Reminder date | Demo Booked Reminder Email | Plain-text or HTML | Protect attendance |
| Demo Booked | No-show/recovery | Demo Booked No-Show Email | Plain-text Sales | Recover/reschedule demo |
| Demo Booked | Post-call chain 1-7 | Demo Booked Post-Call Email Chain 1-7 | Mixed | No-response/reschedule sequence |
| Demo Attended | Demo outcome positive | Demo Attended Post-Demo Email | Plain-text Sales | Thank-you and commercial next steps |
| Demo Attended | Call outcome | Demo Attended Email 1 | Plain-text Sales | Clarify details needed for commercials |
| Demo Attended | Call outcome | Demo Attended Email 2 | HTML or Plain-text | Progress commercial-prep path |
| Demo Attended | Call outcome | Demo Attended Email 3 | Plain-text Sales | Chase missing details |
| Demo Attended | Commercials ready | Commercials Sent Terms Email | Plain-text or HTML | Send commercial terms |
| Demo Attended | Post-call chain 1-7 | Demo Attended Post-Call Email Chain 1-7 | Mixed | No-response sequence before commercials sent |
| Commercials Sent | Call 1 outcome | Commercials Sent Email 1 | Plain-text Sales | Chase commercial decision |
| Commercials Sent | Call 2 outcome | Commercials Sent Email 2 | HTML or Plain-text | Handle objections / prompt discussion |
| Commercials Sent | Call 3 outcome | Commercials Sent Email 3 | Plain-text Sales | Commercial decision follow-up |
| Commercials Sent | Call 4 outcome | Commercials Sent Email 4 | HTML or Plain-text | Final value-led commercial prompt |
| Commercials Sent | Call 5 outcome | Commercials Sent Email 5 | Plain-text Sales | Final phone-attempt follow-up |
| Commercials Sent | Post-call chain 1-7 | Commercials Sent Post-Call Email Chain 1-7 | Mixed | Commercial no-response chase |
| Commercials Signed | Signature confirmed | Commercials Signed Confirmation Email | Plain-text Sales | Confirm next steps |
| Commercials Signed | Call outcome | Commercials Signed Email 1 | Plain-text or HTML | Onboarding handoff |
| Commercials Signed | Post-call chain 1-7 | Commercials Signed Post-Call Email Chain 1-7 | Mixed | Start-onboarding no-response sequence |
| Onboarding | Call outcome | Onboarding Email 1 | Plain-text or HTML | Kickoff/setup steps |
| Onboarding | Call outcome | Onboarding Email 2 | Plain-text Sales | Chase onboarding completion |
| Onboarding | Post-call chain 1-7 | Onboarding Post-Call Email Chain 1-7 | Mixed | Onboarding no-response sequence |
| Renewal | Call 1 outcome | Renewal Email 1 | Plain-text Sales | Start renewal conversation |
| Renewal | Call 2 outcome | Renewal Email 2 | HTML or Plain-text | Reinforce renewal/expansion value |
| Renewal | Call 3 outcome | Renewal Email 3 | Plain-text Sales | Renewal follow-up |
| Renewal | Call 4 outcome | Renewal Email 4 | HTML or Plain-text | Final value-led renewal prompt |
| Renewal | Call 5 outcome | Renewal Email 5 | Plain-text Sales | Final phone-attempt follow-up |
| Renewal | Post-call chain 1-7 | Renewal Post-Call Email Chain 1-7 | Mixed | Renewal no-response sequence |

---

## Template Resolution Rule

The function should resolve template names based on:

```text
Stage
Call Outcome
Attempt Number
Email Chain Step
```

Default:

```text
{Stage} Email {Attempt}
```

After Call 5:

```text
{Stage} Post-Call Email Chain {Step}
```

Special system templates should be mapped explicitly:

```text
Demo Booked Confirmation Email
Demo Booked Reminder Email
Demo Attended Post-Demo Email
Commercials Sent Terms Email
Commercials Signed Confirmation Email
Onboarding Kickoff Email
```
