# V5 Contact-Centric Workflow Refactor

Work in:

```text
C:\Development\Projects\zoho-functions
```

Continue working in:

```text
v5/
```

Do not create a V6 folder.

This is a substantial refactor of the existing V5 functions. Preserve functions and established behaviour that remain useful, but do not preserve the old Deal-owned sequence model merely to minimise edits.

---

# Objective

Move individual workflow and sequence state from Deals to Contacts.

The intended architecture is:

```text
Lead
→ process and convert
→ create or reuse Contact
→ create or reuse Account
→ create or reuse the Account’s canonical Deal
→ link Contact, Account and Deal
→ create an Activation Task for the Contact
→ Task outcome activates the Contact sequence
→ Task, Call, Meeting and email outcomes update the Contact
→ Primary Contact progression rolls up to the Deal
```

The Deal remains the shared commercial container.

The Contact owns the individual communication journey.

---

# Absolute metadata restriction

Under no circumstances create, recreate, rename or add any of the following without explicit user approval:

```text
CRM fields
picklist fields
picklist values
modules
layouts
duplicate replacement fields
duplicate email templates
workflow rules that require new metadata
```

Do not create a field because the implementation would be easier with one.

Do not repair an API-name spelling by creating a replacement field.

Do not add values such as:

```text
Play
Pause
Email First
Call First
Waiting
Queued
Scheduled
```

unless they already exist in current live Zoho metadata or the user explicitly approves them.

If the required behaviour cannot be represented through existing fields and values:

1. stop;
2. identify the exact missing capability;
3. propose the smallest metadata change;
4. wait for explicit approval.

Do not silently improvise metadata.

---

# Authoritative sources

Before editing code, inspect:

```text
.agents/context/api_field_names/
.agents/context/activity-workflows/
.agents/context/activity-workflows/email_path/
docs/
spec.md
v5/
```

Also inspect live Zoho metadata through the available MCP/API tools.

Use this precedence:

```text
1. Current live Zoho metadata
2. Current API-name exports under .agents/context/api_field_names/
3. Current planning CSVs
4. Current repository documentation
5. Older function assumptions
```

Where sources disagree:

* do not change Zoho to match old code;
* update code and documentation to match verified live metadata;
* refresh stale API-name exports;
* record the discrepancy.

Never infer an API name from a field label.

---

# Correct sequence field names

The intended Contact fields are:

```text
Field Label       API Name

Sequence Type     Sequence_Type
Sequence State    Sequence_State
Sequence Stage    Sequence_Stage
Sequence Step     Sequence_Step
```

Verify these exact names against live Zoho metadata.

Search the entire repository for stale spellings:

```text
Seqeunce_Type
Seqeunce_Step
Seqeunce Type
Seqeunce Step
```

If live Zoho still uses a stale spelling:

* do not create a corrected duplicate field;
* report the mismatch;
* use the actual live API name temporarily;
* request approval before renaming or replacing metadata.

If live Zoho already contains the corrected names, update all repository code, documentation and exports accordingly.

---

# Canonical Contact fields

The Contact is the workflow record.

Use the existing Contact fields:

```text
Stage
State
Status
Sequence_Type
Sequence_State
Sequence_Stage
Sequence_Step
Contact_Role
Lead_Source
Owner
Account_Name
Email
```

Do not add another route, action, pause, next-step, next-action or sequence-status field unless explicitly approved.

These fields work in combination.

The current sequence position is defined by:

```text
Contact.Stage
+ Contact.Sequence_Type
+ Contact.Sequence_State
+ Contact.Sequence_Stage
+ Contact.Sequence_Step
```

---

# Contact Stage

Use the current Contact Stage values:

```text
Marketing Consent
Demo Booking
Demo Confirmation
Demo Hosted
Proposal Preparation
Commercial Agreement
Onboarding
Renewal
```

Do not continue using `Marketing Qualification` where the current metadata uses `Marketing Consent`.

Audit legacy references including:

```text
Marketing Qualification
Contact_Completed_Marketing_Qualification_At
Marketing Qualification Email ...
```

Do not rename or recreate fields automatically. Determine the current live field and template names and update repository references accordingly.

---

# Contact State and Status

Use only the current live values.

Expected State values:

```text
Open
Lost
```

Expected Status values:

```text
New
Working
Closed
```

Do not add additional sequence semantics to these fields.

They describe the Contact’s commercial record state, not the current activity type.

---

# Sequence Type

The intended Sequence Type values are:

```text
Email
Call
Manual
```

These replace the older values:

```text
Email First
Call First
```

Verify the live picklist.

If live Zoho still contains `Email First` and `Call First`:

* do not add replacement values automatically;
* report the mismatch;
* determine whether existing values can be mapped temporarily in code;
* wait for approval before changing the picklist.

`Sequence_Type` records the communication context chosen at activation.

It does not create two separate permanent workflow systems.

There is one Stage sequence with different entry actions.

---

# Sequence State

Use only the values present in live Zoho.

Expected values include:

```text
Not Activated
Running
Stopped
Complete
```

Do not add `Paused`, `Play`, `Waiting` or equivalent values without approval.

Audit whether the current values can represent every required interruption case.

If a temporary pause cannot be represented safely with existing values and native activity dates, stop and report the gap.

---

# Sequence Stage

Use the existing values:

```text
Email
Call
Meeting
Task
```

`Sequence_Stage` identifies the current action category.

It does not repeat the Contact Stage.

Example:

```text
Contact.Stage = Demo Booking
Contact.Sequence_Stage = Email
Contact.Sequence_Step = 2
```

means the second email action within Demo Booking.

---

# Sequence Step

Use the existing values:

```text
None
1
2
3
4
5
6
7
8
9
10
```

Do not replace them with verbose values such as:

```text
Demo Booking Follow-Up Email 2
Renewal Call 3
Commercial Agreement Email 4
```

The router derives the action from:

```text
Stage + Sequence Stage + Sequence Step
```

---

# One sequence with different entry actions

Do not maintain separate long-term “Email First” and “Call First” branches.

The Activation Task selects the first action:

```text
Email
Call
Manual
```

Examples:

```text
Activation outcome = Email
→ Sequence_Type = Email
→ Sequence_State = Running
→ Sequence_Stage = Email
→ Sequence_Step = 1
→ send the Stage’s first email
```

```text
Activation outcome = Call
→ Sequence_Type = Call
→ Sequence_State = Running
→ Sequence_Stage = Call or Task, based on the actual outreach activity
→ Sequence_Step = 1
→ create the first outreach activity
```

After the entry action, both paths converge onto one shared Stage-specific progression.

Do not duplicate an entire template or function chain solely because the Contact entered through Email rather than Call.

Most Stages are directed toward acquiring, confirming or completing a Meeting.

The principal exception is Commercial Agreement, whose target is signature.

---

# Lead processing

The Lead module is an intake and processing layer.

When an eligible Lead is created or updated:

1. Read the Lead using verified API names.
2. Create or reuse the Contact.
3. Create or reuse the Account.
4. Create or reuse the Account’s canonical open Deal.
5. Link the Contact to the Account.
6. Link the Contact to the Deal through Contact Roles.
7. Preserve the Contact Role:

   * Decision Maker
   * Influencer
   * End User
8. Link Products and calculate Deal value using the existing rules.
9. Map Lead Stage to Contact Stage.
10. Preserve the Lead/Contact owner.
11. Create an Activation Task when the Contact is not already activated.

Do not create an automatic email, Call or Meeting before activation.

Do not reset an existing Contact’s sequence merely because another Lead record matched that Contact.

Do not create duplicate Contacts, Accounts or Deals.

---

# Activation Task

Create one Activation Task for each new or unactivated Contact.

The Task must be linked to both:

```text
Who_Id  → Contact
What_Id → canonical Deal
```

The Task owner should be the responsible Contact or Lead owner.

The Task starts with:

```text
Status = Not Started
Task Outcome = blank
```

The user completes the Task and selects the outcome.

The user must not then need to edit the Contact separately.

The Task completion handler must update the Contact automatically.

Map activation outcomes to Sequence Type:

```text
Email  → Sequence_Type = Email
Call   → Sequence_Type = Call
Manual → Sequence_Type = Manual
```

Use existing Task Outcome values where possible.

If Task Outcome currently contains values such as:

```text
Activate Email First
Activate Call First
```

do not add replacement values automatically.

Either:

* map the existing Task Outcome values to `Email` and `Call` in code; or
* produce a picklist migration proposal and wait for approval.

Activation Task duplicate identity must include:

```text
Contact
Deal
Contact Stage
open Task status
```

Do not deduplicate only by Deal.

Multiple Contacts on the same Deal may have separate sequences.

---

# Contact-owned sequence routing

Refactor the router so that the authoritative sequence state comes from the Contact.

The router must read:

```text
Contact ID
canonical Deal ID
Contact Stage
Sequence Type
Sequence State
Sequence Stage
Sequence Step
```

It must determine the next action from those values.

Do not continue using Deal sequence fields as a parallel state machine.

Every generated activity must remain linked to:

```text
Who_Id  → Contact
What_Id → Deal
```

This allows multiple Contacts on the same Deal to progress independently while retaining the shared commercial context.

---

# Activity outcomes

Tasks, Calls and Meetings are transition inputs.

For each activity handler:

1. Read the activity.
2. Read `Who_Id` to identify the Contact.
3. Read `What_Id` to identify the Deal.
4. Verify the activity belongs to the current Contact sequence.
5. Read its outcome.
6. Update the Contact’s Stage, State, Status and sequence fields.
7. Create or schedule the next action.
8. Update the Deal only where commercial rollup or Deal-level data requires it.

The user should not need to update the Contact manually.

## Positive outcome

A positive outcome may:

```text
advance Contact.Stage
reset Contact.Sequence_Step
set the next Contact.Sequence_Stage
continue or complete the Contact sequence
```

The exact Stage transition must follow the canonical Stage model.

## Unsuccessful contact or no response

An unsuccessful attempt should generally:

```text
keep Contact.Stage unchanged
advance Contact.Sequence_Step
set the next Contact.Sequence_Stage
create or schedule the next activity
```

Do not maintain separate duplicate follow-up sequences for Email-started and Call-started Contacts.

## Stop or loss

Use the existing Contact fields.

Do not create a second suppression or stop state if `Sequence_State`, `State` and `Status` already represent the outcome.

Stopping automation for one Contact must not automatically mark the Deal Lost.

---

# Calls versus Meetings

Audit how existing V5 functions use Calls and Meetings.

Use Meetings/Events for scheduled calendar conversations such as:

```text
qualification meeting
demo
commercial review
onboarding session
renewal meeting
```

Use Calls only for actual telephone outreach or logged Call activity.

Do not treat a scheduled Meeting as a Call merely because older V5 functions used `createStageCall`.

Retain the correct activity module based on the real business action.

---

# Scheduling and waiting

Do not automatically add a Contact datetime field.

First determine whether waiting can be represented through:

```text
Task due date
Call start time
Meeting start time
scheduled workflow action
existing date-routing capability
```

For Tasks, Calls and Meetings, create the next activity with its future date where supported.

For delayed automatic emails, audit the current implementation and supported Zoho scheduling mechanisms.

Do not assume that old Deal waiting fields remain necessary.

Do not assume a new Contact `Next Action At` field is permitted.

If delayed automatic emails cannot be implemented reliably through existing metadata:

1. stop;
2. explain the limitation;
3. propose the smallest metadata change;
4. wait for approval.

---

# Mandatory completed Task for every automatic email

For sequence audit purposes, do not depend on a first-class editable Email activity record.

Every successfully sent automatic email must produce exactly one completed Task as its CRM audit record.

After Zoho confirms the email send:

```text
create exactly one Task
Status = Completed
Who_Id = Contact
What_Id = Deal
```

Use existing Task-level sequence fields where they exist:

```text
Sequence_Stage = Email
Sequence_Step = the email step that was sent
Sequence_Managed = Yes
```

Do not create these fields if they do not already exist.

Use the existing Task Type value for an email audit record if one exists, such as:

```text
Email Sent
```

Do not add a Task Type value without approval.

The Task’s verified Description or Notes field must record:

```text
email template name
Zoho template ID where available
email subject
recipient
sender
Zoho message ID
Contact Stage
Sequence Type
Sequence Stage
Sequence Step
send timestamp
send result
```

Verify the actual field API name before coding.

Do not invent a `Notes` field.

The email audit Task records the action that just completed. It must not overwrite the Contact’s next sequence action incorrectly.

## Email success rule

Only create or retain the Task as Completed after the email API confirms success.

If the send fails:

```text
do not create a successful Completed email Task
do not advance the Contact as though the email was sent
do not store a successful message ID
leave the sequence retryable where appropriate
record the failure through the existing automation log
```

## Email idempotency

Repeated invocation must not:

```text
send the same email twice
create duplicate completed email Tasks
advance the Contact twice
```

Use existing fields, the Zoho message ID and a deterministic send identity.

Do not create a new idempotency field without approval.

## Audit Task guard

The completed email Task is audit-only.

`handleTaskCompletion` must explicitly recognise it and return without advancing the sequence a second time.

---

# Email-template consolidation

Use:

```text
mcp:crm-email-crud
```

for Zoho email-template retrieval and updates.

The templates already exist in Zoho.

Do not create duplicate templates.

Do not create separate template families for Email-started and Call-started Contacts.

The target is one canonical template sequence for:

```text
Contact Stage
+ Sequence Step
```

Special-purpose templates may remain where genuinely required, including:

```text
demo confirmation
demo reminder
no-show
commercial terms
commercial confirmation
onboarding
renewal
```

Do not retain duplicate copy whose only distinction is “Email First” versus “Call First.”

## Dynamic Sequence Type content

Where email copy needs to describe the communication method, use the Contact Sequence Type merge field.

Expected values:

```text
Email
Call
Manual
```

Do not guess the merge tag.

Verify the live field label and supported Zoho merge syntax.

Correct syntax:

```text
${Contacts.Sequence Type}
```

or the exact equivalent produced by live Zoho metadata.

Incorrect syntax:

```text
$[Contacts.Sequence Type]
```

Do not wrap merge tags in Markdown backticks.

## Repository parity

The repository under:

```text
.agents/context/activity-workflows/email_path/
```

must contain the actual subject and body stored in Zoho.

For template changes:

1. fetch the existing template through `mcp:crm-email-crud`;
2. update the local repository representation;
3. show the diff;
4. update the same existing Zoho template by ID;
5. re-fetch it;
6. verify repository and Zoho match.

Do not commit until the user confirms publication.

---

# Deal model

The Deal remains the Account’s shared commercial record.

Use one canonical open Deal per Account.

The Deal stores:

```text
Account_Name
Contact_Name
Opportunity_Stage
Opportunity_State
Opportunity_Status
Stage
Products
Amount
commercial fields
contract fields
Deal-level demo fields where genuinely required
```

## Primary Contact

Use:

```text
Contact_Name
```

as the canonical Deal Primary Contact lookup.

Do not continue using both:

```text
Contact_Name
Deal_Primary_Contact
```

Update functions, workflows, templates and documentation to use `Contact_Name`.

Treat `Deal_Primary_Contact` as a deletion candidate.

Do not delete it until:

1. all dependencies are identified;
2. all references are migrated;
3. the user explicitly approves deletion.

## Contact Roles

Contact Role is separate from Primary Contact.

Use the existing values:

```text
Decision Maker
Influencer
End User
```

Multiple Contacts may be associated with the Deal.

Primary Contact status does not erase or replace Contact Role.

---

# Deal rollup

The Primary Contact controls the Deal’s commercial rollup:

```text
Primary Contact.Stage  → Deal.Opportunity_Stage
Primary Contact.State  → Deal.Opportunity_State
Primary Contact.Status → Deal.Opportunity_Status
```

Derive Deal `Stage`, labelled Opportunity Type, from `Opportunity_Stage`:

```text
Marketing Consent       → MQL
Demo Booking            → SQL
Demo Confirmation       → SQL
Demo Hosted              → SQL
Proposal Preparation    → FTP
Commercial Agreement    → FTP
Onboarding               → RTP
Renewal                  → RTP
```

Do not use the old Deal API name `Opportunity_Stage` where the current field is:

```text
Opportunity_Stage
```

Do not confuse:

```text
Contact.Stage
Deal.Opportunity_Stage
Deal.Stage
```

Non-primary Contacts may continue their own sequences without rewriting the Deal rollup.

---

# Legacy Deal sequence-field migration

Audit all Deal-level automation fields, including:

```text
Automation_Suppressed
Sequence_Status
Sequence_Paused_Until
Next_Action_Due_Date
Suppression_Reason
Sequence_Action_Mode
Active_Sequence_Stage
Active_Sequence_Attempt
Active_Email_Chain_Step
Next_Action_Type
Opportunity_Stage
State
Status
Deal_Primary_Contact
```

Verify which fields still exist in live metadata.

Create a dependency matrix:

```text
Field label
API name
Module
Function references
Workflow references
Template references
Layout references
Contact replacement
Retain / migrate / deletion candidate
Blocking dependency
```

The goal is to:

```text
move individual sequence state to Contacts
remove new function dependencies on Deal sequence fields
identify obsolete Deal fields
prepare a safe deletion plan
```

Do not delete fields automatically.

Do not delete workflow rules automatically.

---

# Function audit

Audit every V5 function, including:

```text
processLead.deluge
processContact.deluge
processAccount.deluge
processDeal.deluge

sequenceRouter.deluge
createStageCall.deluge
sendSequencedEmail.deluge
handleCallOutcome.deluge
handleTaskCompletion.deluge
handleMeetingEvent.deluge
handleDemoOutcome.deluge
handleCommercialsStatusChange.deluge
handleEmailEvent.deluge
email-event wrappers
supersedeOldSequence.deluge
date utilities
template utilities
logging utilities
```

Classify each function as:

```text
retain with API-name corrections
retain and refactor to Contact-owned state
retain as Deal commercial logic
obsolete after migration
requires workflow-binding change
```

Do not delete a Zoho function without approval.

Prefer retaining existing public function names where practical.

Do not create V6-named duplicates.

Where a function currently accepts a Deal ID but must become Contact-centric, determine whether it should:

```text
accept a Contact ID
accept Contact and Deal IDs
derive Contact from activity Who_Id
```

Document argument and workflow-binding changes before implementation.

---

# Expected responsibility split

## `processLead`

Should:

```text
process and convert Lead
create/reuse Contact
create/reuse Account
create/reuse canonical Deal
link records
map Lead fields to Contact
maintain Contact Roles and Products
create Contact Activation Task if required
```

It must not directly start the Contact sequence.

## `processContact`

Should:

```text
maintain Contact-level workflow state
sync Deal rollup when Contact is the Deal Primary Contact
avoid resetting an existing active sequence
```

## `processAccount`

Should:

```text
maintain Account and canonical Deal relationships
avoid owning Contact sequence logic
```

## `processDeal`

Should:

```text
maintain commercial and contract data
maintain Contact_Name as Primary Contact
derive Opportunity Type from Opportunity Stage
avoid owning individual sequence progression
```

## Router

Should:

```text
read Contact Stage and sequence fields
resolve the next action
create or send the action
link it to Contact and Deal
prevent duplicates
```

## Activity handlers

Should:

```text
read activity outcome
update Contact progression
advance, stop or complete Contact sequence
sync Deal only when Contact is Primary
create or schedule the next action
```

## Email sender

Should:

```text
resolve one canonical template
send it to the Contact
create one completed email audit Task
advance Contact sequence once
prevent duplicate sends
```

---

# Workflow-rule audit

Inspect every current live Zoho workflow and every repository workflow specification.

Identify Deal-based sequence rules, including the current:

```text
WF002
WF003
WF010 variants
```

Determine which rules should:

```text
move to Contacts
remain on Deals for commercial logic
remain on Tasks
remain on Calls
remain on Meetings
be retired after migration
```

Do not modify workflows through the browser.

Use MCP/API capabilities where supported.

Do not delete or disable a live workflow until:

1. the replacement is published;
2. the user confirms publication;
3. replacement tests pass;
4. the user approves removal.

---

# Documentation changes

Update all affected documentation:

```text
spec.md
FUNCTION_SPEC.md
WORKFLOW_TRIGGER_MAP.md
WORKFLOW_CONFIGURATION_CHECKLIST.md
VERIFICATION_PLAN.md
TEST_CASES.md
MCP_TEST_HARNESS_PROMPT.md
TEMPLATE_NAMING_MATRIX.md
email_path inventory
API field-name exports
```

Remove or correct statements asserting that:

```text
the Deal owns sequence state
every Stage starts with Call 1
Email First and Call First are separate permanent paths
Deal.Opportunity_Stage is the current objective
Deal sequence fields are the source of truth
```

Document the completed email Task requirement.

---

# Testing requirements

## Lead conversion

Verify:

* Lead converts immediately.
* Contact, Account and canonical Deal are created or reused.
* Contact Roles and Products are linked.
* Lead Stage maps to Contact Stage.
* No email, Call or Meeting occurs before activation.

## Activation

Verify:

* one Activation Task for an unactivated Contact;
* Task linked to Contact and Deal;
* no duplicate activation Task;
* Email outcome sets Sequence Type to Email;
* Call outcome sets Sequence Type to Call;
* Manual outcome sets Sequence Type to Manual;
* sequence begins without manual Contact editing.

## Independent Contacts

Verify:

* two Contacts may share one Deal;
* each Contact retains independent Stage and sequence values;
* advancing one does not cancel or overwrite another;
* only the Primary Contact updates Deal rollup.

## Primary Contact

Verify:

* `Contact_Name` is used;
* new code does not reference `Deal_Primary_Contact`;
* changing Primary Contact resynchronises Deal Opportunity fields;
* Contact Role remains independent.

## Sequence progression

Verify:

* Stage + Sequence Stage + Sequence Step resolves the action;
* Email and Call entry actions converge onto one shared sequence;
* no duplicate branch-specific email chains remain;
* positive outcome advances Stage and resets Step;
* unsuccessful outcome advances Step without changing Stage;
* Stopped or Complete Contacts create no new activities.

## Email

Verify:

* existing Zoho template used;
* valid `${Contacts...}` merge syntax;
* Sequence Type renders dynamically;
* successful send creates exactly one completed Task;
* Task contains template, subject, recipient, sender, message ID, Stage and Step;
* failed send creates no successful completed Task;
* repeated invocation produces no duplicate send or Task;
* email audit Task does not advance the sequence again.

## Scheduling

Verify:

* future Tasks, Calls and Meetings work;
* delayed email scheduling works through existing capability;
* no new timing field is added without approval.

## Deal migration

Verify:

* new functions do not use obsolete Deal sequence fields;
* Deal Opportunity fields roll up from Primary Contact;
* Opportunity Type mapping is correct;
* deletion candidates have no remaining dependencies before deletion is proposed.

---

# MCP and browser boundaries

Use all relevant MCP/API servers for:

```text
metadata
field API names
picklists
CRM records
workflow rules
function publication
function execution
email-template CRUD
test data
activities
logs
cleanup
```

Use:

```text
mcp:crm-email-crud
```

for email-template operations.

The browser may only be used to verify Gmail delivery and rendering.

Do not use the browser to:

```text
edit functions
publish functions
edit workflows
edit fields
edit picklists
edit templates
create CRM records
```

---

# Git and publication rule

Do not commit or push until:

1. the complete working-tree diff is shown;
2. affected functions and templates are published to Zoho;
3. the user explicitly confirms publication;
4. the published runtime passes required tests;
5. the tested source matches the working tree.

Working-tree edits are allowed.

Commits are forbidden before explicit publication confirmation.

If MCP/API publication is unavailable:

1. provide exact function names and repository paths;
2. provide publication order;
3. stop;
4. wait for user confirmation;
5. do not commit.

---

# Execution phases

## Phase 1 — Audit only

Before editing, return:

```text
verified Contact API names
verified Contact picklists
verified Deal API names
current Deal sequence dependencies
current function responsibilities
current workflow ownership
current template families
Contact-field migration map
Deal deletion candidates
metadata gaps requiring approval
```

Do not create metadata.

If a new field or picklist value is required, stop and request approval.

## Phase 2 — Uncommitted implementation

If existing metadata is sufficient:

```text
edit V5 functions
edit documentation
edit tests
edit local email-template representations
refresh API-name exports
```

Do not commit.

## Phase 3 — Show migration

Return:

```text
files changed
complete uncommitted diff
functions requiring publication
templates requiring update
workflow changes required
Deal fields no longer referenced
deletion candidates
tests prepared
```

## Phase 4 — Publish and stop

Publish through MCP/API where supported.

Then stop and request explicit user confirmation.

Do not perform final runtime testing or commit before confirmation.

## Phase 5 — Runtime test

After confirmation:

```text
run Contact-owned E2E
verify Gmail delivery
verify completed email Tasks
verify independent Contact sequences
verify Deal rollups
verify scheduling
verify idempotency
```

## Phase 6 — Commit

Only after successful testing:

```text
show final diff
show test evidence
show proposed commit message
commit the exact published and tested source
```

Do not push unless explicitly instructed.

---

# Required Phase 1 response

Return:

## Current-state findings

Identify where V5 still owns sequence state on Deals.

## Verified field map

List exact live Contact and Deal field labels, API names and picklist values.

## Function migration matrix

For each V5 function:

```text
current responsibility
new responsibility
files affected
workflow binding affected
```

## Field dependency matrix

For each legacy Deal sequence field:

```text
current dependencies
Contact replacement
retain or deletion candidate
blockers
```

## Template consolidation

List duplicate template families and proposed canonical mapping.

## Metadata approval requirements

List anything requiring a new field, picklist value, module or template.

If this list is non-empty, stop and wait for approval.

If it is empty, proceed with the uncommitted implementation and show the diff.
