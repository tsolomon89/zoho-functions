# WORKFLOW_CONSOLIDATION_MATRIX.md — V5 Final Corrected

## Summary

```
Before:  18–20 workflow rules
After:   17 workflow rules
Retired:  4 rules
New:      1 rule (WF010d sendCommercialFollowUp)
```

---

## Retained Workflows (17)

| # | Rule | Module | Trigger | Function |
|---|------|--------|---------|----------|
| 1 | WF001 | Leads | Create/Edit | `processLead` |
| 2 | WFC-Contact | Contacts | Create OR Edit (specific fields) | `processContact` |
| 3 | WFC-Account | Accounts | Create/Edit | `processAccount` |
| 4 | WFC-Deal | Deals | Create/Edit (All Records) | `processDeal` |
| 5 | WF004 | Deals | `Commercials_Status` changed | `handleCommercialsStatusChange` |
| 6 | WF005 | Deals | `Demo_Outcome` changed | `handleDemoOutcome` |
| 7 | WF006 | Calls | Create/Edit + criteria | `handleCallOutcome` |
| 8 | WF007 | Events | Create/Edit + criteria | `handleMeetingEvent` |
| 9 | WF008 | Tasks | Edit (Status/Task_Outcome) + criteria | `handleTaskCompletion` |
| 10 | WF009a | Emails | Outgoing/Replied | `handleEmailReplied` |
| 11 | WF009b | Emails | Outgoing/Bounced | `handleEmailBounced` |
| 12 | WF009c | Emails | Outgoing/Unreplied (3d) | `handleEmailNotReplied` |
| 13 | WF009d | Emails | Outgoing/Open+Unreplied (3d) | `handleEmailOpenedNotReplied` |
| 14 | WF009e | Emails | Outgoing/Clicked | `handleEmailClicked` |
| 15 | WF010c | Deals | Date: `Demo_Reminder_Send_At` | `sendDemoReminder` |
| 16 | WF010d | Deals | Date: `Next_Comm_Follow_Up_Date` | `sendCommercialFollowUp` |
| 17 | WFC-SchedEmail | Tasks | Date: `Due_Date` + criteria | `sendScheduledEmailFromTask` |

---

## Retired (4)

| Rule | Reason |
|------|--------|
| WF002 — Deal Sequence Router | `Sequence_Status` on Deals is dead |
| WF003 — Deal Stage Change Router | Reverses Contact-centric authority |
| WF010a — Next Action Due Date | Zero V5 writes |
| WF010b — Sequence Paused Until | Zero V5 writes |

---

## Dead Deal Fields (actual CRM deletion candidates)

Only these Deal fields are deletion candidates after verified retirement:

| Field | API Name | V5 replacement |
|-------|----------|----------------|
| Sequence Status | `Sequence_Status` | Contact.Sequence_State |
| Sequence Paused Until | `Sequence_Paused_Until` | Task due dates |
| Next Action Due Date | `Next_Action_Due_Date` | Task due dates |

**Note**: `Opportunity_Stage` is NOT a deletion candidate. It is a stale code identifier for `Opportunity_Stage`, not a separate CRM field.
