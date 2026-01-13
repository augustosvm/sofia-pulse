#!/usr/bin/env tsx
/**
 * Test auto-create cities functionality
 */
import { Pool } from 'pg';
import { normalizeLocation } from './shared/geo-helpers.js';
import * as dotenv from 'dotenv';

dotenv.config();

const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD || 'SofiaPulse2025Secure@DB',
  database: process.env.POSTGRES_DB || 'sofia_db',
});

async function testAutoCreateCity() {
  console.log('🧪 Testing Auto-Create City Functionality\n');

  // Test 1: City that doesn't exist yet
  console.log('Test 1: Creating a new city (Americana, SP)');
  const result1 = await normalizeLocation(pool, {
    country: 'Brazil',
    state: 'SP',
    city: 'Americana'
  });
  console.log('Result:', result1);
  console.log('');

  // Test 2: City that already exists
  console.log('Test 2: Using existing city (São Paulo, SP)');
  const result2 = await normalizeLocation(pool, {
    country: 'Brazil',
    state: 'SP',
    city: 'São Paulo'
  });
  console.log('Result:', result2);
  console.log('');

  // Test 3: City with different casing
  console.log('Test 3: Creating city with accent (Jundiaí, SP)');
  const result3 = await normalizeLocation(pool, {
    country: 'Brazil',
    state: 'SP',
    city: 'Jundiaí'
  });
  console.log('Result:', result3);
  console.log('');

  await pool.end();
  console.log('✅ Test completed!');
}

testAutoCreateCity();
