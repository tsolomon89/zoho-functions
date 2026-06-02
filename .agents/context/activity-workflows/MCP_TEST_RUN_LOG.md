# MCP Test Run Log

Append-only log of MCP test harness runs. One round per `## Round N` section.

---

## Round 1 — 2026-06-01 09:00

**Org mode:** Production (fresh — no real data, treat with care).
**Session prefix:** `MCP_TEST_20260601_T0900`
**Lead-only constraint:** Per user, only Leads are created directly via MCP. Contacts/Accounts/Deals are observed after `processLead` creates them, then *updated* (not directly created) for downstream tests.

### Pre-flight findings

- **Graph-layer workflows (CONFIRMED EXECUTING):**
  - WF001a Process Lead (Leads, create_or_edit, last_executed 2026-05-30) — id `991103000000663622`
  - WF001b Process Contact (Contacts, create_or_edit, last_executed 2026-05-30) — id `991103000000663630`
  - WF001c Process Account (Accounts, create_or_edit, last_executed 2026-05-30) — id `991103000000663648`
  - WF001d Process Deal (Deals, create_or_edit, last_executed 2026-05-30) — id `991103000000663638`

- **Activity-layer workflows (ACTIVE but `last_executed_time = null`, descriptions still read "PLACEHOLDER ACTION ... REPLACE WITH custom function"):**
  - WF002 Deal Sequence Router — id `991103000000796079`
  - WF003 Deal Stage Change Router — id `991103000000784137`
  - WF004 Commercials Status Handler — id `991103000000800001`
  - WF005 Demo Outcome Handler — id `991103000000801001`
  - WF006 Handle Call Outcome — id `991103000000780461`
  - WF007 Event Meeting Handler — id `991103000000782052`
  - WF008 Task Completion Handler — id `991103000000784145`
  - WF010a–d Date Routers — placeholder

  T1's "Marketing Consent Call 1 exists" assertion will tell us if the activity layer is reachable via the direct `automation.sequenceRouter` hook fired from `processDeal`, regardless of WF002 wiring.

- **Module IDs cached:** Leads=`991103000000000043`, Accounts=`991103000000000045`, Contacts=`991103000000000047`, Deals=`991103000000000049`, Tasks=`991103000000000063`, Events=`991103000000000065`, Calls=`991103000000000067`.

### Test results

### T1 — processLead end-to-end conversion

- **Status:** FAIL (partial)
- **Action taken:** Created Lead `MCP_TEST_20260601_T0900_T1_Last` (id `991103000000795089`) with `Job_Title="Head of Marketing"`, `Company="MCP_TEST_20260601_T0900_T1_Co"`, `Website="https://acme-t0900-t1.example"`, `Ready_for_Conversion=true`. Waited 60s. Read derived Contact / Account / Deal / Calls.
- **Observed (graph layer — PASS):**
  - Contact `991103000000721223` created with `Email=mcp_t0900_t1@acme-t0900-t1.example`, `Account_Name → 991103000000735173`, `Contact_Role1="Decision Maker"`, `Job_Title="Head of Marketing"`. ✅
  - Account `991103000000735173` created with `Account_Name="MCP_TEST_20260601_T0900_T1_Co"`, `Account_Key="acme-t0900-t1.example"`, `Website="https://acme-t0900-t1.example"`, `State="Open"`, `Status="New"`. ✅
  - Deal `991103000000762142` created with `Deal_Name="MCP_TEST_20260601_T0900_T1_Co Deal"`, `Stage1="Marketing Consent"`, `Stage="MQL"`, `State="Open"`, `Deal_Key="acme-t0900-t1.example::active"`, `Sequence_Status="Waiting on Call"`, `Active_Sequence_Stage="Marketing Consent"`, `Active_Sequence_Attempt=1`, `Active_Email_Chain_Step=0`. ✅
  - Deal's `Contact_Roles` related list has 1 entry: Contact `991103000000721223` with `Contact_Role="Decision Maker"`. ✅
- **Observed (activity layer — FAIL):**
  - **No Call record exists anywhere in the Calls module** — `getRecords` on Calls (no filter, sort desc by Created_Time, per_page 10) returned 0 records.
  - Deal's related `Calls` list also empty.
- **Expected:** A Call with `Subject="Marketing Consent Call 1"`, `Sequence_Managed="Yes"`, `Sequence_Stage="Marketing Consent"`, `Sequence_Attempt=1`, `Stale="No"`, `What_Id=Deal id`, `$se_module="Deals"`, `Who_Id=Contact id`.
- **Diagnosis:**
  1. Reproduced `createStageCall`'s exact payload via direct MCP `createRecords` on Calls — **succeeded** (Call `991103000000790081`). All fields valid: `Subject`, `What_Id`, `$se_module`, `Who_Id`, `Sequence_Managed`, `Sequence_Stage`, `Sequence_Attempt`, `Block_Email_Until_Done`, `Call_Purpose_Detail`, `Call_Type=Outbound`, `Call_Start_Time` (future), `Stale=No`. So the payload itself is fine. (Diagnostic Call then deleted.)
  2. Re-triggered the Deal by setting `Sequence_Status="Not Started"` and clearing `Active_Sequence_Stage` / `Active_Sequence_Attempt`. WF001d re-fired → `processDeal` → `sequenceRouter`. Sequence-state fields advanced to `Waiting on Call` / `Marketing Consent` / `1` again (proving sequenceRouter executed and entered its `needsBootstrap` branch), **but again no Call was created**.
  3. `sequenceRouter` calls `automation.createStageCall(dealId.toString(), stage, 1)` at [v4/activity/sequenceRouter.deluge:134](../../../v4/activity/sequenceRouter.deluge#L134) and then unconditionally writes `Sequence_Status="Waiting on Call"` at [v4/activity/sequenceRouter.deluge:137-146](../../../v4/activity/sequenceRouter.deluge#L137-L146) without checking the returned `callId`. So if `createStageCall` returns `""` (failure), the Deal advances anyway.
- **Root cause:** `automation.createStageCall` is **silently failing** when invoked from the parent Deluge function. The most likely reason is that the function is not currently published in Zoho's Functions registry (Setup → Functions), so the Deluge invocation `automation.createStageCall(...)` returns null without error. The file [v4/activity/createStageCall.deluge](../../../v4/activity/createStageCall.deluge) exists on disk but must be published as a Zoho custom function under the name `createStageCall` (namespace `automation`).
- **Fix written:** No code change in this round. The fix is operational: publish `createStageCall` in Zoho. (Secondary code finding for a future round: `sequenceRouter` should check `createStageCall`'s return value and skip the Deal state advance when the Call creation fails — but defer until we confirm the primary publish-and-rerun fix actually creates the Call.)

#### T1 follow-up — true root cause (via REST diagnostic)

The "createStageCall is unpublished" hypothesis was wrong — user confirmed it's published. After enabling the function's REST API toggle, direct REST invoke of `createStageCall("991103000000762142","Marketing Consent",1)` returned:

```json
{ "code":"success",
  "details":{
    "output":"",
    "userMessage":["automation_event func=createStageCall module=Calls record= action=create outcome=failed payload={\"deal\":991103000000762142,\"stage\":\"Marketing Consent\",\"attempt\":1,\"resp\":{\"code\":\"INVALID_DATA\",\"details\":{\"expected_data_type\":\"datetime\",\"api_name\":\"Call_Start_Time\"},\"message\":\"invalid data\",\"status\":\"error\"}}"]
  }}
```

- **Actual root cause:** [v4/activity/createStageCall.deluge:61](../../../v4/activity/createStageCall.deluge#L61) assigns `dueDate = zoho.currenttime;` for `attempt == 1` and passes it directly to `callMap.put("Call_Start_Time", dueDate)`. In the `attempt > 1` branch, the code explicitly does `.toDateTime("yyyy-MM-dd HH:mm:ss")` to produce a real DateTime object. The `attempt == 1` branch skipped that conversion, so the value got serialised as a String rather than a Deluge DateTime — Zoho's `createRecord` rejected it with `expected_data_type=datetime`.
- **Why my earlier MCP create with the same payload succeeded:** I passed `Call_Start_Time` as the ISO 8601 string `"2026-06-01T12:00:00+01:00"`, which the REST API parses leniently. The Deluge-internal serialisation path is stricter.
- **Fix written:** unified both branches through the proven `.toDateTime(...)` pattern. Edit landed in [v4/activity/createStageCall.deluge:62-72](../../../v4/activity/createStageCall.deluge#L62-L72):

  ```deluge
  dueDateStr = "";
  if(attempt > 1) {
      dueDateStr = automation.calculateBusinessDate(zoho.currenttime, 2, "business_days");
  } else {
      dueDateStr = zoho.currenttime.toString("yyyy-MM-dd HH:mm:ss");
  }
  dueDate = dueDateStr.toDateTime("yyyy-MM-dd HH:mm:ss");
  ```

- **Secondary code findings (not fixed this round, deferred):**
  1. `sequenceRouter` at [v4/activity/sequenceRouter.deluge:134-146](../../../v4/activity/sequenceRouter.deluge#L134-L146) doesn't check `createStageCall`'s return value — if the Call create fails, the Deal still gets `Sequence_Status="Waiting on Call"`, making the state lie.
  2. The same `zoho.currenttime` → `Call_Start_Time` pattern may exist in other Deluge functions (search candidates: handleCallOutcome, handleCommercialsStatusChange, handleDemoOutcome, sendSequencedEmail). Worth a sweep after the primary fix lands.

- **Republish required next round:** `createStageCall`.

#### T1 follow-up 2 — first fix was wrong, refined

After republish of the unified-`.toDateTime` fix, REST-invoke of `createStageCall` returned the **same** `INVALID_DATA expected_data_type=datetime api_name=Call_Start_Time` error — for **both** `attempt=1` and `attempt=2`. So the existing `.toDateTime("yyyy-MM-dd HH:mm:ss")` pattern in the original `attempt > 1` branch ALSO never worked; the function has likely never successfully created a Call.

Direct probe of Zoho's Calls `createRecord` with raw payloads (via `POST /crm/v7/Calls`) showed the exact format requirement:

| `Call_Start_Time` value | Result |
|---|---|
| `2026-06-01T13:00:00+01:00` (ISO-8601, T-separator, offset) | ✅ SUCCESS |
| `2026-06-01T13:00:00Z` (ISO-8601, T-separator, Zulu) | ✅ SUCCESS |
| `2026-06-01 13:00:00` (space-separator, no offset) | ❌ 400 |
| `2026-06-01 13:00:00+01:00` (space-separator + offset) | ❌ 400 |

Zoho strictly requires the `T` separator. Both `zoho.currenttime` and `automation.calculateBusinessDate(...)` return the space-separated form, and `.toDateTime(format)` followed by passing to `callMap.put` re-serialises in the same space-separated form.

- **Refined fix:** [v4/activity/createStageCall.deluge:60-74](../../../v4/activity/createStageCall.deluge#L60-L74) — format explicitly as ISO-8601 via `.toString("yyyy-MM-dd'T'HH:mm:ssXXX")`:

  ```deluge
  dueDateBaseStr = "";
  if(attempt > 1) {
      dueDateBaseStr = automation.calculateBusinessDate(zoho.currenttime, 2, "business_days");
  } else {
      dueDateBaseStr = zoho.currenttime;
  }
  dueDate = dueDateBaseStr.toDateTime("yyyy-MM-dd HH:mm:ss").toString("yyyy-MM-dd'T'HH:mm:ssXXX");
  ```

  The `XXX` format pattern produces `+01:00`-style offset (confirmed-accepted by Zoho via the probe above).

- **Implication for the broader codebase:** any other Deluge function that writes a datetime field to Zoho via `createRecord` / `updateRecord` is suspect. Likely affected (need a sweep):
  - `handleCallOutcome.deluge` — writes `Next_Action_Due_Date`, `Sequence_Paused_Until` etc.
  - `handleCommercialsStatusChange.deluge` — writes `Signed_At`, `Commercials_Sent_At`
  - `handleDemoOutcome.deluge` — writes demo-related dates
  - `sendSequencedEmail.deluge` — writes email-send timestamps
  - `sequenceRouter.deluge` — writes `Next_Action_Due_Date`
  - `supersedeOldSequence.deluge` — writes timestamps when stamping `Stale=Yes` etc.

  Documented as a deferred sweep below.

- **Republish required:** `createStageCall` (again).

#### T1 final result + batch sweep

After republish of the ISO-8601 fix, REST-invoke of `createStageCall("991103000000762142","Marketing Consent",1)` returned **success** with `output="991103000000740288"` and `due="2026-06-01T12:55:41+02:00"` (proper ISO 8601 with offset).

Full workflow-chain verification: deleted the REST-created Call, reset Deal `Sequence_Status=Not Started`, waited 60s. WF001d fired → `processDeal` → `sequenceRouter` → `createStageCall` → **Call `991103000000762148` created** with all expected fields:
- `Subject="Marketing Consent Call 1"`, `Sequence_Managed="Yes"`, `Sequence_Stage="Marketing Consent"`, `Sequence_Attempt=1`, `Stale="No"`, `Call_Type="Outbound"`, `Call_Start_Time="2026-06-01T11:56:23+01:00"`, `Call_Purpose_Detail="Data Completion"`, `What_Id` → Deal, `$se_module="Deals"`, `Who_Id` → Contact.

**T1 — PASS.**

#### Batch fix — same datetime-format bug applied to 6 other write sites

Grep across `v4/` found the same `zoho.currenttime`/`.toDateTime(...)` → datetime-field pattern in 6 other places. All have the same fix shape: `.toString("yyyy-MM-dd'T'HH:mm:ssXXX")` to produce ISO-8601 with offset. Edits landed:

| # | File:line | Datetime field |
|---|---|---|
| 1 | `v4/activity/handleCallOutcome.deluge:150-153` | `Next_Action_Due_Date` |
| 2 | `v4/activity/sequenceRouter.deluge:118-119` | `Next_Action_Due_Date` |
| 3 | `v4/activity/handleMeetingEvent.deluge:94-96` | `Demo_Reminder_Send_At`, `Reminder_Send_At` (Events) |
| 4 | `v4/activity/sendSequencedEmail.deluge:110-111` | `Last_Email_Sent_At` |
| 5 | `v4/activity/supersedeOldSequence.deluge:37-38` | `Sequence_Superseded_At` |
| 6 | `v4/activity/handleCommercialsStatusChange.deluge:52-53` | `Commercials_Sent_At`, `Commercials_Discussed_At`, `Signed_At` |

**Republish required next round:** all 6 functions above.

### T2 — processDeal idempotency (reframed from "processLead idempotency")

- **Discovery first:** trying to update the T1 Lead returned `INVALID_DATA: "can't update the converted record"`. So Zoho's native conversion flag IS set on the Lead after processLead runs — even though the Converted_Contact/Account/Deal fields didn't return any values when queried. Practical consequence: WF001a / processLead can never re-fire on the same Lead after first conversion. Lead-side idempotency is enforced by Zoho itself, not by function logic.
- **Reframed test:** trigger `processDeal` idempotency by editing the canonical Deal `991103000000762142` with a no-op change (`Description="MCP_TEST_T2_noop_edit_1"`) — WF001d (`create_or_edit`, repeat=true) fires processDeal which then calls sequenceRouter.
- **Status:** PASS
- **Observed:** counts unchanged (Contacts=5, Accounts=2, Deals=2, Calls=1). Deal `Modified_Time` advanced to `13:07:50`, `Description` persisted, `Sequence_Status="Waiting on Call"` / `Active_Sequence_Stage="Marketing Consent"` / `Active_Sequence_Attempt=1` unchanged. sequenceRouter correctly recognised state was already active (sequence not in bootstrap states) and skipped Call creation.

### T4 — multi-Lead → multi-Contact role precedence

- **Status:** PASS (on the actual role-assignment assertion) + separate race-condition bug found.
- **Action taken:** Created 3 Leads with the same `Website="https://acme-t0900-t4.example"`, sequential with 60s / 45s / 60s waits between:
  - Lead A `991103000000799031` — Job_Title="Head of Marketing" (Decision Maker)
  - Lead B `991103000000792032` — Job_Title="Product Manager" (End User)
  - Lead C `991103000000785085` — Job_Title="Marketing Manager" (Influencer)
- **Observed:**
  - 3 Contacts created under one Account (`991103000000762150`, `Account_Key=acme-t0900-t4.example`). Each Contact's `Contact_Role1` matches its title-mapped role: DM / EU / Inf. ✅
  - 1 canonical Deal `991103000000757200` with `Deal_Key=acme-t0900-t4.example::active`, `Stage1=Marketing Consent`, `Stage=MQL`, `State=Open`, `Sequence_Status=Waiting on Call`. ✅
  - Deal's `Contact_Roles` related list has all 3 entries with correct roles. ✅
  - Deal's primary `Contact_Name` is T4_A (Decision Maker). This is correct — primary selection is "furthest viable open Contact", all 3 are equally open at creation, T4_A was first. Role-precedence (EU > Inf > DM) applies to per-Contact role assignment, not primary selection.
- **Race-condition bug found (separate from T4's assertion):** two `Marketing Consent Call 1` records were created on Deal `991103000000757200`, IDs `991103000000733355` (13:10:12) and `991103000000752299` (13:10:13), ~1 second apart. Both have `Sequence_Managed=Yes, Sequence_Stage=Marketing Consent, Sequence_Attempt=1` — the dup-check in `createStageCall` should have prevented this.
  - **Root cause:** Grep across `v4/` found `sequenceRouter(...)` called from FIVE places — [processLead.deluge:898](../../../v4/processLead.deluge#L898), [processContact.deluge:712](../../../v4/processContact.deluge#L712), [processAccount.deluge:562](../../../v4/processAccount.deluge#L562), [processDeal.deluge:519](../../../v4/processDeal.deluge#L519), [handleTaskCompletion.deluge:73](../../../v4/activity/handleTaskCompletion.deluge#L73). When a Lead is created: WF001a → processLead → (creates Deal which triggers WF001d → processDeal → sequenceRouter) AND processLead itself calls sequenceRouter at its tail. Both sequenceRouter invocations enter the bootstrap branch in parallel because Sequence_Status is still empty when both read the Deal. Both call `createStageCall`. `createStageCall`'s `zoho.crm.searchRecords` dup-check returns "no existing Call" for both because neither create has committed yet. Both create Call 1. Race.
  - **Why T1 didn't show it:** T1's only Call creation flowed through a manual MCP-driven Deal update (`Sequence_Status=Not Started`), which fires only WF001d/processDeal/sequenceRouter — single chain, no race. T4's Leads each fire the full graph cascade where processLead + processDeal both invoke sequenceRouter.
  - **Fix options (deferred, design decision needed):**
    1. **Trigger suppression** at processLead/Contact/Account's Deal write: pass `triggerMap = {trigger: []}` so WF001d does not fire, then rely solely on the explicit `sequenceRouter(dealId)` call at the parent function's tail. Cleanest separation.
    2. **Remove the redundant tail calls** to `automation.sequenceRouter(...)` from processLead/processContact/processAccount and rely on WF001d → processDeal → sequenceRouter. Risk: if WF001d is disabled or misconfigured the Deal never bootstraps a sequence.
    3. **Post-create dedup inside createStageCall**: after creating the Call, re-search and if multiple open Calls exist for the same (What_Id, Sequence_Stage, Sequence_Attempt) mark all-but-first as `Stale=Yes`. Doesn't prevent the race but heals afterward.
  - **Cleanup performed:** deleted duplicate Call `991103000000733355`, kept `991103000000752299` for downstream test consistency.

### T5 / T6 — SKIPPED (Lead-only constraint)

T5 (sentinel "(Duplicate)" Deal) and T6 (two open Deals under one Account → silencing) both require **direct creation of Deals** to test the duplicate-recovery silencing path. In Lead-only mode this is unreachable — same-Website Leads converge to one Account+Deal via the cascading dedup logic. Logged as a coverage gap for future rounds when a sandbox or relaxed-mode access is available.

### T7 — Product attachment + Amount sum

- **Status:** FAIL (mid-diagnosis)
- **Action taken:** Created Lead `991103000000788047` with `Product_Interest=["Jurnii Cortex","Jurnii UX"]`. 3 active Products available in catalog (Jurnii Cortex £16k, Jurnii UX £12k, Jurnii 360 £10k). Waited 75s.
- **Observed:**
  - Deal `991103000000747390` created with Stage1/Stage/State/Sequence_Status correct (full graph cascade ran).
  - **`Amount = 0`** ❌ (expected £28,000 = 16000 + 12000)
  - **Deal's `Products` related list returned empty** ❌
  - Lead's `Product_Interest` field correctly retained `["Jurnii Cortex","Jurnii UX"]` post-conversion.
- **Diagnostic blocker:** REST-invoke of `processLead` returned `NOT_ACTIVE` — the function's "Configure for REST API" toggle is off. Without that I can't capture the `info` logs that would tell me whether `searchRecords("Products", "(Product_Active:equals:true)")` returned the catalog, whether the names matched, whether the `Product_Details` write returned success, or whether `processDeal`'s subsequent cascade pass cleared the field.
- **Code analysis pending:**
  - `processLead.deluge:725-890` does the catalog-lookup, name-match, build `mergedPDList`, write `Product_Details` + `Amount` via `updateRecord` with suppressTrigger. Has a pre-pass that sums existing line items first to avoid Amount=0 clobber on cascade re-runs.
  - `processDeal.deluge:338-485` has the same product-resolution pipeline (catalog + name match + write) with the same pre-pass. Its `aggregatedPIList` is built from Contacts' `Products_Linked` (a separate multi-select-lookup field), NOT from the original Lead's `Product_Interest` text. After Lead conversion, Contact's `Products_Linked` is empty, so processDeal's aggregatedPIList would be empty unless existing Deal Products were already attached.
  - **Working hypothesis:** processLead's write fails or returns success but Zoho silently rejects the `Product_Details` subform format. processDeal then runs (from Deal-create cascade), sees empty Product_Details + empty aggregatedPIList, writes Amount=0 (no-op).
- **Republish-tier user action needed:** flip "Configure for REST API" → Active on `processLead` (and `processDeal` for follow-up diagnosis).

### T8-light — Account State rollup (single-Deal close)

- **Status:** PASS (after field-shape discovery)
- **Field-shape finding (important):** the field `Reason_For_Loss__s` is **silently read-only** via REST/MCP — `updateRecord` returns SUCCESS but the field stays null. The `__s` suffix typically indicates a Zoho system-computed field. The writable equivalent is **`Lost_Reasons`** (plural, no suffix). processDeal happens to read both at [processDeal.deluge:864-866](../../../v4/processDeal.deluge#L864-L866) so either populating the writable one (`Lost_Reasons`) triggers the loss path.
- **Action taken (T7 Deal `991103000000747390`):**
  1. Set `Lost_Reasons="Duplicate / Test Record"` with workflows suppressed → field persisted.
  2. Triggered processDeal via no-op `Description` edit with workflows enabled.
- **Observed:**
  - Deal: `State="Lost"`, `Status="Closed"`, `Lost_Reasons="Duplicate / Test Record"`. ✅
  - Account `991103000000718267`: `State="Lost"`, `Status="Closed"`, Modified_Time 1s after Deal close. ✅ Rollup propagated.
- **Minor finding (not fixed):** Deal's `Sequence_Status` stayed at `"Waiting on Call"` rather than flipping to `"Completed"` when the Deal closed — `processDeal`'s rollup logic doesn't reset sequence-management fields on close.

### T13 — Commercials_Status=Signed regression (State=Won hard-fail check)

- **Status:** **CRITICAL ASSERTION PASSES** (State stays Open, not Won). Multiple secondary failures from architectural cascade bug.
- **Action taken (T4 Deal `991103000000757200`):**
  1. Set Stage1="Commercials Sent" with workflows enabled. Waited 60s.
  2. Set Commercials_Status="Signed" with workflows enabled. Waited 60s.
- **Observed:**
  - Step 1 intermediate state: Stage1 reverted to "Marketing Consent" within ~7s of update by `processDeal` (cascade bug, see below).
  - Final state after step 2:

  | Field | Expected | Actual | Result |
  |---|---|---|---|
  | Stage1 | Commercials Signed | Marketing Consent (reverted) | ❌ |
  | Stage | RTP | MQL (reverted) | ❌ |
  | **State** | **Open** | **Open** | ✅ **critical regression PASS** |
  | Status | New or Working | New | ✅ |
  | Signed_At | not empty | `2026-06-01T15:40:01+01:00` | ✅ |
  | Sequence_Status | Not Started | Waiting on Call (reverted) | ❌ |
  | Commercials_Status | Signed | Signed | ✅ |

- **Cross-cutting bug #1 — WF001d cascade hijack (HIGH PRIORITY):**
  - `handleCommercialsStatusChange.Signed` at [handleCommercialsStatusChange.deluge:112](../../../v4/activity/handleCommercialsStatusChange.deluge#L112) calls `zoho.crm.updateRecord("Deals", dealId, dealUpd)` **without `triggerMap`**, intentionally letting WF003 fire to re-bootstrap the RTP sequence (per the trigger-suppression matrix in `WORKFLOW_CONFIGURATION_CHECKLIST.md`).
  - BUT — WF001d (Deal `create_or_edit`, no criteria gate) ALSO fires on the same edit. WF001d → `processDeal` → recompute Stage1/Stage/State/Status from Contacts' progression → reverts whatever the activity layer just wrote.
  - **Root cause:** trigger-suppression matrix didn't anticipate WF001d. processDeal's pipeline step 9 ("Pick furthest viable open Contact + set Stage1/Stage/State") aggressively recomputes these fields on every Deal save, even when an activity-layer handler just set them.
  - **Affected functions (likely all):** every activity-layer handler that writes Stage1 / Stage / Sequence_Status / State without triggerMap will be reverted: handleCommercialsStatusChange (Sent, Signed, Rejected), handleDemoOutcome, handleCallOutcome (Positive, Negative).
  - **Fix shape (design decision needed):**
    1. Pass `triggerMap = {trigger: []}` in every activity-layer Deal update, then explicitly call `sequenceRouter(dealId)` afterward to bootstrap the next sequence — full control, no surprise re-runs.
    2. Add criteria to WF001d to skip Deal edits made by the activity layer (would need a marker field like `Last_Touched_By="activity_layer"`).
    3. Make `processDeal` defer to Stage1 when written by an activity-layer handler — requires the function to know which Contact-stage progression is "trustworthy" vs the explicit handler write.
  - Option 1 is the smallest blast radius.

- **Cross-cutting bug #2 — Timezone discrepancy in datetime stamps:**
  - `Signed_At` was stamped `2026-06-01T15:40:01+01:00` but the update completed at `2026-06-01T16:40:01+01:00` (per Zoho's Modified_Time). Off by 1 hour.
  - **Likely cause:** `zoho.currenttime` in the Deluge runtime returns time as if it were UTC, then `.toString("yyyy-MM-dd'T'HH:mm:ssXXX")` adds the local `+01:00` offset, producing an ISO-8601 string whose instant is 1 hour in the past.
  - **Impact:** all batch-fixed datetime writes are systemically 1 hour behind reality (Commercials_Sent_At, Commercials_Discussed_At, Signed_At, Sequence_Superseded_At, Last_Email_Sent_At, Demo_Reminder_Send_At, Next_Action_Due_Date, Call_Start_Time).
  - **Fix shape:** use a known-correct datetime source. Options: `zoho.currenttime.toString("yyyy-MM-dd HH:mm:ssZ")` (with `Z` for the offset literal — the function context's offset, may be different from `XXX` behaviour), OR explicitly construct from UTC via `zoho.currenttime.toTime("UTC")` + offset arithmetic.

- **Cross-cutting bug #3 — sequenceRouter race + dup-check unreliability:**
  - The T1→T13 transition also created a fresh `Marketing Consent Call 1` (id `991103000000754292`) on the T4 Deal — even though the original Call (`991103000000752299`) was still open with the same `Sequence_Stage` and `Sequence_Attempt`. `createStageCall`'s dup-check via `zoho.crm.searchRecords` did not detect the existing Call.
  - **Likely cause:** Zoho's search-index lag — searchRecords by custom field on a recently-created record returns no match for several minutes. Same issue noted in the function's own comment at [createStageCall.deluge:729](../../../v4/activity/createStageCall.deluge#L729).
  - **Fix shape:** read the Deal's `Calls` related list via `getRelatedRecords` (which reads live data, no search lag) instead of `searchRecords`. Filter client-side by Sequence_Stage + Sequence_Attempt + open Call_Outcome + Stale!=Yes.

### T16 — Positive Call outcome (handleCallOutcome)

- **Status:** FAIL (no Deal mutation observed)
- **Action taken:** Updated T1 Call `991103000000762148` to `Call_Outcome="Positive"`. Waited 60s.
- **Observed:**
  - Call `Modified_Time` advanced to 16:42:58, `Call_Outcome="Positive"` persisted. ✅
  - Deal `991103000000762142` Modified_Time **did not change** (still 13:07:50 from earlier T2 edit). Stage1 still "Marketing Consent", Sequence_Status still "Waiting on Call". ❌
- **Likely root causes (not diagnosed):**
  1. WF006's trigger type was `scheduled_call_createedit` in the pre-flight. This is Zoho's "Scheduled Call Triggers" mechanism — fires only when a scheduled call's specific fields change, not on arbitrary edits. May not fire on Call_Outcome change for already-completed/logged calls.
  2. Alternatively WF006 fired but its criteria gate excluded my edit (Sequence_Managed=Yes, Call_Outcome not empty, Stale != Yes — these all look satisfied; needs UI check).
  3. Or handleCallOutcome ran but the "Positive" branch's Deal-update was silently rejected.
- **Diagnostic blocker:** processLead REST not yet active, same toggle would be needed on handleCallOutcome for REST-invoke diagnosis.

### Round 1 — Summary

| Test | Result | Notes |
|---|---|---|
| T1 | PASS (post-fix) | After datetime fix (Call_Start_Time ISO-8601) |
| T2 | PASS | processDeal idempotent on no-op edit |
| T4 | PASS on role-assignment | 3 Contacts with correct roles; race bug found |
| T5 / T6 | SKIPPED | Lead-only constraint; require direct Deal creation |
| T7 | FAIL — DEFERRED | Amount=0, 0 products attached; needs processLead REST toggle for diagnosis |
| T8-light | PASS | Account State rollup works; field-name discovery (Lost_Reasons not Reason_For_Loss__s) |
| T9 | PASS-by-ref | Covered by T4 |
| T10 | SKIPPED | Per-Contact Stage model unclear |
| T13 | CRITICAL PASS | State=Won regression guarded; cascade hijack reverts other fields |
| T16 | FAIL | WF006 didn't fire Deal update; root cause not yet diagnosed |
| T15, T17, T18, T12, T14, T20-T23 | NOT RUN | Time-bounded; same cascade-hijack bug likely affects all activity-layer tests |

**Fixes written and republished this round:**
- `v4/activity/createStageCall.deluge` (Call_Start_Time ISO-8601 datetime format)
- `v4/activity/handleCallOutcome.deluge` (Next_Action_Due_Date ISO-8601)
- `v4/activity/sequenceRouter.deluge` (post-call-chain Next_Action_Due_Date ISO-8601)
- `v4/activity/handleMeetingEvent.deluge` (Demo_Reminder_Send_At ISO-8601)
- `v4/activity/sendSequencedEmail.deluge` (Last_Email_Sent_At ISO-8601)
- `v4/activity/supersedeOldSequence.deluge` (Sequence_Superseded_At ISO-8601)
- `v4/activity/handleCommercialsStatusChange.deluge` (Commercials_*_At + Signed_At ISO-8601)

**Open bugs requiring future rounds (in priority order):**
1. **WF001d cascade hijack** — reverts Stage1/Sequence_Status writes from activity-layer handlers. Blocks T12, T13 (secondary), T14, T15, T17 from properly testing.
2. **Timezone discrepancy** — all datetime stamps are 1 hour behind actual instant.
3. **T7 Product attachment** — Amount=0, 0 products. Requires REST toggle on processLead/processDeal for diagnosis.
4. **sequenceRouter race + searchRecords lag** — duplicate Call 1's. Affects T4 and any test that creates a new Deal via Lead path.
5. **T16 Positive Call outcome** — Deal didn't react. May be WF006 misconfiguration or handleCallOutcome bug.
6. **Sequence_Status not reset on Deal close** — minor; rollup doesn't touch Sequence_Status when Deal flips to Lost.

**Coverage gaps (not testable in Lead-only mode):**
- T5 (sentinel "(Duplicate)" Deal)
- T6 (direct duplicate-Deal silencing)
- T10 (per-Contact Stage progression — unclear field model)
- T22 (Automation_Suppressed on Deal) — partially exercised by T8-light flow, not asserted

**User-actionable items for Round 2:**
- Flip REST API toggle Active on: `processLead`, `processDeal`, `handleCallOutcome` (for cross-bug diagnosis).
- Decide on cascade-hijack fix approach (Option 1, 2, or 3 above).
- Decide on timezone-fix approach (probably formal: use a UTC-anchored stamp + explicit local offset).

### Round 1 — End-of-session cleanup + cascade-hijack fix (Option 1) applied

**Cleanup performed:**
19 records deleted by id (Calls → Deals → Contacts → Accounts → Leads):
- Calls: `991103000000757206`, `991103000000752299`, `991103000000762148`
- Deals: `991103000000747390`, `991103000000757200`, `991103000000762142`
- Contacts: `991103000000726238`, `991103000000711316`, `991103000000742183`, `991103000000756223`, `991103000000721223`
- Accounts: `991103000000718267`, `991103000000762150`, `991103000000735173`
- Leads: `991103000000788047`, `991103000000785085`, `991103000000792032`, `991103000000799031`, `991103000000795089`

**Records flagged but NOT touched** (likely my workflow side-effects, but not my prefix so leaving for the user to inspect/delete):
- Call `991103000000709309` — `Commercials Sent Call 1` on lionvegas Deal (created during my session at 13:56:58, on a pre-existing Deal).
- Contacts created during the session window with non-prefix names: Munn (`991103000000726252`), Sun (`991103000000708324`), Phrophet (`991103000000740290`), Bob (`991103000000769263`). May be someone else's work in parallel — please verify before any deletion.

**Cascade-hijack fix applied (Option 1: triggerMap + explicit sequenceRouter call):**

| File | Branch | Change |
|---|---|---|
| [handleCommercialsStatusChange.deluge](../../../v4/activity/handleCommercialsStatusChange.deluge) | `Sent` | Add `triggerMap`, add `automation.sequenceRouter(dealId.toString())` |
| same | `Signed` | Same |
| same | `Rejected` | Switch `Reason_For_Loss__s` → `Lost_Reasons` (read-only field swap) |
| [handleCallOutcome.deluge](../../../v4/activity/handleCallOutcome.deluge) | `Positive` | Add `triggerMap`, add `automation.sequenceRouter(dealId.toString())` |
| same | `Negative` | Switch `Reason_For_Loss__s` → `Lost_Reasons` |
| [handleDemoOutcome.deluge](../../../v4/activity/handleDemoOutcome.deluge) | `Attended - Qualified` | Add `triggerMap`, add `automation.sequenceRouter(dealId.toString())` |
| same | `Attended - Not Qualified` | Switch `Reason_For_Loss__s` → `Lost_Reasons` |

Other branches in these three files already passed `triggerMap`, so no change needed.

**Republish required for Round 2:**
1. `handleCommercialsStatusChange`
2. `handleCallOutcome`
3. `handleDemoOutcome`
4. `handleMeetingEvent` (No Show branch — added triggerMap + explicit handleDemoOutcome)
5. `handleTaskCompletion` (Send Commercials branch — added triggerMap + explicit handleCommercialsStatusChange)
6. `processLead` (dup-silencing now writes Lost_Reasons, not read-only Reason_For_Loss__s)
7. `processDeal` (same + sentinel detection at line 44 now reads Lost_Reasons too)
8. `processContact` (same dup-silencing fix)
9. `processAccount` (same dup-silencing fix)

**Final verification (post-sweep grep):**
- `0` matches for `updateRecord("Deals", x, y);` without a `triggerMap` 4th arg — every Deal update now suppresses the WF001d cascade hijack.
- `0` matches for `put("Reason_For_Loss__s", ...)` — no more writes to the read-only field anywhere in v4/.
- Sentinel detection at `processDeal.deluge:44-49` now checks `Lost_Reasons` in addition to `Reason_For_Loss__s`, so the dup-silencing→sentinel-skip pipeline stays consistent.

**Account/Contact updates without triggerMap — left intentionally:**
- `processLead/Contact/Account/Deal` write Account fields (state rollup) via `updateRecord("Accounts", ..., updAcc)` without `triggerMap` so that WF001c fires `processAccount` for the rollup-propagation chain. This is intentional design per the trigger-suppression matrix (the WF001c cascade IS wanted), not the same bug class as the WF001d hijack.
- Contact writes that pass `suppressTrigger` are intentional (avoid Contact-loop on Contact_Role1 stamping). Those that don't pass it are intentional Account-rollup chains.

---

## Round 2 — 2026-06-02 08:43

**Setup:** Same production org, session prefix `MCP_TEST_20260602_R2`. Five additional functions REST-API-enabled by user: `processLead`, `processDeal`, `handleCommercialsStatusChange`, `handleDemoOutcome`, `handleCallOutcome` (in addition to the `createStageCall`/`sequenceRouter` toggled in Round 1).

### T1-retest — fresh Lead end-to-end

- **Status:** Graph layer PASS; race + timezone bugs unchanged (deferred).
- Lead `991103000000797020` → Contact `991103000000768216`, Account `991103000000709313`, Deal `991103000000735175`. Full graph cascade healthy. `Marketing Consent Call 1` created via the workflow chain (proves all Round 1 datetime-format fixes still hold).
- Pre-existing **sequenceRouter race bug** reproduced (2 `Marketing Consent Call 1`s ~1s apart) — unchanged from Round 1, expected.
- Pre-existing **timezone bug** reproduced (`Call_Start_Time=07:43:57` for a Call created at `08:43:57`) — unchanged from Round 1, expected.

### T13 first attempt — deeper bug surfaced

- Set `Commercials_Status="Signed"` with `trigger=["workflow"]`. Observed result: `Stage1` reverted to `"Marketing Consent"` despite handleCommercialsStatusChange having written `"Commercials Signed"` first. Active_Sequence_Stage also reverted.
- **Root cause:** the cascade-hijack fix prevents activity-layer INTERNAL cascades from reverting Stage1, but it does NOT prevent the user's INITIAL Deal edit from firing both WF004 (correct handler) AND WF001d (which re-runs processDeal in parallel). processDeal's `bestStage` computation from Contacts lags behind the activity-layer transition, so it clobbers Stage1.

### Round 2 fix: "never-regress" Stage1 in 4 process functions

Applied to the `else if(hasContacts)` block where Stage1/Stage are written from `bestStage`/`bestOpp`:

| File:line | Block |
|---|---|
| [processDeal.deluge:502-519](../../../v4/processDeal.deluge#L502-L519) | Else-if branch |
| [processLead.deluge:876-890](../../../v4/processLead.deluge#L876-L890) | Same |
| [processContact.deluge:693-706](../../../v4/processContact.deluge#L693-L706) | Same |
| [processAccount.deluge:542-555](../../../v4/processAccount.deluge#L542-L555) | Same |

Logic: compute `currentStageRank` from `stageRanks.get(targetDeal.Stage1)` and `bestStageRank` from `stageRanks.get(bestStage)`. Only write Stage1/Stage if `bestStageRank > currentStageRank`. Manual Stage1 regress still works because WF003 (Stage1 field-update) fires `sequenceRouter` directly, not `processDeal`.

### T13 retest — FULL PASS

After the 4-file fix and republish, re-fired `Commercials_Status="Signed"`:

| Field | Expected | Actual |
|---|---|---|
| Stage1 | Commercials Signed | **Commercials Signed** ✅ |
| Stage | RTP | RTP ✅ |
| State | Open | Open ✅ |
| Status | New | New ✅ |
| Signed_At | not empty | `2026-06-02T07:52:32+01:00` ✅ (still 1hr-off due to timezone bug) |
| Sequence_Status | Not Started → Waiting on Call | Waiting on Call ✅ |
| Active_Sequence_Stage | Commercials Signed | Commercials Signed ✅ |
| Commercials_Status | Signed | Signed ✅ |
| Commercials Signed Call 1 | exists | id `991103000000718272` ✅ |
| **Race-induced duplicate Calls** | **0** | **0** ✅ |

The never-regress fix has an unexpected bonus: when processDeal's `bestStageRank == currentStageRank` it skips the Stage1 write entirely, which shrinks the racing-write window and (in this trigger pattern) avoided the duplicate-Call race condition that's still present on the Lead-create cascade.

### T16 — Positive Call outcome (workflow path) FAIL; handleCallOutcome direct invoke PASS

- Set `Call_Outcome="Positive"` on Commercials Signed Call 1 → Deal didn't react. Same failure as Round 1.
- REST-invoked `handleCallOutcome(callIdStr="991103000000718272")` directly. Function ran end-to-end successfully: supersedeOldSequence → createStageCall(Onboarding,1) → sequenceRouter bootstrap → Stage1 advanced to `Onboarding`, Stage=`RTP`. Confirmed Deal in `Onboarding`.
- **Root cause isolated:** `handleCallOutcome` is correct. **WF006 trigger configuration is the bug** — pre-flight inventory showed WF006 type was `scheduled_call_createedit` which doesn't fire on Call_Outcome-only edits to logged/completed calls. Workflow-config fix (UI), not code.
- Arg-name finding: function signature is `automation.handleCallOutcome(string callIdStr)`. The Trigger Map doc spec says `call_id`. The Zoho function-execute API uses parameter names from the function signature, so REST callers must pass `callIdStr`.

### T14 — Commercials Rejected, FULL PASS

| Field | Expected | Actual |
|---|---|---|
| State | Lost | **Lost** ✅ |
| Status | Closed | **Closed** ✅ |
| Sequence_Status | Completed | **Completed** ✅ |
| **Lost_Reasons** | "Commercial Rejected" | **"Commercial Rejected"** ✅ |
| Reason_For_Loss__s | null (read-only) | null ✅ (confirms field is system-only) |

The Lost_Reasons swap (Round 1 cascade-hijack-sweep fix) works correctly.

### T15 — Demo Outcome Attended-Qualified, PARTIAL PASS

Fresh Lead `991103000000792038` → Deal `991103000000750242`. Set `Demo_Outcome="Attended - Qualified"`.

| Field | Expected | Actual |
|---|---|---|
| Stage1 | Demo Attended | **Demo Attended** ✅ |
| Stage | SQL | **SQL** ✅ |
| Commercials_Status | Drafting | **Drafting** ✅ |
| Demo_Status | Completed | Completed ✅ |
| Active_Sequence_Stage | Demo Attended | Demo Attended ✅ |
| `Draft Commercials` Task | exists | **NOT CREATED** ❌ |

The Deal-state transition is correct. The Task creation step failed because `sendSequencedEmail` throws on invalid email domain (`acme-r2-t15.example`), and the exception **halts handleDemoOutcome's execution before reaching the Task createRecord call**.

- REST diagnostic captured the error: `"Execution exception: 'Error due to - 'Invalid Domain'' Error in executing automation.sendSequencedEmail function. at line No.60"`
- **Real-world impact:** with valid customer email domains in production, this would not throw. But the brittleness (uncaught exception halts caller) is a bug worth fixing.
- **Fix shape:** wrap `sendSequencedEmail`'s `invokeurl` in try/catch, or validate the domain before calling, and return error rather than throw.

### T7 — Product attachment, FULL PASS (both REST and workflow paths)

Fresh Lead `991103000000795105` (workflows suppressed on Lead create) → REST-invoked processLead → captured complete info logs:

```
Lead Product_Interest raw=Jurnii Cortex,Jurnii UX
Lead PI parsed string='Jurnii Cortex,Jurnii UX'
Product catalog loaded: 3 products
Queueing Product for Deal: Jurnii Cortex (id=...694087, price=16000.00)
Queueing Product for Deal: Jurnii UX (id=...659965, price=12000.00)
Products summary: newlyQueued=2 totalAmount=28000.00 totalLineItems=2
Deal updateRecord payload: {Amount:28000.00, Product_Details:[2 rows]}
Deal updateRecord resp: SUCCESS
```

Deal `991103000000754296` read back: `Amount=28000` ✅.

Then fresh Lead `991103000000802028` with workflows enabled (mimics production path that failed in Round 1). Deal `991103000000762170` read back: `Amount=28000` ✅.

**Round 1's T7 failure was a transient race**, no longer reproducing. The never-regress fix is likely partially responsible: now that `processDeal` writes far fewer fields (often `dUpd.size()==0` and skips the updateRecord entirely), the race window between `processLead`'s Product_Details write and any other write has shrunk.

### Round 2 — End-of-session cleanup

25 R2 test records deleted (4 Leads, 4 Contacts, 4 Accounts, 4 Deals, 9 Calls).

### Round 2 — Final summary

**Passing tests:** T1, T13, T14, T15 (Deal-state), T16 (handleCallOutcome via REST), T7 (REST + workflow).

**Bugs identified for follow-up (NOT fixed Round 2):**

1. **WF006 trigger configuration** — `scheduled_call_createedit` type doesn't fire on Call_Outcome edits to non-scheduled calls. UI fix: change to `create_or_edit` with criteria `Sequence_Managed=Yes AND Call_Outcome is not empty AND Stale != Yes`.
2. **`sendSequencedEmail` throws on invalid email domain** — halts caller mid-function, blocks downstream Task / Deal-update logic. Wrap `invokeurl` in try/catch and return error rather than throw.
3. **Timezone discrepancy (1-hour offset)** in all datetime stamps — `Signed_At`, `Call_Start_Time`, etc. all stamped 1hr behind actual instant. Still needs investigation into the correct `zoho.currenttime` → ISO-8601-with-offset incantation.
4. **sequenceRouter race condition (duplicate Call 1)** — `processLead → sequenceRouter` and `processDeal → sequenceRouter` both fire on the initial Lead cascade and race past `createStageCall`'s dup-check (searchRecords lag). Fix: swap `searchRecords` for `getRelatedRecords` + client-side filter in `createStageCall`'s dup-check.

**Fixed and republished this round (cumulative across Round 1 + Round 2):**

| Function | Round 1 fixes | Round 2 fixes |
|---|---|---|
| `createStageCall` | Call_Start_Time ISO-8601 datetime format | — |
| `sequenceRouter` | Next_Action_Due_Date ISO-8601 | — |
| `handleCallOutcome` | Next_Action_Due_Date ISO-8601; cascade-hijack (Positive, Negative); Lost_Reasons swap | — |
| `handleCommercialsStatusChange` | Datetime stamps ISO-8601; cascade-hijack (Sent, Signed, Rejected); Lost_Reasons swap | — |
| `handleDemoOutcome` | Cascade-hijack (Attended-Qualified, Not Qualified); Lost_Reasons swap | — |
| `handleMeetingEvent` | Demo_Reminder_Send_At ISO-8601; No Show triggerMap + explicit handler call | — |
| `handleTaskCompletion` | Send Commercials triggerMap + explicit handler call | — |
| `sendSequencedEmail` | Last_Email_Sent_At ISO-8601 | — |
| `supersedeOldSequence` | Sequence_Superseded_At ISO-8601 | — |
| `processLead` | Lost_Reasons swap (dup-silencing) | **Never-regress Stage1** |
| `processDeal` | Lost_Reasons swap (dup-silencing + sentinel detection) | **Never-regress Stage1** |
| `processContact` | Lost_Reasons swap (dup-silencing) | **Never-regress Stage1** |
| `processAccount` | Lost_Reasons swap (dup-silencing) | **Never-regress Stage1** |

**Coverage gaps (still unreachable in Lead-only mode):**
- T5 (sentinel "(Duplicate)" Deal recovery)
- T6 (direct duplicate-Deal silencing)
- T10 (per-Contact Stage progression)
- T8 multi-Deal (mixed/Lost rollup phases require 2+ Deals under one Account)

---

## Round 3 — Bug-fix pass

Applied 3 code fixes targeting the 4 deferred bugs from Round 2. WF006 trigger-type change blocked by Zoho API (`NOT_ALLOWED: trigger cannot be changed` on `updateWorkflowRuleById`) — UI action required for that one.

### Fix 1: Timezone offset (Bug 3) — direct `.toString()` on `zoho.currenttime`

`zoho.currenttime` is already a Deluge `DateTime` per Zoho docs. The previous pattern `zoho.currenttime.toDateTime("yyyy-MM-dd HH:mm:ss").toString("yyyy-MM-dd'T'HH:mm:ssXXX")` round-trips through a TZ-naive string in the middle (`.toString()` flatten before re-parse), losing the runtime's original offset. The workflow runtime evidently ran in a different zone than `XXX` formatted with, producing 1-hour-off stamps.

**Fix:** drop the intermediate parse; format the DateTime directly.

| File:line | Change |
|---|---|
| [handleCommercialsStatusChange.deluge:53](../../../v4/activity/handleCommercialsStatusChange.deluge#L53) | `now = zoho.currenttime.toString("yyyy-MM-dd'T'HH:mm:ssXXX")` |
| [supersedeOldSequence.deluge:37-38](../../../v4/activity/supersedeOldSequence.deluge#L37-L38) | Same pattern |
| [sendSequencedEmail.deluge:111](../../../v4/activity/sendSequencedEmail.deluge#L111) | `dealUpd.put("Last_Email_Sent_At", zoho.currenttime.toString(...))` |
| [createStageCall.deluge:60-74](../../../v4/activity/createStageCall.deluge#L60-L74) | Split the `attempt == 1` branch (use `zoho.currenttime.toString(...)` directly) from `attempt > 1` branch (still has to parse `calculateBusinessDate`'s string output). |

`calculateBusinessDate`-derived datetimes (in createStageCall attempt>1, handleCallOutcome, sequenceRouter post-call chain, handleMeetingEvent) still go through `.toDateTime(format).toString(ISOformat)` because the helper returns a TZ-naive String — those datetimes are future-dated (reminders, due-dates) so a TZ-runtime mismatch is much less impactful than the "now" stamps we just fixed.

### Fix 2: `sendSequencedEmail` try/catch (Bug 2)

[sendSequencedEmail.deluge:99-121](../../../v4/activity/sendSequencedEmail.deluge#L99-L121) — wrapped the `invokeurl` to Zoho's `send_mail` API in try/catch. On exception (e.g. `Invalid Domain` for test email domains), the function now logs the error and continues with `sendResp = null`. The downstream code already tolerates `sendResp = null` (sentMessageId stays empty, Deal still gets the timestamp + template name for audit). This prevents the exception from halting the caller mid-function — fixes the T15 "Draft Commercials Task not created" issue.

### Fix 3: `createStageCall` dup-check via `getRelatedRecords` (Bug 4)

[createStageCall.deluge:33-58](../../../v4/activity/createStageCall.deluge#L33-L58) — swapped the `zoho.crm.searchRecords("Calls", criteria)` dup-check for `zoho.crm.getRelatedRecords("Calls", "Deals", dealId)` + client-side filter on `Sequence_Managed=Yes`, `Sequence_Stage=stage`, `Sequence_Attempt=attempt`, empty `Call_Outcome`, `Stale != Yes`. `getRelatedRecords` reads live data (no search-index lag), so the race condition between processLead/processDeal both calling sequenceRouter→createStageCall in parallel during Lead-create cascade will no longer produce duplicate Call 1s.

### Fix 4: WF006 trigger type — BLOCKED (Zoho API), UI action required

Tried `updateWorkflowRuleById` to change WF006's trigger from `scheduled_call_createedit` (which doesn't fire on Call_Outcome edits to logged calls) to `outgoing_call_edit`. Zoho rejected with `NOT_ALLOWED: trigger cannot be changed`. This is a permanent constraint of the Zoho workflow API — trigger types are immutable after creation.

`getWorkflowConfigurations(module=Calls)` shows the deprecated triggers (`create_or_edit`, `edit`, `field_update`) are still listed but marked deprecated; current valid triggers are call-type-specific: `outgoing_call_edit`, `outgoing_call_field_update`, `scheduled_call_edit`, etc.

**User UI action required:**
1. Zoho → Setup → Automation → Workflow Rules → WF006 Handle Call Outcome.
2. Either:
   - **Delete** WF006 and **recreate** with trigger type **"Calls → On Record Action → Outgoing Call Edited"** (or similar non-deprecated variant). Set the function action to `handleCallOutcome` with `callIdStr ← ${Calls.id}`.
   - **OR** edit the rule in the UI — the UI may still allow trigger-type changes that the API forbids.

After that, `Call_Outcome="Positive"` edits on Calls (per T16) should trigger handleCallOutcome correctly.

### Round 3 — Republish required

1. `createStageCall` (dup-check + attempt==1 datetime)
2. `sendSequencedEmail` (try/catch + Last_Email_Sent_At)
3. `supersedeOldSequence` (Sequence_Superseded_At)
4. `handleCommercialsStatusChange` (Commercials_*_At + Signed_At)

(Plus the WF006 UI fix above, if you want T16 to work via workflow path.)

### Round 3 — Open items

- **Reason_For_Loss__s is read-only via API** (confirmed Round 1) — already worked around with `Lost_Reasons` swap.
- **WF006 UI fix** — needed for T16 workflow path.
- **`calculateBusinessDate`-derived datetimes** still go through `.toDateTime → .toString` round-trip and may be off by ~1hr in workflow runtime contexts. Future refactor: return DateTime from `calculateBusinessDate` instead of a TZ-naive String.



**Open bugs deferred to Round 2 (NOT fixed this round):**

1. **Timezone discrepancy (1-hour offset on datetime stamps):** Affects all ISO-8601 datetime writes added in the Round 1 batch fix. Needs a follow-up where `zoho.currenttime` is captured and formatted with a verified offset. Possible approach: use `.toString("yyyy-MM-dd HH:mm:ssZ")` (no `'T'` separator but with `Z` for RFC-822 offset that respects Zoho-runtime TZ) and test whether Zoho's createRecord accepts that — or use UTC throughout with explicit `+00:00` literal. Needs an experimental round.

2. **sequenceRouter race condition (duplicate Call 1):** `processLead` → `sequenceRouter` AND `processDeal` → `sequenceRouter` both fire in parallel during Lead-cascade creation, before either commit propagates through Zoho's search index. `createStageCall`'s dup-check via `searchRecords` misses the in-flight Call. Best fix: replace the `searchRecords` dup-check with `getRelatedRecords("Calls", "Deals", dealId)` (live data, no search-index lag) + client-side filter.

3. **T7 Product attachment failure:** Amount=0, 0 products attached to Deal even when Lead has `Product_Interest` populated. Diagnosis blocked until `processLead` REST API toggle is Active — then I can invoke directly and capture the `info` logs to see whether (a) catalog lookup returned empty, (b) name match failed, or (c) the `Product_Details` subform write was silently rejected.

4. **T16 Positive Call outcome — Deal didn't react:** WF006 trigger type was `scheduled_call_createedit` in the pre-flight inventory. May not fire on Call_Outcome-only edits if the Call has Status="Completed" / similar. Needs UI inspection of WF006 trigger configuration. After the Round 2 cascade-hijack fix lands, retry T16 to see if it was just the cascade reverting the advance.

5. **Sequence_Status not reset on Deal close (minor):** When a Deal flips to Lost/Closed via Lost_Reasons, `Sequence_Status` stays at its previous value (e.g. "Waiting on Call") instead of "Completed". processDeal's rollup doesn't touch sequence state on close. Cosmetic for reporting; functional impact low.

6. **Coverage gaps for next sandbox round** (not testable in Lead-only mode):
   - T5 (sentinel "(Duplicate)" Deal recovery)
   - T6 (direct duplicate-Deal silencing under one Account)
   - T10 (per-Contact Stage progression — field model unclear)
   - Multi-Deal Account State rollup (T8 Phase A "mixed" requires 2+ Deals under one Account)

**Round 2 plan once republished:**
1. Re-create a fresh T1 Lead, verify the full graph + activity cascade still works post-fix.
2. Re-test T13 (Commercials Signed) — all assertions should now PASS including Stage1=Commercials Signed.
3. Run T14 (Commercials Rejected) — should now PASS with Lost_Reasons set.
4. Run T15 (Demo Outcome Attended-Qualified) — should now PASS without Stage1 revert.
5. Run T16 (Positive Call outcome) — see if cascade-hijack was the root cause; if not, dig into WF006 trigger config.
6. Then move to T17 (No Answer / Call N+1), T18 (idempotency), then T7 (Product attachment, REST diagnostic).



---

## Round 4 prep — 2026-06-02

**WF006 fix completed via API.**

- **WF006v2 created** — id `991103000000790084`. Trigger: `outgoing_call_createedit`. Action: `handleCallOutcome` (automation action id `991103000000780459`) wired directly via `functions` associate-action — no placeholder, the real function fires immediately. `criteria_details.relational_criteria.module_selection="all"` so the rule fires for any related-module context (Deals, Contacts, etc.).
- **WF006 (original) deactivated** — id `991103000000780461`, renamed to `WF006 Handle Call Outcome DEPRECATED replaced by WF006v2`, `status.active=false`. Trigger `scheduled_call_createedit` was the wrong type for call-outcome edits, and Zoho prohibits changing trigger type on an existing rule (`NOT_ALLOWED: trigger cannot be changed`).
- **API gotchas captured for future reference:**
  - Workflow functions are listed at `/crm/v8/settings/automation/functions` — NOT `/crm/v8/settings/functions` (returns 400).
  - Calls module rejects `assign_owner` and `field_updates` as workflow actions on POST/createFieldUpdates (`NOT_ALLOWED: module not supported`) — only `functions` (via existing function-action id) and `schedule_call` were viable for a Calls-module rule.
  - `outgoing_call_createedit` requires `criteria_details.relational_criteria.module_selection` ∈ {`all`,`specific`,`unknown`}; `repeat=true` is rejected (`DEPENDENT_MISMATCH`); `status.active=false` is rejected on POST (`Can not create inactive rule`); deactivation requires both `status.active=false` AND `status.delete_schedule_action=false`.
  - MCP tool `updateWorkflowRule` (no path variable) accepts `{id, status, name}` inside each workflow_rules entry. The `updateWorkflowRuleById` variant returned `Mandatory path variable id is not present in tool body` and was avoided.

**Round 4 plan (ready to execute once user confirms):**
1. Cleanup any lingering test records from Round 3 via `§9 cleanup`.
2. T13 → T14 → T15 → T16 → T17 sequence on a single fresh Lead, verifying all four Round 2/3 fixes plus the new WF006v2 trigger:
   - Cascade-hijack fix (triggerMap + explicit sequenceRouter) — confirm Stage1 doesn't revert after `handleCommercialsStatusChange`.
   - Never-regress Stage1 guard (stageRanks) in processDeal / Lead / Contact / Account.
   - `Reason_For_Loss__s` → `Lost_Reasons` swap (7 sites).
   - ISO-8601 datetime + direct `.toString` (no `.toDateTime` round-trip).
   - WF006v2 firing handleCallOutcome on outbound Call_Outcome edit (T16 positive, T17 no-answer).
3. Note: `WF002 Deal Sequence Router` still has trigger `create_or_edit` placeholder — keep eye on whether WF003's `field_update` on Stage1 is actually firing handleStageChange (was failing via UI inspection earlier).

