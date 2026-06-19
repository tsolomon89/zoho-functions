# Jurnii Zoho CRM Quote + Product Contract Model — End-State Specification

**Spec type:** target-state / behavioural specification  
**Primary schema context path:** `.agents/context/api_field_names/`  
**Relevant schema CSVs found in:**

```text
.agents/context/api_field_names/
```

This document specifies the desired CRM end state. It is not a deployment plan and does not prescribe function names, commit order, or workflow build order. It defines the object model, field authority rules, CRUD ownership, and automation outcomes that the system must satisfy.

---

## 1. Core end state

Jurnii CRM must model commercial activity as:

```text
Account
└── one canonical Deal
    ├── current commercial objective
    ├── current relationship summary
    ├── initial contract summary
    ├── latest superseding contract summary, if any
    └── many Quotes
        └── many Quoted Items
            └── Products
```

### 1.1 Object meanings

| Object | Meaning |
|---|---|
| Account | The customer organisation. |
| Contact | A person under the Account. Contacts own individual engagement/progression state. |
| Deal | The continuing commercial relationship for the Account. One canonical Deal per Account. |
| Quote | One customer-facing commercial order form / contractual version. Initial contracts, renewals, and upsells are represented as Quotes. |
| Quoted Item | One product/plan line on a Quote. |
| Product | A sellable Jurnii plan SKU used to seed and structure Quote lines. |
| Task / Call / Meeting | Human-action records. Outcomes on these records should trigger CRM administration automatically. |

### 1.2 Non-negotiable invariants

1. There is **one canonical Deal per Account**.
2. There may be **many Quotes per Deal**.
3. A signed/confirmed Quote is the authoritative contract version.
4. A later signed/confirmed Quote supersedes the previous active contract version.
5. The Deal is not the contract ledger; Quotes are the contract ledger.
6. Products define allowed sellable plan SKUs.
7. Mixed-plan agreements are represented by multiple Quoted Items, not by multi-select fields or comma-delimited text.
8. A human should normally update one operational field; automation should perform the surrounding administrative updates.

---

## 2. Human-action automation principle

The CRM should be operable through **single-field human actions**.

A user should not need to manually update several related records to keep the system coherent. The user updates the operational field on the record they are working in; automations reconcile the dependent fields.

### 2.1 Core examples

| Human action | Required automation outcome |
|---|---|
| Update Deal `Opportunity_Stage` | Recalculate Deal `Stage` / Opportunity Type. |
| Update Quote `Quote_Stage` | Update Deal commercial status, contract summaries, ACV, and supersession state where applicable. |
| Complete a Task with an outcome | Update the relevant Contact, Deal, Quote, next task, or email cadence. |
| Complete a Call with an outcome | Update stage/status and create any next administrative object required. |
| Complete a Meeting/Demo with an outcome | Advance the commercial objective and prepare or update the Quote where applicable. |

### 2.2 Directional authority

The system must avoid unrestricted bidirectional synchronisation.

Before a Quote exists:

```text
Deal / Contact / Product Interest → Quote seed data
```

After a Quote exists:

```text
Quote → Deal contract summary
```

Once a Quote is confirmed, the Quote is the contract version. The Deal stores only the automation-friendly summary.

---

## 3. Deal opportunity ontology

### 3.1 Existing Deal fields

| Field label | API name | Meaning |
|---|---|---|
| Opportunity Stage | `Opportunity_Stage` | Current commercial objective / next thing to achieve. |
| Opportunity Type | `Stage` | MQL / SQL / FTP / RTP bucket. This is Zoho's standard Deal stage field relabelled. |
| Opportunity State | `Opportunity_State` | Open/Lost style commercial state where this is the live field in metadata. |
| Opportunity Status | `Opportunity_Status` | New/Working/Closed style commercial status where this is the live field in metadata. |

Older code may still use `State` and `Status`. The CSV metadata in `.agents/context/api_field_names/` is authoritative for new work. Any live mismatch must be treated as a metadata issue, not solved by creating duplicate fields.

### 3.2 Opportunity Stage → Opportunity Type mapping

`Opportunity_Stage` controls `Stage`.

| Opportunity Stage | Opportunity Type / `Stage` |
|---|---|
| Marketing Qualification | MQL |
| Demo Booking | SQL |
| Demo Confirmation | SQL |
| Demo Hosted | SQL |
| Proposal Preparation | FTP |
| Commercial Agreement | FTP |
| Onboarding | RTP |
| Renewal | RTP |

Required invariant:

```text
When Opportunity_Stage changes, Stage must be recalculated automatically.
```

A user should not need to update both fields.

---

## 4. Product catalogue specification

### 4.1 Product purpose

A Product is a sellable plan SKU. It is used to seed Quote lines and standardise commercial options.

A Product is not a customer contract. A Product becomes contractual only when it is selected as a Quoted Item on a Quote.

### 4.2 Required Product structure

Each sellable product/plan combination must be a separate Product record.

For each product family:

```text
<Product> — Fixed
<Product> — Flex
```

For three product families, the target catalogue contains six active Product SKUs:

```text
Jurnii UX — Fixed
Jurnii UX — Flex
Jurnii 360 — Fixed
Jurnii 360 — Flex
Jurnii Cortex — Fixed
Jurnii Cortex — Flex
```

Use the final Jurnii commercial product names in the live CRM.

### 4.3 Canonical Product fields

Use existing default Product fields where they already represent the fact.

| Field label | API name | Field status | Rule |
|---|---|---:|---|
| Product Name | `Product_Name` | Existing standard | Unique readable SKU name. Must distinguish product family and plan type. |
| Product Code | `Product_Code` | Existing standard | Stable SKU identifier. Must not be casually changed after adoption by automations. |
| Product Active | `Product_Active` | Existing standard | Only active Products may be used for new Quotes. |
| Unit Price | `Unit_Price` | Existing standard | Default annual list price for the SKU. Quote line pricing may override this. |
| Description | `Description` | Existing standard | Default description that may seed Quote line/item copy. |
| Taxable | `Taxable` | Existing standard | Used only if relevant to quoting/tax handling. |

### 4.4 Required new Product fields

Do **not** use `CRM_Product_Type` or `Product_Category` as the canonical plan ontology for this contract model.

Create Product custom fields that mirror the already-established Deal plan language:

| Field label | API name | Type | Rule |
|---|---|---:|---|
| Product Plan Brands | `Product_Plan_Brands` | Number | Default brand count/allowance for the SKU. May be blank if always customer-specific. |
| Product Plan Products | `Product_Plan_Products` | Picklist | Product/package value. Must mirror Lead/Deal plan-product values. |
| Product Plan Type | `Product_Plan_Type` | Picklist | Fixed / Flex. Must mirror Lead/Deal plan-type values. |

These fields intentionally align with the Deal fields:

```text
Contract_Initial_Plan_Brands
Contract_Initial_Plan_Products
Contract_Initial_Plan_Type
Contract_Current_Plan_Brands
Contract_Current_Plan_Products
Contract_Current_Plan_Type
```

### 4.5 Product fields not canonical for this model

The following fields may remain in CRM, but they must not drive Quote creation, contract classification, or Deal contract summaries unless separately and explicitly adopted:

| Field label | API name | Status in this spec |
|---|---|---|
| CRM Product Type | `CRM_Product_Type` | Not canonical. |
| Product Category | `Product_Category` | Not canonical for contract plan logic. |
| Default Deal Value | `Default_Deal_Value` | Not canonical if `Unit_Price` and Quote pricing are available. |
| Active for Deal Auto | `Active_for_Deal_Auto` | Not canonical unless retained as a separate provisional-product-interest flag. Prefer `Product_Active` for Quote eligibility. |
| Value Calculation Method | `Value_Calculation_Method` | Not canonical unless later explicitly adopted. |
| Needs Manual Pricing | `Needs_Manual_Pricing` | Optional operational flag only. It does not replace Quote pricing. |

### 4.6 Product CRUD rules

| Operation | End-state rule |
|---|---|
| Create | The catalogue must contain active Product records for every valid product × plan-type SKU. Product creation may be human/admin-driven or automation-assisted from an approved catalogue source. It must not be created from arbitrary lead text without validation. |
| Read | Quote creation and Quote-line seeding read active Products and their `Product_Plan_*` fields. |
| Update | Admin may update Product price, plan metadata, aliases, description, and active status. Updates affect future Quotes only, not historical confirmed Quotes. |
| Delete | Products used by any historical Quote must not be hard-deleted. Deactivate instead. |

### 4.7 Product validation

A Product is quote-ready only when:

```text
Product_Active = true
Product_Name is not blank
Product_Code is not blank
Unit_Price is present or intentionally zero
Product_Plan_Products is not blank
Product_Plan_Type is not blank
```

`Product_Plan_Brands` may be blank only if brand count is always customer-specific and captured on Quote/Quoted Items instead.

---

## 5. Quote specification

### 5.1 Quote purpose

A Quote is the CRM representation of a customer-facing order form / contract version.

The Quote must be related to:

```text
Account_Name
Deal_Name
Contact_Name
Quoted_Items
```

A Quote must not be treated as a blank placeholder. A valid Quote requires at least one Quoted Item.

### 5.2 Use default Quote fields first

The current Quote module already contains the core fields required for this model.

| Field label | API name | Rule |
|---|---|---|
| Subject | `Subject` | Required Quote/order-form title. |
| Quote Stage | `Quote_Stage` | Owns Quote lifecycle. Do not create a custom Quote lifecycle stage/status field. |
| Valid Till | `Valid_Till` | Proposal validity / commercial expiry. Not the contract end date. |
| Account Name | `Account_Name` | Customer Account. |
| Deal Name | `Deal_Name` | Parent canonical Deal. |
| Contact Name | `Contact_Name` | Primary contractual contact. |
| Quote Owner | `Quote_Owner` | Owner of the quote process. |
| Quoted Items | `Quoted_Items` | Required subform containing product lines. |
| Product Name | `Product_Name` | Product lookup used inside Quoted Items. |
| Quantity | `Quantity` | Native line quantity. Use as brand quantity only if commercially valid. |
| List Price | `List_Price` | Line price. May be seeded from Product `Unit_Price`. |
| Discount | `Discount` | Native discount. Use for previous-contract credit only if its semantics are suitable. |
| Adjustment | `Adjustment` | Native quote-level adjustment. Preferred candidate for previous-contract credit if Discount is line/quote discount. |
| Sub Total | `Sub_Total` | Preferred source for full annual contract value if Quote lines represent annual values before credit. |
| Grand Total | `Grand_Total` | Preferred source for net payable/order value after discount/adjustment. |
| Description | `Description` | Context and notes. |
| Terms and Conditions | `Terms_and_Conditions` | Contractual terms. |

### 5.3 Quote Stage lifecycle

`Quote_Stage` owns Quote lifecycle. Do not create `Contract_Stage`, `Contract_Status`, or `Contract_Version_Status` unless the default field proves unusable.

Current exported Quote Stage values:

```text
Draft
Negotiation
Delivered
On Hold
Confirmed
Closed Won
Closed Lost
```

Target semantics:

| Quote Stage | Meaning |
|---|---|
| Draft | Internal Quote exists and is being prepared. |
| Negotiation | Terms are being negotiated or revised. |
| Delivered | Quote/order form has been sent to the customer. |
| On Hold | Quote process is paused. |
| Confirmed | Quote is accepted/signed and is the currently active contract version for the Deal. There must be at most one Confirmed Quote per Deal. |
| Closed Won | Quote was accepted historically but is no longer the active contract version because it has been superseded or completed. |
| Closed Lost | Quote was rejected, expired, or abandoned. |

### 5.4 Required Quote custom fields

The default Quote module does not distinguish proposal validity from contract term dates. These fields are required.

| Field label | API name | Type | Rule |
|---|---|---:|---|
| Contract Date Start | `Contract_Date_Start` | Date | Start date of the contract version represented by the Quote. |
| Contract Date End | `Contract_Date_End` | Date | End date of the contract version. Normally one year from start/signing under the current Jurnii rule. |

### 5.5 Optional Quote custom fields

These fields are not part of the minimum end state. Create only if native Quote fields cannot carry the fact cleanly or reports/templates/functions need a stable custom field.

| Field label | API name | Type | Create only if |
|---|---|---:|---|
| Contract Type | `Contract_Type` | Picklist | The system cannot reliably infer Initial / Renewed / Upsold / Renewed & Upsold from Quote order, ACV change, and timing. |
| Contract ACV | `Contract_ACV` | Currency | `Sub_Total` cannot reliably represent full annual contract value. |
| Previous Contract Credit | `Previous_Contract_Credit` | Currency | `Discount` or `Adjustment` cannot safely represent previous-contract credit. |
| Net Order Value | `Net_Order_Value` | Currency | `Grand_Total` cannot reliably represent net payable/order value. |
| Contract Signed Date | `Contract_Signed_Date` | Date | Signed date must be stored separately from Quote Stage transition timestamp and contract start date. |

If `Contract_Type` is required, its values are:

```text
Initial
Renewed
Upsold
Renewed & Upsold
```

This is a commercial classification field, not a lifecycle field. `Quote_Stage` remains the lifecycle authority.

### 5.6 Quote value semantics

The Quote must preserve the distinction between full annual value and net amount payable now.

Preferred native-field interpretation:

```text
Sub_Total   = full annual value of the new contract version
Adjustment  = previous-contract credit / discount, if suitable
Discount    = product/quote discount, if suitable
Grand_Total = net amount payable now
```

Example:

```text
Previous contract ACV:       £100,000
New annual contract value:   £140,000
Previous contract credit:     £60,000
Net payable now:              £80,000
```

Preferred CRM representation:

```text
Sub_Total / Contract ACV:     £140,000
Adjustment/Credit:             £60,000
Grand_Total / Net Order Value: £80,000
ACV change:                    £40,000, derived when needed
```

Deal `Amount` must equal the full annual active contract value, not net payable and not lifetime value.

---

## 6. Quoted Items specification

### 6.1 Quoted Item purpose

A Quoted Item is one product/plan line in a Quote.

A mixed-plan agreement is represented as multiple Quoted Items.

Example:

```text
Quote
├── Product A — Fixed
└── Product B — Flex
```

### 6.2 Native Quoted Item fields

Use the native subform fields where possible:

| Field | Rule |
|---|---|
| Product Name | Must reference one active Product SKU. |
| Quantity | Use as quantity/brand count only where that matches commercial pricing. |
| List Price | Default or negotiated annual line price. |
| Discount | Line-level discount where applicable. |
| Tax | Tax where applicable. |
| Total | Native line total. |
| Description | Product/quote-line context. |

### 6.3 Brand-count rule

Use `Quantity` as brand count only if pricing is actually:

```text
price per brand × number of brands
```

If brand count affects commercial scope but not linearly priced quantity, then `Quantity` should remain the quoting quantity and a custom line-level brand field may be needed.

### 6.4 Optional Quoted Item custom fields

No Quoted Item custom fields are required in the preferred end state.

Create these only if native fields plus Product `Product_Plan_*` fields cannot support templates, reporting, or automation:

| Field label | API name | Type | Create only if |
|---|---|---:|---|
| Quoted Item Plan Brands | `Quoted_Item_Plan_Brands` | Number | `Quantity` cannot represent brand count and customer-specific brand count must be stored per line. |
| Quoted Item Plan Products | `Quoted_Item_Plan_Products` | Picklist | Product `Product_Plan_Products` is not accessible where needed. |
| Quoted Item Plan Type | `Quoted_Item_Plan_Type` | Picklist | Product `Product_Plan_Type` is not accessible where needed. |

Guideline:

```text
Do not duplicate Product plan fields onto Quoted Items unless the system cannot reliably read the Product fields from the Quote line context.
```

---

## 7. Deal contract summary specification

### 7.1 Deal purpose

The Deal represents the continuing commercial relationship and current commercial objective.

The Deal does not store every contract version. Quotes store contract versions.

### 7.2 Existing Deal contract fields

The Deal already contains the initial/current contract summary structure. Use it.

Initial contract fields:

```text
Contract_Initial_ACV
Contract_Initial_Date_Start
Contract_Initial_Date_End
Contract_Initial_Date_Renewal
Contract_Initial_Plan_Brands
Contract_Initial_Plan_Products
Contract_Initial_Plan_Type
```

Current/latest superseding contract fields:

```text
Contract_Current_ACV
Contract_Current_Date_Start
Contract_Current_Date_End
Contract_Current_Date_Renewal
Contract_Current_Plan_Brands
Contract_Current_Plan_Products
Contract_Current_Plan_Type
```

### 7.3 Initial/current semantics

| Field group | Meaning | Write rule |
|---|---|---|
| Initial | First confirmed Quote for the Deal. | Populate once from the first confirmed Quote. Do not overwrite except admin correction. |
| Current | Latest confirmed Quote after the initial Quote. | Blank until a later confirmed Quote exists. Overwrite whenever a later Quote supersedes the previous contract version. |

The Current fields are not “always-current” fields. They represent the **latest superseding contract version**.

### 7.4 Deal Amount

`Amount` is the active ACV.

Rule:

```text
If at least one later/superseding confirmed Quote exists:
    Deal.Amount = Contract_Current_ACV
Else if the initial confirmed Quote exists:
    Deal.Amount = Contract_Initial_ACV
Else:
    Deal.Amount may be provisional from product interest/default Products
```

Once a Quote is confirmed, Quote-derived ACV controls `Amount`.

The Deal `Amount` must not equal:

- net payable after previous-contract credit
- lifetime contracted value
- sum of all Quotes
- incremental upsell value only

### 7.5 Deal fields that should not be duplicated unnecessarily

Do not create new Deal contract summary fields unless they are required by workflow, template, dashboard, or reporting constraints.

Do not add these by default:

```text
Contract_Plan_Summary
Contract_Brand_Total
Contract_Lifetime_Value
Contract_RTP_Value
Contract_Version_Count
```

They are allowed later only if they solve a real downstream access problem.

### 7.6 Deal commercial fields that remain useful

| Field label | API name | Rule |
|---|---|---|
| Commercials Status | `Commercials_Status` | May be updated from Quote Stage events. |
| Commercials Discussed At | `Commercials_Discussed_At` | Existing timestamp. |
| Intent To Sign | `Intent_To_Sign` | Existing flag. |
| Next Comm Follow-Up Date | `Next_Comm_Follow_Up_Date` | Follow-up automation field. |
| Automation Suppressed | `Automation_Suppressed` | Deal-level kill switch. |
| Contact Name | `Contact_Name` | Preferred primary Contact lookup. |

---

## 8. Quote-to-Deal contract synchronization

### 8.1 First confirmed Quote

When the first Quote for a Deal reaches:

```text
Quote_Stage = Confirmed
```

Required end state:

```text
Deal.Contract_Initial_ACV = Quote full annual contract value
Deal.Contract_Initial_Date_Start = Quote.Contract_Date_Start
Deal.Contract_Initial_Date_End = Quote.Contract_Date_End
Deal.Contract_Initial_Date_Renewal = derived formula/date from initial end date
Deal.Contract_Initial_Plan_Brands = resolved from Quote/Quoted Items/Products
Deal.Contract_Initial_Plan_Products = resolved from Quote/Quoted Items/Products
Deal.Contract_Initial_Plan_Type = resolved from Quote/Quoted Items/Products
Deal.Amount = Quote full annual contract value
Current contract fields remain blank
```

If mixed products/plans prevent a single value being safely written to a single Deal picklist field, the Deal field should use the cleanest available single summary value only if operationally required. The Quote lines remain the source of truth.

### 8.2 Later confirmed Quote

When a later Quote for the same Deal reaches:

```text
Quote_Stage = Confirmed
```

Required end state:

```text
Previous Confirmed Quote for the Deal is moved to Closed Won
New Quote remains Confirmed
Deal.Contract_Current_ACV = new Quote full annual contract value
Deal.Contract_Current_Date_Start = new Quote.Contract_Date_Start
Deal.Contract_Current_Date_End = new Quote.Contract_Date_End
Deal.Contract_Current_Date_Renewal = derived formula/date from current end date
Deal.Contract_Current_Plan_Brands = resolved from new Quote/Quoted Items/Products
Deal.Contract_Current_Plan_Products = resolved from new Quote/Quoted Items/Products
Deal.Contract_Current_Plan_Type = resolved from new Quote/Quoted Items/Products
Deal.Amount = new Quote full annual contract value
```

There must be at most one `Confirmed` Quote per Deal after automation finishes.

### 8.3 Supersession semantics

Under Fraser's commercial rule:

```text
An upsell creates a new order form that supersedes the previous order form.
The new order form has new total amount and dates.
The previous contract fee is discounted/credited.
The new term is always one year from signing/start.
```

Therefore:

- The new Quote is the full new annual contract, not merely the incremental difference.
- Previous-contract credit belongs on the Quote as discount/adjustment/net-value logic.
- Deal `Amount` uses full annual contract value, not credit-adjusted net payable.

---

## 9. Automation outcome specification

This section defines what the automations must achieve. It does not prescribe function names.

### 9.1 Opportunity Stage automation

Source field:

```text
Deal.Opportunity_Stage
```

Required outcomes:

1. `Deal.Stage` is recalculated from the stage mapping.
2. Stage-completion timestamps are populated where applicable.
3. When `Opportunity_Stage = Proposal Preparation`, the system ensures a valid Draft or Negotiation Quote exists if product data is sufficient.
4. If product data is insufficient for Quote creation, the system creates/updates a human task instead of creating an invalid empty Quote.

### 9.2 Quote Stage automation

Source field:

```text
Quote.Quote_Stage
```

Required outcomes:

| Quote Stage change | Required outcome |
|---|---|
| Draft | Quote may be edited. No contract summary update. |
| Negotiation | Quote may be edited. Commercial follow-up may be scheduled. |
| Delivered | Deal `Commercials_Status = Sent`; sent timestamp populated if blank; follow-up cadence eligible. |
| On Hold | Follow-up cadence pauses or switches to hold logic. |
| Confirmed | Quote is validated, previous Confirmed Quote is superseded, Deal contract fields and Amount update. |
| Closed Won | Quote remains a historical signed/successful Quote but is not the active contract version. |
| Closed Lost | Deal commercial status/loss routing updates only if the commercial motion is actually lost. A lost Quote does not necessarily mean the Deal is lost if a replacement Quote remains possible. |

### 9.3 Task outcome automation

Source field:

```text
Task outcome / Task_Outcome
```

Required outcome:

A task outcome should perform the implied CRM administration without requiring the user to update Deal and Quote fields separately.

Examples:

| Task outcome meaning | Required outcome |
|---|---|
| Proposal ready/sent | Quote Stage moves to Delivered; Deal commercials sent fields update. |
| Follow-up required | Next follow-up task/date is created or updated. |
| Customer intends to sign | Deal `Intent_To_Sign = true`; Quote remains in the appropriate active pre-signing stage. |
| Signed / accepted | Quote Stage moves to Confirmed; contract summaries update. |
| Rejected / no fit | Quote Stage moves to Closed Lost; loss/continuation logic runs. |
| Stage incorrect | Stage correction logic runs without duplicating records. |

### 9.4 Call outcome automation

Source record:

```text
Call
```

Required outcome:

A call outcome should update the relevant Contact, Deal, Quote, and next task state where the outcome implies a commercial progression.

Examples:

| Call outcome meaning | Required outcome |
|---|---|
| Demo booked | Opportunity Stage moves to Demo Booking/Confirmation as appropriate. |
| Demo completed / qualified | Opportunity Stage moves toward Proposal Preparation. |
| Commercials discussed | Commercial discussion timestamp/status updates. |
| Proposal requested | Draft/Negotiation Quote is ensured where product data is sufficient. |
| Signed verbally / agreed | Quote Stage may move to Confirmed only if validation is satisfied. |
| Rejected | Quote and/or Deal loss logic runs according to whether the relationship remains viable. |

### 9.5 Meeting/Demo outcome automation

Source record:

```text
Meeting / Event / Demo outcome
```

Required outcome:

Meeting and demo outcomes should advance the commercial object without requiring manual updates across modules.

Examples:

| Meeting/demo outcome | Required outcome |
|---|---|
| Demo confirmed | Opportunity Stage = Demo Confirmation. |
| Demo hosted and qualified | Opportunity Stage = Proposal Preparation; Quote preparation becomes eligible. |
| Demo hosted but unqualified | loss or nurture logic runs. |
| Commercial agreement reached | Quote Stage moves to Confirmed if the Quote validates; Deal enters/onboards according to stage ontology. |

---

## 10. Quote creation rules

### 10.1 Quote creation boundary

The system should prepare a Quote when the Deal reaches the proposal boundary:

```text
Opportunity_Stage = Proposal Preparation
```

and:

```text
Stage = FTP or RTP according to mapping
```

### 10.2 Quote creation requirements

A created Quote must have:

```text
Subject
Account_Name
Deal_Name
Contact_Name
Quote_Stage
Quoted_Items
```

A Quote must not be created with empty `Quoted_Items`.

### 10.3 Product seeding

Quote lines should be seeded from active Products using:

```text
Product_Name
Product_Code
Product_Active
Unit_Price
Product_Plan_Brands
Product_Plan_Products
Product_Plan_Type
```

Product interest can suggest the Quote composition, but it is not the contract source of truth.

### 10.4 Missing product data

If product data is insufficient to create a valid Quote:

```text
Do not create an invalid Quote.
Create/update a human task explaining what is missing.
```

---

## 11. Product/Quote/Deal CRUD ownership matrix

### 11.1 Products

| Operation | Owner | End-state rule |
|---|---|---|
| Create | Admin or approved automation | Creates valid product × plan-type SKUs only. |
| Read | Automation, Quotes, reports | Read active Products to seed Quotes and validate product ontology. |
| Update | Admin | Pricing/plan changes affect future Quotes only. Historical Quotes remain unchanged. |
| Delete | Admin only, discouraged | Do not delete Products used historically. Deactivate instead. |

### 11.2 Quotes

| Operation | Owner | End-state rule |
|---|---|---|
| Create | Automation or human | Quote must relate to Account, Deal, Contact and contain Quoted Items. |
| Read | Automation, reports, templates | Quotes are the contract-version ledger. |
| Update | Human pre-confirmation; automation for lifecycle side effects | User may update Quote terms and `Quote_Stage`. Automation updates dependent records. |
| Delete | Admin only, discouraged | Confirmed/Closed Won/Closed Lost Quotes should not be deleted; preserve contract history. |

### 11.3 Quoted Items

| Operation | Owner | End-state rule |
|---|---|---|
| Create | Quote creation/editing | Each line references one Product SKU. |
| Read | Automation/templates/reports | Used to resolve contract products/plans and ACV. |
| Update | Human pre-confirmation | Confirmed Quote lines are historical facts and should not drift. |
| Delete | Human pre-confirmation only | Do not delete lines from confirmed contract versions except admin correction. |

### 11.4 Deals

| Operation | Owner | End-state rule |
|---|---|---|
| Create | Lead/Contact/Account automation | One canonical Deal per Account. |
| Read | All automations | Deal is the current commercial relationship summary. |
| Update | Automation primarily; human for source fields | Humans update operational fields like `Opportunity_Stage`; automation updates dependent fields. |
| Delete | Admin only, discouraged | Do not delete canonical commercial relationship records casually. |

---

## 12. Reporting definitions

### 12.1 Active ACV

```text
Active ACV = Deal.Amount
```

After a confirmed Quote exists:

```text
Deal.Amount = full annual value of the active Confirmed Quote
```

### 12.2 Initial ACV

```text
Initial ACV = full annual value of the first confirmed Quote
```

Copied to:

```text
Contract_Initial_ACV
```

### 12.3 Current ACV

```text
Current ACV = full annual value of the latest superseding confirmed Quote
```

Copied to:

```text
Contract_Current_ACV
```

Blank if no superseding Quote exists.

### 12.4 Net payable value

```text
Net payable value = amount payable now after previous-contract credit/discount
```

Preferred native source:

```text
Quote.Grand_Total
```

Fallback custom source only if needed:

```text
Quote.Net_Order_Value
```

### 12.5 Lifetime / RTP values

Lifetime and RTP totals are derived from Quotes. They are not required Deal fields unless reporting/dashboard/email needs require them.

Preferred rule:

```text
Lifetime value = sum of signed Quote net payable values
RTP value = sum of signed non-initial Quote net payable values
```

If these are needed on the Deal, use rollup summary fields where available or function-maintained fields where rollups are insufficient.

---

## 13. Exclusions

### 13.1 Do not create these by default

```text
Contract_Stage
Contract_Status
Contract_Version_Status
Contract_Plan_Summary
Contract_Brand_Total
Contract_Lifetime_Value
Contract_RTP_Value
Contract_Version_Count
```

These are not part of the minimum target state.

They may be introduced only after a concrete downstream dependency is identified.

### 13.2 Do not use these as canonical plan fields

```text
CRM_Product_Type
Product_Category
Default_Deal_Value
```

### 13.3 Do not represent mixed plans through Deal picklist hacks

Do not use:

```text
Fixed + Flex
Product A + Product B
comma-separated product text
multi-select plan field as contract source of truth
```

Mixed plans belong in Quoted Items.

---

## 14. Validation rules

### 14.1 Product validation

A Product can be used for Quote creation only if:

```text
Product_Active = true
Product_Name is present
Product_Code is present
Unit_Price is present or intentionally zero
Product_Plan_Products is present
Product_Plan_Type is present
```

### 14.2 Quote validation

A Quote can progress to `Confirmed` only if:

```text
Subject is present
Deal_Name is present
Account_Name is present
Contact_Name is present
Quoted_Items contains at least one item
Contract_Date_Start is present
Contract_Date_End is present or can be derived
Full annual contract value can be resolved from Sub_Total or Contract_ACV
```

### 14.3 Confirmed Quote validation

After Quote activation completes:

```text
There is exactly one Confirmed Quote for the Deal
Previous confirmed contract versions are Closed Won
Deal Amount equals the Confirmed Quote full annual value
Deal initial/current contract fields match the appropriate Quote
```

### 14.4 Deal validation

A Deal is contract-consistent when:

```text
No confirmed Quotes:
    Amount may be provisional

One confirmed Quote:
    Initial contract fields match that Quote
    Current contract fields are blank
    Amount equals initial Quote full annual value

Multiple confirmed/signed historical Quotes:
    Initial fields match first confirmed Quote
    Current fields match active Confirmed Quote
    Previous signed Quotes are Closed Won
    Amount equals active Confirmed Quote full annual value
```

---

## 15. Final operating principle

The desired CRM behaviour is:

```text
Products define valid sellable plan SKUs.
Quotes define contract/order-form versions.
Quoted Items define the product/plan composition of each contract version.
Deals define the current commercial relationship and store only necessary summaries.
Contacts own individual engagement and progression state.
Tasks, Calls, and Meetings are the human-action interface for moving the system.
```

The system should prefer default Zoho fields wherever they already represent the concept cleanly.

Custom fields are justified only when:

1. the fact is not already represented by a default field;
2. the field mirrors established Lead/Deal contract vocabulary; or
3. automation, templates, reports, or validation require a stable Jurnii-specific field.

The ideal operator experience is:

```text
Human updates one meaningful field.
Automation reconciles the dependent CRM state.
```
