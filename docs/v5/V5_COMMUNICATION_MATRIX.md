# V5 Communication-State Matrix (authoritative — derived from working-tree functions)

Reconstructed from the **current consolidated V5 functions** (not template names, not V4,
not the provisional 33). Source of every email-producing branch = the resolver
`_util_resolveContactAction` (emitted `emailKind`/`sideEmailKind`) + `routeContactSequence`
(execution) + `sendSequencedEmail`/`sendScheduledEmailFromTask`/`sendDemoReminder`.

Terminology: `Contact.Stage` (objective) · `Deal.Opportunity_Stage` (Primary-Contact rollup)
· `Deal.Stage` = Opportunity Type (MQL/SQL/FTP/RTP). The Deal "Opportunity Stage" field's
API name is `Opportunity_Stage` (never a `Stage`-suffixed shorthand).

## Enumerated email branches (every kind actually emitted)
| Source fn / branch | Trigger token | Contact.Stage | Seq Type | Seq Stage | Step | Prior activity | Known outcome | Timing | Intended comms | Current key (code) | Proposed canonical | Recipient action | Evidence level |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| routeContactSequence `send_opener_then_call` | activate:email | (cadence stage) | Email | Call | 1 | none | n/a (cold) | immediate | initial outreach | `opener` → "{prefix} Email-First Intro" | `<stage>:1:initial` | reply / engage | **cold first touch — MUST NOT reference a call** |
| routeContactSequence Email-path step | (email cadence) | (cadence stage) | Email | Email | 1..5 | prior email | sent | scheduled +bd | numbered cadence | `cadence` → "{prefix} Email N" | `<stage>:N:{initial/follow-up/final}` | reply / engage | email-only; no call language |
| routeContactSequence sideEmail (call) | call:neutral / call:noanswer (N<5) | (cadence stage) | Call | Call | N | **Call attempt N** | **not connected** | immediate | follow-up after attempt | `cadence` → "{prefix} Email N" | `<stage>:N:follow-up` | reply / call back | **attempt made, NOT connected** — may say "tried to reach you"; must not say "as discussed" |
| routeContactSequence `schedule_email` + `email:postcall_due` | call:neutral (N=5) / email:postcall_due | (cadence stage) | Call/Email | Email | 5 | 5 attempts exhausted | not connected | scheduled +2bd | final low-pressure close | `postcall` → "{prefix} Post-Call Follow-Up" | `<stage>:5:final` (consolidated w/ cadence 5) | reply if interested | no connection proven; pause |
| meeting:created sideEmail | meeting:created | Demo Confirmation | any | Meeting | 0 | **Meeting booked** | booked | immediate (first link) | confirm attendance | `demo_confirmation` → "Demo Confirmation Email" | `demo-confirmation:0:confirmation` | note the meeting; prepare | meeting booked (proven) |
| sendDemoReminder (WF010c) | (date Demo_Reminder_Send_At) | Demo Confirmation | any | Meeting | 0 | Meeting upcoming | booked | scheduled (1bd before, AM) | protect attendance | `demo_reminder` → "Demo Confirmation Reminder Email" | `demo-confirmation:0:reminder` | attend or reschedule `${Users.Website}` | upcoming meeting (proven) |
| demo:noshow sideEmail | demo:noshow | Demo Confirmation → Demo Booking | any | Meeting→Call | 0 | **Meeting missed** | no-show | immediate | re-engage / reschedule | `demo_no_show` → "Demo Confirmation No-Show Email" | `demo-confirmation:0:no-show` | reschedule `${Users.Website}` | missed meeting (proven) — **must not imply attendance** |
| demo:qualified sideEmail | demo:qualified | Demo Hosted → **Proposal Preparation** | any | Task | 0 | **demo attended + qualified** | attended | immediate | next steps → proposal | `demo_post_demo` → "Demo Hosted Post-Demo Email" | `proposal-preparation:0:post-demo` | await proposal | demo attended (proven) — **may acknowledge the demo** |
| commercial:sent sideEmail | commercial:sent | Commercial Agreement | any | Call | 0 | **commercials sent** | sent | immediate | share proposal/terms | `commercials_terms` → "Commercial Agreement Terms Email" | `commercial-agreement:0:proposal-sent` | review/sign `${Accounts.Contract URL}` | commercials sent (proven) |
| commercial:signed sideEmail | commercial:signed | Onboarding | any | Task | 0 | **agreement signed** | signed | immediate | confirm + welcome | `commercials_signed_confirmation` → "Commercial Agreement Confirmation Email" | `onboarding:0:signed-confirmation` | await onboarding | signed (proven) |

## Branches that do NOT produce an email (no template)
| Kind / token | Why no template |
|---|---|
| `onboarding_kickoff` | mapped in `resolveTemplate` but **no resolver/handler branch emits it** → dead → **delete the kind; create no template** |
| `commercial:followup_due` | resolver → `create_call` (re-engage cadence), **no `sideEmail`** → re-uses cadence; **no distinct email** |
| `call:positive` / `task:positive` / `demo:followup` / `demo:cancelled` / `meeting:attended`/`cancelled`/`noshow` (advance) | advance to next stage entry; the email (if any) is the next stage's `:1:initial` cadence, not a distinct template |
| `call:deferred/negative/donotcontact/manualonly/baddata/notrelevant/alreadyhandled` | no email (reschedule/stop/aux Task) |
| Proposal Preparation / Onboarding entry (create_task) | Task-class; no cadence email (post-demo + signed-confirmation are the only event emails) |

## Cadence membership (from resolver)
Cadence stages (opener/cadence/postcall branches): **Marketing Consent, Demo Booking,
Demo Hosted, Commercial Agreement, Renewal** → 5 canonical each (`:1:initial`, `:2..4:follow-up`,
`:5:final`). Demo Confirmation = meeting-class (3 event). Proposal Preparation = task-class
(1 event: post-demo). Onboarding = task-class (1 event: signed-confirmation).

## Derived canonical inventory (31) — folder × count
Marketing Consent 5 · Demo Booking 5 · Demo Confirmation 3 · Demo Hosted 5 ·
Proposal Preparation 1 · Commercial Agreement 6 (5 cadence + proposal-sent) · Onboarding 1 ·
Renewal 5 = **31**.
Provisional was 33; **removed** `onboarding:0:kickoff` (dead) and
`commercial-agreement:0:follow-up` (not an email); **reclassified** post-demo → Proposal
Preparation. Consolidations: opener→`:1:initial`; cadence-5 + postcall→`:5:final`;
Email-First/Call-First/Post-Call-Chain families collapse into the one shared cadence.

## Evidence guardrails enforced in copy
- `<stage>:1:initial` (email entry) — no call reference.
- `<stage>:N:follow-up` (call path) — "tried to reach you", never "as discussed"/"thanks for speaking".
- `demo-confirmation:0:*` — meeting booked/upcoming/missed (proven).
- `proposal-preparation:0:post-demo` — demo attended (proven) → may acknowledge.
- `onboarding:0:signed-confirmation` — signed (proven).
