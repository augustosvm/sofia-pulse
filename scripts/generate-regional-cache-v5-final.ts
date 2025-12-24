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
  password: process.env.POSTGRES_PASSWORD || process.env.DB_PASSWORD || 'sofia123strong',
  database: process.env.POSTGRES_DB || process.env.DB_NAME || 'sofia_db',
});

interface RegionalData {
  total_papers: number;
  percentage_of_world: number;
  top_tags: Array<{ tag: string; count: number; percentage: number }>;
}

interface CacheData {
  brazil: RegionalData;
  north_america: RegionalData;
  europe: RegionalData;
  asia: RegionalData;
  oceania: RegionalData;
  africa: RegionalData;
  world: RegionalData;
  period: string;
  generated_at: string;
  last_3_months_filter: string;
  data_sources: {
    arxiv_total: number;
    arxiv_with_country: number;
    openalex_total: number;
    openalex_with_country: number;
    universities_total: number;
  };
}

// AGGRESSIVE FILTER: Remove all generic/broad terms
const GENERIC_TAGS = new Set([
  // Broad disciplines
  'Medicine', 'Biology', 'Chemistry', 'Physics', 'Engineering',
  'Computer Science', 'Computer science',
  'Materials Science', 'Materials science',
  'Environmental Science', 'Environmental science',
  'Social Science', 'Mathematics', 'Science',

  // Generic CS/AI terms
  'Artificial Intelligence', 'Artificial intelligence',
  'Machine Learning', 'Machine learning',
  'Deep Learning', 'Deep learning',
  'Neural Network', 'Neural network',
  'Data Science', 'Data science',

  // Generic medical terms
  'Clinical Medicine', 'Basic Medicine', 'Health Sciences', 'Medical Research',

  // Too broad
  'Technology', 'Research', 'Innovation', 'Development', 'Analysis',
  'Study', 'Investigation', 'Experiment', 'Theory', 'Model',
  'System', 'Method', 'Application', 'Evaluation',

  // Generic data/CS terms
  'Algorithm', 'Data', 'Information', 'Network', 'Software',
  'Hardware', 'Database', 'Programming', 'Computation', 'Computing',

  // Generic abstract concepts
  'Set (abstract data type)', 'Context (archaeology)',
  'Time', 'Space', 'Energy', 'Power', 'Control', 'Optimization',
  'Statement (logic)', 'Process (computing)', 'Key (lock)',
  'Nomenclature',
]);

// Country → Region mapping (EXPANDED with Oceania and Africa)
const COUNTRY_TO_REGION: Record<string, string> = {
  // North America
  'US': 'north_america', 'USA': 'north_america', 'United States': 'north_america',
  'CA': 'north_america', 'Canada': 'north_america',
  'MX': 'north_america', 'Mexico': 'north_america',

  // Europe
  'GB': 'europe', 'UK': 'europe', 'United Kingdom': 'europe',
  'DE': 'europe', 'Germany': 'europe',
  'FR': 'europe', 'France': 'europe',
  'IT': 'europe', 'Italy': 'europe',
  'ES': 'europe', 'Spain': 'europe',
  'NL': 'europe', 'Netherlands': 'europe', 'The Netherlands': 'europe',
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
  'RO': 'europe', 'Romania': 'europe',
  'SI': 'europe', 'Slovenia': 'europe',
  'RU': 'europe', 'Russia': 'europe',
  'TR': 'europe', 'Turkey': 'europe',
  'IL': 'europe', 'Israel': 'europe',

  // Asia
  'CN': 'asia', 'China': 'asia',
  'JP': 'asia', 'Japan': 'asia',
  'KR': 'asia', 'South Korea': 'asia', 'Korea': 'asia',
  'IN': 'asia', 'India': 'asia',
  'SG': 'asia', 'Singapore': 'asia',
  'TW': 'asia', 'Taiwan': 'asia',
  'HK': 'asia', 'Hong Kong': 'asia',
  'MY': 'asia', 'Malaysia': 'asia',
  'ID': 'asia', 'Indonesia': 'asia',
  'TH': 'asia', 'Thailand': 'asia',
  'VN': 'asia', 'Vietnam': 'asia',
  'PK': 'asia', 'Pakistan': 'asia',
  'BD': 'asia', 'Bangladesh': 'asia',
  'IR': 'asia', 'Iran': 'asia',
  'IQ': 'asia', 'Iraq': 'asia',
  'JO': 'asia', 'Jordan': 'asia',
  'LB': 'asia', 'Lebanon': 'asia',
  'SA': 'asia', 'Saudi Arabia': 'asia',
  'AE': 'asia', 'UAE': 'asia', 'United Arab Emirates': 'asia',

  // Oceania
  'AU': 'oceania', 'Australia': 'oceania',
  'NZ': 'oceania', 'New Zealand': 'oceania',

  // Africa
  'NG': 'africa', 'Nigeria': 'africa',
  'EG': 'africa', 'Egypt': 'africa',
  'ZA': 'africa', 'South Africa': 'africa',
  'GH': 'africa', 'Ghana': 'africa',
  'DZ': 'africa', 'Algeria': 'africa',
  'TN': 'africa', 'Tunisia': 'africa',
  'KE': 'africa', 'Kenya': 'africa',
  'ET': 'africa', 'Ethiopia': 'africa',
  'MA': 'africa', 'Morocco': 'africa',

  // Brazil (separate region)
  'BR': 'brazil', 'Brazil': 'brazil', 'Brasil': 'brazil',

  // LATAM (could be added later)
  'CO': 'north_america', 'Colombia': 'north_america', // Or create separate latam region
  'AR': 'north_america', 'Argentina': 'north_america',
  'CL': 'north_america', 'Chile': 'north_america',
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

function isSpecificTag(tag: string): boolean {
  if (GENERIC_TAGS.has(tag)) return false;
  if (tag.length < 3) return false;
  if (/^[A-Z]$/.test(tag) || /^\d+$/.test(tag)) return false;
  return true;
}

async function generateRegionalCache() {
  console.log('🚀 Generating Regional Research Data Cache V5 FINAL...');
  console.log('   ✅ ALL regions: Brazil, North America, Europe, Asia, Oceania, Africa');
  console.log('   ✅ Numerical metrics (totals, percentages)');
  console.log('   ✅ Top 10 specific tags per region\n');

  try {
    const threeMonthsAgo = new Date();
    threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
    const filterDate = threeMonthsAgo.toISOString().split('T')[0];

    console.log(`📅 Period: ${filterDate} to ${new Date().toISOString().split('T')[0]}\n`);

    // ========================================================================
    // STEP 1: Collect papers by region
    // ========================================================================

    console.log('📊 Step 1/3: Extracting data from all sources...\n');

    const regions = ['brazil', 'north_america', 'europe', 'asia', 'oceania', 'africa', 'world'];
    const regionPapers: Record<string, Set<string>> = {};
    const regionTags: Record<string, string[]> = {};

    for (const region of regions) {
      regionPapers[region] = new Set();
      regionTags[region] = [];
    }

    // ArXiv
    console.log('  📚 ArXiv AI papers...');
    const arxivPapers = await pool.query(`
      SELECT id, keywords, categories
      FROM sofia.arxiv_ai_papers
      WHERE published_date >= $1
    `, [filterDate]);

    for (const paper of arxivPapers.rows) {
      const tags = [...(paper.keywords || []), ...(paper.categories || [])].filter(isSpecificTag);
      regionPapers.world.add(paper.id);
      if (tags.length > 0) regionTags.world.push(...tags);
    }
    console.log(`     ✅ ${arxivPapers.rows.length} papers`);

    // OpenAlex
    console.log('  📊 OpenAlex papers...');
    const openalexPapers = await pool.query(`
      SELECT id, author_countries, concepts
      FROM sofia.openalex_papers
      WHERE publication_date >= $1
    `, [filterDate]);

    let openalexWithCountry = 0;
    for (const paper of openalexPapers.rows) {
      const concepts = (paper.concepts || []).filter(isSpecificTag);

      regionPapers.world.add(paper.id);
      if (concepts.length > 0) regionTags.world.push(...concepts);

      if (paper.author_countries && paper.author_countries.length > 0) {
        openalexWithCountry++;
        const paperRegions = new Set<string>();

        for (const country of paper.author_countries) {
          const region = normalizeCountryToRegion(country);
          if (region) paperRegions.add(region);
        }

        for (const region of paperRegions) {
          regionPapers[region].add(paper.id);
          if (concepts.length > 0) regionTags[region].push(...concepts);
        }
      }
    }
    console.log(`     ✅ ${openalexPapers.rows.length} papers (${openalexWithCountry} with countries)`);

    // Universities
    console.log('  🎓 University papers...');
    const univPapers = await pool.query(`
      SELECT id, institution_country, research_areas
      FROM sofia.global_research_institutions
      WHERE publication_year >= 2023
    `);

    for (const paper of univPapers.rows) {
      const areas = (Array.isArray(paper.research_areas) ? paper.research_areas : [])
        .filter(isSpecificTag);

      regionPapers.world.add(paper.id);
      if (areas.length > 0) regionTags.world.push(...areas);

      if (paper.institution_country) {
        const region = normalizeCountryToRegion(paper.institution_country);
        if (region) {
          regionPapers[region].add(paper.id);
          if (areas.length > 0) regionTags[region].push(...areas);
        }
      }
    }
    console.log(`     ✅ ${univPapers.rows.length} papers\n`);

    // ========================================================================
    // STEP 2: Calculate metrics
    // ========================================================================

    console.log('📊 Step 2/3: Calculating metrics...\n');

    const worldTotal = regionPapers.world.size;
    const regionalData: Record<string, RegionalData> = {};

    for (const region of regions) {
      const totalPapers = regionPapers[region].size;
      const percentage = region === 'world' ? 100 : (totalPapers / worldTotal) * 100;

      // Count tags
      const tagCounts: Record<string, number> = {};
      for (const tag of regionTags[region]) {
        if (tag && isSpecificTag(tag)) {
          tagCounts[tag] = (tagCounts[tag] || 0) + 1;
        }
      }

      // Get top 10 tags with percentages
      const totalTags = Object.values(tagCounts).reduce((a, b) => a + b, 0);
      const topTags = Object.entries(tagCounts)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 10)
        .map(([tag, count]) => ({
          tag,
          count,
          percentage: totalTags > 0 ? (count / totalTags) * 100 : 0,
        }));

      regionalData[region] = {
        total_papers: totalPapers,
        percentage_of_world: percentage,
        top_tags: topTags,
      };

      const regionName = region.replace('_', ' ').toUpperCase();
      console.log(`  🌍 ${regionName}:`);
      console.log(`     Papers: ${totalPapers.toLocaleString()} (${percentage.toFixed(1)}% of world)`);
      console.log(`     Top 3: ${topTags.slice(0, 3).map(t => t.tag).join(', ')}`);
    }

    console.log('');

    // ========================================================================
    // STEP 3: Save to cache
    // ========================================================================

    console.log('📊 Step 3/3: Saving cache...\n');

    const cacheData: CacheData = {
      brazil: regionalData.brazil,
      north_america: regionalData.north_america,
      europe: regionalData.europe,
      asia: regionalData.asia,
      oceania: regionalData.oceania,
      africa: regionalData.africa,
      world: regionalData.world,
      period: `${filterDate} to ${new Date().toISOString().split('T')[0]}`,
      generated_at: new Date().toISOString(),
      last_3_months_filter: filterDate,
      data_sources: {
        arxiv_total: arxivPapers.rows.length,
        arxiv_with_country: 0,
        openalex_total: openalexPapers.rows.length,
        openalex_with_country: openalexWithCountry,
        universities_total: univPapers.rows.length,
      },
    };

    const cacheDir = path.join(__dirname, '../cache');
    if (!fs.existsSync(cacheDir)) fs.mkdirSync(cacheDir, { recursive: true });

    const cacheFile = path.join(cacheDir, 'regional-research-data.json');
    fs.writeFileSync(cacheFile, JSON.stringify(cacheData, null, 2));

    console.log('✅ Cache saved!\n');
    console.log('=' .repeat(80));
    console.log('📊 REGIONAL RESEARCH DATA SUMMARY\n');

    const printRegion = (name: string, emoji: string, data: RegionalData) => {
      console.log(`${emoji} ${name}:`);
      console.log(`   Total: ${data.total_papers.toLocaleString()} papers (${data.percentage_of_world.toFixed(1)}% of world)`);
      console.log(`   Top Tags:`);
      data.top_tags.slice(0, 5).forEach((t, idx) => {
        console.log(`     ${idx + 1}. ${t.tag} (${t.count}, ${t.percentage.toFixed(1)}%)`);
      });
      console.log('');
    };

    printRegion('🇧🇷 BRAZIL', '🇧🇷', cacheData.brazil);
    printRegion('🇺🇸 NORTH AMERICA', '🇺🇸', cacheData.north_america);
    printRegion('🇪🇺 EUROPE', '🇪🇺', cacheData.europe);
    printRegion('🇨🇳 ASIA', '🇨🇳', cacheData.asia);
    printRegion('🇦🇺 OCEANIA', '🇦🇺', cacheData.oceania);
    printRegion('🌍 AFRICA', '🌍', cacheData.africa);
    printRegion('🌎 WORLD', '🌎', cacheData.world);

    console.log('=' .repeat(80));
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

generateRegionalCache();
