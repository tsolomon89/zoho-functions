# 04 — Workflows and Cadences

## TLDR
The CRM automation separates timing from business logic:
*   **Zoho Workflow Rules** decide **when** something runs (Trigger layer).
*   **Deluge Functions** decide **what** actually happens (Logic layer).

Evidence: `.agents/context/activity-workflows/WORKFLOW_TRIGGER_MAP.md`, `v4/activity/sequenceRouter.deluge`

---

## Core Workflow Trigger Inventory

Ten core Zoho workflow rules decide when our Published Deluge functions execute:

| Workflow | Module | Trigger Event | Published Function | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **WF001** | `Leads` | Lead marked ready | `processLead` | Convert Lead immediately |
| **WF002** | `Deals` | Sequence not started | `sequenceRouter` | Create Call 1 and start sequence |
| **WF003** | `Deals` | Stage (`Stage1`) changed | `sequenceRouter` | Reset stage sequence; clear old tasks |
| **WF004** | `Deals` | Commercial status changed | `handleCommercialsStatusChange` | Move to `Commercials Sent` stage (FTP) |
| **WF005** | `Deals` | Demo outcome changed | `handleDemoOutcome` | Move to `Demo Attended` or schedule No Show |
| **WF006** | `Calls` | Call outcome logged | `handleCallOutcome` | Decide next action based on outcome |
| **WF007** | `Events` | Meeting / Demo updated | `handleMeetingEvent` | Set demo reminder dates and status |
| **WF008** | `Tasks` | Task completed | `handleTaskCompletion` | Evaluate manual work and resume sequence |
| **WF009** | `Emails` | Reply or Bounce detected | `handleEmailEvent` | Pause sequence; create review or repair task |
| **WF010** | `Deals` | Date / Time reached | `sequenceRouter` | Resume deferred action or fire next email |

*   *Evidence*: `.agents/context/activity-workflows/WORKFLOW_TRIGGER_MAP.md`

---

## The Sales Cadence Lifecycle

This simple path outlines how a prospect flows through a stage sequence:

```text
Stage starts
→ Call 1 created automatically (Sequence Status = Waiting on Call)
→ Rep logs Call Outcome
→ System evaluates outcome and chooses next action
→ Call/email cadence continues, pauses, or deactivates
```

---

## Call-Outcome Gate Rules

When a representative logs a call, their **Call Outcome** selection determines what happens next:

*   **Positive Outcome**: Advances Deal stage and Opportunity. Stops current sequence and bootstraps Call 1 of the new stage.
*   **Neutral Outcome**: Sends stage-specific email template and creates next Call Task (Call N+1).
*   **No Answer**: Sends no-answer email template and creates next Call Task (Call N+1).
*   **Negative Outcome**: Closes Deal as **Lost** and status as **Closed**. Halts all automation.
*   **Deferred**: Pauses sequence until Follow-Up Date is reached.
*   **Bad Data**: Pauses sequence and creates a **Data Repair Task** for the rep.
*   **Reply Intercepted**: Pauses sequence and creates a **Review Reply Task** for the rep.
*   **Bounce Intercepted**: Pauses sequence and creates a **Data Repair Task**.
*   **After 5 Call Attempts**: The system enters a **7-email chase chain** (sends an automated email every 3 days).
*   **After 7 Chase Emails**: Sequence is marked **Completed** and gracefully deactivates.

*   *Evidence*: `v4/activity/handleCallOutcome.deluge`, `v4/activity/handleEmailEvent.deluge`, `v4/activity/sequenceRouter.deluge`
