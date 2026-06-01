# 06 — Call Scripts and Email Templates

## TLDR
This document maps our standardized sales outreach library. It covers the call scripts and email templates that reps use and that the system sends automatically.

Evidence:
- `.agents/context/activity-workflows/calls`
- `.agents/context/activity-workflows/email_templates`

---

## Call Scripts

What it is:
A standardized collection of stage-specific call scripts and talk tracks. Every sales stage starts with a Call to ensure professional, value-focused outreach.

How it is used:
When a Deal enters a stage, the system automatically creates the Call record in the Calls module. The rep views the Call, reads the corresponding script/talk track, makes the call, and logs the Call Outcome.

Why it matters:
Sales reps do not have to guess what to say or when to follow up. It standardizes Jurnii's message, ensures reps gather consistent qualification data, and guides the automated sequence based on logged outcomes.

Evidence:
- `.agents/context/activity-workflows/calls/Demo Booking/Demo Booking Call 1.md`
- `v4/activity/createStageCall.deluge`

### Stage Call Attempts Inventory

Each stage has a dedicated set of call scripts. The system automatically steps through these attempts until contact is made or the stage is completed:

| Stage | Call Attempts | Purpose of Call Script |
| :--- | :---: | :--- |
| **Marketing Consent** | 5 | Introduce Jurnii, verify email, and gain marketing consent. |
| **Demo Booking** | 5 | Establish pain points, pitch Jurnii's value, and book the demo. |
| **Demo Booked** | 1 | Pre-demo check-in to confirm attendance and clarify goals. |
| **Demo Attended** | 3 | Gather feedback post-demo, qualify, and move to commercials. |
| **Commercials Sent** | 5 | Discuss proposal terms, handle objections, and secure signature. |
| **Commercials Signed** | 5 | Confirm receipt of signed terms and discuss next steps. |
| **Onboarding** | 5 | Coordinate technical setup, database sync, and kickoff meeting. |
| **Renewal** | 5 | Review account health, discuss expansion, and secure renewal. |

### Call Outcome Action Map

When a rep completes a call and logs a **Call Outcome** in the Zoho Calls module, the system triggers the following action:

| Call Outcome | What happens |
| :--- | :--- |
| **Positive** | Advances Deal stage and Opportunity. Stops current sequence and creates Call 1 of the new stage. |
| **Neutral** | Sends stage-specific email template and creates the next Call (Call N+1) after the delay. |
| **No Answer** | Sends no-answer email template and creates the next Call (Call N+1) after the delay. |
| **Negative** | Closes Deal as `Lost` and status as `Closed`. Halts all future automation. |
| **Deferred** | Pauses sequence until the specified Follow-Up Date is reached. |
| **Bad Data** | Pauses sequence and creates a manual **Data Repair Task** for the rep. |
| **Already Handled** | Pauses sequence. No email is sent, no next Call is created. |
| **Not Relevant** | Pauses sequence and creates a manual **Review Task** for the rep. |
| **Manual Only** | Pauses sequence and suppresses future automation. |
| **Do Not Contact** | Pauses sequence and suppresses future automation. |

Evidence:
- `v4/activity/handleCallOutcome.deluge`

---

## Email Templates

What it is:
A library of pre-written, highly-personalized follow-up emails that are automatically resolved and sent based on sales activities.

How it is used:
The system automatically selects the correct email template based on the current stage, the call attempt number, or a triggered event (like a meeting reminder or proposal delivery).

Why it matters:
Ensures timely, professional follow-up without manual rep effort. The email copy matches Jurnii's positioning and automatically chasers prospects who do not reply or answer.

Evidence:
- `.agents/context/activity-workflows/email_templates/Demo Booking/Demo Booking Email 1.md`
- `v4/activity/sequenceRouter.deluge`

### Email Template Groups and Triggers

These are the exact email templates that must be configured inside Zoho CRM. The template names in Zoho must match these names exactly for the automation to locate and send them:

| Template Group / Name | When Used | Trigger |
| :--- | :--- | :--- |
| **Stage Email N**<br>(e.g. `Demo Booking Email 1`) | After a Neutral call outcome on call attempt N | `handleCallOutcome` |
| **No Answer Email N**<br>(e.g. `Demo Booking Email 1`) | After a No Answer call outcome on call attempt N | `handleCallOutcome` |
| **Post-Call Email Chain 1–7**<br>(e.g. `Demo Booking Post-Call Email Chain 1`) | Scheduled chase sequence sent if all call attempts are exhausted | `sequenceRouter` (WF010) |
| **Demo Booked Confirmation Email** | Sent immediately when a demo meeting is scheduled | `handleMeetingEvent` (WF007) |
| **Demo Booked Reminder Email** | Sent 1 business day before the scheduled demo | `sequenceRouter` (WF010) |
| **Demo Booked No-Show Email** | Sent if the prospect fails to attend the demo | `handleDemoOutcome` (WF005) |
| **Demo Attended Post-Demo Email** | Sent immediately after a demo is completed | `handleDemoOutcome` (WF005) |
| **Commercials Sent Terms Email** | Sent when contract terms or proposals are delivered | `handleCommercialsStatusChange` (WF004) |
| **Commercials Signed Confirmation Email** | Sent immediately when commercials are signed | `handleCommercialsStatusChange` (WF004) |
| **Onboarding Kickoff Email** | Sent when the Deal moves into the Onboarding stage | `sequenceRouter` |

---

## Zoho UI and Sales Rep Experience

### What Needs Copying into Zoho UI
*   **Email Templates**: The exact text copy from `.agents/context/activity-workflows/email_templates/` must be copied into Zoho CRM's Email Templates setup page. The template names in Zoho **must match the folder and file names exactly** (e.g. `Demo Booking Email 1`).
*   **Call Scripts**: The talk tracks and objective details from `.agents/context/activity-workflows/calls/` should be placed into Zoho CRM as quick reference cards or stored in the Call script description field for reps.

### What the Sales Rep Actually Sees and Does
1.  **View Call**: The sales rep sees a new `Call` record created automatically in their queue under the `Calls` module (e.g., `Demo Booking Call 1`).
2.  **Read Script**: The script/talk track is visible directly in the description of the Call.
3.  **Log Outcome**: The rep calls the prospect, selects the appropriate `Call_Outcome` from the picklist, and clicks Save.
4.  **Hands-Free Follow-Up**: The system automatically runs the next step (sending the corresponding email template, updating dates, or scheduling the next call) without the rep needing to type or schedule anything manually.
