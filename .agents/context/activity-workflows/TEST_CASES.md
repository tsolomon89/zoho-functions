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

# Test 5 — Imported existing Deal at Commercial Agreement

## Input

```text
Stage = Commercial Agreement
Opportunity = FTP
Commercials Status = Sent
Commercial Agreement At populated
```

## Expected

- Deal state preserved.
- Sequence initialized.
- Commercial Agreement Call 1 created.
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
- Stage moves to Demo Confirmation.
- Opportunity remains SQL.
- Demo Booking sequence superseded.
- Demo Confirmation sequence starts.
- No stale Demo Booking Email 1 is sent after Stage changes.

---

# Test 8 — Demo Event Lifecycle (Scheduled, Rescheduled, Confirmed, Cancelled, No Show)

## Action

Create an Event fixture under the Events module linked to the open Deal (at Demo Confirmation stage):
- Subject = `<sessionPrefix>_Demo`
- What_Id = canonical Deal ID
- $se_module = Deals
- Who_Id = primary Contact ID
- Sequence_Managed = Yes
- Meeting_Type = Demo
- Meeting_Status = Scheduled
- Start_DateTime = future datetime
- End_DateTime = future datetime

Then:
1. Update Event Meeting_Status = "Rescheduled" (and shift Start_DateTime / End_DateTime).
2. Update Event Meeting_Status = "Confirmed".
3. Update Event Meeting_Status = "Cancelled".
4. Update Event Meeting_Status = "No Show".

## Expected

- Event is created and successfully linked to the Deal via `What_Id` and the primary Contact via `Who_Id`.
- Deal `Demo_Meeting_ID` is populated with the Event's ID.
- Deal `Demo_Status = "Scheduled"`.
- Deal `Demo_Start_DateTime` and `Demo_End_DateTime` match the Event.
- Deal `Demo_Reminder_Send_At` and Event `Reminder_Send_At` are populated correctly (-1 business day AM).
- **On Reschedule**: Deal dates and `Demo_Reminder_Send_At` / Event `Reminder_Send_At` are recomputed and updated.
- **On Confirmed**: Deal `Demo_Status` mirrors this.
- **On Cancelled**: Deal `Demo_Status` is cancelled, and a recovery Call (e.g. `Demo Booking Call 1`) is created.
- **On No Show**: Deal `Demo_Status` is updated and demo outcome logic triggers.

## Fail if

- Event fails to link or mirror its state to the Deal.
- Reminder dates are not calculated or do not recalculate on rescheduled.
- Cancelled event fails to trigger a recovery Call.

---

# Test 9 — Task Lifecycle (Creation & Completion)

## Action

1. Advance Deal to Demo Confirmation, set `Demo_Outcome = "Attended - Qualified"`.
2. Retrieve the resulting `Draft Commercials` Task and update its `Status = "Completed"`.
3. Separate flow: set `Call_Outcome = "Bad Data"` on an open Call to trigger a `Data Repair` Task.
4. Retrieve the `Data Repair` Task and update its `Status = "Completed"`.

## Expected

- **On Demo Qualified**:
  - `Draft Commercials` Task is created and linked: `What_Id` = Deal ID, `$se_module` = "Deals", `Who_Id` = primary Contact ID, `Sequence_Managed` = "Yes".
  - Task owner matches the Deal's Owner.
  - Completing the Task fires `WF008` (Task Completion Handler) successfully.
  - Completing `Draft Commercials` does NOT advance the stage or commercials status prematurely (remains Demo Hosted / Drafting).
- **On Bad Data**:
  - `Data Repair` Task is created, linking `What_Id` to the Deal, with `Blocks_Sequence = "Yes"` and `Sequence_Managed = "Yes"`.
  - Deal `Sequence_Status` is updated to `Paused`.
  - Completing the `Data Repair` Task fires `WF008`, which resumes the sequence (`Sequence_Status = Waiting on Call`) and generates a new Call.

## Fail if

- Task is created without proper polymorphic linkage to the Deal or primary Contact.
- Task completion fails to fire WF008 or throws execution exceptions.
- Sequence fails to resume upon completion of the blocking Data Repair Task.

---

# Test 10 — Commercials Status = Sent

## Action

Rep/system sets:

```text
Commercials Status = Sent
```

## Expected

- Commercial Agreement At populated if empty.
- Stage = Commercial Agreement.
- Opportunity = FTP.
- Commercial Agreement Call 1 created.
- Due date = +2 business days unless overridden.
- No chase email sent immediately.

---

# Test 11 — Commercial Agreement Call 1 = Deferred

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

# Test 12 — Commercial Agreement Call 1 = No Answer

## Expected

- Commercial Agreement Email 1 sent.
- Commercial Agreement Call 2 created.
- Stage remains Commercial Agreement.
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
Stage = Demo Confirmation
```

## Expected

- Demo Booking sequence superseded.
- Pending Demo Booking Call/Email actions marked stale/cancelled/ignored.
- Demo Confirmation sequence starts.
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

---

# Reconciliation Suite (Tests 21-27)

The reconciliation suite verifies three hard rules:

1. **Latest open pipeline position wins over historical/lost position.**
2. **Primary Contact is selected by commercial relevance:** open/farthest-along Deal first, then highest Contact Role.
3. **Deal value = sum of linked Product values.**

## Priority hierarchy (apply in order, no skipping)

```text
1. Open beats closed/lost.
2. Among open Deals, farthest Stage wins.
3. Among same Stage, highest Opportunity rank wins.
4. Among same Stage + Opportunity, highest Contact Role wins.
5. Among same role, most recently updated wins.
6. If still tied, existing primary remains unchanged.
```

## Stage rank

| Stage              | Rank |
| ------------------ | ---: |
| Marketing Qualification  |    1 |
| Demo Booking       |    2 |
| Demo Confirmation        |    3 |
| Demo Hosted      |    4 |
| Commercial Agreement   |    5 |
| Onboarding |    6 |
| Onboarding         |    7 |
| Renewal            |    8 |

## Opportunity rank

| Opportunity | Rank |
| ----------- | ---: |
| MQL         |    1 |
| SQL         |    2 |
| FTP         |    3 |
| RTP         |    4 |

## Contact Role rank

| Contact Role   | Rank |
| -------------- | ---: |
| Decision Maker |    3 |
| Influencer     |    2 |
| End User       |    1 |

The rank tables exist so that ties are resolved deterministically. Closed/lost Deals are filtered out **before** ranking — a Lost RTP Deal never wins over an Open FTP Deal, regardless of rank values, because the "Open beats closed/lost" filter applies first.

---

# Test 21 — Open FTP beats Lost RTP

## Setup

Same Account has two Deals:

```text
Deal A:
  Stage = Renewal
  Opportunity = RTP
  Status = Lost / Closed Lost

Deal B:
  Stage = Commercial Agreement
  Opportunity = FTP
  Status = Open
```

## Expected

- Primary active Deal = Deal B.
- Current Stage = Commercial Agreement.
- Current Opportunity = FTP.
- Sequence initializes from Commercial Agreement.
- Commercial Agreement Call 1 is created.
- No RTP/Renewal sequence starts from the lost Deal.

## Fail if

- Lost RTP Deal is treated as the current active pipeline state.
- Renewal sequence starts.
- Commercial Agreement open Deal is ignored.

---

# Test 22 — Highest Contact Role wins within same active Deal

## Setup

One open Deal has three linked Contacts:

```text
Contact A: End User
Contact B: Influencer
Contact C: Decision Maker
```

## Expected

- Primary Contact = Contact C.
- Contact Role = Decision Maker.
- Deal uses Contact C for primary sales communication where a single contact is required.
- All contacts remain linked to the Deal.

## Fail if

- End User or Influencer becomes primary while Decision Maker exists on the same open Deal.

---

# Test 23 — Farthest-along open Deal contact wins over lower-stage Decision Maker

## Setup

Same Account has two open Deals:

```text
Deal A:
  Stage = Demo Booking
  Opportunity = SQL
  Primary Contact Role = Decision Maker

Deal B:
  Stage = Commercial Agreement
  Opportunity = FTP
  Primary Contact Role = Influencer
```

## Expected

- Primary active Deal = Deal B.
- Current Stage = Commercial Agreement.
- Current Opportunity = FTP.
- Commercial Agreement sequence starts.
- Primary Contact for the active commercial motion = Influencer on Deal B.

## Reason

Farthest-along open Deal wins first. Contact Role is the tie-breaker **within the relevant active Deal context**, not across unrelated/lower-stage Deals.

## Fail if

- System picks the SQL Decision Maker and regresses the active pipeline state.

---

# Test 24 — Same Stage tie uses Contact Role priority

## Setup

Same Account has two open Deals:

```text
Deal A:
  Stage = Commercial Agreement
  Opportunity = FTP
  Primary Contact Role = End User

Deal B:
  Stage = Commercial Agreement
  Opportunity = FTP
  Primary Contact Role = Decision Maker
```

## Expected

- Primary active Deal = Deal B.
- Primary Contact = Decision Maker.

## Fail if

- System picks End User when Decision Maker exists at the same active Stage.

---

# Test 25 — Product sum determines Deal value

## Setup

Three active Products exist:

```text
Product A: Default Deal Value = 1000
Product B: Default Deal Value = 2000
Product C: Default Deal Value = 3000
```

Lead/Product Interest resolves to all three products.

## Expected

- All three Products linked to Deal.
- Products linked to Account if supported/configured.
- Deal Amount = 6000.
- Deal Value Source = Product Derived.
- Product Resolution Status = Resolved.

## Fail if

- Only one Product is linked.
- Deal Amount uses only one Product value.
- Deal Amount is manually overwritten incorrectly.
- Product Resolution Status remains unresolved.

---

# Test 26 — Product values follow the selected active Deal

## Setup

Same Account has:

```text
Lost RTP Deal:
  Products = Product A + Product B
  Amount = 3000

Open FTP Deal:
  Products = Product A + Product B + Product C
  Expected Amount = 6000
```

## Expected

- Primary active Deal = Open FTP Deal.
- Deal Amount = 6000.
- Product-derived value belongs to the open FTP Deal.
- Lost RTP Deal is not used to determine current Deal value.

## Fail if

- Lost RTP Deal amount/products overwrite the active FTP Deal.

---

# Test 27 — New Lead updates existing active Deal instead of creating duplicate

## Setup

Existing Account has open FTP Deal.

New Lead arrives with:

```text
Same company/domain
New Contact
Product interest overlaps existing active Deal
Stage implied = FTP or later
```

## Expected

- New Contact created or reused.
- Contact linked to Account.
- Contact linked to existing open FTP Deal.
- No duplicate Deal created unless explicitly required.
- Primary Contact recalculated using role + active Deal rules.
- Products re-synced.
- Deal Amount recalculated.

## Fail if

- Duplicate Deal created unnecessarily.
- New Contact floats unlinked.
- Deal Amount not recalculated.
