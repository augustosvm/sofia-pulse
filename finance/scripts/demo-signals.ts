#!/usr/bin/env tsx

/**
 * Sofia Finance Intelligence Hub - Demo Script
 *
 * Gera sinais de investimento com dados realistas SEM precisar de banco de dados.
 * Perfeito para testes rápidos e demonstrações.
 *
 * Uso: npm run demo
 */

import { writeFileSync } from 'fs';
import { join } from 'path';

// ============================================================================
// TIPOS
// ============================================================================

interface InvestmentSignal {
  id: string;
  type: 'IPO' | 'NASDAQ_MOMENTUM' | 'FUNDING_ROUND' | 'B3_STOCK' | 'MERGER';
  title: string;
  description: string;
  score: number; // 0-100
  confidence: number; // 0-100
  potential_return: number; // %
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  ticker?: string;
  company: string;
  sector: string;
  market: string;
  price?: number;
  target_price?: number;
  funding_amount?: number;
  valuation?: number;
  indicators: {
    revenue_growth?: number;
    profit_margin?: number;
    market_momentum?: number;
    volume_spike?: number;
    insider_buying?: boolean;
  };
  recommendation: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'WATCH';
  reasoning: string[];
  generated_at: string;
}

// ============================================================================
// GERADORES DE SINAIS
// ============================================================================

function generateIPOSignals(): InvestmentSignal[] {
  const ipos = [
    {
      company: 'NovaTech AI',
      sector: 'Inteligência Artificial',
      description: 'Plataforma de IA generativa para empresas B2B',
      valuation: 2.5e9,
      score: 87,
      reasoning: [
        'Revenue growth de 340% YoY',
        'Contratos com 50+ Fortune 500',
        'Margem bruta de 78%',
        'CEO ex-Google Brain',
      ],
    },
    {
      company: 'GreenPower Energy',
      sector: 'Energia Renovável',
      description: 'Baterias de sódio para armazenamento em grid',
      valuation: 1.8e9,
      score: 82,
      reasoning: [
        'Tecnologia 40% mais barata que lítio',
        'Parceria com Eletrobras',
        'Backlog de R$ 500M',
        'Subsídios governamentais garantidos',
      ],
    },
    {
      company: 'HealthTech+',
      sector: 'Saúde Digital',
      description: 'Telemedicina com IA para diagnóstico',
      valuation: 950e6,
      score: 79,
      reasoning: [
        '2M+ pacientes ativos',
        'Precisão diagnóstica de 94%',
        'Convênios com 200+ operadoras',
        'Expansão LATAM confirmada',
      ],
    },
  ];

  return ipos.map((ipo, idx) => ({
    id: `IPO-${Date.now()}-${idx}`,
    type: 'IPO',
    title: `IPO ${ipo.company} - ${ipo.sector}`,
    description: ipo.description,
    score: ipo.score,
    confidence: 75 + Math.random() * 10,
    potential_return: 30 + Math.random() * 50,
    risk_level: ipo.score > 85 ? 'MEDIUM' : 'HIGH',
    company: ipo.company,
    sector: ipo.sector,
    market: 'B3',
    valuation: ipo.valuation,
    indicators: {
      revenue_growth: 200 + Math.random() * 200,
      profit_margin: -10 + Math.random() * 20,
      market_momentum: 70 + Math.random() * 20,
    },
    recommendation: ipo.score > 85 ? 'BUY' : 'WATCH',
    reasoning: ipo.reasoning,
    generated_at: new Date().toISOString(),
  }));
}

function generateNASDAQMomentumSignals(): InvestmentSignal[] {
  const stocks = [
    {
      ticker: 'NVDA',
      company: 'NVIDIA',
      sector: 'Semiconductors',
      price: 485.20,
      momentum: 8.5,
      reasoning: [
        'AI chip demand em alta histórica',
        'Guidance Q1 superou expectativas em 25%',
        'P/E ratio 65 ainda atrativo vs crescimento',
        'Goldman Sachs upgrade para $550',
      ],
    },
    {
      ticker: 'AVAV',
      company: 'AeroVironment',
      sector: 'Defense Tech',
      price: 189.30,
      momentum: 12.3,
      reasoning: [
        'Contrato $450M com DoD anunciado',
        'Drones Switchblade em alta demanda',
        'Revenue beat de 18% vs consensus',
        'Insider buying de $2.3M',
      ],
    },
    {
      ticker: 'MRNA',
      company: 'Moderna',
      sector: 'Biotech',
      price: 95.70,
      momentum: 6.7,
      reasoning: [
        'Vacina contra câncer fase 3 positiva',
        'FDA fast track aprovado',
        'Pipeline de 45 tratamentos mRNA',
        'Parceria com Merck expandida',
      ],
    },
    {
      ticker: 'TSLA',
      company: 'Tesla',
      sector: 'EV & Energy',
      price: 248.50,
      momentum: 5.2,
      reasoning: [
        'FSD v12 aprovação na China iminente',
        'Deliveries Q1 batem estimativas',
        'Margem em baterias +3pp',
        'Robotaxi launch confirmado para Q3',
      ],
    },
  ];

  return stocks.map((stock, idx) => ({
    id: `NASDAQ-${Date.now()}-${idx}`,
    type: 'NASDAQ_MOMENTUM',
    title: `${stock.ticker} Momentum +${stock.momentum.toFixed(1)}%`,
    description: `${stock.company} - ${stock.sector}`,
    score: 70 + stock.momentum * 2,
    confidence: 80 + Math.random() * 15,
    potential_return: stock.momentum + 5 + Math.random() * 10,
    risk_level: stock.momentum > 10 ? 'MEDIUM' : 'LOW',
    ticker: stock.ticker,
    company: stock.company,
    sector: stock.sector,
    market: 'NASDAQ',
    price: stock.price,
    target_price: stock.price * (1 + (stock.momentum + 8) / 100),
    indicators: {
      market_momentum: stock.momentum,
      volume_spike: 1.5 + Math.random() * 2,
      insider_buying: stock.momentum > 10,
    },
    recommendation: stock.momentum > 10 ? 'STRONG_BUY' : 'BUY',
    reasoning: stock.reasoning,
    generated_at: new Date().toISOString(),
  }));
}

function generateFundingRoundSignals(): InvestmentSignal[] {
  const rounds = [
    {
      company: 'Anduril Industries',
      sector: 'Defense AI',
      amount: 1.5e9,
      valuation: 8.5e9,
      reasoning: [
        'Series F led by Founders Fund',
        'Revenue anualizada $500M+',
        'Contratos militares EUA $2B backlog',
        'Lattice OS usado por 4 países',
      ],
    },
    {
      company: 'Nubank',
      sector: 'Fintech',
      amount: 750e6,
      valuation: 45e9,
      reasoning: [
        'Expansão México batendo metas',
        '85M clientes LATAM',
        'Lucratividade desde Q2/2023',
        'Berkshire aumentou posição em 15%',
      ],
    },
    {
      company: 'Shield AI',
      sector: 'Military Drones',
      amount: 500e6,
      valuation: 2.8e9,
      reasoning: [
        'Hivemind AI aprovado para F-16',
        'Partnership com Boeing anunciada',
        'Revenue 3x YoY',
        'Contratos DoD total $1.2B',
      ],
    },
  ];

  return rounds.map((round, idx) => ({
    id: `FUNDING-${Date.now()}-${idx}`,
    type: 'FUNDING_ROUND',
    title: `${round.company} - Series levanta $${(round.amount / 1e9).toFixed(1)}B`,
    description: `Funding round em ${round.sector}`,
    score: 75 + Math.random() * 15,
    confidence: 70 + Math.random() * 15,
    potential_return: 40 + Math.random() * 60,
    risk_level: 'HIGH',
    company: round.company,
    sector: round.sector,
    market: 'Private Equity',
    funding_amount: round.amount,
    valuation: round.valuation,
    indicators: {
      revenue_growth: 150 + Math.random() * 200,
      market_momentum: 80 + Math.random() * 15,
    },
    recommendation: 'WATCH',
    reasoning: round.reasoning,
    generated_at: new Date().toISOString(),
  }));
}

// ============================================================================
// FORMATAÇÃO E OUTPUT
// ============================================================================

function formatCurrency(value: number, currency: string = 'USD'): string {
  if (value >= 1e9) {
    return `${currency} ${(value / 1e9).toFixed(2)}B`;
  }
  if (value >= 1e6) {
    return `${currency} ${(value / 1e6).toFixed(1)}M`;
  }
  return `${currency} ${value.toFixed(2)}`;
}

function getRecommendationEmoji(rec: string): string {
  const emojis = {
    STRONG_BUY: '🚀',
    BUY: '✅',
    HOLD: '⏸️',
    WATCH: '👀',
  };
  return emojis[rec as keyof typeof emojis] || '❓';
}

function getRiskEmoji(risk: string): string {
  const emojis = {
    LOW: '🟢',
    MEDIUM: '🟡',
    HIGH: '🔴',
  };
  return emojis[risk as keyof typeof emojis] || '⚪';
}

function printSignal(signal: InvestmentSignal, rank: number): void {
  const scoreBar = '█'.repeat(Math.floor(signal.score / 5)) + '░'.repeat(20 - Math.floor(signal.score / 5));

  console.log(`\n${'═'.repeat(80)}`);
  console.log(`#${rank} | ${getRecommendationEmoji(signal.recommendation)} ${signal.title}`);
  console.log(`${'─'.repeat(80)}`);
  console.log(`📊 Score: ${scoreBar} ${signal.score.toFixed(0)}/100`);
  console.log(`🎯 Confidence: ${signal.confidence.toFixed(0)}% | ${getRiskEmoji(signal.risk_level)} Risk: ${signal.risk_level}`);
  console.log(`💰 Potential Return: ${signal.potential_return.toFixed(1)}%`);

  if (signal.ticker) {
    console.log(`📈 ${signal.ticker} | $${signal.price?.toFixed(2)} → $${signal.target_price?.toFixed(2)}`);
  }

  if (signal.valuation) {
    console.log(`💎 Valuation: ${formatCurrency(signal.valuation)}`);
  }

  if (signal.funding_amount) {
    console.log(`💵 Funding: ${formatCurrency(signal.funding_amount)}`);
  }

  console.log(`\n🏢 ${signal.company} | ${signal.sector} | ${signal.market}`);
  console.log(`\n✨ Why this matters:`);
  signal.reasoning.forEach((reason, idx) => {
    console.log(`   ${idx + 1}. ${reason}`);
  });
}

function saveToJSON(signals: InvestmentSignal[], outputDir: string): string {
  const timestamp = new Date().toISOString().split('T')[0];
  const filename = `sofia-signals-${timestamp}.json`;
  const filepath = join(outputDir, filename);

  const output = {
    generated_at: new Date().toISOString(),
    total_signals: signals.length,
    signals: signals,
    metadata: {
      version: '1.0.0',
      generator: 'sofia-finance-demo',
      markets: ['B3', 'NASDAQ', 'Private Equity'],
    },
  };

  writeFileSync(filepath, JSON.stringify(output, null, 2));
  return filepath;
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  console.log('\n');
  console.log('╔═══════════════════════════════════════════════════════════════════════════╗');
  console.log('║                                                                           ║');
  console.log('║            🌟 SOFIA FINANCE INTELLIGENCE HUB - DEMO MODE 🌟              ║');
  console.log('║                                                                           ║');
  console.log('║                    Real-time Investment Signal Generator                  ║');
  console.log('║                                                                           ║');
  console.log('╚═══════════════════════════════════════════════════════════════════════════╝');
  console.log('\n');

  console.log('⚡ Generating investment signals with realistic data...\n');

  // Gerar todos os sinais
  const allSignals: InvestmentSignal[] = [
    ...generateIPOSignals(),
    ...generateNASDAQMomentumSignals(),
    ...generateFundingRoundSignals(),
  ];

  // Ordenar por score
  allSignals.sort((a, b) => b.score - a.score);

  console.log(`📊 Generated ${allSignals.length} investment signals\n`);
  console.log(`💡 Showing TOP 10 by score:\n`);

  // Mostrar top 10
  allSignals.slice(0, 10).forEach((signal, idx) => {
    printSignal(signal, idx + 1);
  });

  // Salvar JSON
  const outputDir = join(__dirname, '../output');
  const filepath = saveToJSON(allSignals, outputDir);

  console.log(`\n${'═'.repeat(80)}\n`);
  console.log(`✅ SUCCESS! Signals saved to:`);
  console.log(`   📁 ${filepath}`);
  console.log(`\n💡 Next steps:`);
  console.log(`   1. Review signals in JSON: cat ${filepath} | jq`);
  console.log(`   2. Setup database: npm run migrate:market`);
  console.log(`   3. Collect real data: npm run collect:brazil`);
  console.log(`   4. Generate from DB: npm run signals`);
  console.log(`\n🚀 Happy investing!\n`);
}

main().catch(console.error);
