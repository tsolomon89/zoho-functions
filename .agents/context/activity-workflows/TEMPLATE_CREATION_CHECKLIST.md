# TEMPLATE_CREATION_CHECKLIST.md — Zoho email templates to create

## Purpose

`sendSequencedEmail` looks up Zoho email templates by **exact name**
through `_util_resolveTemplate`. Every template named below must exist
in Setup → Templates → Email Templates with the listed name (case &
spacing must match) before turning on the workflows that send mail
(WF006 onwards).

Total templates: **75** (8 Stages × (5 call-outcome + 7 post-call chain)
+ 11 named specials − 12 not used in current scope = 75).

Categorize templates into folders for sanity. Suggested folder layout:

```
Templates/
  Marketing Consent/      (12 templates)
  Demo Booking/           (12 templates)
  Demo Booked/            (10 templates: Confirmation, Reminder, No-Show, Chain 1-7)
  Demo Attended/          (10 templates: Post-Demo, 3 call-outcome, Chain 1-7)
  Commercials Sent/       (13 templates: Terms + 5 call-outcome + Chain 1-7)
  Commercials Signed/     (10 templates: Confirmation + 1 call-outcome + Chain 1-7 + Email 1)
  Onboarding/             (11 templates: Kickoff + 2 call-outcome + Chain 1-7 + Email 2)
  Renewal/                (12 templates)
```

---

## Marketing Consent (12)

- [ ] Marketing Consent Email 1
- [ ] Marketing Consent Email 2
- [ ] Marketing Consent Email 3
- [ ] Marketing Consent Email 4
- [ ] Marketing Consent Email 5
- [ ] Marketing Consent Post-Call Email Chain 1
- [ ] Marketing Consent Post-Call Email Chain 2
- [ ] Marketing Consent Post-Call Email Chain 3
- [ ] Marketing Consent Post-Call Email Chain 4
- [ ] Marketing Consent Post-Call Email Chain 5
- [ ] Marketing Consent Post-Call Email Chain 6
- [ ] Marketing Consent Post-Call Email Chain 7

## Demo Booking (12)

- [ ] Demo Booking Email 1
- [ ] Demo Booking Email 2
- [ ] Demo Booking Email 3
- [ ] Demo Booking Email 4
- [ ] Demo Booking Email 5
- [ ] Demo Booking Post-Call Email Chain 1
- [ ] Demo Booking Post-Call Email Chain 2
- [ ] Demo Booking Post-Call Email Chain 3
- [ ] Demo Booking Post-Call Email Chain 4
- [ ] Demo Booking Post-Call Email Chain 5
- [ ] Demo Booking Post-Call Email Chain 6
- [ ] Demo Booking Post-Call Email Chain 7

## Demo Booked (10)

- [ ] Demo Booked Confirmation Email
- [ ] Demo Booked Reminder Email
- [ ] Demo Booked No-Show Email
- [ ] Demo Booked Post-Call Email Chain 1
- [ ] Demo Booked Post-Call Email Chain 2
- [ ] Demo Booked Post-Call Email Chain 3
- [ ] Demo Booked Post-Call Email Chain 4
- [ ] Demo Booked Post-Call Email Chain 5
- [ ] Demo Booked Post-Call Email Chain 6
- [ ] Demo Booked Post-Call Email Chain 7

## Demo Attended (11)

- [ ] Demo Attended Post-Demo Email
- [ ] Demo Attended Email 1
- [ ] Demo Attended Email 2
- [ ] Demo Attended Email 3
- [ ] Demo Attended Post-Call Email Chain 1
- [ ] Demo Attended Post-Call Email Chain 2
- [ ] Demo Attended Post-Call Email Chain 3
- [ ] Demo Attended Post-Call Email Chain 4
- [ ] Demo Attended Post-Call Email Chain 5
- [ ] Demo Attended Post-Call Email Chain 6
- [ ] Demo Attended Post-Call Email Chain 7

## Commercials Sent (13)

- [ ] Commercials Sent Terms Email
- [ ] Commercials Sent Email 1
- [ ] Commercials Sent Email 2
- [ ] Commercials Sent Email 3
- [ ] Commercials Sent Email 4
- [ ] Commercials Sent Email 5
- [ ] Commercials Sent Post-Call Email Chain 1
- [ ] Commercials Sent Post-Call Email Chain 2
- [ ] Commercials Sent Post-Call Email Chain 3
- [ ] Commercials Sent Post-Call Email Chain 4
- [ ] Commercials Sent Post-Call Email Chain 5
- [ ] Commercials Sent Post-Call Email Chain 6
- [ ] Commercials Sent Post-Call Email Chain 7

## Commercials Signed (9)

- [ ] Commercials Signed Confirmation Email
- [ ] Commercials Signed Email 1
- [ ] Commercials Signed Post-Call Email Chain 1
- [ ] Commercials Signed Post-Call Email Chain 2
- [ ] Commercials Signed Post-Call Email Chain 3
- [ ] Commercials Signed Post-Call Email Chain 4
- [ ] Commercials Signed Post-Call Email Chain 5
- [ ] Commercials Signed Post-Call Email Chain 6
- [ ] Commercials Signed Post-Call Email Chain 7

## Onboarding (10)

- [ ] Onboarding Kickoff Email
- [ ] Onboarding Email 1
- [ ] Onboarding Email 2
- [ ] Onboarding Post-Call Email Chain 1
- [ ] Onboarding Post-Call Email Chain 2
- [ ] Onboarding Post-Call Email Chain 3
- [ ] Onboarding Post-Call Email Chain 4
- [ ] Onboarding Post-Call Email Chain 5
- [ ] Onboarding Post-Call Email Chain 6
- [ ] Onboarding Post-Call Email Chain 7

## Renewal (12)

- [ ] Renewal Email 1
- [ ] Renewal Email 2
- [ ] Renewal Email 3
- [ ] Renewal Email 4
- [ ] Renewal Email 5
- [ ] Renewal Post-Call Email Chain 1
- [ ] Renewal Post-Call Email Chain 2
- [ ] Renewal Post-Call Email Chain 3
- [ ] Renewal Post-Call Email Chain 4
- [ ] Renewal Post-Call Email Chain 5
- [ ] Renewal Post-Call Email Chain 6
- [ ] Renewal Post-Call Email Chain 7

---

## Merge fields each template should reference

Common merge fields the resolved-template body should be able to use
(naming follows Zoho merge syntax: `${Module.Field}`).

| Purpose | Merge field |
|---|---|
| Contact first name | `${Contacts.First_Name}` |
| Contact full name | `${Contacts.Full_Name}` |
| Account name | `${Contacts.Account_Name}` or `${Deals.Account_Name}` |
| Deal name | `${Deals.Deal_Name}` |
| Stage | `${Deals.Stage1}` |
| Opportunity | `${Deals.Stage}` |
| Demo Start | `${Deals.Demo_Start_DateTime}` |
| Sender first name | `${User.First_Name}` |
| Sender signature | `${User.Email_Signature}` |

If the template depends on the **Deal** record (e.g., Stage,
Demo_Start_DateTime), the send endpoint must be configured to pull the
Deal context. `sendSequencedEmail` currently posts to
`/Contacts/{id}/actions/send_mail`. If Deal-level merge tags don't
populate, switch the endpoint to `/Deals/{deal_id}/actions/send_mail`
and resolve Contact email from the Deal lookup instead.

---

## Acceptance criteria before WF006 activation

- [ ] All 79 templates exist with the exact names listed.
- [ ] Each template renders correctly against a sample Contact + Deal.
- [ ] Marketing Consent merge field renders for Contacts where
      `Marketing_Consent_Status` = `Consented` (and templates explicitly
      do NOT send to `Not Consented` or `Withdrawn` — handled in
      `sendSequencedEmail`).
- [ ] No template sells the whole product as default copy (per Stage
      Goal Rule in `AGENTS.md` §"Stage Goal Rule"). Each Stage sells its
      own goal only.
