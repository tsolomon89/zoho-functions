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

## New finding — Calls module has no `Stale` field

`getFields(Calls)` contains **no field** whose api_name/label includes "stale". So every `{"Stale":"Yes"}` write to Calls — in `handleCallOutcome` (reschedule/CALL-1) and `routeContactSequence` (supersede) — is a **silent no-op** (Zoho drops unknown fields on update). This is pre-existing (the closeout inherited the `Stale` references; CALL-1 only added the `Status:Cancelled` + `Call_Task_Status:Closed` writes alongside it).

- **Impact:** functional non-actionability of a superseded/rescheduled Call is achieved via `Call_Task_Status=Closed` (verified — the replacement is the only Call in the Deal's actionable list). But `Call_Task_State` stays `Open` on the source and the intended `Stale` marker never lands, so any "open Calls" view that filters on `Call_Task_State=Open` alone (rather than `Call_Task_Status != Closed`) would still show the superseded source.
- **Recommendation (owner decision — field create not auto-applied):** either (a) create a `Stale` checkbox on Calls and confirm Tasks has the equivalent for scheduled-send supersede, or (b) standardise all "actionable Call/Task" views/COQL to filter on `*_Task_Status != Closed` and drop the dead `Stale` writes from the code. `"Status":"Cancelled"` on Calls is likely also dropped (Calls have no generic `Status` field) — confirm during the same pass.

## Deferred (time-gated, cannot complete in one session)

- Full Demo Hosted recovery cadence **steps 2–5** and **recovery-exhaustion → Contact Lost** — run on **business-day-scheduled** sends spanning days.
- Minor: "Email Sent" audit Task is created `Task_Status=New` (native `Completed`); ontology suggests `Closed`. Pre-existing in `sendSequencedEmail`, not a closeout regression.

## Optional / not done

- WF006 Condition 2 tightening (`+ Call_Task_State=Open`) — low priority; CALL-4 already clears `Next_Follow_Up_Date` so it cannot perpetually re-fire.
