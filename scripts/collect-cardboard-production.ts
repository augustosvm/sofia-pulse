// Fix for Node.js 18 + undici - MUST BE FIRST!
// @ts-ignore
if (typeof File === 'undefined') {
  // @ts-ignore
  globalThis.File = class File extends Blob {
    constructor(bits: any[], name: string, options?: any) {
      super(bits, options);
    }
  };
}

#!/usr/bin/env tsx

/**
 * Sofia Pulse - Cardboard Production Collector (Leading Economic Indicator)
 *
 * Coleta dados de produção de papelão ondulado de múltiplas fontes globais.
 *
 * POR QUE PAPELÃO É IMPORTANTE:
 * - Leading indicator (antecede PIB em 2-3 meses)
 * - E-commerce = papelão para embalagens
 * - Manufatura = caixas de papelão
 * - Dados disponíveis ANTES do PIB oficial
 *
 * FONTES:
 * - USA: American Forest & Paper Association (AF&PA)
 * - Europe: FEFCO (European Federation of Corrugated Board)
 * - China: China Paper Association
 * - Brazil: ABPO (Associação Brasileira do Papelão Ondulado)
 */

import { Client } from 'pg';
import * as dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

// ============================================================================
// DATABASE SETUP
// ============================================================================

const dbConfig = {
  host: process.env.POSTGRES_HOST || process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || process.env.DB_PORT || '5432'),
  user: process.env.POSTGRES_USER || process.env.DB_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || process.env.DB_PASSWORD || 'postgres',
  database: process.env.POSTGRES_DB || process.env.DB_NAME || 'sofia_db',
};

// ============================================================================
// TYPES
// ============================================================================

interface CardboardData {
  country: string;
  region?: string; // Optional: state/province
  period: string; // YYYY-MM format
  production_tons: number;
  yoy_change_pct: number;
  source: string;
  notes?: string;
}

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

async function createTableIfNotExists(client: Client): Promise<void> {
  const createTableQuery = `
    CREATE TABLE IF NOT EXISTS cardboard_production (
      id SERIAL PRIMARY KEY,
      country VARCHAR(100) NOT NULL,
      region VARCHAR(100), -- Estado/província (optional)
      period VARCHAR(7) NOT NULL, -- YYYY-MM
      production_tons BIGINT NOT NULL,
      yoy_change_pct DECIMAL(6,2),
      source VARCHAR(100) NOT NULL,
      notes TEXT,
      collected_at TIMESTAMP DEFAULT NOW(),
      UNIQUE(country, region, period, source)
    );

    -- Indexes para queries rápidas
    CREATE INDEX IF NOT EXISTS idx_cardboard_country_period
      ON cardboard_production(country, period DESC);

    CREATE INDEX IF NOT EXISTS idx_cardboard_source
      ON cardboard_production(source);

    CREATE INDEX IF NOT EXISTS idx_cardboard_collected_at
      ON cardboard_production(collected_at DESC);
  `;

  await client.query(createTableQuery);
  console.log('✅ Table cardboard_production ready');
}

async function insertCardboardData(
  client: Client,
  data: CardboardData
): Promise<void> {
  const insertQuery = `
    INSERT INTO cardboard_production (
      country, region, period, production_tons,
      yoy_change_pct, source, notes
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    ON CONFLICT (country, region, period, source)
    DO UPDATE SET
      production_tons = EXCLUDED.production_tons,
      yoy_change_pct = EXCLUDED.yoy_change_pct,
      notes = EXCLUDED.notes,
      collected_at = NOW();
  `;

  await client.query(insertQuery, [
    data.country,
    data.region || null,
    data.period,
    data.production_tons,
    data.yoy_change_pct,
    data.source,
    data.notes || null,
  ]);
}

// ============================================================================
// COLLECTORS - Real Data Sources
// ============================================================================

/**
 * USA - American Forest & Paper Association (AF&PA)
 *
 * Source: https://www.afandpa.org/statistics-resources
 * Data: Monthly containerboard production
 * Access: Public reports (would need web scraping in production)
 *
 * NOTE: This is mock data for demonstration.
 * Real implementation would scrape AF&PA monthly reports.
 */
async function collectUSA(): Promise<CardboardData[]> {
  console.log('📦 Collecting USA cardboard data (AF&PA)...');

  // Mock data - Em produção, isso seria scraping dos reports da AF&PA
  // Exemplo: https://www.afandpa.org/statistics-resources/monthly-reports

  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth() + 1;

  const mockData: CardboardData[] = [];

  // Últimos 6 meses de dados
  for (let i = 0; i < 6; i++) {
    let month = currentMonth - i;
    let year = currentYear;

    if (month <= 0) {
      month += 12;
      year -= 1;
    }

    const period = `${year}-${String(month).padStart(2, '0')}`;

    // Produção realista: USA produz ~30-35M tons/ano = ~2.5-3M tons/mês
    // Com sazonalidade: pico em Q4 (holiday season)
    const baseProduction = 2800000; // 2.8M tons
    const seasonality = Math.sin((month / 12) * Math.PI * 2) * 200000; // ±200k variação
    const trend = -i * 50000; // Leve queda nos meses mais antigos

    mockData.push({
      country: 'USA',
      period,
      production_tons: Math.round(baseProduction + seasonality + trend),
      yoy_change_pct: 2.5 - i * 0.5, // Crescimento moderado
      source: 'AF&PA',
      notes: 'Mock data - production implementation would scrape AF&PA monthly reports',
    });
  }

  return mockData;
}

/**
 * Europe - FEFCO (European Federation of Corrugated Board)
 *
 * Source: https://www.fefco.org
 * Data: European corrugated production
 * Access: Quarterly reports (24 EU countries)
 *
 * NOTE: Mock data. Real implementation would parse FEFCO quarterly reports.
 */
async function collectEurope(): Promise<CardboardData[]> {
  console.log('📦 Collecting Europe cardboard data (FEFCO)...');

  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth() + 1;

  const mockData: CardboardData[] = [];

  // FEFCO publica dados trimestrais
  for (let i = 0; i < 2; i++) { // Últimos 2 trimestres
    const quarter = Math.ceil(currentMonth / 3) - i;
    const year = quarter > 0 ? currentYear : currentYear - 1;
    const actualQuarter = quarter > 0 ? quarter : 4 + quarter;

    // Usar primeiro mês do trimestre
    const period = `${year}-${String((actualQuarter - 1) * 3 + 1).padStart(2, '0')}`;

    // Europa produz ~50M tons/ano = ~12.5M tons/trimestre
    const baseProduction = 12500000;
    const seasonality = actualQuarter === 4 ? 500000 : 0; // Q4 boost

    mockData.push({
      country: 'Europe (EU-27)',
      period,
      production_tons: Math.round(baseProduction + seasonality),
      yoy_change_pct: 1.8 - i * 0.4,
      source: 'FEFCO',
      notes: 'Mock data - production would parse FEFCO quarterly reports',
    });
  }

  return mockData;
}

/**
 * China - China Paper Association
 *
 * Source: http://www.chinappi.org
 * Data: Cardboard/corrugated production
 * Access: Public statistics (Chinese + limited English)
 *
 * NOTE: Mock data. Real implementation would scrape China Paper Association
 * and use translation API for Chinese content.
 */
async function collectChina(): Promise<CardboardData[]> {
  console.log('📦 Collecting China cardboard data (CPA)...');

  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth() + 1;

  const mockData: CardboardData[] = [];

  // China é o MAIOR produtor mundial: ~50M tons/ano
  for (let i = 0; i < 6; i++) {
    let month = currentMonth - i;
    let year = currentYear;

    if (month <= 0) {
      month += 12;
      year -= 1;
    }

    const period = `${year}-${String(month).padStart(2, '0')}`;

    // China: ~4-5M tons/mês (maior produtor mundial!)
    const baseProduction = 4200000;
    const seasonality = Math.sin((month / 12) * Math.PI * 2) * 400000;

    mockData.push({
      country: 'China',
      period,
      production_tons: Math.round(baseProduction + seasonality),
      yoy_change_pct: 5.5 - i * 0.8, // China growing faster
      source: 'China Paper Association',
      notes: 'Mock data - production would scrape CPA reports with translation',
    });
  }

  return mockData;
}

/**
 * Brazil - ABPO (Associação Brasileira do Papelão Ondulado)
 *
 * Source: http://www.abpo.org.br
 * Data: Brazilian cardboard production
 * Access: Public statistics (Portuguese)
 */
async function collectBrazil(): Promise<CardboardData[]> {
  console.log('📦 Collecting Brazil cardboard data (ABPO)...');

  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth() + 1;

  const mockData: CardboardData[] = [];

  // Brasil produz ~4M tons/ano = ~330k tons/mês
  for (let i = 0; i < 6; i++) {
    let month = currentMonth - i;
    let year = currentYear;

    if (month <= 0) {
      month += 12;
      year -= 1;
    }

    const period = `${year}-${String(month).padStart(2, '0')}`;

    const baseProduction = 330000; // 330k tons/mês
    const seasonality = Math.sin((month / 12) * Math.PI * 2) * 30000;

    mockData.push({
      country: 'Brazil',
      period,
      production_tons: Math.round(baseProduction + seasonality),
      yoy_change_pct: 3.2 - i * 0.6,
      source: 'ABPO',
      notes: 'Mock data - production would scrape ABPO statistics',
    });
  }

  return mockData;
}

// ============================================================================
// MAIN FUNCTION
// ============================================================================

async function main() {
  console.log('🚀 Sofia Pulse - Cardboard Production Collector');
  console.log('='.repeat(60));
  console.log('');
  console.log('💡 WHY CARDBOARD MATTERS:');
  console.log('   - Leading indicator (2-3 months ahead of GDP)');
  console.log('   - E-commerce explosion = more cardboard');
  console.log('   - Manufacturing activity = packaging demand');
  console.log('   - Available BEFORE official GDP data');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const client = new Client(dbConfig);

  try {
    // Conectar ao banco
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    // Criar tabela se não existir
    await createTableIfNotExists(client);

    // Coletar dados de todas as fontes
    console.log('');
    console.log('📊 Collecting data from all sources...');
    console.log('');

    const allData: CardboardData[] = [];

    // USA
    const usaData = await collectUSA();
    allData.push(...usaData);
    console.log(`   ✅ USA: ${usaData.length} records`);

    // Europe
    const europeData = await collectEurope();
    allData.push(...europeData);
    console.log(`   ✅ Europe: ${europeData.length} records`);

    // China
    const chinaData = await collectChina();
    allData.push(...chinaData);
    console.log(`   ✅ China: ${chinaData.length} records`);

    // Brazil
    const brazilData = await collectBrazil();
    allData.push(...brazilData);
    console.log(`   ✅ Brazil: ${brazilData.length} records`);

    console.log('');
    console.log(`📦 Total records collected: ${allData.length}`);
    console.log('');

    // Inserir no banco
    console.log('💾 Inserting into database...');
    for (const data of allData) {
      await insertCardboardData(client, data);
    }

    console.log(`✅ ${allData.length} records inserted/updated`);
    console.log('');

    // Mostrar resumo por país
    console.log('📊 Summary by country:');
    console.log('');

    const summaryQuery = `
      SELECT
        country,
        COUNT(*) as record_count,
        MAX(period) as latest_period,
        AVG(yoy_change_pct)::DECIMAL(5,2) as avg_yoy_growth,
        SUM(production_tons) as total_production
      FROM cardboard_production
      GROUP BY country
      ORDER BY total_production DESC;
    `;

    const summary = await client.query(summaryQuery);

    summary.rows.forEach((row) => {
      console.log(`   ${row.country}:`);
      console.log(`      Records: ${row.record_count}`);
      console.log(`      Latest: ${row.latest_period}`);
      console.log(`      Avg YoY Growth: ${row.avg_yoy_growth}%`);
      console.log(
        `      Total Production: ${(parseInt(row.total_production) / 1000000).toFixed(2)}M tons`
      );
      console.log('');
    });

    // Exemplo de correlação potencial
    console.log('='.repeat(60));
    console.log('');
    console.log('💡 NEXT STEPS - ML Correlations:');
    console.log('');
    console.log('   1. Correlate with GDP growth (2-3 month lag)');
    console.log('   2. Correlate with stock market indices');
    console.log('   3. Correlate with e-commerce sales data');
    console.log('   4. Correlate with manufacturing PMI');
    console.log('   5. Build predictive model: Cardboard → GDP → Stocks');
    console.log('');
    console.log('   Example query:');
    console.log('   ```sql');
    console.log('   SELECT');
    console.log('     c.period,');
    console.log('     c.production_tons,');
    console.log('     c.yoy_change_pct as cardboard_growth,');
    console.log('     -- Add GDP, stock indices when available');
    console.log('   FROM cardboard_production c');
    console.log('   WHERE c.country = \'USA\'');
    console.log('   ORDER BY c.period DESC;');
    console.log('   ```');
    console.log('');

    console.log('✅ Collection complete!');
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

// ============================================================================
// DRY RUN MODE (No database required)
// ============================================================================

async function dryRun() {
  console.log('🚀 Sofia Pulse - Cardboard Production Collector (DRY RUN)');
  console.log('='.repeat(60));
  console.log('');
  console.log('💡 WHY CARDBOARD MATTERS:');
  console.log('   - Leading indicator (2-3 months ahead of GDP)');
  console.log('   - E-commerce explosion = more cardboard');
  console.log('   - Manufacturing activity = packaging demand');
  console.log('   - Available BEFORE official GDP data');
  console.log('');
  console.log('='.repeat(60));
  console.log('');
  console.log('🔍 Collecting data (preview only - no database write)...');
  console.log('');

  // Coletar dados de todas as fontes
  const allData: CardboardData[] = [];

  // USA
  const usaData = await collectUSA();
  allData.push(...usaData);
  console.log(`   ✅ USA (AF&PA): ${usaData.length} records`);

  // Europe
  const europeData = await collectEurope();
  allData.push(...europeData);
  console.log(`   ✅ Europe (FEFCO): ${europeData.length} records`);

  // China
  const chinaData = await collectChina();
  allData.push(...chinaData);
  console.log(`   ✅ China (CPA): ${chinaData.length} records`);

  // Brazil
  const brazilData = await collectBrazil();
  allData.push(...brazilData);
  console.log(`   ✅ Brazil (ABPO): ${brazilData.length} records`);

  console.log('');
  console.log(`📦 Total records: ${allData.length}`);
  console.log('');

  // Mostrar amostra dos dados
  console.log('📊 Sample data (latest period by country):');
  console.log('');

  const latestByCountry = allData.reduce((acc, data) => {
    if (!acc[data.country] || data.period > acc[data.country].period) {
      acc[data.country] = data;
    }
    return acc;
  }, {} as Record<string, CardboardData>);

  Object.values(latestByCountry).forEach((data) => {
    console.log(`   ${data.country} (${data.period}):`);
    console.log(`      Production: ${(data.production_tons / 1000000).toFixed(2)}M tons`);
    console.log(`      YoY Growth: ${data.yoy_change_pct}%`);
    console.log(`      Source: ${data.source}`);
    console.log('');
  });

  // Calcular totais
  const totalProduction = allData.reduce((sum, d) => sum + d.production_tons, 0);
  const avgGrowth = allData.reduce((sum, d) => sum + d.yoy_change_pct, 0) / allData.length;

  console.log('='.repeat(60));
  console.log('');
  console.log('📈 SUMMARY:');
  console.log('');
  console.log(`   Total Production (all periods): ${(totalProduction / 1000000).toFixed(2)}M tons`);
  console.log(`   Average YoY Growth: ${avgGrowth.toFixed(2)}%`);
  console.log(`   Countries: USA, Europe, China, Brazil`);
  console.log(`   Data Points: ${allData.length}`);
  console.log('');

  console.log('💡 ECONOMIC INSIGHTS:');
  console.log('');

  // China é maior produtor
  const chinaTotal = chinaData.reduce((sum, d) => sum + d.production_tons, 0);
  const usaTotal = usaData.reduce((sum, d) => sum + d.production_tons, 0);
  const europeTotal = europeData.reduce((sum, d) => sum + d.production_tons, 0);

  console.log(`   1. China dominates: ${(chinaTotal / 1000000).toFixed(1)}M tons`);
  console.log(`   2. USA production: ${(usaTotal / 1000000).toFixed(1)}M tons`);
  console.log(`   3. Europe: ${(europeTotal / 1000000).toFixed(1)}M tons`);
  console.log('');
  console.log('   China growth rate indicates strong manufacturing/e-commerce');
  console.log('   USA/Europe growth correlates with consumer spending');
  console.log('');

  console.log('='.repeat(60));
  console.log('');
  console.log('🎯 NEXT STEPS:');
  console.log('');
  console.log('   1. Start PostgreSQL database');
  console.log('   2. Run: npm run collect:cardboard');
  console.log('   3. Data will be stored in cardboard_production table');
  console.log('   4. Correlate with GDP, stock indices, PMI data');
  console.log('');
  console.log('   Example correlation query:');
  console.log('   ```sql');
  console.log('   SELECT c.period,');
  console.log('          c.production_tons,');
  console.log('          c.yoy_change_pct as cardboard_growth,');
  console.log('          -- Correlate with macro_indicators.GDP_growth');
  console.log('          -- Correlate with stock indices');
  console.log('   FROM cardboard_production c');
  console.log('   WHERE c.country = \'USA\'');
  console.log('   ORDER BY c.period DESC;');
  console.log('   ```');
  console.log('');
  console.log('✅ Dry run complete!');
}

// ============================================================================
// RUN
// ============================================================================

if (require.main === module) {
  const args = process.argv.slice(2);
  const isDryRun = args.includes('--dry-run') || args.includes('-d');

  if (isDryRun) {
    dryRun().catch(console.error);
  } else {
    main().catch((error) => {
      if (error.code === 'ECONNREFUSED') {
        console.log('');
        console.log('⚠️  Database connection failed!');
        console.log('');
        console.log('💡 TIP: Run with --dry-run to see sample data without database:');
        console.log('   npm run collect:cardboard -- --dry-run');
        console.log('');
        console.log('Or start PostgreSQL first:');
        console.log('   cd finance && ./docker-run.sh');
        console.log('');
        process.exit(1);
      }
      throw error;
    });
  }
}

export { collectUSA, collectEurope, collectChina, collectBrazil, dryRun };
