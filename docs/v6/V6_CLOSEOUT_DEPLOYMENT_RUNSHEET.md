# v6 Lifecycle Closeout — Function Deployment Runsheet

**Branch:** `codex/v6-lifecycle-closeout` · **Source commit:** `cdf722e` ("v6 closeout: implement 15 lifecycle defect fixes") · **Org:** Jurnii.io (`org20114906201`) · **Date drafted:** 2026-06-25

## ⚠️ MCP cannot deploy Deluge bodies — manual deploy required

The connected Zoho Function MCP exposes function **metadata only**:
- `getAutomationFunctions(functionId)` returns *"Empty response received from API"* for every id — the deployed Deluge **body is not readable**.
- `putAutomationFunctions` updates only a function's **argument configuration** (name/type/value) and binding — there is **no body/source field**.
- `postAutomationFunctions` only **links** an already-created function by id — also no body field.

**Therefore these code changes CANNOT be deployed through the available tools.** They must be pasted into each function in the Zoho UI (**Setup → Developer Hub → Functions**, or the `/settings/functions` API which is not exposed here). Until that is done, **the live org runs the OLD code** and the fixes below are repo-only. Do **not** treat the functions as deployed, and do **not** run the new-logic E2E suite against live until after manual deploy (it would only exercise stale code).

## Functions to deploy (8 files changed in `cdf722e`)

Deploy **callees before callers** to avoid a transient mixed state. The 3 sub-functions are standalone (invoked via `invokeFunction`) and do **not** appear in `getAllAutomationFunctions`; find them in **Setup → Functions** by name.

| # | Repo file (paste body from this) | Live function name | Function id (if MCP-bound) | Defects in this file |
|---|---|---|---|---|
| 1 | `v6/activity/createAuxTask.deluge` | createAuxTask | *standalone — UI lookup* | TASK-4 (aux Tasks → In Progress/Working) |
| 2 | `v6/activity/applyCommercialTransition.deluge` | applyCommercialTransition | *standalone — UI lookup* | COM-1/4 (no force-reopen of Lost Deal) |
| 3 | `v6/activity/routeContactSequence.deluge` | routeContactSequence | *standalone — UI lookup* | SEQ-1 opener, SEQ-4 await_meeting, SEQ-5 supersede, TASK-1 clear Sequence_Type, TASK-2 Manual→Working, TASK-4/CALL-2 Working |
| 4 | `v6/processContact.deluge` | processContact | `991103000000774692` | TASK-1 (blank Task_Sequence_Type) |
| 5 | `v6/processDeal.deluge` | processDeal | `991103000000774697` | COM-2 (Deal-Roles viability), COM-3/COM-5 fail-safes |
| 6 | `v6/activity/handleMeetingEvent.deluge` | handleMeetingEvent | `991103000000780334` | SEQ-1 (demo:followup), MTG-1 (hasNext), MTG-4 (idempotency guard) |
| 7 | `v6/activity/handleCallOutcome.deluge` | handleCallOutcome | `991103000000780322` | CALL-1/3/4, CALL-2, SEQ-6 (exhaustion) |
| 8 | `v6/activity/handleCommercialsStatusChange.deluge` | handleCommercialsStatusChange | `991103000000780325` | COM-1 (skip Lost Deal) |

> Function ids are the **function** ids, not the workflow-association ids. Bindings/criteria are unchanged by this closeout — only the bodies change — so no `putAutomationFunctions` argument edits are needed.

## Per-function deploy steps (repeat for each row, in order)

1. Open the repo file at commit `cdf722e` (e.g. `git show cdf722e:v6/activity/routeContactSequence.deluge`).
2. In **Setup → Functions**, open the matching function and **replace the entire body** with the repo body.
3. **Save & Publish.** Confirm no syntax errors are reported by the Deluge editor.
4. Note the timestamp; record it against the row above as your deploy evidence (MCP cannot read the body back to diff).

## Post-deploy verification (record/behaviour evidence — the only proof available)

Because bodies aren't MCP-readable, verify via **live record behaviour** with synthetic records (Gmail plus-addressing `t.l.c.solomon+<RUN_KEY>@gmail.com`), then delete them. Minimum smoke checks before the full E2E suite:

- **Demo missed:** Meeting `Meeting_Task_State=Lost`, `Meeting_Task_Lost_Reasons="No Meeting / Demo"` → Contact stays **Demo Hosted** (not Demo Booking), State=Open/Status=Working, one recovery Call mirrored to Demo Hosted, **exactly one** opener email (`demo-hosted:1:initial`), **no** one-off no-show email.
- **Meeting No-Response (not exhausted):** Contact is **not** immediately Lost; recovery continues.
- **Meeting terminal idempotency:** unrelated edit on a Won/Lost+Closed Event does **not** re-route / re-send / re-create tasks.
- **Activation prefill:** new Sequence Activation Task created with **blank** `Task_Sequence_Type`; no auto-dispatch until a rep selects Email/Call/Manual.
- **Manual activation:** Contact/Deal/Account → Working, activation Task closes, **no** cadence dispatch.
- **Call reschedule:** `Call_Task_State=Open` + `Next_Follow_Up_Date` change → one actionable Call; source Call Stale+Cancelled+Closed; `Next_Follow_Up_Date` cleared.

Full matrix: `docs/v6/E2E_TEST_HARNESS.md` (T1–T50) and `docs/v6/SINGLE_FIELD_E2E_TEST_PLAN.md`.

## Not in this deploy (gated / deferred)

- **Email-template rewrites** (Demo Hosted recovery copy / merge syntax) — deferred; read-back now possible via the new Email CRUD MCP (see `docs/v6/V6_EMAIL_COPY_VERIFICATION.md`). Verify the live `demo-hosted:1:initial` copy does **not** assume attendance **before** enabling the missed-demo recovery in production.
- **WF006 Condition 2 tightening** (optional: add `Call_Task_State=Open`) — the CALL-4 code change (clearing `Next_Follow_Up_Date`) already removes the re-trigger source; criteria edit is optional defense-in-depth, pending approval of exact criteria.
- **WF004 deactivation / `Commercials_Status` retirement** — gated (cross-coupled to WF021 publish + signature proofs).
- **Field deletes** — none authorized. `Commercial_Outcome` (empty) and `Commercials_Status` (WF004-bound) remain. `Task_Outcome` holds data → blocked.
