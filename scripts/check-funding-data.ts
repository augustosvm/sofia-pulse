import pkg from 'pg';
const { Pool } = pkg;

const pool = new Pool({
  connectionString: 'postgresql://sofia:SofiaPulse2025Secure@DB@localhost:5432/sofia_db'
});

async function checkFunding() {
  console.log('📊 Checking Funding Rounds Data\n');

  // Total funding rounds
  const total = await pool.query('SELECT COUNT(*) FROM sofia.funding_rounds');
  console.log(`Total funding rounds: ${total.rows[0].count}`);

  // With amount_usd
  const withAmount = await pool.query('SELECT COUNT(*) FROM sofia.funding_rounds WHERE amount_usd > 0');
  console.log(`With amount_usd > 0: ${withAmount.rows[0].count}`);

  // Last 12 months
  const recent = await pool.query(`
    SELECT COUNT(*) FROM sofia.funding_rounds
    WHERE announced_date >= NOW() - INTERVAL '12 months'
  `);
  console.log(`Last 12 months: ${recent.rows[0].count}`);

  // Seed/Angel with amount
  const seedAngel = await pool.query(`
    SELECT COUNT(*) FROM sofia.funding_rounds
    WHERE amount_usd > 0
      AND amount_usd < 10000000
      AND announced_date >= NOW() - INTERVAL '12 months'
  `);
  console.log(`Seed/Angel (<$10M) last 12m: ${seedAngel.rows[0].count}`);

  // All with amount (any size)
  const allAmounts = await pool.query(`
    SELECT COUNT(*) FROM sofia.funding_rounds
    WHERE amount_usd > 0
      AND announced_date >= NOW() - INTERVAL '12 months'
  `);
  console.log(`All rounds with $ last 12m: ${allAmounts.rows[0].count}`);

  // Sample funding rounds
  const sample = await pool.query(`
    SELECT
      organization_name,
      amount_usd,
      round_type,
      announced_date,
      source
    FROM sofia.funding_rounds
    WHERE amount_usd > 0
    ORDER BY announced_date DESC
    LIMIT 10
  `);

  console.log('\n📋 Sample recent rounds with amounts:\n');
  sample.rows.forEach(r => {
    const date = r.announced_date ? r.announced_date.toISOString().split('T')[0] : 'N/A';
    const amount = r.amount_usd ? `$${(r.amount_usd / 1000000).toFixed(1)}M` : 'N/A';
    console.log(`  ${date} | ${r.organization_name?.padEnd(30)} | ${amount.padEnd(10)} | ${r.round_type || 'N/A'} | ${r.source}`);
  });

  // Check by source
  const bySource = await pool.query(`
    SELECT
      source,
      COUNT(*) as total,
      COUNT(CASE WHEN amount_usd > 0 THEN 1 END) as with_amount,
      COUNT(CASE WHEN announced_date >= NOW() - INTERVAL '12 months' THEN 1 END) as recent
    FROM sofia.funding_rounds
    GROUP BY source
    ORDER BY total DESC
  `);

  console.log('\n📊 By Source:\n');
  bySource.rows.forEach(r => {
    console.log(`  ${r.source?.padEnd(20)} | Total: ${r.total} | With $: ${r.with_amount} | Recent: ${r.recent}`);
  });

  await pool.end();
}

checkFunding();
