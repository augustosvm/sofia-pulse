/**
 * Database Consolidation Script
 *
 * Phase 1 Quick Wins:
 * 1. Drop hacker_news_stories (empty duplicate)
 * 2. Investigate women_eurostat_data size
 * 3. Check if embeddings are used
 */

import pkg from 'pg';
const { Pool } = pkg;

const pool = new Pool({
  host: process.env.DB_HOST || '91.98.158.19',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'sofia_db',
  user: process.env.DB_USER || 'sofia',
  password: process.env.DB_PASSWORD || 'sofia123strong',
});

async function main() {
  console.log('🗑️  Phase 1 - Database Consolidation\n');

  try {
    // 1. Drop hacker_news_stories (empty duplicate)
    console.log('1️⃣  Dropping hacker_news_stories (empty duplicate)...');
    await pool.query('DROP TABLE IF EXISTS sofia.hacker_news_stories CASCADE;');
    console.log('✅ Dropped hacker_news_stories\n');

    // 2. Investigate women_eurostat_data
    console.log('2️⃣  Investigating women_eurostat_data (1.2GB)...');
    const eurostatStats = await pool.query(`
      SELECT
        COUNT(*) as total_records,
        COUNT(DISTINCT country_code) as unique_countries,
        COUNT(DISTINCT dataset_code) as unique_datasets,
        MIN(year::int) as earliest_year,
        MAX(year::int) as latest_year,
        MIN(collected_at) as first_collection,
        MAX(collected_at) as last_collection
      FROM sofia.women_eurostat_data
      WHERE year ~ '^[0-9]+$';
    `);
    console.log('📊 women_eurostat_data stats:');
    console.log(eurostatStats.rows[0]);

    // Sample data
    const eurostatSample = await pool.query(`
      SELECT dataset_code, dataset_name, country_code, year, sex, age_group, value, unit
      FROM sofia.women_eurostat_data
      LIMIT 5;
    `);
    console.log('\n📝 Sample data:');
    console.table(eurostatSample.rows);

    // 3. Check embeddings usage
    console.log('\n3️⃣  Checking embeddings tables...');

    const embeddingTables = [
      'github_embeddings',
      'hackernews_embeddings',
      'pypi_embeddings',
      'npm_embeddings',
      'paper_embeddings',
      'author_embeddings',
      'reddit_embeddings',
      'university_embeddings'
    ];

    console.log('\n📊 Embeddings Table Statistics:\n');
    let totalEmbeddingsRecords = 0;

    for (const table of embeddingTables) {
      try {
        const stats = await pool.query(`
          SELECT
            COUNT(*) as total_records,
            MIN(created_at) as first_created,
            MAX(created_at) as last_created,
            pg_size_pretty(pg_total_relation_size('sofia.${table}')) as table_size
          FROM sofia.${table};
        `);
        const row = stats.rows[0];
        totalEmbeddingsRecords += parseInt(row.total_records);
        console.log(`${table}:`);
        console.log(`  Records: ${row.total_records}`);
        console.log(`  Size: ${row.table_size}`);
        console.log(`  First: ${row.first_created}`);
        console.log(`  Last: ${row.last_created}\n`);
      } catch (error: any) {
        console.log(`  ⚠️  Table ${table} error: ${error.message}\n`);
      }
    }

    console.log(`\n📈 Total Embeddings Records: ${totalEmbeddingsRecords}`);
    console.log(`\n✅ Phase 1 investigation complete!`);

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('📋 CONSOLIDATION SUMMARY');
    console.log('='.repeat(60));
    console.log('✅ hacker_news_stories: DROPPED');
    console.log(`📊 women_eurostat_data: ${eurostatStats.rows[0].total_records} records`);
    console.log(`🧠 Embeddings: ${totalEmbeddingsRecords} total records across 8 tables`);
    console.log('='.repeat(60));

  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
