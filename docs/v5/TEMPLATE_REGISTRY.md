# V5 Template Registry — canonical key → live Zoho template ID

Generated after Phase 3 creation (2026-06-15). 31 templates, 8 folders, module Contacts
(`991103000000000047`). Merge syntax verified = `${!<Module API>.<Field API>}`. This map is
the single source for the inline registry block in `sendSequencedEmail` (send by ID).

## Folder IDs
| Folder | ID |
|---|---|
| Marketing Consent | 991103000001471001 |
| Demo Booking | 991103000001472001 |
| Demo Confirmation | 991103000001471003 |
| Demo Hosted | 991103000001473001 |
| Proposal Preparation | 991103000001474001 |
| Commercial Agreement | 991103000001475001 |
| Onboarding | 991103000001472003 |
| Renewal | 991103000001476001 |

## Template IDs (key → id)
| canonical_key | template_name | id |
|---|---|---|
| marketing-consent:1:initial | Marketing Consent - Initial 1 | 991103000001478002 |
| marketing-consent:2:follow-up | Marketing Consent - Follow-up 2 | 991103000001467002 |
| marketing-consent:3:follow-up | Marketing Consent - Follow-up 3 | 991103000001484001 |
| marketing-consent:4:follow-up | Marketing Consent - Follow-up 4 | 991103000001474007 |
| marketing-consent:5:final | Marketing Consent - Final 5 | 991103000001485001 |
| demo-booking:1:initial | Demo Booking - Initial 1 | 991103000001476004 |
| demo-booking:2:follow-up | Demo Booking - Follow-up 2 | 991103000001478005 |
| demo-booking:3:follow-up | Demo Booking - Follow-up 3 | 991103000001486001 |
| demo-booking:4:follow-up | Demo Booking - Follow-up 4 | 991103000001487001 |
| demo-booking:5:final | Demo Booking - Final 5 | 991103000001478008 |
| demo-hosted:1:initial | Demo Hosted - Initial 1 | 991103000001476007 |
| demo-hosted:2:follow-up | Demo Hosted - Follow-up 2 | 991103000001470002 |
| demo-hosted:3:follow-up | Demo Hosted - Follow-up 3 | 991103000001477003 |
| demo-hosted:4:follow-up | Demo Hosted - Follow-up 4 | 991103000001471007 |
| demo-hosted:5:final | Demo Hosted - Final 5 | 991103000001488001 |
| commercial-agreement:1:initial | Commercial Agreement - Initial 1 | 991103000001480002 |
| commercial-agreement:2:follow-up | Commercial Agreement - Follow-up 2 | 991103000001469004 |
| commercial-agreement:3:follow-up | Commercial Agreement - Follow-up 3 | 991103000001486004 |
| commercial-agreement:4:follow-up | Commercial Agreement - Follow-up 4 | 991103000001483002 |
| commercial-agreement:5:final | Commercial Agreement - Final 5 | 991103000001480005 |
| renewal:1:initial | Renewal - Initial 1 | 991103000001486007 |
| renewal:2:follow-up | Renewal - Follow-up 2 | 991103000001489001 |
| renewal:3:follow-up | Renewal - Follow-up 3 | 991103000001484004 |
| renewal:4:follow-up | Renewal - Follow-up 4 | 991103000001486010 |
| renewal:5:final | Renewal - Final 5 | 991103000001484007 |
| demo-confirmation:0:confirmation | Demo Confirmation - Confirmation | 991103000001474010 |
| demo-confirmation:0:reminder | Demo Confirmation - Reminder | 991103000001487004 |
| demo-confirmation:0:no-show | Demo Confirmation - No-Show | 991103000001476010 |
| proposal-preparation:0:post-demo | Proposal Preparation - Post-Demo | 991103000001484010 |
| commercial-agreement:0:proposal-sent | Commercial Agreement - Proposal and Terms | 991103000001475003 |
| onboarding:0:signed-confirmation | Onboarding - Agreement Confirmed | 991103000001488004 |

## Deluge registry block (inline into sendSequencedEmail)
```deluge
// === V5 TEMPLATE REGISTRY (generated 2026-06-15) — canonical key -> Zoho template id ===
templateRegistry = Map();
templateRegistry.put("marketing-consent:1:initial", "991103000001478002");
templateRegistry.put("marketing-consent:2:follow-up", "991103000001467002");
templateRegistry.put("marketing-consent:3:follow-up", "991103000001484001");
templateRegistry.put("marketing-consent:4:follow-up", "991103000001474007");
templateRegistry.put("marketing-consent:5:final", "991103000001485001");
templateRegistry.put("demo-booking:1:initial", "991103000001476004");
templateRegistry.put("demo-booking:2:follow-up", "991103000001478005");
templateRegistry.put("demo-booking:3:follow-up", "991103000001486001");
templateRegistry.put("demo-booking:4:follow-up", "991103000001487001");
templateRegistry.put("demo-booking:5:final", "991103000001478008");
templateRegistry.put("demo-hosted:1:initial", "991103000001476007");
templateRegistry.put("demo-hosted:2:follow-up", "991103000001470002");
templateRegistry.put("demo-hosted:3:follow-up", "991103000001477003");
templateRegistry.put("demo-hosted:4:follow-up", "991103000001471007");
templateRegistry.put("demo-hosted:5:final", "991103000001488001");
templateRegistry.put("commercial-agreement:1:initial", "991103000001480002");
templateRegistry.put("commercial-agreement:2:follow-up", "991103000001469004");
templateRegistry.put("commercial-agreement:3:follow-up", "991103000001486004");
templateRegistry.put("commercial-agreement:4:follow-up", "991103000001483002");
templateRegistry.put("commercial-agreement:5:final", "991103000001480005");
templateRegistry.put("renewal:1:initial", "991103000001486007");
templateRegistry.put("renewal:2:follow-up", "991103000001489001");
templateRegistry.put("renewal:3:follow-up", "991103000001484004");
templateRegistry.put("renewal:4:follow-up", "991103000001486010");
templateRegistry.put("renewal:5:final", "991103000001484007");
templateRegistry.put("demo-confirmation:0:confirmation", "991103000001474010");
templateRegistry.put("demo-confirmation:0:reminder", "991103000001487004");
templateRegistry.put("demo-confirmation:0:no-show", "991103000001476010");
templateRegistry.put("proposal-preparation:0:post-demo", "991103000001484010");
templateRegistry.put("commercial-agreement:0:proposal-sent", "991103000001475003");
templateRegistry.put("onboarding:0:signed-confirmation", "991103000001488004");
```

## Resolver kind → canonical key mapping (for the §12 code change)
| resolver emit | canonical key |
|---|---|
| `opener` (drop) → `:1:initial` | `<stage>:1:initial` |
| `cadence` step n (n=1 initial, 2-4 follow-up, 5 final) | `<stage>:<n>:<kind>` |
| `postcall` | `<stage>:5:final` |
| `demo_confirmation` | `demo-confirmation:0:confirmation` |
| `demo_reminder` | `demo-confirmation:0:reminder` |
| `demo_no_show` | `demo-confirmation:0:no-show` |
| `demo_post_demo` | `proposal-preparation:0:post-demo` |
| `commercials_terms` | `commercial-agreement:0:proposal-sent` |
| `commercials_signed_confirmation` | `onboarding:0:signed-confirmation` |
| `onboarding_kickoff` (dead — remove) | — none — |

stage-slug map: Marketing Consent→`marketing-consent`, Demo Booking→`demo-booking`,
Demo Hosted→`demo-hosted`, Commercial Agreement→`commercial-agreement`, Renewal→`renewal`.
