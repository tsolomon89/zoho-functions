# 07 — Call-First Automation and Safeguards

## TLDR
> [!NOTE]
> This document describes the **Call-First** execution path, which is one of the supported sequence modes within the larger routing model (which also supports Email First, Meeting First, Task First, and Manual Review First).
> 
> In the Call-First route, each Stage starts with a Call so a sales representative checks the prospect before emails or follow-up sequences continue.

---

## The Basic Idea
The system is built around small, targeted field updates rather than a massive, sweeping auto-run mechanism. 

Instead of an update on any module triggering all workflows, specific updates on the right fields trigger the right workflow.

When a representative or event updates a field, the matching function decides the next step:

| Representative / System Updates | Workflow / Function Decides |
| :--- | :--- |
| **Ready for Conversion** (checked on Lead) | Whether a Lead becomes an Account, Contact, and Deal |
| **Stage** (updated on Deal) | Whether a new Stage sequence starts |
| **Call Outcome** (updated on Call) | Whether to send an email, create the next Call, move Stage, pause, or close the Deal |
| **Task Status / Task Outcome** (completed on Task) | Whether to resume sequence routing or update commercials status |
| **Demo Outcome** (updated on Deal) | Whether to move the demo Stage or send a demo follow-up |
| **Commercials Status** (updated on Deal) | Whether to move to Commercial Agreement, Onboarding, or Lost |
| **Email Event** (replied or bounced outbound email) | Whether to pause the sequence for review/repair or log passive engagement |
| **Follow-up Date Reached** (scheduled timeframe reached) | Whether scheduled routing resumes |

---

## Why Every Stage Starts With a Call
A Call is the human gate and the primary control point.

We do not immediately drop prospects into blind email sequences the moment a record moves to a new Stage. 

The Call Outcome tells the system what is safe to do next. It lets the representative confirm the prospect's situation before any automated follow-up is allowed to exit the CRM.

| Safeguard | Meaning |
| :--- | :--- |
| **Human check first** | A representative confirms the prospect is reachable and relevant before emails go out. |
| **No blind email sequences** | Emails only follow a Call Outcome, never a random, automated field update. |
| **Bad data catch** | Bad phone numbers or invalid emails pause the sequence and trigger cleanup tasks. |
| **Do-not-contact handling** | Automation is completely suppressed if the prospect opts out. |
| **Deferred handling** | Sequence automatically pauses and schedules a future resume date. |

---

## What The Rep Updates
When work is completed, the representative or system logs the action. The CRM then automatically flows to the next step:

| Work Completed | Field / Action Updated | Expected Result |
| :--- | :--- | :--- |
| **Lead reviewed** | *Ready for Conversion* checked | Lead Processor runs, converting Lead to Contact/Account/Deal |
| **Call completed** | *Call Outcome* updated | Next action is routed (email sent, next call, stage advance) |
| **Manual task completed** | *Task Status* set to Completed / *Task Outcome* set | Sequence resumes or logs the event |
| **Demo happened** | *Demo Outcome* updated | Demo logic runs (advances stage or creates draft tasks) |
| **Commercials sent/signed** | *Commercials Status* updated | Commercial logic runs (updates Stage and starts next sequence) |
| **Customer replied/bounced** | *Email Event* processed (automated) | Sequence pauses immediately for review/repair |

---

## What The System Does Next
Logging a Call Outcome is the single most important action a representative takes. When a sequence-managed Call gets an outcome, the system processes it using this map:

| Call Outcome | What actually happens in the system |
| :--- | :--- |
| **Positive** | Moves Deal to the next Stage, which triggers the sequence router to start Call 1 there. |
| **Neutral** | Sends the current Stage email and creates the next Call (up to Call 5). |
| **No Answer** | Sends the no-answer email and creates the next Call (up to Call 5). |
| **Negative** | Marks Deal State as `Lost`, Status as `Closed`, and halts further automation. |
| **Deferred** | Pauses the sequence until the *Next Follow-Up Date* logged on the Call. |
| **Bad Data** | Pauses the sequence and creates a manual *Data Repair Task*. |
| **Already Handled** | Logs the step; does not send any email and does not create a next Call. |
| **Not Relevant** | Pauses the sequence and creates a manual *Review Task*. |
| **Manual Only** | Suppresses all future automation by setting *Automation Suppressed* to True. |
| **Do Not Contact** | Suppresses all future automation by setting *Automation Suppressed* to True. |

*Note: If the representative logs "Neutral" or "No Answer" on Call 5, the system automatically transitions the Deal into the 7-email post-call follow-up chain, sending one email every 3 business days.*

---

## Safeguards Against Bad Automation
To keep the CRM pristine and prevent erratic behaviors, the system enforces these rules:
* **Automation Suppressed**: If the Deal has *Automation Suppressed* checked, all sequence routing exits immediately.
* **Missing Stage**: If a Deal is missing a *Stage*, the router stops and creates a *Manual Review Task* instead of guessing.
* **Paused / Manual Only / Suppressed / Deferred States**: The sequence router exits early and does not send emails or create calls while a Deal is in any of these states.
* **Stale Calls**: If a Call is completed for a Stage the Deal has already moved past, the system marks the Call stale (`Stale = Yes`) and ignores the outcome.
* **Stage Changes Supersede Old Sequences**: Changing the Deal's *Stage* automatically cancels any active Calls and Tasks for the previous Stage.
* **Replies Interruption**: A replied email event automatically pauses the sequence and creates a *Review Reply Task* for the representative.
* **Bounces Interruption**: A bounced email event pauses the sequence, creates a *Data Repair Task*, and flags the Contact as needing enrichment.
* **Internal Trigger Suppression**: All automated database updates use a special silent trigger parameter to prevent Zoho workflow rules from looping infinitely.
* **Duplicate Deals Silenced**: If multiple open Deals are created under one Account, the system closes newer ones as duplicate (`Lost / Duplicate`) and retains the oldest open Deal.
* **Lead Conversion Gate**: Leads never enter automated email sequences until they are converted by checking *Ready for Conversion*.

---

## What This Means In Practice

### Example 1: Representative logs "No Answer" on Call 1
* **System**: Sends the Stage-specific "No Answer" email template.
* **System**: Automatically creates the next Call (Call 2), scheduled for 2 business days out.
* **System**: Updates the Deal to wait for Call 2.

### Example 2: Representative logs "Positive" on Call 1
* **System**: Moves the Deal to the next *Stage* (e.g., from *Marketing Qualification* to *Demo Booking*).
* **System**: Automatically triggers the sequence router to cancel the previous Stage and create Call 1 for the new *Stage*.

### Example 3: Customer replies to a sequenced email
* **System**: The outbound email replied event handler pauses the sequence immediately.
* **System**: Automatically creates a *Review Reply Task* for the representative to read the reply and decide on the next step.

### Example 4: Commercials Status is updated to "Signed"
* **System**: Moves the Deal's *Stage* to `Onboarding` and sets Opportunity to `RTP`.
* **System**: Stays in the `Open` State (keeping it active for onboarding, retention, and renewal).
* **System**: Resets sequence status to `Not Started` and sends the Commercial Agreement Confirmation Email.
* **System**: Automatically starts Call 1 for the *Onboarding* Stage.

---

## What Still Needs Testing
Before these automations are turned on at scale, the following operational scenarios must be verified in Zoho CRM:
* **Stage Bootstrapping**: Confirming every single Stage successfully starts with Call 1.
* **Positive Outcome Progression**: Verifying a Positive Call Outcome correctly moves the Deal to the target next Stage.
* **Neutral / No Answer Routing**: Verifying a Neutral or No Answer outcome sends the correct template and schedules the next Call.
* **Post-Call Chain**: Verifying that a Neutral outcome on Call 5 starts the 7-email post-call chain.
* **Email Interruptions**: Testing outbound email replies and bounces to ensure the Deal pauses and the correct Review/Repair Tasks are created.
* **Stale Call Protection**: Ensuring a rep completing an old Call on a transitioned Deal is ignored.
* **Stage Override**: Testing manual Stage changes to verify that the old sequence is superseded and the new sequence bootstraps call-first.
* **Suppression**: Confirming that suppressed Deals never trigger sequence router actions.
* **Task Resumption**: Confirming that completing a Data Repair or Review Reply Task successfully restarts sequence routing.
* **Commercial Status Triggers**: Verifying that setting commercials to "Sent" or "Signed" triggers the correct Stage, State, Opportunity, and Call 1.
* **Lead Intake Gate**: Ensuring newly imported Leads do not enter sequences until *Ready for Conversion* is manually checked.

---

## Implementation Reference

Reviewed files:
- `.agents/context/activity-workflows/WORKFLOW_TRIGGER_MAP.md`
- `.agents/context/activity-workflows/WORKFLOW_CONFIGURATION_CHECKLIST.md`
- `v4/activity/sequenceRouter.deluge`
- `v4/activity/createStageCall.deluge`
- `v4/activity/handleCallOutcome.deluge`
- `v4/activity/handleTaskCompletion.deluge`
- `v4/activity/handleEmailEvent.deluge`
- `v4/activity/handleCommercialsStatusChange.deluge`
- `v4/activity/handleDemoOutcome.deluge`
- `v4/activity/supersedeOldSequence.deluge`
- `v4/processLead.deluge`
- `v4/processContact.deluge`
- `v4/processAccount.deluge`
- `v4/processDeal.deluge`
