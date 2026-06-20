# 02 — Pipeline Model

## TLDR
The system uses four clear Zoho fields to track sales progress from start to finish.

*   **Opportunity** answers: what broad pipeline bucket is this in? (MQL, SQL, FTP, RTP)
*   **Stage** answers: what step are we trying to complete next? (Marketing Consent to Renewal)
*   **State** answers: is this commercial motion still active? (Open or Lost)
*   **Status** answers: is this record untouched, being worked, or closed? (New, Working, Closed)

---

## Core Pipeline Fields

*   **Opportunity**: The big pipeline bucket representing the commercial phase (`MQL`, `SQL`, `FTP`, `RTP`).
*   **Stage**: The current operational step within the sales cadence.
*   **State**: The commercial status showing if the Deal is still active (`Open`) or dead (`Lost`).
*   **Status**: Indicates whether the record is untouched (`New`), has manual representative activity (`Working`), or has stopped (`Closed`).

---

## Pipeline Progression Map

The Stage selection automatically decides the Opportunity bucket. Sales progression flows in this exact sequence:

| Rank | Stage | Opportunity | Meaning |
| :---: | :--- | :--- | :--- |
| **1** | Marketing Qualification | MQL | Marketing consent and required profile data obtained |
| **2** | Demo Booking | SQL | Rep is trying to book a demo |
| **3** | Demo Confirmation | SQL | Demo is booked, confirming attendance |
| **4** | Demo Hosted | SQL | Demo completed |
| **5** | Proposal Preparation | FTP | Proposal/commercials are being prepared |
| **6** | Commercial Agreement | FTP | Proposal/commercials sent, chasing agreement/signature |
| **7** | Onboarding | RTP | **Retention Purchase begins** (signed; customer setup) |
| **8** | Renewal | RTP | Renewal / expansion |

---

## Core Pipeline Rules

*   **Stage Decides Opportunity**: Operational steps drive the pipeline buckets automatically.
*   **Proposal Preparation Starts FTP**: First-Time Purchase begins after a positive demo outcome, when we enter proposal preparation.
*   **Onboarding Starts RTP**: The signed contract moves the customer to onboarding.
*   **Won is not a lasting State**: "Won" is just a transition gate event being passed. When commercials are signed, the Deal moves to:
    *   **Stage** = Onboarding
    *   **Opportunity** = RTP
    *   **State** = Open
    *   **Sequence Status** = Not Started (so the next RTP / onboarding sequence can begin)
    *   This keeps onboarding, retention, and renewal active.
*   **State is Only Open or Lost**: A deal is either active or lost.
*   **Status = Closed Only When State = Lost**: You cannot close an active deal.
*   **What Makes a Record Working**: Only manual rep actions (calls, tasks, meetings) make a record `Working`. Automated background emails keep it `New` or `Waiting`.

---

## Examples

### 1. Active Demo Stage
```text
Stage = Demo Confirmation
Opportunity = SQL
State = Open
Status = Working (if a rep has done real activity)
```

### 2. Proposal Sent
```text
Stage = Commercial Agreement
Opportunity = FTP
System creates Commercial Agreement Call 1
```

### 3. Deal Lost
```text
State = Lost
Status = Closed
Automation stops
```

---

## Field Mapping for Implementation

In the API, Zoho's user-facing names map to the following API fields:

| In Zoho UI | API Name |
| :--- | :--- |
| **Opportunity** | `Stage` |
| **Stage** | `Stage1` |
| **State** | `State` |
| **Status** | `Status` |

### Relevant Repo Files

- `v4/processLead.deluge`
- `v4/processContact.deluge`
- `v4/activity/handleCommercialsStatusChange.deluge`
