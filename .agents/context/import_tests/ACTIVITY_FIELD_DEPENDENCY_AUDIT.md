# v6 Activity Field Dependency Audit (Deluge-first)

**Date:** 2026-07-08 · **Scope:** `v6/**/*.deluge` (Tasks, Calls, Events) + live Zoho `getFields`,
`getLayouts`, workflow rules. **Source of truth = Deluge code + live workflow/metadata readback.**
Docs were ignored for extraction; documentation drift is called out where found.

> Constraints honored: no field deleted, no destructive metadata change, no code committed, no
> backfill. This is the audit only — refactor is proposed, not applied.

---

## 1. Executive summary

- **No live activity workflow uses field-level criteria.** WF008 (Tasks, `create_or_edit`), WF006 (Calls, `anyaction`), WF007 (Events, `create_or_edit`) all fire broadly and let the Deluge function gate internally. **Consequence: no workflow criterion blocks any field deprecation — code references are the only constraint.** (WFC-SchedEmail is the only criteria-bearing one: `date_or_datetime` on `Due_Date`.)
- **`Blocks_Sequence` is DERIVABLE** (user hypothesis CONFIRMED). It is read in exactly **2 places** (`routeContactSequence` L329 resume-guard, L1141 dispatch-gate), each already ANDed with `Status`/`Task_Sequence_Stage`. It can be replaced by a computed `isBlockingTask(task, contactStage)` predicate anchored on `Task_Sequence_Managed` + `Task_Type` + `Status`. Deprecate (hide/read-only now; remove reads later; delete only after migration).
- **`Task_Sequence_Managed` is the stored identity flag** (CONFIRMED) — read as "is this automation's task?" (handleTaskCompletion L57, supersede L871, SEQ-6 scan L414). **Not derivable; keep.**
- **`Block_Email_Until_Done` is DEAD** — a single **write** (`routeContactSequence:1238`), **zero reads, zero workflow criteria**. Stop writing; hide; delete later.
- **Stage duplication CONFIRMED.** `Task_Stage` (5 writes/0 reads) duplicates `Task_Sequence_Stage` (the read routing cursor). `Call_Task_Stage` (3 writes/0 reads) duplicates `Sequence_Stage` (the read routing cursor). All six `*_Pipeline`/`*_Opportunity` mirrors, `Call_Purpose_Detail`, `Reminder_Send_At`, `Outgoing_Call_Status` are **write-only reporting mirrors**.
- **Legacy/dead fields (zero code refs, only "retired" comments):** `Meeting_Status`, `Meeting_Type`, `Meeting_Outcome`, `Follow_Up_Required`, `Follow_Up_Stage`, `Check_In_State`, `Check_In_Status`, `Task_Outcome`, `Call_Outcome`.
- **Documentation drift / data-integrity:** `Calls.Sequence_Stage` picklist holds **old vocab** (Demo Booked/Attended, Commercials Sent/Signed) but the code writes/reads **canonical** stage names (Demo Confirmation, Commercial Agreement, …). Field works because API writes tolerate out-of-list values, but the picklist should be re-synced.

## 2. Current operating model (as coded)

User edits a mix of evidence fields **and** (accidentally) automation-owned fields, because every
automation-owned control/mirror sits editable on the one shared layout. Commit surfaces are
consistent per module (`Task_State` / `Call_Task_State` / `Meeting_Task_State`) **except activation
Tasks**, which route off `Task_Sequence_Type` and are auto-closed by automation. Blocking status,
stage, pipeline and opportunity are **persisted twice** (a read cursor + a write-only mirror).

## 3. Corrected target operating model

- Rep edits **only**: `*_Task_State` (+ `*_Lost_Reasons` on Lost), `*_Contract_*` when commercial evidence exists, `Next_Follow_Up_Date` (Calls), `Task_Sequence_Type` (activation only), and optionally `Meeting_Task_Stage` (to force a commercial/renewal meeting type).
- Everything else is automation-owned and should be **read-only/hidden for reps**.
- `Blocks_Sequence` becomes a **computed predicate**, not stored state.
- Dead fields removed from layout; deleted later after report/rollup confirmation.

## 7. Field classification legend

**U** user-evidence · **CU** conditional user-evidence · **AP** activation/route parameter · **IF**
automation identity flag · **AG** automation guard · **IM** idempotency/status mirror · **RC**
routing/stage cursor · **RM** reporting/layout mirror · **MP** machine/dedupe payload · **LG**
legacy/dead · **STD** platform-required standard field · **DV** dangerous-if-edited.

---

## 4. Tasks field matrix

| Field label | API name | Std/Cust | Read by code | Written by code | WF criteria | User edits? | Automation-owned | Derivable | Risk if edited | Class | Recommendation |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Task State | `Task_State` | cust | handleTaskCompletion L85,94,203,208,213,259 | handleTaskCompletion (Won/Lost/Open transitions) | none (WF008 fires all) | **Yes** | no | no | — | **U** | keep visible/editable |
| Task Lost Reasons | `Task_Lost_Reasons` | cust | handleTaskCompletion L87,215 | — | none | Yes on Lost | no | no | — | **CU** | keep visible/editable |
| Task Contract Products/Brands/Date Start/Date End/Frequency | `Task_Contract_*` | cust | handleTaskCompletion L282-307 (on Won) | carried only (no automation authoring) | none | Yes when commercial | no | no | — | **CU** | keep; blocked by P0 picklist (see ACTIVITY_DESCRIPTION_AUDIT) |
| Task Sequence Type | `Task_Sequence_Type` | cust | handleTaskCompletion L83,160 (activation route) | set Won on activation complete | none | Yes (activation only) | partly | no | starting sequence | **AP** | keep editable on activation; see §20 |
| Task Type | `Task_Type` | cust | handleTaskCompletion L41 + dispatch; supersede L871; dedup | createRecord (all tasks) | none | **No** | yes | no | misroute | **IF/RC** | hide/read-only |
| Task Sequence Managed | `Task_Sequence_Managed` | cust (**boolean**) | handleTaskCompletion L57; routeContactSequence L871; handleCallOutcome L414 | put true (all auto tasks) | none | **No** | yes | **no** (identity) | handler skips task | **IF** | **keep**; hide/read-only |
| Blocks Sequence | `Blocks_Sequence` | cust (Yes/No) | routeContactSequence **L329, L1141 (only 2)** | createAuxTask L78, createManualReview L75, processContact L355/414, routeContactSequence L1303/1348, handleTaskCompletion L153, sendSequencedEmail L257/280 | none | **No** | yes | **YES** | can desync vs Status | **AG** | **deprecate → computed predicate** (§17); hide now; delete later |
| Task Status | `Task_Status` | cust (New/Working/Closed) | handleTaskCompletion L127,202; sendScheduledEmailFromTask L24 | many (mirror) | none | **No** | yes | partly | breaks idempotency | **IM** | hide/read-only |
| native Status | `Status` | std | routeContactSequence L323,863; handleTaskCompletion L82,89; dedup/supersede | many | WFC-SchedEmail uses `Due_Date` not Status | **No** | yes | no | breaks guards | **IM/STD** | hide/read-only for reps |
| Task Sequence Stage | `Task_Sequence_Stage` | cust (8-stage) | processContact L322,400; routeContactSequence L325; handleTaskCompletion L112,151; dedup L1331 | processContact L354; routeContactSequence L1302,1347; sendSequencedEmail L256,279 | none | **No** | yes | no | misroute/dedup | **RC** | keep; hide/read-only |
| Task Stage | `Task_Stage` | cust (8-stage) | **none (0 reads)** | processContact L362; createAuxTask L115; routeContactSequence L1366; sendSequencedEmail L263,285 | none | No | yes | **YES (dup of Task_Sequence_Stage)** | none | **RM** | reporting-only; hide or deprecate |
| Task Pipeline | `Task_Pipeline` | cust (B2B/Partnership) | **none** | createAuxTask L113; processContact L372; routeContactSequence L1364; sendSequencedEmail L264,286 | none | No | yes | yes (Deal mirror) | none | **RM** | reporting-only; hide/read-only |
| Task Opportunity | `Task_Opportunity` | cust (MQL/SQL/FTP/RTP) | **none** | createAuxTask L114; processContact L369; routeContactSequence L1365; sendSequencedEmail L265,287 | none | No | yes | yes (Deal.Stage mirror) | none | **RM** | reporting-only; hide/read-only |
| Subject | `Subject` | std | — | createRecord (all) | none | No | yes | no | cosmetic | **RM/STD** | leave |
| Owner | `Owner` | std | — | createRecord (Deal owner) | none | maybe | yes | yes | reassignment | **STD** | leave |
| Who_Id / What_Id / $se_module | — | std | handlers resolve Contact/Deal | createRecord | none | No | yes | no | breaks linkage | **STD/DV** | read-only for reps |
| Due_Date | `Due_Date` | std | sendScheduledEmailFromTask (scheduler) | routeContactSequence L1305 (ScheduledSend) | **WFC-SchedEmail** (`date_or_datetime`) | No | yes | no | mis-send timing | **RC/STD** | read-only for reps |
| Description | `Description` | std | supersede/dedup contains `ScheduledSend|`; audit `SendKey:` | helper text + payloads | none | No (payload rows) | mixed | no | breaks scheduler/dedup | **MP + U-helper** | see description audit |
| Task Outcome | `Task_Outcome` | cust | **none** | **none** | none (WF008 note: "not a lifecycle command") | — | — | — | none | **LG** | remove from layout; delete later |

## 5. Calls field matrix

| Field label | API name | Std/Cust | Read by code | Written by code | WF criteria | User edits? | Auto-owned | Derivable | Class | Recommendation |
|---|---|---|---|---|---|---|---|---|---|---|
| Call Task State | `Call_Task_State` | cust (Open/Won/Lost) | handleCallOutcome L66,125,128,166,297 + dedup | handleCallOutcome, routeContactSequence L1256 | none (WF006 `anyaction`) | **Yes** | no | no | **U** | keep editable |
| Call Task Lost Reasons | `Call_Task_Lost_Reasons` | cust | handleCallOutcome L68,299 | — | none | Yes on Lost | no | no | **CU** | keep editable |
| Next Follow-Up Date | `Next_Follow_Up_Date` | cust (datetime) | handleCallOutcome L174,234 | cleared to null L290,297 | none | Yes (reschedule) | no | no | **CU** | keep editable |
| Call Task Contract * | `Call_Task_Contract_*` | cust | handleCallOutcome L146-207 (on Won + carry) | carried onto reschedule | none | Yes when commercial | no | no | **CU** | keep; blocked by P0 picklist |
| Sequence Managed | `Sequence_Managed` | cust (**Yes/No**) | handleCallOutcome L37 (WF006 gate),236,384; routeContactSequence L850,1204 | put Yes on create/reschedule | none | **No** | yes | no (identity) | **IF** | **keep** (Call identity flag); hide/read-only; consider boolean parity with `Task_Sequence_Managed` |
| Sequence Stage | `Sequence_Stage` | cust (**OLD vocab picklist**) | handleCallOutcome L76,236; routeContactSequence L1204 | handleCallOutcome L187,262; routeContactSequence L1236 | none | **No** | yes | no | **RC** | keep; **re-sync picklist to canonical vocab**; hide/read-only |
| Sequence Attempt | `Sequence_Attempt` | cust (int) | handleCallOutcome L77,236; routeContactSequence L1204 | createRecord | none | No | yes | no | **RC** | hide/read-only |
| Call Task Status | `Call_Task_Status` | cust (New/Working/Closed) | handleCallOutcome L42,236,384; routeContactSequence L850,1204 | many (mirror) | none | **No** | yes | partly | **IM** | hide/read-only |
| Outgoing Call Status | `Outgoing_Call_Status` | std (native) | **none (write-only)** | handleCallOutcome (Scheduled/Completed/Cancelled); routeContactSequence L852,1242 | none | **No** | yes | yes | **RM/DV** | hide/read-only (editing re-fires WF006) |
| Call Task Stage | `Call_Task_Stage` | cust (8-stage) | **none (0 reads)** | routeContactSequence L1251; handleCallOutcome L194,270 | none | No | yes | **YES (dup of Sequence_Stage)** | **RM** | reporting-only; hide or deprecate |
| Call Task Pipeline | `Call_Task_Pipeline` | cust | **none** | handleCallOutcome L192,268; routeContactSequence L1249 | none | No | yes | yes | **RM** | reporting-only; hide/read-only |
| Call Task Opportunity | `Call_Task_Opportunity` | cust | **none** | handleCallOutcome L193,269; routeContactSequence L1250 | none | No | yes | yes | **RM** | reporting-only; hide/read-only |
| Block Email Until Done | `Block_Email_Until_Done` | cust (Yes/No) | **none (0 reads)** | routeContactSequence **L1238 (only ref)** | none | No | yes | n/a | **LG** | **stop writing; remove from layout; delete later** |
| Call Purpose Detail | `Call_Purpose_Detail` | cust | **none** | routeContactSequence L1239 | none | No | yes | yes | **RM** | reporting-only; leave/hide |
| Call Type / Call Start Time | `Call_Type` / `Call_Start_Time` | std | scheduler timing | createRecord | none | No | yes | no | **RC/STD** | read-only for reps |
| Who_Id / What_Id / $se_module | — | std | handlers | createRecord | none | No | yes | no | **STD/DV** | read-only for reps |
| Call Outcome | `Call_Outcome` | cust | **none** | **none** (comment: "legacy outcome retired") | none | — | — | — | **LG** | remove from layout; delete later |

## 6. Meetings/Events field matrix

| Field label | API name | Std/Cust | Read by code | Written by code | WF criteria | User edits? | Auto-owned | Class | Recommendation |
|---|---|---|---|---|---|---|---|---|---|
| Meeting Task State | `Meeting_Task_State` | cust (Open/Won/Lost) | handleMeetingEvent L61,72,107,143,148,162,217,225 | reopen on missing reason | none (WF007 all) | **Yes** | no | **U** | keep editable |
| Meeting Task Lost Reasons | `Meeting_Task_Lost_Reasons` | cust | handleMeetingEvent L63,164,227 | — | none | Yes on Lost | no | **CU** | keep editable |
| Meeting Task Contract * | `Meeting_Task_Contract_*` | cust | handleMeetingEvent L116-134 (on Won) | — | none | Yes when commercial | no | **CU** | keep; blocked by P0 picklist |
| Meeting Task Stage | `Meeting_Task_Stage` | cust (8-stage) | handleMeetingEvent L70 (type inference), L305 | stamp-if-blank L305 (from Contact stage) | none | **conditional** | mostly | **RC/CU** | keep; user may set to force commercial/renewal type; else inferred |
| Meeting Task Status | `Meeting_Task_Status` | cust (New/Working/Closed) | handleMeetingEvent L76 (idempotency), L306 | mirror | none | **No** | yes | **IM** | hide/read-only |
| Reminder Send At | `Reminder_Send_At` | cust (datetime) | **none (write-only)** | handleMeetingEvent L294 (computed) | none | **No** | yes | **RM** | read-only (actual send uses Deal.Demo_Reminder_Send_At via WF010c) |
| Meeting Task Pipeline / Opportunity | `Meeting_Task_Pipeline` / `Meeting_Task_Opportunity` | cust | **none** | handleMeetingEvent L295,296 | none | No | yes | **RM** | reporting-only; hide/read-only. NB: `Meeting_Task_Opportunity` label has a **double space** |
| Start/End DateTime | `Start_DateTime` / `End_DateTime` | std | handleMeetingEvent L280 (reminder calc) | — | none | Yes (booking) | no | **STD/U** | keep (external booking) |
| Event Title / Who_Id / What_Id / $se_module | — | std | handlers | — | none | booking | mixed | **STD** | keep linkage read-only for reps |
| Follow-Up Required | `Follow_Up_Required` | cust (Yes/No) | **none** | **none** | none | — | — | **LG** | remove from layout; delete later |
| Follow-Up Stage | `Follow_Up_Stage` | cust (OLD vocab) | **none** | **none** | none | — | — | **LG** | remove from layout; delete later |
| Meeting Status / Type / Outcome | `Meeting_Status` / `Meeting_Type` / `Meeting_Outcome` | cust | **none** (comments: "Legacy … not read") | **none** | none | — | — | **LG** | remove from layout; delete later |
| Check-In State / Status | `Check_In_State` / `Check_In_Status` | std (read-only native) | **none** | **none** | none | — | — | **LG/STD** | native; remove from layout |

---

## 8. Code-evidence index (key fields)

| Field | Op | File | Function/branch | Line |
|---|---|---|---|---|
| Blocks_Sequence | READ | routeContactSequence.deluge | resume blocking-task guard | 329 |
| Blocks_Sequence | READ | routeContactSequence.deluge | post-reconcile dispatch gate | 1141 |
| Blocks_Sequence | WRITE Yes | createAuxTask.deluge / createManualReview.deluge / processContact.deluge / routeContactSequence.deluge | task creation | 78 / 75 / 355 / 1348 |
| Blocks_Sequence | WRITE No | routeContactSequence.deluge / sendSequencedEmail.deluge / processContact.deluge / handleTaskCompletion.deluge | ScheduledSend, audit, defer | 1303 / 257,280 / 414 / 153 |
| Task_Sequence_Managed | READ | handleTaskCompletion.deluge / routeContactSequence.deluge / handleCallOutcome.deluge | guard / supersede / SEQ-6 | 57 / 871 / 414 |
| Block_Email_Until_Done | WRITE (only ref) | routeContactSequence.deluge | create_call | 1238 |
| Sequence_Managed | READ (WF006 gate) | handleCallOutcome.deluge | entry guard | 37 |
| Task_Stage | WRITE only | processContact/createAuxTask/routeContactSequence/sendSequencedEmail | mirrors | 362/115/1366/263,285 |
| Call_Task_Stage | WRITE only | routeContactSequence/handleCallOutcome | mirrors | 1251/194,270 |
| Task_Sequence_Stage | READ | processContact/routeContactSequence/handleTaskCompletion | dedup/guard/adopt | 322,400/325,1331/112,151 |
| Sequence_Stage (Call) | READ | handleCallOutcome/routeContactSequence | stale/dedup | 76,236/1204 |
| *_Pipeline/*_Opportunity | WRITE only | all handlers | mirrors | see §4–6 |

## 9. Live workflow criteria evidence
- **WF008 Task Completion Handler** (`991103000000784145`): `create_or_edit`, **no field criteria**. Desc confirms Task_State/Task_Sequence_Type are code-side commands; `Task_Outcome` "is not a lifecycle command".
- **WFC-SchedEmail** (`991103000001499121`): `date_or_datetime` on **`Due_Date`** (the only activity workflow with a field dependency).
- **WF006 Handle Call Outcome** (`991103000000808046`): `anyaction`, **no field criteria** (gating in code on `Sequence_Managed` + `Call_Task_State`).
- **WF007 Event Meeting Handler** (`991103000000782052`): `create_or_edit`, **no field criteria**.
- **Contacts** WF001b0 (`field_update` on Stage/State/Status/Contact_Role1/Account_Name) and WF001b2 (`create`) run `processContact` — relevant because Task/Call/Event creation cascades from there, but they reference **Contact** fields, not activity fields.

## 10. Live metadata/layout evidence
- Single **Standard** layout per module, shared by **Administrator / Standard / Team User**; **all automation-owned fields are `read_only=false` and co-located with user fields** (Tasks "Outcome"; Calls "Purpose Of Outgoing Call"; Events "Meeting Additional Information").
- Legacy fields present on layouts: Calls `Sequence_Stage` (old vocab), Events `Follow_Up_Required`/`Follow_Up_Stage`/`Check-In*`.
- Picklist drift: `Calls.Sequence_Stage` = {…, Demo Booked, Demo Attended, Commercials Sent, Commercials Signed, …} vs canonical code values.
- `Task_Sequence_Managed` is a true **boolean**; `Blocks_Sequence`, `Sequence_Managed`, `Block_Email_Until_Done`, `Follow_Up_Required` are **Yes/No picklists**.

## 11. User-editable field list (target)
- **Tasks:** `Task_State`, `Task_Lost_Reasons` (Lost), `Task_Contract_*` (commercial), `Task_Sequence_Type` (activation).
- **Calls:** `Call_Task_State`, `Call_Task_Lost_Reasons` (Lost), `Next_Follow_Up_Date`, `Call_Task_Contract_*` (commercial).
- **Events:** `Meeting_Task_State`, `Meeting_Task_Lost_Reasons` (Lost), `Meeting_Task_Contract_*` (commercial), `Meeting_Task_Stage` (optional override), `Start/End_DateTime` (booking).

## 12. Automation-owned field list (hide/read-only for reps)
- **Tasks:** `Task_Type`, `Task_Status`, native `Status`, `Task_Sequence_Managed`, `Task_Sequence_Stage`, `Blocks_Sequence` (until removed), `Task_Stage`, `Task_Pipeline`, `Task_Opportunity`, `Due_Date`.
- **Calls:** `Sequence_Managed`, `Sequence_Stage`, `Sequence_Attempt`, `Call_Task_Status`, `Outgoing_Call_Status`, `Call_Task_Stage`, `Call_Task_Pipeline`, `Call_Task_Opportunity`, `Call_Purpose_Detail`, `Call_Type`, `Call_Start_Time`, `Block_Email_Until_Done` (until removed).
- **Events:** `Meeting_Task_Status`, `Reminder_Send_At`, `Meeting_Task_Pipeline`, `Meeting_Task_Opportunity`.

## 13. Dangerous visible/editable fields (edit breaks automation)
- Native `Status`, `Task_Status`, `Call_Task_Status`, `Meeting_Task_Status` (idempotency anchors — editing to/from Closed can re-open or skip routing).
- `Outgoing_Call_Status` (editing re-fires WF006 `anyaction`).
- `Task_Sequence_Stage` / `Sequence_Stage` (misroute/dedup).
- `Task_Sequence_Managed` / `Sequence_Managed` (untick → handler stops managing the record).
- `Due_Date` on a ScheduledSend Task (mis-times or double-sends email).
- `Description` rows carrying `ScheduledSend|` / `SendKey:` payloads.

## 14. Redundant/derivable fields
- `Blocks_Sequence` → derivable (see §17).
- `Task_Stage` → duplicate of `Task_Sequence_Stage` (reporting mirror).
- `Call_Task_Stage` → duplicate of `Sequence_Stage` (reporting mirror).
- All six `*_Pipeline`/`*_Opportunity` → Deal mirrors (reporting only).
- `Reminder_Send_At` (Event) → mirror; real send uses `Deal.Demo_Reminder_Send_At`.
- `Call_Purpose_Detail` → derived from stage (reporting).

## 15. Legacy/dead fields (zero code reads/writes, zero WF criteria)
`Task_Outcome` (Tasks); `Call_Outcome`, `Block_Email_Until_Done` (Calls, the latter write-only);
`Meeting_Status`, `Meeting_Type`, `Meeting_Outcome`, `Follow_Up_Required`, `Follow_Up_Stage`,
`Check_In_State`, `Check_In_Status` (Events).

## 16. Native-field replacement candidates
- `*_Task_Status` (New/Working/Closed) vs native `Status`: **keep custom** — native `Status` picklist (Not Started/In Progress/Completed/Deferred/Waiting) does not map cleanly to the Open/Won/Lost + New/Working/Closed model, and both are already used together as separate signals. Replacing would require re-encoding every guard.
- `Outgoing_Call_Status` **is** the native Call status and is already used as the native mirror — no replacement needed; just lock it.
- `Meeting_Status`/`Meeting_Type`/`Meeting_Outcome` are the native-ish Event fields that were **replaced** by `Meeting_Task_*` — the replacement already happened; retire the natives from the layout.
- Verdict: **no safe custom→native collapse** beyond retiring the already-replaced legacy fields; native Open/Won/Lost semantics do not exist, so the custom `*_Task_State` surface must stay.

---

## 17. `Blocks_Sequence` simplification assessment (Phase 3B)

**Finding:** persisted `Blocks_Sequence` duplicates information already implied by
`Task_Sequence_Managed` + `Task_Type` + `Status` (+ `Task_Sequence_Stage` for stage-scoping). Its two
read sites already AND it with those fields.

**Proposed predicate** (replaces both reads):
```
isBlockingTask(task, contactStage):
  Task_Sequence_Managed == true
  AND Task_Type NOT IN {"Scheduled Send", "Email Sent"}
  AND Status NOT IN {"Completed","Cancelled","Deferred"}
  AND Task_Status != "Closed"
  AND (Task_Sequence_Stage == "" OR Task_Sequence_Stage == contactStage)   // stage-scope only at L329
```
**Expected outcomes validated against write map:** open Sequence Activation / Manual Review / Data
Repair / Review Reply / Suppression Review / Draft Commercials / Send Commercials / Onboarding Setup
→ **block** (all are `Task_Sequence_Managed=true`, human types, not Scheduled Send/Email Sent); Scheduled
Send / Email Sent → **do not block** (excluded by type); Deferred/Completed/Cancelled/Closed → **do not
block** (excluded by Status); stale old-stage tasks → **do not block** current-stage routing (stage-scope).
This exactly reproduces today's behavior — and the current `Blocks_Sequence="No"` writes on defer are
already **redundant** with the Status check, proving the field is not independent state.

**Consistency risk today:** a task could carry `Blocks_Sequence="Yes"` while `Status=Deferred` (if any
path defers without also flipping the flag). The predicate removes that desync class.

**Refactor plan (code-only, no delete):**
1. Add `isBlockingTask` inline (or a tiny `automation.isBlockingTask` helper) and replace the L329 and L1141 reads.
2. Stop writing `Blocks_Sequence` (optional; harmless to keep writing during transition).
3. Hide/lock the field on the layout.
4. Smoke test (§25). 5. Delete the Zoho field **only after** a clean smoke + reporting check — **not now**.

## 18. `Block_Email_Until_Done` assessment (Phase 3C)
**Dead.** One write (`routeContactSequence:1238`), no reads, no WF criteria. Removing the write and the
layout field changes **no** automation behavior. Also assess `Sequence_Managed`: it **is** the Call
identity flag (WF006 gate) — **keep**, but it is a **Yes/No picklist** while `Task_Sequence_Managed` is
a boolean; consider standardizing to boolean for parity (migration, not urgent).

## 19. Stage-field collapse assessment (Phase 3D)
- **Tasks:** `Task_Sequence_Stage` = canonical routing cursor (**keep**); `Task_Stage` = write-only reporting mirror of it (**collapse**: hide/deprecate, keep only if a report needs a business-stage column — then make it a formula/rollup, not a stamped duplicate).
- **Calls:** `Sequence_Stage` = routing cursor (**keep**, fix picklist vocab); `Call_Task_Stage` = write-only mirror (**collapse**). `Sequence_Attempt` = keep (step cursor).
- **Meetings:** `Meeting_Task_Stage` = read routing/type cursor (**keep**); `Follow_Up_Stage` = legacy (**retire**).
- **Pipeline/Opportunity mirrors** (all six) = Deal mirrors, write-only → reporting-only; keep for reporting parity but **read-only/hidden**; long-term could be replaced by lookups/rollups to the Deal.
- **Are we storing the same stage twice?** Yes — on Tasks and Calls each business stage is persisted both as a read cursor and a write-only mirror.

## 20. Activation Task model recommendation (Phase 3A)

**Current exact behavior:** [handleTaskCompletion.deluge:125-191](../../v6/activity/handleTaskCompletion.deluge). For `Task_Type == "Sequence Activation"` the handler routes purely on
`Task_Sequence_Type` (Email/Call/Manual), ignores `Task_State`, and **auto-stamps** `Task_State=Won`,
`Task_Status=Closed`, `Status=Completed`. Editing `Task_Sequence_Type` alone (which fires WF008)
**does** start the sequence today — there is no separate commit.

**Risk of the proposed change** (require `Task_State=Won` + `Task_Sequence_Type` as parameter, so
editing the type alone does not start): behavioral change to a core path; a two-field commit is more
robust (prevents accidental activation on a mis-tap) but needs the description + rep training updated,
and a bounce path when `Task_State=Won` with blank `Task_Sequence_Type`.

**Recommended final model (hardened, opt-in):**
1. Rep sets `Task_Sequence_Type` (parameter) **and** `Task_State = Won` (commit).
2. Handler activates only when **both** present; reads type, starts route, auto-closes.
3. `Task_State = Won` with blank `Task_Sequence_Type` → reopen + Manual Review `[activation_no_route]`.
4. Editing `Task_Sequence_Type` alone → no-op (wait for the Won commit).
This makes activation consistent with every other task (commit = `Task_State`). **Requires code
changes** in the activation branch; **no workflow criteria change** (WF008 already fires on all edits).
If you prefer minimal change, keep today's one-field model but adopt the clarified Description (already
drafted) so reps know automation closes the task and `Task_State` is not theirs to set.

## 21. Recommended code changes (await approval)
1. `Blocks_Sequence` → `isBlockingTask()` predicate at routeContactSequence L329 & L1141; stop writing the field (optional during transition).
2. Remove the dead `Block_Email_Until_Done` write (routeContactSequence L1238).
3. Stop stamping the write-only mirrors that duplicate a cursor (`Task_Stage`, `Call_Task_Stage`) **only if** reporting doesn't need them; otherwise leave but lock.
4. (Optional, §20) hardened activation model.
5. Activation Description clarification (already proposed separately).

## 22. Recommended workflow criteria changes
**None required.** No activity workflow uses field criteria, so deprecations do not touch workflow
config. (If the hardened activation model is adopted, WF008 still needs no change — gating stays in code.)

## 23. Recommended layout/profile changes
- Set the entire **automation-owned list (§12)** to **read-only for Standard & Team User** (field-level permissions — there is only one shared layout).
- Remove **legacy fields (§15)** from all three layouts.
- Re-sync `Calls.Sequence_Stage` picklist to canonical stage vocab; fix `Meeting_Task_Opportunity` double-space label.
- Keep `Meeting_Task_Stage` visible (optional rep override).

## 24. Safe migration plan (staged, non-destructive)
1. **Layout/profile pass** (reversible): lock automation-owned fields, hide legacy fields. No code/data change.
2. **Code pass** (after approval + publish): `isBlockingTask` predicate; drop dead `Block_Email_Until_Done` write; optional mirror-stamp removal; optional hardened activation.
3. **Observe** one full cycle (smoke + live) with fields still present (hidden) to confirm no regression.
4. **Field deletion** (last, separately approved): only after reports/dashboards confirmed not to reference `Blocks_Sequence`, `Task_Stage`, `Call_Task_Stage`, `Block_Email_Until_Done`, and the legacy set. **Do not delete before this.**

## 25. Smoke test plan
Reuse the `ZZ DESC SMOKE` harness (Contact → junction → WF001b0 → activation → route). After the code pass, verify:
- Open activation/Manual Review/Draft Commercials **still block** `resume` (predicate path) — sequence does not skip them.
- ScheduledSend + Email Sent tasks **do not block**; Deferred sibling activation does not block.
- Stale old-stage task does not block current-stage routing.
- Rescheduled Call still created (Block_Email_Until_Done removal has no effect).
- Activation still completes; (if hardened) type-only edit is a no-op and Won+blank-type bounces.
- Confirm via COQL that no new `Blocks_Sequence`/`Block_Email_Until_Done` reads are needed.

## 26. Explicit "DO NOT DELETE YET" list
`Blocks_Sequence`, `Task_Stage`, `Call_Task_Stage`, `Block_Email_Until_Done`, `Task_Outcome`,
`Call_Outcome`, `Meeting_Status`, `Meeting_Type`, `Meeting_Outcome`, `Follow_Up_Required`,
`Follow_Up_Stage`, `Check_In_State`, `Check_In_Status`, and all `*_Pipeline`/`*_Opportunity` mirrors.
Hide/lock/stop-writing first; delete only after the staged migration + reporting confirmation.

---

### Documentation-drift notes (Deluge wins)
- `Calls.Sequence_Stage` picklist vocab is stale vs the canonical stages the code uses.
- `Meeting_Task_Opportunity` / `Meeting_Task_Contract_Products` labels contain double spaces.
- `Reminder_Send_At` (Event) is computed/stored but the actual reminder send is driven by
  `Deal.Demo_Reminder_Send_At` (WF010c / `sendDemoReminder`), so the Event field is effectively display-only.
