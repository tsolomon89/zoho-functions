# VERIFICATION_PLAN.md — End-to-end verification before production rollout

## Purpose

Concrete, ordered steps to verify the activity-workflows execution pack
in a Zoho sandbox before turning workflows on in production. Covers
field model correctness, hook integration, the 20-case TEST_CASES.md
plan, idempotency, and the stale-email guard.

Do not skip steps — each verifies a layer that masks downstream failures
if left unchecked.

---

## 0 — Sandbox prep

- [ ] Refresh sandbox from production (or start from a clean org).
- [ ] Run `zoho_custom_fields_by_module.csv` field creation. Replace
      every `TBD_API_NAME` with the actual API name as you create the
      field; keep the CSV updated as the source of truth.
- [ ] Re-export `.agents/context/api_field_names/*.csv` after creation.
      Diff against the spec; the diff should be empty for every CREATE
      row.
- [ ] Publish all 14 Deluge functions + 4 utils to the sandbox.
- [ ] Create all 79 templates from `TEMPLATE_CREATION_CHECKLIST.md`.
- [ ] Configure connection `zoho_crm` (scopes per
      `WORKFLOW_CONFIGURATION_CHECKLIST.md` pre-flight).
- [ ] Leave **all 10 workflows OFF** for steps 1-3.

## 1 — Hook smoke test (workflows still OFF)

Goal: confirm the v3 → activity hook fires without workflow help.

- [ ] Open Setup → Developer Hub → Functions → `processLead`. Run with a
      seeded Lead ID from `test_data/zoho_lead_workflow_test_upload.csv`.
- [ ] In the Function logs, search for `sequenceRouter hook (processLead)`.
- [ ] Then `automation_event func=sequenceRouter ... action=bootstrap outcome=success`.
- [ ] Then `automation_event func=createStageCall ... action=create outcome=success`.
- [ ] In the CRM, navigate to the canonical Deal that was created.
      Verify:
      - [ ] `Sequence_Status` = `Waiting on Call`
      - [ ] `Active_Sequence_Stage` = `Marketing Consent` (or the Stage1
            value set by processLead)
      - [ ] `Active_Sequence_Attempt` = 1
      - [ ] An associated Call exists with `Subject` = `Marketing Consent Call 1`,
            `Sequence_Managed` = true, `Sequence_Attempt` = 1, `Stale` = false.
- [ ] Re-run `processLead` on the same Lead ID. Verify **no** duplicate
      Call is created (the `createStageCall` duplicate-prevention search
      returns the existing Call's ID).

## 2 — Field model audit

Walk the 8 modules in `zoho_custom_fields_by_module.csv` once more,
now in the sandbox UI:

- [ ] **Deals**: Stage1, Stage, State, Status, all 35 new custom fields
      listed in the CSV.
- [ ] **Calls**: all 11 fields (10 spec + 1 `Stale`).
- [ ] **Events**: all 9 fields.
- [ ] **Tasks**: all 8 fields.
- [ ] **Contacts**: 6 new + 1 new picklist (`Marketing_Consent_Status`).
      Legacy Boolean `Marketing_Consent` still present.
- [ ] **Leads**: all 8 fields.
- [ ] **Accounts**: all 7 fields including new `Account_Status` picklist
      distinct from existing `Status`.
- [ ] **Products**: all 6 fields including new `Active_for_Deal_Automation`
      distinct from existing `Product_Active`.

## 3 — Turn workflows ON one at a time

Order from `WORKFLOW_CONFIGURATION_CHECKLIST.md`:

- [ ] **WF001** Lead Processor — on. Re-run T1 (new Lead) below.
- [ ] **WF002** Deal Sequence Router — on. Manually create a Deal with
      `Stage1` set, `Sequence_Status` empty; confirm Call 1 appears.
- [ ] **WF003** Stage Change Router — on. Manually change Stage1 on the
      Deal above; confirm old Call goes `Stale`, new Call 1 created for
      new Stage.
- [ ] **WF006** Call Outcome Handler — on. Set Call_Outcome = No Answer;
      confirm email sent (look at Last_Email_Template), Call 2 created.
- [ ] **WF004** Commercials Status Handler — on. Set Commercials_Status =
      Sent; confirm Stage1 → Commercials Sent, Opportunity → FTP,
      Commercials Sent Terms Email sent, Commercials Sent Call 1 created.
- [ ] **WF005** Demo Outcome Handler — on. Set Demo_Outcome =
      Attended - Qualified; confirm Stage1 → Demo Attended,
      Commercials_Status = Drafting, Draft Commercials task created,
      Demo Attended Post-Demo Email sent.
- [ ] **WF007/008/009/010** — on as needed; see test cases 8, 13, 15,
      16 below for verification.

## 4 — TEST_CASES.md run sheet

The numbered tests below correspond 1-to-1 with the cases in
`TEST_CASES.md`. Run in order; each builds confidence in the next.

- [ ] **T1** New Lead with complete data → graph created, Call 1, no email.
- [ ] **T2** Existing Contact and Account, no Deal → Deal created,
      Contact linked, Call 1, no email.
- [ ] **T3** Existing Contact/Account/Deal → no dupes, sequence consistent.
- [ ] **T4** Product lookup fails → graph still created;
      `Product_Resolution_Status` set; sequence does not crash.
- [ ] **T5** Imported Deal at Commercials Sent → Sequence initialized,
      Commercials Sent Call 1 only, no chase email.
- [ ] **T6** Demo Booking Call 1 = No Answer → Demo Booking Email 1 sent,
      Call 2 created, attempt incremented.
- [ ] **T7** Demo Booking Call 1 = Positive → Stage1 = Demo Booked, old
      sequence superseded, new Demo Booked sequence starts; no stale
      Demo Booking Email 1 fires.
- [ ] **T8** Demo reminder → Reminder Send At = -1 business day AM;
      reschedule recomputes.
- [ ] **T9** Demo Outcome = Attended - Qualified → Stage Demo Attended,
      Post-Demo Email, Draft Commercials task, Commercials Status =
      Drafting. Stage does NOT advance to Commercials Sent.
- [ ] **T10** Commercials Status = Sent → Stage Commercials Sent,
      Opportunity FTP, Call 1 due +2 business days, no chase email yet.
- [ ] **T11** Commercials Sent Call 1 = Deferred → Sequence Deferred,
      Paused Until = Next Follow-Up Date.
- [ ] **T12** Commercials Sent Call 1 = No Answer → Email 1, Call 2,
      Stage unchanged.
- [ ] **T13** After Call 5 → 7-email chain begins; chain stops on Stage
      change or Sequence_Superseded_At set.
- [ ] **T14** Stage manually changed → old Sequence superseded, pending
      Calls marked Stale, old emails do NOT send.
- [ ] **T15** Email reply received → Review Reply task; sequence paused;
      no auto-positive.
- [ ] **T16** Email bounced → Data Repair task; sequence paused; no
      further emails sent.
- [ ] **T17** Do Not Contact → Automation_Suppressed = true,
      Suppression_Reason set, Sequence Suppressed, no further work.
- [ ] **T18** Already Handled → current step marked complete; no
      irrelevant email.
- [ ] **T19** Not Relevant → manual review task; no auto email.
- [ ] **T20** Renewal flow → Renewal Call 1, no email until outcome;
      positive renews/expands; no-answer sends Renewal Email 1 + Call 2.

## 5 — Idempotency assertions

For each of T1, T6, T10:

- [ ] Re-trigger the same source action (re-run processLead, re-set
      Call_Outcome, re-set Commercials_Status).
- [ ] Confirm:
      - No duplicate Contacts / Accounts / Deals.
      - No duplicate open Calls at the same (Stage, Attempt).
      - No duplicate Tasks of the same Task_Type for the same Deal.
      - No duplicate emails (check Last_Email_Sent_At did not move
        backwards or duplicate against the same template).

## 6 — Stale-email guard

- [ ] Trigger T7 (Demo Booking Call 1 = Positive → Stage = Demo Booked).
- [ ] Immediately wait 1 minute and verify NO `Demo Booking Email 1`
      send is logged. Check `Last_Email_Template` on the Deal — it must
      not equal "Demo Booking Email 1" with a timestamp after the Stage
      change.
- [ ] Repeat with a manual Stage change: set Stage1 from `Demo Booking`
      to `Demo Booked` directly; confirm same guard.

## 7 — Production rollout sequence

Only proceed to production once steps 0-6 pass in sandbox.

- [ ] Repeat step 0 (field creation, function publish, template create,
      connection setup) in production.
- [ ] **Migration backfill** per `FIELD_REUSE_NOTES.md` §"Migration
      safety notes":
      - `Sequence_Status = Not Started` on Open Deals that should enter
        the new flow.
      - `Automation_Suppressed = true` on every Deal currently being
        worked manually that should NOT enter the new flow.
- [ ] Turn WF001-WF006 on in the order from
      `WORKFLOW_CONFIGURATION_CHECKLIST.md`, with a 24-hour observation
      window between each.
- [ ] Turn WF007-WF010 on once WF001-WF006 are stable.

## 8 — Observability checklist

- [ ] Build a Function Log filter / saved search for
      `automation_event func=` lines.
- [ ] Build a dashboard view of Deals where:
      - `Sequence_Status` = `Suppressed` and `Suppression_Reason` is
        empty (config drift).
      - `Active_Sequence_Stage` != `Stage1` and
        `Sequence_Superseded_At` is empty (failed supersede).
      - `Sequence_Status` = `Waiting on Email Trigger` and
        `Next_Action_Due_Date` < now (stuck post-call chain).
- [ ] Add a daily alert when `automation_event ... outcome=failed`
      count > 10 in 24h.
