# TEST_CASES.md — Zoho CRM Automation Test Plan

## Purpose

This document defines the minimum test cases required before considering the automation safe.

The core risk is accidental duplicate creation or accidental customer-facing email sends.

---

## Test Data Setup

Use a small controlled dataset:

- 5-10 Lead records.
- 2 existing Contacts.
- 2 existing Accounts.
- 2 existing Deals.
- 3 Products.
- At least one bad product interest.
- At least one imported historical/existing record.
- At least one calendar/demo-booking style record.

---

# Test 1 — New Lead with complete data

## Expected

- Contact created.
- Account created.
- Deal created.
- Contact linked to Account.
- Contact linked to Deal.
- Deal linked to Account.
- Product resolved.
- Product associated to Deal.
- Deal Amount populated.
- Stage assigned.
- Opportunity assigned.
- Sequence Status initialized.
- Call 1 created for current Stage.
- No email sent immediately.

## Fail if

- duplicate Contact created;
- duplicate Account created;
- duplicate Deal created;
- email sent before call outcome.

---

# Test 2 — Existing Contact and Account, no Deal

## Expected

- Existing Contact reused.
- Existing Account reused.
- New Deal created.
- Contact linked to Deal.
- Product/value synced.
- Call 1 created.
- No email sent immediately.

---

# Test 3 — Existing Contact, Account, and Deal

## Expected

- Existing Deal reused/updated.
- No duplicate Deal.
- Product/value updated if needed.
- No duplicate Call 1 if one already exists.
- Sequence state remains consistent.

---

# Test 4 — Product lookup fails

## Expected

- Contact created/reused.
- Account created/reused.
- Deal created/reused.
- Product Resolution Status = Failed / Missing Product Interest / Manual Review.
- Data/product repair task created if configured.
- Sequence does not crash.
- Deal remains repairable.

## Fail if

Contact/Account/Deal creation fails only because product did not resolve.

---

# Test 5 — Imported existing Deal at Commercials Sent

## Input

```text
Stage = Commercials Sent
Opportunity = FTP
Commercials Status = Sent
Commercials Sent At populated
```

## Expected

- Deal state preserved.
- Sequence initialized.
- Commercials Sent Call 1 created.
- No immediate chase email sent.
- Sequence Status = Waiting on Call.

---

# Test 6 — Demo Booking Call 1 = No Answer

## Action

Rep sets:

```text
Call Outcome = No Answer
```

## Expected

- Demo Booking Email 1 sent.
- Last Email Message ID stored.
- Demo Booking Call 2 created.
- Active Sequence Attempt increments.
- Stage remains Demo Booking.

---

# Test 7 — Demo Booking Call 1 = Positive

## Action

Rep sets:

```text
Call Outcome = Positive
```

## Expected

- Meeting/Event created or requested.
- Stage moves to Demo Booked.
- Opportunity remains SQL.
- Demo Booking sequence superseded.
- Demo Booked sequence starts.
- No stale Demo Booking Email 1 is sent after Stage changes.

---

# Test 8 — Demo Booked / meeting reminder

## Expected

- Demo Reminder Send At calculated as one business day before in the AM.
- Reminder sends only when reminder date is reached.
- If meeting rescheduled, Demo Reminder Send At recalculates.

## Fail if

- reminder sends immediately on import;
- old reminder remains active after reschedule.

---

# Test 9 — Demo Outcome = Attended - Qualified

## Action

Rep sets:

```text
Demo Outcome = Attended - Qualified
```

## Expected

- Stage moves to Demo Attended.
- Post-demo email sent.
- Commercials Status = Drafting.
- Task created: Draft Commercials.
- Opportunity remains SQL.
- Stage does not move to Commercials Sent until commercials are actually sent.

---

# Test 10 — Commercials Status = Sent

## Action

Rep/system sets:

```text
Commercials Status = Sent
```

## Expected

- Commercials Sent At populated if empty.
- Stage = Commercials Sent.
- Opportunity = FTP.
- Commercials Sent Call 1 created.
- Due date = +2 business days unless overridden.
- No chase email sent immediately.

---

# Test 11 — Commercials Sent Call 1 = Deferred

## Action

Rep sets:

```text
Call Outcome = Deferred
Next Follow-Up Date = [future date]
```

## Expected

- Sequence Status = Deferred.
- Sequence Paused Until = future date.
- No emails sent before future date.
- Sequence resumes on future date.

---

# Test 12 — Commercials Sent Call 1 = No Answer

## Expected

- Commercials Sent Email 1 sent.
- Commercials Sent Call 2 created.
- Stage remains Commercials Sent.
- Opportunity remains FTP.

---

# Test 13 — After fifth call

## Expected

- Five call attempts exist.
- After Call 5, seven-email post-call chain begins.
- Email chain is Stage-specific.
- Email chain stops if Stage changes or sequence is superseded.

---

# Test 14 — Stage changes while old sequence exists

## Action

Rep manually sets:

```text
Stage = Demo Booked
```

## Expected

- Demo Booking sequence superseded.
- Pending Demo Booking Call/Email actions marked stale/cancelled/ignored.
- Demo Booked sequence starts.
- Old Demo Booking emails do not send.

---

# Test 15 — Email reply received

## Expected

- Reply does not automatically count as positive.
- Review Reply task created.
- Sequence paused if configured.
- Rep decides next state.

---

# Test 16 — Email bounced

## Expected

- Sequence paused.
- Bad email/data repair task created.
- Contact/profile status updated.
- No further emails sent.

---

# Test 17 — Do Not Contact

## Expected

- Automation Suppressed = true.
- Suppression Reason set.
- Sequence Status = Suppressed.
- No further calls/emails created.

---

# Test 18 — Already Handled

## Expected

- Function marks current sequence step complete.
- Advances or creates next safe action depending on Stage.
- Does not send irrelevant email.

---

# Test 19 — Not Relevant

## Expected

- Function pauses or routes to manual review.
- No automatic email sent unless explicitly configured.
- Deal remains active.

---

# Test 20 — Renewal flow

## Expected

- Renewal Call 1 created.
- No renewal email sent until call outcome.
- Positive outcome renews/expands.
- No answer outcome sends Renewal Email 1 and creates Renewal Call 2.
