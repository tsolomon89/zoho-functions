# Sequence Transition Matrix (Contact-owned)

**Status:** authoritative design for the Contact-centric refactor. This is the
single source of truth consumed by `_util_resolveContactAction`, `sequenceRouter`
/ `routeContactSequence`, `sendSequencedEmail`, `createStageCall`, and every
activity handler. Do not reproduce transition rules elsewhere — call the resolver.

> Built from repo exports (not live-verified this session). Picklist values are
> exported / user-confirmed target values. `Sequence_Type` target values
> (`Email`/`Call`/`Manual`) are live only **after** the user renames the live
> picklist + migrates data (cutover prerequisite). Code targets those values.

## 1. State model

The Contact owns the journey. Its position is:

```
Contact.Stage + Sequence_Type + Sequence_State + Sequence_Stage + Sequence_Step
```

| Field | API name | Values | Meaning |
|---|---|---|---|
| Stage | `Stage` | Marketing Consent, Demo Booking, Demo Confirmation, Demo Hosted, Proposal Preparation, Commercial Agreement, Onboarding, Renewal | commercial pipeline position |
| Sequence type | `Sequence_Type` | Email, Call, Manual | entry action chosen at activation |
| Sequence state | `Sequence_State` | Not Activated, Running, Stopped, Complete | automation lifecycle |
| Sequence stage | `Sequence_Stage` | Email, Call, Meeting, Task | category of the **current/outstanding** action |
| Sequence step | `Sequence_Step` | None, 1–10 | step within the current Stage cadence |

`State` (Open/Lost) and `Status` (New/Working/Closed) are the **commercial record
state**, not activity type. They are not part of the sequence machine but are set
on terminal outcomes (loss/closure).

### Sequence_State semantics
- **Not Activated** — Activation Task has not chosen an automated entry action.
- **Running** — the sequence may create/schedule its next action.
- **Stopped** — no further automatic actions; restart only via a new/reopened
  Activation Task (see §7).
- **Complete** — no remaining automated action **right now**. Finishing one Stage
  does not by itself set Complete; advancing to another active Stage sets
  `Running` + the new Stage's first action.

There is **no `Paused` value.** Temporary waiting = `Running` + a future-dated
activity (Task/Call/Meeting `due/start` date). Manual interruption = `Stopped`.

## 2. Stage classes

| Stage | Class | Goal | Entry action category |
|---|---|---|---|
| Marketing Consent | Cadence | qualify → book demo | Call (or Email opener → Call) |
| Demo Booking | Cadence | book the demo meeting | Call (or Email opener → Call) |
| Demo Confirmation | Meeting | protect attendance | Meeting (demo already scheduled) |
| Demo Hosted | Cadence | qualify → proposal | Call (or Email opener → Call) |
| Proposal Preparation | Task | draft commercials | Task (internal) |
| Commercial Agreement | Cadence | obtain signature | Call (or Email opener → Call) |
| Onboarding | Task | kickoff / handoff | Task (internal) |
| Renewal | Cadence | renew | Call (or Email opener → Call) |

**Cadence** = the interleaved 5-attempt Call+Email loop (§4).
**Meeting** = demo confirmation/reminder/no-show emails + the scheduled meeting.
**Task** = a single blocking internal Task gates progression.

## 3. Activation (Activation Task outcome → entry action)

Activation Task: `Who_Id`=Contact, `What_Id`=Deal, `Status`=Not Started, blank
`Task_Outcome`. On completion `handleTaskCompletion` maps the outcome:

| Activation Task_Outcome (existing) | Sequence_Type | Sequence_State | Sequence_Stage | Sequence_Step | First action |
|---|---|---|---|---|---|
| Activate Email First | Email | Running | Call | 1 | send `{prefix} Email-First Intro`, then create Call 1 |
| Activate Call First | Call | Running | Call | 1 | create Call 1 (due now) |
| Manual Only | Manual | Stopped | None | None | no automated action |
| Suppress / Do Not Contact | Manual | Stopped | None | None | no automated action |
| Already Handled / Stage Incorrect | (unchanged) | Stopped | None | None | log; no action |

> Outcome label mapping is done in code against the **existing** `Task_Outcome`
> picklist (reuse `Activate Email First`/`Activate Call First`). If a value is
> missing live, report it — do not add picklist values. Task-class stages
> (Proposal Preparation, Onboarding) and the Meeting-class stage (Demo
> Confirmation) ignore Email/Call entry and use their stage entry action.

For **Task-class** and **Meeting-class** stages the entry action is fixed by the
Stage, regardless of activation choice:
- Proposal Preparation / Onboarding → `Sequence_Stage=Task`, `Step=1`, create one
  blocking internal Task (Draft Commercials / Onboarding Setup).
- Demo Confirmation → `Sequence_Stage=Meeting`; the demo meeting is the action;
  confirmation/reminder/no-show emails are event-driven (§6).

## 4. Cadence loop (Marketing Consent, Demo Booking, Demo Hosted, Commercial Agreement, Renewal)

Entry: `Sequence_Stage=Call`, `Step=1`, create **Call 1** (due now). If
`Sequence_Type=Email`, first send `{prefix} Email-First Intro`, then create Call 1.

Per **Call N** outcome (N = current `Sequence_Step`, 1–5):

| Call outcome | Stage | Sequence_State | Sequence_Stage | Step | Next action | Email |
|---|---|---|---|---|---|---|
| Positive (interested/qualified/booked) | → next Stage (§5) | Running | next Stage's entry category | 1 | next Stage entry action | per Stage |
| Neutral / No Answer, N < 5 | unchanged | Running | Call | N+1 | create **Call N+1** (+2 business days) | send `{prefix} Email {N}` (audit) |
| Neutral / No Answer, N = 5 | unchanged | Running | Email | 1 | schedule **Post-Call Follow-Up** email via future-dated Task (+2 bd) | send `{prefix} Email 5` (audit) |
| Negative / Not Relevant | unchanged | Stopped | None | None | none | — |
| Do Not Contact | unchanged → `State=Lost`,`Status=Closed` | Stopped | None | None | none | — |
| Deferred | unchanged | Running | Call | N (same) | reschedule Call N to deferral date | — |
| Bad Data / Already Handled | unchanged | Stopped | None | None | create/keep Data Repair or stop | — |

Post-Call Follow-Up send (the scheduled `Sequence_Stage=Email, Step=1` action):
→ send `{prefix} Post-Call Follow-Up`, then `Sequence_State=Complete` (no further
automated action for this Stage; Stage unchanged).

> Numbered cadence email is **call-outcome-agnostic**: one `{prefix} Email {N}`
> serves both Neutral and No Answer (no Email-First/Call-First split). The
> `{prefix} Email-First Intro` is only the email-entry opener, not a branch.

## 5. Positive Stage transitions

| From Stage | Positive trigger | To Stage | Notes |
|---|---|---|---|
| Marketing Consent | qualified / interested | Demo Booking | |
| Demo Booking | demo booked (Meeting created) | Demo Confirmation | meeting drives §6 |
| Demo Confirmation | meeting attended | Demo Hosted | no-show/cancel → §6 |
| Demo Hosted | qualified | Proposal Preparation | not qualified → `State=Lost` |
| Proposal Preparation | commercials drafted/sent | Commercial Agreement | Task completion |
| Commercial Agreement | signed | Onboarding | rejected → `State=Lost` |
| Onboarding | onboarding complete | Renewal | |
| Renewal | renewed | Renewal | loops / or Closed Won |

On any positive transition: `Sequence_State=Running`, `Sequence_Stage` = new
Stage's entry category, `Sequence_Step` = 1 (or `Task`/`Meeting` for those
classes). Deal rollup follows §8.

## 6. Meeting-class (Demo Confirmation) events
Driven by `handleMeetingEvent` / `handleDemoOutcome` (Deal-driven; Contact =
`Deal.Contact_Name`):
- Meeting created (from Demo Booking positive) → Stage=Demo Confirmation,
  `Sequence_Stage=Meeting`; send `Demo Confirmation Email`.
- Reminder date reached → send `Demo Confirmation Reminder Email`.
- Outcome Attended-Qualified → Stage=Demo Hosted/Proposal Preparation path;
  send `Demo Hosted Post-Demo Email`; create Draft Commercials Task.
- Outcome No Show → send `Demo Confirmation No-Show Email`; re-enter cadence.
- Outcome Cancelled → Stage back to Demo Booking; supersede; re-enter cadence.

## 7. Stop / restart / loss
- **Stopped**: no automatic actions. Restart only by the user creating/reopening
  a Sequence Activation Task and choosing Email/Call/Manual → `handleTaskCompletion`
  resets the Contact sequence fields (§3) → router starts.
- **Loss**: terminal commercial outcomes set `State=Lost`, `Status=Closed`,
  `Sequence_State=Stopped`. Stopping a Contact never auto-marks the Deal Lost.
- **Email reply / bounce** (`handleEmailEvent`): reply → keep `Running`, create a
  Review Reply Task (manual), do not auto-advance; bounce → `Stopped` + Data
  Repair Task; flag Contact for enrichment. No `Paused`.

## 8. Deal rollup (Primary Contact only)
When the Contact is `Deal.Contact_Name` (Primary):
```
Contact.Stage  → Deal.Opportunity_Stage
Contact.State  → Deal.Opportunity_State
Contact.Status → Deal.Opportunity_Status
```
Derive `Deal.Stage` (Opportunity Type) from `Opportunity_Stage`:
```
Marketing Consent      → MQL
Demo Booking           → SQL
Demo Confirmation      → SQL
Demo Hosted            → SQL
Proposal Preparation   → FTP
Commercial Agreement   → FTP
Onboarding             → RTP
Renewal                → RTP
```
Non-primary Contacts progress independently and do **not** rewrite Deal rollup.

## 9. Template resolution (Stage + Step → one canonical template)
`templatePrefix(Stage)`:
```
Marketing Consent     → "Marketing Qualification"   (folder/template prefix unchanged)
Demo Booking          → "Demo Booking"
Demo Confirmation     → "Demo Confirmation"
Demo Hosted           → "Demo Hosted"
Commercial Agreement  → "Commercial Agreement"
Renewal               → "Renewal"
```
- Numbered cadence step N (1–5): `"{prefix} Email {N}"`
- Email-entry opener: `"{prefix} Email-First Intro"`
- Post-call terminal: `"{prefix} Post-Call Follow-Up"`
- Specials (stage-driven, not numbered): `Demo Confirmation Email`,
  `Demo Confirmation Reminder Email`, `Demo Confirmation No-Show Email`,
  `Demo Hosted Post-Demo Email`, `Commercial Agreement Terms Email`,
  `Commercial Agreement Confirmation Email`, `Onboarding Kickoff Email`.

## 10. Idempotency & scheduling
- **SendKey** (audit-Task `Description`, best-effort): `ContactID | DealID |
  Stage | Sequence_Stage | Sequence_Step | templateName`. Search Completed
  `Email Sent` Tasks for Contact+Deal; skip if the exact SendKey exists. Audit
  Task created **after** confirmed send.
- **Delayed email**: create one future-dated Task (`Due_Date`=send date,
  `Status`=Not Started, `Sequence_Managed=Yes`, Description marker + SendKey),
  Who=Contact/What=Deal. A date-based Task workflow fires the send on `Due_Date`
  (same pattern as Deal WF010). The send flips the same Task to Completed
  (`Task_Type=Email Sent`) + message ID → becomes the audit record.
- **Recursion**: activity handlers update the Contact with workflow triggers
  suppressed and explicitly call `routeContactSequence`; the Contact field-change
  workflow calls the router only for approved manual/scheduled edits. Exactly one
  router owner per transition.

## 11. Resolver trigger tokens (`_util_resolveContactAction` contract)
`routeContactSequence(contactId, dealId, triggerOutcome)` passes one token to the
pure resolver `_util_resolveContactAction`. Handlers map their source outcome to a
token; the resolver is the single place transition rules live.

| Token | Emitted by | Effect (summary) |
|---|---|---|
| `activate:email` / `activate:call` / `activate:manual` / `activate:stop` | `handleTaskCompletion` (Activation Task outcome) | set `Sequence_Type` + entry action, or Stop |
| `call:positive` | `handleCallOutcome` | advance Stage (supersede) + entry |
| `call:neutral` / `call:noanswer` | `handleCallOutcome` | cadence email N + Call N+1 (or scheduled post-call after 5) |
| `call:deferred` | `handleCallOutcome` | keep Running; handler reschedules to follow-up date |
| `call:negative` / `call:donotcontact` | `handleCallOutcome` | Stop + Contact loss (Deal viability) |
| `call:manualonly` | `handleCallOutcome` | `Sequence_Type=Manual`, Stopped |
| `call:baddata` / `call:notrelevant` | `handleCallOutcome` | resumable block (Running, no action) + aux Task |
| `call:alreadyhandled` | `handleCallOutcome` | no-op |
| `task:positive` | `handleTaskCompletion` (Task-class) | advance Stage (supersede) + entry |
| `demo:qualified` / `demo:followup` / `demo:not_qualified` / `demo:noshow` / `demo:cancelled` / `demo:rescheduled` | `handleDemoOutcome` | Stage move + boundary email (sideEmail) / loss |
| `commercial:sent` / `commercial:signed` / `commercial:rejected` / `commercial:followup_due` | `handleCommercialsStatusChange`, `sendCommercialFollowUp` | Stage move + boundary email / loss / re-engage |
| `meeting:created` (a.k.a. `booked`) / `meeting:attended` / `meeting:cancelled` / `meeting:noshow` | `handleMeetingEvent` | Demo Confirmation entry / advance / revert / recover |
| `email:postcall_due` | (scheduled post-call path) | send post-call follow-up, then `Complete` |
| `resume` | WFC-Contact router / `handleTaskCompletion` (block cleared) | re-materialise the current outstanding action (guarded against open blocking Tasks) |

Stage-boundary special emails are carried as the resolver's `sideEmailKind`
(`demo_post_demo`, `demo_no_show`, `commercials_terms`,
`commercials_signed_confirmation`, `demo_confirmation`) and sent by
`routeContactSequence` via `sendSequencedEmail` — handlers contain no email logic.
