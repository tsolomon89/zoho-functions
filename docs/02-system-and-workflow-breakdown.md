# Jurnii.io CRM: System and Workflow Breakdown

## TL;DR

This document provides a clear breakdown of the core commercial rules (invariants) and the data flow in Jurnii.io's v4 CRM architecture. It explains how the system maintains data integrity by automatically linking contacts, deduping accounts and deals, resolving product values, and ensuring that human actions and automated workflows work in perfect harmony.

---

## What This Covers

*   **The Invariant Rules**: The absolute laws of our CRM database (Accounts, Deals, Contacts, Roles, Products).
*   **The Reconciler Pipeline**: How the system processes data behind the scenes.
*   **Workflow Trigger Architecture**: The interaction between Zoho UI Triggers (Workflow Rules) and Deluge script logic.
*   **Cascade and Race Condition Protection**: How the CRM stops automated scripts from infinitely triggering each other.

---

## Core Operational Rules (The Invariants)

The CRM system is governed by a set of strict, automated rules. Every time a record is created or edited, the database is forced to comply with these rules:

### 1. The "One Canonical Account" Rule (Deduplication Tree)
To prevent duplicate accounts for the same company, the system resolves account identities using a strict **4-stage lookup tree**:

```text
    Stage 1: Account_Key
    Matches the unique, derived key (e.g. "acme.com" extracted from Website or Email domain).
          │
          ├──► Found? Re-use Account.
          └──► Not Found? Flow to Stage 2.
                │
                ▼
    Stage 2: Website Domain
    Matches the raw website field (e.g. "www.acme.com" matches "acme.com").
          │
          ├──► Found? Re-use Account. Update Account_Key.
          └──► Not Found? Flow to Stage 3.
                │
                ▼
    Stage 3: Normalized Company Name
    Matches the exact company name after stripping special characters (e.g., "Acme, Inc." matches "Acme Inc").
          │
          ├──► Found? Re-use Account. Update Account_Key.
          └──► Not Found? Flow to Stage 4.
                │
                ▼
    Stage 4: Automated Creation
    Creates a new canonical Account and stamps the unique Account_Key to prevent future duplicates.
```

### 2. The "One Active Deal" Rule
An Account must never have multiple active Deals. The active Deal represents the current, singular commercial motion with that company.
*   **If multiple active Deals exist**: The system identifies the **oldest Deal** (by ID) as the canonical active Deal.
*   **Silencing Duplicates**: All other active deals are marked duplicate. The system updates them to `State = Lost`, `Status = Closed`, `Reason_For_Loss = Duplicate / Test Record`, appends `(Duplicate)` to the Deal Name, and clears their key to release it to the canonical deal.
*   **Business Benefit**: Ensures a clean, non-inflated pipeline. Representatives work inside one shared Deal record rather than multiple disjointed ones.

### 3. The "Furthest Contact" Rule
A Deal's stage comes from the furthest viable open Contact under the Account. The system ranks stages from 1 (coldest) to 8 (closest to signature):

| Rank | Stage Name (`Stage1` API Field) | Opportunity Category (`Stage` API Field) | What It Represents |
| :--- | :--- | :--- | :--- |
| **1** | `Marketing Consent` | **MQL** (Marketing Qualified Lead) | Prospect has agreed to marketing communication. |
| **2** | `Demo Booking` | **SQL** (Sales Qualified Lead) | Booking outreach is in progress. |
| **3** | `Demo Booked` | **SQL** (Sales Qualified Lead) | Demo is scheduled. |
| **4** | `Demo Attended` | **SQL** (Sales Qualified Lead) | Demo occurred; qualified for next steps. |
| **5** | `Commercials Sent` | **FTP** (First Time Purchase) | Proposal and contract are sent to the client. |
| **6** | `Commercials Signed` | **RTP** (Retention Purchase) | Contract is signed; entering commercials. |
| **7** | `Onboarding` | **RTP** (Retention Purchase) | Client is being set up in the Jurnii.io system. |
| **8** | `Renewal` | **RTP** (Retention Purchase) | Client is up for renewal/expansion. |

*   **Deal Promotion**: If a new Contact under the same Account advances (e.g., from `Demo Booking` to `Demo Attended`), the Deal is automatically promoted.
*   **Primary Contact Selection**: The furthest open Contact is designated as the primary `Contact_Name` on the Deal.
*   **Lost Contacts Do Not Pull Deals Back**: If one Contact is "Lost" but another Contact under the same Account is still "Open", the Deal remains **Open** and is driven by the open contact. The Deal only closes as Lost when **all** contacts under that Account are marked Lost or the Deal itself has an explicit loss reason.

### 4. Automated Contact Roles (`Contact_Roles`)
Every Contact under the Account is automatically attached to the Deal's `Contact_Roles` related list. The role is derived from their `Job_Title` field:
*   **Precedence Tree**: If a title maps to multiple roles, the system awards the most senior role: **Decision Maker** > **End User** > **Influencer**.
*   **Fallback**: If `Job_Title` is blank or has no match, it defaults to **Decision Maker**.
*   **Manual Overwrite Protection**: The system **never** overwrites a role that a sales rep has manually adjusted in the Zoho UI.

### 5. Product Catalog Resolution
Prospect product interest is captured as plain text during lead capture. The system:
1.  Takes the **union** of product interests across the triggering Lead, all Account Contacts, and the existing Deal.
2.  Searches our live **Zoho Products Module** for active matches (whitespace and case-tolerant).
3.  Attaches the resolved products to the Deal.
4.  **Sums their Unit Prices** and automatically stamps the total into the `Deal.Amount` field.
5.  *Cascade Protection*: When recalculating, the system sums existing line-item prices first, preventing accidental $0 rewrites on mid-stage updates.

---

## Trigger Layer vs. Logic Layer

Our automation separates the **Trigger (When it happens)** from the **Logic (What happens)**:

```text
  ZOHO CRM UI TRIGGERS                                     DELUGE LOGIC ENGINE
 ┌──────────────────────┐                                 ┌─────────────────────────┐
 │  WF001 (Leads)       │ ───────► (lead_id) ───────────► │  automation.processLead │
 ├──────────────────────┤                                 ├─────────────────────────┤
 │  WF002 (Deals)       │ ───────► (deal_id) ───────────► │  automation.processDeal │
 ├──────────────────────┤                                 ├─────────────────────────┤
 │  WF006 (Calls)       │ ───────► (call_id) ───────────► │  handleCallOutcome      │
 └──────────────────────┘                                 └─────────────────────────┘
```

*   **The Trigger Layer (Zoho UI Workflow Rules)**: Dumb gates configured in the Zoho CRM administration panel. They monitor field changes (e.g., "Demo_Outcome changed") and invoke the matching Deluge script.
*   **The Logic Layer (Deluge Script Library)**: Published functions in Zoho's backend. They perform complex database lookups, query-related lists, and execute calculations that Zoho's basic UI cannot do.

---

## Step-by-Step Lead Conversion Process

When a Lead is marked "Ready for Conversion", the intake pipeline executes the following transitions to enforce our data rules:

| Step | Operation | Action & Enforced Database Rule |
| :---: | :--- | :--- |
| **1** | **Identify Account** | Checks Website and Email domains against the unique `Account_Key` tree to find a match. Reuses an existing Account if found; otherwise, creates a new Account. |
| **2** | **Convert Contact** | Standard Zoho Lead conversion creates the Contact and links them to the resolved Account ID. |
| **3** | **Check Active Deal** | Checks the Account for an active Deal (using `accountKey::active`). Reuses the existing Deal if found; otherwise, creates a new one. |
| **4** | **Silence Duplicates** | If multiple active Deals are found, the oldest is kept as canonical, and others are silenced (State=Lost, Status=Closed). |
| **5** | **Populate Roles** | Scans all Contacts under the Account and adds them to `Contact_Roles` on the Deal, mapping job titles to roles. |
| **6** | **Resolve Products** | Resolves plain-text product interests against the live Product catalog, attaches them, and sums their prices into `Deal.Amount`. |
| **7** | **Roll Up Stage** | Scans all open Contacts, picks the furthest Stage, sets `Deal.Stage1` and `Deal.Stage`, and designates them as the Deal primary Contact. |
| **8** | **Account Roll Up** | Aggregates all Deal states under the Account to roll up the Account `State` and `Status` (Open/Lost/New/Working). |

---

## Workflow Cascade Protection (The Suppression Map)

Because our 4 core modules (Lead, Contact, Account, Deal) are tightly coupled, updating a record in one module can trigger a script that updates another module, creating a loop.
*   **The Solution (Trigger Gating)**: When our scripts perform an automated update that is *purely administrative*, they pass an empty **`trigger` map** to Zoho's `updateRecord` API:
    ```deluge
    suppressTrigger = Map();
    suppressTrigger.put("trigger", List());
    zoho.crm.updateRecord("Deals", dealId, data, suppressTrigger);
    ```
*   **How this behaves**: The database fields are updated immediately, but Zoho is instructed **not** to fire any workflow rules on that change. This prevents infinite loops and racing conditions.
*   **Where Workflows ARE Allowed to Fire**:
    *   When `handleCallOutcome` registers a **Positive** call, it updates `Stage1` *without* suppression. This intentionally trips `WF003` (Stage Change) so the `sequenceRouter` bootstraps the next stage's call activities.
