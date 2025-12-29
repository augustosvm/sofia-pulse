# 📊 Data Quality Report - Sofia Pulse

**Date**: 2025-12-29
**Status**: ✅ Quality Checks Complete

---

## 🎯 Executive Summary

| Metric | Status | Details |
|:---|:---:|:---|
| **Duplicate Organizations** | ✅ | 0 duplicates found |
| **Referential Integrity** | ✅ | All FKs valid, 369 orphaned city_id fixed |
| **Org Normalization** | ⚠️ | 61.4% coverage (16,395/26,691) |
| **Country Normalization** | ❌ | 30.4% coverage (155,929/512,622) |
| **State Normalization** | ❌ | 13.5% coverage (1,653/12,249) |
| **City Normalization** | ❌ | 44.2% coverage (4,711/10,653) |

---

## 🏢 Organization Normalization Coverage

### ✅ Excellent Coverage (≥95%)

| Table | Total | Normalized | Coverage |
|:---|---:|---:|---:|
| space_industry | 6,500 | 6,500 | **100.0%** |
| market_data_brazil | 352 | 352 | **100.0%** |
| market_data_nasdaq | 91 | 91 | **100.0%** |
| global_universities_progress | 370 | 370 | **100.0%** |
| world_ngos | 200 | 200 | **100.0%** |
| hdx_humanitarian_data | 196 | 196 | **100.0%** |
| startups | 80 | 80 | **100.0%** |
| nih_grants | 52 | 52 | **100.0%** |
| hkex_ipos | 100 | 97 | **97.0%** |

### ⚠️ Good Coverage (80-94%)

| Table | Total | Normalized | Coverage | Missing |
|:---|---:|---:|---:|---:|
| funding_rounds | 8,097 | 7,097 | **87.6%** | 1,000 |

**Issue**: 1,000 funding rounds without organization_id
**Cause**: Company names não normalizados ou não encontrados
**Action**: Backfill manual ou melhorar fuzzy matching

### ❌ Low Coverage (<80%)

| Table | Total | Normalized | Coverage | Missing |
|:---|---:|---:|---:|---:|
| jobs | 10,653 | 1,360 | **12.8%** | 9,090 |

**Issue**: 9,090 jobs (85%+) sem organization_id
**Cause**: Coletores antigos não usavam `getOrCreateOrganization()`
**Action**: Backfill com `jobs-inserter.ts` helper

---

## 🌍 Country Normalization Coverage

### ✅ Excellent Coverage (≥95%)

| Table | Total | Normalized | Coverage |
|:---|---:|---:|---:|
| global_universities_progress | 370 | 370 | **100.0%** |
| funding_rounds | 8,097 | 8,077 | **99.8%** |
| world_ngos | 200 | 198 | **99.0%** |

### ⚠️ Good Coverage (80-94%)

| Table | Total | Normalized | Coverage |
|:---|---:|---:|---:|
| space_industry | 6,500 | 6,110 | **94.0%** |
| cardboard_production | 900 | 756 | **84.0%** |
| comexstat_trade | 1,596 | 1,298 | **81.3%** |

### ❌ Low Coverage (<80%)

| Table | Total | Normalized | Coverage | Reason |
|:---|---:|---:|---:|:---|
| jobs | 10,653 | 7,820 | **73.4%** | 1,972 "Remote" jobs (legitimate NULL) |
| tech_jobs | 3,675 | 2,334 | **63.5%** | 1,321 "Remote" jobs (legitimate NULL) |
| persons | 230,732 | 128,449 | **55.7%** | Many without country in source |
| **authors** | **245,965** | **0** | **0.0%** | ❌ **NOT NORMALIZED YET** |
| **publications** | **350** | **0** | **0.0%** | ❌ **NOT NORMALIZED YET** |
| **gdelt_events** | **2,751** | **0** | **0.0%** | ❌ **NOT NORMALIZED YET** |

**Critical**: authors, publications, gdelt_events não têm country_id populado

---

## 🏛️ State Normalization Coverage

| Table | Total | Normalized | Coverage | Issue |
|:---|---:|---:|---:|:---|
| jobs | 10,653 | 1,651 | **15.5%** | Most jobs don't specify state |
| comexstat_trade | 1,596 | 2 | **0.1%** | ❌ **CRITICAL: Almost no states mapped** |

**Critical Issue**: comexstat_trade tem state_code mas não está sendo normalizado para state_id

---

## 🏙️ City Normalization Coverage

| Table | Total | Normalized | Coverage | Issue |
|:---|---:|---:|---:|:---|
| jobs | 10,653 | 4,711 | **44.2%** | 1,867 cities not in cities table |

**Issue**: 1,867 jobs têm city name mas city não existe na tabela cities

---

## ✅ Fixes Applied

### 1. Duplicate Cleanup
- **Result**: 0 duplicates found (already clean)
- **Migration**: `049_cleanup_duplicate_organizations.sql`

### 2. Orphaned Foreign Keys
- **Found**: 369 orphaned city_id in tech_jobs
- **Fixed**: Set to NULL (cities don't exist)
- **Migration**: `050_fix_orphaned_city_ids.sql`
- **Result**: ✅ All FKs valid

### 3. Unused Organizations
- **Found**: 1,165 organizations with no references
- **Status**: ⚠️ OK (created during backfills, available for future use)
- **Action**: None required

---

## 🚨 Critical Issues Identified

### 1. **authors table not normalized** (245,965 records)
- **Impact**: HIGH - Cannot link authors to countries
- **Cause**: Migration 048 has UPDATE but no backfill was run
- **Fix Required**: Run backfill for authors.country_id

### 2. **publications table not normalized** (350 records)
- **Impact**: MEDIUM - Small table but important for research
- **Cause**: Same as authors
- **Fix Required**: Run backfill for publications.country_id

### 3. **gdelt_events table not normalized** (2,751 records)
- **Impact**: MEDIUM - Geopolitical events without location
- **Cause**: Same as authors
- **Fix Required**: Run backfill for gdelt_events.country_id

### 4. **comexstat_trade states not normalized** (1,596 records)
- **Impact**: HIGH - Brazil trade data without state mapping
- **Cause**: state_code exists but not converted to state_id
- **Fix Required**: Create mapping BR state codes → state_id

### 5. **jobs organization_id very low** (12.8% coverage)
- **Impact**: HIGH - Cannot track hiring trends by company
- **Cause**: Old collectors didn't use getOrCreateOrganization()
- **Fix Required**: Backfill jobs.organization_id from company name

---

## 📋 Recommended Actions

### Priority 1 (Critical)
1. ✅ Backfill authors.country_id (245,965 records)
2. ✅ Backfill publications.country_id (350 records)
3. ✅ Backfill gdelt_events.country_id (2,751 records)
4. ✅ Fix comexstat_trade.state_id mapping

### Priority 2 (High)
5. ✅ Backfill jobs.organization_id (9,090 records)
6. ✅ Backfill funding_rounds.organization_id (1,000 records)

### Priority 3 (Medium)
7. ⚠️ Add missing cities to cities table (1,867 cities)
8. ⚠️ Improve state normalization for jobs table

---

## 📊 Scripts Created

- `scripts/validate-referential-integrity.py` - Check FK integrity
- `scripts/audit-normalization-coverage.py` - Coverage audit
- `scripts/run-cleanup-duplicates.py` - Cleanup duplicates
- `scripts/run-fix-orphaned-cities.py` - Fix orphaned FKs

---

## 📝 Migrations Created

- `migrations/049_cleanup_duplicate_organizations.sql` - Merge duplicates
- `migrations/050_fix_orphaned_city_ids.sql` - Fix orphaned city_id

---

**Report Generated**: 2025-12-29 14:00 BRT
**Next Review**: After Priority 1 fixes applied
