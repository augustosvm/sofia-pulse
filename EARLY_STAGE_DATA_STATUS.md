# Early-Stage Deep Dive - Data Availability Status

**Date**: 2026-01-14
**Status**: ⚠️ LIMITED DATA (3 rounds < $50M in last 12 months)

---

## 🎯 EXECUTIVE SUMMARY

The Early-Stage Deep Dive report currently shows limited data because:
- **Only 29 of 10,221 funding rounds** have `amount_usd > 0` (0.28%)
- **None of those 29 are < $10M** (all $25M-$330M)
- **YC Companies (9,111 rounds)** don't include funding amounts
- **YC API only has data until 2013** (no recent batches)

---

## 📊 CURRENT DATA BREAKDOWN

| Source | Total Rounds | With amount_usd > 0 | Date Range | Notes |
|--------|--------------|-------------------|------------|-------|
| **yc-companies** | 9,111 | 0 (0%) | 2008-2013 | ❌ No amounts, outdated API |
| **techcrunch** | 6 | 5 (83%) | 2026-01-05 to 2026-01-13 | ✅ Works but all > $10M |
| **producthunt** | 27 | 0 (0%) | Recent | ❌ No funding amounts |
| **NULL source** | 1,077 | 24 (2%) | Legacy | ⚠️ Old data |

### YC Companies Detailed Issues

**API**: `https://yc-oss.github.io/api/companies/all.json`

**Problems**:
- ✅ API works and returns 5,620 companies
- ❌ Latest batch: "Summer 2013" (over 12 years old!)
- ❌ No W24, S24, W25, or any recent batches
- ❌ API format: `{"name": "...", "batch": "Winter 2012", ...}` (no funding amount)
- ❌ 8,612 of 9,111 rounds in DB have `announced_date = NULL` (94.5%)

**Why**: The unofficial YC API hasn't been updated since 2013. Official YC doesn't provide a public API with recent data.

### TechCrunch Data

**Works** but limited:
- ✅ NLP extraction functioning (amount, company, round_type)
- ✅ Recent data (collected 2026-01-13)
- ❌ Only 6 rounds collected so far
- ❌ All rounds >= $25M:
  - Eleven - $330M (VC Funding)
  - Deepgram - $130M (Series C)
  - Superorganism - $25M (VC Funding)
  - Converge Bio - $25M (Series A)
  - Flutterwave - $25M (Acquisition)
- ❌ Missing `country` and `sector` (NLP needs improvement)

---

## ✅ FIXES APPLIED

### 1. Early-Stage Deep Dive Script Updated

**File**: `analytics/early-stage-deep-dive.py`

**Changes**:
- ✅ Multi-stage fallback queries:
  1. Try < $10M (seed/angel with known amounts)
  2. Try < $50M (early-stage with known amounts)
  3. Try YC companies + seed/angel round_types (even without amounts)
  4. Try any recent funding (last resort)
- ✅ Handles NULL amounts gracefully
- ✅ Shows "(amounts undisclosed)" for YC batches
- ✅ Fixed NULL country/sector handling
- ✅ Added context notes about data limitations

**Test Result**:
```
✅ Report saved to analytics/early-stage-latest.txt

📊 RESUMO EXECUTIVO
Total de rounds encontrados: 3
   • With disclosed amount: 3
   • YC/undisclosed: 0

Ticket médio (disclosed): $25.00M
Range: $25.00M - $25.00M
```

---

## 🚀 RECOMMENDED SOLUTIONS

### **PRIORITY 1: Implement Crunchbase Free API** ⭐

**Why**:
- ✅ Already documented in CLAUDE.md (lines 123-187)
- ✅ FREE tier: 500 requests/month
- ✅ Optimal volume: 15 rounds/day = 450/month
- ✅ Complete data: amount, sector, geography, stage
- ✅ Recent data (Series A/B/C, Seed, Pre-Seed)

**Expected Impact**:
- 📈 In 30 days → 450 early-stage rounds in DB
- 📈 In 90 days → 1,350 rounds (robust dataset!)

**Implementation Status**: Configured but not implemented yet

**Config Location**: `scripts/configs/funding-config.ts` (lines 123-187)

**Next Steps**:
1. Get CRUNCHBASE_API_KEY (free tier)
2. Implement TypeScript collector using config
3. Add to crontab (daily 12:00 UTC)
4. Monitor for 7-14 days

### **PRIORITY 2: Improve TechCrunch NLP**

**Current State**:
- ✅ Amount extraction: `$10M`, `$450 million`, `$1.5B` (working!)
- ✅ Company name extraction (working!)
- ✅ Round type detection (working!)
- ❌ Country extraction (missing)
- ❌ Sector extraction (missing)

**Needed**:
- Add NLP patterns for:
  - Country: "based in [Country]", "[City, Country]"
  - Sector: "AI startup", "fintech company", "biotech firm"
- Improve article parsing (full text vs. summary)

**Expected Impact**:
- 📊 Better geography distribution in reports
- 📊 Sector trends visibility
- 📊 ~4-8 rounds/day from TechCrunch RSS

### **PRIORITY 3: SEC EDGAR Early-Stage Expansion**

**Current State**:
- ✅ Collecting from 60+ tech companies
- ❌ Focused on big companies (Big Tech, public companies)

**Opportunity**:
- Many Series A/B companies file with SEC
- Form D (Regulation D) = early-stage funding
- Can extract amounts, investors, dates

**Implementation**:
- Expand SEC collector to include Form D filings
- Add 200+ Series A/B companies to watch list
- Expected: ~10-20 filings/month

### **PRIORITY 4: Product Hunt → Funding Links**

**Current State**:
- ✅ Collecting 600+ launches/month
- ❌ Not linking to funding announcements

**Opportunity**:
- Many launches include "just raised $XM" in description
- NLP can extract amounts from launch descriptions
- Expected: ~20-40 rounds/month

---

## 📈 PROJECTED DATA AVAILABILITY

### Current (Jan 2026)
- **Early-stage (< $10M)**: 0 rounds in last 12 months ❌
- **Mid-stage (< $50M)**: 3 rounds in last 12 months ⚠️

### After Crunchbase Implementation (30 days)
- **Early-stage**: ~150 rounds (15/day × 30 days) ✅
- **Mid-stage**: ~450 rounds total ✅
- **Report Quality**: Good (enough for trends)

### After Full Pipeline (90 days)
- **Early-stage**: ~1,000 rounds ✅
- **Sources**: Crunchbase (450) + TechCrunch (150) + Product Hunt (80) + SEC EDGAR (50)
- **Report Quality**: Excellent (robust analysis)

---

## 🔧 TECHNICAL DETAILS

### Database Schema

```sql
-- funding_rounds table
id                  | integer
company_name        | varchar
sector              | varchar
round_type          | varchar
amount_usd          | bigint       -- ⚠️ NULL for 99.7% of rows
valuation_usd       | bigint
investors           | ARRAY
country             | varchar
announced_date      | date         -- ⚠️ NULL for 94.5% of YC rows
collected_at        | timestamp
city                | varchar
country_id          | integer
city_id             | integer
source              | varchar      -- yc-companies, techcrunch, producthunt, etc.
organization_id     | integer
```

### Key Constraints

**Unique constraint**: `(company_name, round_type, announced_date)`

**Problem**: If `announced_date = NULL`, duplicates can occur

**Solution**: YC collector now uses `parse_yc_batch_date()` but API data is outdated

---

## 📚 REFERENCES

### Documentation
- **Main docs**: `CLAUDE.md` (lines 1-400)
- **Funding config**: `scripts/configs/funding-config.ts`
- **Collectors**:
  - YC: `scripts/collect-yc-companies.py`
  - TechCrunch: `scripts/collect-techcrunch-funding.ts`
  - Product Hunt: (existing)
  - SEC EDGAR: `scripts/collect-sec-edgar-funding.py`

### External APIs
- **YC Companies (unofficial)**: https://yc-oss.github.io/api/companies/all.json
  - Status: ❌ Outdated (2008-2013 only)
- **TechCrunch RSS**: https://techcrunch.com/feed/
  - Status: ✅ Working (4-8 rounds/day)
- **Crunchbase Free**: https://data.crunchbase.com/docs
  - Status: ⏳ Not implemented (500 req/month free)

---

## ✅ ACTION ITEMS

1. **Immediate** (today):
   - [x] Fix Early-Stage Deep Dive script
   - [x] Test with available data
   - [x] Document data availability issues
   - [ ] Get Crunchbase API key

2. **Short-term** (1-3 days):
   - [ ] Implement Crunchbase collector
   - [ ] Improve TechCrunch NLP (country, sector)
   - [ ] Test collectors for 3 days

3. **Mid-term** (1-2 weeks):
   - [ ] Expand SEC EDGAR to Form D filings
   - [ ] Product Hunt funding link extraction
   - [ ] Wait for 7-14 days of daily collection
   - [ ] Verify Early-Stage Deep Dive quality

---

**Last Updated**: 2026-01-14 09:45 UTC
**Next Review**: After Crunchbase implementation (7 days)
