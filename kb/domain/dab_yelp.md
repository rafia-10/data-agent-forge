# Yelp Dataset — Knowledge Base

## 1. Dataset Overview
This dataset contains Yelp platform data covering businesses, user check-ins, reviews, tips, and user profiles for analyzing business performance, user behavior, and customer sentiment.

---

## 2. CRITICAL — MCP Tool Mapping for Yelp

Only 3 MCP tools exist for yelp. Never invent other tool names:

| Tool | DB | Contains |
|---|---|---|
| `query_mongo_yelp_business` | MongoDB `yelp_db` | `business` collection |
| `query_mongo_yelp_checkin` | MongoDB `yelp_db` | `checkin` collection |
| `query_duckdb_yelp_user` | DuckDB `yelp_user.db` | `review`, `tip`, `user` tables |

**ALL review, tip, AND user queries go through `query_duckdb_yelp_user`.**
Never use `query_duckdb_yelp_review` — it does not exist.

---

## 3. Tables & Collections

### MongoDB: `business` collection (`query_mongo_yelp_business`)
| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId string | MongoDB internal ID |
| `business_id` | VARCHAR | Format: `businessid_##` — join key |
| `name` | VARCHAR | Business name |
| `review_count` | INT | Total number of reviews |
| `is_open` | INT | 1 = open, 0 = closed |
| `attributes` | dict | e.g. WiFi, CreditCards, Parking |
| `hours` | dict | Day → "HH:MM-HH:MM" |
| `description` | VARCHAR | Free text: `"Located at [addr] in [City], [ST], this..."` |

**No `stars`, `city`, or `state` fields exist.** Location is ONLY in `description`.

### MongoDB: `checkin` collection (`query_mongo_yelp_checkin`)
Check-in event data per business. Links to businesses via business identifier.

### DuckDB: `review` table (inside `query_duckdb_yelp_user`)
| Field | Type | Notes |
|---|---|---|
| `review_id` | VARCHAR | Unique review identifier |
| `user_id` | VARCHAR | Links to `user.user_id` |
| `business_ref` | VARCHAR | Format: `businessref_##` — links to MongoDB `business_id` |
| `rating` | BIGINT | 1–5 integer star rating |
| `useful/funny/cool` | BIGINT | Community reaction votes |
| `date` | VARCHAR | Inconsistent formats — use `LIKE '%2018%'` for year filtering |

### DuckDB: `tip` table (inside `query_duckdb_yelp_user`)
| Field | Type | Notes |
|---|---|---|
| `user_id` | VARCHAR | Links to `user.user_id` |
| `business_ref` | VARCHAR | Links to MongoDB business identifier |
| `compliment_count` | BIGINT | Number of compliments |
| `date` | VARCHAR | Same inconsistent format as `review.date` |

### DuckDB: `user` table (inside `query_duckdb_yelp_user`)
| Field | Type | Notes |
|---|---|---|
| `user_id` | VARCHAR | Primary key |
| `yelping_since` | VARCHAR | Date user joined Yelp |
| `elite` | VARCHAR | Comma-separated years e.g. `"2018,2019,2020"` |
| `useful/funny/cool` | BIGINT | Cumulative reaction votes |

---

## 4. Join Keys
- `review.business_ref` ↔ `business.business_id` — PREFIX MISMATCH: `businessref_##` ↔ `businessid_##`
- `review.user_id` ↔ `user.user_id` — same format, direct join
- `tip.user_id` ↔ `user.user_id` — same format, direct join
- `tip.business_ref` ↔ `business.business_id` — same prefix rule as review

---

## 5. Categories and Business Type
MongoDB `business` has **NO `categories` field**. Category is in `description` free text:
`"providing a range of services in Restaurants, Fast Food, Burgers, and American (Traditional)."`

To filter by category: `{"description": {"$regex": "Restaurants", "$options": "i"}}`
Pattern: `"services in [Cat1], [Cat2], and [Cat3]."` — always at end of description.

---

## 6. Attributes / Amenities
`attributes` values are Python repr strings — always use `$regex` for filtering:

- Any parking: `{"attributes.BusinessParking": {"$regex": "True"}}`
- Bike parking: `{"attributes.BikeParking": {"$regex": "True"}}`
- WiFi: `{"attributes.WiFi": {"$regex": "free|paid", "$options": "i"}}`
- Credit cards: `{"attributes.BusinessAcceptsCreditCards": {"$regex": "True"}}`

---

## 7. Exact Query Patterns

### Pattern A — Filter by city/state
No `state` field — extract from `description`:
```
{"description": {"$regex": "in Indianapolis, IN", "$options": "i"}}
```

### Pattern B — Average rating of businesses in a city/state
- Step 1 MongoDB: get all `business_id` values matching city/state regex
- Step 2 DuckDB: compute flat AVG over ALL matching reviews
```sql
SELECT AVG(rating) as avg_rating
FROM review
WHERE business_ref IN ('businessref_1', 'businessref_2', ...)
```
**Use flat AVG — never average per-business averages.**

### Pattern C — State with highest review COUNT + avg rating
**NEVER add an IN clause to DuckDB for this pattern.**
- Step 1 MongoDB: get ALL businesses — no filtering
```
[{"$project": {"business_id": 1, "description": 1, "_id": 0}}]
```
- Step 2 DuckDB: get ALL reviews grouped — no WHERE clause, no IN clause
```sql
SELECT business_ref, COUNT(*) as review_count, SUM(rating) as rating_sum
FROM review
GROUP BY business_ref
```
- Synthesize: join on prefix swap businessid_## to businessref_##, group by state, sum review_count, find max state, compute avg_rating for that state.

### Pattern D — Intersection: businesses reviewed in year X AND have attribute Y
**ALWAYS do DuckDB first, then MongoDB with $in filter.**
- Step 1 DuckDB:
```sql
SELECT DISTINCT business_ref FROM review WHERE date LIKE '%2018%'
```
- Step 2 MongoDB — use ALL business_ids from Step 1 in $in, AND attribute filter, AND $count:
```
[
  {"$match": {
    "business_id": {"$in": ["businessid_1", "businessid_2", "...ALL IDs..."]},
    "$or": [
      {"attributes.BusinessParking": {"$regex": "True"}},
      {"attributes.BikeParking": {"$regex": "True"}}
    ]
  }},
  {"$count": "total"}
]
```
- Answer = `total` field from MongoDB $count
- NEVER count DuckDB rows for this pattern — the MongoDB $count IS the answer
- NEVER run MongoDB without the $in filter from Step 1

### Pattern E — Top business by rating in date range with min reviews
- Step 1 DuckDB: filter by date range, min review count, get top business_ref
```sql
SELECT business_ref, AVG(rating) as avg_r, COUNT(*) as cnt
FROM review
WHERE date LIKE '%2016%'
GROUP BY business_ref
HAVING COUNT(*) >= 5
ORDER BY avg_r DESC
LIMIT 1
```
- Step 2 MongoDB: get name and category for that business_id

### Pattern F — Top N categories by review count from specific user group
- Step 1 DuckDB: get user_ids matching criteria
```sql
SELECT user_id FROM user WHERE yelping_since LIKE '%2016%'
```
- Step 2 DuckDB: get business_refs reviewed by those users
```sql
SELECT business_ref, COUNT(*) as total_reviews
FROM review
WHERE user_id IN ('user_1', 'user_2', ...)
GROUP BY business_ref
ORDER BY total_reviews DESC
```
- Step 3 MongoDB: get descriptions for top business_ids to extract categories

---

## 8. Domain Terms
- **Elite**: High-quality reviewer designation; stored as years e.g. `"2018,2019,2020"`
- **Tip**: Brief suggestion, no star rating, distinct from review
- **business_ref**: DuckDB foreign key — always `businessref_##` format
- **business_id**: MongoDB primary key — always `businessid_##` format

---

## 9. Known Query Patterns
- Top-rated businesses by average `rating`
- Most active users by `review_count` or tip volume
- Sentiment trends over time using `rating` and `date`
- Elite vs. non-Elite user review behavior
- Businesses with highest `compliment_count` on tips
- Check-in frequency correlated with review ratings (cross-DB)