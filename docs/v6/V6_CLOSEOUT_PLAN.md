# v6 Lifecycle Closeout Plan

Date: 2026-06-25
Branch: `codex/v6-lifecycle-closeout`
Target org: Jurnii.io, `org20114906201`

This plan consolidates the read-only repository audit (5 defect clusters), the live Zoho readback
(4 clusters: workflows, fields, functions, templates), and the synthesis into a single deduped,
ordered defect-closure plan with a gated-actions register and open product questions. No `.deluge`
code, workflows, fields, or live Zoho state were modified to produce this document.

## Executive Summary

> v6 lifecycle closeout synthesis over 5 repo-audit clusters + 4 live-readback clusters (workflows,
> fields, functions, templates), org Jurnii.io (org20114906201), branch main, date 2026-06-25. After
> dedupe, the demo/meeting findings collapse to ONE root cause: a missed/lost demo (Lost reason "No
> Meeting / Demo") is mis-routed. handleMeetingEvent.deluge line 222 routes demo:noshow (which reverts
> the Contact to Demo Booking, routeContactSequence.deluge lines 550-555) instead of the correct
> demo:followup token (lines 533-537, target Demo Hosted) — and demo:followup currently has NO caller,
> so the entire Demo Hosted 5-step recovery cadence is dead code. The same handler also (a) hard-codes
> hasNextStep="false" on both Lost paths (lines 154, 212) so a first No-Response is treated as terminal
> sequence exhaustion -> immediate Contact Lost, and (b) lacks the terminal-idempotency guard its peer
> handleTaskCompletion has, so any later edit on a Won/Lost+Closed Event re-runs
> progression/processDeal/recovery/emails. These three (MTG-1/SEQ-1/SEQ-2, MTG-4) are blockers. Verified
> against source: lines 154/212 pass literal "false"; line 221 comment encodes the wrong "revert to Demo
> Booking" intent; line 222 routes demo:noshow; demo:followup (533-537) targets Demo Hosted;
> processContact.deluge line 317 conditionally copies the residual Contact.Sequence_Type onto a new
> Activation Task (TASK-1 blocker, auto-activation leak). Call-handling is in good shape post-2026-06-25
> WF006 fix (Condition 2 added, idempotency retest PASS) — the residual CALL items are repo-only
> hardening (source-Call left open with only Stale=Yes at handleCallOutcome lines 269/274 vs the
> Stale+Cancelled pattern at line 265). Live state largely matches docs: 11 active rules across the 6
> modules, NO active *_Outcome trigger anywhere, WF008 single no-criteria condition (no duplicate
> Status=Completed branch), WF006 dual condition confirmed. Divergences that gate cleanup:
> WF004/Commercials_Status legacy bridge still ACTIVE; Task_Outcome still LIVE and holding data; function
> bodies and email-template copy/active-status are NOT readable via MCP (cannot prove deployed Deluge ==
> repo, cannot confirm the Demo Hosted Initial-1 template carries corrected vs attendance-implying draft
> copy). Plan orders 13 deduped items repo-only/code-first, then gated live changes; obsolete-field audit
> covers all 8 named candidates (5 already absent, Task_Outcome blocked, Commercial_Outcome +
> Commercials_Status safe-to-delete-after-dependency-check); plus a "Renewall" picklist typo across 5
> Stage fields flagged as a separate data-quality cleanup.

## Defect Closure Plan

13 deduped items, ordered repo-only / code-first, then gated live changes. The demo:noshow ->
demo:followup root cause (SEQ-1) collapses MTG-1/2/3, SEQ-1/2/7/8 and MTG-5.

| # | ID | Title | Deployment | Depends on |
| --- | --- | --- | --- | --- |
| 1 | TASK-1 | processContact pre-arms Activation Task with residual Contact.Sequence_Type (auto-activation leak) | requires-redeploy | none |
| 2 | SEQ-1 | Missed/lost demo routes demo:noshow (reverts to Demo Booking) instead of demo:followup (stays Demo Hosted); revives dead recovery cadence (SEQ-2) | requires-redeploy | none |
| 3 | SEQ-4 | Demo Hosted entry on meeting:attended jumps straight to Call cadence; no "awaiting Meeting outcome" sub-state | requires-redeploy | SEQ-1 |
| 4 | MTG-1 | Meeting Lost hard-codes hasNextStep="false", forcing first No-Response to terminal Contact Lost | requires-redeploy | SEQ-4 |
| 5 | SEQ-6 | Recovery-exhaustion -> Contact Lost has no explicit precondition check; failed postcall send strands Contact in Running | requires-redeploy | SEQ-1 |
| 6 | MTG-4 | handleMeetingEvent lacks terminal-idempotency guard; later edits re-run progression, processDeal, recovery, emails | requires-redeploy | none |
| 7 | COM-2 | Deal-loss viability scope diverges: processDeal uses Account Contacts, routeContactSequence uses Deal Contact Roles | requires-redeploy | none |
| 8 | COM-3 | processDeal closes Deal on no-open-Contact without the fail-safe routeContactSequence has | requires-redeploy | COM-2 |
| 9 | COM-5 | Account Status rollup can wrongly Close on an unresolved related-list read | requires-redeploy | COM-3 |
| 10 | CALL-1 | Reschedule leaves source Call open (only Stale=Yes; no Cancelled / no Call_Task_Status close) | repo-only | none |
| 11 | CALL-4-clear | Reschedule never clears Next_Follow_Up_Date, leaving WF006 Condition 2 as a permanent re-trigger source | repo-only | CALL-1 |
| 12 | CALL-3 | Reschedule dedupe falls through to createRecord on a related-list read failure (duplicate-Call risk) | repo-only | CALL-1 |
| 13 | CALL-2/TASK-4 | Automation-created in-flight sequence Calls/Tasks created New/Not-Started instead of Working | repo-only | none |
| 14 | TASK-2 | Manual activation suppresses dispatch but never marks Contact/Deal Working | requires-redeploy | none |
| 15 | COM-1/COM-4-code | Legacy Commercials_Status wrapper still reads the field and can drive routing / re-open a Lost Deal (code half) | requires-redeploy | none |

> Note: the synthesis numbers this a "13 deduped items" plan; the table above lists each `defectClosurePlan`
> entry as published (some entries combine two original defect IDs, e.g. CALL-2/TASK-4 and COM-1/COM-4-code).

### 1. TASK-1 — processContact pre-arms Activation Task with residual Contact.Sequence_Type (auto-activation leak)

- **Files:** `v6/processContact.deluge` (lines 305, 317)
- **Deployment:** requires-redeploy
- **Depends on:** none
- **Fix:** Delete the conditional put at line 317 (`if(existingSeqType != "") actTask.put("Task_Sequence_Type", existingSeqType)`) and the now-unused read at line 305. Always create the Activation Task with `Task_Sequence_Type` BLANK so the rep explicitly chooses Email/Call/Manual. The inline comment at 296-304 already states this is the contract; line 317 contradicts it. If genuine re-activation pre-fill is ever wanted, gate it on an explicit signal (`Sequence_State==Stopped` AND reactivate flag), never on residual `Sequence_Type`. Confirm `routeContactSequence` never CLEARS `Contact.Sequence_Type` when a sequence Stops/Completes (line 869 only sets it) — if it does not, stale values accumulate and this leak hits normal Contacts, so also clear `Sequence_Type` on Stop/Complete.
- **Verification:** Create a Contact carrying a stale `Sequence_Type`; run processContact; read the new Sequence Activation Task and confirm `Task_Sequence_Type` is blank. Then confirm WF008/handleTaskCompletion does NOT auto-route on Task create (no Email/Call dispatch, no sequence advance) until a rep sets `Task_Sequence_Type`. Delete synthetic records after.

### 2. SEQ-1 — Missed/lost demo routes demo:noshow instead of demo:followup (revives dead recovery cadence)

- **Files:** `v6/activity/handleMeetingEvent.deluge` (lines 219-223; comment 221); `v6/activity/routeContactSequence.deluge` (demo:followup 533-537, demo:noshow 550-555)
- **Deployment:** requires-redeploy
- **Depends on:** none
- **Fix:** In handleMeetingEvent the demo Lost continue_cadence branch (line 222) currently calls `routeContactSequence(...,'demo:noshow','{}')`. Change it to route `'demo:followup'`, which sets `targetStage='Demo Hosted'` with supersede+entry and runs the Demo Hosted Call-first 5-step recovery cadence (demo-hosted:1..5). This single change closes SEQ-1, SEQ-2 (demo:followup was dead code with no caller), MTG-3 (regression to Demo Booking), and SEQ-7 (recovery activity Stage mirror then auto-stamps Demo Hosted). Fix the misleading comment at line 221 ("revert to Demo Booking and recover with a call"). Keep demo:noshow reserved ONLY for genuine confirmed-meeting no-show -> rebook if that revert is still wanted (SEQ-8); add a code comment documenting the distinction. Resolve the demo_no_show side-email vs demo-hosted:1 opener overlap (MTG-5) at the same time — pick ONE opener for the missed-demo path so a single missed demo does not fire both demo-confirmation:0:no-show AND demo-hosted:1:initial.
- **Verification:** Create Contact at Demo Hosted with a Meeting; set `Meeting_Task_State=Lost`, `Meeting_Task_Lost_Reasons='No Meeting / Demo'`. Confirm Contact stays Stage=Demo Hosted (not Demo Booking), State=Open, Status=Working, Sequence_Stage=Call, Step=1, and a recovery Call is created mirrored to Stage=Demo Hosted. Confirm EXACTLY ONE opener email is sent (check Email Sent ledger / audit Task across both canonical keys). Delete synthetic records. NOTE: live send verification is a gated E2E action.

### 3. SEQ-4 — Demo Hosted entry on meeting:attended jumps straight to Call cadence; no "awaiting Meeting outcome" sub-state

- **Files:** `v6/activity/routeContactSequence.deluge` (meeting:attended 623-627; entry block 715-741)
- **Deployment:** requires-redeploy
- **Depends on:** SEQ-1
- **Fix:** On first arrival at Demo Hosted via meeting:attended set `Sequence_Stage='Meeting'`, `Step='None'`, `action=await_meeting` (awaiting the Won/Lost/No-Response outcome) rather than entering the generic cadenceStage Call path. Only on a Meeting Lost/No-Response outcome transition to `Sequence_Stage='Call'`, `Step='1'` to begin recovery (the demo:followup path from SEQ-1). This makes the two Demo Hosted sub-states cleanly distinguishable by existing fields (Meeting/None = awaiting; Call/1-5 = recovery) with NO new field, and supplies the awaiting-vs-recovery distinction MTG-2 needs. Confirm first where meeting:attended is emitted (open question MTG-6: the router branch exists but no demo/meeting handler routes it — the Demo Confirmation->Demo Hosted awaiting-outcome advance may currently have no live trigger).
- **Verification:** Drive a Contact Demo Confirmation->Demo Hosted via the meeting:attended trigger (once located). Confirm it lands Sequence_Stage=Meeting, Step=None, no recovery Call created, no cadence email. Then a Meeting Lost flips it to Sequence_Stage=Call Step=1 (one recovery seed). Delete synthetic records.

### 4. MTG-1 — Meeting Lost hard-codes hasNextStep="false", forcing first No-Response to terminal Contact Lost

- **Files:** `v6/activity/handleMeetingEvent.deluge` (lines 154, 212; read Sequence_State near 76-78)
- **Deployment:** requires-redeploy
- **Depends on:** SEQ-4
- **Fix:** Both resolveActivityLoss calls pass the literal `"false"` as hasNextStep (confirmed at lines 154 and 212). The handler never reads Contact `Sequence_State`. Load `Sequence_State` from the `cFull` record already fetched at lines 76-78, compute `hasNext = (seqState=='Complete') ? 'false' : 'true'`, and pass it into BOTH calls in place of `"false"`. This matches peer handlers handleCallOutcome (292-293) and handleTaskCompletion (224-225), which only escalate No Response to Contact Lost when `Sequence_State=='Complete'`. With SEQ-1/SEQ-4 in place this becomes consistent: a missed demo recovers at Demo Hosted and only exhausts to Contact Lost after genuine recovery completion.
- **Verification:** Set `Meeting_Task_State=Lost`, Lost Reason='No Response' on a Contact whose Sequence_State is Running (not Complete). Confirm the Contact is NOT routed contactlost:No Response (stays Open, enters recovery). Then with Sequence_State=Complete confirm it does route Contact Lost / No Response. Delete synthetic records.

### 5. SEQ-6 — Recovery-exhaustion -> Contact Lost has no explicit precondition check; failed postcall send strands the Contact in Running

- **Files:** `v6/activity/handleCallOutcome.deluge` (lines 289-309)
- **Deployment:** requires-redeploy
- **Depends on:** SEQ-1
- **Fix:** Make exhaustion explicit instead of relying solely on `Sequence_State==Complete` (which only flips via the postcall scheduled send and is skipped if that send fails). When a recovery No-Response Lost arrives at `Sequence_Stage='Call'` Step==5 (or postcall sent), verify: (a) no open Sequence_Managed Call for this Contact+Deal, (b) no actionable ScheduledSend Task, (c) no open/valid future Meeting (Events Who_Id=Contact, future Start_DateTime, State!=Lost), (d) no reply signal, (e) Stage unchanged, (f) Sequence_State not Stopped. Only then route contactlost:No Response; else continue_cadence. Ensure a failed postcall send (sendSequencedEmail returns '') does not silently leave the Contact Running with no escalation path. NOTE open question: locate which function flips an email audit Task to Won/replied so the "no reply" precondition can be checked.
- **Verification:** Run the full Demo Hosted recovery to step 5 with No-Response at each step; confirm Contact Lost only fires once all six preconditions hold. Simulate a postcall send failure and confirm the Contact is not stranded (retried/escalated, not left Running indefinitely). Delete synthetic records.

### 6. MTG-4 — handleMeetingEvent lacks terminal-idempotency guard; later edits re-run progression, processDeal, recovery, emails

- **Files:** `v6/activity/handleMeetingEvent.deluge` (add guard after line 66; pattern from handleTaskCompletion 200-207)
- **Deployment:** requires-redeploy
- **Depends on:** none
- **Fix:** WF007 fires on create_or_edit with no criteria (live-confirmed). The handler writes `Meeting_Task_Status=Closed` only AFTER routing/processDeal/recovery (lines 139,160,199,218) and never checks it on entry. Add an early guard after mState/mReason/mStage are read (after line 66): read `mStatus=Meeting_Task_Status`; if `(mState=='Won' || mState=='Lost') && mStatus=='Closed'` then log skip_state_already_processed and return, before any routing/processDeal/createAuxTask. Mirrors the proven handleTaskCompletion guard. This also remediates the documented historical-Event drift (Won + Status=New) once those records are reprocessed.
- **Verification:** Process a Won demo Event to completion (Status=Closed); make an unrelated edit (e.g. change Description) and confirm WF007 re-fire does NOT re-route demo:qualified, does NOT re-invoke processDeal (no duplicate Quote/ledger), and sends no second email. Repeat for a Lost demo (no second Manual Review / recovery seed). Delete synthetic records.

### 7. COM-2 — Deal-loss viability scope diverges: processDeal uses Account Contacts, routeContactSequence uses Deal Contact Roles

- **Files:** `v6/processDeal.deluge` (lines 145, 1408-1415); `v6/activity/routeContactSequence.deluge` (920-979)
- **Deployment:** requires-redeploy
- **Depends on:** none
- **Fix:** Unify on ONE canonical viable-Contact definition. Deal Contact Roles (per-Deal, as routeContactSequence already uses) is the more precise set. Change processDeal's anyContactOpen to consider only Contacts role-linked to targetDealId rather than all Account-related Contacts (or factor a shared `_util_resolveDealViableContacts` used by both). Resolve the open question on canonical scope before changing. Also confirm whether `Deals.Reason_For_Loss__s` or custom `Lost_Reasons` is the canonical loss field (processDeal lines 1405-1407 treat either as hasLossReason but writes use Lost_Reasons).
- **Verification:** Construct a Contact open on the Account but NOT role-linked to a given Deal (and vice versa); run processDeal and routeContactSequence loss paths; confirm both agree on whether the Deal stays Open or closes Lost. Delete synthetic records.

### 8. COM-3 — processDeal closes Deal on no-open-Contact without the fail-safe routeContactSequence has

- **Files:** `v6/processDeal.deluge` (lines 1408-1415)
- **Deployment:** requires-redeploy
- **Depends on:** COM-2
- **Fix:** Add a `viabilityResolved` guard around the rollup close, mirroring routeContactSequence (934-964): only set `Opportunity_State=Lost` when the viable-Contact set was resolved with confidence; otherwise log + createAuxTask Manual Review and leave state unchanged. Prevents an API hiccup on the related-list read from silently closing a Deal.
- **Verification:** Simulate an unresolved/partial Contact viability read; confirm processDeal does NOT close the Deal and instead raises Manual Review, matching routeContactSequence behavior. Delete synthetic records.

### 9. COM-5 — Account Status rollup can wrongly Close on an unresolved related-list read

- **Files:** `v6/processDeal.deluge` (lines 1599-1644)
- **Deployment:** requires-redeploy
- **Depends on:** COM-3
- **Fix:** Guard the else (close) branch: only roll the Account to `State=Lost`/`Status=Closed` when `finalDeals` was actually resolved (response starts with `[` and the loop examined deals); otherwise skip the Account write and log. Mirrors the conservatism applied in COM-3.
- **Verification:** Simulate an empty/error finalDeals response; confirm the Account is NOT flipped to Lost/Closed. With a genuine no-open-Deal set, confirm it does close. Delete synthetic records.

### 10. CALL-1 — Reschedule leaves source Call open (only Stale=Yes; no Cancelled / no Call_Task_Status close)

- **Files:** `v6/activity/handleCallOutcome.deluge` (lines 269, 274)
- **Deployment:** repo-only
- **Depends on:** none
- **Fix:** Confirmed: lines 269 and 274 write only `{"Stale":"Yes"}` on the source Call, leaving `Call_Task_State=Open` / `Call_Task_Status=New` / native Status open, so a second actionable Call appears in any view not filtering on Stale. Change both writes to `{"Stale":"Yes", "Status":"Cancelled", "Call_Task_Status":"Closed"}` to match the surplus-replacement cleanup at line 265 and the routeContactSequence supersede at line 791. Keep `Call_Task_State` unchanged (do NOT write Won/Lost).
- **Verification:** Trigger a reschedule (Open Call + Next_Follow_Up_Date); confirm exactly one actionable Call remains and the source Call reads Status=Cancelled, Call_Task_Status=Closed, Stale=Yes, Call_Task_State unchanged. Delete synthetic records.

### 11. CALL-4-clear — Reschedule never clears Next_Follow_Up_Date, leaving WF006 Condition 2 as a permanent re-trigger source

- **Files:** `v6/activity/handleCallOutcome.deluge` (reschedule paths ~258-275)
- **Deployment:** repo-only
- **Depends on:** CALL-1
- **Fix:** After acting on the follow-up date, write `Next_Follow_Up_Date=null` on the processed Call so WF006 Condition 2 (`Next_Follow_Up_Date != EMPTY AND Sequence_Managed=Yes`) cannot perpetually re-fire. This is the repo-only half of CALL-4. The optional live-side defense (tighten WF006 Condition 2 to also require `Call_Task_State=Open`) is captured separately as a gated live-workflow item.
- **Verification:** After a reschedule, confirm Next_Follow_Up_Date is cleared on the processed Call and a subsequent unrelated edit does not re-invoke the reschedule branch. Delete synthetic records.

### 12. CALL-3 — Reschedule dedupe falls through to createRecord on a related-list read failure (duplicate-Call risk)

- **Files:** `v6/activity/handleCallOutcome.deluge` (catch block ~235-239; reschedule 162-277)
- **Deployment:** repo-only
- **Depends on:** CALL-1
- **Fix:** In the catch block, do NOT silently set `existingRescheduleCallId=""` and proceed to createRecord when the related-list dedupe scan failed — log and return without creating, so a transient getRelatedRecords lag cannot mint a duplicate replacement Call. (Optional larger change: implement true in-place reschedule — update the same Call's Call_Start_Time, clear Next_Follow_Up_Date, keep State=Open/Status=Working — but document that replacement-Call is the locked design first; see open question.)
- **Verification:** Inject a related-list read failure on the reschedule path; confirm no duplicate Call is created (handler aborts+logs). Confirm normal reschedule still produces exactly one replacement. Delete synthetic records.

### 13. CALL-2/TASK-4 — Automation-created in-flight sequence Calls/Tasks created New/Not-Started instead of Working

- **Files:** `v6/activity/handleCallOutcome.deluge` (lines 186, 248); `v6/activity/routeContactSequence.deluge` (create_task 1253, 1266; create_call 1168); `v6/activity/createAuxTask.deluge` (67, 75-76)
- **Deployment:** repo-only
- **Depends on:** none
- **Fix:** Pending the lifecycle-owner decision (open question: is ANY automation-created sequence activity immediately Working, or do brand-new Calls stay New until the rep starts and only rescheduled/in-flight become Working?). Once decided: for the create_task stage tasks set `Status='In Progress'`, `Task_Status='Working'` (`Task_State` stays Open) at routeContactSequence 1253/1266; apply the same to rescheduled Calls at handleCallOutcome 186/248 and create_call 1168 if the rule is "in-flight=Working". Keep the Sequence Activation Task as the sole New exception and Email-audit Tasks as the sole Closed exception. Decide createAuxTask (Manual Review/Data Repair) separately — these may legitimately stay New until a human picks them up. Confirm WF008 gates only on Task_State/Task_Sequence_Type so a Status=Working create is safe.
- **Verification:** After the convention is set, create the relevant activities and confirm Status/Task_Status match the agreed convention and that no spurious WF008/WF006 routing fires on the Working initialization. Delete synthetic records.

### 14. TASK-2 — Manual activation suppresses dispatch but never marks Contact/Deal Working

- **Files:** `v6/activity/routeContactSequence.deluge` (lines 414-422, 897-908, 1418)
- **Deployment:** requires-redeploy
- **Depends on:** none
- **Fix:** For activate:manual (`nextSeqType='Manual'`, `nextSeqState='Stopped'`), the Contact Status->Working write is gated only on `nextSeqState=='Running'` (lines 903-908), so Manual activation leaves Contact (and via anyContactWorking, Deal Opportunity_Status and Account Status) at New. Either broaden the Status->Working condition to include the Manual-activation case (e.g. `isActivation && nextSeqType=='Manual'`) while keeping dispatchSuppressed true, or add `cUpd.put('Status','Working')` on the activation_stop/Manual branch. Ensure processDeal then rolls Deal Opportunity_Status to Working via anyContactWorking. Confirm this does NOT re-enable email/call dispatch.
- **Verification:** Activate a Contact via `Task_Sequence_Type=Manual`; confirm Contact State=Open/Status=Working, Deal Opportunity_Status=Working, Account Status=Working, the activation Task closes Won/Closed/Completed, and NO cadence email/call is dispatched. Delete synthetic records.

### 15. COM-1/COM-4-code — Legacy Commercials_Status wrapper still reads the field and can drive routing / re-open a Lost Deal (code half)

- **Files:** `v6/activity/handleCommercialsStatusChange.deluge` (lines 20-32); `v6/activity/applyCommercialTransition.deluge` (lines 80-86)
- **Deployment:** requires-redeploy
- **Depends on:** none
- **Fix:** Code-side preparation for the WF004/Commercials_Status retirement (the WF004 deactivation + field delete are gated live actions, tracked separately). Remove the unconditional `Opportunity_State=Open` write from applyCommercialTransition 'signed' (lines 80-86) so it cannot re-open a deliberately Lost Deal — let processDeal/routeContactSequence own viability (COM-4). Once WF004 is confirmed the sole trigger and is deactivated, guard handleCommercialsStatusChange + applyCommercialTransition to log-only or delete them. Do NOT duplicate the canonical processDeal commercial gate (Delivered->commercial:sent, term Confirmed->commercial:signed) with a Commercials_Status route.
- **Verification:** With a Lost Deal, simulate a stray `Commercials_Status='Signed'` and confirm the Deal does NOT re-open. Confirm canonical commercial transitions still fire via the Quote/processDeal gate. NOTE: full closure depends on the gated WF004 deactivation + field delete.

## Gated Actions (require explicit user authorization)

These actions touch live Zoho state, outward-facing copy, or irreversible deletes. None were taken
in this read-only/docs-only pass.

- [ ] **Rewrite live email template copy** — in particular correct 'Demo Hosted - Initial 1' (991103000001476007) so the demo-hosted recovery opener does not assume attendance, and replace any rejected merge syntax (`${Organization...}`, no-bang tags) with the verified `${!<Module>.<Field>}` form. Template copy is not MCP-readable so changes are blind and outward-facing.
- [ ] **Edit live workflow rules** — (a) optionally tighten WF006 Condition 2 to add `Call_Task_State=Open` (CALL-4 live half); (b) deactivate/delete WF004 Commercials Status Handler (id 991103000000800001) as part of the Commercials_Status retirement; (c) any change to WF007 (still broad no-criteria) or WF008. All workflow edits need explicit sign-off.
- [ ] **Redeploy (putAutomationFunctions) any Deluge function** — all "requires-redeploy" plan items (TASK-1, SEQ-1, SEQ-4, MTG-1, MTG-4, SEQ-6, COM-1/4 code, COM-2/3/5, TASK-2). Function bodies cannot be round-trip-verified via MCP (GET returns empty), so redeploys are write-without-readback and must be user-authorized and externally verified.
- [ ] **Delete live custom fields** — Commercial_Outcome (safe-after-dependency-check, empty) and Commercials_Status (blocked until WF004 deactivated, empty). Task_Outcome must NOT be deleted (holds data, dependencies unanalysed). NEVER delete native fields. Any field delete is irreversible and gated.
- [ ] **Correct the 'Renewall' picklist typo** across the five Stage fields (Contacts.Stage, Task_Stage, Call_Task_Stage, Meeting_Task_Stage, Deals.Opportunity_Stage) — picklist value edits touch live data/records and are gated.
- [ ] **Run any live E2E test** that creates real CRM records and/or sends real Gmail emails (all plan-item verifications that mention live send, the missed-demo recovery opener, Manual activation, commercial Quote evidence, recovery-exhaustion). Synthetic records must be created and then deleted, and real-email sends require explicit authorization.
- [ ] **Reprocess the documented historical Event drift records** (Meeting_Task_State=Won while Meeting_Task_Status=New) once MTG-4 is deployed — touches live records.
- [ ] **Hide/DEP-rename live fields** (Task_Outcome hide, layout/conditional-rule hardening for Lost-Reason-only-when-Lost and Task_Sequence_Type-only-for-activation) — outward-facing layout changes.

## Open Product Questions (block deployment)

These must be answered by a human before the dependent fixes deploy. Gathered from the per-cluster
`openQuestions` and the deployment-blocking risks.

### Demo / Meeting (gate SEQ-1 / SEQ-4 / SEQ-6 / MTG-5)

1. Where is `meeting:attended` emitted from in the live flow? The router branch (routeContactSequence 623-627) advances Demo Confirmation -> Demo Hosted, but no demo/meeting handler in v6/activity routes it. Confirm whether the Demo Hosted "awaiting outcome" advance has any live trigger, or whether the Contact only reaches Demo Hosted on demo:qualified/Won (skipping awaiting-outcome).
2. Is the intended missed-demo recovery cadence anchored at **Demo Hosted** (demo-hosted:1..5 templates) or at **Demo Booking** (current behaviour)? The template registry has a full demo-hosted:1..5 family, strongly implying Demo Hosted; confirm against the canonical lifecycle spec before changing the demo:noshow target (MTG-3/SEQ-1).
3. For the one-off no-show email vs demo-hosted:1 opener (MTG-5): which is the canonical single opener? Confirm whether demo-confirmation:0:no-show is a courtesy notice that should coexist with the cadence opener, or whether exactly one send is required.
4. Confirm the Contact field that carries recovery step state at Demo Hosted (`Sequence_Step`) so a "start recovery step-1 ONCE" guard (MTG-2/MTG-3/SEQ-1) can be implemented idempotently across repeat WF007 edits.
5. Should the Demo Hosted recovery lead with the demo-hosted:1:initial email (opener) on entry, or is it Call-first with cadence emails accompanying each subsequent neutral call outcome (current behavior)? Affects SEQ-3.
6. Is demo:noshow's revert-to-Demo-Booking still a wanted behavior for a confirmed-meeting no-show, or should ALL demo-loss paths stay at Demo Hosted? Determines whether demo:noshow is repurposed or retained alongside demo:followup (SEQ-8).
7. On a failed postcall send (sendSequencedEmail returns ''), the Contact is left Running with a retryable scheduled Task and no escalation. What is the intended retry/exhaustion behavior so a send failure cannot strand the Contact short of Contact Lost (SEQ-6)?
8. Where is "no reply recorded" tracked for the recovery-exhaustion precondition? No reviewed reply-detection path was found in the four audited files; confirm which function flips an email audit Task to Won/replied so SEQ-6 can check "no reply".

### Call handling (gate CALL-2, CALL-3, CALL-4)

9. CALL-2/TASK-4: Is the intended convention that ANY automation-created sequence activity is immediately `Call_Task_Status=Working` / `Task_Status=Working`, or that brand-new Calls stay New until the rep starts work and only rescheduled/in-flight become Working? Need the lifecycle owner to confirm before changing lines 186/248/1168/1253/1266 (and createAuxTask 67/75).
10. CALL-4: Should reschedule actively clear Next_Follow_Up_Date on the source/replacement Call (recommended), and/or should WF006 Condition 2 be tightened to also require Call_Task_State=Open (a live-workflow edit)?
11. CALL-3: Is the replacement-Call model (vs true in-place reschedule) the intended/locked design? The fix differs depending on the answer.

### Task / Activation (gate TASK-1, TASK-4)

12. TASK-1: Confirm there is no legitimate re-activation flow that RELIES on `Task_Sequence_Type` being pre-filled from `Contact.Sequence_Type`. If such a flow exists it must be re-expressed behind an explicit reactivation signal.
13. Does routeContactSequence ever clear `Contact.Sequence_Type` when a sequence Stops/Completes? Line 869 only sets it; if it never clears, stale values accumulate and the TASK-1 leak hits normal Contacts.
14. TASK-4: Confirm the intended state for createAuxTask outputs (Manual Review / Data Repair) — should they read Working, or stay New until a human picks them up?

### Commercial / Propagation (gate COM-1, COM-2)

15. Is WF004 still active in the live org, and is it the only trigger that invokes handleCommercialsStatusChange? (Live readback shows WF004 ACTIVE; confirm it is the sole trigger before retiring the field — COM-1.)
16. Does any live workflow still WRITE Commercials_Status (e.g. a field-update action), which would keep the legacy route alive even after WF004 is disabled?
17. COM-2: Canonical viability scope — should "viable Contact" for Deal loss be Deal Contact Roles (per-Deal) or Account-related Contacts? The two engines must be unified on one.
18. Is `Deals.Reason_For_Loss__s` the canonical loss field vs the custom `Lost_Reasons`? processDeal treats either as hasLossReason while writes use Lost_Reasons — confirm both are intended.

## Risks

1. **Function bodies are not MCP-readable** (GET returns empty), so EVERY requires-redeploy fix is deployed without round-trip verification — a deployed body could silently diverge from branch main and the connector cannot detect it. Mitigate with external (UI) diff before/after each redeploy.
2. **Email-template copy and active/published status are not MCP-readable.** SEQ-1 routes missed demos into the Demo Hosted recovery cadence; if the live demo-hosted:1 opener still carries attendance-implying draft copy (or rejected merge syntax), non-attendees receive an email assuming they attended. This cannot be verified without a UI/Deluge readback — verify copy before enabling SEQ-1 in production.
3. **WF006 'anyaction' trigger double-invokes handleCallOutcome** when a single save sets both Call_Task_State and Next_Follow_Up_Date; correctness depends entirely on the function's idempotency, which is body-unverifiable via MCP. The 2026-06-25 idempotency retest PASSED but only for the tested path.
4. **The demo/meeting cluster has four unresolved product questions** (where meeting:attended is emitted; Demo Hosted recovery anchored at Demo Hosted vs Demo Booking; single no-show opener choice; the recovery-step-state field for the once-only guard). SEQ-1/SEQ-4/SEQ-6/MTG-5 should not be deployed until these are answered, or the recovery cadence may seed step-1 repeatedly or never advance to Demo Hosted awaiting-outcome.
5. **COM-2 viability-scope unification changes Deal-close behavior;** choosing the wrong canonical set (Account Contacts vs Deal Contact Roles) could close viable Deals or keep dead ones open. Decide the canonical scope before COM-2/COM-3 deploy.
6. **WF004/Commercials_Status retirement is cross-coupled** to the WF021 publish + signature/atomic-Quote-write proofs + harness gates per WF004's own description; deactivating WF004 prematurely could break the live commercial signing bridge. Commercials_Status delete is blocked until then.
7. **Task_Outcome holds production data** and its Deluge dependencies were never analysed; deleting or DEP-hiding it without a dependency check and data migration risks data loss and broken routing. Keep it blocked.
8. **CALL-2/TASK-4 (New vs Working convention) and createAuxTask disposition** are unresolved with the lifecycle owner; applying a guess could mislabel work-state across many activities. Hold until confirmed.
9. **Several documented E2E test areas remain unrun** (Activation Email route; full Task/Call/Meeting Lost reason matrices; commercial Task/Meeting Quote evidence; Commercial_Outcome/Commercials_Status negatives blocked by WF004). v6 E2E coverage is incomplete by the docs' own admission, so closeout cannot assert full behavioral proof.
10. **Referenced docs PRE_CHANGE_FIELD_AUTHORITY_AUDIT.md and SINGLE_FIELD_AUTOMATION_AUDIT.md were not reviewed** in this pass; their current contents are unknown and may contain dependency or layout findings that affect the field-delete gates.
