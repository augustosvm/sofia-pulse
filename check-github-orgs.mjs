import pg from 'pg';
const { Pool } = pg;

const pool = new Pool({
  host: '91.98.158.19',
  port: 5432,
  user: 'sofia',
  password: 'sofia123strong',
  database: 'sofia_db'
});

const result = await pool.query(`
  SELECT 
    COUNT(*) as total,
    COUNT(organization_id) as with_org
  FROM sofia.jobs 
  WHERE platform = 'github'
`);

console.log(`GitHub: ${result.rows[0].with_org}/${result.rows[0].total} jobs com organization`);
await pool.end();
