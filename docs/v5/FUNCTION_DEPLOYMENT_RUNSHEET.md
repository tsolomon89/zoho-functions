# V5 Function Deployment Runsheet (Developer Hub) — 2026-06-15

**Deluge source cannot be published through the connected MCP tools** — re-verified
2026-06-15 against the actual `post`/`put` schemas and live GET responses (not assumed).
Publish source via **Zoho Developer Hub → Functions** (or the function editor). This
runsheet is the exact, ordered package. **Do not commit/push; do not mark source as published.**

### MCP capability boundary — VERIFIED (post/put/get schemas + live responses)
| Operation | Fields it exposes | Source field? |
|---|---|---|
| `postAutomationFunctions` | `feature_type`, **`function.id` (required → links an EXISTING code unit)**, `language`, `module`, `name`, `arguments[]` | **NO** |
| `putAutomationFunctions` | path `functionId`, `id`, `feature_type`, `module`, `arguments[]` | **NO** (updates args/module/feature_type only) |
| `getAutomationFunctions` / `getAll…` | `module`, `language`, `source:"crm"` (origin type, **not** code), `function.{id,api_name}`, `name`, `arguments[]` | **NO** |

**Precise missing capability:** none of create/update/read exposes a Deluge `script`/`source`/
`body`/`code` field. `post` *requires* a pre-existing `function.id` (the code unit must already
exist), and `put` cannot alter the body. The list returns only the **11 workflow-bound**
automation functions; the standalone `automation.*` helpers (routeContactSequence,
sendSequencedEmail, sendScheduledEmailFromTask, sendDemoReminder, sendCommercialFollowUp,
createAuxTask, resolveContactAction, calculateBusinessDate, logAutomationEvent) are **not
returned at all** — they are standalone functions, outside this automation-functions API.
**Therefore Deluge bodies (incl. the updated `sendSequencedEmail` registry) must be pasted in
the Zoho function editor / Developer Hub.** What the MCP CAN do post-deploy: set/verify
`arguments` (workflow merge-field mappings, e.g. `callIdStr ← ${!Calls.id}`), module binding,
and delete obsolete functions — usable for the workflow-rebind + arg steps below.

Authoritative source = the working-tree `v5/` files. 24 functions. Email template resolution
is centralised in `sendSequencedEmail` (inline registry, send-by-ID) — see
`docs/v5/TEMPLATE_REGISTRY.md`.

## Publication order (dependency-first)
Standalone helpers must exist before their callers resolve `automation.X()`.

| # | Function | Repo path | Signature | Depends on |
|---|---|---|---|---|
| 1 | logAutomationEvent | v5/activity/_util_logAutomationEvent.deluge | `void(functionName, moduleName, recordId, action, outcome, map payload)` | — |
| 2 | calculateBusinessDate | v5/activity/_util_calculateBusinessDate.deluge | `string(date startDate, int offset, string calcMode)` | — |
| 3 | resolveContactAction | v5/activity/_util_resolveContactAction.deluge | `string(stage, seqType, seqState, seqStage, seqStep, triggerOutcome)` → JSON | 1 |
| 4 | createAuxTask | v5/activity/createAuxTask.deluge | `string(contactIdStr, dealIdStr, taskType, note)` | 1 |
| 5 | sendSequencedEmail | v5/activity/sendSequencedEmail.deluge | `string(contactIdStr, dealIdStr, stage, int step, kind, existingAuditTaskId)` | 1,4 |
| 6 | routeContactSequence | v5/activity/routeContactSequence.deluge | `void(contactIdStr, dealIdStr, triggerOutcome)` | 1–5 |
| 7 | sendScheduledEmailFromTask | v5/activity/sendScheduledEmailFromTask.deluge | `void(taskIdStr)` | 5 |
| 8 | sendDemoReminder | v5/activity/sendDemoReminder.deluge | `void(dealIdStr)` | 5 |
| 9 | sendCommercialFollowUp | v5/activity/sendCommercialFollowUp.deluge | `void(dealIdStr)` | 6 |
| 10 | handleCallOutcome | v5/activity/handleCallOutcome.deluge | `void(callIdStr)` | 6 |
| 11 | handleTaskCompletion | v5/activity/handleTaskCompletion.deluge | `void(taskIdStr)` | 6 |
| 12 | handleMeetingEvent | v5/activity/handleMeetingEvent.deluge | `void(eventIdStr)` | 6 |
| 13 | handleDemoOutcome | v5/activity/handleDemoOutcome.deluge | `void(dealIdStr)` | 6 |
| 14 | handleCommercialsStatusChange | v5/activity/handleCommercialsStatusChange.deluge | `void(dealIdStr)` | 6 |
| 15 | handleEmailEvent | v5/activity/handleEmailEvent.deluge | `void(emailRecordIdStr, eventType, relatedDealIdStr, relatedContactIdStr)` | 4 |
| 16 | handleEmailReplied | v5/activity/handleEmailReplied.deluge | `void(relatedDealIdStr, relatedContactIdStr)` | 15 |
| 17 | handleEmailBounced | v5/activity/handleEmailBounced.deluge | `void(relatedDealIdStr, relatedContactIdStr)` | 15 |
| 18 | handleEmailNotReplied | v5/activity/handleEmailNotReplied.deluge | `void(relatedDealIdStr, relatedContactIdStr)` | 15 |
| 19 | handleEmailOpenedNotReplied | v5/activity/handleEmailOpenedNotReplied.deluge | `void(relatedDealIdStr, relatedContactIdStr)` | 15 |
| 20 | handleEmailClicked | v5/activity/handleEmailClicked.deluge | `void(relatedDealIdStr, relatedContactIdStr)` | 15 |
| 21 | processDeal | v5/processDeal.deluge | `void(deal_id)` | 1 |
| 22 | processContact | v5/processContact.deluge | `void(contact_id)` | 21 |
| 23 | processAccount | v5/processAccount.deluge | `void(account_id)` | 21 |
| 24 | processLead | v5/processLead.deluge | `void(lead_id)` | 22 |

> **Return-type constraint (Zoho):** `automation`-category functions may return only
> `void` or `string` — **not `map`/`list`**. `resolveContactAction` therefore returns a
> JSON `string` and `routeContactSequence` parses it with `.toMap()`. All 24 functions
> conform (void or string).

## Workflow bindings (argument mappings)
Workflow-invoked functions only (helpers 3–9 are called in-code, no workflow binding except
where noted). IDs from G1 backup.

| Workflow (id) | Trigger | Function | Arg mapping | Action |
|---|---|---|---|---|
| WF001a Process Lead (663622) | Leads create_or_edit | processLead | `lead_id ← ${Leads.id}` | keep |
| WF001b Process Contact (663630) | Contacts create_or_edit | processContact | `contact_id ← ${Contacts.id}` | **narrow** to Stage/State/Status/Sequence_*/Account_Name/Contact_Role1 |
| WF001c Process Account (663648) | Accounts create_or_edit | processAccount | `account_id ← ${Accounts.id}` | keep |
| WF001d Process Deal (663638) | Deals create_or_edit | processDeal | `deal_id ← ${Deals.id}` | keep |
| WF004 (800001) | Deals field_update Commercials_Status | handleCommercialsStatusChange | `dealIdStr ← ${Deals.id}` | keep |
| WF005 (801001) | Deals field_update Demo_Outcome | handleDemoOutcome | `dealIdStr ← ${Deals.id}` | keep |
| WF006 (808046) | Calls (verify trigger=anyaction→Call_Outcome) | handleCallOutcome | `callIdStr ← ${Calls.id}` | verify criteria |
| WF007 (782052) | Events create_or_edit | handleMeetingEvent | `eventIdStr ← ${Events.id}` | keep |
| WF008 (784145) | Tasks create_or_edit | handleTaskCompletion | `taskIdStr ← ${Tasks.id}` | verify (Status=Completed, not ScheduledSend) |
| WF009a-e (790073/806019/789167/796107/799022) | Emails events | handleEmailReplied/Bounced/NotReplied/OpenedNotReplied/Clicked | `relatedDealIdStr ← ${Emails.Deal/Parent}`, `relatedContactIdStr ← ${Emails.Contact}` | keep |
| WF010c (802001) | Deals date Demo_Reminder_Send_At | **sendDemoReminder** | `dealIdStr ← ${Deals.id}` | DONE — **stays on Deals** (date WF can't bind to Meetings); fn guards on Deal demo mirrors written by handleMeetingEvent |
| WF010d (790038) | Deals date Next_Comm_Follow_Up_Date | **sendCommercialFollowUp** | `dealIdStr ← ${Deals.id}` | DONE (was sequenceRouter) |
| WFC-SchedEmail (1499121) | Tasks date Due_Date @09:00, criteria `Task_Sequence_Managed=Selected` AND `Status=Not Started` AND `Task_Type="Scheduled Send"` | **sendScheduledEmailFromTask** | `taskIdStr ← ${Tasks.id}` | created (as-built) |

## Workflows to disable/delete (bound to obsolete sequenceRouter)
WF002 Deal Sequence Router (796079) · WF003 Stage Change Router (784137) ·
WF010a Next_Action_Due_Date (800007) · WF010b Sequence_Paused_Until (800016) →
set inactive, then delete after E2E green.

## Old functions → deletion candidates (after workflows unbound + E2E)
`sequenceRouter` (record id 991103000000780386 / function.id 991103000000780343) ·
`Convert Lead` (543692 / 543684). Delete via function MCP **after** WF002/003/010a/b
are removed; re-verify both ids immediately before delete.

## Manual prerequisite (Zoho UI — not API-reachable here)
**Retire the native "MQL" Sales Cadence** (Setup → Automation → Cadences). It still binds
legacy template `657010`; once retired, delete `657010` + the MQL folder (`657008`). Also
confirm `Sequence_Type` picklist values are `Email / Call / Manual` before enabling WF001b.

## Rollback order
1. Re-point WF010c/d back to sequenceRouter; delete WFC-SchedEmail; re-enable WF002/003/010a/b.
2. Restore prior function versions from git (`git checkout <prev> -- v5/...`) and re-publish.
3. Email templates: the legacy bodies are in git history + the G1 list backup; recreate if needed.

## Smoke / E2E test case (recipient `tlcsolomon+e2eN@gmail.com` — NOT bare tlcsolomon@gmail.com; it matches an existing Contact)
> ✅ Executed & GREEN 2026-06-16 — see `docs/v5/SESSION2_ASBUILT_AND_DEFECTS.md`. Activation is **Task-gated**, not Sequence_Type-driven.
1. Create a test Contact (or convert a Lead) at Stage `Marketing Consent`; `processContact` creates a
   **"Sequence Activation" Task**. Complete that Task with `Task_Outcome="Activate Email First"`
   (do NOT edit `Sequence_Type`) → expect opener `marketing-consent:1:initial` **+ a Call 1**, one
   Completed "Email Sent: marketing-consent:1:initial" audit Task.
2. Force a missing key (temporary) → expect a **Manual Review** Task, no advance.
3. Call path: log Call_Outcome neutral ×5 → cadence follow-ups + terminal `:5:final`.
4. meeting:created → `demo-confirmation:0:confirmation`; Demo_Reminder_Send_At → reminder;
   commercial:sent → `commercial-agreement:0:proposal-sent`; commercial:signed →
   `onboarding:0:signed-confirmation`.
5. Verify one email = one audit Task; no duplicate sends; rollups intact.
