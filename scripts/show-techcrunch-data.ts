import { Pool } from 'pg';

const pool = new Pool({
  connectionString: 'postgresql://sofia:SofiaPulse2025Secure@DB@localhost:5432/sofia_db'
});

async function main() {
  const result = await pool.query(`
    SELECT company_name, round_type, amount_usd, announced_date
    FROM sofia.funding_rounds
    WHERE source = 'techcrunch' AND amount_usd > 0
    ORDER BY amount_usd ASC
  `);

  console.log('📰 TechCrunch Funding Rounds:\n');
  console.log('Company'.padEnd(25) + 'Round'.padEnd(15) + 'Amount'.padStart(12) + '  Seed?');
  console.log('-'.repeat(70));

  for (const row of result.rows) {
    const company = row.company_name.substring(0, 24).padEnd(25);
    const round = row.round_type.substring(0, 14).padEnd(15);
    const amount = `$${(row.amount_usd / 1_000_000).toFixed(1)}M`.padStart(12);
    const isSeed = row.amount_usd < 10_000_000 ? '🌱 SEED/ANGEL' : '';
    console.log(company + round + amount + '  ' + isSeed);
  }

  const seedCount = result.rows.filter((r: any) => r.amount_usd < 10_000_000).length;
  const totalWithAmount = result.rows.length;

  console.log('\n' + '='.repeat(70));
  console.log(`Total TechCrunch rounds with amounts: ${totalWithAmount}`);
  console.log(`🌱 Seed/Angel rounds (<$10M): ${seedCount}`);
  console.log('='.repeat(70));

  await pool.end();
}

main();
