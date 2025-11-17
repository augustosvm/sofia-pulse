#!/usr/bin/env tsx

/**
 * Sofia Finance Intelligence Hub - Investment Signal Generator
 *
 * Gera sinais de investimento baseado em dados reais do banco de dados.
 */

import { Client } from 'pg';
import { writeFileSync } from 'fs';
import { join } from 'path';
import * as dotenv from 'dotenv';

dotenv.config();

// ============================================================================
// TYPES
// ============================================================================

interface InvestmentSignal {
  id: string;
  type: 'B3_STOCK' | 'NASDAQ_MOMENTUM' | 'FUNDING_ROUND';
  title: string;
  description: string;
  score: number;
  confidence: number;
  potential_return: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  ticker?: string;
  company: string;
  sector: string;
  market: string;
  price?: number;
  target_price?: number;
  indicators: {
    price_momentum?: number;
    volume_spike?: number;
    market_cap?: number;
  };
  recommendation: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'WATCH';
  reasoning: string[];
  generated_at: string;
}

interface StockData {
  ticker: string;
  company: string;
  sector: string;
  price: number;
  change_pct: number;
  volume: number;
  market_cap: number;
}

// ============================================================================
// DATABASE SETUP
// ============================================================================

const dbConfig = {
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || 'postgres',
  database: process.env.POSTGRES_DB || 'sofia_db',
};

// ============================================================================
// SIGNAL GENERATION
// ============================================================================

function calculateScore(stock: StockData): number {
  let score = 50; // Base score

  // Price momentum
  if (stock.change_pct > 3) score += 20;
  else if (stock.change_pct > 1) score += 10;
  else if (stock.change_pct > 0) score += 5;

  // Volume (high volume = more confidence)
  if (stock.volume > 30000000) score += 15;
  else if (stock.volume > 20000000) score += 10;
  else if (stock.volume > 10000000) score += 5;

  // Market cap (stability)
  if (stock.market_cap > 200000000000) score += 10;
  else if (stock.market_cap > 100000000000) score += 5;

  return Math.min(Math.max(score, 0), 100);
}

function getRiskLevel(score: number, changePct: number): 'LOW' | 'MEDIUM' | 'HIGH' {
  if (score > 80 && Math.abs(changePct) < 2) return 'LOW';
  if (score > 60 && Math.abs(changePct) < 4) return 'MEDIUM';
  return 'HIGH';
}

function getRecommendation(score: number): 'STRONG_BUY' | 'BUY' | 'HOLD' | 'WATCH' {
  if (score >= 80) return 'STRONG_BUY';
  if (score >= 70) return 'BUY';
  if (score >= 60) return 'HOLD';
  return 'WATCH';
}

function generateReasoning(stock: StockData): string[] {
  const reasons: string[] = [];

  if (stock.change_pct > 2) {
    reasons.push(`Forte momentum de +${stock.change_pct.toFixed(1)}% no período`);
  } else if (stock.change_pct > 0) {
    reasons.push(`Valorização de +${stock.change_pct.toFixed(1)}%`);
  }

  if (stock.volume > 30000000) {
    reasons.push('Volume muito acima da média indicando forte interesse');
  } else if (stock.volume > 20000000) {
    reasons.push('Volume acima da média do setor');
  }

  if (stock.market_cap > 200000000000) {
    reasons.push('Blue chip com alta capitalização');
  }

  if (stock.sector === 'Energia' || stock.sector === 'Mineração') {
    reasons.push('Setor estratégico com demanda global crescente');
  }

  if (reasons.length === 0) {
    reasons.push('Ativo monitorado pelo sistema Sofia');
  }

  return reasons;
}

function stockToSignal(stock: StockData, index: number): InvestmentSignal {
  const score = calculateScore(stock);
  const confidence = Math.min(75 + (score / 5), 95);
  const potentialReturn = Math.abs(stock.change_pct) * (1 + Math.random() * 2);
  const targetPrice = stock.price * (1 + potentialReturn / 100);

  return {
    id: `B3-${Date.now()}-${index}`,
    type: 'B3_STOCK',
    title: `${stock.ticker} - ${stock.company}`,
    description: `Análise técnica ${stock.sector}`,
    score,
    confidence,
    potential_return: potentialReturn,
    risk_level: getRiskLevel(score, stock.change_pct),
    ticker: stock.ticker,
    company: stock.company,
    sector: stock.sector,
    market: 'B3',
    price: stock.price,
    target_price: targetPrice,
    indicators: {
      price_momentum: stock.change_pct,
      volume_spike: stock.volume / 10000000,
      market_cap: stock.market_cap,
    },
    recommendation: getRecommendation(score),
    reasoning: generateReasoning(stock),
    generated_at: new Date().toISOString(),
  };
}

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

async function getLatestStocks(client: Client): Promise<StockData[]> {
  const result = await client.query(`
    SELECT DISTINCT ON (ticker)
      ticker, company, sector, price, change_pct, volume, market_cap
    FROM market_data_brazil
    ORDER BY ticker, collected_at DESC
  `);

  return result.rows;
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  console.log('\n╔═══════════════════════════════════════════════════════════════╗');
  console.log('║     🎯 Sofia Finance - Investment Signal Generator          ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝\n');

  const client = new Client(dbConfig);

  try {
    console.log('🔌 Conectando ao PostgreSQL...');
    await client.connect();
    console.log('✅ Conectado!\n');

    console.log('📊 Buscando dados do mercado...');
    const stocks = await getLatestStocks(client);

    if (stocks.length === 0) {
      console.log('⚠️  Nenhum dado encontrado no banco.');
      console.log('💡 Execute primeiro: npm run collect:brazil\n');
      process.exit(1);
    }

    console.log(`   Encontradas ${stocks.length} ações\n`);

    console.log('🤖 Gerando sinais de investimento...');
    const signals = stocks.map((stock, index) => stockToSignal(stock, index));

    // Sort by score
    signals.sort((a, b) => b.score - a.score);

    console.log(`✅ ${signals.length} sinais gerados!\n`);

    // Display top 5
    console.log('🏆 Top 5 Sinais:\n');
    signals.slice(0, 5).forEach((signal, i) => {
      const recEmoji = signal.recommendation === 'STRONG_BUY' ? '🚀' :
                       signal.recommendation === 'BUY' ? '✅' :
                       signal.recommendation === 'HOLD' ? '👀' : '⏸️';
      const riskEmoji = signal.risk_level === 'LOW' ? '🟢' :
                        signal.risk_level === 'MEDIUM' ? '🟡' : '🔴';

      console.log(`${i + 1}. ${recEmoji} ${signal.ticker} - Score: ${signal.score.toFixed(0)}/100`);
      console.log(`   ${riskEmoji} Risk: ${signal.risk_level} | Return: ${signal.potential_return.toFixed(1)}%`);
      console.log(`   ${signal.reasoning[0]}\n`);
    });

    // Save to file
    const timestamp = new Date().toISOString().split('T')[0];
    const outputPath = join(process.cwd(), 'output', `sofia-signals-${timestamp}.json`);

    const output = {
      generated_at: new Date().toISOString(),
      total_signals: signals.length,
      signals,
      metadata: {
        version: '1.0.0',
        generator: 'sofia-finance-db',
        markets: ['B3'],
        source: 'database',
      },
    };

    writeFileSync(outputPath, JSON.stringify(output, null, 2));
    console.log(`💾 Sinais salvos em: ${outputPath}\n`);
    console.log('✅ Geração de sinais concluída!\n');

  } catch (error) {
    console.error('\n❌ Erro durante geração:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

main();
