# R2 Repair — Session Handoff (2026-06-24)

Pick up the F1–F4 + timestamp repair of the Jurnii v6 Zoho automation. **F2, F4, and the timestamp item are DONE and verified live. F3 and F1 are still open** and need one diagnostic each (Deluge function log / data-model decision) — not more blind redeploys. Read this top to bottom before touching anything.

---

## 0. Environment & hard constraints (read first)

- **Repo:** `C:\Development\Projects\zoho-functions` (work is in `v6/` and `v6/activity/`). Branch `main`.
- **Live org (production):** Jurnii.io, org id `org20114906201`, domain `org20114906201`, DC **EU** (`https://www.zohoapis.eu`), TZ **Europe/London (BST = +01:00)**, currency GBP. Trial expired 2026-06-25 — confirm it's still usable before live testing.
- **Tooling reality (critical):**
  - The Zoho **function MCP tools carry only metadata** (name/module/arguments) — **you CANNOT read or deploy Deluge source via MCP.** Repo files are the source of truth; **the user republishes** by hand. Do not claim a code fix is live until they confirm.
  - You **cannot read Deluge `info` execution logs via MCP** either. To inspect runtime values you must ask the user to paste the function execution log from Setup → Functions.
  - `getFields` for big modules exceeds the token limit → it auto-saves to a file; parse with PowerShell/`jq` (no `jq` binary on this box — use PowerShell `ConvertFrom-Json`).
  - Standalone util functions (`logAutomationEvent`, `createAuxTask`, `sendSequencedEmail`, `resolveDealPipeline`, …) do **not** appear in `getAllAutomationFunctions` (that lists workflow-associated only). You can't verify a standalone fn's existence/mtime via MCP.
- **Test identifiers:** gate run used `E2E-20260624` (alias `t.l.c.solomon+E2E-20260624@gmail.com`); R2 uses `E2E-R2-20260624` (alias `t.l.c.solomon+E2E-R2-20260624@gmail.com`). Use a **distinct Company** per run to avoid `Account_Key` collisions (Account_Key derives from email domain, else company-name-normalized; gmail is a free domain so it falls back to company). There are leftover morning records named `E2E TEST - 20260624 R2` / `ZZE2E…` — don't disturb them.
- **All R2 test records have been deleted.** Nothing to clean up right now.

## 1. The trigger chain (all live)

`Lead create → WF001a processLead → convertLead → WF001b2 processContact (creates "Sequence Activation" Task) → [rep sets Task_Sequence_Type=Email + Status=Completed] → WF008 handleTaskCompletion → routeContactSequence → resolveContactAction → sendSequencedEmail (real send via Contact send_mail, from Deal owner timothy@jurnii.io) → audit Task + next action (Call/Task)`. Cadence/scheduled emails fire date-based via `WFC-SchedEmail` (Tasks Due_Date, 09:00). To create records and let workflows run, use `createRecords` with `trigger:["workflow"]`. Emails go to `Contact.Email` (no plus-address logic in code — set the test Contact's email to the gmail alias). Stage names are canonical 8: Marketing Consent, Demo Booking, Demo Confirmation, Demo Hosted, Proposal Preparation, Commercial Agreement, Onboarding, Renewal. (Spec's "Marketing Qualification" == code's "Marketing Consent".)

## 2. Status of the five items

| Item | State | Evidence |
|---|---|---|
| **F2** `Task_Sequence_Stage` field missing | ✅ DONE | Created live: picklist id **991103000001842018**, 8 canonical stages. R2-1 activation Task carried `Task_Sequence_Stage=Marketing Consent`. Write/read verified. |
| **F4** activation Task missing inherited context | ✅ DONE | R2-1 activation Task carried `Task_Stage`/`Task_Opportunity=MQL`/`Task_State=Open`/`Task_Status=New`. Code: processContact §6 (see below). |
| **Timestamp** | ✅ DONE (reverted) | Original `…XXX` is CORRECT. My round-1 `'Z'` was a +1h regression — proven: same Call native `Created_Time=12:29:22` vs `'Z'` `Call_Start_Time=13:29:21`. zoho.currenttime returns LOCAL components here. Reverted all 4 sites. The original "1h behind" finding was pre-set Lead completion dates copied at conversion, not a live defect. |
| **F3** Pipeline not inherited (`Task_Pipeline`/`Call_Task_Pipeline` null) | ❌ OPEN | Resolver returns "". Needs one function-log read to settle. |
| **F1** Lead Product Interest lost at conversion | ⚠️ PARTIAL | Junction link IS created (parse + link confirmed in processLead log + visible from Product side), but doesn't surface on Contact's `Products_Linked`/formula. Pre-existing junction/formula issue. Needs data-model decision. |

## 3. Repo changes already made (staged; some deployed, some not)

All edits carry `F3 FIX` / `F4 FIX` / `F1 FIX` / `TZ … REVERTED` comments. `git diff` to see them.

- **NEW** `v6/activity/_util_resolveDealPipeline.deluge` — shared resolver. Latest version: tries native `deal.get("Pipeline")` FIRST, then REST v6 `invokeurl GET /crm/v6/Deals/{id}` fallback, validates against `{B2B, Partnership}`, logs `native_read`/`rest_read` diagnostics. Declared `automation.resolveDealPipeline`. **NOT yet redeployed in its latest form.**
- **F3 call sites** (call `automation.resolveDealPipeline(dealId.toString())` instead of `deal.get("Pipeline")`): `processContact` §6 activation, `routeContactSequence` (`mirrorPipeline`, ~line 829 — feeds both Call `Call_Task_Pipeline` and continuation-Task `Task_Pipeline`), `sendSequencedEmail` (`emPipeline`), `createAuxTask` (`auxPipeline`), `handleMeetingEvent` (`dealPipeline`→`Meeting_Task_Pipeline`), `handleCallOutcome` (`dealPipeline`, rescheduled/next Call).
- **F4** `processContact.deluge` §6 activation block: adds `Task_Stage=contactStage`, `Task_State=Open`, `Task_Status=New`, `Task_Opportunity=deal.get("Stage")`, `Task_Pipeline=resolveDealPipeline(...)`. **Deployed & verified (except pipeline, blocked on F3).**
- **F1** `processLead.deluge`: removed dead `Deals.Product_Interest_Staging` write; added **step 6b** (resolve each `Lead.Product_Interest` SKU via `searchRecords("Products", …)` → `updateRelatedRecord("Products12", prodId, "Contacts", newContactId)`, idempotent, Manual Review on unresolved). `processDeal.deluge`: removed its dead `Deals.Product_Interest_Staging` write (replaced with a log line). **Deployed.** (Link works but see F1 caveat §5.)
- **Timestamp REVERT** (`'Z'`→`XXX`): `processContact:178`, `processDeal:1555`, `routeContactSequence` completion stamp (~891) + immediate `Call_Start_Time` (~1147). **NOT yet redeployed** (they currently run the +1h `'Z'` version live).

### Deployment state right now
- **Deployed & current:** F2 field; F4 (processContact); F1 dead-write removal + step 6b (processLead, processDeal).
- **NEEDS REDEPLOY:**
  1. `_util_resolveDealPipeline` (latest native+REST+diagnostics version) — for F3.
  2. `processContact`, `processDeal`, `routeContactSequence` — to apply the **timestamp revert** (`'Z'`→`XXX`). They currently produce +1h-ahead stamps live.
- Other functions (`sendSequencedEmail`, `createAuxTask`, `handleMeetingEvent`, `handleCallOutcome`) have the F3 resolver call; they only start populating pipeline once the resolver itself works.

## 4. F3 — exact next step

1. User redeploys `_util_resolveDealPipeline` (latest version).
2. Create one test Lead (`trigger:["workflow"]`) and complete its activation, OR just trigger any activation.
3. **Ask the user to paste the `resolveDealPipeline` execution log lines** — specifically `native_read=got/blank pipeline=…` and `rest_read=got/blank pipeline=…`.
   - If `native_read=got B2B` → `deal.get("Pipeline")` works; the original F3 failure was deployment drift. Simplify resolver to native-only.
   - If `native_read=blank` but `rest_read=got B2B` → keep the REST fallback; done.
   - If both blank → Pipeline is genuinely unreadable in Deluge. Fall back to deriving pipeline another way (e.g., set a writable mirror field on the Deal at creation, or map from a readable field) — do NOT hardcode B2B (only {B2B, Partnership} exist on the activity picklists).
- Open process question: user hinted standalone utils may need `standalone.X` declaration, but existing utils use `automation.X` and work cross-function. If the resolver must be `standalone.`, change the declaration AND all 6 call sites together.

## 5. F1 — exact next step (data-model decision needed)

Confirmed facts:
- `Contact.Product_Interest_Staging` is a **read-only FORMULA** (API write returns SUCCESS but no-ops). Never write it.
- Canonical writable field = `Products_Linked` (multiselectlookup, id 991103000000659974) → linking module **`Contacts_X_Products`** (id 991103000000659977) → target module **`Products`** (id 991103000000000099); related-list api name **`Products12`** (id 991103000000663042); connected field on Products side = `Product_Interest`.
- My `updateRelatedRecord("Products12", prodId, "Contacts", contactId)` (copied from processDeal:630) creates a junction visible from the **Product** side, but **not** from the Contact's `Products_Linked`/`Products12` related list, and `Product_Interest_Staging` formula stays null. **This is true for ALL contacts including processDeal's full-funnel morning contact `991103000001817003`** → pre-existing, not conversion-caused.
- Direct field write `Products_Linked:[{"id":prodId}]` was rejected `INVALID_DATA`.

Decide with the user:
- (a) Link from the **Contact** side instead: `updateRelatedRecord("Contacts", contactId, "Products12", prodId)` — test whether that surfaces on `Products_Linked` + formula; and/or
- (b) Is the `Product_Interest_Staging` formula itself misconfigured (empty even for contacts that demonstrably have linked products)? That may be the real defect and is an admin/metadata fix, not Deluge.
- Note the `Products` vs `Products12` naming: the code searches `searchRecords("Products", …)` and links via `"Products12"`; confirm these resolve to the same module in this org.

## 6. R2 suite — what remains after F3/F1 settle

R2-1 (converted Lead) and R2-7 (timestamp) effectively done. Still to run once F3/F1 are fixed + deployed:
- **R2-2** direct Contact activation + dedup replay (re-touch a WF001b0 trigger field; expect exactly 1 activation Task; Sequence_State guard prevents re-activation).
- **R2-3** stale-stage protection (**mandatory F2 proof**): create a pending scheduled-email Task for stage X, advance Contact to stage Y (positive Call outcome `Call_Task_State=Won` → supersede cancels the `ScheduledSend|` Task → email never sends), verify new-stage Task carries `Task_Sequence_Stage`=new stage. Supersede logic is at routeContactSequence ~774-823 (cancels open `ScheduledSend|` tasks; defers others; marks Calls Stale+Cancelled).
- **R2-4** email audit inheritance: real send → Gmail receipt at the alias → audit Task carries `Task_Sequence_Stage`/`Task_Stage`/`Task_Pipeline`/`Task_Opportunity`/SendKey/MessageID + correct post-send state (`Task_State=Open`,`Task_Status=New`). Gmail has ~30-60s index lag — re-query.
- **R2-5** Call pipeline: trigger next Call, verify `Call_Task_Pipeline` populated; reschedule once and confirm it persists.
- **R2-6** Product Interest: verify Lead PI survives onto the Contact (per the F1 decision); no write to nonexistent `Deals.Product_Interest_Staging`.

Drive stages via real activities: activation completes with `Task_Sequence_Type=Email`; advance with `Call_Task_State=Won` on the sequence-managed Call (→ `call:positive`); demo via an Event (`Meeting_Task_State=Won` → `demo:qualified`, advances toward Proposal Preparation and sends the post-demo email). All proven in the gate run.

## 7. Useful references & gotchas

- **Deluge `getRecordById` omits fields:** definitively `Pipeline` (root of F3); strongly suspected for the multiselect `Lead.Product_Interest` (though the processLead log showed the parse DID get "Jurnii UX - Fixed", so that one may be fine — re-confirm). REST full GET includes them. `deal.get("Stage")` (Opportunity Type) and `deal.get("Opportunity_Stage")` work fine.
- **Field topology:** `Deals.Stage` = Opportunity **Type** (MQL/SQL/FTP/RTP); `Deals.Opportunity_Stage` = the 8 commercial stages; `Deals.Opportunity_State`/`Opportunity_Status` = viability (Deals never "Won"). `Contact.Stage` = the 8 commercial stages. Activity mirror fields: `*_Task_Stage` = commercial stage, `*_Task_Opportunity` = Deal.Stage, `*_Task_Pipeline` = Deal.Pipeline, `Task_Sequence_Stage`/`Sequence_Stage`(Calls) = routing stage. Legacy `Task_Stage`/`Calls.Sequence_Stage` picklists hold a STALE value set (Demo Booked/Demo Attended/Commercials Sent/Commercials Signed/Renewall) but code writes canonical 8-stage values via API (allowed). The NEW `Task_Sequence_Stage` was created with the canonical 8 to match `Contact.Stage` comparisons.
- **Non-existent fields (writes are silent no-ops):** `Deals.Product_Interest_Staging` (removed those writes). `Contacts.Marketing_Consent_Status` (the send consent-guard reads blank → inert; emails not blocked by it).
- **Activation route selector** = `Task_Sequence_Type` (Email/Call/Manual); `Task_Outcome` is exception-only (Suppress/Already Handled/Stage Incorrect). Activation Task is `Blocks_Sequence=Yes`, `Status=Not Started`; a rep completes it.
- **Related docs:** `.agents/context/import_tests/AUDIT_R2_REPAIR_MANIFEST.md` (deployment manifest), `AUDIT_00_REVISION_R1.md` (original D1–D4 audit). Memory: `v6-e2e-gate-20260624.md` (full chronological findings incl. round-2/3), `v6-stage-field-topology`, `v6-activity-state-migration`.
- **Template registry** (stage emails) is inline in `sendSequencedEmail.deluge` (canonical key → Zoho template id). Marketing-consent opener = `marketing-consent:1:initial` (991103000001478002).

## 8. First actions in the new session

1. `git -C C:\Development\Projects\zoho-functions status` / `git diff` to see staged edits; read this doc + memory `v6-e2e-gate-20260624.md`.
2. Confirm with the user which functions are currently republished (esp. the resolver + the 3 timestamp-revert functions) before testing — otherwise live behavior won't match the repo.
3. Settle **F3** via the resolver log (§4), then **F1** via the data-model decision (§5).
4. Once both deploy clean, run **R2-2…R2-6** (§6) with `E2E-R2b-20260624` (fresh identifier) + alias `t.l.c.solomon+E2E-R2b-20260624@gmail.com`, capture the correlation/activation evidence, then delete the test records.
