# Pre-Import Audit, Part 2: CSV Field Mapping, Row Exceptions, Readiness

Target module for all four files = **Leads** (intake), which then auto-converts to Contact/Account/Deal. Currency throughout = **GBP**. All four files share columns 0–28 and 65–124; **SQL diverges** (uses `Contact AOR*` labels instead of `Contact Role AOR*`, and **blanks out the entire Contract block** as 35 empty-named columns).

Legend — **Required**: Zoho-mandatory or needed for safe matching/conversion. **Derived**: produced by automation post-import. **Default**: safe default if blank. **Drop**: no destination; do not import.

---

## D. Master column → field mapping (applies to all four files unless noted)

| # | Source Column | Target Module.API | Field Label | Transform | Req | Derived | Default | Validation / Notes |
|--|--|--|--|--|--|--|--|--|
| 0 | Company | Leads.`Company` | Company | trim | ✓ | | | feeds `Account_Key` fallback |
| 1 | Company Website | Leads.`Website` | Company Website | normalize host | ✓* | | | **primary `Account_Key` source** (domain). *blank+no-email → key=company slug |
| 2 | Full Name | *(ignore)* | Full_Name | — | | ✓ | | auto-derived from First+Last; duplicate col 123 also ignore |
| 3 | First Name | Leads.`First_Name` | First Name | | | | | |
| 4 | Last Name | Leads.`Last_Name` | Last Name | **fill if blank** | **✓ MANDATORY** | | | blank rows **fail import** — see E |
| 5 | Contact Email Primary | Leads.`Email` | Contact Email Primary | lowercase/trim | ✓(match key) | | | dedup/match key; blanks reduce match safety |
| 6 | Contact Email Secondary | Leads.`Secondary_Email` | Contact Email Secondary | | | | | |
| 7 | Job Title | Leads.`Job_Title` | Job Title | **picklist** | | | | **155-value restricted picklist** — free-text values will fail unless "auto-add new picklist values on import" is enabled, or pre-add values. Drives Contact_Role mapping. |
| 8 | Job Departments | Leads.`Job_Departments` | Job Departments | `;`→multiselect | | | | values must be in {C-Suite, Customer Success, Design, Engineering & Technical, Finance, Human Resources, Information Technology, Legal, Marketing, Operations, Product, Sales} |
| 9 | Job Function | Leads.`Job_Function` | Job Function (text) | | | | | free text OK |
| 10 | Current Job | *(drop)* | — | — | | | | TRUE/FALSE flag; no field |
| 11 | Email Guess | *(drop)* | — | | | | | no field |
| 12 | Person Linkedin Url | Leads.`Contact_Linkedin` | Contact Linkedin | | | | | |
| 13–15 | Contact Address City / State / Country | Leads.`Contact_Address_City` / `Contact_Address_State_Province` / `Contact_Address_Country_Region` | | | | | | **State=3,935-val picklist, Country=248-val picklist** → free-text values fail; map City (text) only, or normalize country names |
| 16 | Notes | Leads.`Description` | Description | | | | | long bio text (SQL/RTP) |
| 17 | Contact Email Opt Out | Leads.`Email_Opt_Out` | (boolean) | TRUE/FALSE | | | | |
| 18 | Contact Marketing Consent | Leads.`Contact_Marketing_Consent` | (boolean) | TRUE/FALSE | | | FALSE | |
| 19 | Company Industry | Leads.`Industry` | Company Industry | **picklist** | | | | **"Gaming" is NOT a valid option** (std 17-value list). Either add "Gaming"/"Ecommerce"/"OTT"/"Fintech"/"UX" to the picklist, or **drop** this column. See E. |
| 20 | Product Interest | Leads.`Product_Interest` | Product Interest | **SKU transform** | | | | line-level values ("Jurnii UX") are **invalid SKUs**; append plan type or alias-resolve (see Part 1 §G) |
| 21 | Type | *(drop from Lead)* | — | | | | | Brand/Agency/Platform → later becomes `Quoted_Item_Pricing_Tier` (Base/Agency/Markup) at quote time, not a Lead field |
| 22 | Had Meeting | *(drop)* | — | | | | | no Lead field; informational |
| 23 | Opportunity | *(drop / file partition)* | — | | | ✓ | | MQL/SQL/FTP/RTP = Opportunity **Type**; no Lead field, derived on Deal from Stage |
| 24 | State | *(drop unless Lost)* | (Leads.State = geographic!) | | | | | **No Lead commercial State field.** Open→drop. **Lost→** set `Lost_Reasons` + `Status`=Closed (see E) |
| 25 | Status | Leads.`Status` | Status | | | | New | {New, Working, Closed} ✓ |
| 26 | Stage | Leads.`Stage` | Stage | map invalid | ✓ | | Marketing Consent | {Marketing Consent…Renewal}; FTP "Contract Signed"→**Commercial Agreement** |
| 27 | Last Contact | *(drop)* | — | | | | | no clean field (`Last_Activity_Time` is system RO) |
| 28 | Lead Owner | Leads.`Owner` | Lead Owner | **user match** | | | current user | ownerlookup — only maps if the name = an active CRM user; most CSV owner names are **not** users → drop or leave default |
| 29–34 | Company Expansion Regional/Region/Continent/Sub Region/Country/Timeline | Leads.`Company_Expansion_*` | | multiselect | | | | region∈{EMEA,APAC,LATAM,NA}; country/sub-region picklists |
| 35–39 | Contact AOR Regional/Region/Continent/Sub Region/Country | Leads.`Contact_AOR_*` | | multiselect | | | | |
| 40–43 | Company AOO Region/Continent/Sub Region/Country | Leads.`Company_AOO_*` | | multiselect | | | | |
| 44 | Qualification : Crypto Casino | *(drop / optional custom)* | — | | | | | TRUE/FALSE; no Lead field. Create a boolean if needed for reporting. |
| 45–46 | Technographics / Technographics Evaluating | Leads.`Technographics` / `Technographics_Evaluating` | | `;`→multiselect | | | | 98-value picklist — validate values (e.g. "Bloomreach" ✓, "PlayTech" verify) |
| 47 | Contact (Role) AOR | Leads.`Contact_AOR` | Contact AOR (textarea) | | | | | bio/territory text |
| 48 | Contact (Role) Brands | Leads.`Contact_AOR_Brands` | | `;`→multiselect | | | | **only {Betfair, Paddy Power, Skybet, Winner, 888 Romania} valid** — other brand names fail |
| 49–51 | Contact (Role) Priority 1/2/3 | Leads.`Contact_AOR_Priority_1/2/3` | (textarea) | | | | | |
| 52 | Lead Referrer | Leads.`Lead_Referrer` | (text) | | | | | free text OK (Timothy, Elliot…) |
| 53 | Lead Source | Leads.`Lead_Source` | Lead Source | **picklist** | | | | "Trade Show / Event"→**Event**; "Google"→**(add or map)**; others valid |
| 54 | Priority | *(drop)* | — | | | | | no Lead field |
| 55 | Report | *(drop)* | — | | | | | |
| 56 | Category | *(drop → Account_Status later)* | — | | | | | Prospect/Client/Existing Customer/… maps to `Account_Status` post-conversion, not a Lead field |
| 57–64 | Contact Completed <Stage> At ×8 | Leads.`Contact_Completed_*_At` | (datetime) | ISO 8601 | | | | exist on Leads; carried to Contact by processLead. **All empty in CSVs.** |
| 65–68 | Address Flat/City/State/Country (company) | Leads.`Flat_House…`/`City`/`State`/`Country` | | | | | | `State`/`Country` are picklists → normalize |
| 69 | Company Phone | Leads.`Phone` | Company Phone | | | | | |
| 70 | Company Annual Revenue | Leads.`Annual_Revenue` | (currency) | numeric | | | | |
| 71 | Company Employee Count | Leads.`No_of_Employees` | (integer) | numeric | | | | |
| 72 | Company Subsidiary of | Leads.`Company_Subsidiary_of` | (text) | | | | | |
| 73 | Company Linkedin | Leads.`Company_Linkedin` | (text) | | | | | |
| 74 | Company Tier | Leads.`Company_Tier` | Company Tier | | | | | {1,2,3} ✓ |
| 75–77 | Jurnii Account Role / Created At / Org ID | *(drop)* | — | | | | | empty; no fields |
| 78 | Contract Primary Contact | *(drop)* | — | | | ✓ | | `Deal_Primary_Contact` set by automation |
| 79 | Contact Org | *(drop)* | — | | | | | empty |
| 80–92 | Contract Initial/Current Plan Products/Type/Brands + Dates | Leads.`Contract_Initial_*` / `Contract_Current_*` | | multiselect/date/int | | | | exist on Leads; **all empty in CSVs**. NB processLead reads *legacy* names so these won't seed the Deal even if filled (drift D-Low). |
| (Days Remaining, ACV Gap, Target ACV) | *(drop)* | — | | | ✓(formula) | | read-only formulas |
| Contract ACV (Target/Initial/Current) | Leads.`Contract_Initial_ACV`/`Contract_Current_ACV` | (currency) | | | | | empty in CSV |
| Contract Score * (9 cols) | *(drop)* | — | | | | | health scores belong on Deal/Account, not Lead; FTP/RTP have some values — capture post-import on the Deal if needed |
| Contract Upsell interest / Actions / Live discussion / % Active users | *(drop)* | — | | | | | no Lead fields |
| 113–120 | cio_* (Customer.io) | *(drop / external)* | — | | | | | no Lead fields. `cio_id` could seed a future external-key field; not now. |
| 123 | Full Name (dup) | *(ignore)* | — | | | | | duplicate header |

**Net importable Lead columns:** ~30 of 124. The remaining ~94 are zero-fill, derived, read-only, or have no destination.

---

## E. Row-level exception report (by class, with addresses)

Row numbers are **1-based file rows including the header** (so data row 1 = file row 2), matching how Zoho's import previewer counts.

| File | Rows | Problem | Severity | Target | Proposed correction | Block import? |
|---|---|---|---|---|---|---|
| **ALL** | every data row | `Company Industry` = "Gaming"/"Ecommerce"/"OTT"/"Fintech"/"UX"/"Other" — none valid in `Leads.Industry` | Medium | Leads.Industry | Add these as picklist options **or** drop the column from the mapping (recommended: drop — Industry isn't used by automation) | No (if dropped/unmapped) |
| **ALL** | rows with `Product Interest` (MQL 1, SQL 19, RTP 32; FTP 0) | line-level value invalid for SKU picklist | Medium | Leads.Product_Interest | append plan type → SKU (UX needs Fixed/Flex decision) **or** alias-resolve via `Product_Mapping_Aliases` | No (drop if unresolved; backfill later) |
| **ALL** | every data row | `Opportunity`, `State`(Open), `Had Meeting`, `Last Contact`, `Priority`, `Report`, `Category`, `cio_*` | Low | — | leave unmapped (no destination) | No |
| MQL | **175** (1 row) | `Last Name` blank (MANDATORY) | **High** | Leads.Last_Name | derive from Full Name / company, or fill placeholder | **Yes (that row)** |
| MQL | 15 rows | `Email` blank | Medium | Leads.Email | acceptable (Account_Key falls back to website); 1 row also lacks website → key=company slug | No |
| SQL | **25, 210, 217, 222** | `Last Name` blank | **High** | Leads.Last_Name | fill from Full Name; row 25 (`Joonas`, single name) → use "Joonas" or company | **Yes (those rows)** |
| SQL | 57 rows | `Email` blank (25% of file) | Medium–High | Leads.Email | reduces match safety & Contact creation; verify these are wanted; 2 rows also lack website | No (but review) |
| SQL | 8 rows | `Lead Source` = "Trade Show / Event" (invalid) | Low | Leads.Lead_Source | → **Event** | No |
| SQL | 1 row | `Lead Source` = "Google" (invalid) | Low | Leads.Lead_Source | add "Google" or → Website/Advertisement | No |
| FTP | **19 rows** (3,4,5,7,8,16,19,23,…) | `Last Name` blank (24% of file) | **High** | Leads.Last_Name | many are single-name ("Megan","Guy R-Nav") — split Full Name or fill | **Yes (those rows)** |
| FTP | **2 rows** | `Stage` = "Contract Signed" (invalid) | Medium | Leads.Stage | → **Commercial Agreement**; flag for Quote/contract backfill (these are effectively signed) | No (after remap) |
| FTP | 3 rows | `State` = Lost / `Status` = Closed | Medium | Leads.Status + Lost_Reasons | set `Status`=Closed (already) + add a `Lost_Reasons` (e.g. "No Commercial Interest") so conversion marks Contact/Deal Lost | No |
| RTP | **14,24,26,27,28,29** (6 rows) | `Last Name` blank | **High** | Leads.Last_Name | fill | **Yes (those rows)** |
| RTP | **row 94** | `Email` = `sergio.poves vidal@betssongroup.com` (space → invalid) | **High** | Leads.Email | remove space → `sergio.poves-vidal@…` or correct local part | **Yes (that row)** |
| RTP | 5 rows | `State`=Lost / `Status`=Closed (churned renewals) | Medium | Status + Lost_Reasons | set Lost_Reasons = "Churned / Did Not Renew" | No |
| RTP | 1 row | `Lead Source` = "Trade Show / Event" | Low | Lead_Source | → Event | No |
| RTP | 3 rows | `Email` blank | Medium | Email | website fallback | No |
| **ALL** | 1 cross-file dup | `nikola.grujanac@meridianbet.com` appears in **MQL + SQL** | Medium | — | dedupe (one person, two stages) — import with Email matching so the later file updates, not duplicates | No |
| **ALL** | 15 companies span files | e.g. `flutter uk & ireland` (SQL+FTP+RTP), `bet365` (MQL+SQL) | Info | Account_Key | **by design** collapse to one Account+Deal; furthest-stage contact wins (never-regress) | No |
| **ALL** | duplicate header `Full Name`; SQL: 35 blank headers + dup `cio_…RFC3339` | structural | Low | — | ignore extra/blank columns in the mapping; do not map blank-named columns | No |

**No invalid dates, currencies, or numbers** were detected in the populated commercial columns (the contract/score numeric columns are empty in MQL/SQL; FTP/RTP score columns are out of scope for the Lead import).

---

## F. CSV readiness summary

| Metric | MQL | SQL | FTP | RTP |
|---|---|---|---|---|
| Total data rows | 174 | 225 | 78 | 172 |
| **Mandatory (Last_Name) missing** | 1 | 4 | **19** | 6 |
| Invalid email format | 0 | 0 | 0 | **1** |
| Blank email | 15 | **57** | 0 | 3 |
| Invalid `Stage` | 0 | 0 | **2** ("Contract Signed") | 0 |
| Invalid `Status` | 0 | 0 | 0 | 0 |
| Invalid `Lead Source` | 0 | 9 | 0 | 1 |
| `Industry`="Gaming"/other (invalid) | 171 | 43 | 24 | 56 |
| Product Interest present (line-level, needs transform) | 1 | 19 | 0 | 32 |
| Lost rows (State=Lost) | 0 | 0 | 3 | 5 |
| Distinct companies / multi-contact | 170 / 3 | 134 / 49 | 67 / 9 | 30 / 18 |
| Quote-eligible (FTP/RTP) | 0 | 0 | 78 | 172 |
| **Quote-ready from CSV alone** | 0 | 0 | **0** | **0** |
| Quote-blocked (needs plan type + brands [+ dates]) | n/a | n/a | 78 | 172 |

**Per-file classification:**
- **MQL — Ready after non-blocking cleanup.** Fix 1 missing Last_Name; decide Industry (drop). Stage/Status/Lead Source all valid. Not quote-eligible (correct).
- **SQL — Ready after non-blocking cleanup.** Fix 4 missing Last_Name; remap 9 Lead Source values; decide Industry; **review the 57 blank emails** (acceptable but lowers match quality). Different column layout — map by **header name**, ignore the 35 blank columns. Not quote-eligible.
- **FTP — Ready after correction (more involved).** Fix **19 missing Last_Name** (24%); remap 2 "Contract Signed"→Commercial Agreement; add `Lost_Reasons` to 3 Lost rows. **No Product Interest at all** → every FTP row is quote-eligible but quote-blocked until product + plan type + brands are supplied at backfill.
- **RTP — Ready after correction.** Fix 6 missing Last_Name + **1 malformed email** (row 94); add `Lost_Reasons` to 5 churned rows; remap 1 Lead Source. Renewals imply existing contracts → all quote-eligible but quote-blocked pending contract/brand data.

**No file is structurally incompatible.** All four are **"Ready after cleanup"** for the **Lead import**; **none is quote-ready** without a supervised backfill (by design — see Part 3).

**Matching / duplicate strategy:** CRM currently holds **no real customer records** (only "Solomon Corp" + a leftover E2E test account), so collision against existing data ≈ zero. Use **Email as the import match field** (handles the 1 cross-file duplicate and makes re-runs safe); rows without email create new. Intra-import company overlap is resolved automatically by `Account_Key` at conversion (one Account + one Deal per domain).
