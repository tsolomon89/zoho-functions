# G1 Pre-Cutover Backup — 2026-06-15T12:14:15Z

Operational rollback snapshot taken before the V5 email/function/workflow cutover.
The cutover is **create-new → switch → test → delete-old**, so **all live objects
remain intact until Phase 7** — rollback before Phase 7 = simply do not delete.

## Artifact classification
| File | Type |
|---|---|
| `live_email_templates_list.json` | **Exported live config** — 138 templates (metadata + subjects; bodies NOT in list endpoint, see limitation) |
| `crm_functions_raw.json` | Historical repo dump (pre-V5) — rollback context |
| `crm_workflow_rules_raw.json` | Historical repo dump (pre-V5) — rollback context |
| `_util_resolveContactAction.deluge` | V5 repo source sample (authoritative deploy source = whole `v5/` tree in git) |
| this README | Fresh live inventory + both-ID mapping + limitations |

## Live folders (12) — `getEmailTemplateFolders`
785056 Marketing Consent · 793114 Demo Booking · 784152 Demo Booked(stale) ·
801009 Demo Attended(stale) · 791066 Commercials Sent(stale) · 789131 Commercials Signed(stale) ·
784154 Onboarding · 782059 Renewal · 657008 MQL · 801007 Jurnii Activity Layer ·
…000007 Public Email Templates(system) · …790051 Draft Templates(system).

## Live automation functions (17) — record `id` / nested `function.id`
process Lead 774791/774702 · process Deal 774797/774697 · process Contact 774779/774692 ·
process Account 774785/774687 · handleCallOutcome 780459/780322 · handleTaskCompletion 780448/780337 ·
handleMeetingEvent 780415/780334 · handleDemoOutcome 780410/780328 ·
handleCommercialsStatusChange 780404/780325 · handleEmailEvent 780517/780331 ·
handleEmailReplied 780547/780542 · handleEmailBounced 780554/780522 ·
handleEmailNotReplied 780561/780532 · handleEmailOpenedNotReplied 780568/780537 ·
handleEmailClicked 780574/780527 · **sequenceRouter 780386/780343 (obsolete)** ·
**Convert Lead 543692/543684 (obsolete)**.
(All ids prefixed `991103000000`.)

## Live workflow rules (21) — id · trigger · status (all active)
195001 Big Deal Rule (sample, unrelated) ·
663622 WF001a Process Lead (create_or_edit) · 663630 WF001b Process Contact (create_or_edit, repeat) ·
663648 WF001c Process Account · 663638 WF001d Process Deal ·
796079 WF002 Deal Sequence Router (create_or_edit) [RETIRE] ·
784137 WF003 Stage Change Router (field_update Opportunity_Stage) [RETIRE] ·
800001 WF004 Commercials (field_update Commercials_Status) · 801001 WF005 Demo (field_update Demo_Outcome) ·
808046 WF006 Call (anyaction) · 782052 WF007 Event (create_or_edit) · 784145 WF008 Task (create_or_edit) ·
790073/806019/789167/796107/799022 WF009a-e (Emails outgoing events) ·
800007 WF010a Next_Action_Due_Date [RETIRE] · 800016 WF010b Sequence_Paused_Until [RETIRE] ·
802001 WF010c Demo_Reminder_Send_At [REBIND→sendDemoReminder] ·
790038 WF010d Next_Comm_Follow_Up_Date [REBIND→sendCommercialFollowUp].
Full execute_when criteria captured this session via `getWorkflowRules(include_inner_details=true)`.
Note: WF002/003/010a-d descriptions indicate placeholder/skeleton actions — verify actual
bound actions with `getWorkflowRuleById` before rebind/retire.

## Limitations (documented, NOT blockers)
1. **Live template bodies** are not returned by the list endpoint and were not bulk-exported
   (138 × `getEmailTemplateById` is impractical here). They are **preserved live** by the
   create-new-then-delete strategy and will be exported in a batched pre-deletion run
   immediately before Phase 7 (the only point bodies are needed to restore).
2. **Live Deluge function source** cannot be exported via the function MCP (G4) and the
   self-client token is expired (no refresh creds). Per decision, the **V5 repo (git) is the
   authoritative deploy source**; rollback source = git history + `crm_*_raw.json` historical dumps.
3. Function **code** deploys via Developer Hub / Functions REST API (not MCP); the function MCP
   manages associations/args/delete only.
