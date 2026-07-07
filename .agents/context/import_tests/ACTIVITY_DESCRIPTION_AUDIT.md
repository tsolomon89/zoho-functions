# v6 Activity Description — Field-Update Contract Audit & Rewrite

**Date:** 2026-07-07
**Scope:** Description / helper text for automation-created or automation-managed **Tasks, Calls,
and Meetings/Events** in `v6/`.
**Method:** repo tracing of every description path + its consuming handler branch, plus **live
read-only Zoho metadata** (`getFields`, `getLayouts`, COQL on `Products` and `Tasks`).
**Golden rule:** a Description is not done when the code string is correct — it is done when the rep
sees a **readable, truthful field-update contract** in the Zoho UI.

> Publish constraint: the Zoho Function MCP cannot push Deluge source. The user publishes each
> function manually; code is not committed until it is published live.

---

## Proven activity-control model

Activities are the evidence layer. A rep records the outcome on ONE field; automation
(`handleCallOutcome`/`handleTaskCompletion`/`handleMeetingEvent` → `routeContactSequence` →
`processDeal`) interprets it and moves the Contact/Deal/Quote.

| Module | Rep sets (surface) | On Lost | Reschedule | Commercial evidence (read only on **Won**) |
|---|---|---|---|---|
| Tasks | **Task State** (`Task_State`) — activation Tasks instead use **Task Sequence Type** (`Task_Sequence_Type`) | **Task Lost Reasons** (`Task_Lost_Reasons`) | — | `Task_Contract_Products/Brands/Date_Start/Date_End/Frequency` |
| Calls | **Call Task State** (`Call_Task_State`) | **Call Task Lost Reasons** | **Next Follow-Up Date** (`Next_Follow_Up_Date`) + State=Open | `Call_Task_Contract_*` |
| Events | **Meeting Task State** (`Meeting_Task_State`) | **Meeting Task Lost Reasons** | — (Calls only) | `Meeting_Task_Contract_*` |

**Automation-owned (rep must NOT edit):** native `Status`; `*_Task_Status` mirror (New/Working/Closed);
`Outgoing_Call_Status`; `Reminder_Send_At`; `*_Stage`/`*_Pipeline`/`*_Opportunity` mirrors; `Sequence_*`;
`Blocks_Sequence`; `Sequence_Managed`; `Block_Email_Until_Done`.

---

## Deliverable 0 — P0 Description RENDERING defect (first gate) — FIXED

### Root cause (proven live)
COQL read of a Deluge-written Task Description returned:

```
"Activate the Contact sequence.\\nContact: Jamie Gordon\\nStage: Renewal\\n..."
```

The JSON **double-backslash** `\\n` means the stored field holds the **literal two characters
`\` + `n`**, not a newline (0x0A). A real newline serialises as a single `\n` in JSON. So this org's
Deluge does **not** interpret `\n` in these string literals — every generated Description rendered as
one escaped blob.

### Rendering method verified in the UI
A scratch Task was written (via API) with three labelled blocks — a real newline, a `<br>` tag, and a
literal backslash-n — and inspected in the Zoho CRM detail view. Result: **Variant A (real newline)
renders as separate lines**; `<br>` shows literally; literal `\n` shows literally. The activity
Description field is plain text, so a real newline is the correct line break.

### Fix applied
Two newline approaches were ruled out here: `"\n"` stores as literal backslash-n (above), and a
**multi-line string literal** (raw newline inside quotes) is a **Deluge compile error** (`"\n is not
supported in Deluge`). The working method is the documented Deluge string function `hextoText("0A")`
(hex `0A` = line feed; single-line, compiles normally; ref
https://www.zoho.com/deluge/help/functions/string/hextotext.html):

```deluge
nl = hextoText("0A");            // real LF, renders as a line break in the plain-text Description field
desc = "line one" + nl + "line two";
```

Each rep-facing function defines `nl = hextoText("0A");` once and assembles Descriptions as
`"line one" + nl + "line two" + …`. Grep confirms **zero literal `\n`** remains in any rep-facing
Description string across the six edited functions (the only surviving `\n` are internal
`Quote_Applied_*_Keys` delimiters and the machine/audit payloads — see Deliverable 15).

### Acceptance criteria (verify one live record per module in the Zoho UI post-publish)
Activation Task · Draft Commercials Task · Sequence Call · Rescheduled Call · Meeting/Event (blank
Description) · Manual Review Task — each renders with **no literal `\n`**, is readable, uses live field
labels, and states what to update / what not to touch / the automation consequence.

> Note: `hextoText("0A")` yields a single LF regardless of the source file's own line endings, so the
> break is consistent across all six functions. Confirm rendering in the post-publish UI smoke test.

---

## Deliverables 1–3 — Description path inventory (kind + verdict)

| # | Path | Context | User-facing | Kind | Action taken |
|---|---|---|---|---|---|
| 1 | `processContact.deluge:342` `actDesc` | Activation Task | yes | helper | rewritten (managed framing + after-save result; render-safe) |
| 2 | `createAuxTask.deluge` footer | Manual Review / Data Repair / Review Reply / Suppression Review / Enrichment | yes | helper | rewritten — **removed false commercial claim** (resume types) |
| 2b | `createAuxTask.deluge` footer (taskType=Send Commercials) | Send Commercials | yes | helper | rewritten — own "deliver on Won" footer |
| 2c | `createAuxTask.deluge` footer (default) | future evidence-driven types | yes | helper | kept commercial line (render-safe) |
| 3 | `routeContactSequence.deluge` `create_call` | Sequence Call | yes | helper | re-templated (render-safe) |
| 4 | `handleCallOutcome.deluge` rescheduled Call | Rescheduled Call | yes | helper | re-templated, **byte-identical to #3** |
| 5 | `routeContactSequence.deluge` `stDesc` (generic) | generic stage Task (dead branch) | yes | helper | aligned |
| 5a | `routeContactSequence.deluge` Draft Commercials | Draft Commercials Task | yes | helper | re-templated (render-safe) |
| 5b | `routeContactSequence.deluge` Onboarding Setup | Onboarding Setup Task | yes | helper | re-templated (render-safe) |
| 6 | `handleMeetingEvent.deluge` | Meeting/Event (blank-only stamp) | yes | helper | re-templated; blank-only policy preserved |
| 7 | `createManualReview.deluge` | Contact-only Manual Review (no Deal) | yes | helper | re-templated (render-safe) |
| 8 | `routeContactSequence.deluge:~1306` `schedPayload` | Scheduled Send Task | no (internal) | **machine payload** `ScheduledSend|…` | **UNCHANGED** |
| 9 | `sendSequencedEmail.deluge:249` `auditDesc` | Email Sent audit Task | no (audit) | **audit payload** `SendKey: …` | **UNCHANGED** |

---

## Deliverable 4 — Field-control matrix (live-verified labels/types)

Legend: **U** user-editable · **C** conditional evidence · **M** automation mirror/status · **R**
automation routing/stage/seq · **O** obsolete/legacy.

**Tasks:** Task State `Task_State` picklist(Open/Won/Lost) **U** · Task Lost Reasons `Task_Lost_Reasons`
picklist **C** · Task Sequence Type `Task_Sequence_Type` picklist(Email/Call/Manual) **U (activation)** ·
Task Contract Products `Task_Contract_Products` multiselect **C** · Task Contract Brands `…_Brands`
integer **C** · Task Contract Date Start/End date **C** · Task Contract Frequency `…_Frequency`
picklist(4x/2x/1x per day) **C** · Task Status `Task_Status` picklist(New/Working/Closed) **M** · native
Status **M** · Task Type `Task_Type` **R** · Task Stage `Task_Stage` **M** · Task Pipeline/Opportunity
**M** · Task Sequence Stage `Task_Sequence_Stage` **R** · Task Sequence Managed `Task_Sequence_Managed`
**boolean R** · Blocks Sequence `Blocks_Sequence` Yes/No **R**.

**Calls:** Call Task State `Call_Task_State` **U** · Call Task Lost Reasons **C** · Next Follow-Up Date
`Next_Follow_Up_Date` datetime **C** · Call Task Contract * **C** · Call Task Status **M** · Outgoing Call
Status `Outgoing_Call_Status` **M** · Call Task Stage/Pipeline/Opportunity **M** · Sequence Stage
`Sequence_Stage` **R (+O: picklist uses old vocab — Demo Booked/Attended/Commercials Sent/Signed)** ·
Sequence Attempt **R** · Sequence Managed `Sequence_Managed` Yes/No **R** · Block Email Until Done
`Block_Email_Until_Done` Yes/No **R**.

**Events:** Meeting Task State `Meeting_Task_State` **U** · Meeting Task Lost Reasons **C** · Meeting Task
Contract * **C** · Meeting Task Status **M** · Reminder Send At `Reminder_Send_At` **M** · Meeting Task
Stage/Pipeline/Opportunity **M** · Follow-Up Required `Follow_Up_Required` Yes/No **O (not read by v6)** ·
Follow-Up Stage `Follow_Up_Stage` **O (old vocab)** · Check-In State/Status read-only native.

---

## Deliverable 5 — Commercial/quote field matrix + Finding P0

Commercial fields exist and are rep-editable on all three layouts. They are read **only when the
activity is set Won** (handlers build the product contextJson only on Won:
`handleCallOutcome:128-159`, `handleTaskCompletion:275-308`, `handleMeetingEvent:107-136`). Commercial
fields **alone never build a Quote** — Won is required.

### 🔴 Finding P0 (BLOCKING, live-verified) — Contract Products picklists list only DEACTIVATED products
- COQL `Products`: **active** = `Jurnii 360`, `Jurnii Cortex`, `Jurnii UX`, `Partnership` (4 canonical, name-only). The 6 plan variants (`Jurnii 360 - Fixed/Flex`, `Jurnii Cortex - Fixed/Flex`, `Jurnii UX - Fixed/Flex`) are `Product_Active=false`.
- `getFields`: the `Task_/Call_/Meeting_Task_Contract_Products` multiselect picklists offer **only those 6 deactivated variant names**.
- `resolveDealProduct` + `computeProductKey` resolve **only canonical name-only** Products. `computeProductKey("Jurnii 360 - Fixed")` = `jurnii_360_fixed` ≠ `jurnii_360`; the resolver's own comment states variants never match. Every picklist value returns `valid=false` (`canonical_product_missing` / `product_unresolved`).
- **Impact:** any Product a rep selects is unresolvable → no Quote line is built → `processDeal` raises Manual Review `[product_unresolved]`; Draft Commercials bounces Open. **The "Quote on Won" promise is false for every current picklist value.**
- **Required manual fix (Zoho, non-destructive):** repopulate the three `*_Contract_Products` picklists with the canonical active names (**Jurnii 360, Jurnii Cortex, Jurnii UX, Partnership**), matching `Product_Interest` and the resolver.

### Commercial wording must not become false in the live org
- If the P0 picklist fix is completed **before** publish → the Descriptions' "on Won automation creates/updates the Quote from the Contract fields" is true; ship as written.
- If the P0 fix is **not** completed before publish → either (a) do not publish the Quote-creation wording, or (b) reword conditionally ("Once product picklists are corrected, on Won automation will use these fields…").
- **Preferred: fix the picklists first, then publish.** The rewritten strings assume the fix; do not publish a knowingly false contract.

### Where commercial fields drive a Quote (post-P0-fix)
- **Draft Commercials Task Won** → builds/updates the Draft Quote (REST), prices via `resolveQuoteLinePrice`, raises Send Commercials. Contract fields **mandatory** (missing brands/start/end bounce Open).
- **Call / generic Task / Meeting Won with products** → `processDeal` links Products, upserts per-Product Quote, recomputes Amount. Contract fields **optional**.
- **Frequency** matters for **Jurnii 360** only.
- Resume-only Task types, Onboarding Setup, and Send Commercials do **not** read Contract Products to build a new Quote.

---

## Deliverable 6 — Workflow-trigger matrix

| Handler | WF | Fires on | Trigger field | Reads after firing |
|---|---|---|---|---|
| `handleCallOutcome` | WF006 | Call create/edit | `Call_Task_State` (+`Next_Follow_Up_Date`) | State, Lost Reasons, Next Follow-Up, `Call_Task_Contract_*` |
| `handleTaskCompletion` | WF008 | Task create/edit | `Task_State` / `Task_Sequence_Type` | State, Lost Reasons, Task_Type, `Task_Contract_*` |
| `handleMeetingEvent` | WF007 | Event create/edit | `Meeting_Task_State` (+ upcoming pass) | State, Lost Reasons, `Meeting_Task_Contract_*`, Start_DateTime |
| `sendScheduledEmailFromTask` | WFC-SchedEmail | Task.Due_Date reached | `ScheduledSend|` payload | payload only |

Each handler mirrors the terminal to `*_Task_Status=Closed` and guards re-entry (idempotent under
create-or-edit).

---

## Deliverable 7 — Save-order conclusion: ONE save is safe

WF006/WF008/WF007 fire **after** the save commits, and each handler **re-fetches the whole record**
via `getRecordById` (not a delta). Contract fields + State=Won written in the **same save** are both
visible to the handler. Descriptions therefore say "fill the Contract fields … before Won" in one
save. Draft Commercials already enforces this (bounces Open if terms are missing). No separate pre-save
is needed.

---

## Deliverable 8 — Boolean / Yes-No control fields

| Field | Module | Type | Written | Read | Recommendation |
|---|---|---|---|---|---|
| `Task_Sequence_Managed` | Tasks | **boolean** | `true` | `=="true"` | already boolean — keep |
| `Blocks_Sequence` | Tasks | Yes/No picklist | `"Yes"/"No"` | `=="Yes"` | automation-owned; hide on layout; do not convert blindly |
| `Sequence_Managed` | Calls | Yes/No picklist | `"Yes"/"No"` | `=="Yes"` | same |
| `Block_Email_Until_Done` | Calls | Yes/No picklist | `"Yes"/"No"` | `=="Yes"` | same |
| `Follow_Up_Required` | Events | Yes/No picklist | (legacy) | not read | obsolete — remove from layout |

Picklist→boolean is **not safe blindly** (every read compares `"Yes"`; WF criteria reference the
values). If desired: staged migration — new boolean → backfill → dual-read → swap WF criteria → retire.
Recommended now: leave as picklists, hide from rep layouts.

## Deliverable 9 — Native Status vs custom State

Three status-like fields per module: native `Status`; `*_Task_Status` mirror (automation-owned);
`*_Task_State` (the rep surface). Reps should **see and edit only `*_Task_State`** (+ `*_Lost_Reasons`,
Contract fields, `Next_Follow_Up_Date` on Calls, `Task_Sequence_Type` on activation). Set native
`Status`, `*_Task_Status`, and `Outgoing_Call_Status` **read-only/hidden** for rep profiles. Every
rewritten Description explicitly warns against editing Status / `*_Task_Status`.

## Deliverable 10 — Layout / profile findings (live-verified)

- **One `Standard` layout per module**, shared by Administrator / Standard / Team User (no rep-only layout) → visibility must be controlled by **field-level profile permissions**.
- **All automation-owned fields are `read_only=false` and co-located with the rep fields** (Tasks "Outcome" section; Calls "Purpose Of Outgoing Call"). High risk a rep edits a mirror/routing field. → make read-only for Standard/Team User, or move to a separate "Automation (do not edit)" section.
- **Legacy fields still on layouts:** Calls `Sequence_Stage` (old vocab) duplicates `Call_Task_Stage`; Events `Follow_Up_Required` + `Follow_Up_Stage` (old vocab, not read by v6). → hide/remove.
- **Contract fields ARE on-layout and rep-editable** in all three modules → the guidance to fill them is actionable once Finding P0 is fixed.
- **No layout-level required fields** (incl. Lost Reasons) — the "Lost needs a reason" rule is code-enforced (handlers reopen + raise Manual Review). Descriptions state it.
- **Cosmetic:** `Meeting_Task_Opportunity` label "Meeting  Task Opportunity" and `Meeting_Task_Contract_Products` "Meeting Task Contract  Products" have double spaces.

## Deliverable 11 — Existing-record backfill

New text applies to **new** records only. Existing open Tasks/Calls keep old footers; behavior is
unchanged. Recommend **new-records-only** (no bulk Description rewrite). Priority is the Finding P0
picklist fix, which affects all existing + future activities. Meetings are never overwritten.

## Deliverable 12 — Meeting helper-text policy

v6 does **not** create Meetings (booked externally; `handleMeetingEvent` reacts). Helper text is
stamped on the first UPCOMING pass **only when `Description` is blank** (never overwrites a rep's
agenda). Keep this policy. For richer guidance prefer field-level help on `Meeting_Task_State` +
Contract fields. No reschedule/Next-Follow-Up line on Meetings (Calls-only path).

---

## Deliverables 13/14 — New behavior + exact before/after (rendered text)

Placeholders in `<angle brackets>`. "Before" shows the literal source string (with the broken `\n`
that rendered literally). "After" shows the rendered UI output (real line breaks via `nl`).

### 1. Activation Task — `processContact.deluge`
**Before (rendered literally as one line):**
`Activate the Contact sequence.\nContact: <name>\nStage: <stage>\nLead Source (context only): <src>\n\nSet Task Sequence Type to choose the route:\n- Email\n- Call\n- Manual\n\nNo other field update is required.\n`

**After:**
```
Automation-managed activation task.
Contact: <name>
Stage: <stage>
Lead Source (context only): <src>

Your action: set Task Sequence Type to choose how the sequence runs:
- Email = automation sends the opener email, then books the first Call
- Call = automation books the first Call
- Manual = you run the sequence yourself
No other field needs changing; automation starts the sequence when you save.
```

### 2. Sequence Call / Rescheduled Call — `routeContactSequence.deluge` + `handleCallOutcome.deluge` (identical)
**Before:** `Automation-managed call for the <stage> sequence (attempt <n>).\nLog the result…\n- Reached and progressed -> …Won\n…` (literal `\n`).

**After:**
```
Automation-managed call for the <stage> sequence (attempt <n>).
Log the result on this Call:
- Reached and progressed -> set Call Task State = Won
- Could not progress -> set Call Task State = Lost + choose Call Task Lost Reasons
- Try again later -> set Next Follow-Up Date and leave Call Task State = Open
If commercial terms were discussed, quoted or agreed, also fill the Call Task Contract fields (Products / Brands / Date Start / Date End / Frequency) before Won.
Do not edit Call Task Status, Outgoing Call Status, or the Stage / Pipeline / Sequence fields - automation advances the sequence (and creates/updates the Quote from the Contract fields) once you save the result.
```

### 3. Draft Commercials Task — `routeContactSequence.deluge`
**After:**
```
Automation-managed task: capture the commercial terms for this Deal, then set Task State = Won.
Required before Won:
- Task Contract Products (one or more products discussed)
- Task Contract Brands
- Task Contract Date Start and Task Contract Date End
- Task Contract Frequency (Jurnii 360 only)
On Won: automation builds/updates the Draft Quote, recalculates the Deal value, and raises the Send Commercials task; missing terms bounce this task back with a Manual Review note.
Do not edit Task Status, Status, the Stage / Pipeline / Sequence fields, or the Quote directly.
```

### 4. Onboarding Setup Task — `routeContactSequence.deluge`
**After:**
```
Automation-managed task for the <stage> stage.
Your action: when onboarding setup is complete, set Task State = Won - automation then marks the sequence Complete.
If commercial terms were discussed or agreed, also fill the Task Contract fields (Products / Brands / Date Start / Date End / Frequency).
Do not edit Task Status, Status, or the Stage / Pipeline / Sequence fields - automation advances the record after you save.
```

### 5. Generic stage Task (dead branch, aligned) — `routeContactSequence.deluge`
**After:**
```
Automation-managed task for the <stage> stage.
Your action: when the work is done, set Task State = Won (or Task State = Lost + Task Lost Reasons if it cannot proceed).
If commercial terms were discussed, quoted or agreed, also fill the Task Contract fields (Products / Brands / Date Start / Date End / Frequency) before Won.
Do not edit Task Status, Status, or the Stage / Pipeline / Sequence fields - automation advances the sequence (and updates any Quote from the Contract fields) after you save.
```

### 6. Manual Review / Data Repair / Review Reply / Suppression Review / Enrichment — `createAuxTask.deluge`
**Before (universal footer — falsely promised Quote on these resume-only types):**
`… If commercial terms were discussed, quoted or agreed, also fill the Task Contract fields … automation … updates any Quote after you save.`

**After (footer appended below the issue note):**
```
<issue note>

--- Automation-managed task.
Your action: resolve the item above, then set Task State = Won (or Task State = Lost + Task Lost Reasons if it cannot proceed).
Do not edit Task Status, Status, or the Stage / Pipeline / Sequence fields - automation owns them.
On save: automation resumes the Contact sequence. No commercial / Contract fields are read on this task.
```

### 7. Send Commercials Task — `createAuxTask.deluge`
**After:**
```
<note: Commercials drafted - send to the customer to advance to Commercial Agreement.>

--- Automation-managed task.
Your action: once the commercials have been sent to the customer, set Task State = Won.
Do not re-enter the Contract fields, and do not edit the Quote, Task Status, Status, or the Stage / Pipeline / Sequence fields.
On save: automation marks the Quote Delivered and advances the Deal to Commercial Agreement.
```

### 8. Default aux footer (future evidence-driven types) — `createAuxTask.deluge`
**After:**
```
<note>

--- Automation-managed task.
Your action: when the work is done, set Task State = Won (or Task State = Lost + Task Lost Reasons).
If commercial terms were discussed, quoted or agreed, also fill the Task Contract fields (Products / Brands / Date Start / Date End / Frequency) before Won.
Do not edit Task Status, Status, or the Stage / Pipeline / Sequence fields - automation advances the record and updates any Quote after you save.
```

### 9. Contact-only Manual Review (no Deal) — `createManualReview.deluge`
**After:**
```
<[code] detail>

--- Automation-raised review. No Deal is linked, so completing this task does not advance a sequence by itself. Resolve the data issue described above; automation resumes the correct Deal flow when the record is re-processed.
```

### 10. Meeting / Event (blank Description only) — `handleMeetingEvent.deluge`
**After:**
```
Automation-managed meeting.
After it happens, log the result on this Event:
- Went ahead / qualified -> set Meeting Task State = Won
- Did not happen / lost -> set Meeting Task State = Lost + choose Meeting Task Lost Reasons
If commercial terms were discussed, quoted or agreed, also fill the Meeting Task Contract fields (Products / Brands / Date Start / Date End / Frequency) before Won.
Do not edit Meeting Task Status, Reminder Send At, or the Stage / Pipeline fields - automation advances the sequence (and creates/updates the Quote from the Contract fields) once you save the result.
```

---

## Deliverable 15 — Machine-readable descriptions kept UNCHANGED

- **Scheduled Send Task** `ScheduledSend|stage=..|step=..|kind=..` + `\n(Awaiting Due_Date …)` (`routeContactSequence`) — parsed by `sendScheduledEmailFromTask` via `desc.getPrefix("\n")`; the literal `\n` is load-bearing and consistent with the parser. Internal record (`Blocks_Sequence=No`), not a rep action surface. **Unchanged.**
- **Email Sent audit** `SendKey: <key>` + `Message ID:` (`sendSequencedEmail:249`) — idempotency dedup matches `SendKey: <key>`; `handleTaskCompletion` audit-guards these Tasks (never advances). **Unchanged.**
- Also unchanged (internal, not rep instructions): supersede marker append on cancelled ScheduledSend tasks (`routeContactSequence:~876`); "Send failed" append on the audit task (`sendSequencedEmail:229`); all `Quote_Applied_*_Keys` `\n` delimiters (data field, not a Description).

---

## Deliverable 16 — Code changes made

0. **Rendering fix (P0):** added a real-newline `nl` variable to each rep-facing function; all rewritten Descriptions use `nl` (zero literal `\n`).
1. `v6/activity/createAuxTask.deluge` — `taskType`-branched footer (resume / Send Commercials / default); reuse-append separator now `nl`.
2. `v6/processContact.deluge` — activation-task `actDesc` rewritten (managed framing + after-save result).
3. `v6/activity/routeContactSequence.deluge` — `create_call`, generic/Draft/Onboarding stage-task descriptions re-templated.
4. `v6/activity/handleCallOutcome.deluge` — rescheduled-Call description re-templated **byte-identical** to `create_call` (verified equal).
5. `v6/activity/handleMeetingEvent.deluge` — meeting description re-templated; blank-only guard preserved.
6. `v6/activity/createManualReview.deluge` — Contact-only review description re-templated.
7. Machine/audit payloads untouched (Deliverable 15).

## Deliverable 17 — Verification

- **Static:** grep confirms zero literal `\n` in the six functions' rep-facing Descriptions (remaining `\n` are `Quote_Applied_*_Keys` delimiters + machine/audit payloads) and zero broken multi-line string literals remain (all `nl` defs are the single-line `hextoText("0A")`). The two shared Call strings are byte-identical templates (checked programmatically).
- **Claims vs handlers:** resume-only footer ↔ `handleTaskCompletion` resume branch (no Contract read); Send Commercials footer ↔ deliver/advance branch; Draft Commercials ↔ REST Quote build + Send Commercials surface; Call/Meeting ↔ Won contextJson → `processDeal`. All match.
- **Pending (post-publish, requires the user to publish + view in UI):** rendered-output smoke test — one record per module in the Zoho UI; confirm no literal `\n` and readability. Dry-run: create a test Manual Review + Draft Commercials, confirm generated text = the templates above and Won behavior matches.

## Deliverable 18 — Manual Zoho changes required (outside repo)

1. **P0 (prerequisite):** repopulate `Task_Contract_Products`, `Call_Task_Contract_Products`, `Meeting_Task_Contract_Products` picklists with canonical active names (Jurnii 360, Jurnii Cortex, Jurnii UX, Partnership). Until done, the commercial line of every Description is untrue.
2. Set automation-owned fields read-only for Standard/Team User (native Status, `*_Task_Status`, `Outgoing_Call_Status`, `*_Stage`/`*_Pipeline`/`*_Opportunity`, `Blocks_Sequence`, `Sequence_Managed`, `Block_Email_Until_Done`), or move to an "Automation (do not edit)" section.
3. Remove/hide legacy fields: Calls `Sequence_Stage`; Events `Follow_Up_Required` + `Follow_Up_Stage`.
4. (Optional) add field-level help on `*_Task_State` + Contract fields; fix the two double-space labels.

## Deliverable 19 — Open product questions

- Approve the P0 picklist repopulation (canonical values)? Required for truthful commercial guidance.
- Convert `Blocks_Sequence` / `Sequence_Managed` / `Block_Email_Until_Done` to real booleans (staged migration) or leave hidden Yes/No picklists (recommended)?
- Backfill existing open activity Descriptions, or new-records-only (recommended)?
