# CRMArena Pro — Knowledge Base Document

---

## 1. Dataset Overview

The `crmarenapro` dataset is a multi-database CRM simulation spanning six databases (SQLite, DuckDB, PostgreSQL) covering sales pipeline, support cases, products/orders, activities, territories, and core CRM entities from a Salesforce-style data model.

---

## 2. CRITICAL — MCP Tool Mapping

| Tool Name | DB Type | Contains |
|---|---|---|
| `query_sqlite_crmarenapro_core` | SQLite | `User`, `Account`, `Contact` |
| `query_duckdb_crmarenapro_sales` | DuckDB | `Contract`, `Lead`, `Opportunity`, `OpportunityLineItem`, `Quote`, `QuoteLineItem` |
| `query_postgres_crmarenapro` | PostgreSQL | `Case`, `knowledge__kav`, `issue__c`, `casehistory__c`, `emailmessage`, `livechattranscript` |
| `query_sqlite_crmarenapro_products` | SQLite | `ProductCategory`, `Product2`, `ProductCategoryProduct`, `Pricebook2`, `PricebookEntry`, `Order`, `OrderItem` |
| `query_duckdb_crmarenapro_activities` | DuckDB | `Event`, `Task`, `VoiceCallTranscript__c` |
| `query_sqlite_crmarenapro_territory` | SQLite | `Territory2`, `UserTerritory2Association` |

---

## 3. Tables and Collections

### 3.1 `core_crm` — `query_sqlite_crmarenapro_core`

#### `User`
Sales team members / agents.
| Field | Type | Meaning |
|---|---|---|
| Id | TEXT | Unique user/agent identifier |
| FirstName | TEXT | First name |
| LastName | TEXT | Last name |
| Email | TEXT | Email address |
| Phone | TEXT | Phone number |
| Username | TEXT | Login username |
| Alias | TEXT | Short alias |
| LanguageLocaleKey | TEXT | Language setting |
| EmailEncodingKey | TEXT | Email encoding |
| TimeZoneSidKey | TEXT | Timezone |
| LocaleSidKey | TEXT | Locale |

#### `Account`
Company/customer records.
| Field | Type | Meaning |
|---|---|---|
| Id | TEXT | Unique account identifier |
| Name | TEXT | Company name |
| Phone | TEXT | Phone number |
| Industry | TEXT | Industry vertical |
| Description | TEXT | Free-text description |
| NumberOfEmployees | REAL | Employee count |
| ShippingState | TEXT | Two-letter US state abbreviation (e.g., `CA`) — used for geographic queries |

#### `Contact`
Individual people associated with accounts.
| Field | Type | Meaning |
|---|---|---|
| Id | TEXT | Unique contact identifier |
| FirstName | TEXT | First name |
| LastName | TEXT | Last name |
| Email | TEXT | Email address |
| AccountId | TEXT | FK → `Account.Id` |

---

### 3.2 `sales_pipeline` — `query_duckdb_crmarenapro_sales`

#### `Contract`
Signed contracts linked to accounts.
| Field | Type | Meaning |
|---|---|---|
| Id | VARCHAR | Unique contract identifier |
| AccountId | VARCHAR | FK → `Account.Id` |
| Status | VARCHAR | Contract status (e.g., `Activated`) |
| StartDate | VARCHAR | Contract start date (string, ISO format) |
| CustomerSignedDate | VARCHAR | Date customer signed |
| CompanySignedDate | VARCHAR | Date company signed — **used as the authoritative "closed" date for sales cycle and sales amount calculations** |
| Description | VARCHAR | Free-text description |
| ContractTerm | VARCHAR | Duration in months |

#### `Lead`
Prospective customers not yet converted.
| Field | Type | Meaning |
|---|---|---|
| Id | VARCHAR | Unique lead identifier |
| FirstName | VARCHAR | First name |
| LastName | VARCHAR | Last name |
| Email | VARCHAR | Email address |
| Phone | VARCHAR | Phone number |
| Company | VARCHAR | Company name |
| Status | VARCHAR | Lead status |
| ConvertedContactId | VARCHAR | FK → `Contact.Id` if converted |
| ConvertedAccountId | VARCHAR | FK → `Account.Id` if converted |
| Title | VARCHAR | Job title |
| CreatedDate | VARCHAR | Creation date |
| ConvertedDate | VARCHAR | Conversion date |
| IsConverted | BIGINT | 1 = converted, 0 = not |
| OwnerId | VARCHAR | FK → `User.Id` |

#### `Opportunity`
Sales deals/opportunities.
| Field | Type | Meaning |
|---|---|---|
| Id | VARCHAR | Unique opportunity identifier |
| ContractID__c | VARCHAR | FK → `Contract.Id` |
| AccountId | VARCHAR | FK → `Account.Id` |
| ContactId | VARCHAR | FK → `Contact.Id` |
| OwnerId | VARCHAR | FK → `User.Id` (the agent) |
| Probability | VARCHAR | Win probability % |
| Amount | VARCHAR | Deal amount |
| StageName | VARCHAR | Current stage: `Qualification`, `Discovery`, `Quote`, `Negotiation`, `Closed` |
| Name | VARCHAR | Opportunity name |
| Description | VARCHAR | Free-text description |
| CreatedDate | VARCHAR | Creation date |
| CloseDate | VARCHAR | Expected/actual close date |

#### `OpportunityLineItem`
Line items on an opportunity.
| Field | Type | Meaning |
|---|---|---|
| Id | VARCHAR | Unique line item identifier |
| OpportunityId | VARCHAR | FK → `Opportunity.Id` |
| Product2Id | VARCHAR | FK → `Product2.Id` |
| PricebookEntryId | VARCHAR | FK → `PricebookEntry.Id` |
| Quantity | VARCHAR | Quantity |
| TotalPrice | VARCHAR | Total price |

#### `Quote`
Price quotes linked to opportunities.
| Field | Type | Meaning |
|---|---|---|
| Id | VARCHAR | Unique quote identifier |
| OpportunityId | VARCHAR | FK → `Opportunity.Id` |
| AccountId | VARCHAR | FK → `Account.Id` |
| ContactId | VARCHAR | FK → `Contact.Id` |
| Name | VARCHAR | Quote name |
| Description | VARCHAR | Free-text description |
| Status | VARCHAR | Quote status |
| CreatedDate | VARCHAR | Creation date |
| ExpirationDate | VARCHAR | Expiration date |

#### `QuoteLineItem`
Line items on a quote.
| Field | Type | Meaning |
|---|---|---|
| Id | VARCHAR | Unique line item identifier |
| QuoteId | VARCHAR | FK → `Quote.Id` |
| OpportunityLineItemId | VARCHAR | FK → `OpportunityLineItem.Id` |
| Product2Id | VARCHAR | FK → `Product2.Id` |
| PricebookEntryId | VARCHAR | FK → `PricebookEntry.Id` |
| Quantity | VARCHAR | Quantity |
| UnitPrice | VARCHAR | Unit price |
| Discount | VARCHAR | Discount % |
| TotalPrice | VARCHAR | Total price |

---

### 3.3 `support` — `query_postgres_crmarenapro`

#### `Case`
Customer support cases.
| Field | Type | Meaning |
|---|---|---|
| id | text | Unique case identifier |
| priority | text | Priority level (e.g., `High`, `Medium`, `Low`) |
| subject | text | Case subject |
| description | text | Case description |
| status | text | Case status (e.g., `Open`, `Closed`) |
| contactid | text | FK → `Contact.Id` |
| createddate | text | Date/time case was opened |
| closeddate | text | Date/time case was closed — **used for handle time calculation** |
| orderitemid__c | text | FK → `OrderItem.Id` — links case to a specific order item/product |
| issueid__c | text | FK → `issue__c.id` || accountid | text | FK → `Account.Id` |

#### `knowledge__kav`
Knowledge base articles.
| Field | Type | Meaning |
|---|---|---|
| id | text | Unique article identifier |
| title | text | Article title |
| summary | text | Short summary |
| faq_answer__c | text | Full FAQ answer text — use ILIKE for search |
| urlname | text | URL-friendly name |

#### `issue__c`
Issue category/type lookup.
| Field | Type | Meaning |
|---|---|---|
| id | text | Unique issue identifier |
| name | text | Issue name/category |
| description__c | text | Free-text issue description |

#### `casehistory__c`
Audit log of field changes on Cases.
| Field | Type | Meaning |
|---|---|---|
| id | text | Unique history record identifier |
| caseid__c | text | FK → `Case.id` |
| field__c | text | Name of the field that changed |
| oldvalue__c | text | Previous value |
| newvalue__c | text | New value |
| createddate | text | Timestamp of the change |

#### `emailmessage`
Emails linked to support cases.
| Field | Type | Meaning |
|---|---|---|
| id | text | Unique email identifier |
| parentid | text | FK → `Case.id` |
| fromaddress | text | Sender email address |
| toids | text | Recipient email address(es) |
| messagedate | text | Date/time email was sent |
| textbody | text | Full email body text |

#### `livechattranscript`
Live chat session transcripts.
| Field | Type | Meaning |
|---|---|---|
| id | text | Unique transcript identifier |
| caseid | text | FK → `Case.id` |
| accountid | text | FK → `Account.Id` |
| contactid | text | FK → `Contact.Id` |
| body | text | Full chat transcript text — use ILIKE for search |

---

### 3.4 `products` — `query_sqlite_crmarenapro_products`

#### `Product2`
Product catalog.
| Field | Type | Meaning |
|---|---|---|
| Id | TEXT | Unique product identifier |
| Name | TEXT | Product name |
| Description | TEXT | Product description |
| IsActive | INTEGER | 1 = active, 0 = inactive |
| External_ID__c | TEXT | External system identifier |

#### `Order` / `OrderItem`
Orders linked to accounts; order items link orders to products.
| Field | Type | Meaning |
|---|---|---|
| Order.Id | TEXT | Unique order identifier |
| Order.AccountId | TEXT | FK → `Account.Id` |
| OrderItem.Id | TEXT | Unique order item identifier |
| OrderItem.OrderId | TEXT | FK → `Order.Id` |
| OrderItem.Product2Id | TEXT | FK → `Product2.Id` |

#### `ProductCategory` / `ProductCategoryProduct`
Category taxonomy; `ProductCategoryProduct` is the junction table linking products to categories.

---

### 3.5 `activities` — `query_duckdb_crmarenapro_activities`

#### `Event`
Calendar events.
| Field | Type | Meaning |
|---|---|---|
| Id | VARCHAR | Unique event identifier |
| WhatId | VARCHAR | FK → `Case.id` or `Opportunity.Id` |
| OwnerId | VARCHAR | FK → `User.Id` |
| StartDateTime | VARCHAR | Event start date/time |
| DurationInMinutes | INTEGER | Duration in minutes |
| Location | VARCHAR | Event location |
| IsAllDayEvent | INTEGER | 1 = all-day event |

#### `Task`
To-do items.
| Field | Type | Meaning |
|---|---|---|
| Id | VARCHAR | Unique task identifier |
| WhatId | VARCHAR | FK → related object |
| Priority | VARCHAR | Priority level |
| Status | VARCHAR | Task status |
| ActivityDate | VARCHAR | Due date |

#### `VoiceCallTranscript__c`
Voice call transcripts.
| Field | Type | Meaning |
|---|---|---|
| Id | VARCHAR | Unique transcript identifier |
| OpportunityId__c | VARCHAR | FK → `Opportunity.Id` |
| LeadId__c | VARCHAR | FK → `Lead.Id` |
| Body__c | VARCHAR | Full transcript text — use ILIKE for search |

---

### 3.6 `territory` — `query_sqlite_crmarenapro_territory`

#### `Territory2`
Sales territories.
| Field | Type | Meaning |
|---|---|---|
| Id | TEXT | Unique territory identifier |
| Name | TEXT | Territory name |
| Description | TEXT | Comma-separated US state abbreviations (e.g., `"MO,KS,OK"`) |

#### `UserTerritory2Association`
Maps users to territories.
| Field | Type | Meaning |
|---|---|---|
| UserId | TEXT | FK → `User.Id` |
| Territory2Id | TEXT | FK → `Territory2.Id` |

---

## 4. Join Keys

| Left Table | Left Field | Right Table | Right Field | Notes |
|---|---|---|---|---|
| `Case` (PostgreSQL) | `id` | `Event` (DuckDB) | `WhatId` | Case ↔ calendar events |
| `Case` (PostgreSQL) | `accountid` | `Account` (SQLite) | `Id` | Case ↔ account |
| `Opportunity` (DuckDB) | `AccountId` | `Account` (SQLite) | `Id` | Opportunity ↔ account |
| `Opportunity` (DuckDB) | `OwnerId` | `User` (SQLite) | `Id` | Opportunity ↔ agent |
| `Order` (SQLite) | `AccountId` | `Account` (SQLite) | `Id` | Order ↔ account |
| `OrderItem` (SQLite) | `Product2Id` | `Product2` (SQLite) | `Id` | Order item ↔ product |
| `Quote` (DuckDB) | `OpportunityId` | `Opportunity` (DuckDB) | `Id` | Quote ↔ opportunity |
| `Case` (PostgreSQL) | `issueid__c` | `issue__c` (PostgreSQL) | `id` | Case ↔ issue type |
| `Case` (PostgreSQL) | `orderitemid__c` | `OrderItem` (SQLite) | `Id` | Case ↔ ordered product |
| `UserTerritory2Association` (SQLite) | `UserId` | `User` (SQLite) | `Id` | User ↔ territory |

---

## 5. Critical Domain Knowledge

### Verbatim Official Hints:
> Some IDs in the crmarenapro dataset have a leading `#` character (e.g., `#0SOB000000024cAMAY`). When joining across databases, strip the leading `#` using LTRIM or REPLACE before comparing IDs. Approximately 25% of records may be affected.

> Some text fields (names, descriptions) may have trailing whitespace. Use TRIM() when comparing or displaying text values. Approximately 20% of text fields are affected.

### Data Quality Rules:
- **Leading `#` on IDs:** ~25% of IDs across tables have a leading `#`. Strip with `LTRIM(Id, '#')` or `REPLACE(Id, '#', '')` before cross-database joins.
- **Trailing whitespace:** ~20% of text fields have trailing spaces. Apply `TRIM()` on name/description fields in WHERE clauses and output.
- **Date fields as strings:** `createddate`, `closeddate`, `StartDateTime`, etc. are VARCHAR — cast appropriately before arithmetic.

### Common Query Patterns:
- **Case handle time:** `CAST(closeddate AS TIMESTAMP) - CAST(createddate AS TIMESTAMP)` in hours or days.
- **Agent workload:** Count `Case.id` per agent via `Case.ownerid → User.Id`.
- **Account territory lookup:** `Account.ShippingState` matched against comma-separated `Territory2.Description` (use LIKE `'%CA%'`).
- **FAQ search:** `knowledge__kav.faq_answer__c ILIKE '%keyword%'`.
- **Transcript search:** `livechattranscript.body ILIKE '%keyword%'` or `VoiceCallTranscript__c.Body__c ILIKE '%keyword%'`.
