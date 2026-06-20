# 05 — Testing, Imports, and Open Items

## TLDR
The core system is built. The remaining work is testing and controlled rollout. 

The biggest risk is not whether the custom functions exist. The biggest risk is whether imports, workflows, emails, calls, and sequence logic behave correctly together with real CRM data. 

This doc explains what still needs to be tested before the system can be trusted with live pipeline operations.

---

## What Is Built vs What Still Needs Testing

The core Zoho Deluge functions have been built and partly tested through dry runs and the API connection. However, we must verify the system end-to-end under real conditions before launch.

| Area | Current Position | What Needs Testing |
| :--- | :--- | :--- |
| **Core Deluge functions** | Built and partly tested through MCP/API | Verify against real Zoho records to confirm field updates are stamped. |
| **Bulk imports** | Possible, but must be controlled | Import as Leads, then manually check before conversion. |
| **Lead conversion** | Base functionality tested / in testing | Confirm no duplicate Accounts, Contacts, or Deals are created. |
| **Workflow triggers** | Mapped / partly configured | Confirm correct firing order in Zoho and no duplicate sequence actions. |
| **Call sequence** | Built | Test Call 1 through Call 5 by Stage to check due date scheduling. |
| **Email sequence** | Templates implemented in Zoho | Test template sends, dynamic operators, merge fields, and reply/bounce handling. |
| **Post-call chase chain** | Built | Test 7-email chain timing, stop conditions on reply, and final completion. |
| **Existing data** | Needs rollout decision | Decide which existing CRM records to enroll, suppress, or leave untouched. |

---

## Core Testing Questions

These are the main behaviors that still need proving before the system can be trusted at scale.

| Question | Why it matters | What needs testing |
| :--- | :--- | :--- |
| **How are Deals with multiple Contacts handled?** | A real Account can have several people involved. The system must not let one Contact incorrectly override the whole Deal. | Test Accounts with 2–5 Contacts at different Stages and States. |
| **Which Contact controls the Deal Stage?** | The Deal should follow the furthest viable open Contact, not the newest Contact or the last edited Contact. | Confirm the Deal moves to the furthest open Contact’s Stage. |
| **What happens when one Contact is Lost but another is Open?** | A single Lost Contact should not close the Deal if another Contact is still active. | Test mixed Contact states under one Account. |
| **How does manual Stage movement interact with Contact rollups?** | Reps may update Stage manually, but the system also rolls up from Contacts. | Confirm manual updates do not cause bad regressions or overwrite correct furthest-stage logic. |
| **How do workflow triggers behave after imports?** | Bulk imports can create timing/concurrency issues. | Import as Leads, manually review, then release controlled batches for conversion. |
| **Does sequence automation start only when it should?** | Calls/emails should not start for suppressed, historical, duplicate, or unreviewed records. | Test Automation Suppressed, Ready for Conversion, and Sequence Status values. |
| **Do email events attach to the right Deal?** | Replies/bounces must pause the correct sequence. | Test replied, bounced, not replied, opened/unreplied, and clicked events. |

---

## Import Testing

Bulk imports are possible, but they need controlled handling. The safe pattern is:

1. **Import as Leads**: Bring new records into the CRM as Leads first.
2. **Review post-import**: Do not immediately convert everything blindly.
3. **Manually check**: Perform a quick check on imported Leads to confirm details are clean.
4. **Mark ready**: Check the `Ready_for_Conversion` field only after review.
5. **Auto-convert**: Let the Lead Processor convert them into Accounts, Contacts, Deals, and Products automatically.

Concurrent imports can create duplicate or conflicting records if too many records are processed at once without review. The system is designed to clean records, but bulk import behavior needs testing before trusting it at scale. The system can support bulk imports, but the rollout should not assume bulk import equals bulk auto-conversion.

---

## Manual Review After Import

After import, there must be a manual check before records are released into the automated conversion and sequence process. The check should verify:
*   **Duplicate company risk**: Ensure no similar company already exists in the Accounts module.
*   **Duplicate contact risk**: Ensure the person's email is not already associated with another Account or Contact.
*   **Duplicate active Deal risk**: Verify the company does not already have an open Deal.
*   **Product Interest mapping**: Confirm Lead product interests are entered correctly for Deal Amount calculation.
*   **Email presence**: Ensure the email field is not blank.
*   **Ready for Conversion status**: Confirm the checkbox is ticked only when lead qualification is complete.
*   **Automation Suppressed status**: Ensure `Automation_Suppressed = true` is ticked for records that require purely manual handling.
*   **Sequence entry**: Check whether the record should enter sequence automation at all.

---

## Multi-Contact Deal Testing

A Deal can have more than one Contact attached to it. This needs specific testing.

The expected rule is:
*   One Account can have many Contacts.
*   One Account should have one active Deal.
*   All relevant Contacts should be linked to that Deal.
*   The Deal Stage should follow the furthest viable open Contact.
*   Lost Contacts should not pull the Deal backward.
*   One Lost Contact should not close the Deal while another Contact is still Open.

Example scenario:

| Contact | Contact Stage | Contact State | Expected Effect |
| :--- | :--- | :--- | :--- |
| **Contact A** | Demo Booking | Open | Lower-stage active Contact |
| **Contact B** | Demo Hosted | Open | Deal should move to Demo Hosted |
| **Contact C** | Commercial Agreement | Lost | Should not control the Deal while open Contacts exist |

Expected Deal result:
*   **Stage** = Demo Hosted
*   **Opportunity** = SQL
*   **State** = Open
*   **Primary Contact** = Contact B, unless an existing valid primary Contact is already tied at the same furthest Stage.

---

## Stage Movement Testing

There are two ways Stage can move:
1. A representative or workflow updates the Deal Stage directly.
2. The system recalculates the Deal Stage from the furthest open Contact.

This needs testing to verify: when manual updates and Contact rollups both exist, does the Deal land in the correct Stage?

Test cases:

| Test | Expected Result |
| :--- | :--- |
| **Rep moves Deal forward** | Deal should move forward and start the correct sequence. |
| **Contact is behind Deal** | Contact should not pull Deal backward incorrectly. |
| **Contact is ahead of Deal** | Deal should move to the furthest open Contact's Stage. |
| **Contact is Lost** | Lost Contact should not control the active Deal. |
| **All Contacts are Lost** | Deal should close as Lost / Closed. |

---

## Contact Role Testing

Contact role mapping needs testing because it affects how representatives read the Deal.

Test cases:

| Test | Expected Result |
| :--- | :--- |
| **Known End User title** | Contact Role = End User |
| **Known Influencer title** | Contact Role = Influencer |
| **Unknown title** | Contact Role = Decision Maker |
| **Blank title** | Contact Role = Decision Maker |
| **Manually changed role** | System does not overwrite it. |
| **Multiple Contacts under one Account** | All relevant Contacts are linked to the Deal through Contact Roles. |

---

## Sequence Testing

We must test that the sequence moves correctly through each Stage.
*   **Initial Bootstrap**: Confirm that when `Sequence_Status` is updated to `Not Started`, the Deal creates Call 1 and updates the status to `Waiting on Call`.
*   **Next Call Generation**: Verify that logging a Neutral or No Answer outcome on Call N creates Call N+1 and schedules it 2 business days out.
*   **Trigger Date Resumption**: Test that date-based triggers (`WF010`) successfully wake up paused or scheduled records on the due date.

---

## Email Template Testing

The email templates should already be implemented in Zoho CRM. The remaining work is testing that the templates:
*   Have the exact expected names mapped in the template resolver (e.g. `Demo Booking Email 1`).
*   Are successfully found and loaded by Jurnii's automation.
*   Send from the correct Zoho function without connection errors.
*   Render the dynamic operators / merge fields correctly in the email body.
*   Preserve links, calendar URLs, and personalization fields without broken tags.
*   Behave correctly across Neutral, No Answer, post-call chase, demo, commercials, onboarding, and renewal contexts.

---

## Call Workflow Testing

We need to confirm that Calls logged by reps actually advance the system as intended:
*   **Positive Outcome**: Confirm the Deal Stage immediately advances and bootstraps Call 1 of the new Stage.
*   **Already Handled**: Verify that logging `Already Handled` completes the step without sending an email or creating a next Call.
*   **Manual Task Pause**: Confirm that logging `Bad Data` or `Not Relevant` successfully pauses the sequence and creates a manual review/repair Task.

---

## Safe Rollout Plan

To safely roll out the new automation, we will execute the following phase-by-phase testing plan:

| Phase | What to test | Goal |
| :---: | :--- | :--- |
| **1** | Small test import | Confirm Leads import correctly into Zoho with correct custom fields. |
| **2** | Manual review | Catch duplicate companies or contacts manually before conversion. |
| **3** | Controlled conversion | Confirm Accounts, Contacts, and Deals are created correctly upon checkbox trigger. |
| **4** | Product mapping | Confirm Product Interest maps correctly to products and sums into Deal Amount. |
| **5** | Call sequence | Confirm Calls are created and outcomes route correctly without cascading loops. |
| **6** | Email sends | Confirm templates, dynamic fields, and open/click/reply tracking work. |
| **7** | Full sequence | Confirm the 5-call + 7-email chase chain behaves correctly and pauses on reply. |
| **8** | Limited live rollout | Run a small real batch (10-20 records) before full production rollout. |

---

## Expected Testing Window

*   **Estimate**: 1–2 weeks for controlled testing and confidence-building.
*   This window is needed to see records move through the system, test staged imports, confirm workflow triggers, send test emails, check dynamic fields, and observe the full call/email sequence behavior.

---

## Open Decisions

Before go-live, commercial leadership must decide:
1.  **Backfill Strategy**: How should we handle existing deals? Should they be mass-enrolled into sequences, suppressed, or left untouched?
2.  **Call Script Location**: Where should reps access the call scripts? Surfaced in Zoho descriptions, Notion, or internal quick-reference cards?
3.  **Suppression Criteria**: What are the exact business rules that should mark a record as permanently `Automation_Suppressed = true`?

---

## Implementation reference

Relevant setup files and configurations:
- `.agents/context/activity-workflows/WORKFLOW_CONFIGURATION_CHECKLIST.md`
- `.agents/context/activity-workflows/TEMPLATE_NAMING_MATRIX.md`
- `.agents/context/activity-workflows/FIELD_REUSE_NOTES.md`
