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

# MCP Test Harness — Prompt for a Claude Code session

> Paste this file's contents to a fresh Claude Code session in the
> `zoho-functions` repo to drive an iterative test-and-fix cycle for the
> activity-workflows execution pack, using the Zoho MCP tools.

---

## Mission

You are running the **MCP test harness** for the activity-workflows
execution pack. Your job is, in this order:

1. Use the Zoho MCP tools to **exercise the live workflow rules** in the
   user's org (sandbox or current — confirm in §0).
2. After each test, read the resulting record state back through the
   MCP and **assert** the expected outcome.
3. When a test fails, locate the offending Deluge function or workflow
   rule, **propose a surgical fix**, write the fix to disk, **stop**,
   and tell the user exactly which function(s) to republish in Zoho
   before the next round.
4. After the user confirms they have republished, **resume from the
   failed test**, not from the start.

You are not testing email-event triggers (WF009a–e) or date-based
triggers (WF010) — those need real emails or wall-clock waits and are
out of scope for this harness. See §10.

---

## How to operate

### Iteration loop

```text
SETUP (once per session) → run tests in order →
  PASS → next test
  FAIL → diagnose → propose fix → write fix to file → STOP and ask the
         user to republish the affected function(s) → on user resume,
         re-run the failed test from the same setup
END → cleanup test records → write a summary
```

### Republish handoff

When you write a Deluge fix, end your turn with a clear, copy-pasteable
republish instruction:

> **Republish required.** Open Zoho → Setup → Functions and republish
> the following functions before saying "continue":
> - `<function_name_1>`
> - `<function_name_2>`
> Then reply with `continue` and I will resume from test `T<n>`.

Do not proceed to the next test until the user says `continue`.

### Where to record findings

Append every test result, root cause, and proposed fix to:

```text
.agents/context/activity-workflows/MCP_TEST_RUN_LOG.md
```

Create the file if it doesn't exist. One section per round. Format
each entry as:

```text
## Round <N> — <YYYY-MM-DD HH:MM>
### T<n> — <short name>
- Status: PASS | FAIL
- Action taken: <one-line summary of the MCP mutation>
- Observed: <what came back from the read assertions>
- Expected: <what should have come back>
- Root cause (if FAIL): <function/file:line>
- Fix written: <file paths edited, or "no fix needed">
```

This file is the audit trail across republish rounds.

### Pacing

Workflow rules in Zoho don't execute instantaneously. After every
mutation that should trigger a workflow, **wait at least 30 seconds**
before reading state back. If a read assertion fails on first attempt,
retry once after another 30 seconds before declaring FAIL.

---

## §0 — Setup (once per session)

Before running any test:

1. Confirm MCP servers are reachable. Call
   `mcp__zoho-crm-module-customisation__ZohoCRM_getModules` with no
   filters and confirm at least Deals, Contacts, Accounts, Leads,
   Calls, Events, Tasks, Emails are returned.

2. Confirm the WF002, WF003, WF004, WF005, WF006, WF007, WF008 rules
   are **active** in this org:
   ```
   mcp__zoho-crm-automation__ZohoCRM_getWorkflowRules
     query_params: { module: "Deals", status_active: true }
   ```
   Repeat for `Calls`, `Events`, `Tasks`. Match by `name` containing
   `WF002`, `WF003`, etc. If any expected rule is missing or inactive,
   STOP and tell the user.

3. Read the **module IDs** for Deals, Contacts, Accounts, Leads, Calls,
   Events, Tasks once and cache them in conversation memory. You will
   reuse them throughout.

4. Generate a session prefix for test records:
   ```text
   sessionPrefix = "MCP_TEST_" + <YYYYMMDD_HHMM>
   ```
   Every Deal/Contact/Account/Lead/Call/Task/Event you create during
   tests must have this prefix in `Deal_Name` / `Last_Name` /
   `Account_Name` / `Subject`, so the cleanup step in §9 can find and
   delete them.

5. Confirm with the user this is a sandbox or a CRM where it's safe to
   create and delete records. If they say no, STOP.

6. Ask the user for **one existing test Account ID** and **one existing
   test Contact ID** they're OK with being touched by tests (some tests
   need a related Deal owner). If they decline, you'll create new ones
   per test.

---

## §1 — Tools you will use

Constantly:
- `mcp__zoho-crm-data-operations__ZohoCRM_createRecords`
- `mcp__zoho-crm-data-operations__ZohoCRM_updateRecords`
- `mcp__zoho-crm-data-operations__ZohoCRM_getRecords` (read-back)
- `mcp__zoho-crm-data-operations__ZohoCRM_getRelatedRecords` (to read
  Calls/Tasks/Events created against a Deal)
- `mcp__zoho-crm-data-operations__ZohoCRM_deleteRecords` (cleanup only)

Occasionally:
- `mcp__zoho-crm-automation__ZohoCRM_getWorkflowRules` (debug a failing
  test — confirm the rule fired by checking `last_executed_time`)
- `mcp__zoho-crm-module-customisation__ZohoCRM_getFields` (verify a
  picklist value exists before writing it)

**What you cannot do via MCP:** read Zoho's Function Execution Log.
Treat the function execution as a black box; assert only on observable
record state.

---

## §2 — Test plan

The test plan runs in two sections, in order:

- **§2A — Core graph layer** (`v5/processLead.deluge`,
  `v5/processContact.deluge`, `v5/processAccount.deluge`,
  `v5/processDeal.deluge`). These are foundational and MUST pass before
  the activity layer can be trusted. The four `processX` functions own:
  Lead → Contact/Account/Deal conversion; Account_Key generation;
  Contact-Role assignment from Job_Title; Product attachment + Amount;
  duplicate detection and silencing; Account State/Status rollup; and
  the hook line `automation.sequenceRouter(canonicalDealId.toLong())`
  that bridges to the activity layer.
- **§2B — Activity layer** (`v5/activity/*.deluge`).
  `sequenceRouter`, `createStageCall`, the outcome handlers, etc.

Run §2A in full before §2B. A failing graph-layer test usually masks
or invalidates downstream activity-layer tests.

Use a fresh `sessionPrefix + "_T<n>"` for each test's records.

### E2E Completion Rule

The harness MUST NOT report a "full end-to-end PASS" unless a single test execution session successfully creates, links, updates, and verifies records in all of the following modules:
1. **Lead** (which successfully converts to Contact + Account + Deal)
2. **Contact** (with correct Job-Title-to-Role assignment and suppression attributes)
3. **Account** (with proper State and Status rollups)
4. **Deal** (with correctly populated Product details, summed Amount, Opportunity_Stage/Stage, and active sequence state)
5. **Call** (with correct attempt progression, stale flagging, outcome handling, and polymorphic What_Id/Who_Id linkage)
6. **Task** (with correct creation for drafting commercials/bad data/manual reviews, proper polymorphic linkage, and verified completion handler execution)
7. **Event / Meeting** (with correct reminder generation, reschedule, and cancellation/no-show recovery handling)

For every generated activity (Call, Task, Event/Meeting), the following invariants must be verified:
- **Direct Read**: Retrieve the record directly from its module using `getRecords` or `getRecordById`.
- **Deal Related List Read**: Retrieve the activity from the related list on the Deal (`getRelatedRecords`).
- **Contact Related List Read**: Retrieve the activity from the related list on the Contact (`Who_Id` linkage).
- **Polymorphic Linkage**: Confirm `What_Id` holds the Deal ID and `$se_module` is set to `"Deals"`. Confirm `Who_Id` holds the primary Contact ID.
- **Ownership**: The activity record owner must match the Deal's owner.
- **Sequence Fields**: Verify fields like `Sequence_Managed = Yes`, `Task_Type` or `Sequence_Stage`, `Sequence_Attempt` match expected values.
- **Deduplication**: Assert no duplicate equivalent activity exists.
- **Lifecycle Mutation**: Assert correct handler execution after updating or completing the record (e.g. WF008 executes on Task completion, WF007 executes on Event update).

Any skipped or deferred Call, Task, or Event test prevents the session from being marked as **full end-to-end**.

---

## §2A — Core graph layer

### T1 — `processLead` end-to-end conversion

**What this tests:** WF001 fires `processLead` on Lead create_or_edit.
The function should create or link a Contact, an Account, and a Deal,
then call the activity-layer hook so Opportunity_Stage = Marketing Qualification on the
new Deal triggers WF002 → sequenceRouter → Call 1.

**Action:** create a Lead via `createRecords` on Leads with:
```
Last_Name              = <sessionPrefix>_T1_Last
First_Name             = MCPTest
Email                  = mcp_t1_<timestamp>@example.com
Phone                  = +44 7000 000001
Company                = <sessionPrefix>_T1_Co
Title                  = "Head of Marketing"
Lead_Source            = "Inbound Form"
Lead_Processing_Status = "Not Started"
Ready_for_Conversion   = true
```
Wait 60s — Lead pipeline is heavier than Deal-only.

**Assertions:**
- A **Contact** exists with `Email` matching the Lead's email.
  - `Account_Name` lookup points at the Account created/linked below.
- An **Account** exists whose `Account_Name` was derived from the
  Lead's `Company` and whose `Account_Key` is non-empty.
- A **Deal** exists with:
  - `Account_Name` = the new Account
  - `Contact_Name` = the new Contact
  - `Opportunity_Stage` = `Marketing Qualification`
  - `State` = `Open`
  - `Deal_Key` is non-empty and ends with `::active`
- The Lead's `Lead_Processing_Status` reflects completion (e.g.
  `Converted` or `Done`).
- The Deal's **Contact_Roles** related list contains the Contact with
  the role derived from `Title`. For `Head of Marketing` the role
  should be **Decision Maker** (per the title → role lists in
  `processAccount.deluge` ~lines 37-40 and `_util_resolveRoleFromTitle.deluge`).
- The hook to `sequenceRouter` fired: within ~30s after Deal creation,
  the Deal's `Sequence_Status` = `Waiting on Call` and a related Call
  with `Subject` = `Marketing Qualification Call 1` exists.

**On failure:**
- `v5/processLead.deluge` — full pipeline.
- Check the Lead's logs for `info` lines indicating which step
  early-returned (Contact lookup vs Account resolution vs Deal create).
- If Deal exists but no `Marketing Qualification Call 1`: the hook at
  `v5/processLead.deluge:898` may have failed to fire — check the
  `if(canonicalDealId != "" && State == "Open")` guard.

### T2 — `processLead` idempotency

**Depends on T1's Lead.**

**Action:** Update the T1 Lead with a no-op edit (e.g. set
`Phone = "+44 7000 000001 "` then back to the original). Each edit
re-fires WF001. Wait 60s.

**Assertions:**
- No second Contact, Account, or Deal was created.
- The Deal's `Sequence_Status` did not regress (still
  `Waiting on Call` if T1's Call 1 hasn't been mutated yet).
- The original Call 1 still exists; no `Marketing Qualification Call 1`
  duplicate appeared.

**On failure:**
- `v5/processLead.deluge` — duplicate check against existing Contact
  by Email and existing Account by Account_Key.
- `v5/activity/createStageCall.deluge` — the Call duplicate-prevention
  search.

### T3 — `processContact` standalone Contact creates an Account and a Deal

**What this tests:** WF (Contacts/create_or_edit) fires `processContact`
on a Contact that wasn't created via Lead conversion. The function
should create or link an Account (by Email domain or explicit linkage)
and ensure an open Deal exists for that Account.

**Action:** `createRecords` on Contacts with:
```
Last_Name      = <sessionPrefix>_T3_Last
First_Name     = MCPTest
Email          = mcp_t3_<timestamp>@example.com
Title          = "Product Manager"
Contact_Source_Class = "Inbound Form"
Account_Name   = (leave empty so processContact must resolve/create)
```
Wait 45s.

**Assertions:**
- The Contact's `Account_Name` lookup is now populated.
- An Account exists, with a non-empty `Account_Key`.
- A Deal exists under that Account with `Opportunity_Stage` = `Marketing Qualification`,
  `State` = `Open`.
- The Deal's `Contact_Roles` related list contains this Contact with
  role **End User** (per the `euTitles` list — `Product Manager` is
  classified End User).
- The hook fired: `Sequence_Status` = `Waiting on Call` on the new
  Deal, related Call `Marketing Qualification Call 1` exists.

**On failure:**
- `v5/processContact.deluge` — Account resolution path, role
  assignment, hook line `~712`.

### T4 — `processContact` role precedence: End User > Influencer > Decision Maker

**What this tests:** the role precedence rule documented in
`processAccount.deluge` and `_util_resolveRoleFromTitle.deluge`.

**Action:** create three Contacts under a single existing Account
(use the test Account from §0 or create one in T3):
```
Contact A: Title = "Head of Marketing"          → Decision Maker
Contact B: Title = "Product Manager"            → End User
Contact C: Title = "Marketing Manager"          → Influencer
```
Wait 45s.

**Assertions:**
- Each Contact appears in the Account's open Deal's `Contact_Roles`
  with the matching role.
- If two Contacts have ambiguous titles, the precedence rule applies
  (End User wins over Influencer wins over Decision Maker default).

**On failure:**
- `v5/processContact.deluge` and `v5/activity/_util_resolveRoleFromTitle.deluge`.
- Check the title is in the right title list (`dmTitles`, `euTitles`,
  `infTitles`) — these are duplicated in `processAccount.deluge` ~37-40
  and `processLead.deluge`/`processContact.deluge`.

### T5 — `processDeal` ignores "(Duplicate)" suffix Deals

**What this tests:** a Deal with `Deal_Name` ending in `(Duplicate)`
or `Reason_For_Loss__s` = `Duplicate / Test Record` is a recovery
sentinel that automation must not revive.

**Action:** create a Deal directly via `createRecords` with:
```
Deal_Name              = <sessionPrefix>_T5 (Duplicate)
Account_Name           = <test account id>
Contact_Name           = <test contact id>
Opportunity_Stage                 = "Marketing Qualification"
State                  = "Open"
Reason_For_Loss__s     = "Duplicate / Test Record"
Closing_Date           = <today + 60>
```
Wait 30s.

**Assertions:**
- The Deal exists but its `Opportunity_Stage`, `State`, `Sequence_Status` were
  NOT mutated by automation.
- No `Marketing Qualification Call 1` was created against this Deal.
- The Deal's `Sequence_Status` is still its initial value (empty or
  whatever was set on create).

**On failure:**
- `v5/processDeal.deluge` — the early-exit branch (~`if dealName ends
  with "(Duplicate)" or reasonForLoss == "Duplicate / Test Record"
  return;`, around line 44-48 of `processDeal.deluge`).

### T6 — `processDeal` silences duplicate active Deals under one Account

**What this tests:** two open Deals under the same Account should not
co-exist. The newer one wins; the older one is silenced to
`State = Lost`, `Status = Closed`,
`Reason_For_Loss__s = "Duplicate / Test Record"`. The canonical Deal
keeps a non-empty `Deal_Key`.

**Action:**
1. Create Deal A under `<test account id>`:
   `Deal_Name = <sessionPrefix>_T6_A`, `Opportunity_Stage = Marketing Qualification`,
   `State = Open`.
2. Wait 45s. Assert Deal A is the canonical one (Call 1 exists).
3. Create Deal B under the same Account:
   `Deal_Name = <sessionPrefix>_T6_B`, `Opportunity_Stage = Marketing Qualification`,
   `State = Open`.
4. Wait 45s.

**Assertions (after step 4):**
- Exactly **one** Deal under the Account has `State = Open`.
- The other Deal has `State = Lost`, `Status = Closed`,
  `Reason_For_Loss__s = "Duplicate / Test Record"`.
- The losing Deal does NOT have a fresh `Call 1` related to it.
- The canonical Deal's `Sequence_Status` is still active.

**On failure:**
- `v5/processDeal.deluge` — duplicate Deal silence loop (~ section 3,
  "Silence duplicate active Deals + identify canonical").
- `v5/processAccount.deluge` and `v5/processContact.deluge` — same
  dedup pattern (~lines 200, 686).

### T7 — `processDeal` Product attachment + total `Amount` sum across multiple Products

**What this tests:** when Contacts under the Account express Product
Interest in **two or more** Products, `processDeal` resolves them by
name, writes them all to the Deal's `Product_Details` subform, and
sums per-line `Unit_Price × Quantity` (with Discount and Tax) into the
Deal's `Amount`. The total is the load-bearing field that downstream
forecasting relies on, so this test must exercise the sum across
multiple products — a single-product check would pass even with broken
aggregation.

**Pre-flight:** Products module needs at least **2 active Products**
with known, distinct `Unit_Price` values. Read them via `getRecords`
on Products. Record their IDs, `Product_Name`, and `Unit_Price` for
the assertion below. If fewer than 2 exist, SKIP and log.

Let `P1 = (name1, price1)`, `P2 = (name2, price2)`, `expectedSum =
price1 + price2` (assume Quantity = 1 each, no Discount/Tax for the
baseline). Adjust expectedSum if your test products have non-zero
Discount/Tax defaults.

**Action:**
1. Create a Contact `<sessionPrefix>_T7_C` with `Account_Name` =
   `<test account id>`, `Title = "Head of Marketing"`, and set the
   Contact's product-interest field to **both** product names
   (`P1.name` and `P2.name`).
2. Wait 45s.

**Assertions on the Account's canonical Deal:**
- `Product_Details` subform contains exactly **2 rows**, one per
  product. The product IDs match `P1.id` and `P2.id`.
- Each row has populated `Discount`, `Tax`, `total`, `net_total` (per
  commit `f2812cc`).
- The Deal's `Amount` equals `expectedSum` (within £0.01 / $0.01
  rounding tolerance). Bug pattern to watch for: `Amount` =
  `price1` only (last write wins) or `Amount` = `price1 × 2` (no
  per-line distinction) — both indicate aggregation broke.
- If `Currency` (or `Currency_Symbol`) is set on the Deal, the rate
  matches expectations (multi-currency is out of scope but should not
  silently corrupt the sum).

**Then add a third product to stress aggregation:**
3. Update the Contact's product-interest to include `P3` as well
   (pick or create a third active Product). Wait 30s.
- Assert `Product_Details` now has 3 rows and `Amount` =
  `price1 + price2 + price3`.

**On failure:**
- `v5/processDeal.deluge` — Product resolution + subform write
  (~step 6, "Resolve Products by name, attach to Deal Products related
  list, sum Unit_Price into Deal.Amount").
- Check recent commits (`git log --oneline v5/processDeal.deluge`) —
  this code path was changed in `f2812cc`, `35e432d`, and `ca65f5a`.
  Bug `ca65f5a` specifically fixed "amount inflation" from cascading
  workflow triggers, so failures here may also indicate a
  triggerMap regression.

### T9 — `processDeal` links multiple Contacts via `Contact_Roles` related list

**What this tests:** a Deal under an Account with multiple Contacts
must end up with **all** Contacts attached to the Deal via the
`Contact_Roles` related list, each with the correct role derived from
`Title`. `Contact_Name` (the primary single-Contact lookup) holds one
deterministic Contact (typically the canonical or first-Decision-Maker
Contact); the rest live in `Contact_Roles`.

**Action:**
1. Pick or create a fresh Account `<sessionPrefix>_T9_Acc`.
2. Under it, create three Contacts (in this order):
   - Contact A: `Title = "Head of Marketing"`, `State = Open` →
     expected role **Decision Maker**.
   - Contact B: `Title = "Product Manager"`, `State = Open` →
     expected role **End User**.
   - Contact C: `Title = "Marketing Manager"`, `State = Open` →
     expected role **Influencer**.
3. After each Contact, wait 30s for `processContact` to run.

**Assertions on the Account's canonical Deal:**
- `Contact_Roles` related list has **exactly 3 entries**, one per
  Contact, each with the matching role.
- `Contact_Name` (primary single-Contact lookup) is set to a
  deterministic value — confirm which one by reading and noting it
  the first time (most likely the Decision Maker, Contact A).
- Reading each Contact back individually, `Account_Name` lookup
  points at the test Account on all three.
- Reading the Account's related Contacts via `getRelatedRecords`
  returns all 3.

**Now mutate to test idempotency + role precedence:**
4. Update Contact B's `Title` from `"Product Manager"` to
   `"Senior Product Manager"` (still classified End User per
   `euTitles`). Wait 30s.
- Assert `Contact_Roles` still has 3 entries; B is still End User; A
  and C are unchanged.
5. Update Contact A's `Title` to `"Product Manager"` (now End User,
   conflicts with B). Wait 30s.
- Assert: role precedence rule (End User > Influencer > Decision
  Maker) is applied per Contact; A is now End User; B is still End
  User; C unchanged. The Deal's `Contact_Name` primary may or may
  not flip — note actual behavior for the run log.

**On failure:**
- `v5/processContact.deluge` — Contact_Roles maintenance loop
  (~lines 230-280 in v3; the equivalent block in v5).
- `v5/processDeal.deluge` — step 5 in processDeal's pipeline:
  "Maintain Contact_Roles related list (Decision Maker default,
  never overwrite a manual role)".
- `v5/activity/_util_resolveRoleFromTitle.deluge` — title-list
  membership.

### T10 — Deal Opportunity (`Stage`) follows the furthest **non-closed** Contact

**What this tests:** when multiple Contacts are linked to a Deal, the
Deal's `Opportunity_Stage` and derived `Stage` (Opportunity bucket: MQL / SQL /
FTP / RTP) reflect the **furthest-along Contact that is still Open**.
If the furthest Contact is closed (`State = Lost` or equivalent), the
Deal must fall back to the next-furthest **Open** Contact, not stay
stuck at the closed Contact's progress.

**Setup:** Use the T9 Account if available, or create a fresh Account
`<sessionPrefix>_T10_Acc`. The Account should currently have a
canonical Deal under it (created by T9 or a fresh `processX` run).
Establish a starting baseline:
1. Set Contact A's "progress hints" so processDeal computes the
   Deal at, say, `Opportunity_Stage = Demo Hosted` (`Stage` = `SQL`).
2. Set Contact B at `Opportunity_Stage = Commercial Agreement` (`Stage` = `FTP`) —
   B is "furthest" so the Deal should reflect FTP.
3. Wait 45s.

> Exact mechanic: the way each Contact's progress is captured varies
> between v3 and v5. Read `v5/processDeal.deluge` step 4 ("compute
> furthest viable open") and `v5/processContact.deluge` to identify
> whether progress is held on the Contact directly (e.g. a
> `Contact_Stage` field), inferred from related Calls/Tasks, or
> derived from the Account's history. Adapt the setup accordingly.
> If the field model doesn't support per-Contact stage progression,
> log this in the run log as a coverage gap and skip the test.

**Phase A — baseline:**
- Assert Deal `Opportunity_Stage` = `Commercial Agreement`, `Stage` = `FTP`
  (Contact B's progress wins because B is Open and furthest).

**Phase B — close the furthest Contact:**
- Update Contact B's `State` to `Lost`. Wait 30s.

**Assertions:**
- Deal `Opportunity_Stage` reverts to `Demo Hosted`, `Stage` = `SQL` —
  Contact A's progress now wins because A is the furthest Open
  Contact.
- Deal `State` stays `Open` (still has at least one open Contact).
- The Deal does **not** stay at FTP just because Contact B was
  there at some point — the recompute must drop closed Contacts.

**Phase C — revive Contact B:**
- Update Contact B's `State` back to `Open`. Wait 30s.
- Assert Deal `Opportunity_Stage` returns to `Commercial Agreement`, `Stage` =
  `FTP`.

**Phase D — close all Contacts:**
- Set both A and B to `State = Lost`. Wait 30s.
- Assert Deal `State` = `Lost`, `Status` = `Closed`. (If no Open
  Contact remains, the Deal itself should close — confirm against
  spec.)

**On failure:**
- `v5/processDeal.deluge` — step 4 ("Gather Contacts under the
  Account, compute furthest viable open"). The bug pattern is
  "furthest ever" instead of "furthest currently open".
- `v5/processContact.deluge` — Contact.State change should re-fire
  `processDeal` (directly or via the Account rollup hook).
- `v5/processAccount.deluge` — Account rollup must propagate the
  Contact-state change to the Deal.

### T8 — `processAccount` State/Status rollup

**What this tests:** when Deals under an Account change State, the
Account's own State/Status is recomputed:
- Account `State = Open` if any related Deal has `State = Open`.
- Account `State = Lost` only when ALL related Deals are `Lost`.
- Account `Status = Closed` only when `State = Lost`.

**Setup:**
1. Use an existing test Account or create a new one
   `<sessionPrefix>_T8_Acc`.
2. Under it, create two Deals: `<sessionPrefix>_T8_D1` (Open) and
   `<sessionPrefix>_T8_D2` (Open). Wait 45s.

**Phase A — mixed:** Set Deal D1 to `State = Lost`. Wait 30s.
- Assert Account `State = Open` (D2 is still Open).

**Phase B — all Lost:** Set Deal D2 to `State = Lost`. Wait 30s.
- Assert Account `State = Lost`, `Status = Closed`.

**Phase C — revive:** Update Deal D1 back to `State = Open`. Wait 30s.
- Assert Account `State = Open` again. `Status` should NOT be
  `Closed` (per the rule: Closed only when State = Lost).

**On failure:**
- `v5/processAccount.deluge` — State/Status rollup (~lines 580-595).
- `v5/processDeal.deluge` — Account rollup hook (~lines 540-548).
- `v5/processContact.deluge` — same rollup pattern (~lines 727-741).

---

## §2B — Activity layer (run after §2A is fully green)

### T11 — `sequenceRouter` bootstraps a new Deal

**What this tests:** WF002 (Deal create_or_edit, Sequence_Status =
Not Started) calls `sequenceRouter`, which calls `createStageCall`,
which creates a "Marketing Qualification Call 1" Call related to the Deal.

This overlaps with T1's hook assertion but tests `sequenceRouter`
directly on a Deal created via the data API (skipping the Lead path).

**Action:**
```
createRecords on Deals with:
  Deal_Name        = <sessionPrefix>_T11
  Account_Name     = <test account id>
  Contact_Name     = <test contact id>
  Opportunity_Stage           = "Marketing Qualification"
  State            = "Open"
  Sequence_Status  = "Not Started"
  Sequence_Action_Mode = "Call First"
  Closing_Date     = <today + 60 days>
  Amount           = 0
```
Wait 30s.

**Assertions (read the Deal back, then its related Calls):**
- `Sequence_Status` == `Waiting on Call`
- `Active_Sequence_Stage` == `Marketing Qualification`
- `Active_Sequence_Attempt` == 1
- `Active_Email_Chain_Step` == 0
- Related Calls: exactly **one** Call with:
  - `Subject` == `Marketing Qualification Call 1`
  - `Sequence_Managed` == `Yes`
  - `Sequence_Stage` == `Marketing Qualification`
  - `Sequence_Attempt` == 1
  - `Stale` == `No`

**On failure:**
1. WF002 active? (`getWorkflowRules` filter by `WF002`)
2. `v5/activity/sequenceRouter.deluge` — bootstrap branch logic
3. `v5/activity/createStageCall.deluge` — Call creation + duplicate
   prevention

### T12 — Stage change supersedes the old sequence

**Depends on T11's Deal.**

**Action:** Update the T11 Deal:
```
Opportunity_Stage = "Demo Booking"
```
Wait 30s.

**Assertions:**
- `Active_Sequence_Stage` == `Demo Booking`
- `Active_Sequence_Attempt` == 1
- `Sequence_Status` == `Waiting on Call`
- The old Marketing Qualification Call from T11 is now `Stale = Yes` and
  `Status = Cancelled`.
- Exactly **one** new open Call exists with `Subject` =
  `Demo Booking Call 1`, `Sequence_Stage = Demo Booking`, `Stale = No`.

**On failure:**
1. WF003 active?
2. `v5/activity/sequenceRouter.deluge` — `stageChanged` branch
3. `v5/activity/supersedeOldSequence.deluge`

### T13 — Commercials_Status = Signed keeps the Deal Open (regression for the State=Won bug)

**Setup:** Create a fresh Deal `<sessionPrefix>_T13`, Opportunity_Stage =
`Commercial Agreement`, State = `Open`, Sequence_Status =
`Waiting on Call`. Wait 15s for any incidental triggers to settle.

**Action:** Update:
```
Commercials_Status = "Signed"
```
Wait 30s.

**Assertions:**
- `Opportunity_Stage` == `Onboarding`
- `Stage` == `RTP`
- `State` == `Open`  ← critical, NOT `Won`
- `Status` is one of `New` or `Working` — NOT `Closed`
- `Signed_At` is not empty
- `Sequence_Status` == `Waiting on Internal Task` (via Task First Onboarding bootstrap)
- `Next_Action_Type` == `Task`
- A related Task exists with `Task_Type` == `Onboarding Setup` and `Status` == `Not Started`

**On failure (any `State == "Won"` is a hard fail):**
1. `v5/activity/handleCommercialsStatusChange.deluge` — the `Signed`
   branch
2. The header comment block should document `State = Open`. If the
   code still writes `Won`, the user republished an old version of the
   function.

### T14 — Commercials_Status = Rejected → Deal Lost

**Setup:** Create a fresh Deal `<sessionPrefix>_T14` at Opportunity_Stage =
`Commercial Agreement`.

**Action:** Update `Commercials_Status = "Rejected"`. Wait 30s.

**Assertions:**
- `State` == `Lost`
- `Status` == `Closed`
- `Sequence_Status` == `Completed`
- `Reason_For_Loss__s` is not empty (e.g. `Commercial Rejected`)

**On failure:**
- `v5/activity/handleCommercialsStatusChange.deluge` — the `Rejected`
  branch

### T15 — Demo_Outcome = Attended - Qualified

**Setup:** Create a fresh Deal `<sessionPrefix>_T15` at Opportunity_Stage =
`Demo Confirmation`.

**Action:** Update `Demo_Outcome = "Attended - Qualified"`. Wait 30s.

**Assertions:**
- `Opportunity_Stage` == `Proposal Preparation`
- `Stage` == `FTP`
- `Commercials_Status` == `Drafting`
- One related Task exists with `Subject` containing
  `Draft Commercials`, `Task_Type` == `Draft Commercials`,
  `Sequence_Managed` == `Yes`.

**On failure:**
- `v5/activity/handleDemoOutcome.deluge` — `Attended - Qualified`
  branch

### T16 — Positive Call outcome advances the Deal

**Depends on T11 or T12's Deal having an open `Marketing Qualification Call 1`
or `Demo Booking Call 1`.** Use whichever exists from prior tests, or
create a new Deal `<sessionPrefix>_T16` with Opportunity_Stage =
`Marketing Qualification`, wait 30s for Call 1 to appear, then proceed.

**Action:** Update that Call:
```
Call_Outcome = "Positive"
```
Wait 30s.

**Assertions:**
- Deal `Opportunity_Stage` advanced one step (Marketing Qualification →
  `Demo Booking`, Demo Booking → `Demo Confirmation`, etc.)
- Deal `Stage` updated accordingly (`MQL` → `SQL`, etc.)

**On failure:**
- WF006 active?
- `v5/activity/handleCallOutcome.deluge` — `Positive` branch + stage
  map.

### T17 — Neutral / No Answer creates Call N+1

**Setup:** Use a fresh Deal `<sessionPrefix>_T17` with Opportunity_Stage =
`Marketing Qualification`. Wait 30s for Call 1.

**Action:** Update Call 1:
```
Call_Outcome = "No Answer"
```
Wait 30s.

**Assertions:**
- Deal `Active_Sequence_Attempt` == 2
- A second open Call exists with `Subject` = `Marketing Qualification Call 2`,
  `Sequence_Attempt` = 2, `Stale` = `No`.

**On failure:**
- `v5/activity/handleCallOutcome.deluge` — `Neutral`/`No Answer` branch

### T18 — Idempotency: second update doesn't duplicate Calls

Pick any Deal from prior tests that already has a Call 1. Update it
with a no-op field change (e.g. add a trailing space to
`Deal_Name`, then remove it again). Each save fires WF002 because
`create_or_edit` is repeat-on. Assert no new Call was created —
`createStageCall` duplicate prevention should hold.

**On failure:**
- `v5/activity/createStageCall.deluge` — duplicate search criteria.

### T24 — Task Lifecycle (Creation & Completion)

**What this tests:** Task creation, polymorphic linkage, task completion trigger (WF008), and sequence resumption.

**Setup:** Use the Deal from T1 or create a fresh Deal `<sessionPrefix>_T24`. Advance the Deal to `Demo Confirmation` and set `Demo_Outcome = "Attended - Qualified"`. Wait 30s.

**Assertions (Creation):**
- Verify Deal `Opportunity_Stage` == `Proposal Preparation`, `Stage` == `FTP`, and `Commercials_Status` == `Drafting`.
- Read Deal's related Tasks via `getRelatedRecords`. Verify exactly **one** Task exists with:
  - `Subject` containing `Draft Commercials`
  - `Task_Type` == `Draft Commercials`
  - `Sequence_Managed` == `Yes`
  - `What_Id` == Deal ID
  - `$se_module` == `Deals`
  - `Who_Id` == primary Contact ID
  - Owner == Deal Owner
- Verify the same Task is returned when querying the Contact's related Tasks.

**Action (Task Completion):**
- Update the Task `Status = "Completed"`. Wait 30s.

**Assertions (Task Completion):**
- Assert `WF008` (Task Completion Handler) executed successfully.
- Assert Deal `Opportunity_Stage` remains `Proposal Preparation` and `Commercials_Status` remains `Drafting` (completing `Draft Commercials` does not advance the sequence prematurely).

**Branch Action (Data Repair Task Completion):**
- Set `Call_Outcome = "Bad Data"` on any open Call related to an active Deal. Wait 30s.
- Verify Deal `Sequence_Status` == `Paused` and a Task with `Task_Type` == `Data Repair` is created.
- Update that `Data Repair` Task `Status = "Completed"`. Wait 30s.
- Assert: Deal `Sequence_Status` returns to `Waiting on Call` and a new Call is created.

**On failure:**
- `v5/activity/handleTaskCompletion.deluge`
- WF008 configuration and argument bindings in Zoho.

### T25 — Demo Event Lifecycle (Scheduled, Rescheduled, Confirmed, Cancelled, No Show)

**What this tests:** Event linkage, Deal field mirroring, reminder calculations, reschedule updates, confirmation, cancellation recovery, and no-show outcome handling.

**Setup:** Since Zoho automation does not automatically create Event records (it only handles them), the test must create the Event fixture itself via `createRecords` on Events:
```json
{
  "Subject": "<sessionPrefix>_Demo",
  "What_Id": "<Deal_ID>",
  "$se_module": "Deals",
  "Who_Id": "<Contact_ID>",
  "Sequence_Managed": "Yes",
  "Meeting_Type": "Demo",
  "Meeting_Status": "Scheduled",
  "Start_DateTime": "future datetime (ISO 8601, e.g. 2026-06-15T10:00:00Z)",
  "End_DateTime": "future datetime (ISO 8601, e.g. 2026-06-15T11:00:00Z)"
}
```
Wait 30s.

**Assertions (Creation & Linkage):**
- Event exists and is owned by the Deal Owner.
- Event appears in Deal's related Events list and Contact's related Activities list.
- Read Deal fields and verify:
  - `Demo_Meeting_ID` == Event ID
  - `Demo_Status` == `Scheduled`
  - `Demo_Start_DateTime` and `Demo_End_DateTime` match the Event's datetimes.
  - `Demo_Reminder_Send_At` is populated.
- Verify Event `Reminder_Send_At` is populated.

**Action 1 (Rescheduled):**
- Update the Event `Meeting_Status = "Rescheduled"` and shift `Start_DateTime` / `End_DateTime` forward by 2 hours. Wait 30s.
- Assert: Deal `Demo_Start_DateTime`, `Demo_End_DateTime`, and `Demo_Reminder_Send_At` are updated. Event `Reminder_Send_At` is recomputed and updated.

**Action 2 (Confirmed):**
- Update the Event `Meeting_Status = "Confirmed"`. Wait 30s.
- Assert: Deal `Demo_Status` is updated to `Confirmed`.

**Action 3 (Cancelled):**
- Update the Event `Meeting_Status = "Cancelled"`. Wait 30s.
- Assert: Deal `Demo_Status` is updated to `Cancelled`, and a recovery Call (`Demo Booking Call 1` or similar recovery Call) is created to reschedule the demo.

**Action 4 (No Show):**
- Update the Event `Meeting_Status = "No Show"`. Wait 30s.
- Assert: Deal `Demo_Status` is updated to `No Show` and the demo outcome logic executes.

**On failure:**
- `v5/activity/handleMeetingEvent.deluge`
- WF007 configuration and argument bindings in Zoho.

### T28 — Unknown / Imported source triggers Manual Review First (Activation Gate)

**What this tests:** When a Deal is created with an unresolved source (e.g., Migration or empty), the route resolver returns `Manual Review First`, creating a Sequence Activation task and setting status to `Waiting on Internal Task` without scheduling any calls or sending emails.

**Action:**
createRecords on Deals with:
  Deal_Name        = <sessionPrefix>_T26
  Account_Name     = <test account id>
  Contact_Name     = <test contact id>
  Opportunity_Stage           = "Marketing Qualification"
  State            = "Open"
  Sequence_Status  = "Not Started"
  Lead_Source      = "Migration"
  Closing_Date     = <today + 60 days>

Wait 30s.

**Assertions:**
- `Sequence_Status` == `Waiting on Internal Task`
- `Active_Sequence_Stage` == `Marketing Qualification`
- `Active_Sequence_Attempt` == 0
- `Next_Action_Type` == `Task`
- Related Tasks: exactly **one** Task exists with:
  - `Subject` == `Activate sequence: <sessionPrefix>_T26 — Marketing Qualification`
  - `Task_Type` == `Sequence Activation`
  - `Sequence_Managed` == `Yes`
  - `Blocks_Sequence` == `Yes`
- Related Calls: **zero** calls exist.

**On failure:**
- `v5/activity/sequenceRouter.deluge` — bootstrap branch for `Manual Review First` route.
- `v5/activity/_util_resolveSequenceRoute.deluge` — source classification checks.

### T29 — Sequence Activation outcome: Activate Call First

**Depends on T28's Deal and activation Task.**

**Action:** Update the activation Task from T28:
```
Task_Outcome = "Activate Call First"
Status = "Completed"
```
Wait 30s.

**Assertions:**
- Deal `Sequence_Action_Mode` == `Call First`
- Deal `Sequence_Status` == `Waiting on Call`
- Deal `Active_Sequence_Attempt` == 1
- Related Calls: exactly **one** Call exists with:
  - `Subject` == `Marketing Qualification Call 1`
  - `Sequence_Stage` == `Marketing Qualification`
  - `Sequence_Attempt` == 1
  - `Stale` == `No`

**On failure:**
- `v5/activity/handleTaskCompletion.deluge` — `Activate Call First` logic.
- `v5/activity/sequenceRouter.deluge` — Call-First bootstrap branch.

### T30 — Sequence Activation outcome: Activate Email First

**Setup:** Create a fresh Deal `<sessionPrefix>_T28` with `Lead_Source = "Migration"`, wait 30s for the activation Task to appear.

**Action:** Update that activation Task:
```
Task_Outcome = "Activate Email First"
Status = "Completed"
```
Wait 30s.

**Assertions:**
- Deal `Sequence_Action_Mode` == `Email First`
- Deal `Sequence_Status` == `Waiting on Call`
- Deal `Active_Sequence_Attempt` == 1
- Related Tasks: an "Email Sent" marker Task exists with `Task_Type` == `Email Sent`, `Status` == `Completed`, and `Description` containing the SendKey.
- Related Calls: exactly **one** Call exists with:
  - `Subject` == `Marketing Qualification Call 1`
  - `Sequence_Stage` == `Marketing Qualification`
  - `Sequence_Attempt` == 1
  - `Stale` == `No`
  - `Call_Start_Time` (due date) is offset by **+2 business days** (spacing rule).

**On failure:**
- `v5/activity/handleTaskCompletion.deluge` — `Activate Email First` logic.
- `v5/activity/sendSequencedEmail.deluge` — template send and marker task.
- `v5/activity/createStageCall.deluge` — attempt 1 business date offset calculation.

### T31 — Email-First Progression: No Answer Call Outcome

**Depends on T30's Deal and Call 1.**

**Action:** Update Call 1 from T30:
```
Call_Outcome = "No Answer"
```
Wait 30s.

**Assertions:**
- Deal `Active_Sequence_Attempt` == 2
- Deal `Sequence_Status` == `Waiting on Call`
- Related Tasks: a new "Email Sent" marker Task exists for attempt 2 (`Marketing Qualification Email 2`).
- Related Calls: exactly **one** new Call exists with `Subject` == `Marketing Qualification Call 2` and `Sequence_Attempt` == 2.

**On failure:**
- `v5/activity/handleCallOutcome.deluge` — `Email First` attempt progression logic.

### T32 — Sequence Activation outcome: Manual Only

**Setup:** Create a fresh Deal `<sessionPrefix>_T30` with `Lead_Source = "Migration"`, wait 30s.

**Action:** Update the activation Task:
```
Task_Outcome = "Manual Only"
Status = "Completed"
```
Wait 30s.

**Assertions:**
- Deal `Sequence_Status` == `Manual Only`
- Deal `Next_Action_Type` is empty
- Related Calls: **zero** calls exist.

**On failure:**
- `v5/activity/handleTaskCompletion.deluge` — `Manual Only` branch.

### T33 — Sequence Activation outcome: Suppress

**Setup:** Create a fresh Deal `<sessionPrefix>_T31` with `Lead_Source = "Migration"`, wait 30s.

**Action:** Update the activation Task:
```
Task_Outcome = "Suppress"
Status = "Completed"
```
Wait 30s.

**Assertions:**
- Deal `Automation_Suppressed` == true
- Deal `Sequence_Status` == `Suppressed`
- Deal `Suppression_Reason` == `Manual Handling Required`
- Related Calls: **zero** calls exist.

**On failure:**
- `v5/activity/handleTaskCompletion.deluge` — `Suppress` branch.

### T34 — Sequence Activation outcome: Already Handled

**Setup:** Create a fresh Deal `<sessionPrefix>_T32` with `Lead_Source = "Migration"`, wait 30s.

**Action:** Update the activation Task:
```
Task_Outcome = "Already Handled"
Status = "Completed"
```
Wait 30s.

**Assertions:**
- Deal `Sequence_Status` == `Completed`
- Deal `Next_Action_Type` is empty
- Related Calls: **zero** calls exist.

**On failure:**
- `v5/activity/handleTaskCompletion.deluge` — `Already Handled` branch.

### T35 — Sequence Activation outcome: Stage Incorrect

**Setup:** Create a fresh Deal `<sessionPrefix>_T33` with `Lead_Source = "Migration"`, wait 30s.

**Action:** Update the activation Task:
```
Task_Outcome = "Stage Incorrect"
Status = "Completed"
```
Wait 30s.

**Assertions:**
- Deal `Sequence_Status` == `Paused`
- Deal `Next_Action_Type` == `Task`
- A new blocking correction Task exists with `Task_Type` == `Manual Review`, `Blocks_Sequence` == `Yes`, and `Subject` containing `Sequence Stage Correction`.
- Related Calls: **zero** calls exist.

**On failure:**
- `v5/activity/handleTaskCompletion.deluge` — `Stage Incorrect` branch.

---

## §3 — Optional / advanced tests

Run only if §2A + §2B are all green and the user wants deeper coverage.

### T20 — Stale Call guard

After T12, attempt to set `Call_Outcome = Positive` on the *stale*
Marketing Qualification Call (the one that got marked `Stale = Yes`).
Assert: the Deal's Opportunity_Stage does **not** change. The handler should drop
the call as stale.

### T21 — Bad data → Manual Review Task

Trigger via `Call_Outcome = "Bad Data"` on an open Call. Assert: Deal
`Sequence_Status = Paused`, a `Data Repair` Task is created.

### T22 — Suppression

Set `Automation_Suppressed = true` on a Deal. Then perform any of the
state mutations from §2B. Assert: no Calls, no emails, no state
changes happen. The functions should early-return.

### T23 — Cross-process consistency

Pick a single canonical Deal that survived §2A. Trigger
`processContact` on its primary Contact (no-op edit), then
`processAccount` on its Account (no-op edit), then `processDeal` on
the Deal itself. After each step, read the Deal back and assert that
`Opportunity_Stage`, `State`, `Status`, `Sequence_Status`, `Amount`,
`Active_Sequence_Stage`, and `Active_Sequence_Attempt` are **unchanged
across all three triggers**. This guards against any of the four
process functions overwriting fields owned by another layer.

**On failure:** look for cascading writes. Cross-process consistency
is the most common regression site when adding a new field write.

---

## §9 — Cleanup

At the end of the session, regardless of pass/fail:

1. Read all Deals where `Deal_Name` starts with `sessionPrefix`. For
   each, read related Calls, Tasks, Events.
2. Delete via `deleteRecords` in this order:
   Calls → Tasks → Events → Deals → Contacts → Accounts → Leads.
3. Confirm zero records remain matching the session prefix.

Then write a final summary to `MCP_TEST_RUN_LOG.md`:

```text
## Round <N> — Summary
- Tests passed: T1, T2, …
- Tests failed: …
- Fixes written this round: <file paths>
- Republish required: yes/no
- Test records cleaned up: yes
```

---

## §10 — Out of scope for this harness

Do NOT attempt to test:
- **WF009a–e (email events).** Outgoing-email triggers require actual
  email sends and engagement; they cannot be simulated via MCP. Trust
  the Phase 14 wrapper architecture and the manual verification in
  `WORKFLOW_CONFIGURATION_CHECKLIST.md`.
- **WF010 (date-based).** Date triggers require either wall-clock
  waits or shifting datetime fields and waiting for Zoho's scheduler
  tick. Out of scope.
- **Email template rendering.** No MCP read access. Manual check in UI.
- **`zoho_crm` connection or function publish step.** User's
  responsibility; you only call the workflows that result.

---

## §11 — Failure handling rules (reference)

- **One fix per round.** If multiple tests fail, propose fixes for all,
  but write them in priority order and hand off to user to republish
  once. The next round re-runs all previously-failed tests.
- **Don't touch the Zoho UI from this prompt.** Workflow rule
  reconfiguration, function configuration mapping, layout work —
  defer to the user with clear UI instructions.
- **Don't expand scope.** A failing T3 (State=Won) doesn't justify
  rewriting `handleCommercialsStatusChange` end-to-end. Make the
  smallest correct change.
- **If a workflow rule itself is misconfigured** (wrong trigger, wrong
  criteria) and the fix is API-supported, you may use
  `mcp__zoho-crm-automation__ZohoCRM_updateWorkflowRuleById` to fix it
  — but log this in the run log as a configuration fix, not a code
  fix, and the user does not need to republish for it.

---

## §4 — Coverage gaps to flag (review before testing)

Items the user explicitly named and items the user might not have
thought to ask about. The Claude Code session should review this list
at session start, decide which items apply to the current round, and
either fold them into the test runs or note them in
`MCP_TEST_RUN_LOG.md` as known gaps for future rounds.

### Cross-module bidirectional link integrity

Every record-to-record reference should be readable from both sides.
Verify by spot-checking, not necessarily as a dedicated test:

| Source → Target | Forward read (on source) | Reverse read (related list on target) |
|---|---|---|
| Lead → Contact (post-convert) | `Lead.Converted_Contact` lookup populated | Contact's audit shows the Lead conversion |
| Contact → Account | `Contact.Account_Name` lookup | Account's related Contacts list |
| Deal → Account | `Deal.Account_Name` lookup | Account's related Deals list |
| Deal → primary Contact | `Deal.Contact_Name` lookup | Contact's related Deals list |
| Deal ↔ multiple Contacts | Deal's `Contact_Roles` related list | Each Contact's related Deals list |
| Deal → Products | `Product_Details` subform | Product's "where used" / related Deals |
| Call/Task/Event → Deal | `What_Id` lookup (polymorphic) + `$se_module` = `Deals` | Deal's related Calls/Tasks/Events list |
| Call/Task/Event → primary Contact | `Who_Id` lookup | Contact's related Activities list |

If any forward reference exists but the reverse read returns empty
(or vice versa), that's a broken bidirectional link — usually caused
by writing the lookup with the wrong shape (string vs `{id, name}`
map). Flag in the log.

### Activities polymorphic `What_Id` linkage

When `createStageCall` or the demo/draft Task creators run, the
resulting Call/Task/Event must be linked to the Deal via:
- `What_Id` = the Deal's record id
- `$se_module` = `"Deals"` (literally that string — Zoho's polymorphic
  marker)

Common bug: writing `What_Id` as a lookup map `{id: ..., name: ...}`
instead of the bare id, or omitting `$se_module`. Verify on at least
one Call from T11 / T14 / T15 by reading the Call record raw.

### Field model audit (pre-flight)

Before running tests, optionally run a one-shot audit:
1. For each module in {Deals, Contacts, Accounts, Leads, Calls,
   Events, Tasks, Products}, call
   `mcp__zoho-crm-module-customisation__ZohoCRM_getFields`.
2. Diff the returned fields against
   `.agents/context/activity-workflows/zoho_custom_fields_by_module.csv`.
3. For each picklist field, diff the actual picklist values against
   the CSV's `Picklist_Values` column.

A missing field or picklist value here will cause an opaque
`INVALID_DATA` failure deep inside a test, so catching it up front
saves time.

### Workflow rule configuration drift

For each WF in `WORKFLOW_TRIGGER_MAP.md`, call
`mcp__zoho-crm-automation__ZohoCRM_getWorkflowRules` with
`include_inner_details=true` and verify:
- Trigger type matches (`create_or_edit`, `field_update`, etc.).
- Criteria match the spec (e.g. WF002 requires
  `Sequence_Status = "Not Started"`).
- Functions attached to each rule's instant_actions are the expected
  ones. **Note:** the MCP `getWorkflowRules` endpoint historically did
  not return inner action details despite `include_inner_details=true`.
  If actions aren't in the response, this verification has to be
  manual in the UI.

### Owner / `Created_By` on automation-generated records

When `createStageCall` creates a Call, who owns it? Should be the
Deal's Owner, but is currently the executing user (the function's
service user). Same for `handleDemoOutcome` → `Draft Commercials`
Task and `handleEmailEvent` → `Review Reply` / `Data Repair` Tasks.

Note for the run log: if Calls/Tasks are assigned to the service user
and not the Deal Owner, users will not see them in their default views
and the sequence will appear stuck.

### Opportunity_Stage → Stage (Opportunity) derived value

Every code path that writes `Opportunity_Stage` should also write the matching
`Stage` (Opportunity bucket). The mapping is:

| Opportunity_Stage | Stage |
|---|---|
| Marketing Qualification | MQL |
| Demo Booking, Demo Confirmation, Demo Hosted | SQL |
| Commercial Agreement | FTP |
| Onboarding, Onboarding, Renewal | RTP |

If a test ever finds `Opportunity_Stage = Onboarding` with `Stage = SQL`
(or any other mismatch), the writing function has a bug. Spot-check
this invariant after T12 (stage change), T13 (Signed), T15 (Demo
Attended).

### `Marketing_Consent_Status` (picklist) vs `Marketing_Consent` (legacy boolean)

Both fields exist. The activity layer reads `Marketing_Consent_Status`;
the boolean is retained for legacy filters. They should not drift —
if `Marketing_Consent_Status = Consented` but `Marketing_Consent =
false`, that's a divergence and someone will eventually wire a query
to the wrong one. Optionally assert consistency on every Contact T1
through T10 touches.

### `Reason_For_Loss__s` vs `Lost_Reasons`

Two distinct fields. Code today writes mostly to `Reason_For_Loss__s`
(commercial reject, demo disqualified, duplicate). `Lost_Reasons` is a
legacy multi-select. Confirm which one filters/reports actually use —
if reports use `Lost_Reasons` and automation writes
`Reason_For_Loss__s`, the loss reasons will silently never appear in
reports.

### Closing_Date defaulting

Several tests set `Closing_Date = today + 60`. The production
processX functions should ideally default `Closing_Date` when not
provided. If a Deal is created without one, does `processDeal` set a
sensible default, or does the Deal end up with `Closing_Date = null`
(which breaks pipeline forecasting)? Worth asserting on T1.

### Onboarding / Renewal stages (under-tested)

The 8 Opportunity_Stage values include `Onboarding` and `Renewal`, but the test
plan focuses on the pre-sign path. The post-sign path
(`Onboarding → Onboarding → Renewal`) is exercised
incidentally by T13 but not asserted end-to-end. If those stages have
specific automation (e.g. onboarding kickoff email, renewal call
cadence), add tests in a future round.

### `Automation_Suppressed` honored across **all** function entry points

T22 covers this for the activity layer. Worth verifying it also gates
the graph layer — i.e. set `Automation_Suppressed = true` on a Deal,
then trigger `processDeal` via a no-op edit, and assert no Opportunity_Stage /
Account-rollup recompute happens. The graph layer should also
short-circuit on the suppression flag, not just the activity layer.

### `Account_Key` and `Deal_Key` uniqueness

`Account_Key` and `Deal_Key` must be UNIQUE in Zoho (per
`processDeal.deluge`'s header comment block). Verify the constraints
are actually enforced in the field config via
`getFields(module=Accounts, include=allowed_permissions_to_update)`.
If uniqueness isn't enforced at field level, two parallel
`processX` runs could create duplicate Accounts/Deals before the dedup
logic catches up.

### Rate limits / API quotas

The test harness will burn through API calls quickly — each
create+read+delete is 3 calls minimum, and a full §2A + §2B run is
~150 calls. Zoho's standard daily quota is generous but not infinite.
If a test fails with `LIMIT_EXCEEDED` or similar, back off and re-run
the failed test only.

### Multi-currency

Deal `Amount` is currency-aware. The test products in T7 must all be
in the same currency, or the sum assertion needs to apply currency
multipliers. Skip multi-currency testing unless explicitly requested.

### Layout completeness (UI-visible new fields)

New custom fields created via MCP default to org-level access but
aren't necessarily added to the page layout. Out of scope for MCP
tests, but flag if tests pass yet the user can't see the field in the
Zoho UI — that's a layout config issue, not a code issue.

### `zoho_crm` connection availability

`sendSequencedEmail` uses a named `zoho_crm` connection. The
test harness can't directly verify the connection is configured,
but if any test fails inside a function that runs `invokeurl ...
connection : "zoho_crm"` with `AUTHENTICATION_FAILURE`, the connection
isn't set up. Direct the user to Setup → Developer Space →
Connections.

---

## Reference docs

- Spec: `spec.md`, `agents.md`
- Pipeline model: `docs/v2/02-pipeline-model.md`
- Workflow trigger shapes: `.agents/context/activity-workflows/WORKFLOW_TRIGGER_MAP.md`
- Workflow wiring checklist: `.agents/context/activity-workflows/WORKFLOW_CONFIGURATION_CHECKLIST.md`
- Field model: `.agents/context/activity-workflows/zoho_custom_fields_by_module.csv`
- Reuse decisions: `.agents/context/activity-workflows/FIELD_REUSE_NOTES.md`
- Manual-UI verification (companion to this MCP harness):
  `.agents/context/activity-workflows/VERIFICATION_PLAN.md`

---

## Kickoff

When you start a session with this prompt, output:

```text
MCP test harness ready. Confirm:
1. Is this org safe for create/delete (sandbox / dev)?
2. Test Account ID I can attach Deals to? (or "create new")
3. Test Contact ID I can attach Deals to? (or "create new")
4. Round number to record in MCP_TEST_RUN_LOG.md?
```

Then wait for the user's reply before running §0.
