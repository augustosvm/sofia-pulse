#!/usr/bin/env tsx

/**
 * Sofia Finance Intelligence Hub - NASDAQ Momentum Collector
 *
 * Coleta dados de momentum do NASDAQ usando Alpha Vantage API.
 * Identifica ações com forte movimento positivo.
 */

import { Client } from 'pg';
import axios from 'axios';
import * as dotenv from 'dotenv';

dotenv.config();

// ============================================================================
// CONFIG
// ============================================================================

const API_KEY = process.env.ALPHA_VANTAGE_API_KEY;
const DELAY_MS = 12000; // Alpha Vantage free tier: 5 calls/min = 12s entre calls

const dbConfig = {
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || 'postgres',
  database: process.env.POSTGRES_DB || 'sofia_db',
};

// ============================================================================
// TYPES
// ============================================================================

interface NasdaqStock {
  ticker: string;
  company: string;
  sector: string;
  price: number;
  change_pct: number;
  volume: number;
  market_cap?: number;
}

// ============================================================================
// TOP NASDAQ STOCKS TO TRACK
// ============================================================================

const NASDAQ_TICKERS = [
  { symbol: 'NVDA', name: 'NVIDIA', sector: 'Semiconductors' },
  { symbol: 'TSLA', name: 'Tesla', sector: 'EV & Energy' },
  { symbol: 'AAPL', name: 'Apple', sector: 'Technology' },
  { symbol: 'MSFT', name: 'Microsoft', sector: 'Technology' },
  { symbol: 'META', name: 'Meta', sector: 'Social Media' },
];

// ============================================================================
// ALPHA VANTAGE API
// ============================================================================

async function fetchQuote(symbol: string): Promise<NasdaqStock | null> {
  if (!API_KEY) {
    throw new Error('ALPHA_VANTAGE_API_KEY não configurada no .env');
  }

  try {
    const url = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=${API_KEY}`;
    const response = await axios.get(url);

    const quote = response.data['Global Quote'];
    if (!quote || !quote['05. price']) {
      console.log(`   ⚠️  ${symbol}: Sem dados disponíveis`);
      return null;
    }

    const ticker = NASDAQ_TICKERS.find(t => t.symbol === symbol);
    if (!ticker) return null;

    return {
      ticker: symbol,
      company: ticker.name,
      sector: ticker.sector,
      price: parseFloat(quote['05. price']),
      change_pct: parseFloat(quote['10. change percent'].replace('%', '')),
      volume: parseInt(quote['06. volume']),
    };
  } catch (error: any) {
    if (error.response?.status === 429) {
      console.log(`   ⚠️  ${symbol}: Rate limit atingido, aguarde...`);
    } else {
      console.log(`   ❌ ${symbol}: Erro - ${error.message}`);
    }
    return null;
  }
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

async function createTableIfNotExists(client: Client) {
  await client.query(`
    CREATE TABLE IF NOT EXISTS market_data_nasdaq (
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
    CREATE INDEX IF NOT EXISTS idx_nasdaq_ticker ON market_data_nasdaq(ticker);
  `);
}

async function insertStock(client: Client, stock: NasdaqStock) {
  try {
    await client.query(`
      INSERT INTO market_data_nasdaq (
        ticker, company, sector, price, change_pct, volume
      ) VALUES ($1, $2, $3, $4, $5, $6)
      ON CONFLICT (ticker, collected_at) DO NOTHING
    `, [
      stock.ticker,
      stock.company,
      stock.sector,
      stock.price,
      stock.change_pct,
      stock.volume,
    ]);
  } catch (error) {
    console.error(`❌ Erro ao inserir ${stock.ticker}:`, error);
  }
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  console.log('\n╔═══════════════════════════════════════════════════════════════╗');
  console.log('║     📊 Sofia Finance - NASDAQ Momentum Collector           ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝\n');

  if (!API_KEY) {
    console.error('❌ ALPHA_VANTAGE_API_KEY não configurada!');
    console.log('\n💡 Configure no .env:');
    console.log('   ALPHA_VANTAGE_API_KEY=sua_key_aqui\n');
    console.log('🔑 Obtenha uma key grátis: https://www.alphavantage.co/support/#api-key\n');
    process.exit(1);
  }

  const client = new Client(dbConfig);

  try {
    console.log('🔌 Conectando ao PostgreSQL...');
    await client.connect();
    console.log('✅ Conectado!\n');

    console.log('📋 Criando tabelas se necessário...');
    await createTableIfNotExists(client);
    console.log('✅ Tabelas prontas!\n');

    console.log(`📈 Coletando ${NASDAQ_TICKERS.length} ações NASDAQ...`);
    console.log('⏱️  Alpha Vantage rate limit: 5 calls/min (aguarde ~12s entre cada)\n');

    let collected = 0;
    for (let i = 0; i < NASDAQ_TICKERS.length; i++) {
      const ticker = NASDAQ_TICKERS[i];
      console.log(`   [${i + 1}/${NASDAQ_TICKERS.length}] Buscando ${ticker.symbol}...`);

      const stock = await fetchQuote(ticker.symbol);

      if (stock) {
        await insertStock(client, stock);
        const arrow = stock.change_pct >= 0 ? '📈' : '📉';
        const sign = stock.change_pct >= 0 ? '+' : '';
        console.log(`   ${arrow} ${stock.ticker.padEnd(6)} $${stock.price.toFixed(2).padStart(8)} ${sign}${stock.change_pct.toFixed(2)}%`);
        collected++;
      }

      // Rate limit: aguardar entre requests (exceto no último)
      if (i < NASDAQ_TICKERS.length - 1) {
        await delay(DELAY_MS);
      }
    }

    console.log(`\n✅ ${collected}/${NASDAQ_TICKERS.length} ações coletadas!\n`);

  } catch (error) {
    console.error('\n❌ Erro durante coleta:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

main();
