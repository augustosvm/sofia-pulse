# 📊 Guide: Updating Analytics Queries for Geographic Normalization

## What Changed

All collectors now use normalized geographic IDs:
- `country_id` → references `sofia.countries(id)`
- `state_id` → references `sofia.states(id)`
- `city_id` → references `sofia.cities(id)`

## How to Update Queries

### BEFORE (Old way - using codes/names):
```sql
SELECT country_code, country_name, COUNT(*) 
FROM sofia.jobs
WHERE country_code = 'USA'
GROUP BY country_code, country_name
```

### AFTER (New way - using JOINs):
```sql
SELECT c.iso_alpha2, c.common_name, COUNT(*) 
FROM sofia.jobs j
JOIN sofia.countries c ON j.country_id = c.id
WHERE c.iso_alpha2 = 'US'
GROUP BY c.iso_alpha2, c.common_name
```

## Benefits

✅ **Faster queries** - JOIN on INTEGER vs VARCHAR
✅ **Consistent data** - One source of truth for country names
✅ **Better aggregation** - No duplicates from typos
✅ **Easier filtering** - Filter by continent, region, etc.

## Files Updated

✅ analyze-db-for-dashboard.py
✅ All 10 collectors with geographic data

## Action Required

Update any custom queries/dashboards to:
1. JOIN with `sofia.countries` using `country_id`
2. Use `c.common_name` instead of `country_name`
3. Use `c.iso_alpha2` or `c.iso_alpha3` instead of `country_code`
