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

Run in the order below. Each test depends on no prior test except
where noted. Use a fresh `sessionPrefix + "_T<n>"` for each test's
records.

### T1 — sequenceRouter bootstraps a new Deal

**What this tests:** WF002 (Deal create_or_edit, Sequence_Status = Not Started)
calls `sequenceRouter`, which calls `createStageCall`, which creates a
"Marketing Consent Call 1" Call related to the Deal.

**Action:**
```
createRecords on Deals with:
  Deal_Name        = <sessionPrefix>_T1
  Account_Name     = <test account id>
  Contact_Name     = <test contact id>
  Stage1           = "Marketing Consent"
  State            = "Open"
  Sequence_Status  = "Not Started"
  Closing_Date     = <today + 60 days>
  Amount           = 0
```

Wait 30s.

**Assertions (read the Deal back, then its related Calls):**
- `Sequence_Status` == `Waiting on Call`
- `Active_Sequence_Stage` == `Marketing Consent`
- `Active_Sequence_Attempt` == 1
- `Active_Email_Chain_Step` == 0
- Related Calls: exactly **one** Call with:
  - `Subject` == `Marketing Consent Call 1`
  - `Sequence_Managed` == `Yes`
  - `Sequence_Stage` == `Marketing Consent`
  - `Sequence_Attempt` == 1
  - `Stale` == `No`

**On failure**, investigate in this order:
1. WF002 active? (`getWorkflowRules` filter by `WF002`)
2. `v4/activity/sequenceRouter.deluge` — bootstrap branch logic
3. `v4/activity/createStageCall.deluge` — Call creation + duplicate
   prevention

### T2 — Stage change supersedes the old sequence

**Depends on T1's Deal.**

**Action:** Update the T1 Deal:
```
Stage1 = "Demo Booking"
```
Wait 30s.

**Assertions:**
- `Active_Sequence_Stage` == `Demo Booking`
- `Active_Sequence_Attempt` == 1
- `Sequence_Status` == `Waiting on Call`
- The old Marketing Consent Call from T1 is now `Stale = Yes` and
  `Status = Cancelled`.
- Exactly **one** new open Call exists with `Subject` =
  `Demo Booking Call 1`, `Sequence_Stage = Demo Booking`, `Stale = No`.

**On failure:**
1. WF003 active?
2. `v4/activity/sequenceRouter.deluge` — `stageChanged` branch
3. `v4/activity/supersedeOldSequence.deluge`

### T3 — Commercials_Status = Signed keeps the Deal Open (regression for the State=Won bug)

**Setup:** Create a fresh Deal `<sessionPrefix>_T3`, Stage1 =
`Commercials Sent`, State = `Open`, Sequence_Status =
`Waiting on Call`. Wait 15s for any incidental triggers to settle.

**Action:** Update:
```
Commercials_Status = "Signed"
```
Wait 30s.

**Assertions:**
- `Stage1` == `Commercials Signed`
- `Stage` == `RTP`
- `State` == `Open`  ← critical, NOT `Won`
- `Status` is one of `New` or `Working` — NOT `Closed`
- `Signed_At` is not empty
- `Sequence_Status` == `Not Started` (so WF003 can bootstrap the RTP
  sequence on the next tick)

**On failure (any `State == "Won"` is a hard fail):**
1. `v4/activity/handleCommercialsStatusChange.deluge` — the `Signed`
   branch
2. The header comment block should document `State = Open`. If the
   code still writes `Won`, the user republished an old version of the
   function.

### T4 — Commercials_Status = Rejected → Deal Lost

**Setup:** Create a fresh Deal `<sessionPrefix>_T4` at Stage1 =
`Commercials Sent`.

**Action:** Update `Commercials_Status = "Rejected"`. Wait 30s.

**Assertions:**
- `State` == `Lost`
- `Status` == `Closed`
- `Sequence_Status` == `Completed`
- `Reason_For_Loss__s` is not empty (e.g. `Commercial Rejected`)

**On failure:**
- `v4/activity/handleCommercialsStatusChange.deluge` — the `Rejected`
  branch

### T5 — Demo_Outcome = Attended - Qualified

**Setup:** Create a fresh Deal `<sessionPrefix>_T5` at Stage1 =
`Demo Booked`.

**Action:** Update `Demo_Outcome = "Attended - Qualified"`. Wait 30s.

**Assertions:**
- `Stage1` == `Demo Attended`
- `Stage` == `SQL`
- `Commercials_Status` == `Drafting`
- One related Task exists with `Subject` containing
  `Draft Commercials`, `Task_Type` == `Draft Commercials`,
  `Sequence_Managed` == `Yes`.

**On failure:**
- `v4/activity/handleDemoOutcome.deluge` — `Attended - Qualified`
  branch

### T6 — Positive Call outcome advances the Deal

**Depends on T1 or T2's Deal having an open `Marketing Consent Call 1`
or `Demo Booking Call 1`.** Use whichever exists from prior tests, or
create a new Deal `<sessionPrefix>_T6` with Stage1 =
`Marketing Consent`, wait 30s for Call 1 to appear, then proceed.

**Action:** Update that Call:
```
Call_Outcome = "Positive"
Call_Result  = (optional, leave existing)
```
Wait 30s.

**Assertions:**
- Deal `Stage1` advanced one step (Marketing Consent →
  `Demo Booking`, Demo Booking → `Demo Booked`, etc.)
- Deal `Stage` updated accordingly (`MQL` → `SQL`, etc.)

**On failure:**
- WF006 active?
- `v4/activity/handleCallOutcome.deluge` — `Positive` branch + stage
  map.

### T7 — Neutral / No Answer creates Call N+1

**Setup:** Use a fresh Deal `<sessionPrefix>_T7` with Stage1 =
`Marketing Consent`. Wait 30s for Call 1.

**Action:** Update Call 1:
```
Call_Outcome = "No Answer"
```
Wait 30s.

**Assertions:**
- Deal `Active_Sequence_Attempt` == 2
- A second open Call exists with `Subject` = `Marketing Consent Call 2`,
  `Sequence_Attempt` = 2, `Stale` = `No`.

**On failure:**
- `v4/activity/handleCallOutcome.deluge` — `Neutral`/`No Answer` branch

### T8 — Idempotency: second update doesn't duplicate Calls

Pick any Deal from prior tests that already has a Call 1. Update it
with a no-op field change (e.g. add a trailing space to
`Deal_Name`, then remove it again). Each save fires WF002 because
`create_or_edit` is repeat-on. Assert no new Call was created —
`createStageCall` duplicate prevention should hold.

**On failure:**
- `v4/activity/createStageCall.deluge` — duplicate search criteria.

### T9 — Lead conversion creates Contact + Account + Deal

**Action:** Create a Lead via `createRecords` on Leads with:
```
Last_Name              = <sessionPrefix>_T9_Last
First_Name             = MCPTest
Company                = <sessionPrefix>_T9_Co
Email                  = mcp_t9@example.com
Lead_Processing_Status = "Not Started"
Ready_for_Conversion   = true
```
Wait 60s (Lead pipeline is heavier).

**Assertions:**
- A Contact exists with `Email` = `mcp_t9@example.com`.
- An Account exists with `Account_Name` containing the Lead's
  `Company`.
- A Deal exists linked to that Account + Contact, with Stage1 =
  `Marketing Consent`, State = `Open`.
- The Lead's `Conversion_Outcome` (or equivalent) reflects success.

**On failure:**
- WF001 active?
- `v4/processLead.deluge` — full pipeline; check the `info` logs.

---

## §3 — Optional / advanced tests

Run only if §2 is all green and the user wants deeper coverage.

### T10 — Stale Call guard

After T2, attempt to set `Call_Outcome = Positive` on the *stale*
Marketing Consent Call (the one that got marked `Stale = Yes`).
Assert: the Deal's Stage1 does **not** change. The handler should drop
the call as stale.

### T11 — Bad data → Manual Review Task

Trigger via `Call_Outcome = "Bad Data"` on an open Call. Assert: Deal
`Sequence_Status = Paused`, a `Data Repair` Task is created.

### T12 — Suppression

Set `Automation_Suppressed = true` on a Deal. Then perform any of the
state mutations from §2. Assert: no Calls, no emails, no state
changes happen. The functions should early-return.

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
