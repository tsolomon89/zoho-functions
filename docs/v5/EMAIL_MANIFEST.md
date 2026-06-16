# V5 Canonical Email Manifest (FINAL — derived from the working-tree state machine)

Authority: `docs/v5/V5_COMMUNICATION_MATRIX.md` (every email-producing V5 branch).
**Final derived count = 31** (provisional 33 → removed dead `onboarding:0:kickoff` and the
non-email `commercial-agreement:0:follow-up`; reclassified post-demo → Proposal Preparation).
One shared cadence keyed `<stage-slug>:<step>:<kind>`; `Sequence_Type` is **not** in the key.

## Terminology (active everywhere)
`Contact.Stage` (objective) · `Deal.Opportunity_Stage` (Primary-Contact rollup) ·
`Deal.Stage` = Opportunity Type (MQL/SQL/FTP/RTP). Deal Opportunity-Stage API name is
`Opportunity_Stage`.

## Canonical folders (exactly 8 — bare Stage labels, no brand prefix)
`Marketing Consent` · `Demo Booking` · `Demo Confirmation` · `Demo Hosted` ·
`Proposal Preparation` · `Commercial Agreement` · `Onboarding` · `Renewal`.

## Merge tags — EMPIRICALLY VERIFIED against Zoho's create API (2026-06-15)
A controlled 4-variant test proved Zoho accepts **only** the `${!<Module API>.<Field API>}`
form (`!` + underscore API names; rejects label/space forms with or without `!`, and API
names without `!`). Lookups (Account fields) nest through `Account_Name`. Verified set:
| Purpose | Tag |
|---|---|
| Contact first name | `${!Contacts.First_Name}` |
| Account name | `${!Contacts.Account_Name.Account_Name}` |
| Org / brand name | `${!org.company_name}` |
| Sending-user first name | `${!users.first_name}` |
| User signature | `${!userSignature}` |
| Booking / reschedule URL | `${!users.website}` |
| Contract URL (initial commercial) | `${!Contacts.Account_Name.Contract_URL}` |
| Contract Renewal URL | `${!Contacts.Account_Name.Contract_Renewal_URL}` |

**Rejected by Zoho (do not use):** `${Contacts.First Name}` (label), `${!Contacts.First Name}`
(label+bang), `${Contacts.First_Name}` (API no bang), `${!Organization.*}`, `${!Org.*}`,
`${!users.company}`, `${!Users.Website}` (caps), any `$[...]`, any `${Deal...}`.

Signature block (every template):
`<p>Best regards,</p><p>${!users.first_name}<br/>${!org.company_name}</p><p>${!userSignature}</p>`

---

## Specification table (31)
| # | canonical_key | folder | template_name | Stage | Step | kind | trigger | timing | prior event | known outcome | URL tag | V5 fn/branch |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | marketing-consent:1:initial | Marketing Consent | Marketing Consent - Initial 1 | Marketing Consent | 1 | initial | activate / cadence:1 | imm/sched | none | — | — | routeContactSequence |
| 2 | marketing-consent:2:follow-up | Marketing Consent | Marketing Consent - Follow-up 2 | " | 2 | follow-up | cadence:2 | imm/sched | prior touch | not connected | — | routeContactSequence |
| 3 | marketing-consent:3:follow-up | Marketing Consent | Marketing Consent - Follow-up 3 | " | 3 | follow-up | cadence:3 | imm/sched | prior touch | not connected | — | routeContactSequence |
| 4 | marketing-consent:4:follow-up | Marketing Consent | Marketing Consent - Follow-up 4 | " | 4 | follow-up | cadence:4 | imm/sched | prior touch | not connected | — | routeContactSequence |
| 5 | marketing-consent:5:final | Marketing Consent | Marketing Consent - Final 5 | " | 5 | final | cadence:5 / postcall | sched +2bd | 5 touches | not connected | — | routeContactSequence |
| 6 | demo-booking:1:initial | Demo Booking | Demo Booking - Initial 1 | Demo Booking | 1 | initial | activate / cadence:1 | imm/sched | none | — | `${!users.website}` | routeContactSequence |
| 7 | demo-booking:2:follow-up | Demo Booking | Demo Booking - Follow-up 2 | " | 2 | follow-up | cadence:2 | imm/sched | prior touch | not connected | `${!users.website}` | routeContactSequence |
| 8 | demo-booking:3:follow-up | Demo Booking | Demo Booking - Follow-up 3 | " | 3 | follow-up | cadence:3 | imm/sched | prior touch | not connected | `${!users.website}` | routeContactSequence |
| 9 | demo-booking:4:follow-up | Demo Booking | Demo Booking - Follow-up 4 | " | 4 | follow-up | cadence:4 | imm/sched | prior touch | not connected | `${!users.website}` | routeContactSequence |
| 10 | demo-booking:5:final | Demo Booking | Demo Booking - Final 5 | " | 5 | final | cadence:5 / postcall | sched +2bd | 5 touches | not connected | `${!users.website}` | routeContactSequence |
| 11 | demo-hosted:1:initial | Demo Hosted | Demo Hosted - Initial 1 | Demo Hosted | 1 | initial | demo:followup / cadence:1 | imm/sched | demo held | attended | — | routeContactSequence |
| 12 | demo-hosted:2:follow-up | Demo Hosted | Demo Hosted - Follow-up 2 | " | 2 | follow-up | cadence:2 | imm/sched | prior touch | not connected | — | routeContactSequence |
| 13 | demo-hosted:3:follow-up | Demo Hosted | Demo Hosted - Follow-up 3 | " | 3 | follow-up | cadence:3 | imm/sched | prior touch | not connected | — | routeContactSequence |
| 14 | demo-hosted:4:follow-up | Demo Hosted | Demo Hosted - Follow-up 4 | " | 4 | follow-up | cadence:4 | imm/sched | prior touch | not connected | — | routeContactSequence |
| 15 | demo-hosted:5:final | Demo Hosted | Demo Hosted - Final 5 | " | 5 | final | cadence:5 / postcall | sched +2bd | 5 touches | not connected | — | routeContactSequence |
| 16 | commercial-agreement:1:initial | Commercial Agreement | Commercial Agreement - Initial 1 | Commercial Agreement | 1 | initial | commercial:sent entry / cadence:1 | imm/sched | proposal sent | sent | `${!Contacts.Account_Name.Contract_URL}` | routeContactSequence |
| 17 | commercial-agreement:2:follow-up | Commercial Agreement | Commercial Agreement - Follow-up 2 | " | 2 | follow-up | cadence:2 | imm/sched | proposal sent | not connected | `${!Contacts.Account_Name.Contract_URL}` | routeContactSequence |
| 18 | commercial-agreement:3:follow-up | Commercial Agreement | Commercial Agreement - Follow-up 3 | " | 3 | follow-up | cadence:3 | imm/sched | proposal sent | not connected | `${!Contacts.Account_Name.Contract_URL}` | routeContactSequence |
| 19 | commercial-agreement:4:follow-up | Commercial Agreement | Commercial Agreement - Follow-up 4 | " | 4 | follow-up | cadence:4 | imm/sched | proposal sent | not connected | `${!Contacts.Account_Name.Contract_URL}` | routeContactSequence |
| 20 | commercial-agreement:5:final | Commercial Agreement | Commercial Agreement - Final 5 | " | 5 | final | cadence:5 / postcall | sched +2bd | proposal sent | not connected | `${!Contacts.Account_Name.Contract_URL}` | routeContactSequence |
| 21 | renewal:1:initial | Renewal | Renewal - Initial 1 | Renewal | 1 | initial | activate / cadence:1 | imm/sched | term ending | — | `${!Contacts.Account_Name.Contract_Renewal_URL}` | routeContactSequence |
| 22 | renewal:2:follow-up | Renewal | Renewal - Follow-up 2 | " | 2 | follow-up | cadence:2 | imm/sched | prior touch | not connected | `${!Contacts.Account_Name.Contract_Renewal_URL}` | routeContactSequence |
| 23 | renewal:3:follow-up | Renewal | Renewal - Follow-up 3 | " | 3 | follow-up | cadence:3 | imm/sched | prior touch | not connected | `${!Contacts.Account_Name.Contract_Renewal_URL}` | routeContactSequence |
| 24 | renewal:4:follow-up | Renewal | Renewal - Follow-up 4 | " | 4 | follow-up | cadence:4 | imm/sched | prior touch | not connected | `${!Contacts.Account_Name.Contract_Renewal_URL}` | routeContactSequence |
| 25 | renewal:5:final | Renewal | Renewal - Final 5 | " | 5 | final | cadence:5 / postcall | sched +2bd | 5 touches | not connected | `${!Contacts.Account_Name.Contract_Renewal_URL}` | routeContactSequence |
| 26 | demo-confirmation:0:confirmation | Demo Confirmation | Demo Confirmation - Confirmation | Demo Confirmation | 0 | confirmation | meeting:created | immediate | meeting booked | booked | `${!users.website}` | meeting:created sideEmail |
| 27 | demo-confirmation:0:reminder | Demo Confirmation | Demo Confirmation - Reminder | " | 0 | reminder | Demo_Reminder_Send_At | sched (1bd before) | meeting upcoming | booked | `${!users.website}` | sendDemoReminder |
| 28 | demo-confirmation:0:no-show | Demo Confirmation | Demo Confirmation - No-Show | " | 0 | no-show | demo:noshow | immediate | meeting missed | no-show | `${!users.website}` | demo:noshow sideEmail |
| 29 | proposal-preparation:0:post-demo | Proposal Preparation | Proposal Preparation - Post-Demo | Proposal Preparation | 0 | post-demo | demo:qualified | immediate | demo attended | attended/qualified | — | demo:qualified sideEmail |
| 30 | commercial-agreement:0:proposal-sent | Commercial Agreement | Commercial Agreement - Proposal and Terms | Commercial Agreement | 0 | proposal-sent | commercial:sent | immediate | commercials sent | sent | `${!Contacts.Account_Name.Contract_URL}` | commercial:sent sideEmail |
| 31 | onboarding:0:signed-confirmation | Onboarding | Onboarding - Agreement Confirmed | Onboarding | 0 | signed-confirmation | commercial:signed | immediate | agreement signed | signed | — | commercial:signed sideEmail |

---

# Full copy (hand-authored, channel-neutral, evidence-aware; verified `${!...}` tags)

Signature = the verified block above; shown as `+ SIG`.

## Marketing Consent
**1 · marketing-consent:1:initial** — Subject: `A quick hello from ${!org.company_name}`
`<p>Hi ${!Contacts.First_Name},</p><p>I'm getting in touch because I think there may be a useful fit between what we do at ${!org.company_name} and the work going on at ${!Contacts.Account_Name.Account_Name}. Before anything else, I want to make sure it's genuinely worth your time.</p><p>If you're open to it, could you reply with a line on what's front-of-mind for your team right now — and whether occasional, relevant updates from us would be welcome? If the timing isn't right, just say so and I'll step back.</p>` + SIG

**2 · marketing-consent:2:follow-up** — Subject: `Worth tailoring this to ${!Contacts.Account_Name.Account_Name}?`
`<p>Hi ${!Contacts.First_Name},</p><p>I wanted to follow up on my note. Rather than send anything generic, I'd prefer to share only what's relevant to ${!Contacts.Account_Name.Account_Name} — so a single line on your current priorities would help me get it right.</p><p>If now isn't the moment, I'm happy to leave it with you.</p>` + SIG

**3 · marketing-consent:3:follow-up** — Subject: `A couple of things that might help`
`<p>Hi ${!Contacts.First_Name},</p><p>I wanted to check in. We regularly share practical, no-fluff guidance that teams like ${!Contacts.Account_Name.Account_Name} have found useful, and I'm glad to point you to the most relevant pieces rather than everything at once.</p><p>Would that be helpful? A quick yes or no is all I need.</p>` + SIG

**4 · marketing-consent:4:follow-up** — Subject: `Shall I keep you in the loop, ${!Contacts.First_Name}?`
`<p>Hi ${!Contacts.First_Name},</p><p>I don't want to crowd your inbox, so I'll keep this short. If staying in touch could be useful for ${!Contacts.Account_Name.Account_Name}, a one-line reply keeps you on the list. If it's not the right time, that's completely fine and I won't keep chasing.</p>` + SIG

**5 · marketing-consent:5:final** — Subject: `Last note for now`
`<p>Hi ${!Contacts.First_Name},</p><p>This is my last note for the time being — I don't want to be a distraction. If it's ever useful to revisit how ${!org.company_name} could support ${!Contacts.Account_Name.Account_Name}, just reply and I'll pick things straight back up.</p><p>Either way, I appreciate your time.</p>` + SIG

## Demo Booking
**6 · demo-booking:1:initial** — Subject: `A short walkthrough for ${!Contacts.Account_Name.Account_Name}?`
`<p>Hi ${!Contacts.First_Name},</p><p>I'd like to offer ${!Contacts.Account_Name.Account_Name} a brief, tailored walkthrough of ${!org.company_name} — focused only on the outcomes that matter to your team, not a generic tour.</p><p>If that's useful, you can pick a time that suits you here: ${!users.website}. If you'd rather I work around a specific window, just reply and I'll sort it.</p>` + SIG

**7 · demo-booking:2:follow-up** — Subject: `15 minutes to see if it fits?`
`<p>Hi ${!Contacts.First_Name},</p><p>Following up on a walkthrough. A focused 15 minutes is usually enough to tell whether ${!org.company_name} is worth pursuing for ${!Contacts.Account_Name.Account_Name} — no preparation needed on your side.</p><p>Grab whatever time works: ${!users.website}.</p>` + SIG

**8 · demo-booking:3:follow-up** — Subject: `I'll tailor it to ${!Contacts.Account_Name.Account_Name}`
`<p>Hi ${!Contacts.First_Name},</p><p>I wanted to check in. I can shape the walkthrough entirely around ${!Contacts.Account_Name.Account_Name}'s priorities so it's time well spent — just let me know what you'd most want to see, or pick a slot here: ${!users.website}.</p>` + SIG

**9 · demo-booking:4:follow-up** — Subject: `Worth a quick look, ${!Contacts.First_Name}?`
`<p>Hi ${!Contacts.First_Name},</p><p>I'll keep this brief. If a short demo would help ${!Contacts.Account_Name.Account_Name} make a decision either way, I'd be glad to set it up: ${!users.website}. If the timing's off, tell me and I'll follow up later instead.</p>` + SIG

**10 · demo-booking:5:final** — Subject: `Closing the loop on a demo`
`<p>Hi ${!Contacts.First_Name},</p><p>I'll leave this here for now so I'm not chasing. Whenever a walkthrough for ${!Contacts.Account_Name.Account_Name} would be useful, the link stays open: ${!users.website}. Thanks for your time, ${!Contacts.First_Name}.</p>` + SIG

## Demo Hosted
**11 · demo-hosted:1:initial** — Subject: `Next steps after your ${!org.company_name} demo`
`<p>Hi ${!Contacts.First_Name},</p><p>Thank you for making time for the demo. I wanted to follow up on the next steps for ${!Contacts.Account_Name.Account_Name} and make sure any questions that have come up since are answered.</p><p>What would be most useful from here?</p>` + SIG

**12 · demo-hosted:2:follow-up** — Subject: `Anything else you need for ${!Contacts.Account_Name.Account_Name}?`
`<p>Hi ${!Contacts.First_Name},</p><p>I wanted to check in and see whether you need anything further to weigh up ${!org.company_name} for ${!Contacts.Account_Name.Account_Name} — more detail, specifics for your team, or a second look at any part of it.</p><p>Happy to help however is most useful.</p>` + SIG

**13 · demo-hosted:3:follow-up** — Subject: `Keeping things moving for ${!Contacts.Account_Name.Account_Name}`
`<p>Hi ${!Contacts.First_Name},</p><p>Following up to see how you're thinking about next steps. Whenever the timing is right, I can prepare what you need for ${!Contacts.Account_Name.Account_Name} to take this forward — no pressure either way.</p>` + SIG

**14 · demo-hosted:4:follow-up** — Subject: `Where would you like to take this?`
`<p>Hi ${!Contacts.First_Name},</p><p>A quick check-in. Is there anything I can clarify or prepare to help ${!Contacts.Account_Name.Account_Name} reach a decision? If it's a no for now, that's genuinely fine — just let me know.</p>` + SIG

**15 · demo-hosted:5:final** — Subject: `I'll pause here for now`
`<p>Hi ${!Contacts.First_Name},</p><p>I don't want to keep chasing, so I'll leave this with you. Whenever you're ready to revisit next steps for ${!Contacts.Account_Name.Account_Name}, just reply and I'll pick it straight back up.</p>` + SIG

## Commercial Agreement
**16 · commercial-agreement:1:initial** — Subject: `Following up on your ${!org.company_name} proposal`
`<p>Hi ${!Contacts.First_Name},</p><p>I wanted to follow up on the proposal for ${!Contacts.Account_Name.Account_Name} and check whether any questions have come up on the terms.</p><p>You can review everything here when convenient: ${!Contacts.Account_Name.Contract_URL}. I'm glad to talk through any part of it.</p>` + SIG

**17 · commercial-agreement:2:follow-up** — Subject: `Happy to walk through the details`
`<p>Hi ${!Contacts.First_Name},</p><p>Following up on the proposal for ${!Contacts.Account_Name.Account_Name}. If it helps, I can walk through any section or adjust details so it works for your team — the documents are here: ${!Contacts.Account_Name.Contract_URL}.</p>` + SIG

**18 · commercial-agreement:3:follow-up** — Subject: `Aligning on timing for ${!Contacts.Account_Name.Account_Name}`
`<p>Hi ${!Contacts.First_Name},</p><p>I wanted to check in on timing. If it's useful to align on a target start date for ${!Contacts.Account_Name.Account_Name}, I'm glad to coordinate around what works for you. The proposal remains here: ${!Contacts.Account_Name.Contract_URL}.</p>` + SIG

**19 · commercial-agreement:4:follow-up** — Subject: `Anything outstanding on the proposal?`
`<p>Hi ${!Contacts.First_Name},</p><p>Just checking whether anything is holding things up on the proposal for ${!Contacts.Account_Name.Account_Name}. I'm happy to resolve any final questions so it's an easy yes or no — review here: ${!Contacts.Account_Name.Contract_URL}.</p>` + SIG

**20 · commercial-agreement:5:final** — Subject: `Leaving the proposal with you`
`<p>Hi ${!Contacts.First_Name},</p><p>I'll leave this with you for now rather than keep chasing. Whenever ${!Contacts.Account_Name.Account_Name} is ready to proceed, everything you need is here: ${!Contacts.Account_Name.Contract_URL}, and a quick reply is all it takes to pick it back up.</p>` + SIG

## Renewal
**21 · renewal:1:initial** — Subject: `Your ${!org.company_name} renewal`
`<p>Hi ${!Contacts.First_Name},</p><p>I'm reaching out ahead of ${!Contacts.Account_Name.Account_Name}'s renewal to make sure everything is set and to answer any questions before it comes around.</p><p>You can review the renewal here: ${!Contacts.Account_Name.Contract_Renewal_URL}.</p>` + SIG

**22 · renewal:2:follow-up** — Subject: `Reviewing ${!Contacts.Account_Name.Account_Name}'s renewal`
`<p>Hi ${!Contacts.First_Name},</p><p>Following up on the renewal. I'm glad to review how things are going and the options available so it continues to fit ${!Contacts.Account_Name.Account_Name} — details here: ${!Contacts.Account_Name.Contract_Renewal_URL}.</p>` + SIG

**23 · renewal:3:follow-up** — Subject: `A quick renewal check-in`
`<p>Hi ${!Contacts.First_Name},</p><p>Just checking in on ${!Contacts.Account_Name.Account_Name}'s renewal. If there's anything you'd like to discuss or adjust, I'm here — the renewal is here whenever you're ready: ${!Contacts.Account_Name.Contract_Renewal_URL}.</p>` + SIG

**24 · renewal:4:follow-up** — Subject: `Anything you need from me?`
`<p>Hi ${!Contacts.First_Name},</p><p>Is there anything you need from me to finalise ${!Contacts.Account_Name.Account_Name}'s renewal? I'm happy to help it go smoothly — you can complete it here: ${!Contacts.Account_Name.Contract_Renewal_URL}.</p>` + SIG

**25 · renewal:5:final** — Subject: `Final note on your renewal`
`<p>Hi ${!Contacts.First_Name},</p><p>A last note on ${!Contacts.Account_Name.Account_Name}'s renewal so it doesn't slip by. Whenever you're ready, it's all here: ${!Contacts.Account_Name.Contract_Renewal_URL}, and a quick reply means I'll make sure it's handled.</p>` + SIG

## Demo Confirmation (event-specific)
**26 · demo-confirmation:0:confirmation** — Subject: `Your ${!org.company_name} demo is confirmed`
`<p>Hi ${!Contacts.First_Name},</p><p>Your demo for ${!Contacts.Account_Name.Account_Name} is confirmed — I'm looking forward to it. We'll keep it focused on what matters most to your team, so if there's anything specific you'd like us to cover, just reply and let me know.</p><p>If you need to change the time, you can do that here: ${!users.website}.</p>` + SIG

**27 · demo-confirmation:0:reminder** — Subject: `Reminder: your ${!org.company_name} demo is coming up`
`<p>Hi ${!Contacts.First_Name},</p><p>A quick reminder about your upcoming demo for ${!Contacts.Account_Name.Account_Name} — I'm looking forward to walking you through it.</p><p>If anything has changed and you need to move the time, you can reschedule here: ${!users.website}.</p>` + SIG

**28 · demo-confirmation:0:no-show** — Subject: `Sorry we missed each other — let's find another time`
`<p>Hi ${!Contacts.First_Name},</p><p>We had a demo in the diary but didn't manage to connect — no problem at all, these things happen. I'd still like to show ${!Contacts.Account_Name.Account_Name} what ${!org.company_name} can do.</p><p>Whenever it suits, you can pick a new time here: ${!users.website}.</p>` + SIG

## Proposal Preparation (event-specific — demo attended, proven)
**29 · proposal-preparation:0:post-demo** — Subject: `Thanks for your time — here's what happens next`
`<p>Hi ${!Contacts.First_Name},</p><p>Thank you for the demo — it was good to walk through ${!org.company_name} with you. Based on what we covered, the next step is to put together a proposal tailored to ${!Contacts.Account_Name.Account_Name}.</p><p>I'll be in touch shortly with the details. In the meantime, if any questions have come up, just reply.</p>` + SIG

## Commercial Agreement (event-specific — commercials sent, proven)
**30 · commercial-agreement:0:proposal-sent** — Subject: `Your ${!org.company_name} proposal & terms`
`<p>Hi ${!Contacts.First_Name},</p><p>Please find the proposal and terms prepared for ${!Contacts.Account_Name.Account_Name}. You can review and complete everything here: ${!Contacts.Account_Name.Contract_URL}.</p><p>I'm happy to walk through any detail — just reply and we'll find a time.</p>` + SIG

## Onboarding (event-specific — agreement signed, proven)
**31 · onboarding:0:signed-confirmation** — Subject: `Welcome aboard — your agreement is confirmed`
`<p>Hi ${!Contacts.First_Name},</p><p>Thank you — the agreement for ${!Contacts.Account_Name.Account_Name} is confirmed, and we're genuinely glad to have you on board with ${!org.company_name}.</p><p>I'll be in touch shortly to get onboarding underway. If anything comes up before then, just reply.</p>` + SIG

---

## Validation (pre-creation)
- Every `email_required` branch in the communication matrix maps to exactly one key here;
  every key here is reachable. No key contains `Sequence_Type`.
- Terminology: `Contact.Stage` / `Deal.Opportunity_Stage` / `Deal.Stage` (Opportunity Type). No hardcoded "Jurnii"; brand via `${!org.company_name}`.
- Only the empirically verified `${!...}` tags used; no label/space forms, no `$[...]`,
  no `${Deal...}`. Booking → `${!users.website}`; initial commercial →
  `${!Contacts.Account_Name.Contract_URL}`; renewal → `${!Contacts.Account_Name.Contract_Renewal_URL}`.
- `:1:initial` never references a call; cadence follow-ups never say "as discussed"/"thanks
  for speaking"; no-show never implies attendance; post-demo (demo proven) acknowledges it.
- No CRM-cleanup / duplicate-account / staging copy; no fabricated results; no manual
  dates/URLs/attachments; no unresolved `[...]` placeholders.

## Folder IDs (created 2026-06-15)
Marketing Consent 991103000001471001 · Demo Booking 991103000001472001 ·
Demo Confirmation 991103000001471003 · Demo Hosted 991103000001473001 ·
Proposal Preparation 991103000001474001 · Commercial Agreement 991103000001475001 ·
Onboarding 991103000001472003 · Renewal 991103000001476001.
