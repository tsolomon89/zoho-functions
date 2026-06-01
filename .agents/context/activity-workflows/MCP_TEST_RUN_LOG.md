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





