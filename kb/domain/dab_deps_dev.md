# Knowledge Base: deps_dev Dataset

---

## 1. Dataset Overview

The deps_dev dataset contains software package metadata (licensing, versions, dependencies) from a SQLite package database and GitHub project information (stars, forks, licenses) from a DuckDB project database, linkable via System/Name/Version keys.

---

## 2. CRITICAL — MCP Tool Mapping

| Tool Name | DB Type | Contains |
|---|---|---|
| `query_sqlite_deps_dev_package` | SQLite | `packageinfo` table — package metadata, versions, licenses, release info |
| `query_duckdb_deps_dev_project` | DuckDB | `project_packageversion` table — package-to-project mappings; `project_info` table — GitHub project details (stars, forks, licenses) |

---

## 3. Tables and Collections

### Table: `packageinfo` (SQLite via `query_sqlite_deps_dev_package`)

Full description: Contains metadata of software packages, including licensing information, version release data, dependency details, and registry metadata.

| Field | Type | Meaning |
|---|---|---|
| System | TEXT | Package ecosystem (e.g., `NPM`, `Maven`) |
| Name | TEXT | Package name |
| Version | TEXT | Version string of the package |
| Licenses | TEXT | JSON-like array of license identifiers |
| Links | TEXT | JSON-like list of relevant links (origin, docs, source) |
| Advisories | TEXT | JSON-like list of security advisories |
| VersionInfo | TEXT | JSON-like object with release metadata — contains `IsRelease` (bool) and `Ordinal` (numeric ordering) |
| Hashes | TEXT | JSON-like list of file hashes |
| DependenciesProcessed | INTEGER | Whether dependencies have been processed (0/1) |
| DependencyError | INTEGER | Whether a dependency processing error occurred (0/1) |
| UpstreamPublishedAt | REAL | Unix timestamp in **milliseconds** for upstream release publication |
| Registries | TEXT | JSON-like list of registries where the package is published |
| SLSAProvenance | REAL | SLSA provenance level if available |
| UpstreamIdentifiers | TEXT | JSON-like list of upstream identifiers |
| Purl | REAL | Package URL in purl format (if available) |

**Important value formats:**
- `VersionInfo` is a JSON string. To check if a version is a release: parse `IsRelease` field (boolean). To find the latest release, use the `Ordinal` field (higher = more recent).
- `System` values are uppercase strings: `NPM`, `Maven`, `PyPI`, etc.
- `UpstreamPublishedAt` is in **milliseconds** (not seconds).

---

### Table: `project_packageversion` (DuckDB via `query_duckdb_deps_dev_project`)

Full description: Contains mappings between package versions and their associated GitHub projects.

| Field | Type | Meaning |
|---|---|---|
| System | VARCHAR | Package ecosystem (e.g., `NPM`) |
| Name | VARCHAR | Package name |
| Version | VARCHAR | Package version string |
| ProjectType | VARCHAR | Type of project (e.g., `GITHUB`) |
| ProjectName | VARCHAR | Repository path in `owner/repo` format |
| RelationProvenance | VARCHAR | Provenance of the relationship data |
| RelationType | VARCHAR | Type of relationship (e.g., source repository type) |

**Important value formats:**
- `ProjectName` is in `owner/repo` format (e.g., `facebook/react`). This is the join key to `project_info`.

---

### Table: `project_info` (DuckDB via `query_duckdb_deps_dev_project`)

Full description: Contains GitHub project information including stars, forks, licenses, and descriptions.

| Field | Type | Meaning |
|---|---|---|
| Project_Information | VARCHAR | Textual description containing project name, **GitHub stars count**, **fork count**, and other metrics — must be parsed to extract numeric values |
| Licenses | VARCHAR | JSON-like array of license identifiers associated with the project |
| Description | VARCHAR | Project description field (may differ from Project_Information) |
| Homepage | VARCHAR | Homepage URL of the project |
| OSSFuzz | DOUBLE | OSSFuzz status indicator |

**Important value formats:**
- `Project_Information` is a **free-text string** that embeds GitHub stars and fork counts. You must extract these numerically from the text (e.g., using string parsing or regex-like SQL functions).
- The project name embedded in `Project_Information` corresponds to the `ProjectName` (`owner/repo`) from `project_packageversion` — use this to join.
- `Licenses` in `project_info` is the **project-level** license (used for query2), distinct from `Licenses` in `packageinfo` (package-level).

---

## 4. Join Keys

### Cross-database join path:

**Step 1:** Join `packageinfo` (SQLite) → `project_packageversion` (DuckDB)
- Join on: `System` = `System`, `Name` = `Name`, `Version` = `Version`
- Both sides store these as strings; values should match directly (e.g., `NPM` = `NPM`).

**Step 2:** Join `project_packageversion` (DuckDB) → `project_info` (DuckDB)
- Join on: `project_packageversion.ProjectName` matched against the project name embedded in `project_info.Project_Information`
- `ProjectName` is in `owner/repo` format; `Project_Information` contains this identifier as part of its text.

**Verbatim from official hints:**
> To solve this query, you will need to combine information from both the package and project databases. First, match package records in "packageinfo" from "package_database" with records in "project_packageversion" from "project_database" using the shared attributes "System", "Name", and "Version". Then, take the "ProjectName" from "project_packageversion" and use it to find the corresponding record in "project_info".

---

## 5. Critical Domain Knowledge

**Verbatim from official hints:**
> To solve this query, you will need to combine information from both the package and project databases. First, match package records in "packageinfo" from "package_database" with records in "project_packageversion" from "project_database" using the shared attributes "System", "Name", and "Version". Then, take the "ProjectName" from "project_packageversion" and use it to find the corresponding record in "project_info".

> The "Project_Information" field in "project_info" contains the project name as well as important repository metrics such as GitHub stars count and fork count, along with other descriptive details.

**Additional critical knowledge:**

1. **Identifying "latest release version" (query1):**
   - Filter `packageinfo` where `System = 'NPM'`.
   - A version is a **release** if `VersionInfo` JSON contains `"IsRelease": true`.
   - The **latest** release per package is determined by the **highest `Ordinal`** value in the `VersionInfo` JSON field. Do NOT rely on lexicographic version string sorting.
   - For each distinct `Name`, select the row with `IsRelease = true` AND the maximum `Ordinal`.

2. **Extracting GitHub stars and forks from `Project_Information`:**
   - `Project_Information` is a plain text/structured string. Stars and forks are embedded as numeric values within this text.
   - Use SQL string functions (e.g., `LIKE`, `INSTR`, `SUBSTR`, or regex in DuckDB) to extract the integer values for stars and forks.
   - DuckDB supports `regexp_extract()` which can be used to pull numeric values from `Project_Information`.

3. **"Marked as release" (query2):**
   - Means `VersionInfo` contains `"IsRelease": true` in `packageinfo`.

4. **Project license vs. package license:**
   - Query2 filters on **project** license `'MIT'` — this comes from `project_info.Licenses`, NOT `packageinfo.Licenses`.

5. **Scope of queries:**
   - Both queries are restricted to `System = 'NPM'` packages only.

6. **`Version