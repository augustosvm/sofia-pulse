const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
    host: process.env.POSTGRES_HOST,
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER,
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB,
});

(async () => {
    try {
        console.log('🔍 Verifying Data Integrity...');

        // 1. Check Patents inserted RECENTLY (Top 10 by updated_at)
        console.log('\n📅 Recent Patents (Top 10 most recent):');
        const patents = await pool.query(`
            SELECT id, source, patent_number, title, updated_at, collected_at
            FROM sofia.patents
            ORDER BY updated_at DESC NULLS LAST, collected_at DESC NULLS LAST
            LIMIT 10;
        `);
        console.table(patents.rows);

        if (patents.rows.length > 0) {
            const sampleId = patents.rows[0].id;
            console.log(`\n🔗 Checking Links for Patent ID: ${sampleId}`);

            // 2. Check Organizations (Applicants)
            const orgs = await pool.query(`
                SELECT o.name, o.organization_id, pa.is_assignee 
                FROM sofia.patent_applicants pa
                JOIN sofia.organizations o ON pa.organization_id = o.id
                WHERE pa.patent_id = $1
             `, [sampleId]);
            console.log('   🏢 Organizations:');
            if (orgs.rows.length === 0) console.log('      (None)');
            else console.table(orgs.rows);

            // 3. Check Persons (Inventors)
            const persons = await pool.query(`
                SELECT p.full_name, pi.inventor_order, pi.is_primary 
                FROM sofia.patent_inventors pi
                JOIN sofia.persons p ON pi.person_id = p.id
                WHERE pi.patent_id = $1
                ORDER BY pi.inventor_order
             `, [sampleId]);
            console.log('   🧑‍🔬 Inventors:');
            if (persons.rows.length === 0) console.log('      (None)');
            else console.table(persons.rows);
        } else {
            console.log('❌ No patents found updated today!');
        }

    } catch (err) {
        console.error('❌ Error:', err.message);
    } finally {
        await pool.end();
    }
})();
