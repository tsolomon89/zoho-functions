# v6 Single-Field Automation Audit

_Audited: 2026-06-19. Scope: `v6/*.deluge`, `v6/activity/*.deluge`, `docs/v6/*`. Goal: every
lifecycle transition is driven by **one** human command/outcome field (two only where the second is
genuine context); everything derived is CRUDed by functions. This doc is the authority reference for a
later agent configuring Zoho workflows + layouts._

---

## 1. Executive summary

The v6 system is **already close to the single-field target**. Each lifecycle has a clear command
field and a clear automation owner, and programmatic writes are consistently suppressed with
`{"trigger": List()}` to avoid workflow recursion. The contact-centric invariants hold:

- **Contact** owns lifecycle (`Stage`, `Sequence_*`). **Deal** is the commercial rollup. **Account** is
  a thin rollup. **Quote** is the commercial-document authority from Proposal Preparation onward.
- `_util_resolveContactAction` is **pure** (no reads/writes); `routeContactSequence` is the **only**
  Contact transition executor; `processDeal` is the **only** Deal reconciliation/rollup owner;
  `syncConfirmedQuoteToDeal` is the **only** contract-ledger writer.
- The demo lifecycle is owned by the **Meeting/Event** (`handleMeetingEvent`). The old Deal-direct
  `Demo_Outcome → WF005 → handleDemoOutcome` path was **retired & deleted** (2026-06-19); `Demo_Status`
  was removed as a concept (it never existed as a Deal field).

**What still needs action (none are loops/data-corruption; mostly config + 1 decision + doc):**
1. **Stage label (RESOLVED, docs-only)** — `Marketing Consent` is the canonical live value on
   `Contacts.Stage` + `Deals.Opportunity_Stage`; v6 code uses it consistently (zero `Marketing
   Qualification` stage *values* — only the legacy completion-field *name*). Documented
   `Marketing Consent ≙ MQL`; no rename (§7).
2. **Manual-field leakage risk** — derived fields (`Contact.Sequence_*`, Deal completion timestamps,
   contract-ledger, Account rollups) must be set **read-only / off rep layouts** so reps can't hand-edit
   them. Layout/profile config, not code (§5, §9).
3. **Duplicate Sequence Activation Tasks** — a concurrency race (processLead's explicit `processContact`
   call + WF001b2 create-trigger). Neutralised by supersede/idempotency-skip but still litters a 2nd
   task. Decision required (§6).
4. **Commercials_Status dual authority** — both a user command (WF004) and Quote-derived
   (`handleQuoteStageChange`). Intentional + loop-safe, but post-Proposal it should be treated as
   Quote-driven (mirror) and not hand-set (§4).
5. **One stale in-code comment** — `_util_resolveQuoteLinePrice` header claims pricing is unresolved
   (`valid=false`); the code actually prices (`ppb×brands`, 2dp, `valid=true`). Doc-in-code fix (§8).

No parallel stage writers, no workflow loops, and the Amount-after-Confirmed-Quote guard are all
correctly implemented. **This session also closed two routing gaps (§8): the full `Task_Outcome` layer
in `handleTaskCompletion`, and Commercial/Renewal meeting outcomes routed into the commercial machinery
in `handleMeetingEvent`.**

---

## 2. Field authority matrix

Legend — **Human?**: `yes` = user command field · `no` = automation-owned (should be read-only on rep
layouts) · `exc` = user-editable only for a documented exception. "Owner" = function that writes it.

### Contacts
| Field | Human? | Owner fn | Trigger | Downstream CRUD |
|---|---|---|---|---|
| `Stage` | exc (rep may correct; adoption is automated) | processContact (default), routeContactSequence (transitions), handleTaskCompletion (activation stage-adoption) | WF001b / activation / call / meeting / commercial | drives Opportunity_Stage rollup in processDeal |
| `Sequence_Type` | **no** | routeContactSequence (from `activate:<type>`) | activation Task | — |
| `Sequence_State` | **no** | routeContactSequence | every transition | gates resume/idempotency |
| `Sequence_Stage` (Email/Call/Meeting/Task) | **no** | routeContactSequence | every transition | next-activity creation |
| `Sequence_Step` | **no** | routeContactSequence | cadence advance | call attempt number |
| `Contact_Role1` | exc | processLead/processContact/processDeal (from Job_Title) | intake / rollup | Contact_Roles role, primary tiebreak |
| `Lost_Reasons` | exc | routeContactSequence (loss), handleCallOutcome (negative/DNC) | call:negative / demo:not_qualified / commercial:rejected | Deal viability |
| `State` / `Status` | exc | processContact default; routeContactSequence on loss **and on Running (`Status→Working`)** | intake / activation / loss | Deal + Account rollup (Deal `Opportunity_Status→Working` when any open Contact is Working) |
| `Contact_Completed_*_At` (8) | **no** | processContact (stamps on normalize) | WF001b | feed Deal completion dates |
| `Marketing_Consent_Status` | yes (consent capture) | — (read by sendSequencedEmail guard) | manual | suppresses sends if Not Consented/Withdrawn |

### Tasks
| Field | Human? | Owner fn | Trigger | Downstream CRUD |
|---|---|---|---|---|
| `Task_Sequence_Type` (Email/Call/Manual) | **yes** (the activation route) | rep sets on Activation Task | — | handleTaskCompletion → `activate:<type>` |
| `Status` (=Completed) | **yes** (the commit) | rep | WF008 | fires handleTaskCompletion |
| `Task_Outcome` | **yes** (the per-task command) | rep | WF008 | Activation: Suppress/Already Handled/Stage Incorrect + legacy route. Non-activation: Completed→task:positive or Type success; Blocked/Failed→Manual Review+hold; Needs Follow-Up→resume; Not Relevant→Manual Review; Already Handled→no-op |
| `Task_Type` | **no** | processContact / routeContactSequence / createAuxTask / sendSequencedEmail | task creation | classifies handler path |
| `Task_Sequence_Stage` (business stage context) | **no** | processContact / routeContactSequence | task creation | stage-adoption + dedup + stale guard |
| `Blocks_Sequence` | **no** | processContact / createAuxTask / routeContactSequence | task creation | resume gating |
| `Due_Date` (scheduled-send) | **no** | routeContactSequence (schedule_email) | postcall schedule | WFC-SchedEmail trigger |
| `Subject` / `Description` / `What_Id` / `Who_Id` | **no** | creating fn | — | links + audit payload (`SendKey:` etc.) |

### Calls
| Field | Human? | Owner fn | Trigger | Downstream CRUD |
|---|---|---|---|---|
| `Call_Outcome` | **yes** (the only field) | rep | WF006 | handleCallOutcome → token → routeContactSequence |
| `Next_Follow_Up_Date` | yes (2nd, **Deferred only**) | rep | with Deferred | reschedules a Call at that datetime |
| `Sequence_Managed` / `Sequence_Stage` / `Sequence_Attempt` | **no** | routeContactSequence / handleCallOutcome (create_call) | call creation | per-contact idempotency match |
| `Stale` | **no** | handleCallOutcome (stale), routeContactSequence (supersede) | stage change | excludes the call from processing |
| `Call_Purpose_Detail` / `Call_Type` / `Call_Start_Time` / `Block_Email_Until_Done` | **no** | routeContactSequence | call creation | — |

### Meetings / Events (demo source of truth)
| Field | Human? | Owner fn | Trigger | Downstream CRUD |
|---|---|---|---|---|
| `Meeting_Status` (Scheduled/Confirmed/Rescheduled/Cancelled/Completed) | **yes** (lifecycle) | rep / calendar integration | WF007 | handleMeetingEvent routing |
| `Meeting_Outcome` (read only when `Completed`) | **yes** (result) | rep | WF007 (Completed) | demo: `qualified/followup/not_qualified/noshow`; commercial/renewal: `Commercials Discussed`/`Intent to Sign`/`Renewal Agreed`/`Renewal Declined` → Deal `Commercials_Status` → handleCommercialsStatusChange |
| `Start_DateTime` / `End_DateTime` | **yes** (scheduling) | rep / integration | WF007 | reminder calc |
| `Reminder_Send_At` | **no** | handleMeetingEvent | scheduled/confirmed/rescheduled | (Event-owned reminder time) |
| `Meeting_Type` (Demo / Commercial Discussion / Renewal) | yes | rep | — | Demo → demo lifecycle; Commercial Discussion/Renewal → commercial machinery; other → skip |
| `Who_Id` / `What_Id` | yes (link) | rep / integration | — | resolves Contact + Deal |

> No-Show is read from **`Meeting_Outcome`** OR **`Meeting_Status = No Show`** — both route `demo:noshow`.

### Deals
| Field | Human? | Owner fn | Trigger | Downstream CRUD |
|---|---|---|---|---|
| `Commercials_Status` | **yes** (pre-Quote/manual) — see §4 | rep (WF004) **or** handleQuoteStageChange (suppressed mirror) | WF004 / Quote stage | handleCommercialsStatusChange → token → router |
| `DEP - Demo_Outcome` (retired) | — | none — **no longer written** by handleMeetingEvent | — | none; demo path is the Meeting. DEP-renamed dead field. |
| `Demo_Start_DateTime` / `Demo_Reminder_Send_At` | **no** | handleMeetingEvent (mirror) | WF007 | WF010c demo-reminder trigger (Deal-based) |
| `Opportunity_Stage` (current objective) | **no** (never-regress) | processDeal | WF001d / rollup | Stage (type) + completion dates + ensureDealQuote |
| `Stage` (Opportunity Type MQL/SQL/FTP/RTP) | **no** | processDeal (from Opportunity_Stage) | rollup | — |
| `Contact_Name` (primary) / `Primary_Contact` | **no** | processDeal (furthest viable open + role tiebreak) | rollup | all handlers resolve primary here |
| `Amount` | **no** | processDeal (Σ Unit_Price) **until** a Confirmed Quote, then syncConfirmedQuoteToDeal (ACV) | rollup / confirm | — |
| `*_Completed_At` (8 Deal stage dates) | **no** | processDeal | rollup | — |
| `Commercials_Sent_At` / `Signed_At` / `Intent_To_Sign` / `Commercials_Discussed_At` | **no** | handleCommercialsStatusChange | WF004 | — |
| `Contract_Initial_*` | **no** | syncConfirmedQuoteToDeal (first Confirmed) | WF020 confirm | ledger |
| `Contract_Current_*` | **no** | syncConfirmedQuoteToDeal (later Confirmed) | WF020 confirm | ledger |
| `Opportunity_State` (Open/Lost) / `Opportunity_Status` (New/Working/Closed) | **no** | processDeal (viability) | rollup | Account rollup. `Opportunity_Status→Working` when any open Contact is Working, else New. **Deals are never "Won"** (positive motion = `Opportunity_Stage`). Deals have **no bare `State`/`Status`** fields — those are Contact/Account-only. |
| `Deal_Key` / `Product_Interest_Staging` | **no** | processLead / processDeal | intake / rollup | dedup, product matching |
| `Automation_Suppressed` | yes (ops override) | manual | — | every handler's skip guard |

### Accounts
| Field | Human? | Owner fn | Downstream |
|---|---|---|---|
| `Account_Key` (UNIQUE) | **no** | processLead / processContact / processAccount | canonical Deal key |
| `State` / `Status` | **no** | processDeal (rollup) | — |
| AOO/Expansion fields | yes (firmographic) | processLead seeds blanks | — |

### Quotes (commercial-document authority)
| Field | Human? | Owner fn | Trigger | Downstream CRUD |
|---|---|---|---|---|
| `Quote_Stage` (Draft→Negotiation→Delivered→Confirmed; On Hold; Closed Won/Lost) | **yes** (the commercial command) | rep (WF020) | WF020 | handleQuoteStageChange |
| `Quoted_Items.Product_Name` | **yes** (line) | rep (ensureDealQuote seeds) | — | pricing |
| `Quoted_Item_Plan_Brands` | **yes** (brand-market count) | rep | — | band + line ACV |
| `Quoted_Item_Pricing_Tier` (Base/Markup/Agency) | **yes** | rep (default Base) | — | pricing tier |
| `Quoted_Item_Frequency` (Jurnii 360 only) | **yes** (when 360) | rep | — | 360 SKU |
| `Contract_Type` (Renewed/Upsold/Renewed & Upsold) | **yes** (2nd field, **later quotes only**) | rep | confirm | first-vs-later ledger branch |
| `Contract_Date_Start` | **yes** | rep | confirm | Contract_Date_End default |
| `Contract_ACV` / `Net_Order_Value` / `Contract_Signed_Date` | **no** | syncConfirmedQuoteToDeal | confirm | Deal ledger |
| `Contract_Date_End` | **no** (default +1yr if blank) | syncConfirmedQuoteToDeal | confirm | ledger |
| `List_Price` (Quoted Item) | **no** | ensureDealQuote seed (best-effort) | seed | display |
| `Account_Name`/`Deal_Name`/`Contact_Name` (Quote links) | **no** | ensureDealQuote | seed | sync resolution |

---

## 3. User-action matrix

| Human action | Field(s) user sets | Fn triggered | Records created/updated | Automation owns | Expected final state |
|---|---|---|---|---|---|
| Import/create Lead | Lead fields | WF001a → processLead | Account, Contact, canonical Deal; Lead→Converted | Account_Key, Contact enrich, Deal seed, Contact_Role | Contact at `Marketing Consent`, canonical Deal, **Sequence Activation Task** created |
| Activate sequence | `Task_Sequence_Type` + `Status=Completed` | WF008 → handleTaskCompletion | opener email audit Task, `… Call 1`; Contact updated | Stage adoption, Sequence_Type/State/Stage/Step, opener send, first Call, idempotency skip | Contact `Sequence_Type=<type>`, `Sequence_State=Running` (Manual→Stopped), Call 1 open |
| Activation exception | `Task_Outcome = Suppress / Already Handled / Stage Incorrect` (+Completed) | handleTaskCompletion | (Manual Review for Stage Incorrect) | `activate:stop` | Sequence Stopped; exception wins over Type |
| Log a call | `Call_Outcome` (+ `Next_Follow_Up_Date` if Deferred) | WF006 → handleCallOutcome | next Call / postcall scheduled email / Data Repair / Manual Review | progression, next Call, cadence email, stale marking, Lost_Reasons | Contact advanced or rescheduled per matrix |
| Book/confirm/reschedule demo | `Meeting_Status` (+`Start_DateTime`) | WF007 → handleMeetingEvent | demo-confirmation email; Event `Reminder_Send_At`; Deal demo mirrors | reminder calc, mirrors, `meeting:created`, stage→Demo Confirmation | Contact at Demo Confirmation; reminders set |
| Record demo result | `Meeting_Status=Completed` + `Meeting_Outcome` | handleMeetingEvent | post-demo email / no-show email / Draft Commercials task; Deal Commercials_Status=Drafting (qualified) | `demo:*` routing, stage move, Quote seed via processDeal | Qualified → Proposal Preparation + Draft Quote |
| Send commercials | `Quote_Stage = Delivered` | WF020 → handleQuoteStageChange | Deal `Commercials_Status=Sent` (suppressed) + commercial cadence | Commercials_Sent_At, commercial:sent routing | Deal commercials Sent; follow-up eligible |
| Confirm / sign | `Quote_Stage = Confirmed` (+ `Contract_Type` for later) | WF020 → handleQuoteStageChange → syncConfirmedQuoteToDeal | Quote stamps; Deal ledger; prior Quote→Closed Won | Contract_ACV/NOV/Signed_Date, Contract_Initial_*/Current_*, Amount, Commercials_Status=Signed | Deal `Signed`; ≤1 Confirmed; onboarding transition |
| Price a line | line Product + `Quoted_Item_Plan_Brands` + `Pricing_Tier` (+ `Frequency` for 360) | (read at confirm) | — | band, ppb×brands, line ACV, Quote ACV, Deal Amount | priced quote |
| Manual ops pause | `Deal.Automation_Suppressed = true` | — | — | every handler skips | sequence frozen |

---

## 3a. Outcome → reconciliation map (every outcome surface)

For each outcome surface: the **one** field the user sets, the handler, the token/write, and what
automation reconciles. `*` = changed this session (§8). Single owners hold throughout: Contact `Stage` =
routeContactSequence; Deal `Opportunity_Stage`/`Stage` = processDeal; contract ledger =
syncConfirmedQuoteToDeal.

| User action (the one field) | Handler | Token / write | Contact Stage | Deal Opp Stage / Type | Verdict |
|---|---|---|---|---|---|
| Activation Task: `Task_Sequence_Type`+Completed | handleTaskCompletion | activate:email/call/manual | enters/stops at adopted stage | rollup | ✅ |
| Stage Task `Task_Outcome=Completed` | handleTaskCompletion | task:positive `*` | advance | advance/recompute | ✅ fixed |
| Draft Commercials `Completed` | handleTaskCompletion | create Send Commercials task `*` | stays Proposal Preparation | — | ✅ fixed |
| Send Commercials Completed | handleTaskCompletion | Quote→Delivered → commercial:sent | Commercial Agreement | advance | ✅ |
| Onboarding Setup Completed | handleTaskCompletion | Sequence Complete | stays Onboarding | — | ✅ |
| Data Repair / Review Reply / Enrichment Completed | handleTaskCompletion | resume | re-enter | — | ✅ |
| Manual Review Completed | handleTaskCompletion | resume `*` | re-enter | — | ✅ fixed |
| Any Task `Blocked`/`Failed` | handleTaskCompletion | Manual Review + hold `*` | unchanged | unchanged | ✅ fixed |
| Any Task `Needs Follow-Up` | handleTaskCompletion | resume `*` | unchanged | — | ✅ fixed |
| Any Task `Not Relevant` | handleTaskCompletion | Manual Review `*` | unchanged | — | ✅ fixed |
| Call `Positive` | handleCallOutcome | call:positive | advance | advance | ✅ |
| Call Neutral/No Answer | handleCallOutcome | call:neutral/noanswer | next Call | — | ✅ |
| Call Deferred (+`Next_Follow_Up_Date`) | handleCallOutcome | call:deferred | reschedule | — | ✅ |
| Call Negative/Do Not Contact | handleCallOutcome | call:negative/donotcontact | Lost + viability | viability | ✅ |
| Call Already Handled / Manual Only | handleCallOutcome | alreadyhandled / manualonly | idempotent / stop | — | ✅ |
| Meeting Scheduled/Confirmed/Rescheduled | handleMeetingEvent | meeting:created | Demo Confirmation + reminder mirror | rollup | ✅ |
| Meeting Completed Qualified | handleMeetingEvent | demo:qualified | Proposal Preparation | advance | ✅ |
| Meeting Completed Needs Follow-up | handleMeetingEvent | demo:followup | Demo Hosted | — | ✅ |
| Meeting Completed Not Qualified | handleMeetingEvent | demo:not_qualified | Lost + viability | viability | ✅ |
| Meeting No Show (Outcome or Status) | handleMeetingEvent | demo:noshow `*` | Demo Booking | — | ✅ (Status fixed) |
| Meeting Cancelled | handleMeetingEvent | meeting:cancelled | Demo Booking + clear reminder | — | ✅ |
| Meeting `Commercials Discussed`/`Intent to Sign` | handleMeetingEvent `*` | Commercials_Status=Discussed / Intent to Sign → WF004 | commercial path | via processDeal | ✅ fixed |
| Meeting `Renewal Agreed` | handleMeetingEvent `*` | Commercials_Status=Intent to Sign (Signed needs Quote Confirmed) | intent only | — | ✅ fixed |
| Meeting `Renewal Declined` | handleMeetingEvent `*` | Commercials_Status=Rejected → commercial:rejected | Lost + viability | viability | ✅ fixed |
| Deal `Demo_Outcome` shortcut | (retired) | — | — | — | ✅ retired (field DEP-renamed; no longer written) |
| Quote Delivered | handleQuoteStageChange | commercial:sent | Commercial Agreement | advance | ✅ |
| Quote Confirmed initial | syncConfirmedQuoteToDeal | commercial:signed | Onboarding | advance + Amount | ✅ |
| Quote Confirmed renewal/upsell (+`Contract_Type`) | syncConfirmedQuoteToDeal | commercial:signed | Onboarding + supersede prior | Current ledger | ✅ |
| Commercials Sent/Signed/Rejected (direct) | handleCommercialsStatusChange | commercial:sent/signed/rejected | advance / Onboarding / Lost | rollup | ✅ |

---

## 4. Duplicate-ownership findings

| # | Area | Finding | Verdict |
|---|---|---|---|
| D1 | **Commercials_Status** | Writers: rep via WF004; `handleQuoteStageChange` (Delivered→Sent, Closed Lost→Rejected); `syncConfirmedQuoteToDeal` (→Signed); and now `handleMeetingEvent` Commercial/Renewal outcomes (→Discussed / Intent to Sign / Rejected). All non-WF004 writes are **suppressed** (`noTrigger`) and then call `handleCommercialsStatusChange` directly — no WF004 loop; `handleCommercialsStatusChange` is the single transition router. | **Loop-safe, but dual authority.** Per the target (Quotes = commercial authority from Proposal Prep), **Quote_Stage should be the primary driver** and `Commercials_Status` a mirror post-Proposal. Action: keep WF004 for the pre-Quote/manual path; make `Commercials_Status` **read-only on the rep Deal layout once a Quote exists** (or guide reps to drive `Quote_Stage`). No code change required. |
| D2 | **Amount** | `processDeal` (Σ Unit_Price) and `syncConfirmedQuoteToDeal` (ACV). | **Resolved correctly** — processDeal skips Amount once a Confirmed Quote exists (`processDeal.deluge:497-508`). Single effective owner per phase. |
| D3 | **Opportunity_Stage** | Written only by `processDeal` (never-regress). Handlers move `Contact.Stage`; processDeal rolls it up. | **No duplicate** — single owner; never-regress guard prevents rollback. |
| D4 | **demo:* routing** | Was dual (handleMeetingEvent + handleDemoOutcome via WF005). | **Resolved** — WF005 + handleDemoOutcome **deleted**; `handleMeetingEvent` is sole demo owner. |
| D5 | **Contact transitions** | Only `routeContactSequence` writes `Sequence_*`. handleCall/Task/Meeting/Commercials all delegate to it. | **No duplicate** — single executor. |
| D6 | **Contract ledger** | Only `syncConfirmedQuoteToDeal` writes `Contract_Initial_*`/`Current_*`. | **No duplicate** — single owner. |

---

## 5. Manual-field-leakage findings

Derived fields that must be **read-only on rep layouts / hidden** so users can't hand-maintain them
(automation owns them). None are code bugs — they are **layout + profile** config:

| Module | Fields to lock (read-only) | Why |
|---|---|---|
| Contacts | `Sequence_Type`, `Sequence_State`, `Sequence_Stage`, `Sequence_Step`, `Contact_Completed_*_At` (8) | router-owned; a manual edit re-fires WF001b1→processContact (idempotent, but noise) |
| Deals | `Opportunity_Stage`, `Stage`, `Amount`, `Contact_Name`/`Primary_Contact`, `Commercials_Sent_At`, `Signed_At`, `Intent_To_Sign`, `*_Completed_At` (8), `Contract_Initial_*`, `Contract_Current_*`, `Demo_Start_DateTime`, `Demo_Reminder_Send_At` | rollup/ledger-owned |
| Accounts | `Account_Key`, `State`, `Status` | rollup-owned |
| Quotes | `Contract_ACV`, `Net_Order_Value`, `Contract_Signed_Date`, `List_Price` | ledger/pricing-owned |
| Tasks | `Task_Sequence_Stage`, `Blocks_Sequence`, `Task_Type` | engine-owned (rep sets only `Task_Sequence_Type` + `Status` + exception `Task_Outcome`) |

**Leakage already removed:** `Deal.Demo_Outcome` is retired (DEP-renamed, no longer written, off-layout).
`Contact.Sequence_Type` is **intentionally rep-settable elsewhere**? No — it must be lock; the route is
chosen on the **Task** (`Task_Sequence_Type`), not on the Contact.

---

## 6. Idempotency & loop-suppression findings

| # | Mechanism | Status |
|---|---|---|
| I1 | All programmatic Deal/Contact/Account/Quote writes use `{"trigger": List()}` | ✅ consistently applied (processDeal, processContact, routeContactSequence, handleCommercialsStatusChange, handleQuoteStageChange, syncConfirmedQuoteToDeal) |
| I2 | Email send idempotency | ✅ `sendSequencedEmail` keys off `SendKey: <contact>|<deal>|<canonicalKey>` in a Completed `Email Sent` audit Task |
| I3 | Confirmed-quote ledger | ✅ `syncConfirmedQuoteToDeal` no-ops if already synced (same ACV + Deal.Amount), demotes prior **before** promoting (≤1 Confirmed holds mid-failure) |
| I4 | Quote seeding | ✅ `ensureDealQuote` skips if any open Quote exists |
| I5 | Call processing | ✅ stale-stage + processed-attempt guards; `Stale=Yes` excludes |
| I6 | Activation idempotency | ✅ Email/Call skipped if Contact already `Running` (handleTaskCompletion); Manual exempt |
| I7 | **Duplicate Sequence Activation Tasks** | ⚠️ **OPEN.** On the lead-convert path, `processLead` calls `processContact` explicitly **and** WF001b2 (Contacts create) fires it — both pass the dedup before either commits → **two** identical activation tasks. Neutralised downstream (completing one flips the contact to Running; the 2nd idempotency-skips/Defers on supersede), but it litters a task. **Decision (§ Required changes).** |
| I8 | Amount overwrite after confirm | ✅ guarded (`processDeal.deluge:497-508`) |
| I9 | WF005/handleDemoOutcome loop risk | ✅ removed entirely |

---

## 7. Stage-label findings (RESOLVED — `Marketing Consent` is canonical)

**Decision (locked):** **`Marketing Consent` is the canonical live stage value** on `Contacts.Stage` and
`Deals.Opportunity_Stage` (both verified via getFields this session). It maps functionally to the
**MQL / "Marketing Qualification" concept**, but the stored value stays `Marketing Consent`. Do **not**
rename the picklist.

**Code is already consistent (no drift):** every v6 file uses the *value* `"Marketing Consent"`; a grep
for `"Marketing Qualification"` finds **zero** uses as a stage value. The only occurrence is the legacy
completion-field *name* `Contact_Completed_Marketing_Qualification_At`, which `processContact:160` /
`processDeal:152` / `processLead:62,456` map *from* the value `"Marketing Consent"`. That legacy field
name may remain as-is. (`Contacts.Marketing_Consent` is a separate GDPR consent flag — the value-label
overlap is a known, documented naming quirk, not a bug.)

Canonical stage ladder + Opportunity Type (the processDeal rollup `>=7→RTP, >=5→FTP, >=2→SQL, else MQL`
already matches this):

| Stage (canonical value) | Opportunity Type |
|---|---|
| Marketing Consent (≙ MQL) | MQL |
| Demo Booking | SQL |
| Demo Confirmation | SQL |
| Demo Hosted | SQL |
| Proposal Preparation | FTP |
| Commercial Agreement | FTP |
| Onboarding | RTP |
| Renewal | RTP |

**Renewal entry (defined future work):** nothing auto-advances Onboarding → Renewal — `Onboarding Setup`
completion sets `Sequence_State=Complete` and the Contact stays at Onboarding (`onboarding complete ≠
renewal active`). Renewal becomes the objective only when the contract window approaches — a
**date-driven workflow off the contract ledger** (`Contract_Current_Date_End` / `Contract_*_Date_Renewal`)
is the defined future build, **not** triggered by onboarding completion.

**Action:** docs-only — keep the value, document the `Marketing Consent ≙ MQL` mapping (this section). No
picklist rename, no data migration, no code-literal change. *(Minor, non-blocking: the
`Calls.Sequence_Stage` context picklist still lists pre-v6 labels — `Demo Booked / Demo Attended /
Commercials Sent / Commercials Signed`. It is a context field, not the authoritative Stage; clean up
opportunistically.)*

---

## 8. Required code changes

The system is sound; the edits below are the only code changes. **C1 is done; C-A and C-B were
implemented this session to close the two routing gaps (§1).** C-A and C-B require a Dev-Hub republish
(MCP cannot publish Deluge source).

| # | File | Change | Status / Risk |
|---|---|---|---|
| C1 | `v6/activity/_util_resolveQuoteLinePrice.deluge` | Header comment was stale (claimed A2/A9 unresolved, `valid=false`); the body prices `ppb × brands` 2dp, `valid=true`. Header corrected to match. **Comment-only, behaviour-neutral.** | ✅ done |
| C-A | `v6/activity/handleTaskCompletion.deluge` | **Full `Task_Outcome` layer** for non-activation tasks: `Blocked`/`Failed`→Manual Review + hold; `Not Relevant`→Manual Review; `Needs Follow-Up`→`resume`; `Already Handled`→no-op; `Completed`→Type success — with `Draft Commercials`→surface `Send Commercials` (stay Proposal Prep, no advance), `Manual Review`/`Suppression Review` Completed→`resume`, generic Completed→`task:positive`. `task:positive` already existed in `_util` (no `_util` change). | ✅ done — republish |
| C-B | `v6/activity/handleMeetingEvent.deluge` | Allow `Commercial Discussion`/`Renewal` meeting types; on `Completed` route `Commercials Discussed`→Discussed, `Intent to Sign`/`Renewal Agreed`→Intent to Sign, `Renewal Declined`→Rejected, each → `handleCommercialsStatusChange` (intent only; the Quote owns Signed). Also `Meeting_Status=No Show`→`demo:noshow`. Demo-only blocks gated; commercial/renewal returns early. | ✅ done — republish |

**Deferred to decisions (not auto-patched):**
- **I7 dup activation tasks** — fix options: (a) remove `processLead`'s explicit `automation.processContact()` call and rely on WF001b2 create-trigger (needs confirmation WF001b2 reliably fires on lead-conversion-created Contacts — some orgs suppress create workflows on convert); (b) keep both but add a short-lived guard (e.g., processContact checks a "just created activation task this run" marker) — harder; (c) accept (current) since downstream neutralises. **Recommend (a) after verifying the convert-trigger fires.**
- **Stage label (§7)** — RESOLVED: keep `Marketing Consent` as canonical; no rename, no code-literal
  change (docs-only). Renewal entry remains defined **future** work (date-driven off the contract ledger),
  not an onboarding-completion advance.
- **`handleMeetingEvent` Demo_Outcome mirror** — RESOLVED: `handleMeetingEvent` **no longer writes** `Deal.Demo_Outcome`; the field is DEP-renamed (`DEP - Demo_Outcome`). The demo path is the Meeting/Event mirrored onto the Contact Stage; `sendDemoReminder` now gates on the Primary Contact's Stage (skip if past Demo Confirmation), not on `Demo_Outcome`.

> Already completed this session (not re-listed as changes): Task field migration to `Task_Sequence_*`;
> `Task_Sequence_Type` activation route; `Demo_Status` removal from `handleMeetingEvent` +
> `handleDemoOutcome`; WF005 + `handleDemoOutcome` retirement; `sendDemoReminder` Deal-mirror guard.

---

## 9. Required Zoho workflow / field / layout changes (manual — no MCP for layouts)

1. **Lock derived fields read-only on rep layouts** (the §5 list) for the rep profile(s). Highest-value
   anti-leakage step.
2. **`Task_Sequence_Type`** picklist (Email/Call/Manual) is created + on the Tasks layout (done). Confirm
   it's on the Activation-Task layout the reps use.
3. **`Demo_Outcome`** is **retired** — DEP-renamed (`DEP - Demo_Outcome`), no longer written, off the
   Deal layout. The demo path is the Meeting (mirrored onto the Contact Stage). Alongside it, the dead
   Deal fields **`Commercial_Outcome`** and **`Sequence_Status`** are likewise DEP-renamed.
4. **WF008** (Task Completion Handler) = `Create or Edit`, fires on `Status=Completed` — confirmed
   correct; no change.
5. **Stage label (§7) — RESOLVED:** keep `Marketing Consent`. **No picklist rename, no backfill, no
   code-literal change.** Document the `Marketing Consent ≙ MQL` mapping only.
6. **Dev-Hub republish (this session's code):** republish `handleTaskCompletion` (C-A) and
   `handleMeetingEvent` (C-B) — both behaviour changes; MCP cannot publish Deluge source.
   **Also delete (TODO):** the retired `handleDemoOutcome` (and `sequenceRouter`) Deluge **code units**
   in Dev Hub (MCP removed only the bindings — WF002/WF003/WF005/WF010a/WF010b automation records).
7. **WF010c (Deal `Demo_Reminder_Send_At`)** stays on Deals (date workflows can't bind to Meetings).
8. **Active workflow set** (verify): WF001a-d, WF004, WF006, WF007, WF008, WF009a-e, WF010c, WF010d,
   WFC-SchedEmail, WF020. (No WF002/003/005/010a/010b.)

---

## 10. Test plan

See **`docs/v6/SINGLE_FIELD_E2E_TEST_PLAN.md`** (15 cases proving one/two-field control, idempotency,
loss paths, Amount handoff, the Task outcome layer (T14), commercial/renewal meeting routing (T15), and
the stage-label resolution (T13)). Mermaid of the full single-field flow:
**`docs/v6/single-field-full-flow.mermaid`**.
