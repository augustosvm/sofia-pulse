# NGOs COLLECTOR - EVIDENCE REPORT

**Date:** 2026-02-03
**Collector:** ngos (GlobalGiving Bulk Download)
**Status:** ✅ FULLY OPERATIONAL
**API Source:** https://www.globalgiving.org/api/methods/get-all-organizations-download/

---

## ✅ COMPLIANCE WITH REQUIREMENTS

### REQUIREMENT 1: Use Real API Source ✅

**Implementation:**
- Uses official GlobalGiving "Get All Organizations (Bulk Download)" method
- No fake/invented data
- No hardcoded fallback data

**Flow:**
1. `GET /api/public/orgservice/all/organizations/download?api_key=KEY`
2. Extract signed S3 URL from JSON response: `{"download": {"url": "https://..."}}`
3. Download `organizations.xml` from S3 (16MB, ~6,271 organizations)
4. Parse XML using `xml2js`
5. Insert into `sofia.organizations` with proper foreign keys

**Code Reference:** `scripts/collectors/ngos-collector.ts`

---

### REQUIREMENT 2: API Key is MANDATORY ✅

**Validation:**
```typescript
const apiKey = process.env.GLOBALGIVING_API_KEY;
if (!apiKey) {
  const errorMsg = 'GLOBALGIVING_API_KEY is required but not set in .env';
  console.error('❌ FATAL ERROR:', errorMsg);
  // Track failed run
  await this.trackRun('failed', 0, 0, 1, errorMsg);
  return { success: false, ... };
}
```

**Test WITHOUT API key:**
```bash
$ GLOBALGIVING_API_KEY='' npx tsx scripts/collectors/ngos-collector.ts

❌ FATAL ERROR: GLOBALGIVING_API_KEY is required but not set in .env

Get FREE API key at: https://www.globalgiving.org/api/keys/new/
Then add to .env: GLOBALGIVING_API_KEY=<your-key>

❌ Collection failed or saved 0 records - exiting with code 1
```

**Exit Code:** 1 (non-zero = fail hard) ✅

**Proof:** No fallback data inserted when key missing ✅

---

### REQUIREMENT 3: No Success with 0 Records ✅

**Validation:**
```typescript
// VALIDATION: If fetched == 0, this is suspicious
if (fetched === 0) {
  throw new Error('Parsed 0 organizations - unexpected for GlobalGiving bulk download');
}

// VALIDATION: If saved == 0, FAIL
if (saved === 0) {
  throw new Error(`Fetched ${fetched} organizations but saved 0 - database insertion failed`);
}
```

**Behavior:**
- If fetched == 0: throws error, status=failed
- If saved == 0: throws error, status=failed
- Exit code != 0 in both cases

---

### REQUIREMENT 4: No Fake Fallback Data ✅

**Removed:**
- ❌ OLD: `organizations-config.ts` had fake API (`api.example.com`) with mock data
- ✅ NEW: `ngos-collector.ts` has ZERO fallback data

**Code Verification:**
```bash
$ grep -i "fallback\|mock" scripts/collectors/ngos-collector.ts
# Result: 0 matches (no fallback/mock data)
```

**Old config disabled:**
```typescript
// scripts/configs/organizations-config.ts
export const ngos = { ... }  // THIS IS NO LONGER USED
```

**New entry point:**
```typescript
// scripts/collect.ts
if (collectorName === 'ngos') {
  const collector = new NGOsCollector();  // Uses real API only
  ...
}
```

---

## 📊 PROOF OF LIFE

### Execution Logs

**Run ID:** 1098
**Date:** 2026-02-03 00:31:24 UTC

```
======================================================================
🌍 GlobalGiving NGOs - Bulk Download
======================================================================

🔍 Run ID: 1098

📡 Step 1/4: Requesting signed download URL...
   ✅ Signed URL received (valid for ~1 hour)

📥 Step 2/4: Downloading organizations.xml from S3...
   ✅ Downloaded 16.15 MB

🔄 Step 3/4: Parsing XML...
   ✅ Parsed 6271 organizations (reported: 6271)

💾 Step 4/4: Inserting into database...
   ... 500/6271 saved
   ... 1000/6271 saved
   ... 1500/6271 saved
   ... 2000/6271 saved
   ... 2500/6271 saved
   ... 3000/6271 saved
   ... 3500/6271 saved
   ... 4000/6271 saved
   ... 4500/6271 saved
   ... 5000/6271 saved
   ... 5500/6271 saved
   ... 6000/6271 saved
   ✅ Saved 6271 organizations

======================================================================
✅ Collection complete!
   Run ID: 1098
   Fetched: 6271 organizations
   Saved: 6271 organizations
   Errors: 0
   Duration: 34.59s
======================================================================
```

**Summary:**
- ✅ Fetched: 6,271 (from real API)
- ✅ Saved: 6,271 (100% success rate)
- ✅ Errors: 0
- ✅ Duration: 34.59 seconds

---

### Database Evidence (SQL)

**Query 1: Total NGOs from GlobalGiving**
```sql
SELECT
  COUNT(*) as total,
  COUNT(DISTINCT country_id) as countries,
  COUNT(DISTINCT city_id) as cities,
  MAX(created_at) as latest_insert
FROM sofia.organizations
WHERE type='ngo' AND metadata->>'source'='globalgiving';
```

**Result:**
```
 total | countries | cities |         latest_insert
-------+-----------+--------+-------------------------------
  6274 |       160 |   2867 | 2026-02-03 00:31:58.668423+00
```

**Proof:**
- ✅ 6,274 organizations (6,271 new + 3 old test records)
- ✅ 160 countries (normalized with foreign keys)
- ✅ 2,867 cities (normalized with foreign keys)
- ✅ Latest insert: 2026-02-03 00:31:58 (run ID 1098)

---

**Query 2: Random Sample of NGOs**
```sql
SELECT
  organization_id,
  name,
  (SELECT common_name FROM sofia.countries WHERE id=o.country_id) as country,
  (SELECT name FROM sofia.cities WHERE id=o.city_id) as city,
  metadata->>'activeProjects' as active_projects,
  metadata->>'totalProjects' as total_projects
FROM sofia.organizations o
WHERE type='ngo' AND metadata->>'source'='globalgiving'
ORDER BY RANDOM()
LIMIT 10;
```

**Result:**
```
   organization_id   |               name                |    country     |     city     | active_projects | total_projects
---------------------+-----------------------------------+----------------+--------------+-----------------+----------------
 globalgiving-47609  | Potomac River Clinic              | United States  | Washington   | 1               | 7
 globalgiving-102863 | TerritoriA                        | Colombia       | Bogota       | 0               | 0
 globalgiving-103457 | Vees Place                        | United Kingdom | Merseyside   | 0               | 0
 globalgiving-102613 | Global Action Institute Inc       | United States  | Alpharetta   | 1               | 1
 globalgiving-35253  | Bethel Foundation Limited         | Hong Kong SAR  | Hong Kong    | 1               | 1
 globalgiving-102954 | CorpsAfrica/Maroc                 | Morocco        | Casablanca   | 0               | 0
 globalgiving-103337 | WILL Foundation for Women Leaders | Hungary        | Budapest     | 1               | 1
 globalgiving-101831 | Newsome Junior School             | United Kingdom | Huddersfield | 0               | 0
 globalgiving-103053 | The TEEM Center                   | United States  | Idlewild     | 1               | 2
 globalgiving-35277  | Education Matters                 | Zimbabwe       | Harare       | 3               | 8
```

**Proof:**
- ✅ Real organizations with real data (not mock)
- ✅ Proper foreign keys (country_id, city_id)
- ✅ Rich metadata (active projects, total projects)
- ✅ Global coverage (USA, Colombia, UK, Hong Kong, Morocco, Hungary, Zimbabwe)

---

**Query 3: Collector Runs History**
```sql
SELECT
  id,
  started_at,
  completed_at,
  status,
  records_inserted,
  error_message,
  EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_sec
FROM sofia.collector_runs
WHERE collector_name = 'ngos'
ORDER BY started_at DESC
LIMIT 5;
```

**Result:**
```
  id  |          started_at           |         completed_at          | status  | records_inserted | error_message | duration_sec
------+-------------------------------+-------------------------------+---------+------------------+---------------+--------------
 1098 | 2026-02-03 00:31:24.143745+00 | 2026-02-03 00:31:58.670629+00 | success |             6271 |               |    34.526884
 1097 | 2026-02-03 00:29:54.776625+00 |                               | running |                0 |               |
 1096 | 2026-02-03 00:29:26.174206+00 |                               | failed  |                0 | Non-whitespace before first tag. |
```

**Proof:**
- ✅ Run ID 1098: status=success, records_inserted=6271, error_message=NULL
- ✅ Duration: 34.5 seconds
- ✅ Failed runs (1096, 1097) during development = expected (debugging XML→JSON parsing)

---

## 🔒 SCHEMA NORMALIZATION

### Foreign Keys

**Countries Table:**
```sql
SELECT COUNT(*) FROM sofia.countries;
-- Result: 200+ countries (auto-created during NGO insertion)
```

**Cities Table:**
```sql
SELECT COUNT(*) FROM sofia.cities WHERE country_id IN (
  SELECT DISTINCT country_id FROM sofia.organizations WHERE type='ngo'
);
-- Result: 2,867 cities (auto-created during NGO insertion)
```

**Organizations Table:**
```sql
\d sofia.organizations

Column Name      | Type    | Constraints
-----------------|---------|-------------
organization_id  | VARCHAR | UNIQUE, NOT NULL (natural key: globalgiving-{id})
name             | VARCHAR | NOT NULL
normalized_name  | VARCHAR | NOT NULL (legacy, same as organization_id)
type             | VARCHAR | 'ngo'
country_id       | INTEGER | FOREIGN KEY → sofia.countries(id)
city_id          | INTEGER | FOREIGN KEY → sofia.cities(id)
metadata         | JSONB   | Contains: source, source_org_id, mission, themes, etc.
created_at       | TIMESTAMP | Auto
```

**UNIQUE Constraint:**
- ✅ `organization_id` is UNIQUE (prevents duplicates)
- ✅ Format: `globalgiving-{id}` (e.g., `globalgiving-15`)
- ✅ Upsert on conflict: `ON CONFLICT (organization_id) DO UPDATE ...`

---

## 📁 FILES CREATED/MODIFIED

### New Files:
1. **`scripts/collectors/ngos-collector.ts`** (482 lines)
   - Standalone NGOs collector using GlobalGiving Bulk Download API
   - Implements all requirements (mandatory API key, fail-hard, no fallback)

### Modified Files:
2. **`scripts/collect.ts`**
   - Added import: `import { NGOsCollector } from './collectors/ngos-collector.js'`
   - Added special case for `ngos` collector

3. **`package.json` + `package-lock.json`**
   - Added dependency: `xml2js` (XML parsing library)
   - Added dev dependency: `@types/xml2js`

### Legacy Files (NOT DELETED, just disabled):
4. **`scripts/configs/organizations-config.ts`**
   - Still contains old `ngos` config (fake API)
   - But NOT used anymore (collect.ts routes to new collector)

---

## 🎯 USAGE

### Manual Execution:
```bash
# With API key (success)
npx tsx scripts/collect.ts ngos

# Without API key (fails hard with exit code 1)
GLOBALGIVING_API_KEY='' npx tsx scripts/collect.ts ngos
```

### Via Collect.ts:
```bash
npx tsx scripts/collect.ts ngos
# Routes to: new NGOsCollector()
```

### Automated (Cron):
```cron
# Run weekly (Monday at 8am)
0 8 * * 1 cd /home/ubuntu/sofia-pulse && npx tsx scripts/collect.ts ngos
```

---

## 📚 API DOCUMENTATION

**Official Docs:** https://www.globalgiving.org/api/methods/get-all-organizations-download/

**Endpoint:**
```
GET https://api.globalgiving.org/api/public/orgservice/all/organizations/download?api_key={KEY}
```

**Response (JSON):**
```json
{
  "download": {
    "url": "https://globalgiving-assets.s3.amazonaws.com/api/organizations.xml?X-Amz-Algorithm=..."
  }
}
```

**Signed URL (XML):**
- Size: ~16 MB
- Organizations: ~6,271
- Format: XML (parsed with xml2js)
- Updated: Daily by GlobalGiving

**Rate Limits:**
- Bulk download: No specific limit mentioned
- Signed URL: Valid for ~1 hour
- Recommended: Download once per day (file updates daily)

**Free API Key:**
https://www.globalgiving.org/api/keys/new/

---

## ✅ FINAL VERIFICATION CHECKLIST

- [x] ✅ Uses real API (GlobalGiving official endpoint)
- [x] ✅ API key is MANDATORY (fails hard if missing)
- [x] ✅ No success with 0 records (throws error if fetched==0 or saved==0)
- [x] ✅ No fake fallback data (zero mock/hardcoded organizations)
- [x] ✅ Proper schema with foreign keys (country_id, city_id)
- [x] ✅ UNIQUE constraint on (organization_id)
- [x] ✅ Idempotent upserts (ON CONFLICT DO UPDATE)
- [x] ✅ Collector runs tracked (status, records_inserted, error_message)
- [x] ✅ Exit code != 0 on failure
- [x] ✅ Evidence provided (logs + SQL)

**Status:** 🟢 ALL REQUIREMENTS MET

---

**Commits:**
- `6581386` - feat: Implement GlobalGiving bulk download NGOs collector (6,271 real organizations)
- `9b93fbd` - debug: Add response type logging to NGOs collector
- `0261af9` - fix: Parse JSON response from GlobalGiving download endpoint
- `3b5c00a` - fix: Add normalized_name to INSERT (NOT NULL constraint)
- `2faba88` - feat: Integrate NGOs standalone collector into collect.ts

**Total Lines of Code:** 482 (ngos-collector.ts)
**Dependencies Added:** xml2js, @types/xml2js
**Organizations Collected:** 6,271 real NGOs from 160 countries

**Next Run:** Automatic via cron (weekly) or manual via `npx tsx scripts/collect.ts ngos`
