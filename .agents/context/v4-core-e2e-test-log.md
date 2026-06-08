# v4 CRM Graph E2E Test Log

* **Org mode:** Production (Test data only)
* **Session prefix:** `V4_E2E_20260608_0800`

---

## Test 1 — Single Lead conversion

* **Records involved:**
  * Lead: `991103000000972018`
  * Account: `991103000000924061`
  * Contact: `991103000000931038`
  * Deal: `991103000000899016`
* **Action performed:** Lead created with website, phone, stage = `Marketing Qualification`, job title = `Head of Marketing`, product interest = `["Jurnii Cortex"]`. Converted via workflow.
* **Expected Result:** Lead converts, Contact role is `Decision Maker`, Deal is linked, `Deal.Stage1 = Marketing Qualification`, `Deal.Stage = MQL`, `Deal.State = Open`, `Deal.Status = New`, Deal has `Jurnii Cortex` product attached, `Deal.Amount = 16000`, Call `Marketing Qualification Call 1` is created and linked.
* **Observed Result:** 
  * Lead converted successfully.
  * Account and Contact created, linked correctly.
  * Deal created and linked.
  * `Contact_Role1` stamped as `Decision Maker` (resolved from "Head of Marketing").
  * `Deal.Stage1 = Marketing Qualification`, `Deal.Stage = MQL`, `Deal.State = Open`, `Deal.Status = New`.
  * Contact linked in `Contact_Roles` with role `Decision Maker`.
  * **Deal Product not mapped: Deal.Amount = 0, Products related list empty.**
  * Call `Marketing Qualification Call 1` successfully created and linked.
* **Status:** FAIL (on Product Mapping & Amount)
* **Root Cause:** 
  1. `zoho.crm.searchRecords("Products", "(Product_Active:equals:true)")` fails/returns empty because boolean search criteria are not supported or are buggy in Zoho CRM `searchRecords`.
  2. Fallback search `zoho.crm.searchRecords("Products", "(Product_Name:equals:" + safeName + ")")` fails for product names with spaces (e.g. `Jurnii Cortex`) because the value is not enclosed in double quotes.
* **Surgical Fix:** 
  1. Replaced product catalog retrieval with `zoho.crm.getRecords("Products", 1, 200)` and filtered active products locally in Deluge.
  2. Wrapped product names in escaped double quotes `\"` in fallback searches.
  3. Modified files: `v4/processLead.deluge`, `v4/processContact.deluge`, `v4/processDeal.deluge`, `v4/processAccount.deluge`.
* **Actions Required:** Republish all 4 deluge functions in Zoho CRM.
