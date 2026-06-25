> [!WARNING]
> **SUPERSEDED — V5 Contact-Centric consolidation.** This document predates the
> Contact-centric refactor and still contains legacy Deal-owned-sequence content
> (e.g. "Deal owns sequence", the legacy `Stage`-suffixed shorthand for the Deal
> Opportunity-Stage field, Email-First/Call-First branches, retired functions/workflows).
> Use `Deal.Opportunity_Stage` / `Deal.Stage` (Opportunity Type) / `Contact.Stage`.
> Authoritative sources:
> `docs/v5/FUNCTION_CONSOLIDATION_MATRIX.md`,
> `docs/v5/WORKFLOW_CONSOLIDATION_MATRIX.md`,
> `docs/v5/FUNCTION_CUTOVER_AND_ROLLBACK.md`,
> `.agents/context/activity-workflows/WORKFLOW_TRIGGER_MAP.md`,
> `.agents/context/activity-workflows/WORKFLOW_CONFIGURATION_CHECKLIST.md`,
> `.agents/context/activity-workflows/SEQUENCE_TRANSITION_MATRIX.md`,
> `.agents/context/activity-workflows/V5_CONTACT_CENTRIC_*.md`.
> Final model: Contact owns sequence state; Deal `Opportunity_Stage` rolls up from
> the Primary Contact via `processDeal`; 24 functions / 17 workflows.

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

`Opportunity_Stage`

Values:

- `Marketing Qualification`
- `Demo Booking`
- `Demo Confirmation`
- `Demo Hosted`
- `Proposal Preparation`
- `Commercial Agreement`
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

- `Commercial Agreement` moves the Deal into `FTP` / `Onboarding`.
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

`Opportunity_Stage` determines `Stage`.

Mapping:

- `Marketing Qualification` → `MQL`
- `Demo Booking` → `SQL`
- `Demo Confirmation` → `SQL`
- `Demo Hosted` → `SQL`
- `Proposal Preparation` → `FTP`
- `Commercial Agreement` → `FTP`
- `Onboarding` → `RTP`
- `Renewal` → `RTP`

Examples:

- `Opportunity_Stage = Demo Confirmation`
- `Stage = SQL`

- `Opportunity_Stage = Commercial Agreement`
- `Stage = FTP`

- `Opportunity_Stage = Onboarding`
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
9. Recalculate Deal `Stage`, `Opportunity_Stage`, `State`, `Status`, primary Contact, and Amount.
10. Roll up Account State / Status.
11. Map Lead `Imported_Record_Type` to `Contacts.Contact_Source_Class` and `Accounts.Account_Source_Class`.
12. Resolve proposed sequence routing mode first: if Deal `Sequence_Status` is empty, determine `Sequence_Action_Mode` and set `Sequence_Status = "Not Started"` before running the sequence router.

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
6. Recalculate Deal `Stage`, `Opportunity_Stage`, `State`, and `Status`.
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
9. Recalculate Deal `Stage`, `Opportunity_Stage`, `State`, and `Status`.
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
8. Recalculate Deal `Stage`, `Opportunity_Stage`, `State`, and `Status`.
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

1. `Marketing Qualification` -> MQL
2. `Demo Booking` -> SQL
3. `Demo Confirmation` -> SQL
4. `Demo Hosted` -> SQL
5. `Proposal Preparation` -> FTP
6. `Commercial Agreement`->FTP
7. `Onboarding` -> RTP
8. `Renewal`-> RTP

The furthest viable open Contact determines:

- Deal primary Contact
- `Deal.Opportunity_Stage`
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
- Role is derived from the Contact's `Job_Title` field using the Jurnii Personas mapping (`resolveContactRole`).
- When a Job Title maps to multiple roles, the most senior role wins: `Decision Maker` > `End User` > `Influencer`.
- If `Job_Title` is blank or has no match in the mapping, fallback role = `Decision Maker`.
- Do not overwrite a manually changed role (skip contacts that already have a role assigned).
- The furthest viable open Contact should also be the Deal primary Contact.
- During Lead conversion, the Lead's `Job_Title` is propagated to the Contact if the Contact's `Job_Title` is blank.

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

## Sequence Routing and Activation Gate

To replace the unconditional Call-first bootstrap (where every stage starts with Call 1), the system implements a task-gated routing sequence.

### Proposed Route Resolution
The canonical sequence action mode is resolved in the following precedence:
1. Deal-level explicit `Sequence_Action_Mode` (if set)
2. Normalized `Contact_Source_Class` from the primary contact
3. Deal-level `Lead_Source` (normalized free-text / picklist)
4. Fallback to `Manual Review First`

Routing Rules:
- `Inbound Form` / `Partner Referral` → `Call First`
- `LinkedIn Prospecting` / Outbound Outreaching → `Email First`
- `Calendar Booking` / Demobooking → `Meeting First`
- `Existing Database` / `Migration` / `Bulk Import` / `Manual Add` / `Unknown` → `Manual Review First`

### Gated Activation Tasks
When the resolved mode is `Manual Review First` or unresolved, sequence automation is gated. The system creates a `Sequence Activation` Task:
- **Subject**: `Activate sequence: {Deal Name} — {Opportunity_Stage}`
- **Task Type**: `Sequence Activation`
- **Blocks Sequence**: `Yes`
- **Deal Sequence Status**: Set to `Waiting on Internal Task`

Selecting `Task_Sequence_Type` transitions the Contact sequence without requiring the rep to update native Task Status:
- `Call` -> executes the call-first route and creates the next Call.
- `Email` -> executes the email-first route, sends Email 1, and creates the follow-up Call.
- `Manual` -> stops automated dispatch and places the Contact under manual management.

After a valid activation choice, automation sets the Activation Task to
`Task_State = Won`, `Task_Status = Closed`, and native `Status = Completed`.
`Task_Outcome` is not a lifecycle command.

### Email-First Cadence Semantics
The `Email First` sequence follows this pattern:
- **Bootstrap**: Sends Stage Email 1 and schedules Call 1 (follow-up, due in 2 business days).
- **Call 1 No Answer/Neutral**: Sends Email 2 and schedules Call 2.
- **Call 2 No Answer/Neutral**: Sends Email 3 and schedules Call 3.
- **Call 3 No Answer/Neutral**: Sends Email 4 and schedules Call 4.
- **Call 4 No Answer/Neutral**: Sends Email 5 and schedules Call 5.
- **Call 5 No Answer/Neutral**: Initiates post-call chase chain. Does not send an Email 6.

### Stage Transitions and Defaults
Stage transitions supersede the old sequence. Standard stage transition defaults are:
- `Proposal Preparation` and `Onboarding` default to `Task First`.
- Other stages default to `Call First`.
On a normal stage transition, the stage-specific default mode is set and the sequence status is reset to `Not Started` to restart routing (without re-gating if it was already activated).

## Final invariant

After any Lead, Contact, Account, or Deal create/update:

- one canonical Account exists
- one active Deal exists for that Account
- all relevant Contacts are linked through `Contact_Roles`
- resolved Products are linked through the Products related list
- furthest viable open Contact is the Deal primary Contact
- `Deal.Opportunity_Stage` reflects the furthest Contact’s Stage
- `Deal.Stage` reflects the correct Opportunity
- `Deal.State` is Open or Lost correctly
- `Deal.Status` is New, Working, or Closed correctly
- lost Contacts do not close the Deal while any Contact remains Open
- duplicate Deals stay closed
