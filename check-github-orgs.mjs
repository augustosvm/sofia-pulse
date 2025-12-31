import pg from 'pg';
import dotenv from 'dotenv';
const { Pool } = pg;

dotenv.config();

const pool = new Pool({
  host: process.env.POSTGRES_HOST || '91.98.158.19',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD || 'sofia123strong',
  database: process.env.POSTGRES_DB || 'sofia_db'
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
