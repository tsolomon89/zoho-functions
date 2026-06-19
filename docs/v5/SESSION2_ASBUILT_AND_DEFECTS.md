# V5 Cutover — Session 2 As-Built + Defect Log (2026-06-16)

End-to-end E2E validation, the Meeting/Event refactor, and the defects found. This is the
authoritative reconciliation for what changed in this session. Read alongside
`SESSION_HANDOFF.md` (now annotated) and `FIELD_REUSE_NOTES.md` (corrected).

Test instance is non-live. All E2E test records created this session were deleted at the end.
Recipient for delivered-mail checks: `tlcsolomon+e2eN@gmail.com` (Gmail ignores `+suffix`, so it
lands in `tlcsolomon@gmail.com`, readable via the Gmail MCP). **Do not use the bare
`tlcsolomon@gmail.com`** — it matches an existing Contact and lead-conversion will reuse that
record instead of creating a fresh one.

---

## 1. E2E results — GREEN

### Instant funnel (Lead → Onboarding), Gmail-verified
One Lead → convert → activation → cadence → meeting → commercial, all via real workflow triggers.
8 distinct emails delivered (Gmail confirmed), 8 "Email Sent" audit Tasks, **one email = one audit
Task, zero duplicates**:
`marketing-consent:1:initial` → `:2/:3/:4:follow-up` → `:5:final` → `demo-confirmation:0:confirmation`
→ `commercial-agreement:0:proposal-sent` → `onboarding:0:signed-confirmation`.
Validated: activation (Task-gated), call cadence (Neutral ×5 → terminal `:5:final` + postcall
schedule), `meeting:created`, `commercial:sent`/`signed`, supersede, Deal `Opportunity_Stage` rollup,
merge-tag rendering, send-idempotency (re-send of `:1:initial` suppressed).

### Demo re-run (after the Meeting refactor) — GREEN
| Scenario | Result |
|---|---|
| Scheduled | `meeting:created` → Demo Confirmation + `demo-confirmation:0:confirmation`; Event `Reminder_Send_At` stamped (−1 business day AM) |
| Confirmed | mirror only, no re-send |
| Rescheduled | `Reminder_Send_At` recalculated, no re-send |
| Cancelled | revert → Demo Booking, reminder cleared, no email, No-Show NOT inferred |
| Completed = Attended-Qualified | `demo:qualified` → Proposal Preparation + `proposal-preparation:0:post-demo` + Draft Commercials task |
| Completed = No Show (`Meeting_Outcome`) | `demo:noshow` → Demo Booking + `demo-confirmation:0:no-show` |
| Completed = Attended-Not Qualified | `demo:not_qualified` → Contact Lost (`No Fit`); Deal fail-safe Manual Review (see Defect 5) |

---

## 2. Refactor (this session) — repo `v5/`, published via Dev Hub

**Activation is Task-gated** (corrects the stale handoff/runsheet wording): setting
`Contact.Sequence_Type = Email` does NOT activate. `processContact` creates a "Sequence Activation"
Task; completing it with `Task_Outcome = "Activate Email First"` (WF008 → `handleTaskCompletion`)
emits `activate:email` → `routeContactSequence` → `send_opener_then_call` (opener `:1:initial` +
Call 1; contact stays at Call step 1). Architecture origin commit `918dfce`; `6e0e9bb` = refinements.

**Meeting/Event is the source of truth for the demo lifecycle.** No `Deal.Demo_Status` /
`Deal.Demo_Meeting_ID` (those fields do not exist and were NOT created).

- `handleMeetingEvent.deluge` — rewritten around Event fields: `Meeting_Status`
  (Scheduled/Confirmed/Rescheduled/Cancelled/Completed) + `Meeting_Outcome` (read only on Completed →
  `demo:qualified|followup|not_qualified|noshow`). **No-Show is read from `Meeting_Outcome`, never
  `Meeting_Status`.** Stamps the Event's own `Reminder_Send_At`; writes Deal summary mirrors
  (`Demo_Start_DateTime`, `Demo_Reminder_Send_At`, `Demo_Outcome`, trigger-suppressed); clears
  `Demo_Reminder_Send_At` on Cancelled. First-booking detected by **Contact stage rank < Demo
  Confirmation** (not a Deal mirror id), so re-edits at Demo Confirmation+ don't re-send.
- `sendDemoReminder.deluge` — **stays `sendDemoReminder(dealIdStr)`; WF010c stays on Deals**
  (date workflows cannot bind to the Meetings/Tasks modules). Guards on the Deal mirror fields
  `handleMeetingEvent` writes from the Event (`Demo_Outcome` blank/Scheduled, `Demo_Start_DateTime`
  in future), Automation_Suppressed, Primary Contact Open. WF010c binding unchanged:
  Module=Deals, date field=`Demo_Reminder_Send_At`, arg `dealIdStr ← ${Deals.id}`.
- Task field references migrated to the **real live api-names** across `processContact`,
  `createAuxTask`, `handleTaskCompletion`, `routeContactSequence`, `sendSequencedEmail` — see §3.
  `Sequence_Attempt` removed from Task writes (it does not exist on Tasks; kept on Calls).

**Fields created on Tasks this session** (only the genuinely-absent ones):
`Task_Sequence_Stage` (Single Line text) and `Blocks_Sequence` (Pick List Yes/No).
`Task_Sequence_Managed` (checkbox) already existed and is reused. **No** new Deal/Meeting/Call
fields; **no** new picklist values.

---

## 3. As-built sequence-field schema (authoritative — verified via live getFields)

The Activities modules do **NOT** share these custom fields (see Defect 3). Each module's real fields:

| Concept | Calls | Tasks | Contacts |
|---|---|---|---|
| sequence-managed flag | `Sequence_Managed` (picklist Yes/No) | `Task_Sequence_Managed` (checkbox) | — |
| sequence stage | `Sequence_Stage` (picklist) | `Task_Sequence_Stage` (text, **created this session**) | `Sequence_Stage` (picklist Email/Call/Meeting/Task) |
| attempt number | `Sequence_Attempt` (number) | — (removed from code) | `Sequence_Step` |
| blocks sequence | `Block_Email_Until_Done` | `Blocks_Sequence` (picklist Yes/No, **created this session**) | — |

Deal demo fields that exist: `Demo_Outcome`, `Demo_Start_DateTime`, `Demo_Reminder_Send_At`,
`Next_Comm_Follow_Up_Date`, `Automation_Suppressed`, `Commercials_Status`. **No** `Demo_Status`,
**no** `Demo_Meeting_ID`. Meeting fields are all present (see `zoho_meetings_api_names.csv`, unchanged).

---

## 4. Defect log

| # | Severity | Defect | Status / fix |
|---|---|---|---|
| 1 | Med | **Duplicate Sequence Activation Tasks** on the lead-conversion path. `processLead` calls `processContact` explicitly AND WF001b2 (Contacts create) fires `processContact` — the two runs race past the dedup before either commits. (The dedup field now exists, but the race remains.) | OPEN. Supersede now auto-Defers the duplicate once the contact advances (mitigation). Real fix: drop one of the two `processContact` invocations on the convert path (e.g., remove the explicit call in `processLead`, or suppress the create trigger during convert). |
| 2 | High → FIXED | **Demo reminder could never fire** — `sendDemoReminder` guarded on `Deal.Demo_Status`, which doesn't exist; `handleMeetingEvent` first-link dedup keyed off non-existent `Deal.Demo_Meeting_ID`. | FIXED this session: Meeting source-of-truth refactor; guards on Deal mirrors written from the Event; stage-rank first-booking. |
| 3 | High → FIXED | **Tasks lacked `Sequence_Managed`/`Sequence_Stage`/`Blocks_Sequence`/`Sequence_Attempt`** — the deluge wrote/read them on Tasks, Zoho silently dropped them → broken activation dedup, supersede-of-Tasks, blocking-task guard, stale guard. The docs wrongly assumed Activities custom fields are shared across Calls/Events/Tasks (they are NOT for this org — verified live). | FIXED: use `Task_Sequence_Managed`; created `Task_Sequence_Stage` + `Blocks_Sequence` on Tasks; removed Task `Sequence_Attempt`. Supersede/dedup now function (verified: duplicate activation task auto-Deferred on advance). |
| 4 | Low | **Postcall scheduled-send is redundant** — resolves to `<stage>:5:final`, already sent by the cadence side-email at step 5, so the WFC-SchedEmail wake-up always idempotency-skips. | OPEN (by design / harmless). Consider dropping the postcall schedule, or give it a distinct template key if a real post-call email is wanted. |
| 5 | Med | **Deal does not auto-close on Contact disqualification.** `routeContactSequence` deal-viability uses `getRelatedRecords("Contacts","Deals",id)`, which does not resolve on this EU tenant → fail-safe path creates a "Manual Review" Task and leaves the Deal Open. Contact loss itself is correct. | OPEN (fail-safe is intentional/safe). To auto-close, resolve Deal-Contact viability via a method that works on this tenant (COQL on Contacts by Account, or Contact_Roles), then close when no other Open contact remains. |

### Documentation defects to fix
- `ACTIVITY_ROUTING_MATRIX.md` §B activation rows say `send_email_now (step1)` advancing to step 2 for
  the Email path; the code does `send_opener_then_call` (opener `:1:initial` **+ Call 1**, stays at
  **Call step 1**). Also `Onboarding | 0 | … | onboarding:0:kickoff` is a **dead key** (not in the
  registry; Onboarding entry creates an Onboarding Setup task, no email).
- `zoho_tasks_api_names.csv` corrected this session (removed `Sequence_Managed`/`Sequence_Stage`,
  added `Task_Sequence_Managed`/`Task_Sequence_Stage`).
- `FIELD_REUSE_NOTES.md` §"Calls / Events / Tasks" claim that Activities custom fields auto-share to
  all three sub-modules is **false** for this org — corrected inline.

---

## 5. Remaining work
- **Date-based workflows (user verifies on Zoho's time-based scheduler):** WF010c (Deals
  `Demo_Reminder_Send_At` → `sendDemoReminder`), WF010d (Deals `Next_Comm_Follow_Up_Date` →
  `sendCommercialFollowUp`), WFC-SchedEmail (Tasks `Due_Date` → `sendScheduledEmailFromTask`).
  Functions + bindings validated by code + the instant paths; only the scheduler firing remains.
- **Post-E2E deletes — DONE (2026-06-17).** Deleted via MCP: retired rules WF002 `…796079`,
  WF003 `…784137`, WF010a `…800007`, WF010b `…800016` (workful-crud) + the `sequenceRouter`
  automation-function record `991103000000780386` (function-crud). The underlying Deluge code unit
  (`…780343`) may still exist in Dev Hub unbound — delete it there if desired (MCP can't). `Convert
  Lead` was already gone.

## 6. Deal-centric remnant cleanup (2026-06-17) — Contact-centric assessment + cleanup
**Assessment:** No v5 function manages comms/sequence at the Deal level — the model is fully
Contact-centric (verified: grep of `v5/` for `Sequence_Status`/`Next_Action_Due_Date`/
`Sequence_Paused_Until`/`Deal_Primary_Contact`/`Commercial_Outcome` = 0 matches; `processDeal` writes
only rollup + `Contact_Name`). The Deal layer is correctly Deal-as-context (rollup + commercial/contract
summary + Deal-event triggers that delegate to the Primary Contact). **No refactor needed.**

Done this session (MCP): deleted the 4 retired Deal-centric routers + `sequenceRouter` (above).

**Remaining (UI-only — no delete-field/edit-action MCP):**
- Delete 5 orphaned Deal fields (their only deps were the now-deleted rules; 0 refs in `v5/`):
  `Sequence_Status`, `Next_Action_Due_Date`, `Sequence_Paused_Until`, `Deal_Primary_Contact`
  (redundant with `Contact_Name`), `Commercial_Outcome` (confirm no report/list-view use first).
- Remove the leftover **`WF Placeholder Marker Deals`** field-update action (id `991103000000797001`)
  from **WF005 Demo Outcome Handler** (`…801001`) — it sits alongside the real `handleDemoOutcome`
  function action (the other 4 active Deal rules are clean). Benign "no-op" marker, but cruft;
  one-click removal in the workflow builder.
- Regenerate `.agents/context/api_field_names/zoho_deals_api_names.csv` from `getFields(Deals)` after
  the field deletions, and fix two pre-existing copy-paste errors in the API Name column: row
  **"Connected To"** (shows `Commercials_Status`) and row **"Contract Currency"** (shows `Contact_Name`).
- **MQL Cadence cleanup — BLOCKED:** needs `zoho-email-crud` reconnected (disconnected mid-session).
  Then retire the native "MQL" Sales Cadence (UI) and delete template `657010` + folder `657008`.
- **Git:** branch `email-template-rewrite`. `v5/` function edits + this session's docs are uncommitted.
  Commit when the user asks.
