import pkg from 'pg';
const { Client } = pkg;

async function checkFunding() {
  const client = new Client({
    host: process.env.POSTGRES_HOST || 'localhost',
    port: Number.parseInt(process.env.POSTGRES_PORT || '5432'),
    database: process.env.POSTGRES_DB || 'sofia_db',
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD || 'sofia123strong'
  });

  try {
    await client.connect();
    console.log('✅ Connected to database');

    // Total funding rounds
    const totalResult = await client.query('SELECT COUNT(*) as total FROM sofia.funding_rounds');
    console.log(`\n📊 Total Funding Rounds: ${totalResult.rows[0].total}`);

    // Funding rounds nos últimos 30 dias
    const recent30 = await client.query(`
      SELECT COUNT(*) as count
      FROM sofia.funding_rounds
      WHERE announced_date >= NOW() - INTERVAL '30 days'
    `);
    console.log(`📅 Last 30 days: ${recent30.rows[0].count}`);

    // Funding rounds nos últimos 90 dias
    const recent90 = await client.query(`
      SELECT COUNT(*) as count
      FROM sofia.funding_rounds
      WHERE announced_date >= NOW() - INTERVAL '90 days'
    `);
    console.log(`📅 Last 90 days: ${recent90.rows[0].count}`);

    // Funding rounds nos últimos 180 dias
    const recent180 = await client.query(`
      SELECT COUNT(*) as count
      FROM sofia.funding_rounds
      WHERE announced_date >= NOW() - INTERVAL '180 days'
    `);
    console.log(`📅 Last 180 days: ${recent180.rows[0].count}`);

    // Por tipo de funding
    const byStage = await client.query(`
      SELECT funding_stage, COUNT(*) as count
      FROM sofia.funding_rounds
      GROUP BY funding_stage
      ORDER BY count DESC
    `);
    console.log('\n💰 By Stage:');
    byStage.rows.forEach(row => {
      console.log(`  - ${row.funding_stage || 'Unknown'}: ${row.count}`);
    });

    // Top 5 companies
    const topCompanies = await client.query(`
      SELECT company_name, COUNT(*) as rounds, SUM(amount_usd) as total_raised
      FROM sofia.funding_rounds
      WHERE company_name IS NOT NULL
      GROUP BY company_name
      ORDER BY total_raised DESC NULLS LAST
      LIMIT 5
    `);
    console.log('\n🏆 Top 5 Companies by Total Raised:');
    topCompanies.rows.forEach((row, i) => {
      const amount = row.total_raised ? `$${(row.total_raised / 1000000).toFixed(1)}M` : 'N/A';
      console.log(`  ${i + 1}. ${row.company_name}: ${row.rounds} rounds, ${amount}`);
    });

  } catch (error: any) {
    console.error('❌ Error:', error.message);
  } finally {
    await client.end();
  }
}

checkFunding();
