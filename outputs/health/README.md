# Phase 3 Collectors - Health Monitoring

## Overview

This directory contains health check outputs for the 4 collectors recovered in Phase 3:

1. **world-sports** → `sofia.world_sports_data`
2. **hdx-humanitarian** → `sofia.hdx_humanitarian_data`
3. **sports-regional** → `sofia.sports_regional`
4. **women-brazil** → `sofia.women_brazil_data`

## Health Check

Run manually:
```bash
bash scripts/health/run-healthcheck.sh
```

**Output files** (timestamped):
- `collectors_health_YYYYMMDD_HHMMSS.txt` - Human-readable report
- `collectors_health_YYYYMMDD_HHMMSS.json` - Machine-readable (future)

**Exit codes**:
- `0` - All collectors healthy (data in last 24h)
- `1` - One or more collectors unhealthy (no data in last 24h)

## Metrics Tracked

For each collector:
- **records_24h** - Records inserted in last 24 hours
- **total_records** - Total records in table
- **latest_insert** - Timestamp of most recent insert
- **is_healthy** - Boolean: has data in last 24h?

## Data Available for Consumption

### 1. World Sports Data (`sofia.world_sports_data`)

**Sources**:
- WHO Global Health Observatory (Physical Activity)
- Eurostat (EU Sports Participation)
- World Bank (Socioeconomic indicators)

**Columns**:
```sql
- id, source, indicator_name, category
- country_code, country_id (FK)
- region, sex, age_group
- year, value, unit
- collected_at
```

**Use Cases**:
- Cross-signal: Physical activity % vs Tech adoption
- Cross-signal: Sports participation vs GDP per capita
- Insights: Countries with high inactivity = health tech opportunity

**Current Status** (as of 2026-02-04):
- Total records: 5,546
- WHO: 2,064 records
- World Bank: 3,379 records
- Eurostat: 3 records

---

### 2. HDX Humanitarian Data (`sofia.hdx_humanitarian_data`)

**Sources**:
- Humanitarian Data Exchange (CKAN API)
- Organizations: UNHCR, WFP, MSF, OCHA, UNICEF, ICRC, IOM

**Columns**:
```sql
- id, dataset_id, name, title
- organization, tags[]
- resources_count, country_code, country_id (FK)
- metadata (JSONB), collected_at
```

**Use Cases**:
- Cross-signal: Humanitarian crises vs Migration tech
- Cross-signal: Food insecurity vs AgTech funding
- Insights: Countries with refugee datasets = integration tech opportunity

**Current Status** (as of 2026-02-04):
- Total records: 61 datasets
- UNHCR: 30 datasets
- WFP: 30 datasets
- MSF: 1 dataset

---

### 3. Sports Regional (`sofia.sports_regional`)

**Sources**:
- FIFA, IOC, UEFA, FIBA, FIVB rankings
- Regional sports federations (17 sports)

**Columns**:
```sql
- id, sport, region, country_code, country_id (FK)
- ranking, num_athletes, performance_index
- collected_at
```

**Use Cases**:
- Cross-signal: Regional sports strength vs Fitness tech adoption
- Cross-signal: E-sports growth vs Gaming hardware sales
- Insights: Countries with high rankings = sponsorship tech opportunity

**Current Status** (as of 2026-02-04):
- Total records: 308
- Sports covered: 17 (Football, Cricket, Basketball, E-Sports, etc.)

---

### 4. Women Brazil Data (`sofia.women_brazil_data`)

**Sources**:
- IBGE SIDRA (Brazilian women's statistics)
- IPEA (Brazilian economic data)
- DataSUS / World Bank (Health indicators)

**Columns**:
```sql
- id, source, indicator_code, indicator_name
- category (labor, health, education, violence)
- region (TEXT), state_id (FK), country_id (FK)
- period (TEXT), sex (TEXT)
- value, unit (TEXT)
- collected_at
```

**Use Cases**:
- Cross-signal: Female labor participation vs Childcare tech
- Cross-signal: Violence data vs Safety tech funding
- Cross-signal: Education gap vs EdTech for women
- Insights: Regions with high gender gaps = opportunity for impact startups

**Current Status** (as of 2026-02-04):
- Total records: 860 (NEW)
- IBGE tables: 7 (unemployment, employment, education, health, violence, demographics)
- IPEA: No data (API limitation)
- World Bank: Maternal mortality (25 records)

**Note**: Schema was fixed (VARCHAR → TEXT) to handle long IBGE values.

---

## Integration with Analytics

### Current Status
These 4 collectors are **NOT YET** consumed by existing analytics pipelines.

### Recommended Next Steps

**Option 1: Add to Cross-Signals Builder**
```bash
# File: scripts/build-cross-signals.py
# Add new signal types:
# - "sports_tech_adoption"
# - "humanitarian_migration_tech"
# - "gender_impact_tech"
```

**Option 2: Create Dedicated Analytics**
```bash
# New analytics:
# - analytics/sports-tech-intelligence.py
# - analytics/humanitarian-tech-insights.py
# - analytics/gender-gap-opportunities.py
```

**Option 3: Add to MEGA Analysis**
```bash
# File: analytics/mega-analysis.py
# Include these tables in cross-database queries
```

### Available Cross-Signal Ideas

**From world-sports**:
- Physical inactivity % → Fitness tech funding
- Sports participation → Wearables market size

**From hdx-humanitarian**:
- Refugee datasets → Migration management tech
- Food insecurity → AgTech + FoodTech funding

**From sports-regional**:
- E-sports rankings → Gaming hardware sales
- Regional strength → Sports tech sponsorships

**From women-brazil**:
- Gender wage gap → HR tech for equality
- Violence data → Safety tech funding
- Education gap → EdTech for women

---

## Cron Schedule

**When collectors run** (UTC):
- **03:10 UTC** - women-brazil
- **03:20 UTC** - hdx-humanitarian
- **03:30 UTC** - sports-regional
- **03:40 UTC** - world-sports

**Healthcheck** (optional):
- After collectors finish: `04:00 UTC`

---

## Troubleshooting

**Collector fails**:
1. Check logs: `outputs/cron/<collector>.log`
2. Run manually: `bash scripts/run-python-collector.sh <name> scripts/collect-<name>.py`
3. Check schema: Ensure migrations are applied

**No data in last 24h**:
1. Check if cron is running: `crontab -l`
2. Check collector exit code in logs
3. Verify API availability (WHO, IBGE, HDX CKAN)

**Schema errors**:
1. Apply migration: `migrations/013_fix_women_brazil_varchar_limits.sql`
2. Re-run collector

---

**Last Updated**: 2026-02-04 22:30 UTC
**Status**: Phase 4 - Integrated into ecosystem
