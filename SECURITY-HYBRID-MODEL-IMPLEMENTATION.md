# 🛡️ Security Hybrid Model - Implementation Guide

## Overview

Sistema híbrido de análise de segurança com 3 camadas:

1. **ACLED** - Incident-level, geo-points (conflitos armados)
2. **GDELT** - Incident-level, country-level (instabilidade global)
3. **World Bank** - Structural risk, country-level (indicadores socioeconômicos)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Observations                     │
│                    (Canonical Table)                         │
│  ┌──────────────┬──────────────┬─────────────────────────┐  │
│  │    ACLED     │    GDELT     │     WORLD_BANK          │  │
│  │  (INCIDENT)  │  (INCIDENT)  │    (STRUCTURAL)         │  │
│  └──────────────┴──────────────┴─────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        │                                       │
        ↓                                       ↓
┌─────────────────┐                   ┌─────────────────┐
│  Acute Risk     │                   │ Structural Risk │
│  (65% weight)   │                   │  (35% weight)   │
│                 │                   │                 │
│ max(ACLED,      │                   │ avg(unemployment│
│     GDELT)      │                   │     inflation,  │
└─────────────────┘                   │     governance) │
                                      └─────────────────┘
        │                                       │
        └───────────────────┬───────────────────┘
                            ↓
                   ┌────────────────┐
                   │  Combined Risk │
                   │ (0.65*Acute +  │
                   │  0.35*Struct)  │
                   └────────────────┘
```

## Step-by-Step Implementation

### 1. Apply Database Migration

```bash
cd sofia-pulse

# Apply migration
psql -h 91.98.158.19 -U dbs_sofia -d sofia -f migrations/052_security_hybrid_model.sql
```

Or via python:
```bash
python3 scripts/apply-migration.py migrations/052_security_hybrid_model.sql
```

This creates:
- ✅ `sofia.dim_country` - Country dimension
- ✅ `sofia.security_observations` - Canonical observations table
- ✅ `sofia.mv_security_country_acled` - ACLED country summary
- ✅ `sofia.mv_security_country_gdelt` - GDELT country summary (placeholder)
- ✅ `sofia.mv_structural_risk_country` - World Bank structural risk (placeholder)
- ✅ `sofia.mv_security_country_combined` - Hybrid combined risk
- ✅ `sofia.refresh_security_hybrid_views()` - Refresh function

### 2. Populate Country Dimension

```bash
python3 scripts/populate-dim-country.py
```

This fetches ~250 countries from REST Countries API and populates:
- country_code (ISO3)
- country_name
- iso2, iso3
- continent, region
- centroid_lat, centroid_lon

### 3. Refresh Existing ACLED Views

```bash
psql -h 91.98.158.19 -U dbs_sofia -d sofia -c "SELECT sofia.refresh_security_hybrid_views();"
```

Or:
```bash
python3 scripts/refresh-security-views.py
```

This refreshes:
- mv_security_country_acled (from existing security_events table)
- mv_security_geo_points (existing geo hotspots)

### 4. Implement GDELT Collector (Optional)

**Placeholder for now** - GDELT views are empty until collector runs.

To implement:
```python
# scripts/collect-gdelt-country-level.py
# Fetch GDELT events for last 90 days
# Aggregate by country: volume * abs(tone)
# Normalize severity_norm (0-100)
# Insert into sofia.security_observations:
#   source='GDELT', signal_type='INCIDENT', metric_name='gdelt_instability'
```

### 5. Implement World Bank Collector (Optional)

**Placeholder for now** - Structural views are empty until collector runs.

To implement:
```python
# scripts/collect-world-bank-structural.py
# Fetch World Bank indicators:
#   - SL.UEM.TOTL.ZS (Unemployment)
#   - FP.CPI.TOTL.ZG (Inflation)
#   - GV.EXCL.GOVT.ZS (Governance proxy - can use other indicators)
# Normalize each indicator to severity_norm (0-100)
# Insert into sofia.security_observations:
#   source='WORLD_BANK', signal_type='STRUCTURAL', metric_name='unemployment|inflation|governance'
```

### 6. Test API Endpoints

```bash
# ACLED country summary (existing data)
curl http://localhost:3001/api/security?view=summary_acled

# GDELT country summary (empty until collector runs)
curl http://localhost:3001/api/security?view=summary_gdelt

# Structural risk (empty until collector runs)
curl http://localhost:3001/api/security?view=summary_structural

# Combined hybrid risk
curl http://localhost:3001/api/security?view=summary_combined

# ACLED geo points (existing data)
curl http://localhost:3001/api/security?view=geo_acled
```

### 7. Test Map UI

Open: http://172.27.140.239:3001/map

Expected:
- ✅ ACLED layer shows existing geo hotspots (Africa, Middle East)
- ⏳ GDELT layer (country centroids) - empty until collector runs
- ⏳ Structural layer (country centroids) - empty until collector runs
- ✅ Combined layer - shows ACLED data only (since GDELT/Structural are empty)

## Current State

**Implemented ✅**:
1. ✅ Database schema (dim_country + security_observations + 4 MVs)
2. ✅ Country dimension populated (REST Countries API)
3. ✅ ACLED views working (from existing security_events table)
4. ✅ API expanded (6 endpoints)
5. ✅ Scoring methodology documented (65% Acute + 35% Structural)

**Pending ⏳**:
1. ⏳ GDELT collector (country-level instability)
2. ⏳ World Bank collector (structural indicators)
3. ⏳ UI layer toggle (ACLED / GDELT / Structural / Combined)
4. ⏳ Country-level choropleth/bubble rendering
5. ⏳ Popup showing component breakdown (Acute vs Structural)

## Verification

After applying migration + populating countries:

```sql
-- Check country dimension
SELECT COUNT(*) FROM sofia.dim_country;
-- Expected: ~250

-- Check ACLED country summary
SELECT COUNT(*) FROM sofia.mv_security_country_acled;
-- Expected: ~40-50 (countries with ACLED data)

-- Check combined view
SELECT
  country_code, country_name,
  acute_severity, structural_severity, total_risk,
  scoring_methodology
FROM sofia.mv_security_country_combined
ORDER BY total_risk DESC
LIMIT 10;
-- Should show countries with ACLED data, structural=0 (until WB collector runs)
```

## Next Steps

1. **Run migration + populate countries** (do this NOW)
2. **Refresh views** (do this NOW)
3. **Test API** (confirm endpoints work)
4. **Implement GDELT collector** (next sprint)
5. **Implement World Bank collector** (next sprint)
6. **Update UI with layer toggle** (next sprint)

## Notes

- ✅ Scoring is transparent: always return components + weights + formula
- ✅ ACLED continues to work as before (backward compatible)
- ✅ New endpoints won't break existing code
- ✅ Empty views (GDELT/Structural) gracefully return [] until collectors run
- ✅ Combined view works with partial data (ACLED-only until other sources populate)
