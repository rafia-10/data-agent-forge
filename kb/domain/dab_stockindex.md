# Knowledge Base: stockindex Dataset for DataAgentBench

---

## 1. Dataset Overview

The stockindex dataset combines metadata about global stock exchanges (SQLite) with daily price/trade data for their corresponding index symbols (DuckDB), enabling cross-database analysis of index performance, volatility, and returns across regions and currencies.

---

## 2. CRITICAL — MCP Tool Mapping

| Tool Name | DB Type | Contains |
|---|---|---|
| `query_sqlite_stockindex_info` | SQLite | `index_info` table — exchange names and trading currencies |
| `query_duckdb_stockindex_trade` | DuckDB | `index_trade` table — daily OHLC price data, adjusted close, and USD-converted close for index symbols |

---

## 3. Tables and Collections

### Table: `index_info` (via `query_sqlite_stockindex_info`)

Metadata about stock market indices from major exchanges worldwide (US, China, Canada, Germany, Japan, and more).

| Field | Type | Meaning |
|---|---|---|
| `Exchange` | TEXT | Full name of the stock exchange (e.g., `"Tokyo Stock Exchange"`, `"New York Stock Exchange"`) |
| `Currency` | TEXT | Trading currency of the exchange (e.g., `"JPY"`, `"USD"`, `"CNY"`) |

**Value formats:**
- `Exchange` contains full English names, not abbreviations or ticker symbols.
- `Currency` contains ISO 4217 currency codes.

---

### Table: `index_trade` (via `query_duckdb_stockindex_trade`)

Daily price data for indices tracking stock exchanges across various countries and regions.

| Field | Type | Meaning |
|---|---|---|
| `Index` | VARCHAR | Abbreviated index symbol (e.g., `"N225"`, `"HSI"`, `"000001.SS"`) |
| `Date` | VARCHAR | Trading date — stored as a string (format: `YYYY-MM-DD`) |
| `Open` | DOUBLE | Opening price in local currency |
| `High` | DOUBLE | Highest price during the trading day in local currency |
| `Low` | DOUBLE | Lowest price during the trading day in local currency |
| `Close` | DOUBLE | Closing price in local currency |
| `Adj Close` | DOUBLE | Adjusted closing price (accounts for splits, dividends) in local currency |
| `CloseUSD` | DOUBLE | Closing price converted to USD |

**Value formats:**
- `Date` is VARCHAR, not a native date type — use string comparison or CAST for filtering (e.g., `Date >= '2020-01-01'`).
- `Index` uses abbreviated symbols, not full exchange names — must be manually mapped to exchanges.

---

## 4. Join Keys

There is **no direct foreign key** between `index_info` and `index_trade`. The join must be performed manually using domain knowledge to map full exchange names (`Exchange`) to abbreviated index symbols (`Index`).

**Verbatim from official hints:**
> The Exchange field in indexinfo_database contains full exchange names (e.g., "Tokyo Stock Exchange", "New York Stock Exchange"). The Index field in indextrade_database contains abbreviated index symbols (e.g., "N225", "HSI", "000001.SS"). To join these datasets, you need to match exchange names with their corresponding major index symbols. For example, "Tokyo Stock Exchange" corresponds to "N225" (Nikkei 225), "Hong Kong Stock Exchange" corresponds to "HSI" (Hang Seng Index).

**Known exchange-to-symbol mappings (critical for queries):**

| Exchange (index_info) | Index Symbol (index_trade) | Country | Region |
|---|---|---|---|
| Tokyo Stock Exchange | N225 | Japan | Asia |
| Hong Kong Stock Exchange | HSI | Hong Kong | Asia |
| Shanghai Stock Exchange | 000001.SS | China | Asia |
| New York Stock Exchange / NYSE | (varies — check actual symbols) | USA | North America |
| NASDAQ | (varies — check actual symbols) | USA | North America |
| Toronto Stock Exchange | (varies) | Canada | North America |
| Frankfurt Stock Exchange | (varies) | Germany | Europe |

> **Action:** Always query `index_info` first to retrieve all exchange names and currencies, then query `index_trade` to retrieve all distinct `Index` symbols, and manually map them using domain knowledge before filtering by region.

---

## 5. Critical Domain Knowledge

### Verbatim Official Hints

> **Hint 1:** The Exchange field in indexinfo_database contains full exchange names (e.g., "Tokyo Stock Exchange", "New York Stock Exchange"). The Index field in indextrade_database contains abbreviated index symbols (e.g., "N225", "HSI", "000001.SS"). To join these datasets, you need to match exchange names with their corresponding major index symbols. For example, "Tokyo Stock Exchange" corresponds to "N225" (Nikkei 225), "Hong Kong Stock Exchange" corresponds to "HSI" (Hang Seng Index).

> **Hint 2:** The region (e.g., Asia, Europe, North America) of each stock exchange is not explicitly provided. You must infer the region using geographic knowledge. For instance, "N225" belongs to the Asia region because it tracks the Tokyo Stock Exchange in Japan.

> **Hint 3:** "Up days" refer to trading days where the closing price is higher than the opening price. "Down days" refer to trading days where the closing price is lower than the opening price.

> **Hint 4:** The term "average intraday volatility" refers to the average relative fluctuation of a stock index within each trading day. It is typically computed as (High - Low) / Open for each day, then averaged across a given time period.

---

### Additional Domain Knowledge for Specific Queries

**Average Intraday Volatility Formula:**
```
avg_volatility = AVG((High - Low) / Open)
```
Applied per `Index`, filtered to `Date >= '2020-01-01'`, grouped by `Index`. The result is a dimensionless ratio (higher = more volatile).

**Up Days vs. Down Days:**
- Up day: `Close > Open`
- Down day: `Close < Open`
- Filter by year: `Date >= '2018-01-01' AND Date <= '2018-12-31'`
- Count up days: `SUM(CASE WHEN Close > Open THEN 1 ELSE 0 END)`
- Count down days: `SUM(CASE WHEN Close < Open THEN 1 ELSE 0 END)`
- Condition: up_days > down_days

**Monthly Investment / Overall Return (query3):**
- "Regular monthly investments since 2000" implies a dollar-cost averaging (DCA) strategy.
- Use `CloseUSD` for cross-index comparison in a common currency (USD).
- For each month, assume one unit purchased at the first available trading day's `CloseUSD` (or average monthly `CloseUSD`).
- Overall return = total current value of all units purchased / total amount invested — or approximate as the ratio of the latest `CloseUSD` to the average `CloseUSD` across all months since 2000.
- Filter: `Date >= '2000-01-01'`.
- Group by `Index`, then compute return metric, rank descending, take top 5.
- Report the country each index belongs to using the exchange-to-symbol mapping.

**Date Filtering in DuckDB (Date is VARCHAR):**
- Use string comparison directly: `WHERE Date >= '2020-01-01'` — works correctly because the format is `YYYY-MM-DD` (lexicographically sortable).
- For year filtering: `WHERE Date LIKE '2018%'` or `WHERE Date >= '2018-01-01' AND Date <= '2018-12-31'`.

**Region Classification (must be inferred — not in data):**
- **Asia:** N225 (Japan), HSI (Hong Kong), 000001.SS (Shanghai/China), any other Asian exchange symbols
- **North America:** Symbols tied to US exchanges (NYSE, NASDAQ, S&P 500 → `^GSPC`, Dow Jones → `^DJI`, NASDAQ Composite → `^IXIC`) and Canadian exchanges (TSX → `^GSPTSE`)
- **Europe:** Symbols tied to German (DAX → `^GDAXI`), French (CAC 40 → `^FCHI`), UK (FTSE 100 → `^FTSE`), and other European exchange symbols
- **Unknown:** If an index symbol is not in the list above, query `index_info` by exchange name and infer region from country geography.