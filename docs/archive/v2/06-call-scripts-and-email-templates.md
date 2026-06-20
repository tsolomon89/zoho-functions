# 06 — Call Scripts and Email Templates

## TLDR
> [!NOTE]
> This document details the outreach library (call scripts and email templates) used in Jurnii's sales sequences. In **v5**, sequence entry is task-gated and resolved via proposed routing, meaning sequences may start with a Call (Call First), an Email (Email First), a Meeting, a Task, or be routed manually.
> 
> This document maps Jurnii's standardized sales outreach library. It covers the call scripts and email templates that reps use and that the system sends automatically.

---

## Call Scripts

What it is:
A standardized collection of stage-specific call scripts and talk tracks. Under the Call-First route, a sales Stage starts with a Call to ensure professional, value-focused outreach.

How it is used:
When a Deal enters a Stage and Call-First routing is active, the system automatically creates the Call record in the Calls module. The rep views the Call, reads the corresponding script/talk track, makes the call, and logs the Call Outcome.

Why it matters:
Sales reps do not have to guess what to say or when to follow up. It standardizes Jurnii's message, ensures reps gather consistent qualification data, and guides the automated sequence based on logged outcomes.

### Stage Call Attempts Inventory

Each Stage has a dedicated set of call scripts. The system automatically steps through these attempts until contact is made or the Stage is completed:

| Stage | Call Attempts | Purpose of Call Script |
| :--- | :---: | :--- |
| **Marketing Qualification** | 5 | Introduce Jurnii, verify email, and gain marketing qualification details. |
| **Demo Booking** | 5 | Establish pain points, pitch Jurnii's value, and book the demo. |
| **Demo Confirmation** | 1 | Pre-demo check-in to confirm attendance and clarify goals. |
| **Demo Hosted** | 3 | Gather feedback post-demo, qualify, and progress to commercials. |
| **Commercial Agreement** | 5 | Discuss proposal terms, handle objections, and secure signature. |
| **Onboarding** | 5 | Coordinate technical setup, database sync, and kickoff meeting. |
| **Renewal** | 5 | Review account health, discuss expansion, and secure renewal. |

### Call Outcome Action Map

When a rep completes a call and logs a **Call Outcome** in the Zoho Calls module, the system triggers the following action:

| Call Outcome | What happens |
| :--- | :--- |
| **Positive** | Advances Deal Stage and Opportunity. Stops current sequence and creates Call 1 of the new Stage. |
| **Neutral** | Sends stage-specific email template and creates the next Call (Call N+1) after the delay. |
| **No Answer** | Sends no-answer email template and creates the next Call (Call N+1) after the delay. |
| **Negative** | Closes Deal as `Lost` and Status as `Closed`. Halts all future automation. |
| **Deferred** | Pauses sequence until the specified Follow-Up Date is reached. |
| **Bad Data** | Pauses sequence and creates a manual **Data Repair Task** for the rep. |
| **Already Handled** | Logs the step as handled. No email is sent and no next Call is created. |
| **Not Relevant** | Pauses sequence and creates a manual **Review Task** for the rep. |
| **Manual Only** | Pauses sequence and suppresses future automation. |
| **Do Not Contact** | Pauses sequence and suppresses future automation. |

---

## Email Templates

What it is:
A library of follow-up emails selected by Stage, attempt, or event.

How it is used:
The system automatically selects the correct email template based on the current Stage, the call attempt number, or a triggered event (like a meeting reminder or proposal delivery).

Why it matters:
Ensures timely, professional follow-up without manual rep effort. The email copy matches Jurnii's positioning and automatically chases prospects who do not reply or answer.

### Dynamic Operators / Merge Fields

The Zoho email templates should already use dynamic operators / merge fields to pass key information into the email body. These need to be tested. The test is not just "does the email send?" The test is:
*   **Template selection**: Does the right template get selected by the resolver?
*   **Target contact**: Does the correct primary Contact receive the message?
*   **Deal context**: Does the correct Deal context pass through?
*   **Personalization fields**: Do fields like `${Contacts.First_Name}` render correctly?
*   **Booking links**: Do custom calendar and demo booking links work?
*   **Commercial/Demo details**: Do specific demo schedules or terms appear correctly?
*   **Reply/bounce tracking**: Does tracking still connect back to the correct Deal?

### Email Template Groups and Triggers

These are the exact email templates that must be configured inside Zoho CRM. The template names in Zoho must match these names exactly for the automation to locate and send them:

| Template Group / Name | When Used | Trigger |
| :--- | :--- | :--- |
| **Stage Email N**<br>(e.g. `Demo Booking Email 1`) | After a Neutral call outcome on call attempt N | `handleCallOutcome` |
| **No Answer Email N**<br>(e.g. `Demo Booking Email 1`) | After a No Answer call outcome on call attempt N | `handleCallOutcome` |
| **Post-Call Email Chain 1–7**<br>(e.g. `Demo Booking Post-Call Email Chain 1`) | Scheduled chase sequence sent if all call attempts are exhausted | `sequenceRouter` (WF010) |
| **Demo Confirmation Email** | Sent immediately when a demo meeting is scheduled | `handleMeetingEvent` (WF007) |
| **Demo Confirmation Reminder Email** | Sent 1 business day before the scheduled demo | `sequenceRouter` (WF010) |
| **Demo Confirmation No-Show Email** | Sent if the prospect fails to attend the demo | `handleDemoOutcome` (WF005) |
| **Demo Hosted Post-Demo Email** | Sent immediately after a demo is completed | `handleDemoOutcome` (WF005) |
| **Commercial Agreement Terms Email** | Sent when contract terms or proposals are delivered | `handleCommercialsStatusChange` (WF004) |
| **Commercial Agreement Confirmation Email** | Sent immediately when commercials are signed | `handleCommercialsStatusChange` (WF004) |
| **Onboarding Kickoff Email** | Sent when the Deal moves into the Onboarding stage | `sequenceRouter` |

---

## Stage-by-Stage Content and Context Walkthrough

This section outlines Jurnii's active outreach library categorized by **Stage**. It explains the purpose of each Stage and the specific scripts/templates that run behind them.

### 1. Marketing Qualification Stage (Opportunity: MQL)
*   **Commercial Purpose**: Obtain marketing consent and complete required lead/contact/account data.
*   **Call Scripts Library**: 5 call attempts (`Marketing Qualification Call 1` to `5`). The script helps the rep introduce Jurnii, verify email, and gain marketing qualification.
*   **Triggered Follow-Up Emails**: Sent after a Neutral or No Answer call outcome:
    *   `Marketing Qualification Email 1` through `5`: Recap Jurnii's value proposition with a quick link to opt-in.
*   **Post-Call Chase Chain**: Sent if all 5 call attempts are exhausted without booking or gaining consent:
    *   `Marketing Qualification Post-Call Email Chain 1` through `7` (sends every 3 days).

### 2. Demo Booking Stage (Opportunity: SQL)
*   **Commercial Purpose**: Book the demo and capture product interest / use case information.
*   **Call Scripts Library**: 5 call attempts (`Demo Booking Call 1` to `5`). Guides the rep to uncover custom CRM/data challenges, pitch Jurnii's tailored 15-minute demo, and book a meeting slot.
*   **Triggered Follow-Up Emails**: Sent after a Neutral or No Answer call outcome:
    *   `Demo Booking Email 1` through `5`: Recap CRM pain points (data duplicates, manual checks) and links to the rep's calendar.
*   **Post-Call Chase Chain**: Sent if all 5 call attempts are exhausted without scheduling:
    *   `Demo Booking Post-Call Email Chain 1` through `7` (sends every 3 days with direct booking links).

### 3. Demo Confirmation Stage (Opportunity: SQL)
*   **Commercial Purpose**: Confirm the prospect will attend the already-booked demo.
*   **Call Scripts Library**: 1 pre-demo call script (`Demo Confirmation Call 1`). Rep confirms the meeting time, checks if other stakeholders will attend, and sets the agenda.
*   **Event-Based & Scheduled Emails**:
    *   `Demo Confirmation Email`: Sent automatically when the event is scheduled (`WF007`) to lock in the calendar slot.
    *   `Demo Confirmation Reminder Email`: Automated reminder sent 1 business day before the demo (`WF010`).
    *   `Demo Confirmation No-Show Email`: Sent if the prospect fails to attend the demo (`WF005`) to prompt rescheduling.
*   **Post-Call Chase Chain**: Sent if all call attempts are exhausted:
    *   `Demo Confirmation Post-Call Email Chain 1` through `7` (reschedule sequence).

### 4. Demo Hosted Stage (Opportunity: SQL)
*   **Commercial Purpose**: Host and complete the demo. If a demo is hosted but needs follow-up, this stage manages nurturing.
*   **Call Scripts Library**: 3 call attempts (`Demo Hosted Call 1` to `3`). Helps the rep follow up on demo impressions, handle pricing objections, and establish intent to sign.
*   **Triggered & Event-Based Emails**:
    *   `Demo Hosted Post-Demo Email`: Sent automatically after demo completion (`WF005`) to deliver a tailored follow-up deck and outline next steps.
    *   `Demo Hosted Email 1` through `3`: Standard follow-ups summarizing solutions discussed during the demo.
*   **Post-Call Chase Chain**: Sent if post-demo call attempts are exhausted:
    *   `Demo Hosted Post-Call Email Chain 1` through `7`.

### 5. Proposal Preparation Stage (Opportunity: FTP)
*   **Commercial Purpose**: Prepare and send the proposal/commercials after a viable or positive demo. This is a task-driven milestone for rep preparation before formal terms are sent.
*   **Trigger**: Demo hosted with viable next step advances stage to `Proposal Preparation` (FTP). When commercials are sent (Commercials Status = Sent), the Deal advances to `Commercial Agreement` (FTP).
*   **Tasks Generated**: Creates a manual **Draft Commercials Task** for the representative.

### 6. Commercial Agreement Stage (Opportunity: FTP)
*   **Commercial Purpose**: Agree the commercial terms and secure signature after proposal/commercials have been sent.
*   **Call Scripts Library**: 5 call attempts (`Commercial Agreement Call 1` to `5`). Guides the rep to review terms, handle pricing/contractual objections, and secure signature.
*   **Triggered & Event-Based Emails**:
    *   `Commercial Agreement Terms Email`: Sent automatically when proposal terms are delivered (`WF004`).
    *   `Commercial Agreement Email 1` through `5`: Standard follow-ups discussing pricing and contract details.
*   **Post-Call Chase Chain**: Sent if calls are exhausted:
    *   `Commercial Agreement Post-Call Email Chain 1` through `7` (sends every 3 days).

### 7. Onboarding Stage (Opportunity: RTP)
*   **Commercial Purpose**: Onboard the customer after commercial agreement/signature.
*   **Call Scripts Library**: 5 call attempts (`Onboarding Call 1` to `5`). Focuses on technical checkpoints, resolving setup questions, and tracking onboarding roadmap milestones.
*   **Triggered & Event-Based Emails**:
    *   `Commercial Agreement Confirmation Email`: Sent automatically when commercials are signed (`WF004`) to celebrate the partnership and outline kickoff steps.
    *   `Onboarding Kickoff Email`: Sent immediately when entering Onboarding (`sequenceRouter`) to deliver setup checklists.
    *   `Onboarding Email 1` through `5`: Technical checklists and checkpoint follow-ups.
*   **Post-Call Chase Chain**: Sent if calls are exhausted:
    *   `Onboarding Post-Call Email Chain 1` through `7`.

### 8. Renewal Stage (Opportunity: RTP)
*   **Commercial Purpose**: Manage renewal, retention, or expansion motion.
*   **Call Scripts Library**: 5 call attempts (`Renewal Call 1` to `5`). Guides the rep to check system usage, gather testimonials, and present renewal terms.
*   **Triggered Follow-Up Emails**: Sent after a Neutral or No Answer call outcome:
    *   `Renewal Email 1` through `5`: Summarize renewal options, key account metrics, and calendar links.
*   **Post-Call Chase Chain**: Sent if calls are exhausted:
    *   `Renewal Post-Call Email Chain 1` through `7`.

---

## What Needs Testing in Zoho

### Email Templates

The email templates should already be implemented in Zoho. The remaining work is to verify:
*   **Resolver matching**: Confirm that the exact template names match the automation resolver.
*   **Dynamic rendering**: Confirm that dynamic operators / merge fields render correctly.
*   **Trigger mapping**: Confirm the correct template sends for each Stage and trigger context.
*   **Target contact**: Confirm emails send to the correct primary Contact.
*   **Reply/bounce link**: Confirm reply and bounce events link back to the correct Deal.
*   **Schedule timing**: Confirm post-call chase emails send on the right schedule.

### Call Scripts

The call scripts exist in the repo content library. The remaining decision is where they should surface for reps:
*   As Zoho call descriptions.
*   As internal quick-reference cards.
*   As Notion/SOP content.
*   As sales enablement notes outside Zoho.

The current functions create Call records with Stage, attempt, purpose, and timing. They do not automatically inject Markdown script text into the Call description unless that has been separately implemented.

### What the Sales Rep Actually Sees and Does
1.  **View Call**: The sales rep sees a new `Call` record created automatically in their queue under the `Calls` module (e.g., `Demo Booking Call 1`).
2.  **Read Script**: If desired, the script text can be copied into the Call description setup, but the current function does not automatically inject Markdown script text into the Call record. The rep uses the matching script from the calls library or wherever it is surfaced in Zoho. The current Call record stores the stage, attempt, and purpose.
3.  **Log Outcome**: The rep calls the prospect, selects the appropriate `Call_Outcome` from the picklist, and clicks Save.
4.  **Hands-Free Follow-Up**: The system automatically runs the next step (sending the corresponding email template, updating dates, or scheduling the next Call) without the rep needing to type or schedule anything manually.

---

## Implementation reference

Relevant libraries and files:
- `.agents/context/activity-workflows/calls`
- `.agents/context/activity-workflows/email_templates`
- `v4/activity/createStageCall.deluge`
- `v4/activity/handleCallOutcome.deluge`
- `v4/activity/sequenceRouter.deluge`
