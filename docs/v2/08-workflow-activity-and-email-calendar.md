# 08 — Workflow Activity and Email Calendar

## TLDR
The system is built on a **relative workflow calendar**. 

Unlike a rigid date calendar, this timeline is dynamic. It moves based on when a sales representative completes an activity, when a customer reacts, or when key commercial events occur.

Every Stage in the customer lifecycle begins with a sequence bootstrap action matching the Stage's Action Mode (e.g. Call First, Email First, Meeting First, Task First, or Manual Review First).

For Call First sequences, the system pauses and waits for the representative to log a **Call Outcome** to determine downstream actions:
* Sends an automated follow-up email.
* Schedules the next Call in the sequence.
* Advances the Deal to the next Stage in the pipeline.
* Pauses the sequence for data cleanup or manual review.
* Commences the intensive **7-Email Chase Chain**.
* Closes or suppresses the Deal completely.

---

## How To Read This Calendar
Understanding the timing and triggers is simple when using these core concepts:

| Term / Field | Zoho Field / Module Name | Meaning in the Workflow |
| :--- | :--- | :--- |
| **Day 0** | *Stage / Stage1* updated | The day a brand new Stage sequence starts on the Deal. |
| **Business Days** | System Date Calculation | Used for scheduling next Call due dates (excludes Saturdays and Sundays). |
| **Calendar Days** | System Date Calculation | Used for spacing out the automated Post-Call Email Chain (includes weekends). |
| **Call Outcome** | *Call Outcome* | The representative’s logged result in the *Calls* module that drives the next action. |
| **Sequence Status** | *Sequence Status* | Where the Deal currently sits in the automation lifecycle (e.g., *Waiting on Call*, *Paused*). |
| **Next Action Due Date** | *Next Action Due Date* | The exact scheduled date and time used by the date-based follow-up router. |

---

## Main Stage Sequence Calendar
When a Deal enters a Stage configured as **Call First** (or resolves to it), the sequence progresses as follows. 

*Note: Automated emails and next Calls are never sent blindly on fixed dates. They are chained directly to when the representative logs a Neutral or No Answer outcome on the current Call.*

| Relative Timing | Activity / Action | System Behavior | Triggered By |
| :--- | :--- | :--- | :--- |
| **Stage Starts (Day 0)** | **Call 1 Created** | Call 1 is created immediately, due today. | `sequenceRouter` |
| **When Call 1 logged** | **Email 1 Sent + Call 2 Created** | Stage Email 1 is sent; Call 2 is scheduled +2 business days out. | `handleCallOutcome` |
| **+2 Business Days** | **Call 2 Due** | Call 2 appears in the rep's queue. | `createStageCall` |
| **When Call 2 logged** | **Email 2 Sent + Call 3 Created** | Stage Email 2 is sent; Call 3 is scheduled +2 business days out. | `handleCallOutcome` |
| **+2 Business Days** | **Call 3 Due** | Call 3 appears in the rep's queue. | `createStageCall` |
| **When Call 3 logged** | **Email 3 Sent + Call 4 Created** | Stage Email 3 is sent; Call 4 is scheduled +2 business days out. | `handleCallOutcome` |
| **+2 Business Days** | **Call 4 Due** | Call 4 appears in the rep's queue. | `createStageCall` |
| **When Call 4 logged** | **Email 4 Sent + Call 5 Created** | Stage Email 4 is sent; Call 5 is scheduled +2 business days out. | `handleCallOutcome` |
| **+2 Business Days** | **Call 5 Due** | Call 5 appears in the rep's queue. | `createStageCall` |
| **When Call 5 logged** | **Email 5 Sent + Chase Scheduled** | Stage Email 5 is sent; Post-Call Chase Chain is queued to start in +2 business days. | `handleCallOutcome` |
| **+2 Business Days** | **Post-Call Chain Starts** | Post-Call Chain Email 1 is sent automatically. | `sequenceRouter` |

---

## Stage-Specific Call Attempt Table
Each Stage has dedicated Call scripts tailored to its commercial goal. 

| Zoho Deal Stage Name | Call Scripts Available | Call Script Filename Pattern | Core Call Purpose |
| :--- | :---: | :--- | :--- |
| **Marketing Qualification** | 5 | `Marketing Qualification Call 1-5.md` | Obtain missing qualification and contact data |
| **Demo Booking** | 5 | `Demo Booking Call 1-5.md` | Sell and secure the demo booking |
| **Demo Confirmation** | 1 | `Demo Confirmation Call 1.md` | Protect attendance and confirm meeting agenda |
| **Demo Hosted** | 3 | `Demo Hosted Call 1-3.md` | Gather outstanding client details needed for commercial terms |
| **Commercial Agreement** | 5 | `Commercial Agreement Call 1-5.md` | Prompt discussion, handle objections, and secure signature |
| **Onboarding** | 5 | `Onboarding Call 1-5.md` | Ensure kickoff completion and setup checklists |
| **Renewal** | 5 | `Renewal Call 1-5.md` | Initiate renewal discussions and expansion value |

---

## Call Outcome Calendar
When a representative logs a *Call Outcome* on a sequence-managed Call, the system acts immediately to determine the next step:

| Representative Logs | System Actions | Next Scheduled Step | Sequence Status |
| :--- | :--- | :--- | :--- |
| **Positive** | Advances the Deal to the next Stage in the pipeline. | The new Stage sequence bootstraps based on its action mode. | `Waiting on Call` or `Waiting on Internal Task` (New Stage) |
| **Neutral** | Sends Stage Email N (matching the current attempt). | Schedules next Call (Call N+1) due in +2 business days (if N < 5). | `Waiting on Call` |
| **No Answer** | Sends Stage Email N (matching the current attempt). | Schedules next Call (Call N+1) due in +2 business days (if N < 5). | `Waiting on Call` |
| **Neutral / No Answer (Call 5)** | Sends Stage Email 5. | Schedules Post-Call Chase Chain Step 1 in +2 business days. | `Waiting on Email Trigger` |
| **Negative** | Marks Deal State as `Lost` and Status as `Closed`. | All automation stops. | `Completed` |
| **Deferred** | Pauses sequence routing. | Next follow-up is scheduled at the Call's *Next Follow-Up Date*. | `Deferred` |
| **Bad Data** | Pauses the sequence. | Automatically creates a manual *Data Repair Task*. | `Paused` |
| **Already Handled** | Logs the call as handled. | None. No email is sent and no next Call is created. | `Waiting on Call` |
| **Not Relevant** | Pauses the sequence. | Automatically creates a manual *Review Task*. | `Paused` |
| **Manual Only** | Exits the router and checks *Automation Suppressed*. | None. Automation is permanently disabled. | `Manual Only` |
| **Do Not Contact** | Exits the router and checks *Automation Suppressed*. | None. Automation is permanently disabled. | `Suppressed` |

---

## Post-Call 7-Email Chase Calendar
If a prospect does not answer any of the 5 Call attempts, the system takes over. 

It enters the **Post-Call Chase Chain** and sends a series of value-led emails automatically. 

* *Call 5 outcome = No Answer / Neutral* kicks off the sequence.
* Step 1 starts in **+2 business days**.
* Steps 2 through 7 are spaced exactly **+3 calendar days** apart.
* If a customer replies or bounces at any point, the chase chain is terminated instantly.

| Timing / Step | Email Sent | Trigger / Context | Next Scheduled Action |
| :--- | :--- | :--- | :--- |
| **+2 Business Days (from Call 5)** | `{Stage} Post-Call Email Chain 1` | `post_call_chain` | Next email scheduled in +3 calendar days. |
| **+3 Calendar Days** | `{Stage} Post-Call Email Chain 2` | `post_call_chain` | Next email scheduled in +3 calendar days. |
| **+3 Calendar Days** | `{Stage} Post-Call Email Chain 3` | `post_call_chain` | Next email scheduled in +3 calendar days. |
| **+3 Calendar Days** | `{Stage} Post-Call Email Chain 4` | `post_call_chain` | Next email scheduled in +3 calendar days. |
| **+3 Calendar Days** | `{Stage} Post-Call Email Chain 5` | `post_call_chain` | Next email scheduled in +3 calendar days. |
| **+3 Calendar Days** | `{Stage} Post-Call Email Chain 6` | `post_call_chain` | Next email scheduled in +3 calendar days. |
| **+3 Calendar Days** | `{Stage} Post-Call Email Chain 7` | `post_call_chain` | Sequence marks `Completed`. The follow-up date clears. |

---

## Template Naming Table
To prevent erratic templates, the email resolver maps triggers to specific templates in the Zoho CRM library:

| Trigger Context / Action | System Resolves This Template Name | Target Audience Goal |
| :--- | :--- | :--- |
| **Call Outcome (1-5)** | `{Stage} Email {Attempt}` | Value-led follow-up after a failed call |
| **Post-Call Chase (1-7)** | `{Stage} Post-Call Email Chain {Step}` | Spaced nurture follow-up for unresponsive leads |
| **Demo Booked (Event Created)** | `Demo Confirmation Email` | Agenda details and calendar invite confirmation |
| **Demo 1-Day Reminder** | `Demo Confirmation Reminder Email` | Protect attendance (sent 1 business day before at 9:00 AM) |
| **Demo No-Show logged** | `Demo Confirmation No-Show Email` | Re-engage and recover the booking |
| **Demo Completed Qualified** | `Demo Hosted Post-Demo Email` | Confirm demo value and highlight commercials preparation |
| **Commercials Sent** | `Commercial Agreement Terms Email` | Share commercial terms and contract link |
| **Commercials Signed** | `Commercial Agreement Confirmation Email` | Confirm signature and kickoff next steps |
| **Onboarding Started** | `Onboarding Kickoff Email` | Share kickoff steps and first setup requirements |

---

## Demo / Meeting Calendar
Meetings (logged as *Events* in Zoho) directly govern the Demo pipeline. The timing rules are:

| Trigger Event | Immediate System Action | Scheduled System Action | Email / Template Used |
| :--- | :--- | :--- | :--- |
| **Meeting Scheduled** (Meeting Type = Demo) | Mirrors details to Deal (*Demo_Status = Scheduled* and copy dates). | Schedules a reminder 1 business day before the demo at 9:00 AM. | `Demo Confirmation Email` |
| **Demo Reminder Time Reached** | Sends the protect-attendance reminder. | None. | `Demo Confirmation Reminder Email` |
| **Demo Attended (Qualified)** | Updates Deal Stage to `Proposal Preparation` and sets Opportunity to `FTP`. | Creates a manual **Draft Commercials Task** for the rep. | `Demo Hosted Post-Demo Email` |
| **Demo Completed (No-Show)** | Updates Deal to *Demo_Status = No Show*. | Automatically recreates a recovery Call at the `Demo Confirmation` Stage. | `Demo Confirmation No-Show Email` |
| **Demo Cancelled** | Updates Deal *Demo_Status = Cancelled*. | Automatically recreates a recovery Call at the `Demo Booking` Stage. | None |
| **Demo Rescheduled** | Updates Deal *Demo_Status = Rescheduled*. | Recomputes the new 1-day reminder date and time. | None |

---

## Commercials Calendar
The commercials workflow governs the FTP (First Time Purchase) and RTP (Retention Purchase) commercial motions.

| Commercials Status | Immediate Pipeline Action | Sent Email | Next Sequence Impact |
| :--- | :--- | :--- | :--- |
| **Sent** | Stage becomes `Commercial Agreement`, Opportunity becomes `FTP`, stamps sent timestamp. | `Commercial Agreement Terms Email` | Resets sequence to `Not Started` to trigger Commercial Agreement Call 1. |
| **Discussed** | Stamps discussed timestamp. | None. | None (No Stage move). |
| **Intent to Sign** | Checks Deal *Intent to Sign* flag. | None. | None (No Stage move). |
| **Signed** | Stage becomes `Onboarding`, Opportunity becomes `RTP`, State stays `Open`. | `Commercial Agreement Confirmation Email` | Resets sequence to `Not Started` to trigger Onboarding Call 1. |
| **Deferred** | Pauses sequence routing. | None. | Pauses until the *Next Commercial Follow-Up Date*. |
| **Rejected** | Marks Deal State as `Lost` and Status as `Closed`. | None. | Halts all future automation. |

---

## Email Event Calendar
Outgoing email events are processed automatically by the system to safeguard communication and prevent spamming:

| Customer Event | Workflow Rule | Immediate Effect | Next Manual Step |
| :--- | :--- | :--- | :--- |
| **Customer Replies** | WF009a (Replied) | Pauses sequence (*Sequence_Status = Paused*) to prevent automated replies. | Automatically creates a **Review Reply Task** for the rep. |
| **Email Bounces** | WF009b (Bounced) | Pauses sequence (*Sequence_Status = Paused*) and flags Contact as *Needs Enrichment*. | Automatically creates a **Data Repair Task** for the rep. |
| **No Reply Received** | WF009c (Unreplied) | Logged in history only. | Regular sequence continues to drive follow-ups. |
| **Email Opened (No Reply)**| WF009d (Opened) | Logged in history only. | Regular sequence continues. |
| **Email Link Clicked** | WF009e (Clicked) | Logged in history only. | Regular sequence continues. |

---

## Task Completion Calendar
When a representative completes a manual Task, the sequence is automatically evaluated for resumption:

| Completed Task Type | When Representative Completes It | System Action |
| :--- | :--- | :--- |
| **Data Repair** | Mark Task as Completed | Lifts the pause state. Sets sequence to `Not Started` and resumes routing. |
| **Enrichment** | Mark Task as Completed | Re-resolves proposed route with Call-First fallback, sets Sequence_Status to `Not Started` and resumes routing. |
| **Review Reply** | Mark Task as Completed | Resumes sequence routing. |
| **Onboarding Setup** | Mark Task as Completed | Sets sequence status to `Completed` (terminating next-action loops). |
| **Send Commercials** | Mark Task as Completed | Automatically bumps Deal *Commercials_Status* to `Sent` (triggering commercial terms). |
| **Draft Commercials**| Mark Task as Completed | Logged. No auto-advance. Rep must explicitly send the terms. |
| **Manual Review** | Mark Task as Completed | Logged. |
| **Suppression Review**| Mark Task as Completed | Logged. |

---

## Full Example Timeline
This relative timeline demonstrates a scenario where a prospect goes through the entire Stage sequence and Post-Call Chase without answering:

* **Step 1 (Day 0)**: Deal moves to `Demo Booking`. If sequence mode resolves to Call First, the system immediately creates **Demo Booking Call 1** (or a Sequence Activation Task if it resolved to Manual Review First).
* **Step 2 (Day 1)**: Rep dials, gets no answer, and logs Call Outcome = **No Answer**. System immediately sends **Demo Booking Email 1** and schedules **Demo Booking Call 2** for 2 business days out.
* **Step 3 (Day 3)**: **Demo Booking Call 2** becomes due. Rep dials, gets no answer, and logs Call Outcome = **No Answer**. System sends **Demo Booking Email 2** and schedules **Demo Booking Call 3** for 2 business days out.
* **Step 4 (Day 5)**: **Demo Booking Call 3** becomes due. Rep logs **No Answer**. System sends **Demo Booking Email 3** and schedules **Demo Booking Call 4**.
* **Step 5 (Day 7)**: **Demo Booking Call 4** becomes due. Rep logs **No Answer**. System sends **Demo Booking Email 4** and schedules **Demo Booking Call 5**.
* **Step 6 (Day 9)**: **Demo Booking Call 5** becomes due. Rep logs **No Answer**. System sends **Demo Booking Email 5** and queues the Post-Call Chase Chain.
* **Step 7 (Day 11)**: **+2 business days** pass. System automatically sends **Demo Booking Post-Call Email Chain 1**.
* **Step 8 (Day 14)**: **+3 calendar days** pass. System automatically sends **Demo Booking Post-Call Email Chain 2**.
* **Step 9 (Day 17)**: **+3 calendar days** pass. System automatically sends **Demo Booking Post-Call Email Chain 3**.
* **Step 10 (Day 20)**: **+3 calendar days** pass. System automatically sends **Demo Booking Post-Call Email Chain 4**.
* **Step 11 (Day 23)**: **+3 calendar days** pass. System automatically sends **Demo Booking Post-Call Email Chain 5**.
* **Step 12 (Day 26)**: **+3 calendar days** pass. System automatically sends **Demo Booking Post-Call Email Chain 6**.
* **Step 13 (Day 29)**: **+3 calendar days** pass. System automatically sends **Demo Booking Post-Call Email Chain 7**.
* **Step 14 (Day 29)**: The sequence marks `Completed`. The Deal waits for manual reactivation.

---

## What Still Needs Testing
The relative calendar logic must be validated against the following tests to ensure complete precision:
* **Stage Bootstrapping**: Confirming that all Stage changes bootstrap the correct action mode.
* **Call Due-Date Offsets**: Verifying that Call 2–5 and initial chase-chain start offsets skip weekends (using business days).
* **Call-Email Matching**: Ensuring Call N outcomes send the exact template `{Stage} Email N`.
* **Chase Chain Hand-off**: Verifying that Call 5 outcomes correctly transition to the chase chain.
* **Chase Chain Spacing**: Confirming that Post-Call Emails 2-7 are spaced exactly 3 calendar days apart.
* **Reminder Accuracy**: Testing that Demo Reminders send exactly 1 business day before the demo at 9:00 AM.
* **Bounce / Reply Pauses**: Sending replies and bounces to verify the Deal's *Sequence Status* pauses and the correct Tasks are created.
* **Task Complete Triggers**: Confirming that completing a Data Repair Task resumes sequence routing.
* **Import Gate Checks**: Ensuring newly imported Leads do not enter the sequence until converted.

---

## Implementation Reference

Reviewed files:
- `.agents/context/activity-workflows/WORKFLOW_TRIGGER_MAP.md`
- `.agents/context/activity-workflows/WORKFLOW_CONFIGURATION_CHECKLIST.md`
- `.agents/context/activity-workflows/TEMPLATE_NAMING_MATRIX.md`
- `v5/activity/sequenceRouter.deluge`
- `v5/activity/createStageCall.deluge`
- `v5/activity/handleCallOutcome.deluge`
- `v5/activity/handleTaskCompletion.deluge`
- `v5/activity/handleMeetingEvent.deluge`
- `v5/activity/handleDemoOutcome.deluge`
- `v5/activity/handleCommercialsStatusChange.deluge`
- `v5/activity/handleEmailEvent.deluge`
- `v5/activity/sendSequencedEmail.deluge`
- `v5/activity/_util_resolveTemplate.deluge`
- `v5/activity/_util_calculateBusinessDate.deluge`
