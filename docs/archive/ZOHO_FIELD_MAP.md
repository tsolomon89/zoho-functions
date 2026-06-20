# ZOHO_FIELD_MAP.md — Field Creation and API Name Map

## Purpose

This file maps required custom fields to their intended module, type, and values.

Before coding, replace every `TBD_API_NAME` with the actual Zoho API name.

Zoho functions and API calls must use API names, not UI labels.

---

## Required API-name verification process

For every custom field:

1. Create the field in Zoho.
2. Go to Developer Hub / API Names, or use Zoho Fields Metadata API.
3. Copy the actual API name.
4. Replace `TBD_API_NAME`.
5. Confirm picklist values exactly match this document or update this document to match the CRM.

---

# Deals

Deals own the commercial state machine.

| Label | API Name | Type | Values / Notes | Required |
|---|---|---|---|---|
| Label | API Name | Type | Values / Notes | Required |
|---|---|---|---|---|
| Stage | `Opportunity_Stage` | Picklist | Marketing Qualification; Demo Booking; Demo Confirmation; Demo Hosted; Commercial Agreement; Onboarding; Onboarding; Renewal | Yes |
| Stage Rank | `(derived)` | Number | 1-8 | Yes |
| Opportunity | `Stage` | Picklist | MQL; SQL; FTP; RTP | Yes |
| Sequence Status | `Sequence_Status` | Picklist | Not Started; Initialized; Waiting on Call; Waiting on Meeting; Waiting on Email Trigger; Waiting on Internal Task; Paused; Deferred; Manual Only; Completed; Superseded; Suppressed | Yes |
| Sequence Action Mode | `Sequence_Action_Mode` | Picklist | Call First; Email First; Meeting First; Task First; Manual Review First | Yes |
| Active Sequence Stage | `Active_Sequence_Stage` | Picklist | Same values as Stage | Yes |
| Active Sequence Attempt | `Active_Sequence_Attempt` | Number | 0-5 | Yes |
| Active Email Chain Step | `Active_Email_Chain_Step` | Number | 0-7 | Yes |
| Next Action Type | `Next_Action_Type` | Picklist | Call; Automated Email; Meeting; Task; Stage Update; Manual Review | Yes |
| Next Action Due Date | `Next_Action_Due_Date` | DateTime | Next internal/customer action due | Yes |
| Sequence Paused Until | `Sequence_Paused_Until` | DateTime | Deferral/pause date | Yes |
| Sequence Superseded At | `Sequence_Superseded_At` | DateTime | Used to prevent stale actions | Yes |
| Automation Suppressed | `Automation_Suppressed` | Checkbox | true/false | Yes |
| Suppression Reason | `Suppression_Reason` | Picklist | Existing Client; Existing Open Conversation; Partner Managed; Bad Data; Do Not Contact; Duplicate; Imported Historical Record; Manual Handling Required; Legal/Compliance; Stage Incorrect | Yes |
| Demo Meeting ID | `Demo_Meeting_ID` | Text | Stores related Event ID | Yes |
| Demo Start DateTime | `Demo_Start_DateTime` | DateTime | Demo start | Yes |
| Demo End DateTime | `Demo_End_DateTime` | DateTime | Demo end | Yes |
| Demo Reminder Send At | `Demo_Reminder_Send_At` | DateTime | One business day before, AM | Yes |
| Demo Status | `Demo_Status` | Picklist | Not Scheduled; Scheduled; Confirmed; Rescheduled; Cancelled; Completed; No Show | Yes |
| Demo Outcome | `Demo_Outcome` | Picklist | Scheduled; Attended - Qualified; Attended - Needs Follow-up; Attended - Not Qualified; No Show; Rescheduled; Cancelled; Commercials Requested; Follow-up Required | Yes |
| Commercials Status | `Commercials_Status` | Picklist | Not Started; Drafting; Ready to Send; Sent; Discussed; Intent to Sign; Signed; Deferred; Rejected | Yes |
| Commercial Agreement At | `Commercials_Sent_At` | DateTime | Starts FTP follow-up | Yes |
| Commercials Discussed At | `Commercials_Discussed_At` | DateTime | Used for chase timing | Yes |
| Commercial Outcome | `Commercial_Outcome` | Picklist | Intent to Sign; Needs Review; Deferred; Rejected; No Answer; Signed | Yes |
| Next Commercial Follow-Up Date | `Next_Comm_Follow_Up_Date` | DateTime | Deferral override | Yes |
| Commercial Follow-Up Reason | `Comm_Follow_Up_Reason` | Picklist/Text | Budget Timing; Board Approval; Legal Review; Procurement; Asked To Defer; No Response; Other | Recommended |
| Intent To Sign | `Intent_To_Sign` | Checkbox | true/false | Yes |
| Expected Signature Date | `Expected_Signature_Date` | Date | Forecast/deferral date | Recommended |
| Signed At | `Signed_At` | DateTime | Signature timestamp | Yes |
| Sequence Thread Message ID | `Seq_Thread_Message_ID` | Text | Root message/thread ID | Required for email threading |
| Last Email Message ID | `Last_Email_Message_ID` | Text | Last sent message ID | Required for email threading |
| Last Email Template | `Last_Email_Template` | Text | Debug/audit | Recommended |
| Last Email Sent At | `Last_Email_Sent_At` | DateTime | Timing/no-reply logic | Recommended |
| Product Resolution Status | `Product_Resolution_Status` | Picklist | Not Started; Resolved; Missing Product Interest; Failed; Manual Review; No Active Product Match | Yes |
| Deal Value Source | `Deal_Value_Source` | Picklist | Product Derived; Manual; Imported; Estimated; Unknown | Recommended |
| Associated Product IDs | `Associated_Product_IDs` | Text | Debug/reference | Optional |

---

# Calls

Calls are the primary human checkpoint and the main trigger for emails.

| Label | API Name | Type | Values / Notes | Required |
|---|---|---|---|---|
| Related Deal | `TBD_API_NAME` | Lookup: Deals | Must link every sequence call to a Deal | Yes |
| Sequence Managed | `TBD_API_NAME` | Checkbox | true/false | Yes |
| Sequence Stage | `TBD_API_NAME` | Picklist/Text | Same values as Stage | Yes |
| Sequence Attempt | `TBD_API_NAME` | Number | 1-5 | Yes |
| Call Outcome | `TBD_API_NAME` | Picklist | Positive; Neutral; No Answer; Negative; Deferred; Bad Data; Already Handled; Not Relevant; Manual Only; Do Not Contact | Yes |
| Outcome Notes | `TBD_API_NAME` | Multi-line Text | Rep notes | Recommended |
| Next Follow-Up Date | `TBD_API_NAME` | DateTime | Used for deferral | Yes |
| Email Trigger Template | `TBD_API_NAME` | Text | Optional resolved template name | Recommended |
| Call Purpose Detail | `TBD_API_NAME` | Picklist | Data Completion; Book Demo; Confirm Attendance; Post-Demo Follow-Up; Commercial Discussion; Onboarding; Renewal | Recommended |
| Blocks Email Until Completed | `TBD_API_NAME` | Checkbox | true/false | Yes |

---

# Events / Meetings

Meetings are `Events` in Zoho API.

| Label | API Name | Type | Values / Notes | Required |
|---|---|---|---|---|
| Related Deal | `TBD_API_NAME` | Lookup: Deals | Link meeting to Deal | Yes |
| Sequence Managed | `TBD_API_NAME` | Checkbox | true/false | Recommended |
| Meeting Type | `TBD_API_NAME` | Picklist | Demo; Commercial Discussion; Onboarding; Renewal; Other | Yes |
| Meeting Status | `TBD_API_NAME` | Picklist | Scheduled; Confirmed; Rescheduled; Cancelled; Completed; No Show | Yes |
| Meeting Outcome | `TBD_API_NAME` | Picklist | Scheduled; Attended - Qualified; Attended - Needs Follow-up; Attended - Not Qualified; No Show; Rescheduled; Cancelled; Commercials Discussed; Intent to Sign; Renewal Agreed; Renewal Declined | Recommended |
| Reminder Send At | `TBD_API_NAME` | DateTime | Meeting reminder date/time | Recommended |
| Follow-Up Required | `TBD_API_NAME` | Checkbox | true/false | Recommended |
| Follow-Up Stage | `TBD_API_NAME` | Picklist | Same values as Stage | Recommended |
| External Calendar Booking ID | `TBD_API_NAME` | Text | Calendly/booking integration ID | Optional |

---

# Tasks

Tasks are for non-call manual work.

| Label | API Name | Type | Values / Notes | Required |
|---|---|---|---|---|
| Related To | `What_Id` | Lookup: polymorphic | Link task to Deal (with $se_module="Deals") | Yes |
| Sequence Managed | `Sequence_Managed` | Picklist | Yes; No | Yes |
| Task Type | `Task_Type` | Picklist | Enrichment; Data Repair; Draft Commercials; Send Commercials; Review Reply; Onboarding Setup; Manual Review; Suppression Review; Sequence Activation | Yes |
| Task Outcome | `Task_Outcome` | Picklist | Completed; Blocked; Not Relevant; Already Handled; Needs Follow-Up; Failed; Activate Call First; Activate Email First; Manual Only; Suppress; Stage Incorrect | Recommended |
| Sequence Stage | `Sequence_Stage` | Picklist/Text | Same values as Stage | Recommended |
| Sequence Attempt | `Sequence_Attempt` | Number | 0-5 | Recommended |
| Next Follow-Up Date | `Next_Follow_Up_Date` | DateTime | Deferral | Recommended |
| Blocks Sequence | `Blocks_Sequence` | Picklist | Yes; No | Yes |

---

# Contacts

Contacts hold identity/profile/consent context.

| Label | API Name | Type | Values / Notes | Required |
|---|---|---|---|---|
| Contact Source Classification | `TBD_API_NAME` | Picklist | Inbound Form; LinkedIn Prospecting; Partner Referral; Existing Database; Existing Client; Calendar Booking; Migration; Manual Add; Bulk Import | Recommended |
| Marketing Qualification Status | `TBD_API_NAME` | Picklist | Consented; Not Consented; Unknown; Withdrawn | Yes |
| Profile Completion Status | `TBD_API_NAME` | Picklist | Complete; Missing Company; Missing Phone; Missing Product Interest; Missing Role; Needs Enrichment | Recommended |
| Do Not Contact Reason | `TBD_API_NAME` | Picklist | Unsubscribed; Existing Client; Duplicate; Bad Data; Legal/Compliance; Requested No Contact | Recommended |
| Preferred Contact Method | `TBD_API_NAME` | Picklist | Phone; Email; No Preference; Partner Managed | Optional |
| Last Enrichment Status | `TBD_API_NAME` | Picklist | Not Started; Completed; Failed; Needs Review | Optional |
| Active Deal ID | `TBD_API_NAME` | Text | Debug/reference | Optional |

---

# Leads

Leads are conversion input records only. Once a Deal exists, the Deal owns the commercial state.

| Label | API Name | Type | Values / Notes | Required |
|---|---|---|---|---|
| Lead Processing Status | `TBD_API_NAME` | Picklist | Not Processed; Processing; Converted; Failed; Manual Review; Duplicate | Yes |
| Conversion Outcome | `TBD_API_NAME` | Picklist/Text | Contact Created; Contact Reused; Account Created; Account Reused; Deal Created; Deal Reused; Failed | Recommended |
| Imported Record Type | `TBD_API_NAME` | Picklist | Inbound Form; LinkedIn Prospecting; Partner Referral; Existing Database; Existing Client; Calendar Booking; Migration; Manual Add; Bulk Import | Recommended |
| Initial Stage | `TBD_API_NAME` | Picklist | Same values as Stage | Recommended |
| Initial Opportunity | `TBD_API_NAME` | Picklist | MQL; SQL; FTP; RTP | Recommended |
| Product Resolution Status | `TBD_API_NAME` | Picklist | Not Started; Resolved; Missing Product Interest; Failed; Manual Review; No Active Product Match | Recommended |
| Processing Error | `TBD_API_NAME` | Multi-line Text | Error/debug output | Recommended |
| Ready for Conversion | `TBD_API_NAME` | Checkbox | true/false | Optional |

---

# Accounts

Accounts hold company-level context.

| Label | API Name | Type | Values / Notes | Required |
|---|---|---|---|---|
| Account Source Classification | `TBD_API_NAME` | Picklist | Inbound Form; LinkedIn Prospecting; Partner Referral; Existing Database; Existing Client; Calendar Booking; Migration; Manual Add; Bulk Import | Recommended |
| Account Enrichment Status | `TBD_API_NAME` | Picklist | Not Started; Complete; Needs Research; Failed | Recommended |
| Industry Confirmation Status | `TBD_API_NAME` | Picklist | Known; Inferred; Unknown; Needs Review | Optional |
| Company Size Band | `TBD_API_NAME` | Picklist | 1-10; 11-50; 51-200; 201-500; 501-1000; 1000+; Unknown | Recommended |
| Account Status | `TBD_API_NAME` | Picklist | Prospect; Active Customer; Existing Client; Partner; Churned; Do Not Contact | Recommended |
| Automation Suppressed | `TBD_API_NAME` | Checkbox | true/false | Recommended |
| Suppression Reason | `TBD_API_NAME` | Picklist | Existing Client; Existing Open Conversation; Partner Managed; Bad Data; Do Not Contact; Duplicate; Imported Historical Record; Manual Handling Required; Legal/Compliance; Stage Incorrect | Recommended |

---

# Products

Products support value calculation and product mapping.

| Label | API Name | Type | Values / Notes | Required |
|---|---|---|---|---|
| CRM Product Type | `TBD_API_NAME` | Picklist | Product; Feature; Solution; Use Case; Bundle | Recommended |
| Default Deal Value | `TBD_API_NAME` | Currency | Used for Deal Amount calculation | Yes |
| Value Calculation Method | `TBD_API_NAME` | Picklist | Fixed; Tiered; Manual; Imported | Recommended |
| Active for Deal Automation | `TBD_API_NAME` | Checkbox | true/false | Yes |
| Product Mapping Aliases | `TBD_API_NAME` | Text/Multi-line | Names/synonyms for resolution | Recommended |
| Needs Manual Pricing | `TBD_API_NAME` | Checkbox | true/false | Recommended |
