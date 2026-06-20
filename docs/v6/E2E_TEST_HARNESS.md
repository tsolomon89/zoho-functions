# E2E Test Harness — v6 (complete pipeline, single workflow)

> Paste this file into a fresh Claude Code session in the `zoho-functions` repo to drive the **complete end-to-end journey** — Lead → Contact/Account/Deal → contact-centric sequence → Proposal Preparation → seeded Quote → priced → Confirmed → Deal contract ledger → renewal/upsell supersession — as one continuous workflow, using the Zoho MCP tools.
>
> This is the canonical v6 E2E doc. It supersedes the Quote-only harness. Other agents: add new coverage under **§Extension points**, keeping the golden-path scenario (Phase 1→4) intact and continuous.

---

## The one workflow (golden path)

```
Lead (Product_Interest = "Jurnii UX - Fixed", Title decision-maker)
  → processLead converts → Contact + Account + canonical Deal
  → processContact → processDeal: Contact_Roles, links the UX Fixed Product, Opportunity_Stage = Marketing Consent; creates a Sequence Activation Task (route NOT auto-chosen)
  → rep sets Activation Task.Task_Sequence_Type = Email|Call|Manual + completes it  (WF008)
      → handleTaskCompletion → routeContactSequence("activate:<type>"): opener email + Call 1; Contact.Sequence_Type set, Sequence_State = Running
  → [sequence advances Contact via Call / Meeting / Email outcomes]
  → demo completed — Meeting (Events) Meeting_Status = Completed + Meeting_Outcome = "Attended - Qualified"  (WF007 handleMeetingEvent — the source of truth)
      → routeContactSequence("demo:qualified"); Commercials_Status = Drafting (Deal.Demo_Outcome is an optional off-layout mirror only)
      → Contact.Stage = Proposal Preparation; "Draft Commercials" task created; processDeal runs
      → Deal.Opportunity_Stage = Proposal Preparation, Stage = FTP
      → ensureDealQuote (inline in processDeal): seeds a Draft Quote with a "Jurnii UX - Fixed" line
  → rep sets the Quoted Item brand-market count (+ tier/frequency); Quote_Stage = Delivered  (WF020)
      → Deal.Commercials_Status = Sent
  → Quote_Stage = Confirmed  (WF020)
      → syncConfirmedQuoteToDeal: Deal Contract_Initial_* + Amount; Contract_Type = Initial
  → later Quote (Contract_Type = Renewed/Upsold/…) Confirmed
      → prior Quote → Closed Won; Deal Contract_Current_* + Amount; ≤1 Confirmed
```

## How to operate
- **Pacing:** workflow rules aren't instant. After any mutation that should trigger a workflow, **wait ≥30s** before reading back; retry once after another 30s before declaring FAIL. Lead conversion is heavier — wait ≥60s.
- MCP **cannot** read the Zoho Function Execution Log; assert only on observable record state.
- Record results in `docs/v6/MCP_TEST_RUN_LOG_E2E.md` (create if missing), one section per round, per the format in `docs/archive/MCP_TEST_HARNESS_PROMPT.md` §"Where to record findings".
- **One fix per round.** On FAIL: propose a surgical fix, write it to disk, STOP, and give a copy-pasteable republish instruction; resume from the failed step after the user replies `continue`.

## MCP tools (this environment)
Record CRUD (module-parameterized — Leads/Contacts/Deals/Tasks/Calls/Events/Quotes): `createRecords` / `updateRecord(s)` / `getRecord` / `getRecords` / `getRelatedRecords` / `searchRecords` / `deleteRecords` / `executeCOQLQuery` (preferred for read-back). Field metadata: `getFields` / `createFields` (Field-CRUD server). Workflows: `getWorkflowRules` / `getWorkflowRulesActionsCount` / `getWorkflowRuleById` (Workflow-CRUD server).
> **Server names have changed across sessions** (`Zoho CRM`, `Zoho Field CRUD`, `Zoho Event CRUD`, `Zoho Workflow CRUD`, `Zoho Function CRUD`, …) and some flap mid-session — re-probe with ToolSearch at start. MCP **cannot publish Deluge** (Dev Hub only) and **cannot delete CRM fields** (UI only). Gmail MCP may be unavailable — then verify sends via the in-CRM `Email Sent` audit Task (created only after a confirmed send), not inbox delivery.

## §0 — Setup (once per session)
1. Confirm the org is safe to create/delete in.
2. Confirm active workflows. **The model is fully Contact-centric, and the Meeting is the sole demo path — `WF002`/`WF003`/`WF005`/`WF010a`/`WF010b` and the `sequenceRouter` + `handleDemoOutcome` functions were retired & deleted; do NOT expect them.** Active set: WF001a-d (processLead/Contact/Account/Deal), WF004 (Deals `Commercials_Status` → handleCommercialsStatusChange), WF006 (Calls → handleCallOutcome), WF007 (Events → handleMeetingEvent), WF008 (Tasks **create_or_edit** → handleTaskCompletion), WF009a-e (Email events), WF010c (Deals `Demo_Reminder_Send_At` → sendDemoReminder), WF010d (Deals `Next_Comm_Follow_Up_Date` → sendCommercialFollowUp), WFC-SchedEmail (Tasks `Due_Date` → sendScheduledEmailFromTask), **WF020** (Quotes `Quote_Stage` → handleQuoteStageChange, arg `quoteIdStr ← ${Quotes.id}`). Confirm functions published, incl. the edited `processContact`, `handleTaskCompletion`, `handleMeetingEvent`, `sendDemoReminder`, `processDeal` and the Quote set (`handleQuoteStageChange`, `syncConfirmedQuoteToDeal`, `resolveQuotePlanSummary`, `resolveQuoteLinePrice`, `ensureDealQuote`). Confirm the **`Task_Sequence_Type`** picklist (Email/Call/Manual) exists on Tasks and is on the layout.
3. Session prefix `E2E_<YYYYMMDD_HHMM>` in every record name/Subject.
4. Confirm the catalogue: 6 quote-ready Products (`Jurnii UX/360/Cortex - Fixed/Flex`). Read their IDs via `getRecords` on Products.

## Pricing reference (PPB × brand-markets, 2 dp; bands UX [5,7,10,15,20,50,100] / 360 [5,10,20,50]; Cortex unpriced)
| Line (Base) | Brands | Band | line_acv |
|---|---|---|---|
| UX Fixed | 10 | 10 | **18,480.00** |
| UX Fixed | 8 | 10 | **14,784.00** |
| UX Fixed | 12 | 15 | **19,605.60** |
| UX Fixed | 20 | 20 | **29,400.00** |
| UX Fixed | 50 | 50 | **63,000.00** |
| 360 (2x per day) | 10 | 10 | **117,504.00** |

---

## Phase 1 — Graph + sequence bootstrap (Lead → Deal)

**GP1.** `createRecords` on Leads:
```
Last_Name = <prefix>_Last, First_Name = E2E, Email = e2e_<ts>@example.com,
Company = <prefix>_Co, Title = "Head of Marketing", Lead_Source = "Inbound Form",
Product_Interest = "Jurnii UX - Fixed"
```
Wait ≥60s.

**Assert** (the foundation the rest depends on):
- A **Contact** exists (Email match), `Account_Name` populated; an **Account** with non-empty `Account_Key`; a canonical **Deal** (`Account_Name`, `Contact_Name` set, `State` = Open, `Deal_Key` ends `::active`).
- Deal `Opportunity_Stage` = `Marketing Consent`, and `Contact_Roles` contains the Contact as **Decision Maker**.
- The Deal has the **`Jurnii UX - Fixed` Product linked** (related Products list) — this is what `ensureDealQuote` will seed from in Phase 2.
- A **Sequence Activation Task** was created: `Task_Type = Sequence Activation`, `Task_Sequence_Stage = Marketing Consent`, **`Task_Sequence_Type` blank**, `Blocks_Sequence = Yes`. **Activation is Task-gated** — the sequence does NOT auto-start; the rep chooses the route in Phase 1b. (A known dup-activation race can create two identical tasks; completing one is enough — the other idempotency-skips/defers.)

> For full per-function graph/sequence assertions (idempotency, role precedence, duplicate silencing, Amount sum, Account rollup), defer to the detailed cases **T1–T10** in `docs/archive/MCP_TEST_HARNESS_PROMPT.md`. This harness asserts only what the Quote continuation depends on, then drives forward.

---

## Phase 1b — Activation routing (the human-approved command record)

Activation is **Task-gated**: `Contact.Sequence_*` stays blank until the rep completes the Sequence
Activation Task with a chosen route. **`Task_Sequence_Type` (Email/Call/Manual) is the primary route
selector**; `Task_Outcome` carries only exceptions (Suppress / Already Handled / Stage Incorrect) plus a
legacy fallback. `Task_Sequence_Stage` is the **business-stage context** (= `Contact.Stage`), NOT the
action-stage `Contact.Sequence_Stage` (Email/Call/Meeting/Task) — do not conflate.

Each row: take a fresh Lead→Contact (Phase 1) at `Marketing Consent`, set the named fields on its
Activation Task with `Status = Completed`, wait ≥30s, assert. Use recipient `tlcsolomon+e2e<n>@gmail.com`
for any inbox checks (never bare `tlcsolomon@gmail.com` — it matches an existing Contact).

| # | Set on Activation Task | Expect |
|---|---|---|
| A1 | `Task_Sequence_Type = Email`, Completed (Task_Outcome blank) | `activate:email` → opener `marketing-consent:1:initial` audit Task + `Marketing Consent Call 1`; Contact `Sequence_Type = Email`, `Sequence_State = Running`, `Sequence_Stage = Call`, `Sequence_Step = 1` |
| A2 | `Task_Sequence_Type = Call`, Completed | `activate:call` → `Marketing Consent Call 1`, **no** opener email; `Sequence_Type = Call`, `Running` |
| A3 | `Task_Sequence_Type = Manual`, Completed | `activate:manual` → `Sequence_Type = Manual`, `Sequence_State = Stopped`; no Call, no email |
| A4 | `Task_Sequence_Type = Email` **and** `Task_Outcome = Suppress`, Completed | **Exception wins**: `activate:stop` (Stopped); no opener, no Call |
| A5 | `Task_Outcome = Stage Incorrect`, Completed | `activate:stop` + a `Manual Review` Task; stopped |
| A6 | Contact at `Marketing Consent` but `Task_Sequence_Stage = Demo Booking`; `Task_Sequence_Type = Email`, Completed | **Stage adoption**: Contact `Stage` → `Demo Booking` first, then opener resolves there (`demo-booking:1:initial`) |
| A7 | `Task_Sequence_Type` blank, `Task_Outcome = "Activate Email First"`, Completed | **Legacy fallback** = A1 (`activate:email`); honored only when `Task_Sequence_Type` is blank |
| A8 | After A1 (Contact Running), complete the **second** Activation Task with `Task_Sequence_Type = Email` | **Idempotency**: skipped, no second opener/stage change (Manual is exempt — may re-stop a Running Contact) |

**On failure:** `handleTaskCompletion` activation precedence (exception → resolve route → idempotency
**before** any write → stage adoption → route once), `processContact` activation-task creation
(`Task_Sequence_Type` left blank), WF008 trigger (must fire on `Status = Completed`),
`routeContactSequence` / `_util_resolveContactAction` (`activate:*` tokens).

---

## Phase 2 — Progress to Proposal Preparation → seeded Quote (the integration)

**GP2.** Drive the Deal to the proposal boundary via the **Meeting — the sole demo path**: create an Event with `What_Id` = Deal (`$se_module = Deals`), `Who_Id` = primary Contact, `Meeting_Type = Demo`, then `Meeting_Status = Completed` + `Meeting_Outcome = "Attended - Qualified"` → WF007 `handleMeetingEvent` → `demo:qualified`. *(The old Deal-direct `Demo_Outcome` → WF005 path is **retired** — `Demo_Outcome` is off-layout/unsettable and WF005 + `handleDemoOutcome` were deleted.)* Wait ≥45s.

**Assert:**
- Deal `Commercials_Status` = `Drafting`. *(No `Demo_Status` field on Deals — the demo lifecycle is canonical on the Meeting via `Meeting_Status`/`Meeting_Outcome`; the Deal keeps only the `Demo_Outcome` mirror. The dead `Demo_Status` writes were removed from both `handleMeetingEvent` and `handleDemoOutcome`.)*
- Deal `Opportunity_Stage` = `Proposal Preparation`, `Stage` = `FTP`.
- A `Draft Commercials` Task exists (Who = primary Contact, What = Deal).
- **A Draft Quote now exists for the Deal** (`getRelatedRecords("Quotes","Deals",dealId)`): `Quote_Stage` = `Draft`, `Account_Name`/`Deal_Name`/`Contact_Name` set, and `Quoted_Items` contains **one line** referencing `Jurnii UX - Fixed` with `Quantity` = 1. (The line is typically **unpriced** here — `Quoted_Item_Plan_Brands` is blank until the rep sets it.)

**Branch GP2b (insufficient product data → no empty Quote):** repeat the journey with a Lead that has **no** quote-ready Product Interest (or only an unmatched value). Assert that at Proposal Preparation `ensureDealQuote` raises a **Manual Review** Task instead of creating an empty/invalid Quote.

**On failure:** `ensureDealQuote` (seeding/guards), `processDeal` (the `finalOppStage == "Proposal Preparation"` hook + Product linking), `handleDemoOutcome` / `routeContactSequence` (stage propagation).

---

## Phase 3 — Quote pricing + contract ledger

**GP3 — Initial contract.** On the seeded Draft Quote: set the Quoted Item `Quoted_Item_Plan_Brands` = 10, `Quoted_Item_Pricing_Tier` = `Base`; set the Quote `Contract_Date_Start` = today. Then `Quote_Stage = "Delivered"` (wait 30s) → assert Deal `Commercials_Status` = `Sent`, `Commercials_Sent_At` set. Then `Quote_Stage = "Confirmed"` (wait 30s).

**Assert:**
- Quote: `Contract_ACV` = 18480.00, `Contract_Type` = `Initial`, `Contract_Signed_Date` set, `Contract_Date_End` = today + 1 year.
- Deal: `Contract_Initial_ACV` = 18480, Initial dates set, `Contract_Initial_Plan_Type` = `Fixed`, `Contract_Initial_Plan_Products` = `Jurnii UX`, `Contract_Initial_Plan_Brands` = 10, `Amount` = 18480, `Contract_Current_ACV` empty, `Commercials_Status` = `Signed`.
- Exactly **one** Confirmed Quote on the Deal.

**GP4 — Renewal supersedes.** Create a second Quote on the same Deal: one `Jurnii UX - Fixed` line, brands 12, Base; `Contract_Date_Start` = today; **set `Contract_Type` = `Renewed`**; `Quote_Stage = Confirmed`. Wait 30s.
**Assert:** Q1 → `Closed Won`; new Quote `Contract_ACV` = 19605.60; Deal `Contract_Current_ACV` = 19605.60, `Amount` = 19605.60; `Contract_Initial_*` unchanged; exactly one Confirmed Quote.

**GP5 / GP6 — Upsold / Renewed & Upsold.** Repeat GP4 with brands 20 (`Upsold`, £29,400) then brands 50 (`Renewed & Upsold`, £63,000); each supersedes the prior to `Closed Won` and updates `Contract_Current_*` + `Amount`.

**Classification guard:** create a later Quote and confirm it **without** `Contract_Type`. Assert it bounces to `Quote_Stage = On Hold` + a `Manual Review` Task; the Deal is **not** synced. (This is the A5 resolution — Contract_Type is rep-set, never inferred.)

---

## Phase 4 — Branch + edge matrix

| # | Scenario | Setup | Expected |
|---|---|---|---|
| E1 | Mixed plan | Fresh Deal; Quote w/ `UX - Fixed` @10 Base + `360 - Flex` @10 Base `Frequency=2x per day`; Confirm | `Contract_Initial_ACV` = 135,984.00; `Plan_Type` **blank** (mixed); `Plan_Products` = both; `Plan_Brands` = 20 |
| E2 | Between bands | `UX - Fixed` @8 Base | `Contract_Initial_ACV` = 14,784.00 (proves next-highest band 10) |
| E3 | Above max band | `UX - Fixed` @120 → Confirm | Quote → `On Hold`; `Manual Review` task; Deal not synced |
| E4 | Cortex (unpriced) | `Cortex - Fixed` @10 → Confirm | Quote → `On Hold`; `Manual Review` (reason `no_pricing_for_product`); not synced |
| E5 | Idempotency | After GP3 on an isolated Deal, set Quote `Negotiation` then back to `Confirmed` | No drift: `Contract_Initial_ACV` / `Amount` unchanged; still one Confirmed; no new Manual Review |
| E6 | Amount handoff | After a Confirmed Quote, no-op edit the Deal (fire `processDeal`) | `Amount` unchanged (not overwritten by product-sum) |
| E7 | Closed Lost (replacement possible) | Deal with 2 active Quotes; set one `Closed Lost` | No commercial-loss routing while another active Quote remains (log `replacement_possible`) |

---

## §9 — Cleanup
Read all records whose name/Subject starts with the session prefix; delete in order **Calls → Tasks → Events → Quotes → Deals → Contacts → Accounts → Leads**. Confirm none remain. (Confirmed/Closed Won Quotes are "do not delete" in production — fine for disposable test records.)

---

## Extension points (for the next agent)

Add new coverage here without disturbing the Phase 1→4 golden path. Known areas that other changes may touch — slot tests in following the same SETUP → mutate → wait → assert pattern:
- **Call / Meeting outcomes** driving `Opportunity_Stage` (`handleCallOutcome` WF006, `handleMeetingEvent` WF007) — see T16/T25 in `docs/archive/MCP_TEST_HARNESS_PROMPT.md`.
- **Task outcomes** (`handleTaskCompletion` WF008): activation routing via `Task_Sequence_Type` is now covered in **Phase 1b**; also the Send Commercials → Quote `Delivered` extension added in v6.
- **Email-event / date-router workflows** (WF009/WF010) — out of scope for MCP (need real emails / wall-clock); note as manual.
- **`Product_Interest` ↔ catalogue alignment** — the Lead picklist currently only half-matches the 6 `Product_Name` values (3 `- Fixed` match; 3 `- Flex` unselectable; 3 bare names match no Product). A test that a Flex-interest Lead seeds a Flex Quote line will fail until the picklist/aliases are aligned.
- For each added area: list the WF, the trigger field, and the expected record-state delta, and keep the run-log format consistent.

## Kickoff
On start, output:
```
v6 E2E harness ready. Confirm:
1. Is this org safe for create/delete?
2. Are the graph/sequence WFs + WF020 active and all functions published?
3. Round number for MCP_TEST_RUN_LOG_E2E.md?
```
Then wait for the user before running §0.
