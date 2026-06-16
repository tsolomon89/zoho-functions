# §12 Sequence_Type → Activity-Record Refactor (SCOPED — deferred, do as a tested change)

**Status: NOT implemented.** This is the one remaining architectural item from the plan's
§12. It is intentionally deferred because it is a multi-file behavioral change to the core
sequencing engine that cannot be tested in this environment, and a partial implementation is
worse than the current safe behavior. The email-template migration does **not** depend on it
(template resolution is already canonical/by-ID in `sendSequencedEmail`).

## Goal
`Sequence_Type` (Email / Call / Manual) selects **which activity record** is created around
the **one shared template chain** — it must NOT create parallel template families:
- **Email** path → a scheduled-email wake-up **Task** per cadence step (→ `sendScheduledEmailFromTask`).
- **Call** path → a **Call** record per cadence step (current behavior).
- **Manual** path → a manual rep **Task** per cadence step.

## Current behavior (verified in code)
- `_util_resolveContactAction` lines **89–97**: `activate:manual` → `Sequence_State=Stopped`
  (Manual is parked, not active). Only `activate:stop` should stop.
- Entry block lines **392–406** (cadence stages): branches only **Email**
  (`send_opener_then_call` — sends an opener email **then creates a Call**, a hybrid) vs
  else `create_call`. No Manual branch.
- Stepping: `call:neutral|noanswer` lines **116–139** drive the Call path (next Call +
  side cadence email; at step 5 → `schedule_email` postcall). There is **no pure
  Email-path stepping** (it falls into the Call path) and **no Manual stepping**.
- `task:positive` lines **190–196** advances the **whole stage** — so a Manual rep-Task
  completing would skip the cadence.

## Required changes (coordinated)
1. **Resolver `activate:manual`** → set `Sequence_Type=Manual` and route into the entry
   block (like `activate:email/call`); keep `activate:stop` as the only stop.
2. **Resolver entry block (cadence stages)** → add a 3-way branch on `Sequence_Type`:
   - Email → `schedule_email` step 1 (`emailKind` canonical `:1:initial`; drop the
     opener/`send_opener_then_call` hybrid so the Email path is pure scheduled email).
   - Call → `create_call` step 1 (current).
   - Manual → a new `create_rep_task` action step 1 (distinct from the task-class
     `create_task` used by Proposal Preparation / Onboarding).
3. **Resolver stepping** → add Email-path stepping (on scheduled-send completion, schedule
   step n+1 until K, then terminal `:K:final`) and Manual-path stepping (rep-Task neutral
   outcome → next rep Task step n+1; positive → advance stage; negative → stop).
4. **`routeContactSequence`** → handle `create_rep_task` (a non-blocking-or-blocking rep
   Task with `Sequence_Stage`/`Sequence_Attempt`, deduped like the Call path) and the pure
   Email cadence stepping; remove the `send_opener_then_call` hybrid (use `:1:initial`).
5. **`handleTaskCompletion`** → distinguish a Manual **rep-Task** outcome (step vs advance
   vs stop) from a task-class stage Task (advance) and from a scheduled-email wake-up Task
   (handled by `sendScheduledEmailFromTask`). Emit the right trigger token to the resolver.
6. **Template keys are already correct** — `sendSequencedEmail` maps `cadence`/`opener`/
   `postcall` → `:n:initial/follow-up/final`; once the resolver emits canonical kinds + the
   per-type actions, no template change is needed.

## Test gates (after implementing)
Run the same cadence stage with `Sequence_Type` = Email, Call, Manual and assert: the
rendered email never asserts a channel; each path creates only its own activity record type;
one email = one audit Task; Manual stepping advances per rep-Task outcome; no parallel
template family is used. (See `docs/v5/FUNCTION_DEPLOYMENT_RUNSHEET.md` smoke/E2E.)
