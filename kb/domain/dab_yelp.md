# Yelp Dataset — Knowledge Base

## 1. Dataset Overview
This dataset contains Yelp platform data covering businesses, user check-ins, reviews, tips, and user profiles for analyzing business performance, user behavior, and customer sentiment.

---

## 2. Tables & Collections

### MongoDB: `business` collection (`query_mongo_yelp_business`)
Confirmed fields (from live inspection):
| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId string | MongoDB internal ID |
| `business_id` | VARCHAR | Format: `businessid_##` — join key |
| `name` | VARCHAR | Business name |
| `review_count` | INT | Total number of reviews |
| `is_open` | INT | 1 = open, 0 = closed |
| `attributes` | dict | e.g. WiFi, CreditCards accepted |
| `hours` | dict | Day → "HH:MM-HH:MM" |
| `description` | VARCHAR | Free text: `"Located at [addr] in [City], [ST], this..."` |

**No `stars`, `city`, or `state` fields exist.** Location is only in `description`.
Filter by city/state: `{"description": {"$regex": "in Indianapolis, IN", "$options": "i"}}`

### MongoDB: `checkin` collection (`query_mongo_yelp_checkin`)
Contains check-in event data per business. Schema details unavailable — query directly to inspect fields. Expected to link to businesses via a business identifier.

### DuckDB: `review` table
Individual user reviews of businesses.
| Field | Type | Notes |
|---|---|---|
| `review_id` | VARCHAR | Unique review identifier |
| `user_id` | VARCHAR | Links to `user.user_id` |
| `business_ref` | VARCHAR | Links to MongoDB business `_id` — format: `businessref_##` |
| `rating` | BIGINT | 1–5 integer star rating |
| `useful/funny/cool` | BIGINT | Community reaction vote counts |
| `date` | VARCHAR | Inconsistent formats (e.g., `"August 01, 2016 at 03:44 AM"`, `"29 May 2013, 23:01"`) — parse carefully |

### DuckDB: `tip` table
Short user tips about businesses (shorter than reviews, no rating).
| Field | Type | Notes |
|---|---|---|
| `user_id` | VARCHAR | Links to `user.user_id` |
| `business_ref` | VARCHAR | Links to MongoDB business identifier |
| `compliment_count` | BIGINT | Number of compliments the tip received |
| `date` | VARCHAR | Same inconsistent format as `review.date` |

### DuckDB: `user` table
Yelp user profiles.
| Field | Type | Notes |
|---|---|---|
| `user_id` | VARCHAR | Primary key, links to `review` and `tip` |
| `yelping_since` | VARCHAR | Date user joined Yelp |
| `elite` | VARCHAR | Comma-separated years user held Elite status; empty string if never Elite |
| `useful/funny/cool` | BIGINT | Cumulative reaction votes received across all reviews |

---

## 3. Join Keys
- `review.user_id` → `user.user_id` (same format, direct join)
- `tip.user_id` → `user.user_id` (same format, direct join)
- `review.business_ref` → MongoDB `business.business_id` — format mismatch: DuckDB uses `businessref_##`, MongoDB uses `businessid_##`. Replace prefix `businessid_` → `businessref_` before building IN clause.
- `tip.business_ref` → MongoDB `business.business_id` (same prefix replacement rule as review)

---

## 4. Domain Terms
- **Elite**: Yelp's designation for high-quality reviewers; stored as years (e.g., `"2018,2019,2020"`)
- **Tip**: A brief suggestion, distinct from a full review; has no star rating
- **business_ref**: DuckDB-side foreign key referencing a MongoDB business document

---

## 5. Categories and Business Type
MongoDB `business` has **NO `categories` field**. Business type/category is embedded in the `description` as free text:
`"providing a range of services in Restaurants, Fast Food, Burgers, and American (Traditional)."`

To filter by category: `{"description": {"$regex": "Restaurants", "$options": "i"}}`

Common category patterns in description: `"services in [Cat1], [Cat2], and [Cat3]."` — always at the end of the description.

---

## 6. Attributes / Amenities
`attributes` is a flat Python dict with **string** values (not actual booleans or nested dicts):
```json
{
  "BusinessAcceptsCreditCards": "True",
  "WiFi": "u'no'",
  "BusinessParking": "{'garage': False, 'street': True, 'lot': True, 'valet': False, 'validated': False}",
  "BusinessAcceptsBitcoin": "False"
}
```

**Parking queries:** Use regex on the stringified BusinessParking value:
- Any parking at all: `{"attributes.BusinessParking": {"$regex": "True"}}`
- Street parking specifically: `{"attributes.BusinessParking": {"$regex": "'street': True"}}`

Note: attributes values are stored as Python repr strings, not proper JSON. Use `$regex` for all attribute filtering.

---

## 7. Known Query Patterns
- Top-rated businesses by average `rating`
- Most active users by `review_count` or tip volume
- Sentiment trends over time using `rating` and `date`
- Elite vs. non-Elite user review behavior comparison
- Businesses with highest `compliment_count` on tips
- Check-in frequency correlated with review ratings (cross-DB)