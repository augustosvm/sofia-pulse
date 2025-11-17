#!/usr/bin/env tsx

/**
 * Sofia Pulse - AI Companies Tracker
 *
 * Rastreia empresas de IA globalmente com foco em LLMs, Computer Vision, e AI Chips
 *
 * POR QUE TRACKING DE EMPRESAS DE IA É CRÍTICO:
 * - Corrida IA: USA vs China
 * - $100B+ investidos em 2023-2024
 * - OpenAI ($80B valuation), Anthropic ($15B), Mistral ($2B)
 * - China: Baidu, Alibaba, ByteDance competindo
 * - Chips: NVIDIA, AMD, startups
 *
 * CATEGORIAS:
 * - LLMs (Large Language Models)
 * - Computer Vision
 * - AI Chips/Hardware
 * - AI Drug Discovery
 * - Robotics
 * - AutoML/MLOps
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

interface AICompany {
  name: string;
  country: string;
  founded_year: number;
  category: string; // LLM, Computer Vision, AI Chips, etc
  total_funding_usd: number;
  last_valuation_usd?: number;
  last_funding_date?: string;
  funding_stage: string; // Seed, Series A-F, Public
  model_names?: string[]; // GPT-4, Claude, etc
  products?: string[];
  investors: string[];
  employee_count?: number;
  status: 'active' | 'acquired' | 'public' | 'defunct';
  acquired_by?: string;
  ipo_date?: string;
  description: string;
}

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

async function createTableIfNotExists(client: Client): Promise<void> {
  const createTableQuery = `
    CREATE TABLE IF NOT EXISTS ai_companies (
      id SERIAL PRIMARY KEY,
      name VARCHAR(255) UNIQUE NOT NULL,
      country VARCHAR(100),
      founded_year INT,
      category VARCHAR(100),
      total_funding_usd BIGINT,
      last_valuation_usd BIGINT,
      last_funding_date DATE,
      funding_stage VARCHAR(50),
      model_names TEXT[],
      products TEXT[],
      investors TEXT[],
      employee_count INT,
      status VARCHAR(20),
      acquired_by VARCHAR(255),
      ipo_date DATE,
      description TEXT,
      collected_at TIMESTAMP DEFAULT NOW()
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_ai_companies_country
      ON ai_companies(country);

    CREATE INDEX IF NOT EXISTS idx_ai_companies_category
      ON ai_companies(category);

    CREATE INDEX IF NOT EXISTS idx_ai_companies_valuation
      ON ai_companies(last_valuation_usd DESC NULLS LAST);

    CREATE INDEX IF NOT EXISTS idx_ai_companies_status
      ON ai_companies(status);
  `;

  await client.query(createTableQuery);
  console.log('✅ Table ai_companies ready');
}

async function insertCompany(client: Client, company: AICompany): Promise<void> {
  const insertQuery = `
    INSERT INTO ai_companies (
      name, country, founded_year, category,
      total_funding_usd, last_valuation_usd, last_funding_date,
      funding_stage, model_names, products, investors,
      employee_count, status, acquired_by, ipo_date, description
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
    ON CONFLICT (name)
    DO UPDATE SET
      total_funding_usd = EXCLUDED.total_funding_usd,
      last_valuation_usd = EXCLUDED.last_valuation_usd,
      last_funding_date = EXCLUDED.last_funding_date,
      funding_stage = EXCLUDED.funding_stage,
      employee_count = EXCLUDED.employee_count,
      status = EXCLUDED.status,
      collected_at = NOW();
  `;

  await client.query(insertQuery, [
    company.name,
    company.country,
    company.founded_year,
    company.category,
    company.total_funding_usd,
    company.last_valuation_usd || null,
    company.last_funding_date || null,
    company.funding_stage,
    company.model_names || [],
    company.products || [],
    company.investors,
    company.employee_count || null,
    company.status,
    company.acquired_by || null,
    company.ipo_date || null,
    company.description,
  ]);
}

// ============================================================================
// COLLECTORS
// ============================================================================

async function collectAICompanies(): Promise<AICompany[]> {
  console.log('🤖 Collecting AI companies globally...');
  console.log('   (Mock data - production would use Crunchbase/PitchBook APIs)');

  const companies: AICompany[] = [
    // ========== USA - LLMs ==========
    {
      name: 'OpenAI',
      country: 'USA',
      founded_year: 2015,
      category: 'LLM',
      total_funding_usd: 11300000000, // $11.3B
      last_valuation_usd: 80000000000, // $80B
      last_funding_date: '2024-10-01',
      funding_stage: 'Series C',
      model_names: ['GPT-3.5', 'GPT-4', 'GPT-4 Turbo', 'DALL-E 3'],
      products: ['ChatGPT', 'API Platform', 'Enterprise'],
      investors: ['Microsoft', 'Sequoia Capital', 'Andreessen Horowitz', 'Khosla Ventures'],
      employee_count: 750,
      status: 'active',
      description: 'Leading AI research lab creating GPT models and ChatGPT',
    },
    {
      name: 'Anthropic',
      country: 'USA',
      founded_year: 2021,
      category: 'LLM',
      total_funding_usd: 7300000000, // $7.3B
      last_valuation_usd: 15000000000, // $15B (est)
      last_funding_date: '2024-03-15',
      funding_stage: 'Series C',
      model_names: ['Claude', 'Claude 2', 'Claude 3 Opus/Sonnet/Haiku'],
      products: ['Claude API', 'Claude Pro'],
      investors: ['Google', 'Spark Capital', 'Salesforce Ventures'],
      employee_count: 500,
      status: 'active',
      description: 'AI safety focused company building Claude LLMs',
    },
    {
      name: 'Cohere',
      country: 'Canada',
      founded_year: 2019,
      category: 'LLM',
      total_funding_usd: 445000000,
      last_valuation_usd: 2200000000,
      last_funding_date: '2023-06-01',
      funding_stage: 'Series C',
      model_names: ['Command', 'Embed', 'Generate'],
      products: ['Enterprise LLM Platform'],
      investors: ['NVIDIA', 'Salesforce Ventures', 'Index Ventures'],
      employee_count: 300,
      status: 'active',
      description: 'Enterprise-focused LLM platform',
    },
    {
      name: 'Inflection AI',
      country: 'USA',
      founded_year: 2022,
      category: 'LLM',
      total_funding_usd: 1500000000,
      last_valuation_usd: 4000000000,
      last_funding_date: '2023-06-29',
      funding_stage: 'Series A',
      model_names: ['Inflection-1', 'Inflection-2'],
      products: ['Pi (Personal Intelligence)'],
      investors: ['Microsoft', 'Reid Hoffman', 'Bill Gates', 'NVIDIA'],
      employee_count: 100,
      status: 'active',
      description: 'Building personal AI assistant Pi',
    },

    // ========== China - LLMs ==========
    {
      name: 'Baidu AI',
      country: 'China',
      founded_year: 2000,
      category: 'LLM',
      total_funding_usd: 0, // Public company
      last_valuation_usd: 45000000000, // Market cap portion
      funding_stage: 'Public',
      model_names: ['ERNIE Bot', 'ERNIE 3.0', 'ERNIE 4.0'],
      products: ['ERNIE Bot', 'Apollo (autonomous driving)'],
      investors: ['Public (NASDAQ: BIDU)'],
      employee_count: 38000,
      status: 'public',
      description: 'Chinese tech giant with ERNIE LLM competing with GPT',
    },
    {
      name: 'Alibaba DAMO Academy',
      country: 'China',
      founded_year: 2017,
      category: 'LLM',
      total_funding_usd: 0, // Part of Alibaba
      last_valuation_usd: 30000000000, // Estimated
      funding_stage: 'Corporate',
      model_names: ['Tongyi Qianwen', 'Qwen'],
      products: ['Tongyi Qianwen chatbot'],
      investors: ['Alibaba Group'],
      employee_count: 5000,
      status: 'active',
      description: 'Alibaba research institute building Tongyi Qianwen LLM',
    },
    {
      name: 'Zhipu AI',
      country: 'China',
      founded_year: 2019,
      category: 'LLM',
      total_funding_usd: 340000000,
      last_valuation_usd: 1000000000,
      last_funding_date: '2023-10-01',
      funding_stage: 'Series B',
      model_names: ['GLM-130B', 'ChatGLM'],
      products: ['ChatGLM'],
      investors: ['Tencent', 'Alibaba', 'Sequoia China'],
      employee_count: 200,
      status: 'active',
      description: 'Chinese LLM startup with GLM models',
    },
    {
      name: 'Moonshot AI',
      country: 'China',
      founded_year: 2023,
      category: 'LLM',
      total_funding_usd: 1000000000, // $1B
      last_valuation_usd: 2500000000,
      last_funding_date: '2024-02-01',
      funding_stage: 'Series A',
      model_names: ['Kimi'],
      products: ['Kimi Chat'],
      investors: ['Alibaba', 'HongShan (Sequoia China)'],
      employee_count: 150,
      status: 'active',
      description: 'Fast-growing Chinese LLM startup',
    },
    {
      name: '01.AI',
      country: 'China',
      founded_year: 2023,
      category: 'LLM',
      total_funding_usd: 200000000,
      last_valuation_usd: 1000000000,
      last_funding_date: '2023-11-01',
      funding_stage: 'Seed',
      model_names: ['Yi-34B', 'Yi-6B'],
      products: ['Yi models'],
      investors: ['Sinovation Ventures'],
      employee_count: 80,
      status: 'active',
      description: 'Founded by Kai-Fu Lee, building Yi LLM family',
    },

    // ========== Europe - LLMs ==========
    {
      name: 'Mistral AI',
      country: 'France',
      founded_year: 2023,
      category: 'LLM',
      total_funding_usd: 640000000,
      last_valuation_usd: 2000000000,
      last_funding_date: '2023-12-01',
      funding_stage: 'Series A',
      model_names: ['Mistral 7B', 'Mixtral 8x7B'],
      products: ['Open-source models', 'Enterprise platform'],
      investors: ['Andreessen Horowitz', 'Lightspeed Venture Partners', 'NVIDIA'],
      employee_count: 60,
      status: 'active',
      description: 'European open-source LLM leader',
    },
    {
      name: 'Aleph Alpha',
      country: 'Germany',
      founded_year: 2019,
      category: 'LLM',
      total_funding_usd: 130000000,
      last_valuation_usd: 500000000,
      last_funding_date: '2022-11-01',
      funding_stage: 'Series B',
      model_names: ['Luminous'],
      products: ['Luminous models', 'Enterprise AI'],
      investors: ['Innovation Park AI', 'Lakestar'],
      employee_count: 150,
      status: 'active',
      description: 'German enterprise-focused LLM company',
    },

    // ========== AI Chips/Hardware ==========
    {
      name: 'Cerebras',
      country: 'USA',
      founded_year: 2016,
      category: 'AI Chips',
      total_funding_usd: 720000000,
      last_valuation_usd: 4000000000,
      last_funding_date: '2021-11-01',
      funding_stage: 'Series F',
      products: ['Wafer-Scale Engine (WSE-2)', 'CS-2 system'],
      investors: ['Benchmark', 'Eclipse Ventures', 'Coatue'],
      employee_count: 400,
      status: 'active',
      description: 'Wafer-scale AI chip manufacturer',
    },
    {
      name: 'Graphcore',
      country: 'UK',
      founded_year: 2016,
      category: 'AI Chips',
      total_funding_usd: 710000000,
      last_valuation_usd: 2500000000,
      last_funding_date: '2020-12-01',
      funding_stage: 'Series E',
      products: ['IPU (Intelligence Processing Unit)'],
      investors: ['Sequoia Capital', 'Baillie Gifford'],
      employee_count: 600,
      status: 'active',
      description: 'IPU chips for AI training and inference',
    },
    {
      name: 'SambaNova Systems',
      country: 'USA',
      founded_year: 2017,
      category: 'AI Chips',
      total_funding_usd: 1100000000,
      last_valuation_usd: 5000000000,
      last_funding_date: '2021-04-01',
      funding_stage: 'Series D',
      products: ['DataScale systems', 'RDU chips'],
      investors: ['SoftBank Vision Fund', 'Google Ventures', 'Intel Capital'],
      employee_count: 500,
      status: 'active',
      description: 'AI infrastructure company with custom chips',
    },

    // ========== Computer Vision ==========
    {
      name: 'Midjourney',
      country: 'USA',
      founded_year: 2021,
      category: 'Computer Vision',
      total_funding_usd: 0, // Bootstrapped
      last_valuation_usd: 10000000000, // Estimated
      funding_stage: 'Bootstrapped',
      products: ['Midjourney (text-to-image)'],
      investors: ['Bootstrapped'],
      employee_count: 40,
      status: 'active',
      description: 'Leading text-to-image AI, fully bootstrapped',
    },
    {
      name: 'Stability AI',
      country: 'UK',
      founded_year: 2020,
      category: 'Computer Vision',
      total_funding_usd: 101000000,
      last_valuation_usd: 1000000000,
      last_funding_date: '2022-10-01',
      funding_stage: 'Seed',
      model_names: ['Stable Diffusion', 'SDXL'],
      products: ['Stable Diffusion', 'DreamStudio'],
      investors: ['Coatue', 'Lightspeed Venture Partners'],
      employee_count: 150,
      status: 'active',
      description: 'Open-source Stable Diffusion image generation',
    },
    {
      name: 'Runway',
      country: 'USA',
      founded_year: 2018,
      category: 'Computer Vision',
      total_funding_usd: 237000000,
      last_valuation_usd: 1500000000,
      last_funding_date: '2023-06-01',
      funding_stage: 'Series C',
      products: ['Gen-2 (text-to-video)', 'Video editing AI'],
      investors: ['Google', 'NVIDIA', 'Salesforce Ventures'],
      employee_count: 120,
      status: 'active',
      description: 'AI video generation and editing platform',
    },
    {
      name: 'SenseTime',
      country: 'China',
      founded_year: 2014,
      category: 'Computer Vision',
      total_funding_usd: 5200000000,
      last_valuation_usd: 3000000000, // Post-IPO
      last_funding_date: '2021-12-30',
      funding_stage: 'Public',
      ipo_date: '2021-12-30',
      products: ['Face recognition', 'Smart city', 'Autonomous driving'],
      investors: ['Public (HKEX: 0020)'],
      employee_count: 5000,
      status: 'public',
      description: 'Chinese computer vision giant, public company',
    },

    // ========== AI Drug Discovery ==========
    {
      name: 'Recursion Pharmaceuticals',
      country: 'USA',
      founded_year: 2013,
      category: 'AI Drug Discovery',
      total_funding_usd: 674000000,
      last_valuation_usd: 2000000000,
      funding_stage: 'Public',
      ipo_date: '2021-04-16',
      products: ['Recursion OS', 'Drug discovery platform'],
      investors: ['Public (NASDAQ: RXRX)'],
      employee_count: 350,
      status: 'public',
      description: 'AI-powered drug discovery platform',
    },
    {
      name: 'Insilico Medicine',
      country: 'Hong Kong/USA',
      founded_year: 2014,
      category: 'AI Drug Discovery',
      total_funding_usd: 410000000,
      last_valuation_usd: 1700000000,
      last_funding_date: '2023-06-01',
      funding_stage: 'Series D',
      products: ['Pharma.AI platform'],
      investors: ['Warburg Pincus', 'CPE'],
      employee_count: 300,
      status: 'active',
      description: 'AI for drug discovery and aging research',
    },
  ];

  return companies;
}

// ============================================================================
// MAIN FUNCTION
// ============================================================================

async function main() {
  console.log('🚀 Sofia Pulse - AI Companies Tracker');
  console.log('='.repeat(60));
  console.log('');
  console.log('🤖 WHY AI COMPANIES TRACKING IS CRITICAL:');
  console.log('   - AI Race: USA vs China ($100B+ invested)');
  console.log('   - OpenAI: $80B valuation (ChatGPT)');
  console.log('   - Anthropic: $15B (Claude)');
  console.log('   - China: Baidu, Alibaba, ByteDance competing');
  console.log('   - NVIDIA enabling all with H100 GPUs');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    await createTableIfNotExists(client);

    console.log('');
    console.log('📊 Collecting companies...');
    console.log('');

    const companies = await collectAICompanies();
    console.log(`   ✅ Collected ${companies.length} AI companies`);
    console.log('');

    console.log('💾 Inserting into database...');
    for (const company of companies) {
      await insertCompany(client, company);
    }
    console.log(`✅ ${companies.length} companies inserted/updated`);
    console.log('');

    // Summary
    console.log('📊 Summary by category:');
    console.log('');

    const summaryQuery = `
      SELECT
        category,
        COUNT(*) as company_count,
        SUM(total_funding_usd) / 1e9 as total_funding_billions,
        AVG(last_valuation_usd) / 1e9 as avg_valuation_billions
      FROM ai_companies
      GROUP BY category
      ORDER BY total_funding_billions DESC;
    `;

    const summary = await client.query(summaryQuery);

    summary.rows.forEach((row) => {
      console.log(`   ${row.category}:`);
      console.log(`      Companies: ${row.company_count}`);
      console.log(`      Total Funding: $${parseFloat(row.total_funding_billions || 0).toFixed(1)}B`);
      console.log(`      Avg Valuation: $${parseFloat(row.avg_valuation_billions || 0).toFixed(1)}B`);
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
  console.log('🚀 Sofia Pulse - AI Companies Tracker (DRY RUN)');
  console.log('='.repeat(60));
  console.log('');
  console.log('🤖 AI RACE: USA vs CHINA');
  console.log('');

  const companies = await collectAICompanies();
  console.log(`✅ Tracking ${companies.length} AI companies globally`);
  console.log('');

  // By country
  const byCountry = companies.reduce((acc, c) => {
    if (!acc[c.country]) acc[c.country] = [];
    acc[c.country].push(c);
    return acc;
  }, {} as Record<string, AICompany[]>);

  console.log('🌍 Companies by Country:');
  console.log('');

  Object.entries(byCountry)
    .sort(([, a], [, b]) => b.length - a.length)
    .forEach(([country, comps]) => {
      const totalFunding = comps.reduce((sum, c) => sum + c.total_funding_usd, 0);
      console.log(`   ${country}: ${comps.length} companies, $${(totalFunding / 1e9).toFixed(1)}B funding`);
    });

  console.log('');
  console.log('💰 Top 10 by Valuation:');
  console.log('');

  const sorted = [...companies]
    .filter(c => c.last_valuation_usd)
    .sort((a, b) => (b.last_valuation_usd || 0) - (a.last_valuation_usd || 0));

  sorted.slice(0, 10).forEach((company, idx) => {
    console.log(`   ${idx + 1}. ${company.name} (${company.country})`);
    console.log(`      Valuation: $${(company.last_valuation_usd! / 1e9).toFixed(1)}B`);
    console.log(`      Category: ${company.category}`);
    if (company.model_names && company.model_names.length > 0) {
      console.log(`      Models: ${company.model_names.join(', ')}`);
    }
    console.log('');
  });

  // By category
  const byCategory = companies.reduce((acc, c) => {
    if (!acc[c.category]) acc[c.category] = [];
    acc[c.category].push(c);
    return acc;
  }, {} as Record<string, AICompany[]>);

  console.log('📊 Companies by Category:');
  console.log('');

  Object.entries(byCategory)
    .sort(([, a], [, b]) => b.length - a.length)
    .forEach(([cat, comps]) => {
      console.log(`   ${cat}: ${comps.length} companies`);
      console.log(`      Companies: ${comps.map(c => c.name).join(', ')}`);
      console.log('');
    });

  console.log('='.repeat(60));
  console.log('');
  console.log('💡 KEY INSIGHTS:');
  console.log('');

  const totalFunding = companies.reduce((sum, c) => sum + c.total_funding_usd, 0);
  const usaFunding = companies.filter(c => c.country === 'USA').reduce((sum, c) => sum + c.total_funding_usd, 0);
  const chinaFunding = companies.filter(c => c.country === 'China').reduce((sum, c) => sum + c.total_funding_usd, 0);

  console.log(`   Total Funding Tracked: $${(totalFunding / 1e9).toFixed(1)}B`);
  console.log(`   USA Funding: $${(usaFunding / 1e9).toFixed(1)}B`);
  console.log(`   China Funding: $${(chinaFunding / 1e9).toFixed(1)}B`);
  console.log('');
  console.log('   OpenAI leads with $80B valuation');
  console.log('   Mistral AI: European dark horse at $2B');
  console.log('   China LLM market fragmented but growing fast');
  console.log('   AI Chips: Critical bottleneck, few players');
  console.log('');

  console.log('🎯 CORRELATIONS:');
  console.log('');
  console.log('   - Company funding → GPU demand (NVIDIA revenue)');
  console.log('   - Valuations → ArXiv breakthrough papers');
  console.log('   - China vs USA funding → geopolitical AI race');
  console.log('   - Employee growth → talent competition');
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
        console.log('   npm run collect:ai-companies -- --dry-run');
        console.log('');
        process.exit(1);
      }
      throw error;
    });
  }
}

export { collectAICompanies, dryRun };
