> [!WARNING]
> **SUPERSEDED — V5 Contact-Centric consolidation.** This document predates the
> Contact-centric refactor and still contains legacy Deal-owned-sequence content
> (e.g. "Deal owns sequence", `Opportunity_Stage`, Email-First/Call-First branches, retired
> functions/workflows). Authoritative sources:
> `docs/v5/FUNCTION_CONSOLIDATION_MATRIX.md`,
> `docs/v5/WORKFLOW_CONSOLIDATION_MATRIX.md`,
> `docs/v5/FUNCTION_CUTOVER_AND_ROLLBACK.md`,
> `.agents/context/activity-workflows/WORKFLOW_TRIGGER_MAP.md`,
> `.agents/context/activity-workflows/WORKFLOW_CONFIGURATION_CHECKLIST.md`,
> `.agents/context/activity-workflows/SEQUENCE_TRANSITION_MATRIX.md`,
> `.agents/context/activity-workflows/V5_CONTACT_CENTRIC_*.md`.
> Final model: Contact owns sequence state; Deal `Opportunity_Stage` rolls up from
> the Primary Contact via `processDeal`; 24 functions / 17 workflows.

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
- Marketing Qualification status.
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
- Unit Price (the Zoho Products field that carries the per-product value; spec calls it "Default Deal Value", actual API name is `Unit_Price`).
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

if Stage changed from Active Sequence Stage:
    supersedeOldSequence(deal_id)
    resolve and reset default mode based on Stage (Task First for Proposal Preparation/Onboarding; Call First for others)
    clear paused status and set Sequence Status = Not Started

if Sequence Status in Paused/Manual Only/Suppressed:
    do nothing unless resume date reached

if Sequence Status is empty or Not Started:
    resolve proposed sequence action mode (resolveSequenceRoute)
    if resolved mode is Manual Review First:
        create/reuse Sequence Activation Task, set Sequence Status = Waiting on Internal Task
    if resolved mode is Call First:
        create Call 1, set Sequence Status = Waiting on Call
    if resolved mode is Email First:
        send Email 1, create Call 1 (due in 2 business days), set Sequence Status = Waiting on Call
    if resolved mode is Meeting First:
        set Sequence Status = Waiting on Meeting
    if resolved mode is Task First:
        create/reuse stage-specific task, set Sequence Status = Waiting on Internal Task
```

## Key rule

Sequence activation and routing are task-gated. A stage start creates Call 1, Email 1, a Meeting wait, or a blocking Task depending on the resolved sequence action mode.


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
Commercial Agreement Email 3
Renewal Post-Call Email Chain 7
```

---

# 11. `handleDemoOutcome(deal_id)`

## Purpose

Handle Demo Outcome transitions.

## Rules

```text
Attended - Qualified:
    Stage = Demo Hosted
    send post-demo email
    Commercials Status = Drafting
    create task: Draft Commercials

Attended - Needs Follow-up:
    Stage = Demo Hosted
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
    Stage = Commercial Agreement
    Opportunity = FTP
    Commercial Agreement At = now if empty
    Sequence Status = Not Started
    create Commercial Agreement Call 1
```

```text
Commercials Status = Signed:
    Stage = Onboarding
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

---

# Reconciliation Hierarchy (Mandatory model for resolvers)

The graph processor must NOT simply say "Contact exists → reuse it. Deal exists → reuse it." It must find all relevant Contacts/Deals/Products for an Account or Lead cluster and then choose the active commercial truth based on open state, pipeline rank, and role priority.

Three hard rules drive every resolver:

1. **Latest open pipeline position wins over historical/lost position.**
2. **Primary Contact is selected by commercial relevance:** open/farthest-along Deal first, then highest Contact Role.
3. **Deal value = sum of linked Product values.**

## Priority order (apply top-to-bottom, no skipping)

```text
1. Open beats closed/lost.
2. Among open Deals, farthest Stage wins.
3. Among same Stage, highest Opportunity rank wins.
4. Among same Stage + Opportunity, highest Contact Role wins.
5. Among same role, most recently updated wins.
6. If still tied, existing primary remains unchanged.
```

"Farthest along" is **not absolute** — it is "farthest along among open Deals". A Lost RTP Deal never beats an Open FTP Deal because step 1 filters lost/closed Deals out before steps 2-5 apply.

## Rank tables (used as deterministic tie-breakers)

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

| Opportunity | Rank |
| ----------- | ---: |
| MQL         |    1 |
| SQL         |    2 |
| FTP         |    3 |
| RTP         |    4 |

| Contact Role   | Rank |
| -------------- | ---: |
| Decision Maker |    3 |
| Influencer     |    2 |
| End User       |    1 |

---

# 18. `resolvePrimaryActiveDeal` — primary-active-Deal selection contract

> **Implementation note (Round 7e):** Zoho's `automation.` namespace rejects functions that return `Map` / `List` / `string` — only `void` is accepted. The contract below was originally implemented as `map automation.resolvePrimaryActiveDeal(...)` and could not be published. It is now **inlined** directly into [processLead.deluge §7](../../../v4/processLead.deluge), [processAccount.deluge §3](../../../v4/processAccount.deluge), and [processContact.deluge §5](../../../v4/processContact.deluge). processDeal deliberately does NOT inline this — it operates on its triggered Deal, not the Account's primary. The ranking contract below remains the source of truth; bug fixes must be applied in all 3 inline sites.

## Purpose

Return the single Deal that represents the current active commercial position for an Account / Contact cluster. Used by every graph-layer entry point whenever a new Lead, import, or Deal-affecting edit lands.

## Inputs

```text
account_id           — id of the Account being reconciled
contact_ids          — list of Contact ids relevant to the inbound signal
incoming_stage       — Opportunity_Stage implied by the inbound signal (may be null)
incoming_opportunity — Opportunity implied by the inbound signal (may be null)
```

## Reads

- All Deals related to Account.
- All Deals linked to any Contact in contact_ids.
- Each Deal's: Opportunity_Stage, Stage (Opportunity), State, Status, Modified_Time, linked Contact_Roles.

## Logic

```text
1. Fetch all Deals related to Account and relevant Contacts.
2. Exclude closed/lost/disqualified Deals from active-state selection
   (State == "Lost" OR Status == "Closed" OR Lost_Reasons populated).
3. Rank remaining open Deals by Stage Rank (highest wins).
4. If tied, rank by Opportunity Rank (highest wins).
5. If tied, rank by highest linked Contact Role rank.
6. If tied, rank by Modified_Time (most recent wins).
7. If still tied, retain the existing primary Deal (no change).
8. Return primary active Deal id.
9. If no open Deal exists at all, return null — caller creates a new Deal
   using incoming_stage / incoming_opportunity.
```

## Writes

None. Pure query / scoring function.

## Returns

```text
{
  deal_id: string | null,
  reason: string,              // e.g. "open_ftp_wins_over_lost_rtp"
  rejected: [{deal_id, reason}]
}
```

## Must-not behaviours

- MUST NOT treat a Lost or Closed Deal as the current active pipeline state — even if its Stage Rank is higher.
- MUST NOT regress the active pipeline (e.g., pick an SQL Decision-Maker Deal when an Open FTP Influencer Deal exists for the same Account).
- MUST NOT silently skip step 1 (the open-vs-closed filter) — every downstream rule depends on it.

---

# 19. `resolvePrimaryContactForDeal` — within-Deal primary-Contact contract

> **Implementation note (Round 7e):** Inlined in all 4 process functions ([processLead §10b](../../../v4/processLead.deluge), [processAccount §4b](../../../v4/processAccount.deluge), [processContact §8b](../../../v4/processContact.deluge), [processDeal §5b](../../../v4/processDeal.deluge)) — same Zoho namespace constraint as §18. Bug fixes must be applied in all 4 inline sites.

## Purpose

Return the single Contact that represents the primary commercial interlocutor for an active Deal. Used whenever the Deal's primary needs reconciliation (new Lead arrives, contact role changes, deal advances stage).

## Inputs

```text
deal_id — id of the active Deal
```

## Reads

- All Contacts linked to Deal (via Contact_Roles related list).
- Each Contact's Contact_Role on the Deal.
- Each Contact's contactability fields (Do_Not_Contact_Reason, Email_Opt_Out, Unsubscribed_Mode, Marketing_Consent_Status, Record_Status__s).
- Each Contact's State (soft tie-break).
- Each Contact's Modified_Time (recency tie-break).
- Deal's current Contact_Name (existing primary for "preserve on full tie" rule).

## Logic

```text
1. Hard-EXCLUDE non-contactable Contacts. A Contact is suppressed if ANY of:
     Do_Not_Contact_Reason ∈ {Unsubscribed, Existing Client, Duplicate,
                              Bad Data, Legal/Compliance, Requested No Contact}
     Email_Opt_Out == true
     Unsubscribed_Mode ∈ {Consent form, Manual, Unsubscribe link, Zoho campaigns}
     Marketing_Consent_Status ∈ {Not Consented, Withdrawn}
     Record_Status__s == Trash
   Hard-suppressed Contacts NEVER become primary, regardless of role.
2. Rank remaining Contacts by Contact_Role:
     Decision Maker (3) > Influencer (2) > End User (1).
3. If tied on role rank, prefer Contact.State == "Open" as a SOFT tie-break.
     (A Lost Decision Maker still beats an Open Influencer — state preference
     only matters when role rank is equal.)
4. If tied on role + state, prefer most recently Modified_Time.
5. If tied on role + state + recency AND the existing Deal.Contact_Name passes
   hard suppression, preserve it (no change).
6. Return the resolved primary Contact id.
```

## Writes

Update Deal.Contact_Name to the resolved primary (suppressing the Deal trigger to avoid cascade recursion).

## Returns

```text
{
  contact_id: string,
  contact_role: string,
  changed: boolean             // true if different from previous primary
}
```

## Must-not behaviours

- MUST NOT promote a Contact that fails the hard-suppression check, even at the highest role rank.
- MUST NOT hard-filter by Contact.State alone — State == Open is a soft preference only (Test: a Lost Decision Maker outranks an Open End User on the same Deal).
- MUST NOT promote an End User or Influencer to primary while a non-suppressed Decision Maker exists on the same Deal.
- MUST NOT cross Deal boundaries — the Decision Maker on Deal A cannot be promoted to primary of Deal B. Use resolvePrimaryActiveDeal to pick the right Deal first, then resolve its primary Contact within that Deal's scope only.
- MUST NOT reset the existing primary when a tie-break fails — preserve it (provided it still passes hard suppression).

---

# 20. `syncDealProductsAndValue` — Product link + Amount summation contract

> **Implementation note (Round 7e):** Inlined in all 4 process functions ([processLead §12a-bis](../../../v4/processLead.deluge), [processAccount §5a-bis](../../../v4/processAccount.deluge), [processContact §9a-bis](../../../v4/processContact.deluge), [processDeal §6a-bis](../../../v4/processDeal.deluge)) — same Zoho namespace constraint as §18. Bug fixes must be applied in all 4 inline sites.

## Purpose

Recompute Deal Amount from linked Products and stamp the value-source flags. Runs whenever Products change on the Deal or whenever a process function lands a fresh Product_Interest signal.

## Inputs

```text
deal_id — id of the Deal to recompute
```

## Reads

- All Product_Interest tokens / values from the source signal (if called from upsertDeal).
- All Products linked to Deal via Product_Details subform.
- Each Product's `Unit_Price` (the actual Zoho field — spec wording "Default Deal Value" maps to this).
- Account.Account_Products linked list (where supported/configured).

## Logic

```text
1. Resolve ALL product interests from the source signal, not just the
   first match (e.g., "Product A; Product B" → both resolved).
2. Link every resolved Product to the Deal (Product_Details subform).
3. Link Products to Account where supported/configured.
4. Read `Unit_Price` from each linked Product (spec wording "Default Deal Value" → actual field `Products.Unit_Price`).
5. Sum the values: `deal_amount = SUM(Unit_Price of all linked Products)`.
6. Write deal_amount to Deal.Amount.
7. Set Deal.Deal_Value_Source = "Product Derived".
8. Set Deal.Product_Resolution_Status = "Resolved".
```

## Writes

- Deal.Product_Details (subform, all resolved Products)
- Deal.Amount
- Deal.Deal_Value_Source = "Product Derived"
- Deal.Product_Resolution_Status = "Resolved"
- Account.Account_Products (if supported)

## Returns

```text
{
  product_ids: [string],
  deal_amount: number,
  resolution_status: "Resolved" | "Manual Review" | "Missing Product Interest" | "Failed",
  changed: boolean
}
```

## Resolution status mapping

Maps to the `Deals.Product_Resolution_Status` picklist (verified picklist values: -None-, Not Started, Resolved, Missing Product Interest, Failed, Manual Review, No Active Product Match):

| Condition                                                            | Status                     |
| -------------------------------------------------------------------- | -------------------------- |
| Every linked Product has a non-null `Unit_Price`                     | `Resolved`                 |
| Some linked Products have values, some do not                        | `Manual Review`            |
| No Products were linked at all                                       | `Missing Product Interest` |
| Products were linked but all failed to load or had no value          | `Failed`                   |

## Must-not behaviours

- MUST NOT stop at the first matched Product when multiple are signalled — link all of them.
- MUST NOT use a single Product's value when multiple are linked — the Amount is always the SUM.
- MUST NOT overwrite Deal.Amount with a manual / stale value when called as part of a Lead reconciliation flow — Product-derived value wins.
- MUST NOT carry value from a Lost/Closed Deal into the active Deal — value belongs to the resolved primary active Deal only (see Test 26). The resolver skips Lost/Closed Deals via the State/Status guard.
- MUST NOT leave Product_Resolution_Status as `Missing Product Interest` or `Failed` when all linked Products resolved successfully.
