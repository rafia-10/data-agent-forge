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

> Citation information is stored in the `citation` field of the `publicationinfo` table as a JSON-like string containing cited patent publication numbers, assignees, and non-patent literature references.

---

## 5. Critical Domain Knowledge

### Verbatim Official Hints (complete set):
> The `cpc` field in `publicationinfo` contains CPC classification codes. The full definitions are in `cpc_definition.titleFull`.

> The descriptive title for each CPC code can be found in the `titleFull` field of `cpc_definition`.

> Citation information is stored in the `citation` field of `publicationinfo` as a JSON-like string. To find patents that cite a specific assignee, parse the `citation` field for entries referencing that assignee's publication numbers.

> All dates in `publicationinfo` (`publication_date`, `filing_date`, `grant_date`, `priority_date`) are stored as natural-language strings (e.g., "March 15th, 2020"). Year extraction requires LIKE '%2022%' or SUBSTR/INSTR — NOT SQL date functions.

> The `Patents_info` field in `publicationinfo` contains a natural-language summary including `assignee_harmonized`, `application_number`, `publication_number`, and `country_code`. Use LIKE for filtering by assignee or country.

### Key Query Patterns:
### Key Query Patterns:
- **Filter by technology area (CPC):** Extract codes from `publicationinfo.cpc` using `LIKE '%H04L%'` → look up `titleFull` in `cpc_definition` where `symbol LIKE 'H04L%'`
- **Filter by assignee:** `Patents_info LIKE '%UNIVERSITY OF CALIFORNIA%'` (case-insensitive with UPPER() or ILIKE)
- **Filter by country:** `Patents_info LIKE '%country_code: DE%'` for Germany
- **Filter by year:** `publication_date LIKE '%2020%'` or `filing_date LIKE '%2019%'`
- **Cited patents:** Parse `citation` field for `publication_number` values referencing a specific assignee
- **CPC hierarchy traversal:** Actual levels in this database are 2, 4, 5, 7–19. Level 5 = subclass codes (format: A01H, A22B — 4 characters). NOT the standard 1–5 hierarchy.
- **CPC codes filter:** Use `status = 'published'` — NOT `'active'`. Status values are `'published'` and `'frozen'` only. `'active'` does not exist and returns 0 rows.
- **Level 5 query:** `SELECT symbol, "titleFull" FROM cpc_definition WHERE level = 5.0 AND status = 'published'` — returns 677 rows.
- **Year extraction from natural-language dates:** Use `SUBSTR(filing_date, LENGTH(filing_date)-3, 4)` — year is always the last 4 characters (e.g., "January 3rd, 2019" → "2019").

### Query 1 — EMA of filings by CPC level-5 code, best year = 2022

Step 1 — PostgreSQL: get all level-5 published CPC symbols:
```sql
SELECT symbol, "titleFull" FROM cpc_definition WHERE level = 5.0 AND status = 'published'
```

Step 2 — SQLite: get filing year and cpc text for all patents:
SELECT 
  SUBSTR(filing_date, LENGTH(filing_date)-3, 4) AS year,
  cpc,
  COUNT(*) as filing_count
FROM publicationinfo
WHERE filing_date IS NOT NULL 
  AND cpc IS NOT NULL
  AND CAST(SUBSTR(filing_date, LENGTH(filing_date)-3, 4) AS INTEGER) BETWEEN 2015 AND 2023
GROUP BY year, cpc
ORDER BY year
```

Step 3 — Synthesize (Python): for each level-5 symbol, check if it appears in cpc text using LIKE matching. Count filings per (year, symbol). Compute EMA with alpha=0.2 going forward through years. Find the year with maximum EMA per symbol. Return only symbols where best year = 2022.

### Common Pitfalls:
- `status = 'active'` DOES NOT EXIST — returns 0 rows. Always use `status = 'published'`.
- `level` is `double precision` — use `level = 5.0` not `level = 5`.
- `cpc` field is multi-value JSON-like string — never direct-join; use LIKE matching.
- All date fields are free-text — `strftime` and date functions WILL FAIL.
- Year is at the END of the date string — use `SUBSTR(filing_date, LENGTH(filing_date)-3, 4)`.

### Query 1 — EMA of patent filings by CPC level-5 code, best year = 2022

**Step 1 — SQLite:** Extract filing year and individual CPC codes:
```sql
SELECT 
  CAST(SUBSTR(filing_date, LENGTH(filing_date)-3, 4) AS INTEGER) AS year,
  cpc
FROM publicationinfo 
WHERE filing_date IS NOT NULL 
  AND cpc IS NOT NULL
  AND CAST(SUBSTR(filing_date, LENGTH(filing_date)-3, 4) AS INTEGER) BETWEEN 2015 AND 2023
```

**Step 2 — PostgreSQL:** Get all level-5 active CPC symbols:
```sql
SELECT symbol, "titleFull" 
FROM cpc_definition 
WHERE level = 5 AND status = 'active'
```

**Step 3 — Synthesize (Python pre-computation):**
- Parse each patent's `cpc` field to extract individual codes using LIKE matching
- Count filings per (year, cpc_code) pair
- For each cpc_code, compute EMA across years with alpha=0.2:
  `EMA_t = alpha * count_t + (1 - alpha) * EMA_{t-1}`
- Find the year with maximum EMA per code
- Return only level-5 codes whose best year = 2022

**CRITICAL:** Year is at the END of the natural-language date string (e.g., "January 3rd, 2019" → last 4 chars = "2019"). Use `SUBSTR(filing_date, LENGTH(filing_date)-3, 4)` to extract year.

### Common Pitfalls:
- `cpc` in `publicationinfo` is a multi-value JSON-like string — never direct-join; always use LIKE/INSTR for code matching.
- All date fields are free-text — `strftime` and date functions WILL FAIL; use string patterns.
- `assignee_harmonized` is embedded in `Patents_info` free text — extract with LIKE, not a separate column.
- `level` is `double precision`, not integer — compare as `level = 5.0` or `level = 4.0`.
