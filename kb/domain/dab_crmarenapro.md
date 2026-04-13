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
| issueid__c | text | FK → `issue__c.id` |