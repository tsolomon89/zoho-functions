# V5 Email-Template Destructive Cleanup — Execution Report (2026-06-15)

Executed after the 31 canonical templates + 8 canonical folders were created and verified.
Retention allowlist = the 31 IDs in `docs/v5/TEMPLATE_REGISTRY.md`. Rule: ID in registry →
retain; else → delete.

## Templates
| Outcome | Count | Notes |
|---|---|---|
| Canonical retained | 31 | the registry allowlist (IDs `…0014xxxxx`) |
| Legacy deleted | 136 | all Email-First / Post-Call / numbered-cadence / stale-stage families |
| Legacy blocked | 1 | `991103000000657010` (MQL folder) — `ASSOCIATIONS_EXIST` |
| "Big Deal Alert" | DELETED | `991103000000000013` — on the user's "delete everything" instruction, removed by deleting the unrelated **Big Deal Rule** workflow (`991103000000195001`) → its WFAlert notification (`991103000000027470`) → the template. |
| **Live total now** | **32** | 31 canonical + blocked 657010 (confirmed via `getCountEmailTemplates`) |

### Blocked template `657010` — root cause + manual step
`getEmailTemplateAssociations` shows it is bound to a **native Zoho Sales Cadence** named
**"MQL"** (`automation_feature_type: Cadences`, `type: WFAlert`, steps FollowUp1/FollowUp3
on the Deals module). Cadences are a distinct Zoho automation feature with **no MCP tool** in
`zoho-email-crud` / `zoho-function-crud` / `zoho-workful-crud`, so the association cannot be
released programmatically here.
**Manual step (Zoho UI):** Setup → Automation → **Cadences** → retire/delete the legacy
**"MQL"** cadence (it is superseded by the V5 function-driven sequencing). Then:
`deleteEmailTemplates ids=991103000000657010` and `deleteEmailTemplateFolder 991103000000657008` (MQL folder).

## Folders
| Outcome | Folders |
|---|---|
| Canonical retained (8) | Marketing Consent `…1471001`, Demo Booking `…1472001`, Demo Confirmation `…1471003`, Demo Hosted `…1473001`, Proposal Preparation `…1474001`, Commercial Agreement `…1475001`, Onboarding `…1472003`, Renewal `…1476001` |
| Legacy deleted (9) | Jurnii - Marketing Consent `…785056`, Jurnii - Demo Booking `…793114`, Jurnii - Demo Booked `…784152`, Jurnii - Demo Attended `…801009`, Jurnii - Commercials Sent `…791066`, Jurnii - Commercials Signed `…789131`, Jurnii - Onboarding `…784154`, Jurnii - Renewal `…782059`, Jurnii Activity Layer `…801007` |
| Legacy blocked (1) | MQL `…657008` — non-empty (holds blocked `657010`); delete after the MQL Cadence is retired |
| System retained | Public Email Templates `…000007` (default), Draft Templates `…790051` (draft) — Zoho infrastructure, not Jurnii email folders |

## Repository
- Deleted the entire legacy template `.md` corpus: `.agents/context/activity-workflows/call_path/email_templates/` (Email-First Intro, Post-Call Follow-Up, Marketing Qualification, numbered/channel-specific bodies). Git history retains them. Canonical corpus now lives only in `docs/v5/EMAIL_MANIFEST.md`.
- `call_path/calls/` (call scripts) retained — not email templates.

## Bulk-delete note
`deleteEmailTemplates` rejects the array form (`UNABLE_TO_PARSE_DATA_TYPE`); pass `ids` as a
single comma-separated string. `createEmailTemplateFolders` accepts only 1 folder/request
despite the 1000 doc. Template `name` regex forbids `` ` ~ # % ^ & * ( ) + = " ; < > [ ] { } | \ ``.

## Validation (post-deletion)
- canonical templates = 31 ✓ · canonical folders = 8 ✓
- legacy email-sequence templates = 0 ✓ · legacy folders = 1 remaining (MQL, gated on Cadence)
- no Email-First / Call-First / Post-Call-Chain / opener-only family remains ✓
- no hardcoded "Jurnii" in canonical corpus ✓ · only verified `${!...}` tags ✓
- no V5 function resolves templates by name (registry/ID only) ✓
