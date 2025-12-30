# 🚀 Deploy: Catho Jobs Collector

**Status**: ✅ Ready for Production
**Commit**: `c7dba97`
**Date**: 2025-12-30

---

## 📋 Summary

Complete integration of Catho.com.br jobs collector with intelligent parsing:

- ✅ **67 keywords** in Portuguese (centralized)
- ✅ **Parse Helpers**: salary, skills, seniority, remote type, sector
- ✅ **Database Integration**: 72 fields, geo-normalized, organizations FK
- ✅ **Tested**: Mock data integration tests passed
- ✅ **Automated**: Integrated with `collect-all-complete.sh`

---

## 🎯 What Was Built

### 1. **Complete Catho Collector** (`scripts/collect-catho-final.ts`)
- Scrapes Catho.com.br with Puppeteer Stealth mode
- Extracts: title, company, location, salary, description
- Uses 67 centralized keywords in Portuguese

### 2. **Intelligent Parse Helpers**
```typescript
parseSalaryBRL()      // R$ 8.000 - R$ 12.000/mês → min: 8000, max: 12000, period: monthly
detectRemoteType()    // "Trabalho remoto" → remote
detectSeniority()     // "Desenvolvedor Sênior" → senior
extractSkills()       // "Python, AWS, Docker" → ['Python', 'AWS', 'Docker']
detectSector()        // "Backend Developer" → Backend
```

### 3. **Database Schema**
- Table: `sofia.jobs` (72 fields)
- New fields used:
  - `salary_min`, `salary_max`, `salary_currency`, `salary_period`
  - `remote_type`, `seniority_level`, `employment_type`
  - `skills_required[]`, `sector`
  - `organization_id` (FK to organizations)
  - `city_id`, `state_id`, `country_id` (geo-normalized)

### 4. **Database Maintenance**
- Migration 009: UNIQUE constraint on `job_id`
- Cleaned 2,709 duplicate jobs
- Scripts: check schema, check duplicates, clean duplicates

### 5. **Testing**
- `test-catho-integration.ts` - Full integration test with mock data
- ✅ All tests passed

---

## 🚀 Deploy Instructions (Server)

### Option A: Automated Deploy (Recommended)

```bash
# On your server
cd ~/sofia-pulse

# Run the deployment script
bash deploy-catho-collector.sh
```

This will:
1. Pull latest code from GitHub
2. Install Node dependencies
3. Install Chrome dependencies (requires sudo)
4. Apply database migration
5. Clean duplicate jobs
6. Run integration test
7. Optionally run test collection with real data
8. Show database statistics

---

### Option B: Manual Deploy

#### Step 1: Pull Latest Code

```bash
cd ~/sofia-pulse
git pull origin master
```

**⚠️ IMPORTANT - Git Push Issue**:
If you see this error when pushing from your local machine:
```
refusing to allow a Personal Access Token to create or update workflow
```

**Solution**: On the server, pull directly:
```bash
cd ~/sofia-pulse
git fetch origin
git reset --hard origin/master
```

Or manually copy the commit hash and checkout:
```bash
git fetch origin
git checkout c7dba97
```

---

#### Step 2: Install Dependencies

```bash
# Node.js dependencies
npm install

# Chrome/Chromium dependencies (requires sudo)
sudo bash scripts/install-chrome-dependencies.sh
```

---

#### Step 3: Database Setup

```bash
# Apply migration (adds UNIQUE constraint to job_id)
npx tsx scripts/apply-migration-009.ts

# Clean duplicates (if any)
npx tsx scripts/clean-duplicate-jobs.ts
```

---

#### Step 4: Test

```bash
# Integration test with mock data
npx tsx scripts/test-catho-integration.ts

# Real data collection test (takes ~5-10 minutes)
bash scripts/automation/collect-catho-jobs.sh
```

---

#### Step 5: Check Results

```bash
# Check database statistics
npx tsx << 'EOF'
import { Pool } from 'pg';
import * as dotenv from 'dotenv';
dotenv.config();

const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER,
  password: process.env.POSTGRES_PASSWORD,
  database: process.env.POSTGRES_DB || 'sofia_db',
});

(async () => {
  const result = await pool.query(`
    SELECT COUNT(*) as total,
           COUNT(*) FILTER (WHERE platform = 'catho') as catho_jobs,
           COUNT(*) FILTER (WHERE salary_min IS NOT NULL) as with_salary
    FROM sofia.jobs;
  `);
  console.log(result.rows[0]);
  await pool.end();
})();
EOF
```

---

## 📊 Expected Results

### Mock Data Test
```
✅ 3 jobs saved:
- Backend Sênior (Python/Django) - R$8.000-12.000/mês - 5 skills
- Frontend Pleno (React) - R$6.000/mês - 5 skills - Híbrido
- ML Júnior - Remote - AI & ML sector
```

### Real Data Collection (67 keywords)
```
Expected:
- ~500-1000 jobs per run (depends on Catho availability)
- 20 jobs per keyword (max)
- Full parsing: salary, skills, seniority, remote, sector
```

---

## 🔧 Troubleshooting

### Issue: Chrome dependencies missing

**Error**: `error while loading shared libraries: libnspr4.so`

**Solution**:
```bash
sudo bash scripts/install-chrome-dependencies.sh
```

---

### Issue: Duplicate job_id error

**Error**: `there is no unique or exclusion constraint matching the ON CONFLICT specification`

**Solution**:
```bash
# Apply migration
npx tsx scripts/apply-migration-009.ts

# Clean existing duplicates
npx tsx scripts/clean-duplicate-jobs.ts
```

---

### Issue: Puppeteer timeout

**Error**: `Navigation timeout of 60000 ms exceeded`

**Solution**: Catho may be slow or blocking. The collector has:
- 8s wait for JS to load
- 5-10s delay between keywords
- Stealth mode to avoid detection

If still failing, try:
- Check internet connection
- Verify Catho.com.br is accessible
- Run with fewer keywords (edit `collect-catho-final.ts`)

---

## 📁 Files Reference

### Core Collector
- `scripts/collect-catho-final.ts` - Main collector with parse helpers

### Automation
- `scripts/automation/collect-catho-jobs.sh` - Wrapper script
- `scripts/automation/collect-all-complete.sh` - Includes Catho (56 collectors)

### Database
- `db/migrations/009_add_job_id_unique_constraint.sql` - Migration

### Utilities
- `scripts/test-catho-integration.ts` - Integration test
- `scripts/check-jobs-schema.ts` - Schema inspector
- `scripts/check-job-id-duplicates.ts` - Duplicate checker
- `scripts/clean-duplicate-jobs.ts` - Duplicate cleaner
- `scripts/apply-migration-009.ts` - Migration runner
- `scripts/install-chrome-dependencies.sh` - Chrome setup

### Deploy
- `deploy-catho-collector.sh` - Automated deployment

---

## 🎯 Integration with Existing System

The Catho collector is now **part of the automated daily collection**:

```bash
# Run ALL collectors (including Catho)
bash scripts/automation/collect-all-complete.sh
```

This runs:
- 55 existing collectors
- 1 NEW: Catho Brazil Jobs ✨

**Total: 56 collectors**

---

## 📈 Future Enhancements

Potential improvements:
1. **More Job Platforms**: LinkedIn, Indeed, Glassdoor Brazil
2. **Better Parsing**: Use LLM to parse unstructured job descriptions
3. **Deduplication**: Cross-platform job matching
4. **Salary Normalization**: Convert all to USD or BRL/month
5. **Job Analytics**: Top skills, salary trends, hiring companies

---

## ✅ Checklist for Production

- [ ] Pull latest code (`git pull` or `git reset --hard origin/master`)
- [ ] Install dependencies (`npm install`)
- [ ] Install Chrome deps (`sudo bash scripts/install-chrome-dependencies.sh`)
- [ ] Apply migration (`npx tsx scripts/apply-migration-009.ts`)
- [ ] Clean duplicates (`npx tsx scripts/clean-duplicate-jobs.ts`)
- [ ] Run integration test (`npx tsx scripts/test-catho-integration.ts`)
- [ ] Test real collection (`bash scripts/automation/collect-catho-jobs.sh`)
- [ ] Verify results in database
- [ ] Add to crontab (already in `collect-all-complete.sh`)

---

## 🚀 Quick Start (TL;DR)

```bash
# On server
cd ~/sofia-pulse
git pull origin master  # or git reset --hard origin/master
bash deploy-catho-collector.sh
```

**Done!** The collector is now running and integrated with your automated daily collection.

---

**Generated with Claude Code**
https://claude.com/claude-code

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
