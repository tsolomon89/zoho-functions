You are working on a Zoho CRM Deluge automation repo. The repo contains the current functions uploaded from ChatGPT:

- convert2lead.deluge
- normalizeContactCommercialState.deluge
- normalizeDealCommercialState.deluge
- rollupAccountCommercialState.deluge
- syncDealProductsAndValue.deluge

Review all files before editing. You may create helper files / utility functions if that is cleaner, but keep Zoho Deluge save constraints in mind. You may also go online and research Zoho CRM Deluge documentation, especially around `convertLead`, field API names, multi-select lookup fields, related records, products, deals, and workflow-triggered custom functions.

Do not use Zoho Cadences. This must remain workflow-adjacent custom-function logic.

## High-level goal

Fix the current CRM automation so Leads act as a staging/import/input area and are processed into canonical CRM records:

Lead → Contact + Account + Deal

The Lead object is not the durable source of truth. Contacts, Accounts, Deals, and Products are.

The current system broke after we split logic into multiple functions. The main observed failures after bulk CSV upload were:

1. Duplicate Accounts were created.
2. Lead Phone mapped to Account Phone instead of Contact Phone.
3. No Deals were created.
4. Many Leads did not convert, but the desired behavior is that all Leads should convert whenever Zoho has enough mandatory data to create canonical records.
5. Product Interest mapping failed because Lead Product Interest is not the same field type as Product Interest on Contacts/Accounts/Deals.

## Core correction

Old model, now wrong:

Lead validation decides whether conversion happens.

New model:

Lead conversion should happen first. Validation only determines where the converted Contact / Deal lands in the ontology.

All Leads should be processed out of Leads into Contact / Account / Deal where possible. Missing marketing consent, missing website, missing industry, missing phone, missing product interest, etc. should not block conversion. They should affect Stage / Opportunity / State / Status and/or leave data-quality gaps for later cleanup.

## Commercial ontology

Opportunity values:

- MQL
- SQL
- FTP
- RTP

Meanings:

- MQL = Marketing Qualified Lead
- SQL = Sales Qualified Lead
- FTP = First Time Purchase
- RTP = Retention Purchase

Important: these are active commercial motions, not final labels.

Stage values:

- Marketing Consent
- Demo Booking
- Demo Booked
- Demo Attended
- Commercials Sent
- Commercials Signed
- Onboarding
- Renewal

State values:

- Open
- Lost

Do not use Won as a persistent State. “Won” only means a gate was passed and the next commercial motion opens.

Status values:

- New
- Working
- Closed

Status rules:

- Closed only when State = Lost
- Working when at least one meaningful manual/human activity exists
- New otherwise

Meaningful manual activity includes Calls, Meetings/Events, Tasks, Notes, and later manually logged emails if distinguishable from automated emails. Automated nurture/system workflow emails must not count.

Stage → Opportunity mapping:

- Marketing Consent → MQL
- Demo Booking → SQL
- Demo Booked → SQL
- Demo Attended → SQL
- Commercials Sent → FTP
- Commercials Signed → FTP initially, but if gate passed then move to RTP / Onboarding
- Onboarding → RTP
- Renewal → RTP

Gate rules:

- Marketing Consent + marketing consent captured + enough marketing data → SQL / Demo Booking
- Demo Attended + Product Interest resolvable + explicit commercial-ready signal → FTP / Commercials Sent
- Commercials Signed → RTP / Onboarding
- Lost records do not gate-advance

Commercial-ready signals may include fields such as:

- Ready_For_Commercials = true
- Demo_Outcome in [Qualified, Proceed to Commercials, Proceed to Commercial Terms, Good Demo]

If those fields do not exist, do not invent new required fields without making that a clear TODO/config item.

## Product Interest correction

This is important.

Lead Product Interest was changed to a multiselect field for import/staging.

Contacts, Accounts, and Deals still have Product Interest as a linked join / multi-select lookup style field to Product records.

Therefore:

- Do not assume Lead Product_Interest is a lookup map with `{id, name}`.
- Do not do `productInterest.get("id")` on Leads.
- Do not directly map Lead Product Interest into Contact/Account/Deal Product Interest join fields unless the correct Zoho multi-select lookup payload/linking module behavior is implemented and tested.
- Treat Lead Product Interest as product-name staging input.
- Use product names to resolve Products by Product_Name where possible.
- Use resolved Products to calculate Deal Amount.
- Syncing the actual linked join Product Interest field can be a later explicit task unless you can verify the exact API structure from Zoho docs and implement it safely.

`syncDealProductsAndValue` should be rewritten to resolve product names/product signals and calculate value, not assume `Deal.Product_Interest` is a single lookup.

## Account duplicate prevention

The duplicate Account issue must be fixed in `convertLead2`.

Use a canonical Account identity before conversion.

Account lookup priority:

1. Existing Contact’s Account, if matching Contact already exists.
2. Account_Key, if the field exists or is added.
3. Account_Name equals normalized Company.
4. Website equals normalized Website/domain.
5. Account_Name equals normalized Website/domain.
6. Email domain.
7. Fallback: `Unknown Account - {Lead ID}`.

Important cases from the bulk upload:

- Company may be a domain, e.g. `lionvegas.com`, `spires.com`, `theprofs.com`, `oblio.app`.
- If Company looks like a domain and Website is blank, derive Website/domain from Company.
- If Company is blank but Website exists, derive Company/domain from Website.
- If both are blank but Email exists, derive Account identity from email domain.

Normalize domains consistently:

- lower-case
- strip `https://`
- strip `http://`
- strip `www.`
- strip trailing `/`
- use domain as Account_Key where available

If Account_Key does not exist in Zoho, either:
- add it as a configurable optional field and use it if present, or
- implement matching through Account_Name / Website / email domain only.

Do not create duplicate Accounts for repeated leads at the same company.

## Phone mapping correction

Lead Phone maps to Contact Phone only.

Do not map Lead Phone to Account Phone.

Only a separate explicit company/account phone field should map to Account.Phone. If such a field does not exist, leave Account.Phone blank.

## Deals creation correction

`convertLead2` must always attempt to create or reuse a Deal when converting a Lead, unless Zoho’s mandatory data makes that impossible.

If no existing Deal is found under the Account, create one with required fields.

Deal matching:

- Prefer existing Deal under same Account + same product signal, if product is resolvable.
- Otherwise use furthest Open Deal under the Account.
- Otherwise use furthest Lost Deal only if appropriate.
- Otherwise create a new Deal.

Deal field naming issue:

The Zoho UI label and API names may differ. The default Zoho Deal Stage field may have been relabelled as “Opportunity”. A new custom field labelled “Stage” may have an API name like `Stage_1`.

Confirm the actual API names from the repo/config or Zoho docs/metadata if possible.

The intended semantic fields are:

- Opportunity = MQL / SQL / FTP / RTP
- Stage = Marketing Consent / Demo Booking / Demo Booked / Demo Attended / Commercials Sent / Commercials Signed / Onboarding / Renewal

Do not blindly assume display labels are API names. If uncertain, centralize config constants at the top of each function and document what must be changed.

## Required file/function changes

### 1. `convert2lead.deluge`

Rewrite this first.

Make it an always-convert processor.

Required changes:

- Remove blocking validation for missing Website, Industry, Phone, Marketing Consent, Product Interest.
- Keep only true hard failures:
  - Lead not found.
  - Zoho cannot convert because mandatory Zoho fields are missing and no fallback can be derived.
- Derive Company / Website / Account identity from Company, Website, and Email domain.
- Strengthen existing Contact lookup:
  - Email first.
  - Phone second only if Email missing/no match.
- Strengthen existing Account lookup using Account identity rules above.
- Remove Lead Phone → Account Phone mapping.
- Treat Lead Product Interest as staging names, not a lookup ID.
- Do not map Lead Product Interest directly into linked Product Interest join fields unless safely implemented.
- Always pass a Deal map to `convertLead` when no suitable existing Deal exists.
- After conversion, enrich Contact and Account.
- Then call `automation.normalizeContactCommercialState(finalContactId)`.

Validation now controls normalization only:

- Missing Marketing Consent → MQL / Marketing Consent.
- Marketing Consent captured → SQL / Demo Booking.
- Later imported Stage should be preserved where sensible.
- Lost Reasons → State Lost / Status Closed.
- Missing Product Interest at FTP/RTP should not block conversion; it should leave product/value unresolved.

### 2. `normalizeContactCommercialState.deluge`

Patch this after `convert2lead`.

Required changes:

- Do not block normalization because Product Interest is missing.
- Remove any `return "Product_Interest is required..."` logic.
- Do not assume Product Interest is a single lookup map.
- Continue normalizing Contact Stage / State / Status.
- Continue finding/creating/updating the relevant Deal.
- Preserve imported stage where appropriate.
- Call `automation.syncDealProductsAndValue(finalDealId)` after Deal update.
- Call `automation.rollupAccountCommercialState(accountId)` after product sync.
- Do not use Contact Roles API / invokeurl yet.
- Keep the current fallback rollup pool as Contacts under the same Account until Contact Roles sync is separately solved.

### 3. `normalizeDealCommercialState.deluge`

Patch this after Contact normalizer.

Required changes:

- Do not block if Product Interest is missing.
- Remove any product-required blocking return.
- Do not assume Product Interest is a single lookup map.
- Normalize direct Deal edits:
  - Stage → Opportunity
  - Lost Reasons / Reason For Loss → State
  - Activity → Status
- Preserve direct imported Deal stage where appropriate.
- Do not roll Deal backward from Contacts.
- Use Account Contacts as fallback rollup pool.
- Call `automation.syncDealProductsAndValue(dealId)`.
- Call `automation.rollupAccountCommercialState(accountId)`.

### 4. `syncDealProductsAndValue.deluge`

Rewrite this substantially.

Current assumption is obsolete:

`Deal.Product_Interest = single lookup`

New behavior:

- Read Deal.
- Resolve product signals from available fields:
  - Deal Product Interest linked/join field if readable.
  - Any product-name staging field if present.
  - Existing related Products if available.
  - Product names from fields copied from Lead import if available.
- Resolve product names against Products module by Product_Name.
- Sum product value fields.
- Update Deal.Amount.
- Use `Unit_Price` as default product value field unless a better field exists.
- Do not fail if no product is resolvable.
- Return a clear message:
  - no product signal found
  - product signal found but no product records matched
  - amount calculated and updated

Do not require a direct workflow for this function. It is called by the Contact and Deal normalizers.

### 5. `rollupAccountCommercialState.deluge`

Patch this last.

Required changes:

- Do not touch Account Product Interest for now.
- Only roll up Account State and Status from related Deals.
- Account State = Open if any related Deal is Open.
- Account State = Lost only if all related Deals are Lost.
- Account Status = Closed only if State = Lost.
- Account Status = Working if any Open Deal is Working.
- Otherwise New.

## Workflow expectations

Do not use Zoho Cadences.

Workflows should be:

1. Leads created/edited → `automation.convertLead2(lead_id)`
2. Contacts created/edited → `automation.normalizeContactCommercialState(contact_id)`
3. Deals created/edited → `automation.normalizeDealCommercialState(deal_id)`
4. Accounts created/edited → `automation.rollupAccountCommercialState(account_id)`

If Zoho workflow loops occur, narrow triggers to source fields only and avoid triggering on fields the functions themselves write.

Source fields include:

- Stage
- Marketing_Consent
- Lost_Reasons
- Reason_For_Loss
- Product Interest staging fields
- Ready_For_Commercials
- Demo_Outcome
- Account_Name
- Contact_Name

Avoid using fields mainly written by functions as workflow triggers:

- Opportunity
- State
- Status
- Amount

## Testing plan

After changes, test with a 5-row import only.

Test rows should include:

1. Same company/domain, two leads, no duplicate Account.
2. Lead with missing Marketing Consent, should still convert to MQL / Marketing Consent.
3. Lead with Marketing Consent, should convert to SQL / Demo Booking.
4. Lead at Commercials Sent with missing Product Interest, should still convert but not calculate Amount.
5. Lead with Product Interest names matching Products, should convert and calculate Deal Amount if product resolution works.

Inspect:

- Leads converted.
- Contacts created/reused.
- Accounts deduplicated.
- Phone only on Contact.
- Deals created.
- Stage / Opportunity / State / Status correct.
- Amount calculated only when product can be resolved.
- No Account Product Interest writes for now.

## Final invariant

Lead = staging/import/form input.
Contact = person-level commercial progress.
Deal = canonical commercial motion and commercial value.
Account = aggregate commercial state.
Product Interest on Leads = product-name staging signal.
Product Interest on Contacts/Accounts/Deals = linked join field, not directly mapped until join sync is explicitly implemented.