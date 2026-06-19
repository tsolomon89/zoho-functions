# README_EXECUTION_PACK.md — Zoho CRM Automation Execution Pack

## Files in this pack

| File | Purpose |
|---|---|
| `AGENTS.md` | Master agent context and architecture rules |
| `ZOHO_FIELD_MAP.md` | Field creation/API-name mapping document |
| `WORKFLOW_TRIGGER_MAP.md` | Workflow rules and function-trigger map |
| `FUNCTION_SPEC.md` | Function-level implementation specification |
| `TEST_CASES.md` | QA/test plan |
| `TEMPLATE_NAMING_MATRIX.md` | Email template naming and purpose map |

---

## Existing CSVs also required

Use these alongside this Markdown pack:

| CSV | Purpose |
|---|---|
| `zoho_custom_fields_by_module.csv` | Custom field creation checklist |
| `stage_day_sequence_matrix_call_first_30_days.csv` | Day-indexed stage sequence matrix |

---

## Implementation order

1. Create/verify custom fields.
2. Fill in actual Zoho API names in `ZOHO_FIELD_MAP.md`.
3. Confirm module/related-list API names.
4. Create templates using `TEMPLATE_NAMING_MATRIX.md`.
5. Implement helper/upsert functions.
6. Implement Deal sequence router.
7. Implement Call outcome handler.
8. Implement Demo and Commercial handlers.
9. Configure workflows using `WORKFLOW_TRIGGER_MAP.md`.
10. Run tests in `TEST_CASES.md`.

---

## Non-negotiable rule

Every Stage starts with Call 1.

No customer-facing email should be sent merely because a record was imported, created, converted, or assigned a Stage.

Emails are downstream of activity state, especially call outcome.
