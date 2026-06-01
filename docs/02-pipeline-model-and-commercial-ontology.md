# Jurnii.io CRM: Pipeline Model and Commercial Ontology

## TL;DR

Jurnii.io operates a structured, four-field commercial ontology to monitor and manage customer progression. By cleanly separating the broad commercial motion (**Opportunity**) from the immediate operational milestone (**Stage**), the CRM drives precise forecasting. Crucially, "Won" is treated not as a permanent state, but as a transitional gate event that advances a customer into onboarding and retention.

---

## What This Covers

This document details Jurnii.io's pipeline model for commercial leadership. It explains:
*   **The Four Key Commercial Fields**: Opportunity, Stage, State, and Status.
*   **The Stage-to-Opportunity Mapping**: How the operational steps feed into broad pipeline buckets.
*   **The Mechanics of State and Status**: Why "Won" is a transitional gate rather than a dead-end state.
*   **Module-Specific Ontology**: How these fields behave across Leads, Contacts, Deals, and Accounts.

---

## The Four Key Commercial Fields

Our CRM uses four core fields to track every stage of the customer lifecycle. These fields prevent manual rep reporting errors and establish a standardized commercial vocabulary:

| Concept | API Field | Question It Answers | Allowed Values / Notes |
| :--- | :--- | :--- | :--- |
| **Opportunity** | `Stage` | **What broad commercial motion is this record in?** | `MQL`, `SQL`, `FTP`, `RTP` |
| **Stage** | `Stage1` | **What specific step are we trying to complete next?** | `Marketing Consent`, `Demo Booking`, `Demo Booked`, `Demo Attended`, `Commercials Sent`, `Commercials Signed`, `Onboarding`, `Renewal` |
| **State** | `State` | **Is this commercial motion still active or lost?** | `Open` (active motion), `Lost` (motion closed unsuccessfully) |
| **Status** | `Status` | **Is this active record untouched, being worked, or closed?** | `New` (no manual activity), `Working` (meaningful manual activity exists), `Closed` (only when `State = Lost`) |

*   *Evidence*: `spec.md`, `v4/processLead.deluge`, `v4/processContact.deluge`, `v4/processDeal.deluge`

---

## The Stage-to-Opportunity Mapping

The specific operational `Stage` (`Stage1`) dynamically drives the broad `Opportunity` bucket (`Stage`). As a prospect passes operational milestones, they automatically progress through Jurnii.io's commercial buckets:

| Stage Rank | Stage / Current Step | Opportunity Bucket | Commercial Meaning |
| :---: | :--- | :--- | :--- |
| **1** | `Marketing Consent` | `MQL` | Prospect has consented to marketing and entered our intake queue. |
| **2** | `Demo Booking` | `SQL` | Sales reps are actively trying to schedule an initial demo. |
| **3** | `Demo Booked` | `SQL` | A demo has been successfully scheduled on the calendar. |
| **4** | `Demo Attended` | `SQL` | The demo has occurred, and the sales qualification is still active. |
| **5** | `Commercials Sent` | `FTP` | **First-Time Purchase (FTP)** motion begins. The prospect has received contract terms and is reviewing a proposal. |
| **6** | `Commercials Signed` | `RTP` | **Retention Purchase (RTP)** motion begins. The contract is signed, shifting the prospect into client status. |
| **7** | `Onboarding` | `RTP` | The customer is being technically activated and integrated. |
| **8** | `Renewal` | `RTP` | The customer is in a active subscription phase, approaching renewal or expansion. |

*   *Evidence*: `spec.md`, `v4/processLead.deluge` (lines 327–333), `v4/processContact.deluge` (lines 398–401)

---

## Core Ontology Principles for Leadership

Understanding these three principles is essential to interpreting Jurnii.io's pipeline reports:

### 1. "Won" is a Gate Event, Not a Stable State
In standard CRM systems, deals are marked "Closed Won" and archived. This isolates historical customers and breaks communication tracking.
*   **Our Model**: We do not use "Won" as a permanent state. When a gate is passed, the Deal is **promoted** to the next commercial phase. 
*   **Example**: Signing the contract does not close the Deal; it moves the Deal from `FTP / Commercials Sent` into the `RTP / Onboarding` phase, keeping the record active and monitored by customer success workflows.
*   *Evidence*: `spec.md` (lines 68–79)

### 2. Commercials Sent is the FTP Boundary
A prospect is only counted in the **First-Time Purchase (FTP)** pipeline after commercial terms have actually been generated and sent to them. Up until that exact moment, they remain in the qualification phase (`SQL`).
*   *Evidence*: `spec.md` (lines 110–116), `v4/activity/handleCommercialsStatusChange.deluge`

### 3. Status Represents True Manual Engagement
A record is only marked `Working` if a representative is performing **meaningful manual activity** (e.g., executing manual tasks, holding meetings, or handling a custom negotiation).
*   **Workflows Do Not Touch Status**: Automated background sequences, automated emails, and routine system updates **never** set `Status = Working`—they keep the record in its standard system state (`New` or `Waiting`).
*   *Evidence*: `spec.md` (lines 89–100)

---

## How Mappings Differ Across CRM Objects

The commercial ontology operates slightly differently depending on the module, ensuring data flows correctly from staging into reporting:

*   **Leads (Staging Layer)**:
    *   Holds `Initial_Stage` and `Initial_Opportunity` fields.
    *   These act strictly as temporary staging inputs. When the Lead is converted, the reconciler reads these fields to bootstrap the permanent Contact and Deal records.
    *   *Evidence*: `v4/processLead.deluge`
*   **Contacts (Individual Layer)**:
    *   Each Contact has a `Stage` and `State` (e.g., Contact A is booking a demo, while Contact B has attended).
    *   These fields track the progress of **individual stakeholders** within a prospect company.
    *   *Evidence*: `v4/processContact.deluge`
*   **Deals (Deal Pipeline Layer)**:
    *   The Deal is the absolute **source of truth** for the company's active commercial status.
    *   The Deal’s `Stage1` and `Stage` are dynamically calculated based on the **furthest open Contact** under that Account. It represents the overall progress of the account negotiation.
    *   *Evidence*: `v4/processDeal.deluge`
*   **Accounts (Company Rollup Layer)**:
    *   Accounts do not have detailed stages. They hold high-level `State` (`Open` / `Lost`) and `Status` (`New` / `Working` / `Closed`) fields.
    *   These fields roll up the aggregate state of all active deals under that company to provide an executive view of our client relationships.
    *   *Evidence*: `v4/processAccount.deluge`
