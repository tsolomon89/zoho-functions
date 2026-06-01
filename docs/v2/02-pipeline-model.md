# 02 — Pipeline Model

## TLDR
The system uses four clear database fields to track sales progress. 
*   **Opportunity** = where it sits in the pipeline.
*   **Stage** = what needs to happen next.
*   **State** = whether the deal is still alive.
*   **Status** = whether a rep is actively working it.

Evidence: `spec.md`, `v4/processLead.deluge`, `v4/processContact.deluge`

---

## Core Ontology Fields

| Field | API Field | Plain meaning | Allowed Values |
| :--- | :--- | :--- | :--- |
| **Opportunity** | `Stage` | Big pipeline bucket | `MQL`, `SQL`, `FTP`, `RTP` |
| **Stage** | `Stage1` | Current operational step | `Marketing Consent` to `Renewal` |
| **State** | `State` | Open or Lost | `Open`, `Lost` |
| **Status** | `Status` | New, Working, or Closed | `New`, `Working`, `Closed` |

---

## Pipeline Progression Map

`Stage1` is the operational step. It automatically decides the `Stage` (Opportunity bucket):

| Rank | Stage (`Stage1`) | Opportunity (`Stage`) | Plain meaning |
| :---: | :--- | :--- | :--- |
| **1** | `Marketing Consent` | `MQL` | Prospect has consented to marketing |
| **2** | `Demo Booking` | `SQL` | Rep is actively trying to book a demo |
| **3** | `Demo Booked` | `SQL` | Demo is booked on the calendar |
| **4** | `Demo Attended` | `SQL` | Demo occurred; sales qualification is active |
| **5** | `Commercials Sent` | `FTP` | **First-Time Purchase begins** (terms/proposal sent) |
| **6** | `Commercials Signed` | `RTP` | **Retention Purchase begins** (signed; moving to onboarding) |
| **7** | `Onboarding` | `RTP` | Customer technical setup and kickoff |
| **8** | `Renewal` | `RTP` | Customer active phase; renewal or expansion |

---

## Core Pipeline Rules

*   **`Stage1` Decides `Stage`**: Operational steps drive the pipeline buckets automatically.
    *   *Evidence*: `spec.md` (lines 103–128)
*   **`Commercials Sent` Starts FTP**: FTP begins only when contract terms are sent. Up until then, the deal is `SQL`.
    *   *Evidence*: `v4/activity/handleCommercialsStatusChange.deluge`
*   **`Commercials Signed` Starts RTP**: The signed contract moves the customer to onboarding.
    *   *Evidence*: `v4/processDeal.deluge`
*   **`Won` is Not a Permanent State**: "Won" is just a gate event. When passed, the Deal advances into the next active phase (`RTP`) instead of being closed as Won.
    *   *Evidence*: `spec.md` (lines 72–80)
*   **`State` is Only `Open` or `Lost`**: A deal is either active or lost.
    *   *Evidence*: `spec.md` (lines 57–72)
*   **`Status = Closed` only when `State = Lost`**: You cannot close an active deal.
    *   *Evidence*: `spec.md` (lines 81–97)
*   **What Makes a Record `Working`**: Only manual rep actions (calls, tasks, meetings) make a record `Working`. Automated background emails keep it `New` or `Waiting`.
    *   *Evidence*: `spec.md` (lines 95–100)

---

## Examples

### 1. Active Demo Stage
```text
Stage1 = Demo Booked
Stage = SQL
State = Open
Status = Working (if a rep has logged a call or meeting manually)
```

### 2. Proposal Sent
```text
Stage1 = Commercials Sent
Stage = FTP
sequenceRouter starts Commercials Sent Call 1
```

### 3. Deal Lost
```text
State = Lost
Status = Closed
Automation stops immediately
```
