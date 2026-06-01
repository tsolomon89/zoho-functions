# 07 — Call-First Automation and Safeguards

## TLDR
The system is designed to be call-first. A Call is the human checkpoint before the CRM sends the next email, creates the next Call, moves the Deal forward, pauses the sequence, or closes the Deal.

The sales representative should not have to manually manage the whole sequence. Specific updates on the right fields trigger the right workflow. The rep updates the outcome of the thing they just did, and the workflow then routes the next action.

---

## Why Every Stage Starts With a Call

Every Stage starts with Call 1 because the system should not blindly drop people into automated emails. The Call is the gate. It confirms whether the prospect is a real person, interested, reachable, relevant, deferred, bad data, or should not be contacted. 

Only after the Call Outcome is logged does the system decide what to do next.

| Reason | Meaning |
| :--- | :--- |
| **Human check first** | A rep confirms what is happening before automation continues. |
| **Avoid bad sequences** | Prospects should not get irrelevant emails because a field changed. |
| **Better data** | Calls expose bad phone numbers, wrong contacts, deferrals, and do-not-contact cases. |
| **Cleaner pipeline** | Stage changes are based on explicit outcomes, not guesses. |
| **Safer automation** | Emails and follow-ups happen only after the right gate is passed. |

---

## The Rep Only Updates the Outcome

The rep should only need to update the field connected to the work they just completed. They do not need to manually create every next Call, email, task, or follow-up date.

| Rep action | Field they update | What the system does |
| :--- | :--- | :--- |
| **Lead is ready** | *Ready for Conversion* | Converts Lead into Account, Contact, and Deal automatically. |
| **Call completed** | *Call Outcome* | Sends email, creates next Call, advances Stage, pauses, or closes Deal. |
| **Demo happened** | *Demo Outcome* | Sends post-demo email, updates Stage, and creates next work. |
| **Commercials sent/signed** | *Commercials Status* | Moves Stage and starts the next sequence. |
| **Manual task completed** | *Task Outcome* or *Status* | Resumes sequence or updates commercial status. |
| **Customer replies** | *Email Event* (Incoming) | Pauses sequence and creates a review Task. |
| **Email bounces** | *Email Event* (Bounced) | Pauses sequence and creates a repair Task. |

---

## What Happens After Each Update

### Call Outcome Flow

When a Call Outcome is logged in the Calls module, the system routes the following action:

| Call Outcome | Next action |
| :--- | :--- |
| **Positive** | Move to the next Stage and start Call 1 there. |
| **Neutral** | Send Stage email and create the next Call (Call N+1) after the delay. |
| **No Answer** | Send no-answer email and create the next Call (Call N+1) after the delay. |
| **Negative** | Mark Deal `Lost` and Status `Closed`. Halts all automation. |
| **Deferred** | Pause sequence until specified follow-up date. |
| **Bad Data** | Pause sequence and create a manual **Data Repair Task**. |
| **Already Handled** | Log step as handled; no email sent and no next Call created. |
| **Not Relevant** | Pause sequence and create a manual **Review Task**. |
| **Manual Only** | Suppress automation and mark suppression reason. |
| **Do Not Contact** | Suppress automation and mark do-not-contact reason. |

### Task Completion Flow

When a rep completes a manual Task, the system processes it by Task Type:

| Task Type | What happens |
| :--- | :--- |
| **Data Repair** | Resumes the paused sequence after data fix is complete. |
| **Enrichment** | Resumes the paused sequence after contact enrichment. |
| **Review Reply** | Resumes the paused sequence after representative review. |
| **Onboarding Setup** | Resumes the paused sequence after setup checklists are marked. |
| **Send Commercials** | Automatically sets the Deal's *Commercials Status* to `Sent`. |
| **Draft Commercials** | Logs the completion only; rep must mark commercials ready/sent. |
| **Manual Review** | Logs the completion only. |
| **Suppression Review** | Logs the completion only. |

---

## Safeguards That Stop Bad Automation

The system has eight built-in safeguards to prevent erratic CRM behavior, bad email sends, or infinite loops:

1.  **Automation Suppressed**: If a Deal is suppressed (`Automation_Suppressed = true`), the sequence router exits immediately. Meaning: *Do not automate this record under any circumstance (e.g. existing clients, compliance, legal).*
2.  **Stage must exist**: If a Deal has no Stage, the system halts and creates a manual review Task instead of guessing. Meaning: *No Stage = no blind automation.*
3.  **Paused / Manual Only / Suppressed / Deferred statuses stop routing**: If the sequence status is paused, suppressed, or deferred, the router does not continue until the right date is reached or a manual task is cleared. Meaning: *Paused means paused.*
4.  **Stale Calls are ignored**: If a Call belongs to an old Stage, it is marked stale and ignored by the outcome handler. Meaning: *Old calls cannot accidentally move a Deal after a rep has already changed the Stage.*
5.  **Stage change supersedes old sequence**: When the Stage changes, old pending sequence Calls and Tasks are cancelled or deferred, and the new Stage starts fresh with Call 1. Meaning: *Only one active Stage sequence should exist at a time.*
6.  **Replies and bounces pause automation**: Incoming replies create a review Task and pause emails. Bounces create a data repair Task. Meaning: *The system will not keep emailing someone after they reply or if an email fails.*
7.  **Trigger suppression prevents workflow loops**: Internal database writes made by automation pass a suppression parameter to prevent Zoho from re-firing the same workflow rules. Meaning: *The system updates records without creating infinite workflow loops.*
8.  **Duplicate Deals are silenced**: Duplicate active Deals on the same Account are automatically closed as `Lost / Duplicate` so reps do not work conflicting records. Meaning: *One Account should have one active Deal.*

---

## Simple Examples

### Example 1: Rep logs Call Outcome = No Answer
*   **System**: Sends the stage-specific no-answer email, creates the next Call (Call 2), and keeps the sequence status waiting on Call.

### Example 2: Rep logs Call Outcome = Positive
*   **System**: Moves the Deal to the next Stage, updates Opportunity, clears the old sequence, and creates Call 1 for the new Stage.

### Example 3: Customer replies to an email
*   **System**: Pauses the automated sequence, creates a `Review Reply` Task for the rep, and waits for manual intervention.

### Example 4: Outbound email bounces
*   **System**: Pauses the automated sequence, creates a `Data Repair` Task for the rep, and marks the Contact as needing enrichment.

### Example 5: Commercials Status = Signed
*   **System**: Moves the Stage to `Commercials Signed`, updates Opportunity to `RTP`, keeps State `Open`, and starts Call 1 of the onboarding sequence.

---

## What Still Needs Testing

While this logic is built, it still needs end-to-end testing with real records to verify:
*   Every Stage successfully starts with Call 1.
*   A Positive Call Outcome moves to the next Stage.
*   Neutral / No Answer outcomes create the next Call and send the correct email.
*   Call 5 correctly starts the 7-email chase chain.
*   Incoming email replies and bounce events successfully pause sequence automation.
*   Stale Calls are ignored and do not move Deals backward.
*   Manual Stage changes successfully cancel/supersede the old sequence.
*   Suppressed Deals do not run or send emails.
*   Completed Tasks successfully resume sequences.
*   *Commercials Status* updates move the Deal and sequence correctly.
*   Imported records do not enter sequences before manual review.

---

## Implementation Reference

Main repository files mapping this logic:
- `.agents/context/activity-workflows/WORKFLOW_TRIGGER_MAP.md`
- `v4/activity/sequenceRouter.deluge`
- `v4/activity/createStageCall.deluge`
- `v4/activity/handleCallOutcome.deluge`
- `v4/activity/handleTaskCompletion.deluge`
- `v4/activity/handleEmailEvent.deluge`
- `v4/activity/handleCommercialsStatusChange.deluge`
- `v4/activity/handleDemoOutcome.deluge`
