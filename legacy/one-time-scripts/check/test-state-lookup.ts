#!/usr/bin/env npx tsx
import {Pool} from 'pg';
import {getStateId} from './scripts/shared/geo-id-helpers.js';

const pool = new Pool({
  host: '91.98.158.19',
  port: 5432,
  user: 'sofia',
  password: 'sofia123strong',
  database: 'sofia_db'
});

async function testStateLookup() {
  console.log('\n🧪 Testing State Lookup:\n');

  const usCountryId = 1; // United States

  const tests = [
    {name: 'Louisiana', expected: 'LA'},
    {name: 'Florida', expected: 'FL'},
    {name: 'California', expected: 'CA'},
    {name: 'New York', expected: 'NY'},
  ];

  for (const test of tests) {
    const stateId = await getStateId(pool, test.name, usCountryId);

    if (stateId) {
      const result = await pool.query('SELECT name, code FROM sofia.states WHERE id = $1', [stateId]);
      console.log(`✅ ${test.name} → Found: ${result.rows[0].name} (${result.rows[0].code})`);
    } else {
      console.log(`❌ ${test.name} → NOT FOUND`);
    }
  }

  await pool.end();
}

testStateLookup();
