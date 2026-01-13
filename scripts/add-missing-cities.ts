import pkg from 'pg';
const { Pool } = pkg;
import { getStateId, getCityId } from './shared/geo-id-helpers.js';

// Database connection
const pool = new Pool({
  host: 'localhost',
  port: 5432,
  database: 'sofia_db',
  user: 'sofia',
  password: 'SofiaPulse2025Secure@DB',
});

// Missing cities from Catho collection warnings
const missingCities = [
  { name: 'Goiânia', state: 'GO', country_id: 1 }, // Brazil
  { name: 'Itajaí', state: 'SC', country_id: 1 },
  { name: 'Novo Hamburgo', state: 'RS', country_id: 1 },
  { name: 'Aracruz', state: 'ES', country_id: 1 },
  { name: 'Laranjeiras', state: 'SE', country_id: 1 },
  { name: 'Pomerode', state: 'SC', country_id: 1 },
  { name: 'Palhoça', state: 'SC', country_id: 1 },
  { name: 'Colombo', state: 'PR', country_id: 1 },
  { name: 'Criciúma', state: 'SC', country_id: 1 },
  { name: 'Guaratinguetá', state: 'SP', country_id: 1 },
  { name: 'Saquarema', state: 'RJ', country_id: 1 },
  { name: 'Paulínia', state: 'SP', country_id: 1 },
  { name: 'Brasópolis', state: 'MG', country_id: 1 },
  { name: 'Cachoeirinha', state: 'RS', country_id: 1 },
  { name: 'Araguari', state: 'MG', country_id: 1 },
  { name: 'Tupã', state: 'SP', country_id: 1 },
  { name: 'Foz do Iguaçu', state: 'PR', country_id: 1 },
  { name: 'Macaé', state: 'RJ', country_id: 1 },
  { name: 'Catu', state: 'BA', country_id: 1 },
  { name: 'Cuiabá', state: 'MT', country_id: 1 },
  { name: 'Itapevi', state: 'SP', country_id: 1 },
  { name: 'Balneário Piçarras', state: 'SC', country_id: 1 },
  { name: 'Barras', state: 'PI', country_id: 1 },
  { name: 'Codó', state: 'MA', country_id: 1 },
  { name: 'Toledo', state: 'PR', country_id: 1 },
  { name: 'Eusébio', state: 'CE', country_id: 1 },
  { name: 'Erechim', state: 'RS', country_id: 1 },
  { name: 'Santa Maria', state: 'RS', country_id: 1 },
  { name: 'São Borja', state: 'RS', country_id: 1 },
  { name: 'Jaú', state: 'SP', country_id: 1 },
  { name: 'Rio Pardo', state: 'RS', country_id: 1 },
  { name: 'Cáceres', state: 'MT', country_id: 1 },
  { name: 'Gramado', state: 'RS', country_id: 1 },
  { name: 'Campos dos Goytacazes', state: 'RJ', country_id: 1 },
  { name: 'Cubatão', state: 'SP', country_id: 1 },
  { name: 'Parauapebas', state: 'PA', country_id: 1 }, // Carajás
  { name: 'Carapicuíba', state: 'SP', country_id: 1 },
  { name: 'Jacutinga', state: 'MG', country_id: 1 },
  { name: 'Pirassununga', state: 'SP', country_id: 1 },
  { name: 'Santa Rita do Sapucaí', state: 'MG', country_id: 1 },
  { name: 'Torres', state: 'RS', country_id: 1 },
  { name: 'Niterói', state: 'RJ', country_id: 1 },
  { name: 'Birigui', state: 'SP', country_id: 1 },
  { name: 'São Vicente', state: 'SP', country_id: 1 },
  { name: 'Vitória', state: 'ES', country_id: 1 },
  { name: 'Santa Isabel', state: 'SP', country_id: 1 },
  { name: 'Santana de Parnaíba', state: 'SP', country_id: 1 },
  { name: 'Boa Vista', state: 'RR', country_id: 1 },
];

async function addMissingCities() {
  const client = await pool.connect();

  try {
    console.log('🏙️  Adding Missing Cities to Database');
    console.log('=====================================\n');

    let added = 0;
    let skipped = 0;
    let errors = 0;

    for (const city of missingCities) {
      try {
        // Get state_id from state code
        const state_id = await getStateId(pool, city.state, city.country_id);

        if (!state_id) {
          console.log(`⚠️  Warning: State "${city.state}" not found for ${city.name}`);
          errors++;
          continue;
        }

        // Check if city already exists
        const existing = await getCityId(pool, city.name, city.state, city.country_id);

        if (existing) {
          console.log(`⏭️  Skipped: ${city.name}, ${city.state} (already exists)`);
          skipped++;
          continue;
        }

        // Insert city
        await client.query(
          `INSERT INTO sofia.cities (name, state_id, country_id, created_at)
           VALUES ($1, $2, $3, NOW())
           ON CONFLICT (name, state_id, country_id) DO NOTHING`,
          [city.name, state_id, city.country_id]
        );

        console.log(`✅ Added: ${city.name}, ${city.state}`);
        added++;

      } catch (error: any) {
        console.error(`❌ Error adding ${city.name}: ${error.message}`);
        errors++;
      }
    }

    console.log('\n=====================================');
    console.log(`✅ Added: ${added} cities`);
    console.log(`⏭️  Skipped: ${skipped} cities (already exist)`);
    console.log(`❌ Errors: ${errors} cities`);
    console.log(`📊 Total processed: ${missingCities.length} cities`);

  } catch (error) {
    console.error('Error:', error);
  } finally {
    client.release();
    await pool.end();
  }
}

addMissingCities();
