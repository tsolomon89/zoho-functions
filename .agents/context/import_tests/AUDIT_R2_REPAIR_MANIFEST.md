# R2 Repair + Deployment Manifest (2026-06-24)

Repairs for the four E2E gate findings (F1–F4) + timestamp classification. **Hard constraint: Deluge function source cannot be deployed via MCP** (the function-CRUD tools carry only metadata — no `script`/`body`). Repo edits below are the deployable source of truth; **the user must republish** each changed function. The new `_util_resolveDealPipeline` must be **created** as a function in the org and its code pasted in.

## Live metadata change (DONE — verified live)
- **Created `Tasks.Task_Sequence_Stage`** — picklist, field id **991103000001842018**, API name `Task_Sequence_Stage`. Values = canonical 8 stages: Marketing Consent, Demo Booking, Demo Confirmation, Demo Hosted, Proposal Preparation, Commercial Agreement, Onboarding, Renewal. Verified: write "Demo Confirmation" persisted + read back via COQL; available to record CRUD. (Chosen to mirror `Contact.Stage` — the value the code compares against — NOT the legacy stale picklist on `Task_Stage`/`Calls.Sequence_Stage` which still read `Demo Booked/Demo Attended/Commercials Sent/Commercials Signed/Renewall`; that legacy set is a separate cleanup.)
- **No Deal field created** for product interest (F1 decision): the canonical path is `Contact.Product_Interest_Staging` → activity `*_Contract_Products` → Quote/Quoted_Items → `Deal.Contract_*_Plan_Products`. `Deals.Product_Interest_Staging` is intentionally NOT created.

## Deployment manifest

| Function | Changed? | Reason | Must republish? | Published? |
|---|---|---|---|---|
| **_util_resolveDealPipeline** (NEW) | Yes (new file) | F3 shared resolver: Deluge `getRecordById` omits Pipeline; fetch via REST `?fields=Pipeline`, validate vs picklist, log unmapped | **CREATE + deploy** | ☐ |
| **processContact** | Yes | F4 (activation Task gets Task_Stage/Pipeline/Opportunity/State/Status) + F3 (resolver) + TZ fix (completion stamp `'Z'`) | **Yes** | ☐ |
| **routeContactSequence** | Yes | F3 (mirrorPipeline via resolver) + TZ fix (completion stamp + immediate Call_Start_Time `'Z'`) | **Yes** | ☐ |
| **sendSequencedEmail** | Yes | F3 (emPipeline via resolver) — fixes email-audit Task_Pipeline | **Yes** | ☐ |
| **createAuxTask** | Yes | F3 (auxPipeline via resolver) | **Yes** | ☐ |
| **handleMeetingEvent** | Yes | F3 (Meeting_Task_Pipeline via resolver) | **Yes** | ☐ |
| **handleCallOutcome** | Yes | F3 (rescheduled/next Call pipeline via resolver) | **Yes** | ☐ |
| **processLead** | Yes | F1 (remove dead `Deals.Product_Interest_Staging` write). Republish ALSO activates the existing D4 Contact-staging fix if the deployed copy predates it | **Yes** | ☐ |
| **processDeal** | Yes | F1 (remove dead `Deals.Product_Interest_Staging` write) + TZ fix (completion stamp `'Z'`) | **Yes** | ☐ |
| **handleTaskCompletion** | No (code) | Reads `Task_Sequence_Stage` for stale-stage guard / activation dedup. Behavior now ACTIVATES because the field exists. Republish only if the deployed copy predates the repo refs | Verify (likely No) | n/a |
| **sendScheduledEmailFromTask** | No | Unchanged; obsolete-email protection is via supersede-cancel on stage advance (routeContactSequence) | No | n/a |

## Timestamp classification (item 5)
**Conclusion: genuine ~1-hour stored-instant error (NOT correct-UTC-mislabelled-as-display).** Proof: live Contact `991103000001817003` has native `Created_Time=07:56:33+01:00` but `Contact_Completed_Marketing_Qualification_At=06:56:35+01:00` — a completion stamped an hour *before* the Contact existed; Demo Booking/Onboarding stamps likewise 1h behind native timestamps. Root cause: `zoho.currenttime` returns **UTC-valued components** in this org's Deluge runtime, and `toString("…XXX")` appended the org offset `+01:00` to those UTC components, shifting the instant back 1h. Fix: serialize as UTC (`'Z'`) at the three completion-stamp sites (processContact, processDeal, routeContactSequence) + the immediate `Call_Start_Time`. **Must be re-verified live post-deploy** (zoho.currenttime TZ behavior is environment-dependent and untestable via MCP). Lower-risk siblings left unchanged: scheduled/reminder dates (handleMeetingEvent:225, routeContactSequence:1143) build a *local wall-clock target* string and are correct; processLead:68–138 reformat pre-existing Lead datetimes.

## R2 regression — BLOCKED on republication
R2-1…R2-7 validate republished code behavior and cannot run until the table above is deployed. After republish, run R2 with identifier `E2E-R2-20260624` / `t.l.c.solomon+E2E-R2-20260624@gmail.com` (use a distinct Company to avoid Account_Key collision with the morning `E2E TEST - 20260624 R2` leftovers).
