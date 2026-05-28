# Antigravity 2.0 Agent Configuration

Welcome to the Zoho CRM Deluge automation repository configuration. This workspace is optimized for the **Antigravity 2.0** agentic engine, using a modular and project-centric structure.

## Agent Team & Personas

For this project, the following agent personas are defined to orchestrate the automation:

*   **Deluge Architect (Lead)**: Specializes in Zoho CRM Deluge syntax, execution limits, workflow triggers, and entity normalization.
*   **Deduplication Engineer**: Specializes in CRM data hygiene, contact matching, and duplicate Account prevention.
*   **Commercial Operations Analyst**: Ensures the Opportunity/Stage commercial ontology is strictly mapped and Deal values/Product Interests are calculated correctly.

---

## High-Level Goal

Fix the current CRM automation so Leads act as a staging/import/input area and are processed into canonical CRM records:

$$\text{Lead} \longrightarrow \text{Contact} + \text{Account} + \text{Deal}$$

The Lead object is not the durable source of truth. **Contacts, Accounts, Deals, and Products** are.

### Main Failures Corrected

1.  **Duplicate Accounts**: Re-assigning existing accounts or using sophisticated lookup priority to prevent bulk-import duplicates.
2.  **Phone Mapping**: Lead Phone must map to Contact Phone only (never Account Phone).
3.  **Missing Deals**: Always attempt to create or reuse a Deal when converting.
4.  **Conversion Gates**: Conversion should happen first. Validation only determines where the record lands in the ontology, not whether it is converted.
5.  **Product Interest**: Correct multi-select staging values and map them to Products via lookup resolution.

---

## Workspace Rules & Skills

This repository uses local workspace configurations to guide agent behavior. The configurations are organized as follows:

*   **Global Rules**: Found in [.agents/rules/deluge-rules.md](file:///c:/Development/Projects/zoho-functions/.agents/rules/deluge-rules.md) and [.agents/rules/powershell-rules.md](file:///c:/Development/Projects/zoho-functions/.agents/rules/powershell-rules.md).
*   **API References**: Found in [.agents/rules/zoho-api-reference.md](file:///c:/Development/Projects/zoho-functions/.agents/rules/zoho-api-reference.md).
*   **On-Demand Skills**: The core refactoring instruction manual is defined in [.agents/skills/zoho-crm-deluge-refactoring/SKILL.md](file:///c:/Development/Projects/zoho-functions/.agents/skills/zoho-crm-deluge-refactoring/SKILL.md).
*   **Automated Workflows**: Chained slash command pipelines are defined in [.agents/workflows/deluge-refactor-workflow.md](file:///c:/Development/Projects/zoho-functions/.agents/workflows/deluge-refactor-workflow.md).

---

## Commercial Ontology Map

### 1. Opportunity Values
*   `MQL` (Marketing Qualified Lead): Initial intake.
*   `SQL` (Sales Qualified Lead): Validated consent or booked/attended demo.
*   `FTP` (First Time Purchase): Moving into commercials.
*   `RTP` (Retention Purchase): Signed commercials, onboarding, and renewal.

### 2. Stage Values
*   `Marketing Consent`
*   `Demo Booking`
*   `Demo Booked`
*   `Demo Attended`
*   `Commercials Sent`
*   `Commercials Signed`
*   `Onboarding`
*   `Renewal`

### 3. State & Status
*   **State**: `Open` or `Lost` (Do not use `Won` as a persistent State).
*   **Status**: `New`, `Working` (if manual activities exist), or `Closed` (only if State is `Lost`).

---

## Core Operational Files

The following files constitute the automated workflow pipeline:

1.  [convert2lead.deluge](file:///c:/Development/Projects/zoho-functions/convert2lead.deluge): Intake processor.
2.  [normalizeContactCommercialState.deluge](file:///c:/Development/Projects/zoho-functions/normalizeContactCommercialState.deluge): Person-level normalization.
3.  [normalizeDealCommercialState.deluge](file:///c:/Development/Projects/zoho-functions/normalizeDealCommercialState.deluge): Deal-level normalization.
4.  [syncDealProductsAndValue.deluge](file:///c:/Development/Projects/zoho-functions/syncDealProductsAndValue.deluge): Product lookup and Deal Amount summation.
5.  [rollupAccountCommercialState.deluge](file:///c:/Development/Projects/zoho-functions/rollupAccountCommercialState.deluge): Account-level aggregate state and status.
