import pkg from 'pg';
const { Pool } = pkg;

const pool = new Pool({
  host: '91.98.158.19',
  port: 5432,
  database: 'sofia_db',
  user: 'sofia',
  password: 'sofia123strong',
});

async function main() {
  try {
    console.log('🔍 Investigating tech_jobs table...\n');

    // Get schema
    const schema = await pool.query(`
      SELECT column_name, data_type
      FROM information_schema.columns
      WHERE table_schema = 'sofia' AND table_name = 'tech_jobs'
      ORDER BY ordinal_position;
    `);

    console.log('📋 Schema:');
    console.table(schema.rows);

    // Get stats
    const stats = await pool.query(`
      SELECT
        COUNT(*) as total_records,
        COUNT(DISTINCT title) as unique_titles,
        COUNT(DISTINCT company) as unique_companies,
        MIN(posted_date) as earliest_post,
        MAX(posted_date) as latest_post,
        pg_size_pretty(pg_total_relation_size('sofia.tech_jobs')) as table_size
      FROM sofia.tech_jobs;
    `);

    console.log('\n📊 Statistics:');
    console.log(stats.rows[0]);

    // Sample data
    const sample = await pool.query(`SELECT * FROM sofia.tech_jobs LIMIT 3;`);
    console.log('\n📝 Sample Data:');
    console.table(sample.rows);

    // Check if there's any column that could be "source"
    const possibleSources = await pool.query(`
      SELECT
        platform,
        COUNT(*) as count
      FROM sofia.tech_jobs
      GROUP BY platform
      ORDER BY count DESC;
    `);

    console.log('\n🔍 Platform breakdown (could be "source"):');
    console.table(possibleSources.rows);

    // Check overlap with jobs table
    console.log('\n🔄 Checking overlap with jobs table...');
    const overlap = await pool.query(`
      SELECT COUNT(*) as duplicate_count
      FROM sofia.jobs j
      INNER JOIN sofia.tech_jobs tj
        ON LOWER(TRIM(j.title)) = LOWER(TRIM(tj.title))
        AND LOWER(TRIM(j.company)) = LOWER(TRIM(tj.company))
        AND DATE(j.posted_date) = DATE(tj.posted_date);
    `);
    console.log(`Duplicate records: ${overlap.rows[0].duplicate_count}`);

    // Check records only in tech_jobs
    const uniqueInTechJobs = await pool.query(`
      SELECT COUNT(*) as unique_in_tech_jobs
      FROM sofia.tech_jobs tj
      WHERE NOT EXISTS (
        SELECT 1 FROM sofia.jobs j
        WHERE LOWER(TRIM(j.title)) = LOWER(TRIM(tj.title))
        AND LOWER(TRIM(j.company)) = LOWER(TRIM(tj.company))
        AND DATE(j.posted_date) = DATE(tj.posted_date)
      );
    `);
    console.log(`Records ONLY in tech_jobs: ${uniqueInTechJobs.rows[0].unique_in_tech_jobs}`);

    // Check records only in jobs
    const uniqueInJobs = await pool.query(`
      SELECT COUNT(*) as unique_in_jobs
      FROM sofia.jobs j
      WHERE NOT EXISTS (
        SELECT 1 FROM sofia.tech_jobs tj
        WHERE LOWER(TRIM(tj.title)) = LOWER(TRIM(j.title))
        AND LOWER(TRIM(tj.company)) = LOWER(TRIM(j.company))
        AND DATE(tj.posted_date) = DATE(j.posted_date)
      );
    `);
    console.log(`Records ONLY in jobs: ${uniqueInJobs.rows[0].unique_in_jobs}`);

  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
