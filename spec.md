# CRM CRUD Convergence Spec

## Core rule

Any Lead, Contact, Account, or Deal create/update must correct the same CRM structure:

- one canonical Account
- many Contacts under that Account
- one active Deal for that Account
- all relevant Contacts linked to the Deal through Contact_Roles
- resolved Products linked to the Deal through the Products related list
- Deal Opportunity, Stage, State, and Status set correctly
- Account State and Status rolled up correctly

The workflow trigger decides when processing runs.

The processor must make the Account, Contacts, Deal, Contact_Roles, and Products correct.

---

## Opportunity, Stage, State, and Status

### Opportunity

API field:

`Stage`

Values:

- `MQL`
- `SQL`
- `FTP`
- `RTP`

This is the pipeline bucket.

### Stage

API field:

`Stage1`

Values:

- `Marketing Consent`
- `Demo Booking`
- `Demo Booked`
- `Demo Attended`
- `Commercials Sent`
- `Commercials Signed`
- `Onboarding`
- `Renewal`

This is the current commercial step.

### State

API field:

`State`

Values:

- `Open`
- `Lost`

Rules:

- `Open` means the commercial motion is still active.
- `Lost` means the commercial motion is closed unsuccessfully.
- Do not use `Won` as a persistent State.

`Won` is a gate event, not a durable state. When a gate is passed, the Deal moves forward into the next commercial motion instead of being closed as Won.

Example:

- `Commercials Signed` moves the Deal into `RTP` / `Onboarding`.
- It does not close the Deal as `Won`.

### Status

API field:

`Status`

Values:

- `New`
- `Working`
- `Closed`

Rules:

- `New` = active record with no meaningful manual activity.
- `Working` = active record with meaningful manual activity.
- `Closed` = only when `State = Lost`.

Automated workflow emails do not make a record `Working`.

---

## Stage to Opportunity mapping

`Stage1` determines `Stage`.

Mapping:

- `Marketing Consent` → `MQL`
- `Demo Booking` → `SQL`
- `Demo Booked` → `SQL`
- `Demo Attended` → `SQL`
- `Commercials Sent` → `FTP`
- `Commercials Signed` → `RTP`
- `Onboarding` → `RTP`
- `Renewal` → `RTP`

Examples:

- `Stage1 = Demo Booked`
- `Stage = SQL`

- `Stage1 = Commercials Sent`
- `Stage = FTP`

- `Stage1 = Onboarding`
- `Stage = RTP`

---

## Lead create/update

When a Lead is created or updated:

1. Convert the Lead where possible.
2. Resolve or create the canonical Account.
3. Resolve or create the Contact.
4. Link the Contact to the canonical Account.
5. Resolve or create the Account’s one active Deal.
6. Add the Contact to the Deal through `Contact_Roles`.
7. Merge Product Interest into the Deal.
8. Resolve Products and attach them through the Products related list.
9. Recalculate Deal `Stage`, `Stage1`, `State`, `Status`, primary Contact, and Amount.
10. Roll up Account `State` and `Status`.

All Leads should convert where possible.

Missing enrichment data should not block conversion.

---

## Contact create/update

When a Contact is created or updated:

1. Ensure the Contact belongs to the canonical Account.
2. Ensure the Account has one active Deal.
3. Add or update the Contact in `Contact_Roles` on the Deal.
4. Recalculate the furthest viable Contact.
5. Set the Deal primary Contact.
6. Recalculate Deal `Stage`, `Stage1`, `State`, and `Status`.
7. Recalculate Product mapping and Deal Amount.
8. Roll up Account `State` and `Status`.

---

## Account create/update

When an Account is created or updated:

1. Ensure this is the canonical Account.
2. Gather Contacts under the Account.
3. Gather Deals under the Account.
4. Keep one active Deal.
5. Silence duplicate active Deals.
6. Ensure all relevant Contacts are linked through `Contact_Roles`.
7. Recalculate the furthest viable Contact.
8. Set the Deal primary Contact.
9. Recalculate Deal `Stage`, `Stage1`, `State`, and `Status`.
10. Recalculate Product mapping and Deal Amount.
11. Roll up Account `State` and `Status`.

---

## Deal create/update

When a Deal is created or updated:

1. If the Deal is marked duplicate, do not revive it.
2. Ensure the Deal belongs to the canonical Account.
3. Ensure this is the Account’s one active Deal.
4. Silence duplicate active Deals.
5. Ensure all relevant Contacts are linked through `Contact_Roles`.
6. Recalculate the furthest viable Contact.
7. Set the Deal primary Contact.
8. Recalculate Deal `Stage`, `Stage1`, `State`, and `Status`.
9. Recalculate Product mapping and Deal Amount.
10. Roll up Account `State` and `Status`.

---

## One Account rule

There should be one canonical Account per real company.

All Contacts and the active Deal should point to that Account.

Duplicate Accounts should not be used as the working Account.

---

## One active Deal rule

There should be one active Deal per Account.

The active Deal represents the Account’s current commercial motion.

Do not create:

- one Deal per Lead
- one Deal per Contact
- one Deal per Product

---

## Furthest Contact rule

The Deal stage comes from the furthest viable open Contact under the Account.

Rank:

1. `Marketing Consent`
2. `Demo Booking`
3. `Demo Booked`
4. `Demo Attended`
5. `Commercials Sent`
6. `Commercials Signed`
7. `Onboarding`
8. `Renewal`

The furthest viable open Contact determines:

- Deal primary Contact
- `Deal.Stage1`
- `Deal.Stage`

If two open Contacts are at the same furthest Stage, keep the existing primary Contact unless it is blank.

---

## Lost Contact handling

A lost Contact does not close the Deal if another Contact under the Account is still open.

Rules:

- If at least one Contact under the Account is Open, the Deal remains Open.
- Lost Contacts do not pull the Deal backward.
- Lost Contacts do not become primary while an Open Contact exists.
- The Deal closes only when all relevant Contacts under the Account are Lost, or the Deal itself has an explicit Deal-level loss reason.

When the Deal closes:

- `State = Lost`
- `Status = Closed`

---

## Duplicate Deal handling

If multiple active Deals exist for the same Account:

- keep the oldest / lowest-ID Deal as canonical
- mark all other active Deals as duplicate

Duplicate Deal values:

- `State = Lost`
- `Status = Closed`
- `Reason_For_Loss = Duplicate / Test Record`
- clear the Deal identity key
- append `(Duplicate)` to the Deal name

Duplicate Deals must not be revived.

---

## Contact_Roles related list

The canonical Deal must include all relevant Account Contacts in `Contact_Roles`.

Rules:

- Add each relevant Account Contact to the canonical Deal.
- Default role = `Decision Maker`.
- Do not overwrite a manually changed role.
- The furthest viable open Contact should also be the Deal primary Contact.

---

## Products related list

Product Interest is staging input.

The canonical Deal’s product set is the deduped union of:

- current triggering record Product Interest
- all Contact Product Interest staging under the Account
- existing Deal Product Interest staging

For each product name:

1. Search Products by `Product_Name`.
2. Attach the resolved Product to the Deal through the Products related list.
3. Sum resolved Product `Unit_Price`.
4. Write the total to `Deal.Amount`.

Missing Product matches should not block the workflow.

---

## Final invariant

After any Lead, Contact, Account, or Deal create/update:

- one canonical Account exists
- one active Deal exists for that Account
- all relevant Contacts are linked through `Contact_Roles`
- resolved Products are linked through the Products related list
- furthest viable open Contact is the Deal primary Contact
- `Deal.Stage1` reflects the furthest Contact’s Stage
- `Deal.Stage` reflects the correct Opportunity
- `Deal.State` is Open or Lost correctly
- `Deal.Status` is New, Working, or Closed correctly
- lost Contacts do not close the Deal while any Contact remains Open
- duplicate Deals stay closed