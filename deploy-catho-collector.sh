#!/bin/bash
################################################################################
# Deploy: Catho Jobs Collector - Production Setup
################################################################################
#
# This script deploys the Catho collector to production
#
# Run on server:
#   bash deploy-catho-collector.sh
#
################################################################################

set -e

echo "🚀 Deploying Catho Jobs Collector"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if running as root for dependencies installation
if [[ $EUID -ne 0 ]]; then
   echo "⚠️  Warning: Not running as root. Some steps may require sudo."
   echo ""
fi

################################################################################
# STEP 1: Pull latest code
################################################################################

echo "📥 Step 1: Pulling latest code from GitHub..."
git pull origin master
echo "   ✅ Code updated"
echo ""

################################################################################
# STEP 2: Install Node dependencies
################################################################################

echo "📦 Step 2: Installing Node.js dependencies..."
npm install
echo "   ✅ Dependencies installed"
echo ""

################################################################################
# STEP 3: Install Chrome dependencies (requires sudo)
################################################################################

echo "🌐 Step 3: Installing Chrome/Chromium dependencies..."
echo "   This requires root privileges. You may need to enter your password."
echo ""

if [[ $EUID -eq 0 ]]; then
    bash scripts/install-chrome-dependencies.sh
else
    sudo bash scripts/install-chrome-dependencies.sh
fi

echo "   ✅ Chrome dependencies installed"
echo ""

################################################################################
# STEP 4: Apply database migration
################################################################################

echo "💾 Step 4: Applying database migration (UNIQUE constraint on job_id)..."
npx tsx scripts/apply-migration-009.ts
echo "   ✅ Migration applied"
echo ""

################################################################################
# STEP 5: Clean duplicate jobs (if any)
################################################################################

echo "🧹 Step 5: Cleaning duplicate jobs (if any)..."
npx tsx scripts/clean-duplicate-jobs.ts
echo "   ✅ Duplicates cleaned"
echo ""

################################################################################
# STEP 6: Run integration test
################################################################################

echo "🧪 Step 6: Running integration test with mock data..."
npx tsx scripts/test-catho-integration.ts
echo "   ✅ Integration test passed"
echo ""

################################################################################
# STEP 7: Test real data collection (optional)
################################################################################

read -p "🎯 Step 7: Do you want to run a test collection with REAL data? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   Running Catho collector..."
    echo "   This will take a few minutes (67 keywords to process)..."
    bash scripts/automation/collect-catho-jobs.sh
    echo "   ✅ Test collection completed"
else
    echo "   ⏭️  Skipped real data collection"
fi
echo ""

################################################################################
# STEP 8: Check results
################################################################################

echo "📊 Step 8: Checking results in database..."
npx tsx << 'TYPESCRIPT'
import { Pool } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD || 'sofia123strong',
  database: process.env.POSTGRES_DB || 'sofia_db',
});

(async () => {
  const result = await pool.query(`
    SELECT
      COUNT(*) as total,
      COUNT(*) FILTER (WHERE platform = 'catho') as catho_jobs,
      COUNT(*) FILTER (WHERE platform = 'catho' AND collected_at >= NOW() - INTERVAL '24 hours') as catho_24h,
      COUNT(*) FILTER (WHERE platform = 'catho' AND salary_min IS NOT NULL) as with_salary,
      COUNT(*) FILTER (WHERE platform = 'catho' AND remote_type IS NOT NULL) as with_remote_type,
      COUNT(*) FILTER (WHERE platform = 'catho' AND seniority_level IS NOT NULL) as with_seniority,
      COUNT(*) FILTER (WHERE platform = 'catho' AND array_length(skills_required, 1) > 0) as with_skills
    FROM sofia.jobs;
  `);

  const row = result.rows[0];
  console.log('   📊 Database Statistics:');
  console.log(`      Total jobs: ${row.total}`);
  console.log(`      Catho jobs: ${row.catho_jobs}`);
  console.log(`      Catho (last 24h): ${row.catho_24h}`);
  console.log(`      With salary: ${row.with_salary}`);
  console.log(`      With remote type: ${row.with_remote_type}`);
  console.log(`      With seniority: ${row.with_seniority}`);
  console.log(`      With skills: ${row.with_skills}`);
  console.log('');

  await pool.end();
})();
TYPESCRIPT

echo ""

################################################################################
# STEP 9: Summary
################################################################################

echo "════════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📋 What was deployed:"
echo "   ✅ Catho Jobs Collector (scripts/collect-catho-final.ts)"
echo "   ✅ Parse Helpers (salary, skills, seniority, remote, sector)"
echo "   ✅ Database migration (UNIQUE constraint on job_id)"
echo "   ✅ Chrome dependencies for Puppeteer"
echo "   ✅ Integration with automation (collect-all-complete.sh)"
echo ""
echo "🚀 How to run:"
echo "   Manual: bash scripts/automation/collect-catho-jobs.sh"
echo "   Auto:   bash scripts/automation/collect-all-complete.sh (includes Catho)"
echo ""
echo "🔧 Troubleshooting:"
echo "   Check schema:     npx tsx scripts/check-jobs-schema.ts"
echo "   Check duplicates: npx tsx scripts/check-job-id-duplicates.ts"
echo "   Clean duplicates: npx tsx scripts/clean-duplicate-jobs.ts"
echo "   Test integration: npx tsx scripts/test-catho-integration.ts"
echo ""
echo "📊 The collector is now part of the automated daily collection!"
echo ""
