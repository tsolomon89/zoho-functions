# v6 Email Copy Verification Tracker

Date: 2026-06-25 (updated after Email CRUD MCP readback)
Branch: `codex/v6-lifecycle-closeout`
Target org: Jurnii.io, `org20114906201`

**UPDATE:** The Zoho **Email CRUD MCP is now available**, so template copy, subjects, merge fields, folders
and active status ARE now live-readable. A full read-only readback was performed on 2026-06-25 (folders +
all 31 templates; priority templates fetched in full). The previously MCP-blind items below are now
**RESOLVED** with live evidence. Any live copy *edits* remain outward-facing and are applied + read back.

## Live readback result (2026-06-25)

- **Folders (live, confirmed):** Marketing Consent `991103000001471001`, Demo Booking `991103000001472001`,
  Demo Confirmation `991103000001471003`, Demo Hosted `991103000001473001`, Proposal Preparation
  `991103000001474001`, Commercial Agreement `991103000001475001`, Onboarding `991103000001472003`,
  Renewal `991103000001476001`. No separate "no-show"/"post-demo" folder: the one-off no-show lives in
  **Demo Confirmation**; post-demo in **Proposal Preparation**.
- **All 31 lifecycle templates are live and `active: true`**, `content_type: html`, `primary_module: Contacts`.
- **Merge syntax is clean everywhere** — only the verified `${!Module.Field}` bang form is used
  (`${!Contacts.First_Name}`, `${!Contacts.Account_Name.Account_Name}`, `${!org.company_name}`,
  `${!users.first_name}`, `${!users.website}`, `${!userSignature}`). **No** rejected/no-bang syntax exists
  live (the bad syntax was only ever in the `V5_EMAIL_ARCHITECTURE_REVIEW.md` draft).
- **No shared signature/footer object:** `email_footer` is `null` on every template; templates end with the
  `${!userSignature}` merge variable, resolved per sending user at send time. `getEmailSignatures` returned
  empty for the current user — signature consistency depends on each user configuring their CRM signature.

## Verification Items

| # | Item | Template / scope | Live finding | Status |
| --- | --- | --- | --- | --- |
| 1 | Demo Hosted - Initial 1 attendance implication | `demo-hosted:1:initial` — id **991103000001476007** | **CONFIRMED DEFECT.** Live body: *"Thank you for making time for the demo. I wanted to follow up on the next steps…"* — asserts the contact attended. Under SEQ-1 (missed demos route into this chain) this opener now goes to non-attendees. **Needs rewrite to missed-demo copy.** | **RESOLVED — rewrite required (proposed, awaiting go-ahead)** |
| 2 | No-show vs demo-hosted:1 single-opener (MTG-5) | `demo_no_show` (id 991103000001476010) vs `demo-hosted:1:initial` (id 991103000001476007) | **DECIDED:** `demo-hosted:1:initial` is the sole missed-demo opener; the one-off `demo_no_show` send is suppressed in code (routeContactSequence). The live `demo_no_show` copy is correctly worded for a miss ("didn't manage to connect") and stays in place as a template but is no longer auto-sent on this path. | **RESOLVED (decision applied in code `cdf722e`)** |
| 3 | Merge-syntax verification (all templates) | All 31 templates + signature | **PASS.** Every template uses only the verified `${!Module.Field}` form; no rejected tags. | **RESOLVED — no action** |
| 4 | Folder-name check ('Marketing Consent') | Folder `991103000001471001` + 8-folder set | **PASS.** Live folder is named "Marketing Consent"; all 8 folder names match the registry. | **RESOLVED — no action** |
| 5 | demo-hosted:2 soft attendance implication | `demo-hosted:2:follow-up` — id **991103000001470002** | Live body: *"…or a second look at any part of it."* softly presumes they already saw the demo. Lower severity than #1; reword for consistency on the recovery path. | **RESOLVED — secondary rewrite proposed** |
| 6 | demo-hosted:3/4/5 | ids 991103000001477003 / 991103000001471007 / 991103000001488001 | Attendance-neutral; safe for the missed-demo recovery path. | **RESOLVED — no action** |

## Proposed rewrites (awaiting go-ahead before live write)

Outward-facing change → the new copy is proposed here and will be applied via
`updateEmailTemplateById` + read back only on explicit approval. Both preserve the exact merge-tag set and
sign-off block; both add the `${!users.website}` reschedule link; both avoid attendance/proposal language
and get progressively shorter (spec §10).

**`demo-hosted:1:initial` (991103000001476007) — Step 1 (acknowledge the miss, no blame, reschedule link)**
- Subject: `Let's find another time for your ${!org.company_name} demo`
- Body:
  > Hi ${!Contacts.First_Name},
  > We had a demo in the diary but didn't manage to connect — no problem at all, schedules shift.
  > I'd still like to show ${!Contacts.Account_Name.Account_Name} what ${!org.company_name} can do. Whenever it suits, you can pick a new time here: ${!users.website}.
  > Best regards,
  > ${!users.first_name} / ${!org.company_name} / ${!userSignature}

**`demo-hosted:2:follow-up` (991103000001470002) — Step 2 (still interested? easy rebooking)**
- Subject: `Still keen on a quick ${!org.company_name} demo?`
- Body:
  > Hi ${!Contacts.First_Name},
  > Just following up — are you still interested in seeing ${!org.company_name} for ${!Contacts.Account_Name.Account_Name}? No worries if the timing wasn't right before.
  > If you'd like, grab a slot that works for you here: ${!users.website}.
  > Best regards,
  > ${!users.first_name} / ${!org.company_name} / ${!userSignature}

## Gate

- **Do not enable SEQ-1 in production until `demo-hosted:1:initial` (and ideally `:2`) is reworded** — routing
  non-attendees into an opener that assumes attendance would send incorrect outward-facing copy.
- Steps 3–5, the no-show, confirmation, reminder, and post-demo templates need **no** change.
