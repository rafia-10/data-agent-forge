# Knowledge Base: music_brainz Dataset (DataAgentBench)

---

## 1. Dataset Overview

The music_brainz dataset combines a SQLite tracks database (track metadata with potential duplicates) and a DuckDB sales database (per-transaction sales records) linked by `track_id`.

---

## 2. CRITICAL — MCP Tool Mapping

| Tool Name | DB Type | Contains |
|---|---|---|
| `query_sqlite_music_brainz` | SQLite | `tracks` table — track metadata (title, artist, album, year, length, language) |
| `query_duckdb_music_brainz_sales` | DuckDB | `sales` table — sales transactions (country, store, units_sold, revenue_usd) |

---

## 3. Tables and Collections

### Table: `tracks` (via `query_sqlite_music_brainz`)

Contains all track records, including duplicates generated from different sources. Each row is a single track record.

| Field | Type | Meaning |
|---|---|---|
| `track_id` | INTEGER (PK) | Unique identifier for this row in the tracks table |
| `source_id` | INTEGER | Identifier of the data source that contributed this record |
| `source_track_id` | TEXT | Original track ID from the source system; NOT globally unique |
| `title` | TEXT | Track title (may have minor variations across duplicate rows) |
| `artist` | TEXT | Artist or band name (may have minor spelling variations across duplicates) |
| `album` | TEXT | Album name (may vary slightly across duplicates) |
| `year` | TEXT | Year of publication — stored as TEXT; format may vary (e.g., "2006" vs "06") |
| `length` | TEXT | Track length — stored as TEXT; may be seconds or formatted string |
| `language` | TEXT | Language of the track |

**Important format notes:**
- `year` is TEXT and may appear in different formats across duplicate rows (e.g., full year vs. 2-digit year).
- `title` and `artist` may have minor spelling differences across duplicate rows representing the same real-world track.

---

### Table: `sales` (via `query_duckdb_music_brainz_sales`)

Contains individual sales transactions. Each row is one sale event for one `track_id`.

| Field | Type | Meaning |
|---|---|---|
| `sale_id` | INTEGER | Unique identifier for this sale record |
| `track_id` | INTEGER | Foreign key linking to `tracks.track_id` |
| `country` | VARCHAR | Country where the sale occurred |
| `store` | VARCHAR | Platform/store where the sale occurred |
| `units_sold` | INTEGER | Number of units sold in this transaction |
| `revenue_usd` | DOUBLE | Revenue in USD from this transaction |

**Known exact values:**
- `country` values: `USA`, `UK`, `Canada`, `Germany`, `France`
- `store` values: `iTunes`, `Spotify`, `Apple Music`, `Amazon Music`, `Google Play`

---

## 4. Join Keys

**Primary join:** `tracks.track_id` = `sales.track_id`

- Both fields are INTEGER type — no format mismatch on the join key itself.
- However, because `tracks` contains **duplicate rows** for the same real-world track, a single real-world track may have **multiple `track_id` values**, each of which may independently appear in `sales`. You must collect ALL matching `track_id`s after entity resolution and aggregate sales across all of them.

**Entity resolution requirement (verbatim from hints):**
> Different `track_id`s can represent the same real-world track. To answer queries correctly, you need to perform **entity resolution** by comparing track attributes such as `title`, `artist`, `album`, `year`, etc. Note that duplicates may not match exactly (e.g., different year formats or minor attribute variations), so you must reason about the meaning of these attributes rather than relying on exact string equality for entity resolution.

---

## 5. Critical Domain Knowledge

### Verbatim Hints (copy exactly as provided):

> - The `tracks` table may contain duplicate entries. Different `track_id`s can represent the same real-world track. To answer queries correctly, you need to perform **entity resolution** by comparing track attributes such as `title`, `artist`, `album`, `year`, `length`, etc. Note that duplicates may not match exactly (e.g., different year formats or minor attribute variations), so you must reason about the meaning of these attributes rather than relying on exact string equality for entity resolution.
> - The `sales` table records sales in five countries: USA, UK, Canada, Germany, and France.
> - Sales occur across five platforms or stores: iTunes, Spotify, Apple Music, Amazon Music, and Google Play.

### Additional Domain Knowledge for These Queries:

1. **Artist name misspellings in queries:** Query2 references "Brucqe Maginnis" — this is likely a misspelling of the actual artist name in the database. Search using fuzzy/partial matching (e.g., `LIKE '%Maginnis%'`) rather than exact match on the artist field.

2. **Revenue aggregation:** Total revenue for a track = `SUM(revenue_usd)` across all matching `sale_id` rows. Always SUM, never take a single row.

3. **Entity resolution workflow:** After finding candidate `track_id`s via title/artist search, inspect all results and group rows that represent the same real-world track. Then collect the full set of `track_id`s for that entity and use `IN (id1, id2, ...)` when querying sales.

4. **Store filter:** Use exact string match for store names (e.g., `store = 'Apple Music'`). Case matters — use the exact casing from the known values list above.

5. **Country filter:** Use exact string match (e.g., `country = 'Canada'`). Use the exact casing from the known values list above.

---

## 6. Query Patterns

### query1: *How much revenue in USD did Apple Music make from Beyoncé's song 'Get Me Bodied' in Canada?*

**Step 1 — `query_sqlite_music_brainz`:**
```sql
SELECT track_id, title, artist, album, year
FROM tracks
WHERE title LIKE '%Get Me Bodied%'
  AND artist LIKE '%Beyonc%'
```
- Inspect results; identify all `track_id`s that resolve to the same real-world track "Get Me Bodied" by Beyoncé.

**Step 2 — `query_duckdb_music_brainz_sales`:**
```sql
SELECT SUM(revenue_usd) AS total_revenue
FROM sales
WHERE track_id IN (<all resolved track_ids>)
  AND store = 'Apple Music'
  AND country = 'Canada'
```

**Expected answer format:** A single USD dollar amount (DOUBLE), e.g., `1234.56`.

---

### query2: *Which store earned the most revenue in USD from Brucqe Maginnis' song 'Street Hype' across all countries?*

**Step 1 — `query_sqlite_music_brainz`:**
```sql
SELECT track_id, title, artist, album, year
FROM tracks
WHERE title LIKE '%Street Hype%'
  AND artist LIKE '%Maginnis%'
```
- Note: "Brucqe Maginnis" is likely a misspelling; use `LIKE '%Maginnis%'` to find the actual artist name.
- Inspect results; identify all `track_id`s resolving to the same real-world track.

**Step 2 — `query_duckdb_music_brainz_sales`:**
```sql
SELECT store, SUM(revenue_usd) AS total_revenue
FROM sales
WHERE track_id IN (<all resolved track_ids>)
GROUP BY store
ORDER BY total_revenue DESC
LIMIT 1
```

**Expected answer format:** A single store name string from the known set: `iTunes`, `Spotify`, `Apple Music`, `Amazon Music`, or `Google Play`.

---

### query3: *Which song generated the highest total revenue in USD across all stores and countries?*

**Step 1 — `query_duckdb_music_brainz_sales`:**
```sql
SELECT track_id, SUM(revenue_usd) AS total_revenue
FROM sales
GROUP BY track_id
ORDER BY total_revenue DESC
LIMIT 20
```
Retrieve the top `track_id` values by revenue (top 20 to allow for entity resolution across duplicates).

**Step 2 — `query_sqlite_music_brainz`:**
```sql
SELECT track_id, title, artist, album, year
FROM tracks
WHERE track_id IN (<top track_ids from Step 1>)
```
- Perform entity resolution: group rows that represent the same real-world track (same title + artist, possibly different formats).
- Aggregate total revenue for all `track_id`s belonging to the same real-world track.

**Expected answer format:** A single song title string (the title of the track with highest aggregate revenue).
