# v6 Email Copy Verification Tracker (MCP-Blind, Gated)

Date: 2026-06-25
Branch: `codex/v6-lifecycle-closeout`
Target org: Jurnii.io, `org20114906201`

This tracker captures the email-template verification items that the v6 closeout cannot complete via
the MCP connector. **True email-template copy and active/published status are NOT readable via MCP** —
there is no Email Templates GET tool, and `getEmailNotifications` returned only a single 'test' cadences
action (id 991103000001866043 -> template 991103000001488004). Every item below is therefore **PENDING**
until a UI / Deluge `zoho.crm.invokeConnector` readback (or a future Email Templates API) can confirm the
live copy. All such verifications, and any subsequent copy edits, are **gated** (outward-facing,
write-blind).

## Verification Items

| # | Item | Template / scope | Concern | Required readback | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Demo Hosted - Initial 1 attendance implication | `demo-hosted:1:initial` — id **991103000001476007** | Under the new SEQ-1 routing, missed/lost demos are routed INTO the Demo Hosted recovery cadence, so this opener will be sent to contacts who did NOT attend. The canonical EMAIL_MANIFEST copy implies attendance ('Thank you for making time for the demo'); an older DRAFT in V5_EMAIL_ARCHITECTURE_REVIEW.md (lines 655-664) ALSO implies attendance ('Now that you've had a chance to see how ${Organization.Organization Name} could work...') AND uses rejected merge syntax. Must confirm the LIVE body does not assume attendance for the recovery path. | UI / Deluge readback of live template 991103000001476007 body + subject | **PENDING** (MCP cannot read template copy) |
| 2 | No-show vs demo-hosted:1 single-opener decision (MTG-5) | `demo-confirmation:0:no-show` (id 991103000001476010) vs `demo-hosted:1:initial` (id 991103000001476007) | A single missed demo must not fire BOTH the one-off no-show email AND the demo-hosted:1 recovery opener. Product must decide which is the canonical single opener; copy of both must be confirmed consistent with that decision (no-show copy must NOT imply attendance; recovery opener copy must match the chosen path). | Product decision (MTG-5) + UI readback of both live bodies | **PENDING** (MCP cannot read template copy; decision unresolved) |
| 3 | Merge-syntax verification (all templates) | All 31 lifecycle templates + signature block | Only the `${!<Module API>.<Field API>}` form is accepted by Zoho. The architecture-review draft used REJECTED forms (`${Organization.Organization Name}`, `${Contacts.First_Name}` no-bang, `${Users.Website}`, `${User.First_Name}`). Must confirm the LIVE templates use only the verified bang form and that no template carries a rejected merge tag. | UI / Deluge readback of live template bodies (merge tags not exposed via MCP) | **PENDING** (MCP cannot read merge fields) |
| 4 | Folder-name check ('Marketing Consent') | Folder 991103000001471001 and the 8-folder set | EMAIL_MANIFEST/TEMPLATE_REGISTRY authority = 'Marketing Consent'; an architecture-review draft used 'Marketing Qualification'. MEMORY confirms canonical Stage value is 'Marketing Consent' (no rename). Must confirm the LIVE folder is named 'Marketing Consent' (and the other 7 folder names match the registry). | UI readback of live template-folder names (folders not exposed via getEmailNotifications) | **PENDING** (MCP cannot read folders) |

## Notes

- The only template ID confirmed live today is **991103000001488004 (Onboarding - Agreement
  Confirmed)**, surfaced because the single live notification action 'test' references it. Its subject/body
  were still not readable — only the action's `{name,id}` reference.
- The no-show template (991103000001476010) copy is doc-asserted to correctly avoid implying attendance
  ("didn't manage to connect"), and Proposal Preparation post-demo (991103000001484010) is doc-asserted to
  intentionally acknowledge attendance (proven path). These remain doc-asserted, not live-verified.
- Any correction to live template copy (item 1) or folder names (item 4) is a **gated action** — it is
  outward-facing and, because copy is not MCP-readable, would be applied blind. Verify via UI before any
  edit, and re-verify after.
- **Do not enable SEQ-1 in production** until item 1 is resolved: routing non-attendees into a
  demo-hosted:1 opener that assumes attendance would send incorrect outward-facing copy.
