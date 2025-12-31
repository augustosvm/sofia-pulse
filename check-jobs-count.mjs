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

// Total stats
const result = await pool.query(`
  SELECT
    COUNT(*) as total,
    COUNT(DISTINCT source) as sources,
    COUNT(DISTINCT platform) as platforms,
    COUNT(DISTINCT country_id) as countries,
    COUNT(DISTINCT state_id) as states,
    COUNT(DISTINCT city_id) as cities
  FROM sofia.jobs
`);

console.log('📊 JOBS DATABASE STATS:');
console.log(`   Total jobs: ${result.rows[0].total}`);
console.log(`   Sources: ${result.rows[0].sources}`);
console.log(`   Platforms: ${result.rows[0].platforms}`);
console.log(`   Countries (by ID): ${result.rows[0].countries}`);
console.log(`   States (by ID): ${result.rows[0].states}`);
console.log(`   Cities (by ID): ${result.rows[0].cities}`);

// Top countries
const countries = await pool.query(`
  SELECT c.common_name, COUNT(*) as count
  FROM sofia.jobs j
  LEFT JOIN sofia.countries c ON j.country_id = c.id
  WHERE j.country_id IS NOT NULL
  GROUP BY c.common_name
  ORDER BY count DESC
  LIMIT 10
`);

console.log('\n🌍 Top Countries:');
countries.rows.forEach(r => {
  console.log(`   - ${r.common_name}: ${r.count} jobs`);
});

// Top sources
const sources = await pool.query(`
  SELECT source, COUNT(*) as count
  FROM sofia.jobs
  WHERE source IS NOT NULL AND source != 'unknown'
  GROUP BY source
  ORDER BY count DESC
  LIMIT 10
`);

console.log('\n📍 Top Sources:');
sources.rows.forEach(r => {
  console.log(`   - ${r.source}: ${r.count} jobs`);
});

// Skills stats
const skills = await pool.query(`
  SELECT COUNT(*) FILTER (WHERE skills IS NOT NULL) as with_skills,
         COUNT(*) FILTER (WHERE skills IS NULL) as without_skills
  FROM sofia.jobs
`);

console.log('\n🛠️ Skills Coverage:');
console.log(`   With skills: ${skills.rows[0].with_skills} (${(skills.rows[0].with_skills / result.rows[0].total * 100).toFixed(1)}%)`);
console.log(`   Without skills: ${skills.rows[0].without_skills} (${(skills.rows[0].without_skills / result.rows[0].total * 100).toFixed(1)}%)`);

await pool.end();
