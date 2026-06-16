# V5 Email Architecture — Reconstruction & Review

Branch: `email-template-rewrite`
Scope: reconstruct the email communication model from the V5 Deluge functions and conform the
template corpus to it. Local repository only — no Zoho, MCP, publishing, live CRM, or email send.

This document supersedes the prior `EMAIL_TEMPLATE_REWRITE_REVIEW.md` (removed), which described
the earlier kebab-case / 81-template / 7-step-chain structure that this pass replaces.

---

## 0. Headline outcome

- The intended architecture was reconstructed **from the V5 functions**, not from filenames,
  folder names, the naming matrix, or the creation checklist.
- The corpus went from **81 → 49 templates**, restructured into **exactly 8 canonical Opportunity_Stage
  folders**, with the **email-first path added** and the **generic 7-step post-call chain
  removed** as a duplicate parallel cadence.
- Two V5 functions were changed deliberately and minimally to support this (resolver +
  sequenceRouter); all triggers, timing, stop conditions, and stage-transition logic are
  preserved. Every reachable V5 email branch resolves to exactly one valid template.

---

## A. V5 communication matrix

Reconstructed by reading every function in `v5/activity/` end to end. Columns:
Function · Trigger · Opportunity_Stage at send · First-touch mode · Prior event · Call outcome known ·
Sequence position · Intended communication · Template (resolver output).

| Function | Trigger | Opportunity_Stage | Mode | Prior event | Call outcome | Position | Intended communication | Template |
|---|---|---|---|---|---|---|---|---|
| sequenceRouter (bootstrap, Email First) | Initial activation, source = outbound/LinkedIn | cadence stage | Email-first | none | n/a (no call yet) | opener | Cold first touch | `{Stage} Email-First Intro` |
| sequenceRouter (bootstrap, Call First) | Initial activation / stage change | cadence stage | Call-first | none | n/a | call 1 created | (no email; createStageCall) | — |
| handleCallOutcome (Neutral) | Call_Outcome = Neutral, attempt N | cadence stage | either | call attempt N (connected) | Neutral | N | Follow-up after a call attempt | `{Stage} Email N` |
| handleCallOutcome (No Answer) | Call_Outcome = No Answer, attempt N | cadence stage | either | call attempt N (no connect) | No Answer | N | Follow-up after a call attempt | `{Stage} Email N` |
| handleCallOutcome (Positive) | Call_Outcome = Positive | any | either | conversation | Positive | — | (no email; advance Opportunity_Stage + re-route) | — |
| handleCallOutcome (after attempt 5) | Neutral/No Answer at attempt 5 | cadence stage | either | 5 attempts exhausted | mixed/unknown | terminal | Single email-only close | `{Stage} Post-Call Follow-Up` |
| sequenceRouter (post-call follow-up) | WF010 date trigger, Waiting on Email Trigger | cadence stage | either | calls exhausted | unknown | terminal | Single email-only close | `{Stage} Post-Call Follow-Up` |
| handleMeetingEvent (Scheduled/Confirmed) | Demo Event created/confirmed (WF) | Demo Confirmation | — | meeting booked | — | special | Confirm the booked meeting | `Demo Confirmation Email` |
| date trigger on Demo_Reminder_Send_At (WF) | 1 business day before demo | Demo Confirmation | — | meeting booked | — | special | Pre-demo reminder | `Demo Confirmation Reminder Email` |
| handleDemoOutcome (No Show) / handleMeetingEvent (No Show) | Demo_Outcome = No Show | Demo Confirmation | — | missed meeting | — | special | Recover / rearrange | `Demo Confirmation No-Show Email` |
| handleDemoOutcome (Attended - Qualified) | Demo_Outcome = Attended - Qualified | **Proposal Preparation** | — | demo held | — | special | Thank you + prepare commercials | `Demo Hosted Post-Demo Email` |
| handleCommercialsStatusChange (Sent) | Commercials_Status = Sent | Commercial Agreement | — | commercials issued | — | special | Initial agreement ready | `Commercial Agreement Terms Email` |
| handleCommercialsStatusChange (Signed) | Commercials_Status = Signed | **Onboarding** | — | agreement signed | — | special | Signed acknowledgement | `Commercial Agreement Confirmation Email` |
| (WF / manual onboarding kickoff) | onboarding_kickoff context | Onboarding | — | onboarding begun | — | special | Onboarding welcome | `Onboarding Kickoff Email` |
| handleEmailEvent (replied/bounced) | Email reply/bounce (WF009) | any | — | email sent | — | — | (no email; pause + Task) | — |
| handleTaskCompletion (Onboarding Setup / Draft Commercials) | Task completed | Onboarding / Proposal Preparation | Task-first | — | — | — | (no email; advance/complete) | — |

**Cadence stages** (run `createStageCall` → `handleCallOutcome` → numbered cadence): Marketing
Qualification, Demo Booking, Demo Confirmation, Demo Hosted, Commercial Agreement, Renewal.
**Task-first stages** (no call cadence, so `Email N` / post-call never fire): Proposal
Preparation, Onboarding.

### Key control-flow facts that drove classification
- **Email-first reuses the numbered cadence after the opener.** `sequenceRouter` Email-First
  bootstrap sends one cold email (`email_first_bootstrap`) then `createStageCall(…,1)`;
  thereafter `handleCallOutcome` sends `{Stage} Email N` exactly as in call-first. So only the
  **opener** is unique to email-first; Email 2–5 are shared. (Per the agreed model:
  Email-first = `Intro → Email 2 → … → Email 5`; Call-first = `call → Email 1 → … → Email 5`.)
- **One template name per attempt serves both Neutral and No Answer.** The resolver does not
  branch on outcome, so `{Stage} Email N` is written **call-outcome-agnostic** — it never claims
  a conversation occurred and never falsely claims a miss. (A separate "Connected Call" family
  was explicitly *not* created, since V5 does not expose that distinction.)
- **Post-Demo email is sent at Opportunity_Stage = Proposal Preparation** (`demo_attended_qualified`), and
  the **signed-agreement confirmation at Opportunity_Stage = Onboarding** (`commercials_signed_confirmation`).
  Both are filed by **objective**, not by the historical stage in their name.
- **Onboarding is Task-First**: it creates an "Onboarding Setup" task and completes on task
  completion. It never creates calls, so `Onboarding Email 1–2` and any post-call chain were
  **unreachable orphans** and were removed.

---

## B. Current-template audit (retain / add / remove / reclassify)

| Group | Prior (kebab, 81) | V5 reference | Decision |
|---|---|---|---|
| `{Stage} Email 1–5` (MQ, Demo Booking, Commercial Agreement, Renewal) | present | `handleCallOutcome` cadence | **Retain**, rewrite openers call-agnostic; Email 5 changed from hard close to "easing off the calls" |
| Demo Hosted Email 1–3 | present | cadence | **Retain**; **add Email 4–5** (reachable, were missing) |
| Demo Confirmation Email 1–5 | absent | cadence (Confirm-Attendance calls) | **Add** (stage runs a call cadence; was a gap) |
| `{Stage} Email-First Intro` (6 cadence stages) | absent | `email_first_bootstrap` | **Add** (email-first path was missing) |
| `{Stage} Post-Call Email Chain 1–7` (7 stages, 49 files) | present | `post_call_chain` (7-step loop) | **Remove**; replace with single `{Stage} Post-Call Follow-Up` per cadence stage |
| Onboarding Email 1–2 | present | none (Task-First) | **Remove** (unreachable orphan) |
| Demo Confirmation Email / Reminder / No-Show | present | demo_confirmation / demo_reminder / demo_no_show | **Retain** (distinct events) |
| Demo Hosted Post-Demo Email | present in Demo Hosted | demo_attended_qualified @ Proposal Preparation | **Reclassify → Proposal Preparation**; copy sharpened toward preparing commercials |
| Commercial Agreement Terms Email | present | commercials_terms @ Commercial Agreement | **Retain** |
| Commercial Agreement Confirmation Email | present in Commercial Agreement | commercials_signed_confirmation @ Onboarding | **Reclassify → Onboarding** |
| Onboarding Kickoff Email | present | onboarding_kickoff (resolver contract) | **Retain** (in Onboarding) |

---

## C. Final-template architecture (49 templates)

Sequence families: **Email-first cadence** (cold intro then shared numbered cadence),
**Call-first cadence** (numbered, call-outcome-agnostic), **Post-call follow-up** (single
terminal), **Meeting confirmation**, **Post-demo progression**, **Agreement sequence**,
**Onboarding sequence**.

| Folder (Opportunity_Stage) | Templates | Family | Trigger | Required link |
|---|---|---|---|---|
| Marketing Qualification | Email-First Intro; Email 1–5; Post-Call Follow-Up | email-first opener + call cadence + terminal | bootstrap / call outcomes / exhaustion | Website (intro, follow-up) |
| Demo Booking | Email-First Intro; Email 1–5; Post-Call Follow-Up | same | same | `${Users.Website}` |
| Demo Confirmation | Email-First Intro; Email 1–5; Post-Call Follow-Up; Demo Confirmation Email; Reminder; No-Show | cadence + meeting specials | call outcomes + meeting events | `${Users.Website}` |
| Demo Hosted | Email-First Intro; Email 1–5; Post-Call Follow-Up | cadence (post-demo follow-up calls) | call outcomes | `${Users.Website}` |
| Proposal Preparation | Demo Hosted Post-Demo Email | post-demo progression | demo_attended_qualified | none |
| Commercial Agreement | Email-First Intro; Email 1–5; Post-Call Follow-Up; Commercial Agreement Terms Email | cadence + agreement | call outcomes / commercials_terms | `${Accounts.Contract URL}` (cadence/terms); Website (intro) |
| Onboarding | Commercial Agreement Confirmation Email; Onboarding Kickoff Email | onboarding sequence | commercials_signed_confirmation / onboarding_kickoff | none |
| Renewal | Email-First Intro; Email 1–5; Post-Call Follow-Up | cadence | call outcomes | `${Accounts.Contract Renewal URL}` (cadence); Website (intro) |

---

## D. Folder migration

| Previous folder (kebab) | Canonical Opportunity_Stage folder | Templates moved | References updated |
|---|---|---|---|
| marketing-qualification | Marketing Qualification | 5 retained + 2 added | n/a (no code references repo paths) |
| demo-booking | Demo Booking | 5 retained + 2 added | n/a |
| demo-confirmation | Demo Confirmation | 3 retained + 7 added | n/a |
| demo-hosted | Demo Hosted | 3 retained + 4 added; Post-Demo moved out | n/a |
| commercial-agreement | Commercial Agreement | 6 retained + 2 added; Confirmation moved out | n/a |
| onboarding | Onboarding | Kickoff retained; +Confirmation (in); Email 1–2 removed | n/a |
| renewal | Renewal | 5 retained + 2 added | n/a |
| (new) | Proposal Preparation | +Demo Hosted Post-Demo Email (in) | n/a |

No `.deluge` function or config references repository folder paths or markdown filenames; the
resolver works on Zoho template **names**. Folder names now exactly match the eight Opportunity_Stage values.

---

## E. Deleted / consolidated templates

| Deleted | Prior V5 reference | Replacement | Reason | Unresolved ref? |
|---|---|---|---|---|
| `{Stage} Post-Call Email Chain 1–7` ×7 stages (49 files) | `post_call_chain` 7-step loop in sequenceRouter | `{Stage} Post-Call Follow-Up` (single) per cadence stage | Generic 7-step chain duplicated the numbered cadence as a parallel sequence with no per-step outcome info to justify distinct copy | No — resolver now returns the single follow-up; sequenceRouter sends once then completes |
| `Onboarding Email 1`, `Onboarding Email 2` | none reachable (Onboarding is Task-First) | none needed | Unreachable orphans; retaining them creates drift | No |

### V5 function changes (deliberate, minimal, documented)
1. **`_util_resolveTemplate.deluge`** — added `email_first_bootstrap → {Stage} Email-First Intro`
   (cold opener distinct from the call-first `Email 1`); changed
   `post_call_chain → {Stage} Post-Call Follow-Up` (was `{Stage} Post-Call Email Chain {step}`).
2. **`sequenceRouter.deluge`** — the post-call branch now sends one `Post-Call Follow-Up` and sets
   `Sequence_Status = Completed` (was a 1→7 step loop on a 3-day drip). Trigger (Waiting on Email
   Trigger), stop condition (Completed), and all other routing preserved.
3. **`handleCallOutcome.deluge`** — header comment updated to describe the single follow-up;
   **no logic change** (still stamps `Active_Email_Chain_Step = 1`, which now drives the one send).

No stage-transition logic, call cadence (1–5), timing, suppression, loss, or bootstrap routing
was altered. A separate "Connected Call" family was **not** introduced (would require V5 to first
expose the Neutral/No-Answer distinction, which it does not).

---

## F. Validation results

| Check | Result |
|---|---|
| Exactly 8 folders, names = Opportunity_Stage values | **Pass** (Marketing Qualification, Demo Booking, Demo Confirmation, Demo Hosted, Proposal Preparation, Commercial Agreement, Onboarding, Renewal) |
| No legacy/generic folders remain | **Pass** |
| Total templates | **49** |
| Every reachable V5 email branch → exactly one template | **Pass** (branch-coverage script) |
| Email-first path present (intro + shared cadence) | **Pass** (6 intros) |
| No email-first template references a prior call | **Pass** |
| Numbered cadence is call-outcome-agnostic (never implies a conversation) | **Pass** |
| Post-call: single terminal follow-up, not a parallel chain | **Pass** |
| Onboarding/Proposal Preparation carry no unreachable cadence | **Pass** |
| Forbidden literals (Jurnii, `${Deal*`, Email_Signature, attached, sandbox, duplicate, Stage Goal, Product Scope, Post-Call Email Chain) | **CLEAN** |
| Unresolved `[bracket]` placeholders / backtick-wrapped tags | **NONE** |
| Merge tags outside approved set | **NONE** |
| Initial contract links `${Accounts.Contract URL}` / renewal `${Accounts.Contract Renewal URL}` / scheduling `${Users.Website}` | **Correct per stage** |
| Exact-duplicate bodies / duplicate subjects | **NONE / all unique** |
| Any V5 function references a missing or deleted template | **No** |

Approved merge-tag counts: `${Organization.Organization Name}` ×34, `${Contacts.First_Name}` ×69,
`${Contacts.Account_Name}` ×53, `${Accounts.Contract URL}` ×7, `${Accounts.Contract Renewal URL}` ×6,
`${Users.Website}` ×27, `${User.First_Name}` ×49, `${userSignature}` ×49.

---

# Appendix — complete final copy (all 49 templates)

The full, current subject and body of every template follows, grouped by canonical folder.

## Marketing Qualification

### Marketing Qualification Email 1

```text
Subject: Following up after my call, ${Contacts.First_Name}

Hi ${Contacts.First_Name},

I tried to reach you by phone earlier today and wanted to follow up here as well. I'd like to make sure we have the right details for ${Contacts.Account_Name} and understand whether staying in touch would be useful for you.

If it helps, just reply and let me know whether you'd like to hear more from ${Organization.Organization Name}, and what's most relevant to your work at the moment. A one-line reply is plenty.

Best regards,

${User.First_Name}
${userSignature}
```

### Marketing Qualification Email 2

```text
Subject: Is this useful for ${Contacts.Account_Name}?

Hi ${Contacts.First_Name},

Following up on my earlier note, I want to make sure anything we send is genuinely relevant to you and the team at ${Contacts.Account_Name} — and nothing more.

Would you be happy for ${Organization.Organization Name} to keep in touch by email? If so, a quick reply is all I need, along with a note on what matters most to you right now so I can keep things relevant.

Best,

${User.First_Name}
${userSignature}
```

### Marketing Qualification Email 3

```text
Subject: A quick yes or no, ${Contacts.First_Name}?

Hi ${Contacts.First_Name},

I tried calling again today but couldn't reach you.

I don't want to fill your inbox with anything you haven't asked for, so before I send anything further I'd just like to check: are you happy for ${Organization.Organization Name} to stay in touch by email? A simple "yes" or "no" is perfect.

If someone else at ${Contacts.Account_Name} is better placed for this, let me know and I'll reach out to them instead.

Thanks,

${User.First_Name}
${userSignature}
```

### Marketing Qualification Email 4

```text
Subject: Shall we keep in touch, ${Contacts.First_Name}?

Hi ${Contacts.First_Name},

I haven't managed to reach you yet, so I wanted to ask directly: would it be useful for ${Organization.Organization Name} to stay in touch with ${Contacts.Account_Name}?

A one-word reply settles it either way, and if it's a yes I'll make sure anything I send is genuinely relevant to you.

Best regards,

${User.First_Name}
${userSignature}
```

### Marketing Qualification Email 5

```text
Subject: Easing off the calls, ${Contacts.First_Name}

Hi ${Contacts.First_Name},

I've tried you by phone a few times now without much luck, so I'll ease off the calls — I don't want to be a nuisance.

If staying in touch with ${Organization.Organization Name} would be useful, a one-line reply is all it takes, and I'll keep anything I send relevant to ${Contacts.Account_Name}.

Best regards,

${User.First_Name}
${userSignature}
```

### Marketing Qualification Email-First Intro

```text
Subject: A quick hello from ${Organization.Organization Name}

Hi ${Contacts.First_Name},

I'm reaching out from ${Organization.Organization Name} to introduce myself and check whether what we do might be relevant to you and the team at ${Contacts.Account_Name}.

Rather than assume, I'd rather ask: would it be useful to stay in touch? If so, just reply and let me know what's most relevant to your work at the moment, and I'll keep anything I send useful and brief.

Best regards,

${User.First_Name}
${userSignature}
```

### Marketing Qualification Post-Call Follow-Up

```text
Subject: Leaving this with you for now, ${Contacts.First_Name}

Hi ${Contacts.First_Name},

I haven't managed to reach you, so I'll leave it here for now rather than keep filling your inbox.

If staying in touch with ${Organization.Organization Name} would be useful at any point, you're welcome to reach out whenever it suits:

${Users.Website}

Wishing you and the team at ${Contacts.Account_Name} all the best.

Best regards,

${User.First_Name}
${userSignature}
```

## Demo Booking

### Demo Booking Email 1

```text
Subject: A short walkthrough for ${Contacts.Account_Name}?

Hi ${Contacts.First_Name},

I tried to reach you by phone earlier today and wanted to follow up here too.

I'd like to show you a short, tailored walkthrough of how ${Organization.Organization Name} could help ${Contacts.Account_Name}, focused on what matters most to you rather than a generic overview.

If that would be useful, you can pick a time that suits you here:

${Users.Website}

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Booking Email 2

```text
Subject: Worth a quick look together, ${Contacts.First_Name}?

Hi ${Contacts.First_Name},

Following up on my last note — a short live walkthrough is usually the quickest way to see whether ${Organization.Organization Name} is a good fit for how ${Contacts.Account_Name} works, far more so than reading about it.

We'd keep it brief and focused on your priorities. If you'd like to find a time, you can choose a slot here:

${Users.Website}

Best,

${User.First_Name}
${userSignature}
```

### Demo Booking Email 3

```text
Subject: Happy to work around your schedule

Hi ${Contacts.First_Name},

I tried calling again today but didn't manage to catch you.

I know diaries fill up quickly, so rather than go back and forth, you're welcome to pick whatever time works best for you and the team at ${Contacts.Account_Name}:

${Users.Website}

If there's anything specific you'd like the walkthrough to cover, just reply and let me know and I'll tailor it accordingly.

Warm regards,

${User.First_Name}
${userSignature}
```

### Demo Booking Email 4

```text
Subject: Still worth a conversation for ${Contacts.Account_Name}?

Hi ${Contacts.First_Name},

I don't want to keep chasing if the timing isn't right, so I'll keep this short.

If seeing how ${Organization.Organization Name} could support ${Contacts.Account_Name} is still of interest, a short walkthrough is the easiest next step. You can choose a time here:

${Users.Website}

If now isn't the moment, just let me know and I'll hold off.

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Booking Email 5

```text
Subject: I'll ease off the calls for now

Hi ${Contacts.First_Name},

I've tried reaching you by phone a few times without success, so I'll stop calling for now.

If a short walkthrough for ${Contacts.Account_Name} would still be useful, you can pick a time whenever it suits — no need to wait for me to call:

${Users.Website}

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Booking Email-First Intro

```text
Subject: An introduction — and an offer to show you

Hi ${Contacts.First_Name},

I wanted to introduce myself from ${Organization.Organization Name}. We work with teams like the one at ${Contacts.Account_Name}, and I'd value the chance to show you how in a short, tailored walkthrough.

If that sounds useful, you can pick a time that suits you here:

${Users.Website}

Or just reply and tell me what you'd most like it to cover.

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Booking Post-Call Follow-Up

```text
Subject: Here whenever you're ready, ${Contacts.First_Name}

Hi ${Contacts.First_Name},

I haven't managed to catch you, so I'll stop chasing for now.

If you'd ever like that short walkthrough for ${Contacts.Account_Name}, the door stays open — you can pick a time whenever it suits:

${Users.Website}

Thank you for your time, and all the best.

Best regards,

${User.First_Name}
${userSignature}
```

## Demo Confirmation

### Demo Confirmation Email 1

```text
Subject: Confirming your time with ${Organization.Organization Name}

Hi ${Contacts.First_Name},

I tried to reach you by phone and wanted to follow up here too. We have your demo with ${Organization.Organization Name} booked, and I'd like to make sure the time still works for you and the team at ${Contacts.Account_Name}.

You'll find the details in your calendar invitation. If you need to rearrange, you can pick a new time here:

${Users.Website}

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Confirmation Email 2

```text
Subject: Does your booked time still suit, ${Contacts.First_Name}?

Hi ${Contacts.First_Name},

Just following up to confirm your upcoming demo still works for you. A quick reply to let me know is a great help — and if the timing has shifted, you can rearrange here:

${Users.Website}

Looking forward to speaking with the team at ${Contacts.Account_Name}.

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Confirmation Email 3

```text
Subject: Quick confirmation on your demo

Hi ${Contacts.First_Name},

I haven't yet heard whether your booked time still suits, so I wanted to check in. If it does, no action is needed; if not, you can pick a more convenient slot here:

${Users.Website}

Either way, a quick word would be appreciated.

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Confirmation Email 4

```text
Subject: Making sure your demo goes ahead

Hi ${Contacts.First_Name},

I'd hate for your booked time to slip by accident, so I'm checking in once more. If you're still good to go, that's great — and if not, you can rearrange whenever suits ${Contacts.Account_Name}:

${Users.Website}

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Confirmation Email 5

```text
Subject: Holding your slot — just let me know

Hi ${Contacts.First_Name},

I've tried to confirm your demo a few times without hearing back, so I'll ease off for now. Your slot is still held, and if the timing no longer works you can rearrange here whenever you're ready:

${Users.Website}

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Confirmation Email-First Intro

```text
Subject: A quick introduction from ${Organization.Organization Name}

Hi ${Contacts.First_Name},

I'm getting in touch from ${Organization.Organization Name} to introduce myself and make sure we're set up to help you and the team at ${Contacts.Account_Name}.

If it would help to find a time to talk, you can choose a slot that works for you here:

${Users.Website}

Or simply reply and I'll take it from there.

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Confirmation Email

```text
Subject: Your demo with ${Organization.Organization Name} is confirmed

Hi ${Contacts.First_Name},

Thank you — your walkthrough with ${Organization.Organization Name} is now confirmed, and I'm looking forward to speaking with you and the team at ${Contacts.Account_Name}.

You'll find the date, time, and joining details in the calendar invitation in your inbox. If anything changes between now and then, you can rearrange to a time that suits you here:

${Users.Website}

If there's anything in particular you'd like to focus on, just reply and let me know so I can make the most of our time.

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Confirmation No-Show Email

```text
Subject: Sorry we missed each other, ${Contacts.First_Name}

Hi ${Contacts.First_Name},

We had a walkthrough scheduled today but weren't able to connect — I know how easily calendars get away from us.

I'd still very much like to show you how ${Organization.Organization Name} could help ${Contacts.Account_Name}. Whenever it's convenient, you can pick a new time here:

${Users.Website}

Hope to speak soon.

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Confirmation Post-Call Follow-Up

```text
Subject: Leaving the booking with you for now

Hi ${Contacts.First_Name},

I haven't been able to reach you to confirm the details, so I'll leave it with you for now.

If you'd like to confirm or rearrange your time with ${Organization.Organization Name}, you can do that here whenever it suits:

${Users.Website}

All the best to you and the team at ${Contacts.Account_Name}.

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Confirmation Reminder Email

```text
Subject: A quick reminder about your upcoming demo

Hi ${Contacts.First_Name},

Just a quick note ahead of your walkthrough with ${Organization.Organization Name}. The date, time, and joining link are in the calendar invitation already in your inbox.

If something has come up and the time no longer works, no problem at all — you can pick a new slot here:

${Users.Website}

Looking forward to speaking with you and the team at ${Contacts.Account_Name}.

Best,

${User.First_Name}
${userSignature}
```

## Demo Hosted

### Demo Hosted Email 1

```text
Subject: Following up after our conversation, ${Contacts.First_Name}

Hi ${Contacts.First_Name},

I tried to reach you by phone earlier today and wanted to follow up here as well.

Now that you've had a chance to see how ${Organization.Organization Name} could work for ${Contacts.Account_Name}, I'd like to help you take the next step whenever you're ready. If there's anything still open from our conversation, just reply and let me know.

If it's easier to talk it through, you can pick a time here:

${Users.Website}

Best,

${User.First_Name}
${userSignature}
```

### Demo Hosted Email 2

```text
Subject: Ready when you are, ${Contacts.First_Name}

Hi ${Contacts.First_Name},

Following up on my last note — whenever you and the team at ${Contacts.Account_Name} are ready, I'm happy to put together the next steps and walk you through what they involve.

If there's anything you'd like to discuss first, just reply or pick a time that suits you here:

${Users.Website}

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Hosted Email 3

```text
Subject: Anything I can help with, ${Contacts.First_Name}?

Hi ${Contacts.First_Name},

I tried to catch you by phone again today.

I don't want to move things forward before you're ready, so I'll just check: is there anything I can answer or help with to make the decision easier for ${Contacts.Account_Name}? A quick reply is all I need, or you can grab a time here:

${Users.Website}

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Hosted Email 4

```text
Subject: A clear next step for ${Contacts.Account_Name}?

Hi ${Contacts.First_Name},

I've been trying to reach you since the demo and don't want to let things drift.

If you're ready to take the next step, I can set it out for you — just reply and I'll make it straightforward. And if something's giving you pause, I'd genuinely like to understand it so I can help.

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Hosted Email 5

```text
Subject: Easing off the calls after the demo

Hi ${Contacts.First_Name},

I've tried you by phone a few times since the demo without managing to connect, so I'll ease off the calls.

Whenever you're ready to pick things back up for ${Contacts.Account_Name}, I'm here to help — just reply or grab a time:

${Users.Website}

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Hosted Email-First Intro

```text
Subject: Opening a conversation with ${Contacts.Account_Name}

Hi ${Contacts.First_Name},

I wanted to introduce myself from ${Organization.Organization Name} and open a conversation with you and the team at ${Contacts.Account_Name}.

If you'd like to talk through how we could help, you can pick a convenient time here:

${Users.Website}

Or just reply and let me know what would be most useful.

Best regards,

${User.First_Name}
${userSignature}
```

### Demo Hosted Post-Call Follow-Up

```text
Subject: Leaving the next step with you for now

Hi ${Contacts.First_Name},

I haven't managed to reach you since the demo, so I'll ease off for now rather than keep following up.

Whenever you'd like to pick things back up for ${Contacts.Account_Name}, I'm glad to help — just reach out:

${Users.Website}

Thank you for your time, and all the best.

Best regards,

${User.First_Name}
${userSignature}
```

## Proposal Preparation

### Demo Hosted Post-Demo Email

```text
Subject: Thank you for your time today, ${Contacts.First_Name}

Hi ${Contacts.First_Name},

Thank you for taking the time to meet with me today — it was good to speak with you and the team at ${Contacts.Account_Name}.

Now that we've spoken, I'll start putting together the commercial details for ${Contacts.Account_Name} and follow up shortly. In the meantime, if anything came to mind after our conversation or there's something you'd like me to clarify, just reply and I'll be glad to help.

Best regards,

${User.First_Name}
${userSignature}
```

## Commercial Agreement

### Commercial Agreement Email 1

```text
Subject: Following up on your agreement, ${Contacts.First_Name}

Hi ${Contacts.First_Name},

I tried to reach you by phone earlier today and wanted to follow up here as well.

I wanted to check whether you've had a chance to look over the agreement, and whether there's anything I can answer for you or the team at ${Contacts.Account_Name}.

You can review it here whenever it's convenient:

${Accounts.Contract URL}

If a quick conversation would help, just reply and I'll find a time that works.

Best,

${User.First_Name}
${userSignature}
```

### Commercial Agreement Email 2

```text
Subject: Anything to adjust on the terms, ${Contacts.First_Name}?

Hi ${Contacts.First_Name},

As ${Contacts.Account_Name} reviews the agreement, I wanted to check whether there's anything you'd like to discuss or adjust so it fits comfortably on your side.

I'm happy to talk through any of the detail. You can revisit the agreement here at any time:

${Accounts.Contract URL}

Just reply and let me know what would help.

Warm regards,

${User.First_Name}
${userSignature}
```

### Commercial Agreement Email 3

```text
Subject: Anything holding the agreement up, ${Contacts.First_Name}?

Hi ${Contacts.First_Name},

I tried to catch you by phone again today.

If there are any internal approvals or reviews still in progress at ${Contacts.Account_Name}, I'm glad to help in whatever way makes things easier. And if you're ready to go ahead, you can review and sign here:

${Accounts.Contract URL}

Just let me know where things stand.

Best regards,

${User.First_Name}
${userSignature}
```

### Commercial Agreement Email 4

```text
Subject: Happy to find a path that works, ${Contacts.First_Name}

Hi ${Contacts.First_Name},

I don't want to keep chasing, so I'll be brief.

If the agreement as it stands isn't quite right for ${Contacts.Account_Name}, I'd genuinely welcome the chance to understand what would make it work — just reply and tell me. And if you're ready to proceed, you can review and sign here:

${Accounts.Contract URL}

Best regards,

${User.First_Name}
${userSignature}
```

### Commercial Agreement Email 5

```text
Subject: Easing off the calls on your agreement

Hi ${Contacts.First_Name},

I've tried you by phone a few times without managing to connect, so I'll ease off the calls.

Whenever you're ready, the agreement is there to review and sign at your own pace:

${Accounts.Contract URL}

And if a quick question would help, just reply — I'm happy to help ${Contacts.Account_Name} however I can.

Best regards,

${User.First_Name}
${userSignature}
```

### Commercial Agreement Email-First Intro

```text
Subject: Introducing ${Organization.Organization Name}

Hi ${Contacts.First_Name},

I'm reaching out from ${Organization.Organization Name} to introduce myself and understand how we might support you and the team at ${Contacts.Account_Name}.

If it would help to talk it through, you can choose a time that suits you here:

${Users.Website}

Or simply reply and I'll be glad to help.

Best regards,

${User.First_Name}
${userSignature}
```

### Commercial Agreement Post-Call Follow-Up

```text
Subject: Leaving the agreement with you for now

Hi ${Contacts.First_Name},

I haven't managed to reach you, so I'll leave things here for now rather than keep following up.

The agreement remains available whenever you're ready to revisit it for ${Contacts.Account_Name}:

${Accounts.Contract URL}

If anything changes, just reach out and I'll gladly pick it back up.

Best regards,

${User.First_Name}
${userSignature}
```

### Commercial Agreement Terms Email

```text
Subject: Your agreement with ${Organization.Organization Name} is ready to review

Hi ${Contacts.First_Name},

Thank you for the time you've given us so far. Your agreement with ${Organization.Organization Name} is now ready for you and the team at ${Contacts.Account_Name} to review.

You can read it in full and sign here:

${Accounts.Contract URL}

If you or your finance team have any questions, or there's anything you'd like to talk through before signing, just reply and I'll be glad to help.

Best regards,

${User.First_Name}
${userSignature}
```

## Onboarding

### Commercial Agreement Confirmation Email

```text
Subject: Thank you — your agreement is all set

Hi ${Contacts.First_Name},

Thank you — we've received your signed agreement, and we're delighted to be working with you and the team at ${Contacts.Account_Name}.

Our team will be in touch shortly to get things underway. In the meantime, if you have any questions, just reply and I'll be happy to help.

Welcome aboard, and thank you for choosing ${Organization.Organization Name}.

Best regards,

${User.First_Name}
${userSignature}
```

### Onboarding Kickoff Email

```text
Subject: Welcome to ${Organization.Organization Name}, ${Contacts.First_Name}

Hi ${Contacts.First_Name},

Welcome aboard — we're really pleased to be working with you and the team at ${Contacts.Account_Name}.

To get started, I'd like to arrange a short kickoff so we can walk you through the first steps together and answer any questions you have. Whenever it's convenient, you can pick a time here:

${Users.Website}

If you'd prefer, just reply and let me know what suits you and I'll work around you.

Looking forward to getting started.

Best regards,

${User.First_Name}
${userSignature}
```

## Renewal

### Renewal Email 1

```text
Subject: Looking ahead to your renewal with ${Organization.Organization Name}

Hi ${Contacts.First_Name},

As your current term with ${Organization.Organization Name} comes up for renewal, I wanted to reach out and start the conversation early.

It's been a pleasure working with you and the team at ${Contacts.Account_Name}, and we'd love to continue. You can review the renewal agreement here whenever it's convenient:

${Accounts.Contract Renewal URL}

If you'd like to talk anything through first, just reply and I'll find a time that works.

Best regards,

${User.First_Name}
${userSignature}
```

### Renewal Email 2

```text
Subject: Continuing our work together, ${Contacts.First_Name}

Hi ${Contacts.First_Name},

Following up on your upcoming renewal — we'd be glad to keep supporting ${Contacts.Account_Name} into the next term, and to make sure the agreement still fits where you're heading.

You can review the renewal agreement here:

${Accounts.Contract Renewal URL}

If there's anything you'd like to revisit or discuss, just reply and let me know.

Best,

${User.First_Name}
${userSignature}
```

### Renewal Email 3

```text
Subject: Checking in on your renewal, ${Contacts.First_Name}

Hi ${Contacts.First_Name},

I tried to reach you by phone earlier today and wanted to follow up here as well.

I wanted to check in on where things stand with your renewal, so we can keep everything running smoothly for ${Contacts.Account_Name} without any gap. You can review and sign the renewal agreement here:

${Accounts.Contract Renewal URL}

If there are any approvals or adjustments I can help with, just let me know.

Best regards,

${User.First_Name}
${userSignature}
```

### Renewal Email 4

```text
Subject: Keeping things continuous for ${Contacts.Account_Name}

Hi ${Contacts.First_Name},

As your renewal date approaches, I wanted to make it easy to keep everything in place for ${Contacts.Account_Name} without interruption.

If the renewal as it stands works for you, you can review and sign here:

${Accounts.Contract Renewal URL}

And if anything needs adjusting before then, I'd genuinely welcome the chance to help — just reply and tell me what would work better.

Best regards,

${User.First_Name}
${userSignature}
```

### Renewal Email 5

```text
Subject: Easing off the calls on your renewal

Hi ${Contacts.First_Name},

I've tried reaching you by phone a few times without luck, so I'll ease off the calls.

Whenever it suits ${Contacts.Account_Name}, the renewal agreement is ready to review at your own pace:

${Accounts.Contract Renewal URL}

And if anything would be easier to talk through, just reply.

Best regards,

${User.First_Name}
${userSignature}
```

### Renewal Email-First Intro

```text
Subject: Introducing ${Organization.Organization Name} — looking ahead

Hi ${Contacts.First_Name},

I wanted to introduce myself from ${Organization.Organization Name} and open a conversation with you and the team at ${Contacts.Account_Name} about how we can support you going forward.

If you'd like to talk, you can pick a convenient time here:

${Users.Website}

Or just reply whenever it suits.

Best regards,

${User.First_Name}
${userSignature}
```

### Renewal Post-Call Follow-Up

```text
Subject: Leaving your renewal with you for now

Hi ${Contacts.First_Name},

I haven't managed to reach you, so I'll leave it here for now rather than keep filling your inbox.

If you'd like to continue with ${Organization.Organization Name}, the renewal agreement remains available whenever you're ready:

${Accounts.Contract Renewal URL}

Thank you for working with us, and all the best to the team at ${Contacts.Account_Name}.

Best regards,

${User.First_Name}
${userSignature}
```
