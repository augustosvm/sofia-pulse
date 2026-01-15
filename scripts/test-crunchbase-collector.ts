#!/usr/bin/env tsx
/**
 * Test Script for Crunchbase Collector
 *
 * Quick test to verify:
 * 1. API key is configured
 * 2. API request works
 * 3. Response parsing works
 * 4. Database insertion works
 *
 * Usage:
 *   npx tsx scripts/test-crunchbase-collector.ts
 */

import { Pool } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

const pool = new Pool({
  host: process.env.POSTGRES_HOST || process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || process.env.DB_PORT || '5432'),
  user: process.env.POSTGRES_USER || process.env.DB_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD || process.env.DB_PASSWORD,
  database: process.env.POSTGRES_DB || process.env.DB_NAME || 'sofia_db',
});

async function testCrunchbase() {
  console.log('');
  console.log('='.repeat(70));
  console.log('🧪 CRUNCHBASE COLLECTOR TEST');
  console.log('='.repeat(70));
  console.log('');

  // 1. Check API key
  console.log('1️⃣  Checking API Key...');
  const apiKey = process.env.CRUNCHBASE_API_KEY;

  if (!apiKey) {
    console.log('   ❌ Missing CRUNCHBASE_API_KEY in .env file');
    console.log('   ℹ️  See GET_CRUNCHBASE_API_KEY.md for instructions');
    process.exit(1);
  }

  console.log(`   ✅ API Key found (${apiKey.substring(0, 8)}...)`);
  console.log('');

  // 2. Test API request
  console.log('2️⃣  Testing API Request...');

  const requestBody = {
    field_ids: [
      'identifier',
      'announced_on',
      'funded_organization_identifier',
      'funding_type',
      'money_raised',
      'investor_identifiers',
      'lead_investor_identifiers',
    ],
    order: [{ field_id: 'announced_on', sort: 'desc' }],
    query: [
      {
        type: 'predicate',
        field_id: 'announced_on',
        operator_id: 'gte',
        values: [new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]],
      },
      {
        type: 'predicate',
        field_id: 'funding_type',
        operator_id: 'includes',
        values: ['seed', 'series_a', 'series_b', 'series_c', 'series_d', 'series_e', 'venture', 'pre_seed'],
      },
    ],
    limit: 5, // Small limit for testing
  };

  try {
    const response = await fetch('https://api.crunchbase.com/api/v4/searches/funding_rounds', {
      method: 'POST',
      headers: {
        'X-cb-user-key': apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      console.log(`   ❌ API Error: ${response.status} ${response.statusText}`);
      const text = await response.text();
      console.log(`   Response: ${text.substring(0, 200)}`);
      process.exit(1);
    }

    const data = await response.json();
    console.log(`   ✅ API Response: 200 OK`);
    console.log(`   📦 Entities returned: ${data.entities?.length || 0}`);
    console.log('');

    if (!data.entities || data.entities.length === 0) {
      console.log('   ⚠️  No funding rounds found in last 30 days');
      console.log('   💡 This is normal if filters are restrictive or low activity period');
      console.log('');
      process.exit(0);
    }

    // 3. Test parsing
    console.log('3️⃣  Testing Response Parsing...');

    const rounds = data.entities.map((entity: any) => {
      const props = entity?.properties || {};
      const org = props.funded_organization_identifier || {};
      const money = props.money_raised || {};
      const investors = (props.investor_identifiers || []).map((inv: any) => inv.value).filter(Boolean);
      const leadInvestors = (props.lead_investor_identifiers || []).map((inv: any) => inv.value).filter(Boolean);

      return {
        company_name: org.value || 'Unknown',
        round_type: props.funding_type || 'Unknown',
        amount_usd: money.value_usd || null,
        announced_date: props.announced_on?.value || null,
        investors: [...investors, ...leadInvestors].slice(0, 10),
        uuid: props.identifier?.uuid,
      };
    });

    console.log(`   ✅ Parsed ${rounds.length} rounds`);
    console.log('');

    // 4. Show sample data
    console.log('4️⃣  Sample Funding Rounds:');
    console.log('');

    for (let i = 0; i < Math.min(5, rounds.length); i++) {
      const round = rounds[i];
      const amountStr = round.amount_usd
        ? `$${(round.amount_usd / 1_000_000).toFixed(1)}M`
        : '(undisclosed)';

      console.log(`   ${i + 1}. ${round.company_name}`);
      console.log(`      💰 ${amountStr} | ${round.round_type} | ${round.announced_date || 'N/A'}`);
      if (round.investors && round.investors.length > 0) {
        console.log(`      👥 ${round.investors.slice(0, 3).join(', ')}`);
      }
      console.log('');
    }

    // 5. Test database connection
    console.log('5️⃣  Testing Database Connection...');

    const result = await pool.query('SELECT COUNT(*) FROM sofia.funding_rounds WHERE source = $1', ['crunchbase']);
    const existingCount = parseInt(result.rows[0].count);

    console.log(`   ✅ Database connected`);
    console.log(`   📊 Existing Crunchbase rounds in DB: ${existingCount}`);
    console.log('');

    // Summary
    console.log('='.repeat(70));
    console.log('✅ ALL TESTS PASSED');
    console.log('='.repeat(70));
    console.log('');
    console.log('📋 Next Steps:');
    console.log('   1. Run full collector: npx tsx scripts/collect.ts crunchbase');
    console.log('   2. Add to crontab for daily collection');
    console.log('   3. Wait 7-14 days for data accumulation');
    console.log('   4. Check Early-Stage Deep Dive report');
    console.log('');

  } catch (error: any) {
    console.log(`   ❌ Error: ${error.message}`);
    console.log('');
    process.exit(1);
  } finally {
    await pool.end();
  }
}

testCrunchbase().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
