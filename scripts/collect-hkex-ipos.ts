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
 * Sofia Pulse - HKEX IPOs Collector
 *
 * Coleta dados de IPOs da Hong Kong Stock Exchange (HKEX)
 *
 * POR QUE HKEX É CRÍTICA:
 * - Principal exchange para empresas chinesas listarem globalmente
 * - Alibaba, Tencent, Xiaomi, Meituan listadas aqui
 * - Indicador de saúde do mercado de capitais chinês
 * - Gateway entre China e investidores internacionais
 *
 * FONTE:
 * - URL: https://www.hkex.com.hk
 * - API: Market Data API (delayed data gratuito)
 * - Cobertura: Main Board + GEM (Growth Enterprise Market)
 */

import { Client } from 'pg';
import * as dotenv from 'dotenv';

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

interface HKEXipo {
  ticker: string;
  company: string;
  company_cn?: string;
  exchange: string; // 'HKEX Main' | 'HKEX GEM'
  sector: string;
  ipo_date: string;
  ipo_price_hkd: number;
  amount_raised_usd: number;
  market_cap_usd: number;
  underwriters?: string[];
  description?: string;
}

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

async function createTableIfNotExists(client: Client): Promise<void> {
  const createTableQuery = `
    CREATE TABLE IF NOT EXISTS hkex_ipos (
      id SERIAL PRIMARY KEY,
      ticker VARCHAR(20) NOT NULL,
      company VARCHAR(255) NOT NULL,
      company_cn VARCHAR(255),
      exchange VARCHAR(20), -- 'HKEX Main' | 'HKEX GEM'
      sector VARCHAR(100),
      ipo_date DATE,
      ipo_price_hkd DECIMAL(12,2),
      amount_raised_usd BIGINT,
      market_cap_usd BIGINT,
      underwriters TEXT[],
      description TEXT,
      collected_at TIMESTAMP DEFAULT NOW(),
      UNIQUE(ticker, ipo_date)
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_hkex_ipo_date
      ON hkex_ipos(ipo_date DESC);

    CREATE INDEX IF NOT EXISTS idx_hkex_sector
      ON hkex_ipos(sector);

    CREATE INDEX IF NOT EXISTS idx_hkex_market_cap
      ON hkex_ipos(market_cap_usd DESC);
  `;

  await client.query(createTableQuery);
  console.log('✅ Table hkex_ipos ready');
}

async function insertIPO(client: Client, ipo: HKEXipo): Promise<void> {
  const insertQuery = `
    INSERT INTO hkex_ipos (
      ticker, company, company_cn, exchange, sector,
      ipo_date, ipo_price_hkd, amount_raised_usd,
      market_cap_usd, underwriters, description
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
    ON CONFLICT (ticker, ipo_date)
    DO UPDATE SET
      market_cap_usd = EXCLUDED.market_cap_usd,
      collected_at = NOW();
  `;

  await client.query(insertQuery, [
    ipo.ticker,
    ipo.company,
    ipo.company_cn || null,
    ipo.exchange,
    ipo.sector,
    ipo.ipo_date,
    ipo.ipo_price_hkd,
    ipo.amount_raised_usd,
    ipo.market_cap_usd,
    ipo.underwriters || [],
    ipo.description || null,
  ]);
}

// ============================================================================
// COLLECTORS
// ============================================================================

/**
 * Mock data - Em produção, isso seria scraping do HKEX ou API
 * Dados baseados em IPOs reais recentes de HKEX
 */
async function collectHKEXipos(): Promise<HKEXipo[]> {
  console.log('🏦 Collecting HKEX IPOs...');
  console.log('   (Mock data - production would scrape HKEX website)');

  const currentYear = new Date().getFullYear();

  const mockIPOs: HKEXipo[] = [
    // Tech Giants
    {
      ticker: '9988.HK',
      company: 'Alibaba Group',
      company_cn: '阿里巴巴集团',
      exchange: 'HKEX Main',
      sector: 'E-commerce',
      ipo_date: '2019-11-26',
      ipo_price_hkd: 176.0,
      amount_raised_usd: 13000000000, // $13B
      market_cap_usd: 250000000000,
      underwriters: ['Morgan Stanley', 'CICC', 'JPMorgan'],
      description: 'Largest e-commerce platform in China',
    },
    {
      ticker: '1810.HK',
      company: 'Xiaomi Corporation',
      company_cn: '小米集团',
      exchange: 'HKEX Main',
      sector: 'Consumer Electronics',
      ipo_date: '2018-07-09',
      ipo_price_hkd: 17.0,
      amount_raised_usd: 4700000000,
      market_cap_usd: 45000000000,
      underwriters: ['Goldman Sachs', 'Morgan Stanley', 'CLSA'],
      description: 'Smartphone manufacturer and IoT ecosystem',
    },

    // Recent Tech IPOs (2023-2024)
    {
      ticker: '2333.HK',
      company: 'Great Wall Motor',
      company_cn: '长城汽车',
      exchange: 'HKEX Main',
      sector: 'Electric Vehicles',
      ipo_date: '2023-03-15',
      ipo_price_hkd: 28.5,
      amount_raised_usd: 2100000000,
      market_cap_usd: 18000000000,
      underwriters: ['CICC', 'Morgan Stanley'],
      description: 'Chinese EV manufacturer',
    },
    {
      ticker: '2015.HK',
      company: 'Li Auto Inc.',
      company_cn: '理想汽车',
      exchange: 'HKEX Main',
      sector: 'Electric Vehicles',
      ipo_date: '2021-08-12',
      ipo_price_hkd: 118.0,
      amount_raised_usd: 1500000000,
      market_cap_usd: 22000000000,
      underwriters: ['Goldman Sachs', 'UBS'],
      description: 'Premium EV manufacturer',
    },

    // Biotech
    {
      ticker: '2269.HK',
      company: 'WuXi Biologics',
      company_cn: '药明生物',
      exchange: 'HKEX Main',
      sector: 'Biotechnology',
      ipo_date: '2017-06-13',
      ipo_price_hkd: 6.5,
      amount_raised_usd: 420000000,
      market_cap_usd: 8500000000,
      underwriters: ['Morgan Stanley', 'CICC'],
      description: 'Biologic drug CDMO leader',
    },
    {
      ticker: '1801.HK',
      company: 'Innovent Biologics',
      company_cn: '信达生物',
      exchange: 'HKEX Main',
      sector: 'Biotechnology',
      ipo_date: '2018-10-31',
      ipo_price_hkd: 16.5,
      amount_raised_usd: 420000000,
      market_cap_usd: 5200000000,
      underwriters: ['Goldman Sachs', 'JPMorgan'],
      description: 'Biopharmaceutical company',
    },

    // Fintech
    {
      ticker: '6690.HK',
      company: 'Haier Smart Home',
      company_cn: '海尔智家',
      exchange: 'HKEX Main',
      sector: 'Smart Home',
      ipo_date: '2020-12-23',
      ipo_price_hkd: 25.8,
      amount_raised_usd: 870000000,
      market_cap_usd: 12000000000,
      underwriters: ['CICC', 'HSBC'],
      description: 'Smart home appliances and IoT',
    },

    // Recent 2024 IPOs (Mock future data)
    {
      ticker: `${9000 + Math.floor(Math.random() * 100)}.HK`,
      company: 'ByteDance AI Division',
      company_cn: '字节跳动人工智能',
      exchange: 'HKEX Main',
      sector: 'Artificial Intelligence',
      ipo_date: `${currentYear}-06-15`,
      ipo_price_hkd: 88.0,
      amount_raised_usd: 5000000000,
      market_cap_usd: 80000000000,
      underwriters: ['Morgan Stanley', 'Goldman Sachs', 'CICC'],
      description: 'AI and machine learning platform (hypothetical)',
    },
    {
      ticker: `${9100 + Math.floor(Math.random() * 100)}.HK`,
      company: 'Contemporary Energy Storage',
      company_cn: '当代储能科技',
      exchange: 'HKEX Main',
      sector: 'Energy Storage',
      ipo_date: `${currentYear}-09-20`,
      ipo_price_hkd: 45.5,
      amount_raised_usd: 3200000000,
      market_cap_usd: 28000000000,
      underwriters: ['CICC', 'UBS', 'HSBC'],
      description: 'Next-gen battery technology (hypothetical)',
    },

    // GEM (Growth Enterprise Market) - Smaller companies
    {
      ticker: '8888.HK',
      company: 'China Renaissance',
      company_cn: '华兴资本',
      exchange: 'HKEX GEM',
      sector: 'Financial Services',
      ipo_date: '2018-09-27',
      ipo_price_hkd: 22.0,
      amount_raised_usd: 350000000,
      market_cap_usd: 1800000000,
      underwriters: ['CICC'],
      description: 'Investment banking for new economy',
    },
  ];

  return mockIPOs;
}

// ============================================================================
// MAIN FUNCTION
// ============================================================================

async function main() {
  console.log('🚀 Sofia Pulse - HKEX IPOs Collector');
  console.log('='.repeat(60));
  console.log('');
  console.log('🏦 WHY HKEX MATTERS:');
  console.log('   - Gateway for Chinese companies to global capital');
  console.log('   - Alibaba, Tencent, Xiaomi listed here');
  console.log('   - Indicator of China tech market health');
  console.log('   - Bridge between China and international investors');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    await createTableIfNotExists(client);

    console.log('');
    console.log('📊 Collecting IPOs...');
    console.log('');

    const ipos = await collectHKEXipos();
    console.log(`   ✅ Collected ${ipos.length} IPOs`);
    console.log('');

    console.log('💾 Inserting into database...');
    for (const ipo of ipos) {
      await insertIPO(client, ipo);
    }
    console.log(`✅ ${ipos.length} IPOs inserted/updated`);
    console.log('');

    // Summary
    console.log('📊 Summary by sector:');
    console.log('');

    const summaryQuery = `
      SELECT
        sector,
        COUNT(*) as ipo_count,
        SUM(amount_raised_usd) / 1000000000 as total_raised_billions,
        AVG(market_cap_usd) / 1000000000 as avg_market_cap_billions
      FROM hkex_ipos
      GROUP BY sector
      ORDER BY total_raised_billions DESC;
    `;

    const summary = await client.query(summaryQuery);

    summary.rows.forEach((row) => {
      console.log(`   ${row.sector}:`);
      console.log(`      IPOs: ${row.ipo_count}`);
      console.log(`      Total Raised: $${parseFloat(row.total_raised_billions).toFixed(1)}B`);
      console.log(`      Avg Market Cap: $${parseFloat(row.avg_market_cap_billions).toFixed(1)}B`);
      console.log('');
    });

    console.log('✅ Collection complete!');
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

// ============================================================================
// DRY RUN MODE
// ============================================================================

async function dryRun() {
  console.log('🚀 Sofia Pulse - HKEX IPOs Collector (DRY RUN)');
  console.log('='.repeat(60));
  console.log('');
  console.log('🏦 WHY HKEX MATTERS:');
  console.log('   - Gateway for Chinese companies to global capital');
  console.log('   - Alibaba, Tencent, Xiaomi listed here');
  console.log('   - Indicator of China tech market health');
  console.log('   - Bridge between China and international investors');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const ipos = await collectHKEXipos();
  console.log(`✅ Collected ${ipos.length} IPOs`);
  console.log('');

  // Group by sector
  const bySector = ipos.reduce((acc, ipo) => {
    if (!acc[ipo.sector]) acc[ipo.sector] = [];
    acc[ipo.sector].push(ipo);
    return acc;
  }, {} as Record<string, HKEXipo[]>);

  console.log('📊 IPOs by Sector:');
  console.log('');

  Object.entries(bySector)
    .sort(([, a], [, b]) => {
      const aTotal = a.reduce((sum, i) => sum + i.amount_raised_usd, 0);
      const bTotal = b.reduce((sum, i) => sum + i.amount_raised_usd, 0);
      return bTotal - aTotal;
    })
    .forEach(([sector, sectorIPOs]) => {
      const totalRaised = sectorIPOs.reduce((sum, i) => sum + i.amount_raised_usd, 0);
      console.log(`   ${sector}: ${sectorIPOs.length} IPOs`);
      console.log(`      Total Raised: $${(totalRaised / 1e9).toFixed(1)}B`);
      console.log(`      Companies: ${sectorIPOs.map((i) => i.company).join(', ')}`);
      console.log('');
    });

  // Show largest IPOs
  console.log('💰 Largest IPOs:');
  console.log('');

  const sorted = [...ipos].sort((a, b) => b.amount_raised_usd - a.amount_raised_usd);
  sorted.slice(0, 5).forEach((ipo, idx) => {
    console.log(`   ${idx + 1}. ${ipo.company} (${ipo.ticker})`);
    console.log(`      Amount Raised: $${(ipo.amount_raised_usd / 1e9).toFixed(1)}B`);
    console.log(`      Market Cap: $${(ipo.market_cap_usd / 1e9).toFixed(1)}B`);
    console.log(`      IPO Date: ${ipo.ipo_date}`);
    console.log(`      Sector: ${ipo.sector}`);
    console.log('');
  });

  console.log('='.repeat(60));
  console.log('');
  console.log('💡 MARKET INSIGHTS:');
  console.log('');

  const totalRaised = ipos.reduce((sum, i) => sum + i.amount_raised_usd, 0);
  const avgRaised = totalRaised / ipos.length;

  console.log(`   Total Capital Raised: $${(totalRaised / 1e9).toFixed(1)}B`);
  console.log(`   Average IPO Size: $${(avgRaised / 1e9).toFixed(1)}B`);
  console.log(`   Top Sector: ${Object.keys(bySector)[0]}`);
  console.log('');
  console.log('   HKEX is THE gateway for Chinese tech to global markets');
  console.log('   IPO activity correlates with investor confidence in China');
  console.log('');

  console.log('🎯 CORRELATIONS:');
  console.log('');
  console.log('   - IPO volume → Market sentiment');
  console.log('   - Sector focus → Strategic priorities');
  console.log('   - Valuations → Tech bubble indicators');
  console.log('   - Link to: WIPO patents, funding rounds, research');
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
        console.log('💡 TIP: Run with --dry-run to see sample data:');
        console.log('   npm run collect:hkex -- --dry-run');
        console.log('');
        process.exit(1);
      }
      throw error;
    });
  }
}

export { collectHKEXipos, dryRun };
