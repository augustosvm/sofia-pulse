#!/usr/bin/env tsx
/**
 * Refresh Security Materialized Views
 * Run after ACLED data is collected to update maps
 */

import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import { sql } from 'drizzle-orm';

const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
  console.error('❌ DATABASE_URL not set');
  process.exit(1);
}

async function main() {
  console.log('🔄 Refreshing security materialized views...\n');

  const client = postgres(DATABASE_URL);
  const db = drizzle(client);

  try {
    // Check current data
    console.log('📊 Checking current data in security_events table...');
    const totalEvents = await db.execute(sql`
      SELECT
        COUNT(*) as total,
        MIN(latitude) as min_lat,
        MAX(latitude) as max_lat,
        MIN(longitude) as min_lng,
        MAX(longitude) as max_lng,
        COUNT(DISTINCT country_code) as countries
      FROM sofia.security_events
    `);

    const stats = totalEvents[0] as any;
    console.log(`   Total events: ${stats.total}`);
    console.log(`   Countries: ${stats.countries}`);
    console.log(`   Lat range: ${stats.min_lat} to ${stats.max_lat}`);
    console.log(`   Lng range: ${stats.min_lng} to ${stats.max_lng}\n`);

    if (Number(stats.total) === 0) {
      console.log('⚠️  No data in security_events table!');
      console.log('   Run ACLED collector first: npm run collect:acled\n');
      process.exit(1);
    }

    // Refresh views
    console.log('🔄 Refreshing materialized views...');
    await db.execute(sql`SELECT sofia.refresh_security_views()`);
    console.log('✅ Views refreshed!\n');

    // Check geo points
    const geoCount = await db.execute(sql`
      SELECT COUNT(*) as count FROM sofia.mv_security_geo_points
    `);
    console.log(`📍 Geo points in view: ${(geoCount[0] as any).count}\n`);

    // Sample by region
    console.log('🌍 Sample countries by region:');
    const sample = await db.execute(sql`
      SELECT country_code, country_name, incidents, severity_norm, risk_level
      FROM sofia.mv_security_country_summary
      ORDER BY severity_norm DESC
      LIMIT 20
    `);

    (sample as any[]).forEach((row: any, i: number) => {
      console.log(`   ${i + 1}. ${row.country_name} (${row.country_code}): ${row.incidents} incidents, severity ${row.severity_norm}, ${row.risk_level}`);
    });

    console.log('\n✅ Done! Refresh your map in the browser.');

  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

main();
