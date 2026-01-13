import pkg from 'pg';
const { Pool } = pkg;

// Database connection
const pool = new Pool({
  host: 'localhost',
  port: 5432,
  database: 'sofia_db',
  user: 'sofia',
  password: 'SofiaPulse2025Secure@DB',
});

// All 27 Brazilian states
const brazilianStates = [
  { name: 'Acre', code: 'AC' },
  { name: 'Alagoas', code: 'AL' },
  { name: 'Amapá', code: 'AP' },
  { name: 'Amazonas', code: 'AM' },
  { name: 'Bahia', code: 'BA' },
  { name: 'Ceará', code: 'CE' },
  { name: 'Distrito Federal', code: 'DF' },
  { name: 'Espírito Santo', code: 'ES' },
  { name: 'Goiás', code: 'GO' },
  { name: 'Maranhão', code: 'MA' },
  { name: 'Mato Grosso', code: 'MT' },
  { name: 'Mato Grosso do Sul', code: 'MS' },
  { name: 'Minas Gerais', code: 'MG' },
  { name: 'Pará', code: 'PA' },
  { name: 'Paraíba', code: 'PB' },
  { name: 'Paraná', code: 'PR' },
  { name: 'Pernambuco', code: 'PE' },
  { name: 'Piauí', code: 'PI' },
  { name: 'Rio de Janeiro', code: 'RJ' },
  { name: 'Rio Grande do Norte', code: 'RN' },
  { name: 'Rio Grande do Sul', code: 'RS' },
  { name: 'Rondônia', code: 'RO' },
  { name: 'Roraima', code: 'RR' },
  { name: 'Santa Catarina', code: 'SC' },
  { name: 'São Paulo', code: 'SP' },
  { name: 'Sergipe', code: 'SE' },
  { name: 'Tocantins', code: 'TO' },
];

async function addMissingStates() {
  const client = await pool.connect();

  try {
    console.log('🗺️  Adding Missing Brazilian States');
    console.log('====================================\n');

    const countryId = 1; // Brazil
    let added = 0;
    let skipped = 0;

    for (const state of brazilianStates) {
      try {
        // Check if state exists
        const checkResult = await client.query(
          'SELECT id FROM sofia.states WHERE code = $1 AND country_id = $2',
          [state.code, countryId]
        );

        if (checkResult.rows.length > 0) {
          console.log(`⏭️  Skipped: ${state.name} (${state.code}) - already exists`);
          skipped++;
          continue;
        }

        // Insert state
        await client.query(
          `INSERT INTO sofia.states (name, code, country_id, created_at)
           VALUES ($1, $2, $3, NOW())`,
          [state.name, state.code, countryId]
        );

        console.log(`✅ Added: ${state.name} (${state.code})`);
        added++;

      } catch (error: any) {
        console.error(`❌ Error adding ${state.name}: ${error.message}`);
      }
    }

    console.log('\n====================================');
    console.log(`✅ Added: ${added} states`);
    console.log(`⏭️  Skipped: ${skipped} states`);
    console.log(`📊 Total: ${brazilianStates.length} states`);

  } catch (error) {
    console.error('Error:', error);
  } finally {
    client.release();
    await pool.end();
  }
}

addMissingStates();
