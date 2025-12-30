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
  const result = await pool.query(`
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'sofia'
    AND table_name = 'women_eurostat_data'
    ORDER BY ordinal_position;
  `);

  console.log('\n📋 women_eurostat_data Schema:\n');
  console.table(result.rows);

  // Also get a sample row
  const sample = await pool.query('SELECT * FROM sofia.women_eurostat_data LIMIT 1;');
  console.log('\n📝 Sample Row:\n');
  console.log(sample.rows[0]);

  await pool.end();
}

main();
