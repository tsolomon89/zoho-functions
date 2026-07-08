# v6 Activity Field Cleanup — Execution Plan (awaiting approval)

Companion to `ACTIVITY_FIELD_DEPENDENCY_AUDIT.md`. Four layers, sequenced. **No code committed, no
field deleted, no record backfilled.** Layer 1–2 are admin/metadata (reversible); Layer 3 is the code
diff plan that must be approved before any edit; Layer 4 (deletion) is explicitly deferred.

---

## Layer 1 — User-surface / layout & profile hardening (reversible, do first)

Single `Standard` layout per module shared by **Administrator / Standard / Team User**. There is no
rep-only layout, so control is via **field-level profile permissions** (Setup → Modules and Fields →
[module] → each field → *Edit Properties / Set Permission* → Read Only for Standard & Team User) plus
layout removal for dead fields. Administrator keeps full edit.

### Tasks
- **Keep visible + editable (reps):** `Task_State`, `Task_Lost_Reasons`, `Task_Sequence_Type` (activation), `Task_Contract_Products/Brands/Date_Start/Date_End/Frequency`, `Description` (read), `Subject` (read).
- **Read-only for Standard + Team User:** `Task_Type`, `Task_Status`, native `Status`, `Task_Sequence_Managed`, `Task_Sequence_Stage`, `Blocks_Sequence`, `Task_Stage`, `Task_Pipeline`, `Task_Opportunity`, `Due_Date`.
- **Remove from layout (dead):** `Task_Outcome`.

### Calls
- **Keep visible + editable:** `Call_Task_State`, `Call_Task_Lost_Reasons`, `Next_Follow_Up_Date`, `Call_Task_Contract_*`, `Description` (read), `Subject` (read).
- **Read-only for Standard + Team User:** `Sequence_Managed`, `Sequence_Stage`, `Sequence_Attempt`, `Call_Task_Status`, `Outgoing_Call_Status`, `Call_Task_Stage`, `Call_Task_Pipeline`, `Call_Task_Opportunity`, `Call_Purpose_Detail`, `Call_Type`, `Call_Start_Time`.
- **Remove from layout (dead):** `Call_Outcome`, `Block_Email_Until_Done`.

### Meetings / Events
- **Keep visible + editable:** `Meeting_Task_State`, `Meeting_Task_Lost_Reasons`, `Meeting_Task_Stage` (optional type override), `Meeting_Task_Contract_*`, `Start_DateTime`, `End_DateTime`, `Description` (read).
- **Read-only for Standard + Team User:** `Meeting_Task_Status`, `Reminder_Send_At`, `Meeting_Task_Pipeline`, `Meeting_Task_Opportunity`.
- **Remove from layout (dead):** `Meeting_Status`, `Meeting_Type`, `Meeting_Outcome`, `Follow_Up_Required`, `Follow_Up_Stage`, `Check_In_State`, `Check_In_Status`.

> All fields stay **physically present**. No deletion. Fully reversible (re-grant edit / re-add to layout).
> Execution note: these are Zoho **UI/metadata** operations. The available MCP tools do not safely edit
> per-profile field permissions or layout sections (no non-destructive layout-write tool), so this layer
> is delivered as an admin apply-spec unless you explicitly want me to attempt API writes.

## Layer 2 — Metadata corrections (admin, reversible)
1. **P0 Contract Products picklists** (`Task_/Call_/Meeting_Task_Contract_Products`): replace the 6 deactivated variant values with the 4 canonical active names — **Jurnii 360, Jurnii Cortex, Jurnii UX, Partnership** (required for the commercial "Quote on Won" path to work; see the description audit).
2. **`Calls.Sequence_Stage` picklist**: add the canonical stage values (Marketing Consent, Demo Booking, Demo Confirmation, Demo Hosted, Proposal Preparation, Commercial Agreement, Onboarding, Renewal). The field already stores canonical values via API; the picklist is stale. Keep old values until records are migrated/re-uploaded, then prune.
3. **Label fixes:** `Meeting_Task_Opportunity` ("Meeting  Task Opportunity") and `Meeting_Task_Contract_Products` ("Meeting Task Contract  Products") — remove the double spaces.

---

## Layer 3 — Code diff plan (APPROVAL REQUIRED before editing; you publish)

**Git:** work on a new branch `codex/activity-field-cleanup` off `main` (not committed until you approve;
Deluge published manually by you before commit, per house rule).

### 3.1 `Blocks_Sequence` → computed `isBlockingTask` (Phase A: replace reads, keep writes)

**Files/branches touched:** `v6/activity/routeContactSequence.deluge` — two read sites only.

**Predicate (inlined at each site; no new function to publish):**
```
btManaged   = ifnull(t.get("Task_Sequence_Managed"), false).toString();   // "true"
btType      = ifnull(t.get("Task_Type"), "").toString();
btStatus    = ifnull(t.get("Status"), "").toString();                     // native
btTaskStat  = ifnull(t.get("Task_Status"), "").toString();               // mirror
btSeqStage  = ifnull(t.get("Task_Sequence_Stage"), "").toString();
isBlocking  = (btManaged == "true"
               && btType != "Scheduled Send" && btType != "Email Sent"
               && btStatus != "Completed" && btStatus != "Cancelled" && btStatus != "Deferred"
               && btTaskStat != "Closed");
```

**Site 1 — resume guard, `routeContactSequence.deluge:~324-329`:**
- *Before:* `... ifnull(bt.get("Blocks_Sequence"),"No")=="Yes" && btStatus not in (Completed/Cancelled/Deferred) && (btSeqStage=="" || btSeqStage==stage)`
- *After:* compute `isBlocking` from `bt`, then `if(btWho==contactId && isBlocking && (btSeqStage=="" || btSeqStage==stage)) { blocked }`.

**Site 2 — dispatch gate, `routeContactSequence.deluge:~1136-1141`:**
- *Before:* `... ifnull(rt.get("Blocks_Sequence"),"No")=="Yes" && rtStatus not in (...)`
- *After:* compute `isBlocking` from `rt`, then `if(rtWho==contactId && isBlocking) { suppressOuter=true }`. (No stage-scope here, preserving current behavior.)

**KEY RISK + mitigation (must smoke):** the two scans use `getRelatedRecords("Tasks","Deals",dealId)`
with a `searchRecords` fallback. The predicate needs `Task_Type` + `Task_Sequence_Managed` + `Task_Status`
to be present on each fetched task. `Blocks_Sequence` (today) needs fewer fields. If `getRelatedRecords`
returns a **field-limited** view, the predicate could misfire. Mitigation options (pick in review):
(a) switch these two scans to `searchRecords` (returns full records), or (b) `getRecordById` each
candidate before evaluating. **Phase A keeps writing `Blocks_Sequence`**, so nothing is lost if we revert.

**Not touched in Phase A:** all `Blocks_Sequence` writes stay. Field stays present, set read-only (Layer 1).
Phase B (separate approval) removes the writes; Phase C (much later) deletes the field.

### 3.2 Remove dead `Block_Email_Until_Done` write

**File:** `v6/activity/routeContactSequence.deluge:1238`.
- *Before:* `callMap.put("Block_Email_Until_Done", "Yes");`
- *After:* line deleted. Zero reads, zero criteria → no behavior change. Field stays present (Layer 1 removes from layout); delete later.

### 3.3 Hardened activation model (Task_Sequence_Type = parameter, Task_State = Won = commit)

**File/branch:** `v6/activity/handleTaskCompletion.deluge` — the `if(tType == "Sequence Activation")` branch (~L125-191). **No workflow change** (WF008 already fires on all edits).

**New branch order:**
1. Keep already-processed idempotency: `if(taskState=="Won" && Task_Status=="Closed") return;`.
2. **NEW — commit gate:** `if(taskState != "Won") { log "activation_awaiting_commit"; return; }` → editing `Task_Sequence_Type` alone (State still Open) is now a **no-op**.
3. **NEW — route-required-on-commit:** `routeType = taskSeqType; if(routeType not in {Email,Call,Manual}) { updateRecord Task {Task_State:"Open", Task_Status:"Working", Status:"In Progress"} noTrigger; createAuxTask(contact, deal, "Manual Review", "[activation_no_route] Activation set Won without choosing Task Sequence Type. Choose Email / Call / Manual, then set Task State = Won again."); log "activation_no_route"; return; }`.
4. Keep D1 sibling-dedupe (now runs only on the Won commit).
5. Keep Email/Call already-Running idempotency.
6. Keep stage adoption + `routeContactSequence(activate:*)` + close (`Task_State=Won, Task_Status=Closed, Status=Completed`).

**Behavior after change:** type-alone edit = no-op; Won+valid type = activate+close; Won+blank type =
reopen + Manual Review; both-in-one-save = activate. **Risk:** moderate (core path); mitigated by smoke §Smoke.

### 3.4 Activation Task Description update (`v6/processContact.deluge`)

Reflect the two-step commit (uses the existing `nl = hextoText("0A")`):
```
Automation-managed activation task.
Contact: <name>
Stage: <stage>
Lead Source (context only): <src>

Your action:
1. Set Task Sequence Type to choose the route:
   - Email = automation sends the opener email, then books the first Call
   - Call = automation books the first Call
   - Manual = you run the sequence yourself (automated emails/calls stay off)
2. Set Task State = Won to start.
On save, automation starts the selected route and completes this task for you.
Do not edit Task Status, Status, Blocks Sequence, or the Stage / Pipeline / Sequence fields.
```

### 3.5 Mirrors — NO code change now (per your decision)
`Task_Stage`, `Call_Task_Stage`, `*_Pipeline`, `*_Opportunity` keep being stamped. Lock/hide (Layer 1),
check reports/dashboards, then decide separately whether to stop stamping. Not in this diff.

---

## Layer 4 — Deletion (DEFERRED, separate approval only)
Delete a Zoho field only after it is proven unused by code, workflows, **reports, dashboards, layouts,
and imports**. Do-not-delete-yet set: `Blocks_Sequence`, `Block_Email_Until_Done`, `Task_Stage`,
`Call_Task_Stage`, `*_Pipeline`/`*_Opportunity`, `Task_Outcome`, `Call_Outcome`, `Meeting_Status`,
`Meeting_Type`, `Meeting_Outcome`, `Follow_Up_Required`, `Follow_Up_Stage`, `Check_In_State/Status`.

---

## Smoke test plan (after Layer 3 publish)
Reuse the `ZZ DESC SMOKE` cascade (Contact → `Contacts_X_Products` junction → WF001b0 → activation).
1. **Activation hardening:** create activation task; set `Task_Sequence_Type=Call` only → **no** Call created, task stays Not Started (log `activation_awaiting_commit`). Then set `Task_State=Won` → Sequence Call created, activation task Completed. Separately: set `Task_State=Won` with blank type → task reopens + Manual Review `[activation_no_route]`.
2. **isBlockingTask:** with an open Draft Commercials / Manual Review present, confirm `resume` does **not** advance (blocked); Deferred sibling + Scheduled Send + Email Sent do **not** block; stale old-stage task does **not** block current-stage routing. Verify the related-list fetch returns `Task_Type`/`Task_Sequence_Managed`/`Task_Status` (the §3.1 risk) — if any come back null, switch scan to `searchRecords`.
3. **Block_Email_Until_Done removal:** rescheduled Call still created normally.
4. **Descriptions:** activation Description shows the 2-step text with real line breaks.
5. Confirm via COQL that no path still needs a `Blocks_Sequence`/`Block_Email_Until_Done` read.

## Approved cleanup sequence (recap)
1. Layout/profile hardening (Layer 1) — reversible, first.
2. Metadata corrections (Layer 2).
3. Code simplification (Layer 3) — after diff-plan approval + your publish.
4. Observation cycle (smoke + regenerate scratch data).
5. Stop unnecessary writes (Blocks_Sequence Phase B; optionally mirror stamps).
6. Deletion pass (Layer 4) — separate approval.

## What I need from you to proceed
- **Layer 1/2:** admin-UI only (see capability note) — apply from this spec.
- **Layer 3:** diff staged on `codex/activity-field-cleanup` (mitigation (a) implemented). You publish, then we smoke. No commit until you confirm.
- **Layer 4:** approve the safe-delete batch below (deletion is admin-UI; no MCP delete tool).

---

## API-capability finding (2026-07-08)
ToolSearch confirms the available MCP toolset has **no** endpoint for: field label edit, picklist-value
edit, layout section/field edit, per-profile field permission, or **field deletion**. `getFields` /
`getLayouts` are read-only. Therefore **Layers 1, 2, and 4 are admin-UI operations** — I cannot execute
them via API. The only cleanup I can execute is the Layer-3 code (done, on branch, awaiting your publish).

## Layer 4 — Safe-delete batch (evidence; deletion = admin UI + explicit approval)
Gate = custom + 0 Deluge reads + 0 Deluge writes (post-diff) + 0 workflow criteria + 0 layout usage +
0 report/dashboard/import usage + no data to preserve.

| Field (API) | Module | Field ID | Custom | Deluge reads | Deluge writes | WF criteria | On layout | Data rows | Gate verdict |
|---|---|---|---|---|---|---|---|---|---|
| `Task_Outcome` | Tasks | 991103000000786020 | yes | 0 | 0 | 0 | **no** | **0** | ✅ passes all machine checks now |
| `Meeting_Type` (label "DEP - Meeting Type") | Events | 991103000000784078 | yes | 0 | 0 | 0 | **no** | **0** | ✅ passes all machine checks now |
| `Follow_Up_Required` | Events | 991103000000793003 | yes | 0 | 0 | 0 | YES (Meeting Additional Information) | 0 | ⏳ passes after layout removal |
| `Follow_Up_Stage` | Events | 991103000000793015 | yes | 0 | 0 | 0 | YES (Meeting Additional Information) | 0 | ⏳ passes after layout removal |
| `Block_Email_Until_Done` | Calls | 991103000000789090 | yes | 0 | 1 (removed on branch; publish pending) | 0 | YES (Purpose Of Outgoing Call) | 1 (ZZ DESC SMOKE scratch call) | ⏳ passes after publish + layout removal + scratch cleanup |

**Do NOT delete (native, read-only):** `Check_In_State` (991103000000035011), `Check_In_Status`
(991103000000035023) — `custom=false`. Remove from the Events layout only.

**Already absent (no field exists — nothing to delete):** `Call_Outcome`, `Meeting_Status`,
`Meeting_Outcome`.

**Cannot verify via API (you must confirm before deleting):** reports, dashboards, and
import/templates usage — there is no MCP tool to list these. The Zoho delete-field UI will also surface
any remaining dependency blocker at delete time.

**Rollback/backup note:** data rows are 0 (Block_Email = 1 scratch value), so no export is materially
needed. Zoho retains deleted custom fields for restore for a limited window; still, record each field's
`id` / api_name / picklist values (captured above) before deletion for quick re-create if required.
