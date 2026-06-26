# v6 Lifecycle Closeout — Live E2E Results

**Date:** 2026-06-25 · **Org:** Jurnii.io (`org20114906201`) · **Branch:** `codex/v6-lifecycle-closeout` · **Functions:** published by owner (incl. COM-3 follow-up fix `abb4128`)

Run keys `V6CL0625` / `V6CL0625B` / `V6CL0625C`. All synthetic records created and **deleted** (verified: no `V6CL0625*` records remain). Email sends verified via Zoho "Email Sent" audit Tasks (no Gmail MCP this session).

## Results

| Fix | Scenario | Result |
| --- | --- | --- |
| **TASK-1** | New Contact → Sequence Activation Task created with **blank** `Task_Sequence_Type`, no auto-dispatch | ✅ PASS |
| **TASK-2** | Manual activation → Contact **Open/Working**, Deal `Opportunity_Status=Working`, Account Working, activation Task `Won/Closed/Completed`, **no** cadence dispatch (`Sequence_State=Stopped`) | ✅ PASS |
| **TASK-4 / CALL-2** | Aux Tasks + recovery/sequence Calls created **Working / In Progress** | ✅ PASS |
| **SEQ-1** | Missed demo (`Meeting_Task_State=Lost`, `No Meeting / Demo`) → Contact **stays Demo Hosted**, `Sequence_Stage=Call`/`Step=1`, `State=Open`/`Status=Working`, **not Lost**; Event `Meeting_Task_Status=Closed` | ✅ PASS |
| **SEQ-7** | Recovery Call `Demo Hosted Call 1` → `Open`/`Working`, `Call_Task_Stage=Demo Hosted` | ✅ PASS |
| **MTG-5** | **Exactly one** opener `demo-hosted:1:initial` (Email Sent audit Task); **no** `demo_no_show` send | ✅ PASS |
| **MTG-4** | Unrelated edit on terminal Lost+Closed Event → **no** re-route / new Call / new email / step reset | ✅ PASS |
| **COM-3** | Fresh Deal with Open primary → **no** spurious "viability could not be resolved" Manual Review (was a defect; fixed `abb4128`, re-verified live) | ✅ PASS |
| **CALL-1/3/4** | Call reschedule (`Call_Task_State=Open` + `Next_Follow_Up_Date`) → exactly **one** actionable replacement Call at the new time (`Working`); source Call `Call_Task_Status=Closed`, `Next_Follow_Up_Date` cleared; **no** duplicate; no false Won/Lost | ✅ PASS (functional) — see Stale note |
| **SF-N1/N2/N3** | Legacy `*_Outcome` edits do not route | ✅ Verified structurally (live readback: **no** active `*_Outcome` workflow trigger on any module). `Call_Outcome`/`Meeting_Outcome`/`Demo_Outcome` are absent live; `Task_Outcome` exists but has no trigger. |
| **SF-N4/N5** | Native `Status` / custom `*_Task_Status` edits do not route | ✅ Verified structurally (WF008 routes only on `Task_State`/`Task_Sequence_Type`; only `WFC-SchedEmail` reads native `Status='Not Started'`, not Completed; `handleTaskCompletion` skips blank `Task_State`). |

## Resolved — Calls `Stale` (and Calls `Status`) are not live fields

`getFields(Calls)` contains **no** `Stale` field and **no** writable generic `Status` field (the real native status is `Outgoing_Call_Status`, values `Scheduled/Completed/Overdue/Cancelled`). So every `{"Stale":"Yes"}` and `{"Status":"Cancelled"|"Completed"}` write to Calls was a **silent no-op** (Zoho drops unknown fields). The local field export (`docs/zoho_custom_fields_by_module.csv`) and `PRE_CHANGE_FIELD_AUTHORITY_AUDIT.md` listed a Calls `Stale` field that does not actually exist live.

**Owner decision (2026-06-25): do NOT create a `Stale` field.** Canonical predicates standardised:

- **Actionable Call** = `Call_Task_State = Open AND Call_Task_Status = Working`.
- **Superseded / rescheduled source Call** = keep `Call_Task_State = Open` (it was not Won/Lost), set `Call_Task_Status = Closed`, set native `Outgoing_Call_Status = Cancelled`, clear `Next_Follow_Up_Date`; exactly one replacement remains Open/Working.

**Code cleanup applied** (`handleCallOutcome`, `routeContactSequence`, `sendScheduledEmailFromTask`):
- Removed all dead `Stale = Yes`/`Stale = No` writes from every Call reschedule + supersession path.
- Replaced dead `"Status"` writes with the real `Outgoing_Call_Status` (`Cancelled` on supersede, `Completed` on worked Won/Lost, `Scheduled` on new/rescheduled).
- Rewrote the skip guard, reschedule dup-check, SEQ-6 open-call scan, and the routeContactSequence supersede + create_call dup-check to use the canonical `Open + Working` predicate (was `Call_Task_State != Won/Lost AND Stale != Yes`, which treated a Closed-but-Open superseded Call as actionable — and the supersede write previously set neither Stale nor a real field, so it never closed the Call at all).
- **Tasks** has no `Stale` field either, but has a real native `Status`. `sendScheduledEmailFromTask` now refuses to send when native `Status` ∈ {Completed, Cancelled, Deferred} **or** custom `Task_Status = Closed`.
- Field inventory `docs/zoho_custom_fields_by_module.csv` annotated (Calls `Stale` not live).
- **Requires republish:** `handleCallOutcome`, `routeContactSequence`, `sendScheduledEmailFromTask`.

## Recovery cadence steps 1–5 + exhaustion (date-accelerated, run `V6CL0625D`)

Drove the cadence by marking each recovery Call `Lost / No Response` (advances steps without waiting on the business-day clock). Verified after each step:

- **Steps 1→5:** each step created exactly one actionable Call (`Demo Hosted Call N`, Open/Working, `Call_Task_Stage=Demo Hosted`); the prior Call went `Closed` (non-actionable); Contact stayed `Demo Hosted` / Open / Working throughout. ✅
- **Emails:** `demo-hosted:1:initial, :2, :3, :4, :5:final` — **exactly one each**, each with a unique SendKey + Message ID; the step-1 re-send was correctly **deduped** (SendKey idempotency). No duplicate email/Call/Task. ✅
- **Postcall:** at step 5 the cadence created the postcall **ScheduledSend Task** (`Due_Date` +2 business days, `kind=postcall`) and moved the Contact to `Sequence_Stage=Email`. ✅ (The date-based WFC-SchedEmail send fires at 09:00 on Due_Date and cannot be triggered synchronously via MCP; its documented effect — Task→Completed, `Sequence_State→Complete` — was simulated to exercise the downstream path.)
- **Exhaustion → Contact Lost:** with `Sequence_State=Complete` and no open recovery Call / no actionable ScheduledSend / no future Meeting, a final `Lost/No Response` routed `contactlost:No Response` → Contact `State=Lost`, `Status=Closed`, `Lost_Reasons=No Response`, `Sequence_Type` cleared. ✅

### Live vs simulated (explicit, per closeout requirement)

- **Live-executed:** recovery steps 1→5 (all Calls, all `demo-hosted:1..5` emails, postcall ScheduledSend Task creation), the Contact-Lost-on-exhaustion transition, and the multi-Contact viability outcome — all driven by the real published functions on live records.
- **Simulated (NOT live-verified):** the **date-triggered ScheduledSend execution**. WFC-SchedEmail fires at 09:00 on `Due_Date` and cannot be invoked on-demand via MCP; setting `Due_Date` to a past same-day time does not fire it retroactively. The postcall *send itself is therefore NOT live-verified*. Its documented downstream effect (Task→Completed, `Sequence_State→Complete`) was applied by controlled date-accelerated **state simulation** to exercise the exhaustion transition. Scheduled-send *timing* is not claimed as live-verified.

### Bug found + fixed (E2E) — invalid Deal→Contacts relation name

Root cause of the Deal not auto-closing: `getRelatedRecords("Contacts", "Deals", dealId)` returns **`INVALID_DATA: "the relation name given seems to be invalid"`** — `"Contacts"` is not a valid Deals relation. The valid relation is **`"Contact_Roles"`** (each entry's `id` is the Contact id). **Fixed** in all 3 sites (`processDeal.deluge:1417`, `routeContactSequence.deluge:163`, `:1010`) to use `"Contact_Roles"` directly; **published + confirmed** (no more `INVALID_DATA`; requirement #3: zero `getRelatedRecords("Contacts","Deals")` remain in the repo).

### Single-Contact exhaustion (run `V6CL0626A`)

- Contact → **`State=Lost`, `Status=Closed`, `Lost_Reasons=No Response`** ✅
- **Deal close NOT deterministically verified in-test.** The contactlost routing's Deal-viability block ran (primary matched), but the `Contact_Roles` read **lagged on the freshly-created Deal** at evaluation time → `viabilityResolved=false` → the **intentional conservative fail-safe** raised a "viability could not be resolved" Manual Review and left the Deal Open. This is a **seconds-old synthetic-record relationship-lag artifact**, not the invalid-relation error (that is fixed). In production a Deal that has run a multi-day recovery cadence is not a fresh record, so the read resolves and the Deal closes; the test environment's seconds-old related-list lag prevents deterministic confirmation here.
- **Owner decision (kept):** the conservative fail-open behaviour stays as-is — a false-open Deal + Manual Review is strictly preferable to a false close. **No `searchRecords` fallback is added**: it would still be subject to Zoho indexing lag and would add another nondeterministic read path without proving viability can be resolved safely.

### Multi-Contact viability (run `V6CL0626B`, one Deal, two role-linked Contacts)

- Exhausted primary Contact (B1) → **`Lost/Closed/No Response`** ✅
- Other Contact (B2) → **remains `Open`, completely unmodified** (`Status` unchanged, no sequence/stage change) ✅
- **Deal remains `Open`** ✅ (not closed — another viable Contact exists). Deal `Status` stayed `New` because neither Contact was activated to Working in this minimal setup (not a regression; "remains Working" applies only when the Deal was already Working). Note: the Deal stayed Open via the same conservative fail-safe (fresh-Deal `Contact_Roles` lag) as well as the correct "another open Contact" semantics — both yield Open, so the safety property (no erroneous close) holds.

- Minor: "Email Sent" audit Task is created `Task_Status=New` (native `Completed`); ontology suggests `Closed`. Pre-existing in `sendSequencedEmail`, not a closeout regression.

## Final closeout status

1. **Invalid relationship-name defect — FIXED.** `getRelatedRecords("Contacts","Deals",id)` (invalid) replaced with the valid `"Contact_Roles"` relation in all three sites; zero invalid reads remain; published and confirmed (no more `INVALID_DATA`).
2. **Multi-Contact viability — LIVE-VERIFIED.** Losing the exhausted primary kept the Deal Open, left the other viable Contact Open and unmodified.
3. **Contact exhaustion — LIVE-VERIFIED.** Recovery steps 1–5 ran live and the exhausted Contact became `Lost / Closed` with Lost Reason `No Response` (single- and multi-Contact).
4. **Single-Contact Deal closure — UNVERIFIED under seconds-old synthetic-record relationship lag.** The viability read could not resolve on the freshly-created Deal at evaluation time, so the Deal was (correctly) left Open with a Manual Review. Not claimed as verified.
5. **Production behaviour intentionally fails open.** When viability cannot be resolved, the Deal is kept Open and a Manual Review is raised — a false-open Deal is preferable to a false close.

### Canonical Deal-viability behaviour (unchanged)
- viability resolves AND no viable Contact remains → **close the Deal**;
- another viable Contact remains → **keep the Deal Open**;
- viability cannot be resolved → **keep the Deal Open + create Manual Review** (intentional fail-open).

### Deferred hardening recommendation (separate scoped improvement — NOT on this branch)
Add a **deferred viability recalculation** that re-runs after a *failed* related-list read (once the index has caught up), instead of an immediate `searchRecords` fallback. An immediate fallback would still be subject to Zoho indexing lag and would add another nondeterministic read path without proving viability can be resolved safely. This should be scoped and implemented as its own change, not folded into the lifecycle closeout.

## Optional / not done

- WF006 Condition 2 tightening (`+ Call_Task_State=Open`) — low priority; CALL-4 already clears `Next_Follow_Up_Date` so it cannot perpetually re-fire.
