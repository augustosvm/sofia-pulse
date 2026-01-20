# Data Quality: Week Alignment Standardization

## Overview

Enterprise-grade week alignment system for temporal tables. Ensures all week-based date columns are Monday-aligned for deterministic time window filtering.

## Quick Start

### 1. Apply Migration 017d
```bash
python scripts/apply_enterprise_migrations.py
```

Or manually:
```bash
psql -f sql/migrations/017d_week_start_standardization.sql
```

### 2. Run Health Check
```bash
python scripts/data_quality_week_alignment.py
```

**Exit Codes:**
- `0` - PASS (all weeks aligned)
- `2` - FAIL (misaligned weeks detected)
- `1` - ERROR (connection/execution failure)

### 3. Query Health Check View
```sql
SELECT * FROM sofia.v_data_quality_week_alignment;
```

## Fixed Tables

| Table | Column | Fix Applied |
|-------|--------|-------------|
| `acled_aggregated` | `week_start` | Added in 017c, verified in 017d |
| `security_events` | `week_start` | Aligned in 017d |

## Health Check Details

**View:** `sofia.v_data_quality_week_alignment`

Returns per-table metrics:
- `total_rows` - Total rows in table
- `distinct_weeks` - Unique week values
- `rows_not_aligned` - Rows where week != Monday
- `distinct_weeks_not_aligned` - Unique misaligned weeks
- `pct_rows_not_aligned` - Percentage of misaligned rows
- `pct_distinct_not_aligned` - Percentage of misaligned weeks
- `status` - PASS/FAIL

## Legacy Columns

Some tables retain original `week` columns for backwards compatibility:
- `acled_aggregated.week` - Original column (may be misaligned)
- `acled_aggregated.week_start` - Aligned column (use this)

**Best Practice:** Always filter on `week_start` columns in queries and MVs.

## Integration

To add new temporal tables to monitoring, edit:
`sql/migrations/017d_week_start_standardization.sql`

Add UNION ALL clause to `v_data_quality_week_alignment`:
```sql
UNION ALL
SELECT 
    'your_table'::text,
    'week_start'::text,
    COUNT(*),
    COUNT(DISTINCT week_start),
    COUNT(*) FILTER (WHERE week_start <> date_trunc('week', week_start)),
    COUNT(DISTINCT week_start) FILTER (WHERE week_start <> date_trunc('week', week_start))
FROM sofia.your_table
WHERE week_start IS NOT NULL
```

## CI/CD Integration

Add to your pipeline:
```bash
python scripts/data_quality_week_alignment.py || exit 1
```

This will fail the build if any temporal tables have misaligned weeks.
