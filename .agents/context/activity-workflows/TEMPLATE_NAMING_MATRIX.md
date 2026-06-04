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
Demo Confirmation Reminder Email
Commercial Agreement Email 1
```

Reason: `SQL` contains multiple different goals: Demo Booking, Demo Confirmation, and Demo Hosted.

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
Commercial Agreement Email 1
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
Commercial Agreement Post-Call Email Chain 3
Renewal Post-Call Email Chain 7
```

### Special meeting/commercial emails

```text
Demo Confirmation Email
Demo Confirmation Reminder Email
Demo Hosted Post-Demo Email
Commercial Agreement Terms Email
Commercial Agreement Confirmation Email
Onboarding Kickoff Email
```

---

## Template Matrix

| Stage | Trigger | Template Name | Email Type | Purpose |
|---|---|---|---|---|
| Marketing Qualification | Call 1 outcome | Marketing Qualification Email 1 | Plain-text or HTML | Request missing qualification/profile data |
| Marketing Qualification | Call 2 outcome | Marketing Qualification Email 2 | Plain-text or HTML | Missing info follow-up |
| Marketing Qualification | Call 3 outcome | Marketing Qualification Email 3 | Plain-text or HTML | Qualification reminder |
| Marketing Qualification | Call 4 outcome | Marketing Qualification Email 4 | Plain-text or HTML | Final qualification prompt |
| Marketing Qualification | Call 5 outcome | Marketing Qualification Email 5 | Plain-text Sales | Final phone-attempt follow-up |
| Marketing Qualification | Post-call chain 1-7 | Marketing Qualification Post-Call Email Chain 1-7 | Mixed | No-response sequence |
| Demo Booking | Call 1 outcome | Demo Booking Email 1 | Plain-text Sales | Sell booking the demo after failed/neutral call |
| Demo Booking | Call 2 outcome | Demo Booking Email 2 | HTML or Plain-text | Reinforce demo value |
| Demo Booking | Call 3 outcome | Demo Booking Email 3 | Plain-text Sales | Continued demo-booking follow-up |
| Demo Booking | Call 4 outcome | Demo Booking Email 4 | HTML or Plain-text | Final value-led demo prompt |
| Demo Booking | Call 5 outcome | Demo Booking Email 5 | Plain-text Sales | Final phone-attempt follow-up |
| Demo Booking | Post-call chain 1-7 | Demo Booking Post-Call Email Chain 1-7 | Mixed | No-response sequence |
| Demo Confirmation | Call outcome / meeting created | Demo Confirmation Email | HTML or Plain-text | Confirm demo details and agenda |
| Demo Confirmation | Reminder date | Demo Confirmation Reminder Email | Plain-text or HTML | Protect attendance |
| Demo Confirmation | No-show/recovery | Demo Confirmation No-Show Email | Plain-text Sales | Recover/reschedule demo |
| Demo Confirmation | Post-call chain 1-7 | Demo Confirmation Post-Call Email Chain 1-7 | Mixed | No-response/reschedule sequence |
| Demo Hosted | Demo outcome positive | Demo Hosted Post-Demo Email | Plain-text Sales | Thank-you and commercial next steps |
| Demo Hosted | Call outcome | Demo Hosted Email 1 | Plain-text Sales | Clarify details needed for commercials |
| Demo Hosted | Call outcome | Demo Hosted Email 2 | HTML or Plain-text | Progress commercial-prep path |
| Demo Hosted | Call outcome | Demo Hosted Email 3 | Plain-text Sales | Chase missing details |
| Demo Hosted | Commercials ready | Commercial Agreement Terms Email | Plain-text or HTML | Send commercial terms |
| Demo Hosted | Post-call chain 1-7 | Demo Hosted Post-Call Email Chain 1-7 | Mixed | No-response sequence before Commercial Agreement |
| Commercial Agreement | Call 1 outcome | Commercial Agreement Email 1 | Plain-text Sales | Chase commercial decision |
| Commercial Agreement | Call 2 outcome | Commercial Agreement Email 2 | HTML or Plain-text | Handle objections / prompt discussion |
| Commercial Agreement | Call 3 outcome | Commercial Agreement Email 3 | Plain-text Sales | Commercial decision follow-up |
| Commercial Agreement | Call 4 outcome | Commercial Agreement Email 4 | HTML or Plain-text | Final value-led commercial prompt |
| Commercial Agreement | Call 5 outcome | Commercial Agreement Email 5 | Plain-text Sales | Final phone-attempt follow-up |
| Commercial Agreement | Post-call chain 1-7 | Commercial Agreement Post-Call Email Chain 1-7 | Mixed | Commercial no-response chase |
| Onboarding | Signature confirmed | Commercial Agreement Confirmation Email | Plain-text Sales | Confirm next steps |
| Onboarding | Call outcome | Onboarding Email 1 | Plain-text or HTML | Onboarding handoff |
| Onboarding | Post-call chain 1-7 | Onboarding Post-Call Email Chain 1-7 | Mixed | Start-onboarding no-response sequence |
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
Demo Confirmation Email
Demo Confirmation Reminder Email
Demo Hosted Post-Demo Email
Commercial Agreement Terms Email
Commercial Agreement Confirmation Email
Onboarding Kickoff Email
```
