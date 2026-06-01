# 05 — Setup and Open Items

## TLDR
This playbook outlines what is built, what requires manual setup in the Zoho UI, and the safe rollout order for commercial leadership.

Evidence: `.agents/context/activity-workflows/WORKFLOW_CONFIGURATION_CHECKLIST.md`, `.agents/context/activity-workflows/TEMPLATE_NAMING_MATRIX.md`

---

## Launch Playbook Checklist

The following actions must be completed before go-live:

| Item | Status | Owner / Next action |
| :--- | :--- | :--- |
| **Core Deluge functions** | Built / needs verification | Test in Zoho using sample data records. |
| **Workflow rules** | Mapped | Enable in the Zoho UI (sequential activation). |
| **Email templates** | Naming and routing mapped | Write actual template text copy inside Zoho. |
| **Product catalog** | Required | Confirm active Products list and check unit prices. |
| **Existing records** | Needs backfill decision | Mass-update `Sequence_Status = Not Started` to enroll. |
| **Suppression rules** | Required | Set `Automation_Suppressed = true` on manual records. |

---

## Safe Launch Order

Workflows must be activated sequentially in this exact order to prevent race conditions or duplicate call creation:

1.  **Phase 1 (Intake)**: Turn on `WF001` (Lead Processor). This converts Leads when marked ready into clean, non-automated Accounts, Contacts, and Deals.
2.  **Phase 2 (Human Call Gates)**: Turn on `WF002`, `WF003`, `WF006` (Call Outcome), and outcome handlers `WF004` and `WF005`. This allows representatives to drive deals and schedule sequential Calls manually.
3.  **Phase 3 (Outreach & Scheduling)**: Turn on `WF007` (Meetings), `WF008` (Tasks), the date scheduler `WF010`, and the email reply/bounce intercepts (`WF009`). This fully automates our email follow-up chaser sequences.

---

## Open Technical Realities

Leadership must understand these system realities:

*   **Connection Dependency**: The automated email engine relies on a custom connection named **`zoho_crm`** in our Zoho Developer Hub. If the connection permissions expire, automated emails will fail to send.
    *   *Required Scopes*: `ZohoCRM.modules.contacts.UPDATE`, `ZohoCRM.modules.contacts.READ`, `ZohoCRM.modules.contacts.send_mail`
*   **Zoho UI Outgoing Email Trigger API Limitation**: Zoho's API does not support configuring outgoing email event rules (`WF009`). These rules **must be configured manually in the Zoho UI** following the exact parameters in our configuration checklist.
    *   *Reference*: `activity-workflows/WORKFLOW_CONFIGURATION_CHECKLIST.md` (lines 133–147)
*   **Activity Picklist Rule**: Because Zoho CRM prevents true checkbox fields on Activities (Calls, Tasks, Events), fields like `Sequence_Managed` are custom picklists set to `Yes` / `No`. Sales reps must not alter these values.
    *   *Reference*: `activity-workflows/FIELD_REUSE_NOTES.md` (lines 60–68)
