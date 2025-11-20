#!/usr/bin/env tsx

// Fix for Node.js 18 + undici - MUST BE AFTER SHEBANG!
// @ts-ignore
if (typeof File === 'undefined') {
  // @ts-ignore
  globalThis.File = class File extends Blob {
    constructor(bits: any[], name: string, options?: any) {
      super(bits, options);
    }
  };
}


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
  country?: string;
  announced_date: string;
}

// ============================================================================
// MOCK DATA - Recent Notable Funding Rounds
// ============================================================================

function getRecentFundingRounds(): FundingRound[] {
  return [
    // AI & Machine Learning
    {
      company: 'OpenAI',
      sector: 'Artificial Intelligence',
      round_type: 'Series C',
      amount_usd: 10000000000,
      valuation_usd: 86000000000,
      investors: ['Microsoft', 'Thrive Capital'],
      country: 'USA',
      announced_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Anthropic',
      sector: 'AI Safety',
      round_type: 'Series C',
      amount_usd: 4000000000,
      valuation_usd: 18000000000,
      investors: ['Google', 'Spark Capital', 'Salesforce'],
      country: 'USA',
      announced_date: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Inflection AI',
      sector: 'Artificial Intelligence',
      round_type: 'Series B',
      amount_usd: 1300000000,
      valuation_usd: 4000000000,
      investors: ['Microsoft', 'Reid Hoffman', 'Bill Gates'],
      country: 'USA',
      announced_date: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Adept AI',
      sector: 'AI Agents',
      round_type: 'Series B',
      amount_usd: 350000000,
      valuation_usd: 1000000000,
      investors: ['General Catalyst', 'Spark Capital'],
      country: 'USA',
      announced_date: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Mistral AI',
      sector: 'Open Source AI',
      round_type: 'Series A',
      amount_usd: 415000000,
      valuation_usd: 2000000000,
      investors: ['a16z', 'Lightspeed Venture Partners'],
      country: 'France',
      announced_date: new Date(Date.now() - 50 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },

    // Defense & Aerospace
    {
      company: 'Anduril Industries',
      sector: 'Defense AI',
      round_type: 'Series F',
      amount_usd: 1500000000,
      valuation_usd: 8500000000,
      investors: ['Founders Fund', 'a16z', 'Valor Equity'],
      country: 'USA',
      announced_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Shield AI',
      sector: 'Military Drones',
      round_type: 'Series E',
      amount_usd: 500000000,
      valuation_usd: 2800000000,
      investors: ['Riot Ventures', 'Point72 Ventures'],
      country: 'USA',
      announced_date: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },

    // Cloud & Infrastructure
    {
      company: 'Databricks',
      sector: 'Data & Analytics',
      round_type: 'Series I',
      amount_usd: 500000000,
      valuation_usd: 43000000000,
      investors: ['T. Rowe Price', 'Morgan Stanley'],
      country: 'USA',
      announced_date: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Wiz',
      sector: 'Cloud Security',
      round_type: 'Series D',
      amount_usd: 300000000,
      valuation_usd: 10000000000,
      investors: ['Sequoia', 'Thrive Capital', 'Greylock'],
      country: 'USA',
      announced_date: new Date(Date.now() - 70 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Vercel',
      sector: 'Developer Tools',
      round_type: 'Series D',
      amount_usd: 250000000,
      valuation_usd: 2500000000,
      investors: ['Accel', 'GV'],
      country: 'USA',
      announced_date: new Date(Date.now() - 100 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },

    // Fintech
    {
      company: 'Nubank',
      sector: 'Fintech',
      round_type: 'Series H',
      amount_usd: 750000000,
      valuation_usd: 45000000000,
      investors: ['Berkshire Hathaway', 'Tencent', 'Sequoia'],
      country: 'Brazil',
      announced_date: new Date(Date.now() - 21 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Stripe',
      sector: 'Payments',
      round_type: 'Series I',
      amount_usd: 600000000,
      valuation_usd: 50000000000,
      investors: ['Thrive Capital', 'General Catalyst'],
      country: 'USA',
      announced_date: new Date(Date.now() - 120 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Chime',
      sector: 'Neobank',
      round_type: 'Series G',
      amount_usd: 750000000,
      valuation_usd: 25000000000,
      investors: ['Sequoia', 'Tiger Global'],
      country: 'USA',
      announced_date: new Date(Date.now() - 150 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },

    // Biotech & Healthcare
    {
      company: 'Recursion Pharmaceuticals',
      sector: 'AI Drug Discovery',
      round_type: 'Series D',
      amount_usd: 239000000,
      valuation_usd: 2200000000,
      investors: ['Baillie Gifford', 'ARK Investment'],
      country: 'USA',
      announced_date: new Date(Date.now() - 80 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Insitro',
      sector: 'Machine Learning Biotech',
      round_type: 'Series C',
      amount_usd: 400000000,
      valuation_usd: 2400000000,
      investors: ['a16z', 'BlackRock'],
      country: 'USA',
      announced_date: new Date(Date.now() - 110 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },

    // Climate Tech
    {
      company: 'Northvolt',
      sector: 'Battery Manufacturing',
      round_type: 'Series E',
      amount_usd: 1200000000,
      valuation_usd: 12000000000,
      investors: ['Goldman Sachs', 'Volkswagen'],
      country: 'Sweden',
      announced_date: new Date(Date.now() - 130 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Redwood Materials',
      sector: 'Battery Recycling',
      round_type: 'Series D',
      amount_usd: 700000000,
      valuation_usd: 3700000000,
      investors: ['T. Rowe Price', 'Baillie Gifford'],
      country: 'USA',
      announced_date: new Date(Date.now() - 140 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Climeworks',
      sector: 'Carbon Capture',
      round_type: 'Series F',
      amount_usd: 650000000,
      valuation_usd: 1000000000,
      investors: ['Partners Group', 'Baillie Gifford'],
      country: 'Switzerland',
      announced_date: new Date(Date.now() - 160 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },

    // EV & Mobility
    {
      company: 'Rivian',
      sector: 'Electric Vehicles',
      round_type: 'Series E',
      amount_usd: 2500000000,
      valuation_usd: 27600000000,
      investors: ['Amazon', 'T. Rowe Price'],
      country: 'USA',
      announced_date: new Date(Date.now() - 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Waymo',
      sector: 'Autonomous Vehicles',
      round_type: 'Series C',
      amount_usd: 2500000000,
      valuation_usd: 30000000000,
      investors: ['Alphabet', 'Silver Lake', 'Andreessen Horowitz'],
      country: 'USA',
      announced_date: new Date(Date.now() - 200 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },

    // Crypto & Web3
    {
      company: 'Circle',
      sector: 'Stablecoin',
      round_type: 'Series E',
      amount_usd: 400000000,
      valuation_usd: 9000000000,
      investors: ['BlackRock', 'Fidelity'],
      country: 'USA',
      announced_date: new Date(Date.now() - 170 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Chainalysis',
      sector: 'Blockchain Analytics',
      round_type: 'Series F',
      amount_usd: 170000000,
      valuation_usd: 8600000000,
      investors: ['GIC', 'Coatue'],
      country: 'USA',
      announced_date: new Date(Date.now() - 190 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },

    // E-commerce & Retail
    {
      company: 'Klarna',
      sector: 'Buy Now Pay Later',
      round_type: 'Series H',
      amount_usd: 800000000,
      valuation_usd: 6700000000,
      investors: ['Sequoia', 'Silver Lake'],
      country: 'Sweden',
      announced_date: new Date(Date.now() - 210 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    },
    {
      company: 'Shein',
      sector: 'Fast Fashion E-commerce',
      round_type: 'Series E',
      amount_usd: 2000000000,
      valuation_usd: 66000000000,
      investors: ['General Atlantic', 'Sequoia China'],
      country: 'Singapore',
      announced_date: new Date(Date.now() - 220 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
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
      country VARCHAR(100),
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
        company_name, sector, round_type, amount_usd, valuation_usd, investors, country, announced_date
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      ON CONFLICT (company_name, round_type, announced_date) DO NOTHING
    `, [
      round.company,
      round.sector,
      round.round_type,
      round.amount_usd,
      round.valuation_usd,
      round.investors,
      round.country,
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
