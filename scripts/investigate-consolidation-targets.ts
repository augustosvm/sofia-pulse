/**
 * Investigation Script for Phase 2 Consolidation
 *
 * Investigates:
 * 1. Gender Data (5 tables)
 * 2. Research Papers (3 tables)
 * 3. Jobs Tables
 */

import pkg from 'pg';
const { Pool } = pkg;

const pool = new Pool({
  host: '91.98.158.19',
  port: Number.parseInt(process.env.POSTGRES_PORT || '5432'),
  database: process.env.POSTGRES_DB || 'sofia_db',
  user: process.env.POSTGRES_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD || 'sofia123strong',
});

async function investigateGenderTables() {
  console.log('\n' + '='.repeat(80));
  console.log('👩 GENDER DATA TABLES (5 tables)');
  console.log('='.repeat(80));

  const genderTables = [
    'women_eurostat_data',
    'women_world_bank_data',
    'women_ilo_data',
    'central_banks_women_data',
    'gender_indicators'
  ];

  for (const table of genderTables) {
    try {
      console.log(`\n📊 ${table}:`);

      // Get schema
      const schema = await pool.query(`
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'sofia' AND table_name = $1
        ORDER BY ordinal_position;
      `, [table]);

      // Get stats
      const stats = await pool.query(`
        SELECT
          COUNT(*) as total_records,
          pg_size_pretty(pg_total_relation_size('sofia.${table}')) as table_size
        FROM sofia.${table};
      `);

      console.log(`  Records: ${stats.rows[0].total_records}`);
      console.log(`  Size: ${stats.rows[0].table_size}`);
      console.log(`  Columns: ${schema.rows.map(r => r.column_name).join(', ')}`);

      // Sample data
      const sample = await pool.query(`SELECT * FROM sofia.${table} LIMIT 1;`);
      console.log(`  Sample:`, sample.rows[0]);

    } catch (error: any) {
      console.log(`  ⚠️  Error: ${error.message}`);
    }
  }
}

async function investigateResearchPaperTables() {
  console.log('\n' + '='.repeat(80));
  console.log('📚 RESEARCH PAPERS TABLES (3 tables)');
  console.log('='.repeat(80));

  const paperTables = [
    'arxiv_ai_papers',
    'openalex_papers',
    'bdtd_theses'
  ];

  for (const table of paperTables) {
    try {
      console.log(`\n📄 ${table}:`);

      // Get schema
      const schema = await pool.query(`
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'sofia' AND table_name = $1
        ORDER BY ordinal_position;
      `, [table]);

      // Get stats
      const stats = await pool.query(`
        SELECT
          COUNT(*) as total_records,
          pg_size_pretty(pg_total_relation_size('sofia.${table}')) as table_size
        FROM sofia.${table};
      `);

      console.log(`  Records: ${stats.rows[0].total_records}`);
      console.log(`  Size: ${stats.rows[0].table_size}`);
      console.log(`  Columns: ${schema.rows.map(r => r.column_name).join(', ')}`);

      // Sample data
      const sample = await pool.query(`SELECT * FROM sofia.${table} LIMIT 1;`);
      console.log(`  Sample:`, sample.rows[0]);

    } catch (error: any) {
      console.log(`  ⚠️  Error: ${error.message}`);
    }
  }
}

async function investigateJobsTables() {
  console.log('\n' + '='.repeat(80));
  console.log('💼 JOBS TABLES');
  console.log('='.repeat(80));

  const jobsTables = [
    'jobs',
    'tech_jobs'
  ];

  for (const table of jobsTables) {
    try {
      console.log(`\n💼 ${table}:`);

      // Get schema
      const schema = await pool.query(`
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'sofia' AND table_name = $1
        ORDER BY ordinal_position;
      `, [table]);

      // Get stats
      const stats = await pool.query(`
        SELECT
          COUNT(*) as total_records,
          COUNT(DISTINCT source) as unique_sources,
          pg_size_pretty(pg_total_relation_size('sofia.${table}')) as table_size
        FROM sofia.${table};
      `);

      console.log(`  Records: ${stats.rows[0].total_records}`);
      console.log(`  Sources: ${stats.rows[0].unique_sources}`);
      console.log(`  Size: ${stats.rows[0].table_size}`);
      console.log(`  Columns (${schema.rows.length}): ${schema.rows.map(r => r.column_name).join(', ')}`);

      // Get sources
      const sources = await pool.query(`
        SELECT source, COUNT(*) as count
        FROM sofia.${table}
        GROUP BY source
        ORDER BY count DESC;
      `);
      console.log(`  Source breakdown:`);
      sources.rows.forEach(row => {
        console.log(`    - ${row.source}: ${row.count}`);
      });

      // Sample data
      const sample = await pool.query(`SELECT * FROM sofia.${table} LIMIT 1;`);
      console.log(`  Sample columns:`, Object.keys(sample.rows[0] || {}));

    } catch (error: any) {
      console.log(`  ⚠️  Error: ${error.message}`);
    }
  }

  // Check overlap
  try {
    console.log('\n🔍 Checking for duplicates between jobs and tech_jobs...');
    const overlap = await pool.query(`
      SELECT COUNT(*) as duplicate_count
      FROM sofia.jobs j
      INNER JOIN sofia.tech_jobs tj
        ON j.title = tj.title
        AND j.company = tj.company
        AND j.posted_date::date = tj.posted_date::date;
    `);
    console.log(`  Duplicate records: ${overlap.rows[0].duplicate_count}`);
  } catch (error: any) {
    console.log(`  ⚠️  Error checking overlap: ${error.message}`);
  }
}

async function main() {
  try {
    console.log('🔍 PHASE 2 CONSOLIDATION INVESTIGATION\n');

    await investigateGenderTables();
    await investigateResearchPaperTables();
    await investigateJobsTables();

    console.log('\n' + '='.repeat(80));
    console.log('✅ INVESTIGATION COMPLETE');
    console.log('='.repeat(80));

  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
