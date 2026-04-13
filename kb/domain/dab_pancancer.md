# PanCancer Atlas DataAgentBench Knowledge Base

---

## 1. Dataset Overview

The PanCancer Atlas dataset combines clinical metadata (PostgreSQL) with molecular profiling data including somatic mutations and RNA-seq expression (SQLite/DuckDB) for patients across multiple cancer types.

---

## 2. CRITICAL — MCP Tool Mapping

| Tool Name | DB Type | Contains |
|---|---|---|
| `query_postgres_pancancer` | PostgreSQL | `clinical_info` table — patient clinical metadata, demographics, histology, survival, cancer type |
| `query_duckdb_pancancer_molecular` | DuckDB (SQLite) | `Mutation_Data` table — somatic mutation calls per patient/gene; `RNASeq_Expression` table — normalized RNA-seq expression per patient/gene |

---

## 3. Tables and Collections

### Table: `clinical_info` (PostgreSQL via `query_postgres_pancancer`)

Full description: Contains clinical information for patients in the PanCancer Atlas, including patient identifiers, cancer type acronyms, demographics, diagnosis records, treatment outcomes, survival status, and other clinical annotations.

| Field | Type | Meaning |
|---|---|---|
| `Patient_description` | text | Patient identifier — **join key** to molecular data `ParticipantBarcode` |
| `days_to_birth` | double precision | Days from birth to diagnosis (negative value = born before diagnosis) |
| `days_to_death` | text | Days from diagnosis to death (stored as text; may be NULL if alive) |
| `days_to_last_followup` | text | Days from diagnosis to last follow-up (stored as text) |
| `days_to_initial_pathologic_diagnosis` | double precision | Days to initial pathologic diagnosis |
| `age_at_initial_pathologic_diagnosis` | double precision | Age in years at initial diagnosis |
| `icd_10` | text | ICD-10 diagnosis code |
| `tissue_retrospective_collection_indicator` | text | Whether tissue was retrospectively collected |
| `icd_o_3_histology` | text | ICD-O-3 histology code and description — **used for histological type classification** |
| `tissue_prospective_collection_indicator` | text | Whether tissue was prospectively collected |
| `history_of_neoadjuvant_treatment` | text | Neoadjuvant treatment history |
| `icd_o_3_site` | text | ICD-O-3 anatomical site code |
| `tumor_tissue_site` | text | Tumor tissue site description |
| `new_tumor_event_after_initial_treatment` | text | Whether a new tumor event occurred after initial treatment |

> **Note:** The `clinical_info` table contains over 100 fields. Key fields for the target queries include:
> - Cancer type: look for a field containing cancer type acronym (e.g., `acronym`, `type`, or similar — query the table to discover the exact column name for cancer type filtering such as `LGG` or `BRCA`)
> - Vital status: field indicating alive/dead (e.g., `vital_status`)
> - Gender/sex: field indicating patient sex (e.g., `gender`)
> - Histology: `icd_o_3_histology` contains histological type annotations; **values enclosed in square brackets (e.g., `[Not Available]`, `[Unknown]`) must be excluded** from histology-based analyses

**Important value formats for `clinical_info`:**
- Histology values enclosed in square brackets (e.g., `[Not Available]`, `[Discrepancy]`, `[Unknown]`) are invalid/missing annotations and must be filtered out using: `icd_o_3_histology NOT LIKE '[%]'`
- `days_to_death` and `days_to_last_followup` are stored as **text**, not numeric — cast with `CAST(... AS FLOAT)` or `NULLIF` as needed
- Cancer type acronym field must be identified by querying schema; likely column names: `acronym`, `type`, `Study`, or `cancer_type`
- Vital status values: typically `'Alive'` or `'Dead'` (exact case must be verified by querying)
- Gender values: typically `'FEMALE'` or `'MALE'` (exact case must be verified by querying)

---

### Table: `Mutation_Data` (DuckDB via `query_duckdb_pancancer_molecular`)

Full description: Contains somatic mutation calls for patients in the PanCancer Atlas, one row per mutation event per patient.

| Field | Type | Meaning |
|---|---|---|
| `ParticipantBarcode` | VARCHAR | Patient identifier — **join key** to `clinical_info.Patient_description` |
| `Tumor_SampleBarcode` | VARCHAR | Tumor sample identifier |
| `Tumor_AliquotBarcode` | VARCHAR | Tumor aliquot identifier |
| `Normal_SampleBarcode` | VARCHAR | Normal control sample identifier |
| `Normal_AliquotBarcode` | VARCHAR | Normal control aliquot identifier |
| `Normal_SampleTypeLetterCode` | VARCHAR | Sample type abbreviation for the normal sample |
| `Hugo_Symbol` | VARCHAR | Gene symbol of the mutation (e.g., `TP53`, `CDH1`) — **filter on this for gene-specific queries** |
| `HGVSp_Short` | VARCHAR | Protein-level mutation annotation (e.g., `p.E542K`) |
| `Variant_Classification` | VARCHAR | Classification of the mutation (e.g., `Missense_Mutation`, `Nonsense_Mutation`) |
| `HGVSc` | VARCHAR | Coding DNA sequence mutation annotation |
| `CENTERS` | VARCHAR | Contributing sequencing center |
| `FILTER` | VARCHAR | Mutation filter status — **`'PASS'` indicates reliable/high-confidence mutation calls** |

**Important value formats for `Mutation_Data`:**
- `Hugo_Symbol` is case-sensitive: use exact gene symbols (e.g., `'CDH1'`, `'IGF2'`)
- `FILTER = 'PASS'` is the standard for reliable mutation entries — **required for query3**
- A patient "has a mutation" in a gene if they appear at least once in `Mutation_Data` with that `Hugo_Symbol` (and `FILTER = 'PASS'` when reliability is required)
- Multiple rows per patient per gene are possible (multiple mutation events); use `DISTINCT ParticipantBarcode` when counting mutated patients

---

### Table: `RNASeq_Expression` (DuckDB via `query_duckdb_pancancer_molecular`)

Full description: Contains normalized RNA-seq expression values for patients in the PanCancer Atlas, one row per patient per gene per sample.

| Field | Type | Meaning |
|---|---|---|
| `ParticipantBarcode` | VARCHAR | Patient identifier — **join key** to `clinical_info.Patient_description` |
| `SampleBarcode` | VARCHAR | Sample identifier |
| `AliquotBarcode` | VARCHAR | Aliquot identifier |
| `SampleTypeLetterCode` | VARCHAR | Sample type abbreviation |
| `SampleType` | VARCHAR | Sample type description (e.g., `Primary Tumor`) |
| `Symbol` | VARCHAR | Gene symbol — **filter on this for gene-specific queries** |
| `Entrez` | BIGINT | Entrez gene ID |
| `normalized_count` | DOUBLE | Normalized RNA expression value — **must be > 0 or handle with +1 before log10 transform** |

**Important value formats for `RNASeq_Expression`:**
- `Symbol` is case-sensitive: use exact gene symbols (e.g., `'IGF2'`)
- `normalized_count` can be 0 or NULL; "valid IGF2 expression values" means `normalized_count IS NOT NULL`
- Log10 transform: `LOG10(normalized_count + 1)` — the `+1` pseudocount is mandatory per the official hint
- Multiple rows per patient per gene are possible (multiple samples/aliquots); average across all valid rows per patient before grouping, or average directly across all rows per histology group

---

## 4. Join Keys

### Primary Join: `clinical_info.Patient_description` ↔ `Mutation_Data.ParticipantBarcode` / `RNASeq_Expression.ParticipantBarcode`

- `clinical_info.Patient_description` (PostgreSQL) contains the full TCGA barcode (e.g., `TCGA-AX-A3G8`).
- `Mutation_Data.ParticipantBarcode` and `RNASeq_Expression.ParticipantBarcode` (DuckDB) contain the same full TCGA barcode format.
- **Join condition:** `clinical_info.Patient_description = Mutation_Data.ParticipantBarcode` (direct string match — same format in both databases).
- **Workflow:** Query PostgreSQL to get `Patient_description` values matching clinical criteria → use those values as an `IN` list to filter DuckDB molecular tables, or vice versa.

### Secondary Join: `Mutation_Data` ↔ `RNASeq_Expression`
- Both tables share `ParticipantBarcode` — direct string match.

---

## 5. Critical Domain Knowledge

### Cancer Type Acronyms
- `LGG` = Brain Lower Grade Glioma
- `BRCA` = Breast Invasive Carcinoma
- `OV` = Ovarian Serous Cystadenocarcinoma
- `LUAD` = Lung Adenocarcinoma
- `LUSC` = Lung Squamous Cell Carcinoma
- `GBM` = Glioblastoma Multiforme
- `UCEC` = Uterine Corpus Endometrial Carcinoma
- `KIRC` = Kidney Renal Clear Cell Carcinoma
- **Note:** The exact cancer type field name in `clinical_info` must be discovered by querying the schema. Likely candidates: `acronym`, `type`, `Study`, or `cancer_type`.

### Verbatim Official Hints
> The gene expression data in RNASeq_Expression is stored as normalized counts. To compute log-transformed expression values, use the formula: log10(normalized_count + 1). The +1 offset (pseudocount) ensures that zero-expression values remain valid.

> In clinical_info, entries where the histological_type or icd_o_3_histology field is enclosed in square brackets (e.g., [Not Available], [Unknown], [Discrepancy]) represent missing or invalid annotations and should be excluded from histological-type analysis.

> The FILTER field in Mutation_Data is used for quality control. Only mutations with FILTER = 'PASS' are considered reliable.

### Key Formulas
- **Log10 gene expression:** `LOG10(normalized_count + 1)` — mandatory pseudocount +1
- **Average expression by histology group:** `AVG(LOG10(normalized_count + 1))` grouped by `icd_o_3_histology`
- **Survival days to years:** `CAST(days_to_death AS FLOAT) / 365.25`

### Common Pitfalls
- `days_to_death` and `days_to_last_followup` are TEXT — always `CAST(... AS FLOAT)` before arithmetic.
- `[Not Available]`, `[Unknown]` are strings, not NULL — filter with `icd_o_3_histology NOT LIKE '[%]'`.
- Multiple rows per patient in molecular tables — use `DISTINCT ParticipantBarcode` when counting patients.
- Cancer type acronym column name must be verified from schema before use.
