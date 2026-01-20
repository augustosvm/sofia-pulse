# Women & NGO Intelligence - Demo & Audit

## Critical Fix Applied

**Migration 017c** addresses ACLED week alignment issue (197k+ rows with misaligned weeks).
- Adds `week_start` column (week-aligned date)
- Updates Women MV to use `week_start` for accurate filtering
- Fixes `events_30d=0` but `score>50` anomalies

## Quick Start

### Apply Migration 017c (if not already applied)
```bash
python scripts/apply_enterprise_migrations.py
```

or manually:
```bash
psql -f sql/migrations/017c_acled_week_alignment.sql
```

### Refresh Materialized Views
```bash
psql -c "REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_women_intelligence_by_country;"
psql -c "REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_ngo_coverage_by_country;"
```

### Run Full SQL Audit
```bash
psql -f sql/women_ngo_demo_audit.sql
```

### Run Quick Python Diagnostics
```bash
python scripts/women_ngo_audit.py
```

## Auditorias Included

1. **Score Components** - Breakdown of violence score by events vs fatalities
2. **Week Alignment** - Distinct weeks analysis (critical for data quality)
3. **NGO Raw vs Mapped** - Backfill coverage detection
4. **NGO Unmapped** - Pipeline failure detection
5. **NGO Examples** - Unmapped signal samples
6. **Country Mention Heuristic** - Proves pipeline failures vs missing data
7. **Keyword Frequency** - NGO keyword effectiveness

## Expected Output After 017c

```
AUDITORIA 2 (week alignment):
  distinct_weeks_not_aligned: 0 (FIXED)
  rows_not_aligned: 0 (FIXED)
```
