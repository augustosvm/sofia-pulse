
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
        console.log('✅ Connected');

        // List tables in sofia schema
        const res = await client.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'sofia'
      ORDER BY table_name;
    `);

        console.log('Tables found:', res.rows.length);
        for (const row of res.rows) {
            const tableName = row.table_name;
            try {
                const countRes = await client.query(`SELECT count(*) as c FROM sofia.${tableName}`);
                console.log(`- ${tableName} (Rows: ${countRes.rows[0].c})`);
            } catch (err) {
                console.log(`- ${tableName} (Error counting: ${err.message})`);
            }
        }

        // Check columns for organizations if it exists
        const orgs = res.rows.find(r => r.table_name === 'organizations');
        if (orgs) {
            console.log('\nColumns in organizations:');
            const cols = await client.query(`
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'sofia' AND table_name = 'organizations'
        `);
            cols.rows.forEach(c => console.log(`  - ${c.column_name} (${c.data_type})`));
        }

        // Check columns for funding_rounds if it exists
        const funds = res.rows.find(r => r.table_name === 'funding_rounds');
        if (funds) {
            console.log('\nColumns in funding_rounds:');
            const cols = await client.query(`
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'sofia' AND table_name = 'funding_rounds'
        `);
            cols.rows.forEach(c => console.log(`  - ${c.column_name} (${c.data_type})`));
        }

    } catch (err) {
        console.error('❌ Error:', err);
    } finally {
        client.end();
    }
}

run();
