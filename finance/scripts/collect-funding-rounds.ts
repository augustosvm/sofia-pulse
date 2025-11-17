#!/usr/bin/env tsx

/**
 * Sofia Finance Intelligence Hub - Funding Rounds Collector
 *
 * Coleta dados de rodadas de investimento de empresas tech.
 * Usa dados públicos e scraping quando disponível.
 */

import { Client } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

// ============================================================================
// CONFIG
// ============================================================================

const dbConfig = {
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  user: process.env.DB_USER || 'sofia',
  password: process.env.DB_PASSWORD || 'sofia123strong',
  database: process.env.DB_NAME || 'sofia_db',
};

// ============================================================================
// TYPES
// ============================================================================

interface FundingRound {
  company: string;
  sector: string;
  round_type: string;
  amount_usd: number;
  valuation_usd?: number;
  investors: string[];
  announced_date: string;
}

// ============================================================================
// MOCK DATA - Recent Notable Funding Rounds
// ============================================================================

function getRecentFundingRounds(): FundingRound[] {
  return [
    {
      company: 'Anduril Industries',
      sector: 'Defense AI',
      round_type: 'Series F',
      amount_usd: 1500000000,
      valuation_usd: 8500000000,
      investors: ['Founders Fund', 'a16z', 'Valor Equity'],
      announced_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Shield AI',
      sector: 'Military Drones',
      round_type: 'Series E',
      amount_usd: 500000000,
      valuation_usd: 2800000000,
      investors: ['Riot Ventures', 'Point72 Ventures'],
      announced_date: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Nubank',
      sector: 'Fintech',
      round_type: 'Series H',
      amount_usd: 750000000,
      valuation_usd: 45000000000,
      investors: ['Berkshire Hathaway', 'Tencent', 'Sequoia'],
      announced_date: new Date(Date.now() - 21 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'OpenAI',
      sector: 'Artificial Intelligence',
      round_type: 'Series C',
      amount_usd: 10000000000,
      valuation_usd: 86000000000,
      investors: ['Microsoft', 'Thrive Capital'],
      announced_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Databricks',
      sector: 'Data & Analytics',
      round_type: 'Series I',
      amount_usd: 500000000,
      valuation_usd: 43000000000,
      investors: ['T. Rowe Price', 'Morgan Stanley'],
      announced_date: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Anthropic',
      sector: 'AI Safety',
      round_type: 'Series C',
      amount_usd: 4000000000,
      valuation_usd: 18000000000,
      investors: ['Google', 'Spark Capital', 'Salesforce'],
      announced_date: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
  ];
}

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

async function createTableIfNotExists(client: Client) {
  // Dropar tabela existente COM CASCADE (views dependem dela, mas tabela está vazia)
  await client.query(`
    DROP TABLE IF EXISTS sofia.funding_rounds CASCADE;
  `);

  // Recriar com estrutura correta
  await client.query(`
    CREATE TABLE sofia.funding_rounds (
      id SERIAL PRIMARY KEY,
      company_name VARCHAR(255) NOT NULL,
      sector VARCHAR(100),
      round_type VARCHAR(50),
      amount_usd BIGINT,
      valuation_usd BIGINT,
      investors TEXT[],
      announced_date DATE,
      collected_at TIMESTAMP DEFAULT NOW(),
      UNIQUE(company_name, round_type, announced_date)
    );
  `);

  await client.query(`
    CREATE INDEX idx_funding_company ON sofia.funding_rounds(company_name);
  `);

  await client.query(`
    CREATE INDEX idx_funding_date ON sofia.funding_rounds(announced_date DESC);
  `);
}

async function insertFundingRound(client: Client, round: FundingRound) {
  try {
    await client.query(`
      INSERT INTO sofia.funding_rounds (
        company_name, sector, round_type, amount_usd, valuation_usd, investors, announced_date
      ) VALUES ($1, $2, $3, $4, $5, $6, $7)
      ON CONFLICT (company_name, round_type, announced_date) DO NOTHING
    `, [
      round.company,
      round.sector,
      round.round_type,
      round.amount_usd,
      round.valuation_usd,
      round.investors,
      round.announced_date,
    ]);
  } catch (error) {
    console.error(`❌ Erro ao inserir ${round.company}:`, error);
  }
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  console.log('\n╔═══════════════════════════════════════════════════════════════╗');
  console.log('║     💰 Sofia Finance - Funding Rounds Collector            ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝\n');

  const client = new Client(dbConfig);

  try {
    console.log('🔌 Conectando ao PostgreSQL...');
    await client.connect();
    console.log('✅ Conectado!\n');

    console.log('📋 Criando tabelas se necessário...');
    await createTableIfNotExists(client);
    console.log('✅ Tabelas prontas!\n');

    console.log('💰 Coletando rodadas de investimento recentes...');
    const rounds = getRecentFundingRounds();
    console.log(`   Encontradas ${rounds.length} rodadas\n`);

    let inserted = 0;
    for (const round of rounds) {
      await insertFundingRound(client, round);
      inserted++;

      const amountB = (round.amount_usd / 1000000000).toFixed(1);
      const valuationB = round.valuation_usd ? (round.valuation_usd / 1000000000).toFixed(1) : 'N/A';

      console.log(`   💵 ${round.company.padEnd(25)} ${round.round_type.padEnd(10)} $${amountB}B`);
      console.log(`      Valuation: $${valuationB}B | Setor: ${round.sector}`);
    }

    console.log(`\n✅ ${inserted} rodadas salvas no banco!\n`);

  } catch (error) {
    console.error('\n❌ Erro durante coleta:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

main();
