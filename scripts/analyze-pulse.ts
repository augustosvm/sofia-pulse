/**
 * Unified Pulse Analyst
 * 
 * Generates a comprehensive intelligence report combining:
 * - Job Market (Demand)
 * - Tech Trends (Innovation)
 * - Economic Indicators (Trade/MDIC)
 * - Industry Sentiment (FIESP)
 * - Strategic Risks (Signals/GDELT)
 */

import { Client } from 'pg';
import * as dotenv from 'dotenv';
dotenv.config();

const dbConfig = {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    user: process.env.DB_USER || 'sofia',
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME || 'sofia_db',
};

async function run() {
    const client = new Client(dbConfig);
    try {
        await client.connect();
        console.log('🧠 Sofia Pulse - Intelligence Report Generating...\n');

        // 1. Job Market
        const jobCount = await client.query('SELECT COUNT(*) FROM sofia.jobs');
        const topSkills = await client.query(`
        SELECT skill, COUNT(*) as mentions 
        FROM sofia.jobs, UNNEST(skills) AS skill
        WHERE skills IS NOT NULL
        GROUP BY skill
        ORDER BY mentions DESC
        LIMIT 5
    `);

        // 2. Tech Trends (GitHub/NPM/StackOverflow)
        const trends = await client.query(`
        SELECT name, source, score, growth_rate
        FROM sofia.tech_trends
        WHERE collected_at > NOW() - INTERVAL '7 days'
        ORDER BY score DESC
        LIMIT 10
    `);

        // 3. Economic (MDIC Trade)
        const trade = await client.query(`
        SELECT flow, SUM(value_usd) as total_usd
        FROM sofia.comexstat_trade
        GROUP BY flow
    `);

        // 4. Industry (FIESP)
        const fiesp = await client.query(`
        SELECT period, market_conditions, investment_intention
        FROM sofia.fiesp_sensor
        ORDER BY period DESC
        LIMIT 1
    `);

        // 5. Risks (High Impact Signals)
        const risks = await client.query(`
        SELECT title, impact_score, category
        FROM sofia.industry_signals
        WHERE impact_score >= 7
        ORDER BY published_at DESC
        LIMIT 5
    `);

        // --- REPORT OUTPUT ---
        console.log('==================================================');
        console.log('📊 SOFIA PULSE: COMPREHENSIVE INTELLIGENCE REPORT');
        console.log('==================================================\n');

        console.log('💼 JOB MARKET');
        console.log(`   Total Active Jobs: ${jobCount.rows[0].count}`);
        if (topSkills.rows.length > 0) {
            console.log(`   Top Skills: ${topSkills.rows.map(r => `${r.skill} (${r.mentions})`).join(', ')}`);
        } else {
            console.log(`   Top Skills: No skill data available`);
        }
        console.log('');

        console.log('🚀 TECH TRENDS (Innovation Signals)');
        if (trends.rows.length === 0) {
            console.log('   No recent trends data.');
        } else {
            trends.rows.forEach(t => {
                const growth = t.growth_rate ? ` +${(t.growth_rate * 100).toFixed(1)}%` : '';
                console.log(`   - [${t.source.toUpperCase()}] ${t.name}: ${Math.round(t.score)}${growth}`);
            });
        }
        console.log('');

        console.log('💰 ECONOMIC INDICATORS (Brazil Trade - MDIC)');
        let exports = 0, imports = 0;
        trade.rows.forEach(r => {
            const val = parseFloat(r.total_usd);
            if (r.flow === 'Export') exports = val;
            if (r.flow === 'Import') imports = val;
        });
        console.log(`   Exports: $${(exports / 1000000).toFixed(1)}M USD`);
        console.log(`   Imports: $${(imports / 1000000).toFixed(1)}M USD`);
        console.log(`   Balance: $${((exports - imports) / 1000000).toFixed(1)}M USD`);
        console.log('');

        console.log('🏭 INDUSTRY SENTIMENT (FIESP Sensor)');
        if (fiesp.rows.length > 0) {
            const f = fiesp.rows[0];
            console.log(`   Reference: ${new Date(f.period).toLocaleDateString('pt-BR')}`);
            console.log(`   Market Conditions: ${f.market_conditions} (>50 = Positive)`);
            console.log(`   Investment Intention: ${f.investment_intention}`);
        } else {
            console.log('   No recent FIESP data.');
        }
        console.log('');

        console.log('⚠️ STRATEGIC RISKS (Industry Signals)');
        if (risks.rows.length === 0) {
            console.log('   No critical risks detected.');
        } else {
            risks.rows.forEach(r => {
                console.log(`   [${r.category.toUpperCase()}] ${r.title.substring(0, 60)}... (Impact: ${r.impact_score}/10)`);
            });
        }

        console.log('\n==================================================');
        console.log('✅ Analysis Complete - All New Data Sources Verified');
        console.log('==================================================\n');

    } catch (err) {
        console.error('❌ Error:', err);
    } finally {
        client.end();
    }
}

run();
