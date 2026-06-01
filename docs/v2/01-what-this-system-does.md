# 01 — What This System Does

## TLDR
The CRM should not run from Leads. Leads are messy, temporary intake records. The system converts them when they are marked ready for conversion into the records that actually matter for Jurnii.io:
*   **Account** = the company
*   **Contact** = the person
*   **Deal** = the active sales motion
*   **Product** = what they are interested in

This keeps Jurnii.io's pipeline clean, prevents duplicate work, and runs outreach automatically.

---

## Core Business Value

This system fixes common CRM problems automatically:

| Problem | What the system does | Why it matters to Jurnii.io |
| :--- | :--- | :--- |
| **Duplicate companies** | Finds or creates one Account per real company | Reps do not double-book or conflict on outreach |
| **Duplicate Deals** | Keeps exactly one active Deal per Account | Pipeline reports and forecasts are accurate |
| **Missed follow-up** | Creates Calls and sends emails automatically | No prospect goes cold or gets forgotten |
| **Bad pipeline numbers** | Uses one Deal per Account instead of per Lead | The CEO sees real sales opportunities, not fluff |
| **Manual Deal values** | Adds Product catalog prices into the Deal Amount | Stops reps from guessing or typing wrong deal values |

---

## How It Behaves

*   **Leads are Intake Only**: Leads convert when they are marked ready for conversion. The conversion is gated by standard fields (Ready for Conversion checked, Email set, etc.) but missing enrichment data never blocks it once the gate is passed.
*   **One Company = One Account**: The system uses domain, website, and cleaned company name to find the right Account before creating a new one.
*   **Deals Own the Process**: Once converted, the active Deal drives the commercial relationship.
*   **Outreach is Call-Gated**: Sequences start with a Call (in the `Calls` module). Call outcomes recorded by reps decide the next automated action. Tasks are used only for repair, review, enrichment, onboarding setup, and other manual work.

---

## Implementation reference

Relevant repo files:
- `v4/processLead.deluge`
- `v4/processDeal.deluge`
- `v4/activity/handleCallOutcome.deluge`
