# FIELD_REUSE_NOTES.md — Existing fields the new spec should reuse

## Purpose

`ZOHO_FIELD_MAP.md` lists every field the activity-workflows pack needs. Some of those fields already exist in the org (sometimes under different API names than the labels suggest). This note documents the reuse decisions so the implementer creates only the **new** fields and does not duplicate or conflict with the existing graph layer.

The authoritative current-org export is `.agents/context/api_field_names/*.csv`.

---

## Deals

| Spec label | Existing API name | Action | Reason |
|---|---|---|---|
| Stage | `Opportunity_Stage` | **REUSE** | Org's custom `Opportunity_Stage` already holds the 8 spec values. v3 reads/writes it as the stage value. Do not create a second `Stage` field. |
| Opportunity | `Stage` (default) | **REUSE** | Default Zoho `Stage` field has been renamed in the UI to "Opportunity" and holds `MQL/SQL/FTP/RTP`. v3 writes it via `dealMap.put("Stage", bestOpp)`. |
| State | `State` | **REUSE** | Existing picklist (`Open/Lost/Won`). Automation writes only `Open` or `Lost`; `Won` is a gate event, not a durable State (see `docs/v2/02-pipeline-model.md`). v3/v4 already follow this rule. |
| Status | `Status` | **REUSE** | Existing picklist (`New/Working/Closed`). v3 already writes this. |
| Reason For Loss | `Reason_For_Loss__s` | **REUSE** | Existing system field. v3 writes "Duplicate / Test Record" on silenced duplicates. |
| Stage Rank | — | **DO NOT CREATE** | Derive in Deluge from `Opportunity_Stage` via the `stageRanks` map already defined in v3 (and in the shared util we are extracting in Phase 2). |

The Deal already uses `Account_Name`, `Contact_Name`, `Amount`, `Deal_Key`, `Closing_Date`, `Lost_Reasons`, `Deal_Name`, `Product_Details` (subform). None of those are duplicated by the spec.

## Contacts

| Spec label | Existing API name | Action | Reason |
|---|---|---|---|
| Marketing Qualification Status | `Marketing_Consent` (Boolean) | **CREATE NEW** `Marketing_Consent_Status` (Picklist) | The existing Boolean cannot represent the 4 spec values (`Consented/Not Consented/Unknown/Withdrawn`). Keep the Boolean live for legacy filters, populate the new picklist alongside, deprecate the Boolean after migration. |
| Contact Role | `Contact_Role1` | partially reused via Contact_Roles junction | v3 stamps `Contact_Role1` on the Contact directly. The activity layer uses the `Contact_Roles` sub-module (deal-scoped roles) — different surface, both kept. |
| Products Linked | `Products_Linked` | — | Existing aggregation field used by v3 for product interest rollup. Not in spec but read by `processX`. |

## Accounts

| Spec label | Existing API name | Action | Reason |
|---|---|---|---|
| Account Name | `Account_Name` | **REUSE** | Standard field. |
| Website | `Website` | **REUSE** | Used by v3 for `Account_Key` derivation. |
| Account Key | `Account_Key` | **REUSE** | Custom UNIQUE field already in use by v3. |
| State | `State` | **REUSE** | Existing; rolled up by v3 from Deals. |
| Status | `Status` | **REUSE** | Existing; rolled up by v3 from Deals. |
| Account Status | — | **CREATE NEW** as `Account_Status` Picklist | Spec calls for a commercial classification (`Prospect/Active Customer/Existing Client/Partner/Churned/Do Not Contact`) that is orthogonal to the lifecycle `Status` field. Create as a new picklist; do not collapse. |

## Products

| Spec label | Existing API name | Action | Reason |
|---|---|---|---|
| Unit Price | `Unit_Price` | **REUSE** | v3 sums `Unit_Price` into `Deal.Amount`. The new `Default Deal Value` field is for deals where Unit_Price is not the right multiplier. Both coexist; resolver prefers `Default_Deal_Value` if set, else falls back to `Unit_Price`. |
| Product Name | `Product_Name` | **REUSE** | Used for catalog lookup by v3. |
| Product Active | `Product_Active` | **REUSE** | Existing flag. Keep filtering catalog queries on it. |
| Active for Deal Automation | — | **CREATE NEW** as `Active_for_Deal_Automation` Checkbox | Distinct gate from `Product_Active` so admins can keep a product visible in the UI but pause its automation eligibility. |

## Calls / Events / Tasks

Org has **no custom fields on these modules today**. Module API names:

- Calls → `Calls`
- Events (meetings) → `Events`
- Tasks → `Tasks`

**Discovered constraints when creating fields via Zoho API (Phase 10 execution):**

1. **Custom `Lookup` field type is disallowed on Activities modules.** Attempting to create `Related_Deal` as a Lookup→Deals returns `NOT_ALLOWED` ("Field type is not supported in the given module"). The activity layer therefore uses the built-in polymorphic `What_Id` lookup + `$se_module = "Deals"` for Deal linkage on Calls, Events, and Tasks.

2. **`Boolean` (Checkbox) field type is disallowed on Activities modules.** All originally-planned booleans (`Sequence_Managed`, `Blocks_Email_Until_Completed`, `Stale`, `Follow_Up_Required`, `Blocks_Sequence`) were created as `Picklist` fields with values `Yes` / `No` instead. The Deluge code therefore checks `ifnull(call.get("Sequence_Managed"), "No").toString() == "Yes"` rather than the original `== "true"`, and writes `"Yes"` / `"No"` strings.

3. **Custom fields are shared across all three Activities sub-modules.** A field created on Calls (e.g., `Sequence_Managed`, `Sequence_Stage`, `Sequence_Attempt`, `Next_Follow_Up_Date`) is automatically visible on Events and Tasks too, so attempting to create them again on those modules returns `DUPLICATE_DATA`. Plan accordingly when adding more shared fields.

4. **Task Type & Outcome additions (v5)**:
   - `Task_Type` is extended to support `Sequence Activation`.
   - `Task_Outcome` is extended to support `Activate Call First`, `Activate Email First`, `Manual Only`, `Suppress`, `Already Handled`, and `Stage Incorrect`.

These modules use the standard fields `Subject`, `Owner`, `Status`, `Description`, plus the per-module lookups (`Who_Id`, `What_Id`, `Se_Module`). For workflow criteria that need to filter on "calls related to a Deal", use `What_Id is not empty AND $se_module equals Deals`.

## Field labels shortened for the 25-character cap

Zoho's API enforces a 25-character maximum on `field_label`. The following spec labels were shortened during field creation; the **actual** API names in the org are the shortened forms below — Deluge code and CSV reference these:

| Spec label (long) | Actual label | Actual api_name |
|---|---|---|
| Active for Deal Automation | Active for Deal Auto | `Active_for_Deal_Auto` (Products) |
| Sequence Thread Message ID | Seq Thread Message ID | `Seq_Thread_Message_ID` (Deals) |
| Commercial Follow-Up Reason | Comm Follow-Up Reason | `Comm_Follow_Up_Reason` (Deals) |
| Next Commercial Follow-Up Date | Next Comm Follow-Up Date | `Next_Comm_Follow_Up_Date` (Deals) |
| Blocks Email Until Completed | Block Email Until Done | `Block_Email_Until_Done` (Calls) |
| External Calendar Booking ID | Ext Calendar Booking ID | `Ext_Calendar_Booking_ID` (Events) |
| Industry Confirmation Status | Industry Validation | `Industry_Validation` (Accounts) |
| Account Source Classification | Account Source Class | `Account_Source_Class` (Accounts) |
| Contact Source Classification | Contact Source Class | `Contact_Source_Class` (Contacts) |

---

## Hook line in v3 — exact text

The same one-line hook in each of the four v3 files:

```deluge
if(canonicalDealId != "" && ifnull(targetDeal.get("State"), "Open") == "Open") {
    info "sequenceRouter hook: canonicalDealId=" + canonicalDealId;
    automation.sequenceRouter(canonicalDealId.toLong());
}
```

`processLead.deluge`, `processContact.deluge`, `processDeal.deluge` all already have `targetDeal` in scope at the insertion point. `processAccount.deluge` has it inside the `if(canonicalDealId != "")` block (line ~263 onward) — the hook goes at the end of that block.

If `targetDeal` is not in scope at the chosen line, the hook can fall back to:

```deluge
if(canonicalDealId != "") {
    dealStateCheck = zoho.crm.getRecordById("Deals", canonicalDealId.toLong());
    if(ifnull(dealStateCheck.get("State"), "Open") == "Open") {
        automation.sequenceRouter(canonicalDealId.toLong());
    }
}
```

---

## Migration safety notes

1. **Backfill `Sequence Status` on existing Deals** before turning on `WF002`. Set `Sequence Status = Not Started` on Open Deals that should enter the new flow; leave blank on imported/historical/closed ones to keep the router idle.
2. **`Automation Suppressed` defaults to false** — explicitly set `true` on every Deal currently being worked manually before the workflows are switched on.
3. **`Stage Rank` is never persisted.** Always recompute from `Opportunity_Stage` in code via the canonical map (see `_util_resolveRoleFromTitle.deluge` partner util in Phase 2).
