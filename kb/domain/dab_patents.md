# Knowledge Base: Patents Dataset — DataAgentBench Production Agent

---

## 1. Dataset Overview

This knowledge base covers two databases — a SQLite publication database containing natural-language metadata for published patents, and a PostgreSQL CPC definition database containing the hierarchical classification structure for Cooperative Patent Classification codes — used together to answer analytical queries about patent filings, technology areas, assignees, and citations.

---

## 2. CRITICAL — MCP Tool Mapping

| Tool Name | DB Type | Contains |
|---|---|---|
| `query_sqlite_patents` | SQLite | `publicationinfo` table — patent publication metadata including dates, inventors, CPC codes, citations, assignees, abstracts, claims |
| `query_postgres_patents` | PostgreSQL | `cpc_definition` table — CPC symbol hierarchy, definitions, titles, levels, parent/child relationships |

**NEVER swap these tools.** CPC definitions are ONLY in `query_postgres_patents`. Patent records are ONLY in `query_sqlite_patents`.

---

## 3. Tables and Collections

### Table: `publicationinfo` (via `query_sqlite_patents`)

Full description: One record per patent publication. Contains natural-language metadata for published patents including identifiers, dates, classification codes, relationships, and citations.

| Field | Type | Meaning |
|---|---|---|
| `Patents_info` | TEXT | Natural-language summary including `application_number`, `publication_number`, `assignee_harmonized`, `country_code` — must be parsed with LIKE/INSTR for filtering |
| `kind_code` | TEXT | Type of document issued (e.g., "B2" = granted patent) |
| `application_kind` | TEXT | Type of application (e.g., "utility patent application") |
| `pct_number` | TEXT | PCT application number if applicable |
| `family_id` | INTEGER | Links related patents in the same family |
| `title_localized` | TEXT | Patent title |
| `abstract_localized` | TEXT | Patent abstract |
| `claims_localized_html` | TEXT | Claims in HTML format |
| `description_localized_html` | TEXT | Description in HTML format |
| `publication_date` | TEXT | Natural-language date, e.g., `"March 15th, 2020"` |
| `filing_date` | TEXT | Natural-language date, e.g., `"January 3rd, 2019"` |
| `grant_date` | TEXT | Natural-language date, e.g., `"July 22nd, 2021"` |
| `priority_date` | TEXT | Natural-language date |
| `priority_claim` | TEXT | List of priority applications |
| `inventor_harmonized` | TEXT | Harmonized inventor list |
| `examiner` | TEXT | USPTO examiner(s) |
| `uspc` | TEXT | US Patent Classification codes |
| `ipc` | TEXT | International Patent Classification codes |
| `cpc` | TEXT | JSON-like list of CPC entries, each with a `code` field and metadata — **primary join key to `cpc_definition`** |
| `citation` | TEXT | Cited patents and non-patent literature |
| `parent` | TEXT | Parent patent applications |
| `child` | TEXT | Child patent applications |
| `entity_status` | TEXT | Legal entity status (e.g., "small entity", "large entity") |
| `art_unit` | TEXT | USPTO art unit |

**Important value formats:**
- All dates (`publication_date`, `filing_date`, `grant_date`, `priority_date`) are stored as **natural-language strings** (e.g., `"March 15th, 2020"`). Year extraction requires `LIKE '%2022%'` or `SUBSTR`/`INSTR` parsing — NOT date functions.
- `Patents_info` contains assignee info as free text; filter with `LIKE '%UNIV CALIFORNIA%'` or similar.
- `cpc` field is a JSON-like string; CPC codes must be extracted via string parsing (e.g., `LIKE '%H04L%'`).
- Country codes are embedded in `Patents_info`; Germany = `country_code: DE` or similar text pattern.
- `citation` field contains free-text references; cited patent assignees must be parsed from this field.

---

### Table: `cpc_definition` (via `query_postgres_patents`)

Full description: One record per CPC symbol. Contains the hierarchical structure, definitions, and metadata for all CPC codes.

| Field | Type | Meaning |
|---|---|---|
| `applicationReferences` | text | Informative references to related applications |
| `breakdownCode` | boolean | Whether the symbol is a breakdown code |
| `childGroups` | text | JSON-like list of child CPC symbols |
| `children` | text | Additional child references |
| `dateRevised` | double precision | Revision date (stored as numeric, not text) |
| `definition` | text | Full definition of the CPC symbol |
| `glossary` | text | Glossary terms for the symbol |
| `informativeReferences` | text | Additional informative references |
| `ipcConcordant` | text | IPC concordance mapping |
| `level` | double precision | Hierarchical level (1–5); **level 5 = most specific group codes; level 4 = group codes one level up** |
| `limitingReferences` | text | Scope-limiting references |
| `notAllocatable` | boolean | Whether this symbol can be assigned to a patent |
| `parents` | text | JSON-like list of parent CPC symbols |
| `precedenceLimitingReferences` | text | Precedence-limiting references |
| `residualReferences` | text | Residual references |
| `rules` | text | Rules for applying the CPC symbol |
| `scopeLimitingReferences` | text | Scope-limiting references |
| `status` | text | Status: `"active"` or `"deleted"` |
| `symbol` | text | **CPC classification code** — primary join key to `cpc` field in `publicationinfo` |
| `synonyms` | text | Synonyms for the symbol |
| `titleFull` | text | **Full descriptive title of the CPC symbol** — use this for human-readable technology area names |
| `titlePart` | text | Abbreviated/partial title |

**Important value formats:**
- `level` is stored as `double precision` — compare as `level = 5` or `level = 4` (numeric, not string).
- `symbol` format examples: `"H04L63/00"`, `"A61B5/00"` — must match exactly against codes extracted from `publicationinfo.cpc`.
- `status` filter: prefer `status = 'active'` to exclude deleted codes.
- CPC hierarchy: level 1 = section, level 2 = class, level 3 = subclass, level 4 = group, level 5 = subgroup (most specific).

---

## 4. Join Keys

### Primary Join: `publicationinfo.cpc` ↔ `cpc_definition.symbol`

- The `cpc` field in `publicationinfo` (SQLite) contains a JSON-like string with CPC codes embedded.
- The `symbol` field in `cpc_definition` (PostgreSQL) contains the exact CPC code string.
- **Format mismatch risk:** `cpc` in SQLite is a multi-value string (list of entries); individual codes must be extracted via string matching (LIKE, INSTR, or JSON parsing if supported) before joining to `symbol` in PostgreSQL.
- **Workflow:** Extract CPC codes from SQLite first → look up matching `symbol` rows in PostgreSQL, or extract symbols from PostgreSQL first → filter patents in SQLite by matching code strings.

### Verbatim Hints (from official DAB hints):
> The `cpc` field in the `publicationinfo` table of `publication_database` contains CPC classification codes. The full definitions for these CPC codes are located in the `cpc_definition` table of `CPCDefinition_database`, where each row includes fields such as `symbol` and `titleFull`.

> The descriptive title for each CPC code can be found in the `titleFull` field of the `cpc_definition` table.

> Citation information is stored in