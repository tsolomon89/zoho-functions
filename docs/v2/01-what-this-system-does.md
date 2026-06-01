# 01 — What This System Does

## TLDR
The CRM should not run from Leads. Leads are messy, temporary intake records. The system converts them immediately into the records that actually matter for Jurnii.io:
*   **Account** = the company
*   **Contact** = the person
*   **Deal** = the active sales motion
*   **Product** = what they are interested in

This keeps Jurnii.io's pipeline clean, prevents duplicate work, and runs outreach automatically.

Evidence: `spec.md`, `v4/processLead.deluge`

---

## Core Business Value

This system fixes common CRM problems automatically:

| Problem | What the system does | Why it matters to Jurnii.io |
| :--- | :--- | :--- |
| **Duplicate companies** | Finds or creates one Account per domain | Reps do not double-book or conflict on outreach |
| **Duplicate Deals** | Keeps exactly one active Deal per Account | Pipeline reports and forecasts are accurate |
| **Missed follow-up** | Creates calls and sends emails automatically | No prospect goes cold or gets forgotten |
| **Bad pipeline numbers** | Uses one Deal per Account instead of per Lead | The CEO sees real sales opportunities, not fluff |
| **Manual Deal values** | Adds Product catalog prices into the Deal Amount | Stops reps from guessing or typing wrong deal values |

---

## How It Behaves

*   **Leads are Intake Only**: Every Lead converts immediately. Missing information (like a phone number or website) never blocks conversion.
    *   *Evidence*: `v4/processLead.deluge`
*   **One Company = One Account**: The system checks domains and clean company names to reuse existing Accounts before making new ones.
    *   *Evidence*: `v4/processLead.deluge`
*   **Deals Own the Process**: Once converted, the active Deal drives the commercial relationship.
    *   *Evidence*: `v4/processDeal.deluge`
*   **Outreach is Call-Gated**: Sequences start with a call. Call outcomes recorded by reps decide the next automated action.
    *   *Evidence*: `v4/activity/handleCallOutcome.deluge`
