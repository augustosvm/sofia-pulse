import { Pool } from 'pg';

const pool = new Pool({
  connectionString: 'postgresql://sofia:SofiaPulse2025Secure@DB@localhost:5432/sofia_db'
});

async function main() {
  console.log('🗑️  Cleaning problematic TechCrunch records...\n');

  // Delete TechCrunch records that look like errors
  const result = await pool.query(`
    DELETE FROM sofia.funding_rounds
    WHERE source = 'techcrunch'
      AND (
        amount_usd > 5000000000  -- >$5B (unrealistic)
        OR amount_usd < 100000    -- <$100K (unrealistic)
        OR company_name IN ('Tech', 'Meta', 'Big', 'Startup')  -- Generic names
      )
    RETURNING company_name, amount_usd
  `);

  console.log(`Deleted ${result.rows.length} problematic records:\n`);
  result.rows.forEach(r => {
    console.log(`  ❌ ${r.company_name}: $${(r.amount_usd / 1_000_000).toFixed(1)}M`);
  });

  console.log(`\n✅ Cleanup complete!`);
  await pool.end();
}

main();
