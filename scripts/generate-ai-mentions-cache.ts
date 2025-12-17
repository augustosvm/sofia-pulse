#!/usr/bin/env npx tsx
import { Pool } from 'pg';
import * as fs from 'fs';
import * as path from 'path';
import * as dotenv from 'dotenv';

dotenv.config();

const pool = new Pool({
  host: process.env.POSTGRES_HOST || process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || process.env.DB_PORT || '5432'),
  user: process.env.POSTGRES_USER || process.env.DB_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD || process.env.DB_PASSWORD || '',
  database: process.env.POSTGRES_DB || process.env.DB_NAME || 'sofia_db',
});

interface AIModel {
  name: string;
  count: number;
  percentage: number;
}

interface RegionalAI {
  total_papers: number;
  percentage_of_world: number;
  top_models: AIModel[];
}

interface AICache {
  brazil: RegionalAI;
  latam: RegionalAI;
  north_america: RegionalAI;
  europe: RegionalAI;
  asia: RegionalAI;
  oceania: RegionalAI;
  africa: RegionalAI;
  world: RegionalAI;
  period: string;
  generated_at: string;
}

// AI Models to track
const AI_MODELS = [
  'GPT', 'ChatGPT', 'GPT-4', 'GPT-3',
  'Claude', 'Gemini', 'LLaMA', 'Llama',
  'BERT', 'Transformer', 'Stable Diffusion',
  'Mistral', 'Falcon', 'PaLM', 'Bard',
  'Anthropic', 'OpenAI', 'DeepMind',
  'Midjourney', 'DALL-E', 'Whisper',
];

// Country → Region mapping
const COUNTRY_TO_REGION: Record<string, string> = {
  // Brazil
  'BR': 'brazil', 'Brazil': 'brazil', 'Brasil': 'brazil',

  // LATAM (excluding Brazil)
  'MX': 'latam', 'Mexico': 'latam',
  'CO': 'latam', 'Colombia': 'latam',
  'AR': 'latam', 'Argentina': 'latam',
  'CL': 'latam', 'Chile': 'latam',
  'PE': 'latam', 'Peru': 'latam',
  'VE': 'latam', 'Venezuela': 'latam',
  'EC': 'latam', 'Ecuador': 'latam',
  'GT': 'latam', 'Guatemala': 'latam',
  'CU': 'latam', 'Cuba': 'latam',
  'BO': 'latam', 'Bolivia': 'latam',
  'DO': 'latam', 'Dominican Republic': 'latam',
  'HN': 'latam', 'Honduras': 'latam',
  'PY': 'latam', 'Paraguay': 'latam',
  'NI': 'latam', 'Nicaragua': 'latam',
  'SV': 'latam', 'El Salvador': 'latam',
  'CR': 'latam', 'Costa Rica': 'latam',
  'PA': 'latam', 'Panama': 'latam',
  'UY': 'latam', 'Uruguay': 'latam',

  // North America
  'US': 'north_america', 'USA': 'north_america', 'United States': 'north_america',
  'CA': 'north_america', 'Canada': 'north_america',

  // Europe
  'GB': 'europe', 'UK': 'europe', 'United Kingdom': 'europe',
  'DE': 'europe', 'Germany': 'europe',
  'FR': 'europe', 'France': 'europe',
  'IT': 'europe', 'Italy': 'europe',
  'ES': 'europe', 'Spain': 'europe',
  'NL': 'europe', 'Netherlands': 'europe',
  'CH': 'europe', 'Switzerland': 'europe',
  'SE': 'europe', 'Sweden': 'europe',
  'NO': 'europe', 'Norway': 'europe',
  'DK': 'europe', 'Denmark': 'europe',
  'FI': 'europe', 'Finland': 'europe',
  'BE': 'europe', 'Belgium': 'europe',
  'AT': 'europe', 'Austria': 'europe',
  'PL': 'europe', 'Poland': 'europe',
  'CZ': 'europe', 'Czech Republic': 'europe',
  'PT': 'europe', 'Portugal': 'europe',

  // Asia
  'CN': 'asia', 'China': 'asia',
  'JP': 'asia', 'Japan': 'asia',
  'KR': 'asia', 'South Korea': 'asia', 'Korea': 'asia',
  'IN': 'asia', 'India': 'asia',
  'SG': 'asia', 'Singapore': 'asia',
  'TW': 'asia', 'Taiwan': 'asia',
  'HK': 'asia', 'Hong Kong': 'asia',

  // Oceania
  'AU': 'oceania', 'Australia': 'oceania',
  'NZ': 'oceania', 'New Zealand': 'oceania',

  // Africa
  'NG': 'africa', 'Nigeria': 'africa',
  'EG': 'africa', 'Egypt': 'africa',
  'ZA': 'africa', 'South Africa': 'africa',
  'KE': 'africa', 'Kenya': 'africa',
  'MA': 'africa', 'Morocco': 'africa',
};

function normalizeCountryToRegion(country: string): string | null {
  if (!country) return null;
  if (COUNTRY_TO_REGION[country]) return COUNTRY_TO_REGION[country];

  const countryLower = country.toLowerCase();
  for (const [key, region] of Object.entries(COUNTRY_TO_REGION)) {
    if (key.toLowerCase() === countryLower) return region;
  }
  return null;
}

async function generateAIMentionsCache() {
  console.log('🚀 Generating AI Mentions Cache...\n');
  console.log('   ✅ Tracking models:', AI_MODELS.slice(0, 5).join(', '), '...\n');

  try {
    const threeMonthsAgo = new Date();
    threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
    const filterDate = threeMonthsAgo.toISOString().split('T')[0];

    console.log(`📅 Period: ${filterDate} to ${new Date().toISOString().split('T')[0]}\n`);

    const regions = ['brazil', 'latam', 'north_america', 'europe', 'asia', 'oceania', 'africa', 'world'];
    const regionPapers: Record<string, Set<string>> = {};
    const regionModels: Record<string, string[]> = {};

    for (const region of regions) {
      regionPapers[region] = new Set();
      regionModels[region] = [];
    }

    // ========================================================================
    // ArXiv Papers
    // ========================================================================
    console.log('📚 ArXiv AI papers...');
    const arxivPapers = await pool.query(`
      SELECT id, title, abstract
      FROM sofia.arxiv_ai_papers
      WHERE published_date >= $1
    `, [filterDate]);

    for (const paper of arxivPapers.rows) {
      const text = `${paper.title} ${paper.abstract || ''}`.toLowerCase();

      regionPapers.world.add(paper.id);

      for (const model of AI_MODELS) {
        if (text.includes(model.toLowerCase())) {
          regionModels.world.push(model);
        }
      }
    }
    console.log(`   ✅ ${arxivPapers.rows.length} papers`);

    // ========================================================================
    // OpenAlex Papers
    // ========================================================================
    console.log('📊 OpenAlex papers...');
    const openalexPapers = await pool.query(`
      SELECT id, title, abstract, author_countries
      FROM sofia.openalex_papers
      WHERE publication_date >= $1
    `, [filterDate]);

    for (const paper of openalexPapers.rows) {
      const text = `${paper.title} ${paper.abstract || ''}`.toLowerCase();
      const models: string[] = [];

      for (const model of AI_MODELS) {
        if (text.includes(model.toLowerCase())) {
          models.push(model);
        }
      }

      regionPapers.world.add(paper.id);
      regionModels.world.push(...models);

      if (paper.author_countries && paper.author_countries.length > 0) {
        const paperRegions = new Set<string>();

        for (const country of paper.author_countries) {
          const region = normalizeCountryToRegion(country);
          if (region) paperRegions.add(region);
        }

        for (const region of paperRegions) {
          regionPapers[region].add(paper.id);
          regionModels[region].push(...models);
        }
      }
    }
    console.log(`   ✅ ${openalexPapers.rows.length} papers`);

    // ========================================================================
    // Calculate metrics
    // ========================================================================
    console.log('\n📊 Calculating metrics...\n');

    const worldTotal = regionPapers.world.size;
    const regionalData: Record<string, RegionalAI> = {};

    for (const region of regions) {
      const totalPapers = regionPapers[region].size;
      const percentage = region === 'world' ? 100 : (totalPapers / worldTotal) * 100;

      // Count models
      const modelCounts: Record<string, number> = {};
      for (const model of regionModels[region]) {
        modelCounts[model] = (modelCounts[model] || 0) + 1;
      }

      // Get top 10 models
      const totalMentions = Object.values(modelCounts).reduce((a, b) => a + b, 0);
      const topModels = Object.entries(modelCounts)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 10)
        .map(([name, count]) => ({
          name,
          count,
          percentage: totalMentions > 0 ? (count / totalMentions) * 100 : 0,
        }));

      regionalData[region] = {
        total_papers: totalPapers,
        percentage_of_world: percentage,
        top_models: topModels,
      };

      const regionName = region.replace('_', ' ').toUpperCase();
      console.log(`  🌍 ${regionName}:`);
      console.log(`     Papers: ${totalPapers.toLocaleString()} (${percentage.toFixed(1)}% of world)`);
      console.log(`     Top 3: ${topModels.slice(0, 3).map(m => m.name).join(', ') || 'N/A'}`);
    }

    console.log('');

    // ========================================================================
    // Save cache
    // ========================================================================
    console.log('📊 Saving cache...\n');

    const cacheData: AICache = {
      brazil: regionalData.brazil,
      latam: regionalData.latam,
      north_america: regionalData.north_america,
      europe: regionalData.europe,
      asia: regionalData.asia,
      oceania: regionalData.oceania,
      africa: regionalData.africa,
      world: regionalData.world,
      period: `${filterDate} to ${new Date().toISOString().split('T')[0]}`,
      generated_at: new Date().toISOString(),
    };

    const cacheDir = path.join(__dirname, '../cache');
    if (!fs.existsSync(cacheDir)) fs.mkdirSync(cacheDir, { recursive: true });

    const cacheFile = path.join(cacheDir, 'ai-mentions.json');
    fs.writeFileSync(cacheFile, JSON.stringify(cacheData, null, 2));

    console.log('✅ Cache saved!\n');
    console.log('='.repeat(80));
    console.log('📊 AI MENTIONS SUMMARY\n');

    const printRegion = (name: string, emoji: string, data: RegionalAI) => {
      console.log(`${emoji} ${name}:`);
      console.log(`   Total: ${data.total_papers.toLocaleString()} papers (${data.percentage_of_world.toFixed(1)}% of world)`);
      console.log(`   Top Models:`);
      data.top_models.slice(0, 5).forEach((m, idx) => {
        console.log(`     ${idx + 1}. ${m.name} (${m.count} mentions, ${m.percentage.toFixed(1)}%)`);
      });
      console.log('');
    };

    printRegion('🇧🇷 BRAZIL', '🇧🇷', cacheData.brazil);
    printRegion('🌎 LATAM', '🌎', cacheData.latam);
    printRegion('🇺🇸 NORTH AMERICA', '🇺🇸', cacheData.north_america);
    printRegion('🇪🇺 EUROPE', '🇪🇺', cacheData.europe);
    printRegion('🇨🇳 ASIA', '🇨🇳', cacheData.asia);
    printRegion('🇦🇺 OCEANIA', '🇦🇺', cacheData.oceania);
    printRegion('🌍 AFRICA', '🌍', cacheData.africa);
    printRegion('🌎 WORLD', '🌎', cacheData.world);

    console.log('='.repeat(80));
    console.log(`\n💾 Cache: ${cacheFile}`);
    console.log(`📅 Period: ${cacheData.period}`);
    console.log(`⏰ Generated: ${cacheData.generated_at}\n`);

    await pool.end();
    process.exit(0);
  } catch (error: any) {
    console.error('❌ Error:', error.message);
    await pool.end();
    process.exit(1);
  }
}

generateAIMentionsCache();
