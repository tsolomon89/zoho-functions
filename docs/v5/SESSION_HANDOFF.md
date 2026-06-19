# V5 Cutover — Session Handoff (2026-06-16)

Single source of truth for resuming the V5 email/function/workflow cutover in a fresh
Claude Code session. Read this first, then the linked docs.

## ⚠️ Session 2 update (2026-06-16 PM) — read `docs/v5/SESSION2_ASBUILT_AND_DEFECTS.md`
The E2E is **GREEN** (instant Lead→Onboarding funnel, Gmail-verified; demo path re-run after a
refactor). Key corrections to the text below:
- **Activation is Task-gated, NOT `Sequence_Type`-driven.** The old "set `Sequence_Type=Email` to
  activate" wording (in §E and the runsheet) is wrong. Real flow: `processContact` creates a
  "Sequence Activation" Task → complete it with `Task_Outcome="Activate Email First"` (WF008 →
  `handleTaskCompletion` → `activate:email`) → opener `marketing-consent:1:initial` + Call 1.
- **Meeting/Event is the source of truth for the demo lifecycle** (`Meeting_Status` + `Meeting_Outcome`).
  `handleMeetingEvent` + `sendDemoReminder` were refactored; **no** `Deal.Demo_Status`/`Demo_Meeting_ID`.
  WF010c **stays on Deals** (date workflows can't bind to Meetings/Tasks).
- **Tasks use Task-specific fields:** `Task_Sequence_Managed` (existing), `Task_Sequence_Stage` +
  `Blocks_Sequence` (created this session). Activities fields are **not** shared across Calls/Events/Tasks.
- **Done 2026-06-17:** deleted retired rules WF002/WF003/WF010a/WF010b + the `sequenceRouter`
  automation-function record (Contact-centric model confirmed; they were unused). **Remaining UI-only**
  (no delete-field MCP): drop 5 orphaned Deal fields (`Sequence_Status`, `Next_Action_Due_Date`,
  `Sequence_Paused_Until`, `Deal_Primary_Contact`, `Commercial_Outcome`) and remove the leftover
  `WF Placeholder Marker Deals` field-update action from WF005. See §6 of SESSION2_ASBUILT_AND_DEFECTS.md.
- Use `tlcsolomon+e2eN@gmail.com` for test recipients, never bare `tlcsolomon@gmail.com` (matches an
  existing Contact). All Session-2 test records were deleted.

## Where we are
- **Email templates: MIGRATED & LIVE.** 8 canonical folders + **31 canonical templates**
  created and verified in Zoho. Registry (canonical key → template ID) in
  `docs/v5/TEMPLATE_REGISTRY.md`.
- **V5 function source: DEPLOYED.** The user has published/updated **all 24** `v5/`
  functions in Zoho (incl. the `_util_resolveContactAction` string-return fix +
  `routeContactSequence` `.toMap()` parse).
- **Legacy cleanup: DONE except one blocked item.** 136 legacy templates + 9 legacy
  folders deleted; legacy `.md` template tree removed; "Big Deal Alert" + its Big Deal Rule
  workflow + alert deleted. See `docs/v5/TEMPLATE_DELETION_REPORT.md`.
- **NOT done yet:** workflow rebinds/creates/retires, obsolete-function deletes, the MQL
  Cadence retirement (+ its template/folder), E2E test, and the git commit. Details below.

## Authoritative docs (read in this order)
1. `docs/v5/SESSION_HANDOFF.md` (this file)
2. `docs/v5/FUNCTION_DEPLOYMENT_RUNSHEET.md` — 24 functions, order, signatures, **workflow
   binding table** (rebind/create/retire), rollback, E2E test case
3. `docs/v5/TEMPLATE_REGISTRY.md` — canonical key → live template ID + folder IDs
4. `docs/v5/EMAIL_MANIFEST.md` — the 31 templates (copy + verified merge tags)
5. `docs/v5/V5_COMMUNICATION_MATRIX.md` — every email-producing branch (derivation)
6. `docs/v5/TEMPLATE_DELETION_REPORT.md` — what was deleted / the one blocked item
7. `docs/v5/SEQUENCE_TYPE_ACTIVITY_REFACTOR.md` — optional §12 engine refactor (scoped, deferred)
8. Backup: `.agents/context/zoho-backups/20260615T121415Z/README.md` (pre-cutover inventory + both-ID map)

## Remaining work

### A. Workflow changes (MCP-capable now — `zoho-workful-crud`)
Per the runsheet's binding table:
- **Rebind** WF010c (`991103000000802001`) → `sendDemoReminder` (arg `dealIdStr ← ${!Deals.id}`).
- **Rebind** WF010d (`991103000000790038`) → `sendCommercialFollowUp` (arg `dealIdStr ← ${!Deals.id}`).
- **Create** `WFC-SchedEmail`: Tasks, date `Due_Date`, criteria `Sequence_Managed = Yes`
  AND `Description contains ScheduledSend` → `sendScheduledEmailFromTask` (arg `taskIdStr ← ${!Tasks.id}`).
- **Narrow** WF001b (`991103000000663630`) to create/edit of
  `Stage,State,Status,Sequence_Type,Sequence_State,Sequence_Stage,Sequence_Step,Account_Name,Contact_Role1`.
- **Verify** WF006 (`…808046`, anyaction→Call_Outcome) and WF008 (`…784145`, Tasks) criteria.
- **Retire** (set inactive, then delete after E2E): WF002 (`…796079`), WF003 (`…784137`),
  WF010a (`…800007`), WF010b (`…800016`) — all bound to obsolete `sequenceRouter`.

### B. Delete obsolete functions (after their workflows are unbound)
`sequenceRouter` (record `…780386` / function `…780343`) and `Convert Lead`
(`…543692` / `…543684`) via `zoho-function-crud` deleteAutomationFunction. **Re-fetch
`getAllAutomationFunctions` first** — the user just republished everything, so the
standalone helpers now have NEW function IDs; reconcile before any delete.

### C. Metadata prereq
Confirm the `Sequence_Type` picklist values are exactly **Email / Call / Manual** before
enabling WF001b on live Contacts.

### D. MQL Cadence (UI-only — no Cadences API in any MCP)
Setup → Automation → Cadences → retire/delete **MQL**. Then delete template `657010`
+ folder `MQL` (`991103000000657008`) via `zoho-email-crud` → reaches "legacy = 0".

### E. E2E smoke test (recipient `tlcsolomon@gmail.com`)
Runsheet §test case: activate an Email-path Contact → expect `marketing-consent:1:initial`
send-by-ID + one Completed "Email Sent: …" audit Task; missing-key → Manual Review Task;
call-path cadence + `:5:final`; demo/commercial event emails; one email = one audit Task.
NOTE: `tlcsolomon@gmail.com` == `t.l.c.solomon@gmail.com` (Gmail ignores dots) → the
Gmail MCP can read the delivered tests.

### F. Optional / housekeeping
- §12 Sequence_Type→activity refactor (scoped, deferred — `docs/v5/SEQUENCE_TYPE_ACTIVITY_REFACTOR.md`).
- **Git: nothing committed/pushed.** Branch `email-template-rewrite`. Commit when ready.

## Hard-won facts / gotchas (do not relearn)
- **Merge tags — ONLY** `${!<Module API>.<Field API>}` (bang + underscore API names). Verified set:
  `${!Contacts.First_Name}`, `${!Contacts.Account_Name.Account_Name}`, `${!org.company_name}`
  (brand), `${!users.first_name}`, `${!userSignature}`, `${!users.website}` (booking),
  `${!Contacts.Account_Name.Contract_URL}`, `${!Contacts.Account_Name.Contract_Renewal_URL}`.
  Account fields are reached via the `Account_Name` lookup. Label/space forms are REJECTED.
- **`automation`-category functions return only `void` or `string`** (not map/list). The
  resolver returns JSON string; the router parses with `.toMap()`.
- **MCP cannot write Deluge source** (Developer Hub only). MCP CAN set function args,
  workflow bindings, and deletes.
- **No Cadences API** in any of the three MCP servers.
- Template **name** regex forbids `` ` ~ # % ^ & * ( ) + = " ; < > [ ] { } | \ `` (no parens).
- `createEmailTemplateFolders`: **1 folder per request** (despite the 1000 doc).
- `deleteEmailTemplates`: pass `ids` as a **single comma-separated string**, not an array.
- Module IDs: Contacts `991103000000000047`. API domain = `https://www.zohoapis.eu`.
- Three MCP servers: `zoho-email-crud` (templates/folders/notifications), `zoho-function-crud`
  (automation functions: args/bindings/delete), `zoho-workful-crud` (workflow rules).
- Terminology: `Contact.Stage` · `Deal.Opportunity_Stage` (Primary-Contact rollup) ·
  `Deal.Stage` = Opportunity Type (MQL/SQL/FTP/RTP). **No `Stage1`** in active code/docs.

## Canonical folder IDs
Marketing Consent `991103000001471001` · Demo Booking `991103000001472001` ·
Demo Confirmation `991103000001471003` · Demo Hosted `991103000001473001` ·
Proposal Preparation `991103000001474001` · Commercial Agreement `991103000001475001` ·
Onboarding `991103000001472003` · Renewal `991103000001476001`.

## First actions for the new session
1. `getAllAutomationFunctions` (refresh function IDs — they changed on republish).
2. `getWorkflowRules(include_inner_details=true)` (confirm current bindings before changes).
3. Then execute Remaining §A (workflow changes), §B (obsolete deletes), §E (E2E).
4. MQL Cadence (§D) needs the user in the UI; surface it, don't block on it.
