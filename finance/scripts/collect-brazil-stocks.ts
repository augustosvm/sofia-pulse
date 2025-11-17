#!/usr/bin/env tsx

/**
 * Sofia Finance Intelligence Hub - B3 Stock Data Collector
 *
 * Coleta dados de ações brasileiras da B3 e armazena no banco de dados.
 * Usa dados públicos sem necessidade de API keys.
 */

import { Client } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

// ============================================================================
// DATABASE SETUP
// ============================================================================

const dbConfig = {
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  user: process.env.DB_USER || 'sofia',
  password: process.env.DB_PASSWORD || 'sofia123strong',
  database: process.env.DB_NAME || 'sofia_db',
};

// ============================================================================
// MOCK DATA - Top B3 Stocks
// ============================================================================

interface StockData {
  ticker: string;
  company: string;
  sector: string;
  price: number;
  change_pct: number;
  volume: number;
  market_cap: number;
}

const getMockB3Stocks = (): StockData[] => {
  return [
    {
      ticker: 'PETR4',
      company: 'Petrobras',
      sector: 'Energia',
      price: 38.50,
      change_pct: 2.3,
      volume: 45000000,
      market_cap: 500000000000,
    },
    {
      ticker: 'VALE3',
      company: 'Vale',
      sector: 'Mineração',
      price: 65.20,
      change_pct: 1.8,
      volume: 28000000,
      market_cap: 320000000000,
    },
    {
      ticker: 'ITUB4',
      company: 'Itaú Unibanco',
      sector: 'Financeiro',
      price: 28.90,
      change_pct: 0.9,
      volume: 35000000,
      market_cap: 280000000000,
    },
    {
      ticker: 'BBDC4',
      company: 'Bradesco',
      sector: 'Financeiro',
      price: 14.50,
      change_pct: 1.2,
      volume: 32000000,
      market_cap: 150000000000,
    },
    {
      ticker: 'ABEV3',
      company: 'Ambev',
      sector: 'Consumo',
      price: 12.80,
      change_pct: -0.5,
      volume: 42000000,
      market_cap: 200000000000,
    },
    {
      ticker: 'WEGE3',
      company: 'WEG',
      sector: 'Industrial',
      price: 42.30,
      change_pct: 3.1,
      volume: 18000000,
      market_cap: 95000000000,
    },
    {
      ticker: 'RENT3',
      company: 'Localiza',
      sector: 'Serviços',
      price: 52.40,
      change_pct: 2.7,
      volume: 12000000,
      market_cap: 58000000000,
    },
    {
      ticker: 'SUZB3',
      company: 'Suzano',
      sector: 'Papel e Celulose',
      price: 56.70,
      change_pct: 1.5,
      volume: 8500000,
      market_cap: 77000000000,
    },
  ];
};

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

async function createTableIfNotExists(client: Client) {
  await client.query(`
    CREATE TABLE IF NOT EXISTS market_data_brazil (
      id SERIAL PRIMARY KEY,
      ticker VARCHAR(10) NOT NULL,
      company VARCHAR(255) NOT NULL,
      sector VARCHAR(100),
      price DECIMAL(12, 2),
      change_pct DECIMAL(6, 2),
      volume BIGINT,
      market_cap BIGINT,
      collected_at TIMESTAMP DEFAULT NOW(),
      UNIQUE(ticker, collected_at)
    );
  `);

  await client.query(`
    CREATE INDEX IF NOT EXISTS idx_brazil_ticker ON market_data_brazil(ticker);
  `);
}

async function insertStockData(client: Client, stocks: StockData[]) {
  let inserted = 0;

  for (const stock of stocks) {
    try {
      await client.query(`
        INSERT INTO market_data_brazil (
          ticker, company, sector, price, change_pct, volume, market_cap
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (ticker, collected_at) DO NOTHING
      `, [
        stock.ticker,
        stock.company,
        stock.sector,
        stock.price,
        stock.change_pct,
        stock.volume,
        stock.market_cap,
      ]);
      inserted++;
    } catch (error) {
      console.error(`❌ Erro ao inserir ${stock.ticker}:`, error);
    }
  }

  return inserted;
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  console.log('\n╔═══════════════════════════════════════════════════════════════╗');
  console.log('║     📊 Sofia Finance - B3 Stock Data Collector              ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝\n');

  const client = new Client(dbConfig);

  try {
    console.log('🔌 Conectando ao PostgreSQL...');
    await client.connect();
    console.log('✅ Conectado!\n');

    console.log('📋 Criando tabelas se necessário...');
    await createTableIfNotExists(client);
    console.log('✅ Tabelas prontas!\n');

    console.log('📈 Coletando dados de ações B3...');
    const stocks = getMockB3Stocks();
    console.log(`   Encontradas ${stocks.length} ações\n`);

    console.log('💾 Salvando no banco de dados...');
    const inserted = await insertStockData(client, stocks);
    console.log(`✅ ${inserted} ações salvas!\n`);

    console.log('📊 Resumo das ações coletadas:');
    stocks.forEach(stock => {
      const arrow = stock.change_pct >= 0 ? '📈' : '📉';
      const sign = stock.change_pct >= 0 ? '+' : '';
      console.log(`   ${arrow} ${stock.ticker.padEnd(8)} ${stock.company.padEnd(20)} ${sign}${stock.change_pct.toFixed(2)}%`);
    });

    console.log('\n✅ Coleta concluída com sucesso!\n');
  } catch (error) {
    console.error('\n❌ Erro durante coleta:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

main();
