# v6 Single-Field E2E Test Plan

_Proves the single-field/two-field control model from `SINGLE_FIELD_AUTOMATION_AUDIT.md`. Each case
names **the only field(s) the user sets**, then asserts that automation owns everything else. Companion
to `docs/v6/E2E_TEST_HARNESS.md` (golden path) and `docs/v6/single-field-full-flow.mermaid`._

## Operating rules
- **Recipient:** `tlcsolomon+e2e<n>@gmail.com` (Gmail ignores `+suffix`; never bare
  `tlcsolomon@gmail.com` — it matches an existing Contact and lead-conversion reuses it).
- **Pacing:** workflows aren't instant — wait ≥30s after a mutation (≥60s after Lead conversion) before
  read-back; retry once before FAIL. MCP can't read the Function Execution Log — assert on record state.
- **Send verification:** if Gmail MCP is down, assert the in-CRM `Email Sent: <key>` audit Task (created
  only after a confirmed send) instead of inbox delivery.
- **MCP:** record CRUD (`createRecords`/`getRecord`/`getRecords`/`searchRecords`/`updateRecord`/
  `executeCOQLQuery`/`deleteRecords`), `getFields`/`createFields` (Field-CRUD), `getWorkflowRules`
  (Workflow-CRUD). Server names drift across sessions — re-probe with ToolSearch. Can't publish Deluge
  or delete fields via MCP.
- **Cleanup:** delete each test funnel after (Calls → Tasks → Events → Quotes → Deals → Contacts →
  Accounts → Leads). Give every record a `SF_<ts>` prefix.

## Pricing reference (Base tier, ppb × brand-markets, 2dp)
| Line | Brands | Band | line ACV |
|---|---|---|---|
| UX Fixed | 10 | 10 | 18,480.00 |
| UX Fixed | 8 | 10 | 14,784.00 |
| UX Fixed | 12 | 15 | 19,605.60 |
| UX Fixed | 20 | 20 | 29,400.00 |
| UX Fixed | 50 | 50 | 63,000.00 |
| 360 (2x per day) | 10 | 10 | 117,504.00 |

---

## T1 — Lead conversion creates the graph
**User sets:** Lead fields only (Last_Name, Email, Company, Website, Title decision-maker,
`Product_Interest = "Jurnii UX - Fixed"`). **Trigger:** WF001a → `processLead`.
**Assert (automation owns all):** a Contact (Email match) with `Account_Name` set; an Account with
non-empty `Account_Key`; one canonical Deal (`Deal_Key` ends `::active`, `Contact_Name` set,
`State=Open`); Deal `Opportunity_Stage = Marketing Consent` (live label), `Stage=MQL`; Contact_Roles has
the Contact as Decision Maker; UX-Fixed Product linked; **a Sequence Activation Task** exists
(`Task_Sequence_Type` blank, `Task_Sequence_Stage = Marketing Consent`, `Blocks_Sequence=Yes`).
**Pass = user touched zero derived fields.**

## T2 — Activation starts the sequence from one (+commit) field
**User sets:** on the Activation Task, `Task_Sequence_Type = Email` + `Status = Completed` (leave
`Task_Outcome` blank). **Trigger:** WF008 → `handleTaskCompletion`.
**Assert:** Contact `Sequence_Type=Email`, `Sequence_State=Running`, `Sequence_Stage=Call`,
`Sequence_Step=1`; one `Email Sent: marketing-consent:1:initial` audit Task; one open
`Marketing Consent Call 1`. Repeat with `=Call` → `activate:call` (Call 1, **no** opener email).
Repeat with `=Manual` → `Sequence_Type=Manual`, `Sequence_State=Stopped`, **no** Call, **no** email.
**Pass = rep never edited any `Contact.Sequence_*` field.**

## T3 — Call outcome advances/reschedules from one field
**User sets:** `Call_Outcome` (and `Next_Follow_Up_Date` **only** for Deferred). **Trigger:** WF006 →
`handleCallOutcome`.
**Assert:** Neutral ×N → next `Call N+1` auto-created, side cadence email per step, `Step` advances;
step 5 Neutral → terminal `:5:final` + a Scheduled-Send task (no Call 6). Deferred + `Next_Follow_Up_Date`
→ a rescheduled Call at that datetime (no stage change). Bad Data → Data Repair task; Not Relevant →
Manual Review task; Negative → Contact Lost (`No Fit`). **Pass = only `Call_Outcome` (+date for Deferred)
touched.**

## T4 — Meeting scheduled mirrors reminder without manual Deal edits
**User sets:** create a Demo Event with `Meeting_Type=Demo`, `Meeting_Status=Scheduled`, `Start_DateTime`,
`What_Id`=Deal, `Who_Id`=Contact. **Trigger:** WF007 → `handleMeetingEvent`.
**Assert (automation owns):** Event `Reminder_Send_At` = −1 business-day AM before start; Deal
`Demo_Start_DateTime` / `Demo_Reminder_Send_At` mirrored (LOCK); Contact → `Demo Confirmation`;
`demo-confirmation:0:confirmation` audit Task. Then `Meeting_Status=Confirmed` then `Rescheduled` (new
`Start_DateTime`) → `Reminder_Send_At` recalculated, **no** duplicate confirmation email. **Pass = no
manual Deal demo-field edits.**

## T5 — Meeting completed + qualified → Proposal Preparation
**User sets:** `Meeting_Status=Completed` + `Meeting_Outcome="Attended - Qualified"`. **Trigger:**
`handleMeetingEvent` → `demo:qualified`.
**Assert:** Contact → `Proposal Preparation`; `proposal-preparation:0:post-demo` audit Task; a
`Draft Commercials` task; Deal `Commercials_Status=Drafting`; processDeal rollup
`Opportunity_Stage=Proposal Preparation`, `Stage=FTP`. Also: `Meeting_Outcome="No Show"` →
`demo:noshow` → `demo-confirmation:0:no-show` + revert to Demo Booking. **Pass = `Meeting_*` only; no
`Deal.Demo_Status` exists/needed.**

## T6 — Proposal Preparation auto-seeds the Draft Quote
**User sets:** nothing (continuation of T5). **Trigger:** `processDeal` → `ensureDealQuote`.
**Assert:** a Draft Quote on the Deal (`Quote_Stage=Draft`), Account/Deal/Contact links set,
`Quoted_Items` has one `Jurnii UX - Fixed` line (`Quantity=1`). Negative branch: a Lead with **no**
quote-ready Product → at Proposal Preparation `ensureDealQuote` raises a **Manual Review** task instead
of an empty Quote. **Pass = no rep manually creates the first Quote.**

## T7 — Quote Delivered drives Commercials Sent
**User sets:** `Quote_Stage = Delivered`. **Trigger:** WF020 → `handleQuoteStageChange`.
**Assert:** Deal `Commercials_Status=Sent` (suppressed) and `Commercials_Sent_At` stamped (via the
direct `handleCommercialsStatusChange` call); commercial cadence eligible. **Pass = one field
(`Quote_Stage`).**

## T8 — Quote Confirmed drives the Initial contract ledger
**User sets:** line `Quoted_Item_Plan_Brands=10`, `Pricing_Tier=Base`, Quote `Contract_Date_Start=today`;
then `Quote_Stage=Delivered` then `Quote_Stage=Confirmed`. **Trigger:** WF020 →
`syncConfirmedQuoteToDeal`.
**Assert:** Quote `Contract_ACV=18480.00`, `Contract_Type=Initial`, `Contract_Signed_Date` set,
`Contract_Date_End=start+1yr`; Deal `Contract_Initial_ACV=18480`, Initial dates,
`Contract_Initial_Plan_Type=Fixed`, `Contract_Initial_Plan_Products=Jurnii UX`,
`Contract_Initial_Plan_Brands=10`, `Amount=18480`, `Commercials_Status=Signed`; exactly **one** Confirmed
Quote. **Pass = `Quote_Stage` (+ commercial inputs) only; ledger fields automation-owned.**

## T9 — Later Confirmed Quote → Current ledger + supersession
**User sets:** new Quote on same Deal, one UX-Fixed line brands 12 Base, `Contract_Date_Start=today`,
**`Contract_Type=Renewed`**, `Quote_Stage=Confirmed`. **Trigger:** `syncConfirmedQuoteToDeal`.
**Assert:** prior Quote → `Closed Won`; new Quote `Contract_ACV=19605.60`; Deal
`Contract_Current_ACV=19605.60`, `Amount=19605.60`; `Contract_Initial_*` unchanged; exactly one Confirmed.
**Negative (A5 guard):** confirm a later Quote **without** `Contract_Type` → bounces to `Quote_Stage=On
Hold` + Manual Review; Deal **not** synced. **Pass = two fields (`Quote_Stage` + `Contract_Type`).**

## T10 — Loss paths don't wrongly close the Deal when another viable Contact remains
**Setup:** Deal with **two** open Contacts (C1 primary, C2 open). **User sets (each sub-case):**
(a) `Call_Outcome=Negative` on C1; (b) `Meeting_Outcome="Attended - Not Qualified"` on C1's demo;
(c) `Quote_Stage=Closed Lost` (with a 2nd active Quote present).
**Assert:** the acting Contact is Lost, but the **Deal stays Open** (viability finds C2 / another active
Quote) and a **Manual Review** "review primary / replacement possible" task is raised. Repeat with C2
also closed → Deal closes Lost. **Pass = loss is one field; Deal viability is automation-owned + fail-safe.**

## T11 — Re-firing a workflow does not duplicate
**Action:** re-trigger each handler on an already-processed record (re-save the Activation Task; set the
same `Call_Outcome` again; set `Quote_Stage` Negotiation→Confirmed→Negotiation→Confirmed; re-run
`processDeal`). **Assert:** no second opener email / Call / Quote / Confirmed Quote / audit Task;
activation idempotency-skips when Contact already Running; `syncConfirmedQuoteToDeal` no-ops when already
synced. **Pass = idempotency guards hold.** *(Known: the lead-convert path may create **2** Activation
Tasks — see audit I7; completing one neutralises the other. This case documents that until I7's fix.)*

## T12 — processDeal does not overwrite Amount after a Confirmed Quote
**Action:** after T8 (Confirmed Quote, `Amount=18480`), make a no-op edit on the Deal to fire
`processDeal`. **Assert:** `Amount` stays `18480` (not overwritten by Σ Unit_Price). **Pass =
`processDeal.deluge:497-508` handoff works.**

## T13 — Stage-label audit (Marketing Consent is canonical)
**Action (read-only):** `getFields(Contacts)`/`getFields(Deals)`; grep v6 for `Marketing Qualification`.
**Assert:** live `Contacts.Stage` and `Deals.Opportunity_Stage` both use **`Marketing Consent`** (the
8-stage ontology); **no v6 code uses `Marketing Qualification` as a stage *value*** — the only occurrence
is the legacy field *name* `Contact_Completed_Marketing_Qualification_At`, which `processContact:160` /
`processDeal:152` / `processLead` map *from* the value `Marketing Consent`; `Deals.Stage` holds the
Opportunity Type (`MQL/SQL/FTP/RTP`). The `Marketing Consent ≙ MQL / Marketing Qualification concept`
mapping is documented (audit §7). **Pass = the canonical value is `Marketing Consent` everywhere; nothing
treats the *value* as "Marketing Qualification".**

## T14 — Task outcome layer (non-activation tasks honor `Task_Outcome`)
**User sets** on a non-activation sequence-managed Task: `Status=Completed` + `Task_Outcome=<value>`.
**Trigger:** WF008 → `handleTaskCompletion`. **Assert each:**
- `Completed` on a generic stage-gate Task → `task:positive` → Contact.Stage advances one step; `processDeal`
  advances Deal.Opportunity_Stage + recomputes Stage (Type); rep edited no derived field.
- `Completed` on **Draft Commercials** → a **Send Commercials** task is created (deduped) and the Contact
  **stays at Proposal Preparation** (no advance); completing Send Commercials → Quote Delivered →
  `commercial:sent` → Commercial Agreement.
- `Blocked` / `Failed` (any type, incl. Send Commercials) → a **Manual Review** task is created, sequence
  held, **no** advance and the Type side-effect does **not** run (no Quote delivered).
- `Needs Follow-Up` → `resume` at current stage, no advance.
- `Not Relevant` → **Manual Review** task, no advance.
- `Already Handled` → idempotent no-op.
- **Manual Review** task `Completed` → `resume`.
**Pass = the one field (`Task_Outcome`) is the command; automation owns every derived write.**

## T15 — Commercial / Renewal meeting outcomes route into the Deal/Quote machinery
**User sets:** an Event `Meeting_Type=Commercial Discussion` (or `Renewal`), `Meeting_Status=Completed`,
`Meeting_Outcome=<value>`, `What_Id`=Deal. **Trigger:** WF007 → `handleMeetingEvent`. **Assert:**
- `Commercials Discussed` → Deal `Commercials_Status=Discussed` → `handleCommercialsStatusChange` (stamps
  `Commercials_Discussed_At`; no premature Signed).
- `Intent to Sign` / `Renewal Agreed` → Deal `Commercials_Status=Intent to Sign`, `Intent_To_Sign` stamped;
  **not** Signed (signed still requires `Quote_Stage=Confirmed`).
- `Renewal Declined` → Deal `Commercials_Status=Rejected` → `commercial:rejected` → acting Contact Lost;
  **Deal stays Open** if another viable Contact remains, else closes Lost.
- Demo path intact: `Meeting_Status=No Show` directly (no Outcome) → `demo:noshow` → Demo Booking.
**Pass = no meeting outcome logs without routing; meetings set intent only, the Quote owns the ledger.**

---

## Coverage map
| Lifecycle | Case(s) | The one field |
|---|---|---|
| Intake | T1 | Lead fields |
| Activation | T2 | `Task_Sequence_Type` (+Completed) |
| Calls | T3 | `Call_Outcome` (+date Deferred) |
| Meeting schedule | T4 | `Meeting_Status` (+Start) |
| Demo result | T5 | `Meeting_Outcome` |
| Quote seed | T6 | (none — auto) |
| Commercials sent | T7 | `Quote_Stage=Delivered` |
| Initial ledger | T8 | `Quote_Stage=Confirmed` |
| Renewal ledger | T9 | `Quote_Stage` + `Contract_Type` |
| Loss viability | T10 | one outcome field |
| Idempotency | T11 | re-fire |
| Amount handoff | T12 | re-fire processDeal |
| Stage drift | T13 | read-only audit |
| Task outcome layer | T14 | `Task_Outcome` |
| Commercial/Renewal meeting | T15 | `Meeting_Outcome` |
