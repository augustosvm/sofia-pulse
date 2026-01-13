import pkg from 'pg';
const { Pool } = pkg;

const pool = new Pool({
  connectionString: 'postgresql://sofia:SofiaPulse2025Secure@DB@localhost:5432/sofia_db'
});

async function getCathoStats() {
  // Total Catho jobs
  const total = await pool.query(`
    SELECT COUNT(*) as total FROM sofia.jobs WHERE platform = 'catho'
  `);

  // By country
  const byCountry = await pool.query(`
    SELECT
      country,
      COUNT(*) as total,
      COUNT(DISTINCT city) as unique_cities,
      COUNT(skills_required) FILTER (WHERE skills_required IS NOT NULL AND array_length(skills_required, 1) > 0) as with_skills
    FROM sofia.jobs
    WHERE platform = 'catho'
    GROUP BY country
    ORDER BY total DESC
  `);

  // Top skills
  const topSkills = await pool.query(`
    SELECT
      unnest(skills_required) as skill,
      COUNT(*) as count
    FROM sofia.jobs
    WHERE platform = 'catho'
      AND skills_required IS NOT NULL
      AND array_length(skills_required, 1) > 0
    GROUP BY skill
    ORDER BY count DESC
    LIMIT 20
  `);

  // Seniority breakdown
  const seniority = await pool.query(`
    SELECT
      seniority_level,
      COUNT(*) as total
    FROM sofia.jobs
    WHERE platform = 'catho'
    GROUP BY seniority_level
    ORDER BY total DESC
  `);

  // Remote type
  const remoteType = await pool.query(`
    SELECT
      COALESCE(remote_type, 'unknown') as remote_type,
      COUNT(*) as total
    FROM sofia.jobs
    WHERE platform = 'catho'
    GROUP BY remote_type
    ORDER BY total DESC
  `);

  console.log('📊 CATHO JOBS ANALYSIS');
  console.log('======================\n');

  console.log(`Total Catho Jobs: ${total.rows[0].total}\n`);

  console.log('📍 By Country:');
  byCountry.rows.forEach(row => {
    console.log(`  ${row.country || 'Unknown'}: ${row.total} jobs, ${row.unique_cities} cities, ${row.with_skills} with skills`);
  });

  console.log('\n🔥 Top 20 Skills:');
  topSkills.rows.forEach((row, i) => {
    console.log(`  ${i+1}. ${row.skill}: ${row.count}x`);
  });

  console.log('\n🎓 Seniority Levels:');
  seniority.rows.forEach(row => {
    console.log(`  ${row.seniority_level || 'Unknown'}: ${row.total} jobs`);
  });

  console.log('\n🏠 Remote Type:');
  remoteType.rows.forEach(row => {
    console.log(`  ${row.remote_type}: ${row.total} jobs`);
  });

  await pool.end();
}

getCathoStats();
