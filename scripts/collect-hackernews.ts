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
 * Sofia Pulse - HackerNews Collector
 *
 * Captura BUZZ tecnológico ANTES de virar mainstream
 *
 * POR QUE HACKERNEWS É CRÍTICO:
 * - HN = termômetro de interesse da comunidade tech
 * - Stories aparecem ANTES de funding rounds/IPOs
 * - Comments revelam sentiment real (não marketing)
 * - Autores influentes (patio11, antirez, etc) = sinal forte
 *
 * WEAK SIGNALS DETECTADOS:
 * - 100+ points em <24h: Interesse explosivo
 * - 50+ comments: Debate ativo (polêmico ou muito interessante)
 * - Timing: Story sobre tecnologia X aparece ANTES de VC funding
 * - Show HN: Produtos sendo lançados (early access)
 * - Ask HN: Comunidade perguntando = demanda latente
 *
 * CORRELAÇÕES:
 * - HN front page → NPM downloads spike (1-7 days)
 * - HN buzz → VC funding announcement (2-8 weeks)
 * - Ask HN sobre tech X → Job postings para tech X (1-3 months)
 */

import { Client } from 'pg';
import * as dotenv from 'dotenv';
import axios from 'axios';

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

interface HNStory {
  story_id: number;
  object_id: string;
  title: string;
  url: string | null;
  author: string;
  points: number;
  num_comments: number;
  story_type: string;
  tags: string[];
  created_at: string;
  keywords?: string[];
  mentioned_companies?: string[];
  mentioned_technologies?: string[];
}

interface HNApiResponse {
  hits: Array<{
    objectID: string;
    title: string;
    url: string | null;
    author: string;
    points: number | null;
    num_comments: number | null;
    created_at: string;
    _tags: string[];
  }>;
}

// ============================================================================
// HACKERNEWS API
// ============================================================================

const HN_API_BASE = 'https://hn.algolia.com/api/v1';

async function fetchTopStories(
  timeRange: '24h' | '7d' | '30d' = '24h'
): Promise<HNStory[]> {
  // Numeric filters for time range
  const now = Math.floor(Date.now() / 1000);
  const secondsBack = timeRange === '24h' ? 86400 : timeRange === '7d' ? 604800 : 2592000;
  const timestampFrom = now - secondsBack;

  // Query for top stories (front page material)
  const queries = [
    // Top stories
    { tags: 'story', hitsPerPage: 100 },
    // Show HN (product launches)
    { tags: 'show_hn', hitsPerPage: 50 },
    // Ask HN (community questions = demand signals)
    { tags: 'ask_hn', hitsPerPage: 50 },
  ];

  const allStories: HNStory[] = [];

  for (const query of queries) {
    const url = `${HN_API_BASE}/search_by_date?tags=${query.tags}&numericFilters=created_at_i>${timestampFrom}&hitsPerPage=${query.hitsPerPage}`;

    try {
      const response = await axios.get<HNApiResponse>(url);

      const stories = response.data.hits
        .filter((hit) => hit.points && hit.points >= 10) // Minimum threshold
        .map((hit) => {
          const storyIdMatch = hit.objectID.match(/\d+/);
          const storyId = storyIdMatch ? parseInt(storyIdMatch[0]) : 0;

          return {
            story_id: storyId,
            object_id: hit.objectID,
            title: hit.title,
            url: hit.url,
            author: hit.author,
            points: hit.points || 0,
            num_comments: hit.num_comments || 0,
            story_type: hit._tags.find((t) => t.includes('story') || t.includes('ask') || t.includes('show')) || 'story',
            tags: hit._tags,
            created_at: hit.created_at,
          };
        });

      allStories.push(...stories);

      // Respect rate limits
      await new Promise((resolve) => setTimeout(resolve, 500));
    } catch (error: any) {
      console.error(`❌ Error fetching HN stories for ${query.tags}:`, error.message);
    }
  }

  // Deduplicate by story_id
  const uniqueStories = Array.from(
    new Map(allStories.map((story) => [story.story_id, story])).values()
  );

  // Enrich with metadata
  uniqueStories.forEach((story) => {
    story.keywords = extractKeywords(story.title);
    story.mentioned_companies = extractCompanies(story.title, story.url || '');
    story.mentioned_technologies = extractTechnologies(story.title);
  });

  return uniqueStories;
}

// ============================================================================
// EXTRACTION FUNCTIONS
// ============================================================================

function extractKeywords(title: string): string[] {
  const text = title.toLowerCase();
  const keywords: string[] = [];

  // Technology categories
  if (text.match(/\b(ai|artificial intelligence|ml|machine learning|llm|gpt)\b/)) keywords.push('AI/ML');
  if (text.match(/\b(blockchain|crypto|bitcoin|ethereum|web3|nft)\b/)) keywords.push('Blockchain');
  if (text.match(/\b(cloud|aws|azure|gcp|kubernetes|docker)\b/)) keywords.push('Cloud');
  if (text.match(/\b(security|vulnerability|exploit|breach|hack)\b/)) keywords.push('Security');
  if (text.match(/\b(startup|funding|raised|series [a-d]|ipo)\b/)) keywords.push('Funding');
  if (text.match(/\b(open.?source|oss|github|mit license)\b/)) keywords.push('Open Source');
  if (text.match(/\b(performance|optimization|speed|fast|slow)\b/)) keywords.push('Performance');
  if (text.match(/\b(privacy|gdpr|data protection|encryption)\b/)) keywords.push('Privacy');
  if (text.match(/\b(mobile|ios|android|app)\b/)) keywords.push('Mobile');
  if (text.match(/\b(web|frontend|backend|fullstack|api)\b/)) keywords.push('Web Dev');
  if (text.match(/\b(database|sql|nosql|postgres|mongo)\b/)) keywords.push('Database');
  if (text.match(/\b(devops|ci\/cd|deployment|infrastructure)\b/)) keywords.push('DevOps');

  return [...new Set(keywords)];
}

function extractCompanies(title: string, url: string): string[] {
  const text = `${title} ${url}`.toLowerCase();
  const companies: string[] = [];

  // Tech giants
  const knownCompanies = [
    'google', 'microsoft', 'apple', 'amazon', 'meta', 'facebook',
    'netflix', 'tesla', 'openai', 'anthropic', 'nvidia', 'intel',
    'amd', 'uber', 'airbnb', 'stripe', 'shopify', 'spotify',
    'twitter', 'reddit', 'github', 'gitlab', 'vercel', 'cloudflare',
    'databricks', 'snowflake', 'mongodb', 'redis', 'elastic',
  ];

  knownCompanies.forEach((company) => {
    if (text.includes(company)) {
      companies.push(company.charAt(0).toUpperCase() + company.slice(1));
    }
  });

  return [...new Set(companies)];
}

function extractTechnologies(title: string): string[] {
  const text = title.toLowerCase();
  const technologies: string[] = [];

  // Programming languages
  const languages = [
    'javascript', 'typescript', 'python', 'rust', 'go', 'golang',
    'java', 'kotlin', 'swift', 'c\\+\\+', 'c#', 'ruby', 'php',
    'elixir', 'haskell', 'scala', 'clojure', 'zig', 'mojo',
  ];

  languages.forEach((lang) => {
    const regex = new RegExp(`\\b${lang}\\b`, 'i');
    if (regex.test(text)) {
      technologies.push(lang.charAt(0).toUpperCase() + lang.slice(1).replace('\\+\\+', '++').replace('#', 'Sharp'));
    }
  });

  // Frameworks/libraries
  const frameworks = [
    'react', 'vue', 'angular', 'svelte', 'solid', 'next\\.js', 'nuxt',
    'express', 'fastify', 'django', 'flask', 'rails', 'laravel',
    'spring', 'phoenix', 'actix', 'axum', 'gin', 'fiber',
    'tensorflow', 'pytorch', 'keras', 'scikit-learn',
  ];

  frameworks.forEach((fw) => {
    const regex = new RegExp(`\\b${fw}\\b`, 'i');
    if (regex.test(text)) {
      const name = fw.replace('\\.js', '.js');
      technologies.push(name.charAt(0).toUpperCase() + name.slice(1));
    }
  });

  // Infrastructure/tools
  const tools = [
    'kubernetes', 'docker', 'terraform', 'ansible', 'jenkins',
    'postgres', 'mysql', 'mongodb', 'redis', 'elasticsearch',
    'kafka', 'rabbitmq', 'grpc', 'graphql', 'rest',
    'wasm', 'webassembly', 'edge computing', 'serverless',
  ];

  tools.forEach((tool) => {
    const regex = new RegExp(`\\b${tool}\\b`, 'i');
    if (regex.test(text)) {
      technologies.push(tool.charAt(0).toUpperCase() + tool.slice(1));
    }
  });

  return [...new Set(technologies)];
}

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

async function insertStory(client: Client, story: HNStory): Promise<void> {
  const insertQuery = `
    INSERT INTO sofia.hackernews_stories (
      story_id, object_id, title, url, author,
      points, num_comments, story_type, tags,
      created_at, keywords, mentioned_companies, mentioned_technologies
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
    ON CONFLICT (story_id)
    DO UPDATE SET
      points = EXCLUDED.points,
      num_comments = EXCLUDED.num_comments,
      collected_at = NOW();
  `;

  await client.query(insertQuery, [
    story.story_id,
    story.object_id,
    story.title,
    story.url,
    story.author,
    story.points,
    story.num_comments,
    story.story_type,
    story.tags,
    story.created_at,
    story.keywords || [],
    story.mentioned_companies || [],
    story.mentioned_technologies || [],
  ]);
}

// ============================================================================
// MAIN FUNCTION
// ============================================================================

async function main() {
  // V2 JSON output contract
  const v2Metrics: Record<string, any> = {
    status: 'ok',
    source: 'hackernews-algolia-api',
    items_read: 0,
    items_candidate: 0,
    items_inserted: 0,
    items_updated: 0,
    items_ignored_conflict: 0,
    tables_affected: ['sofia.hackernews_stories'],
    meta: {},
  };
  let exitCode = 0;

  // V2: All logs go to stderr
  const log = (...args: any[]) => console.error(...args);

  log('🚀 Sofia Pulse - HackerNews Collector');
  log('='.repeat(60));

  const client = new Client(dbConfig);

  try {
    await client.connect();
    log('✅ Connected to PostgreSQL');

    // Run migration
    const migrationPath = 'db/migrations/010_create_hackernews_stories.sql';
    log(`📦 Running migration: ${migrationPath}`);
    const fs = await import('fs/promises');
    const migrationSQL = await fs.readFile(migrationPath, 'utf-8');
    await client.query(migrationSQL);
    log('✅ Migration complete');

    log('📊 Fetching top stories from HackerNews...');
    const stories = await fetchTopStories('24h');
    log(`   ✅ Fetched ${stories.length} stories`);

    v2Metrics.items_read = stories.length;
    v2Metrics.items_candidate = stories.length;

    log('💾 Inserting into database...');
    let inserted = 0;
    for (const story of stories) {
      try {
        await insertStory(client, story);
        inserted++;
      } catch (err: any) {
        log(`⚠️ Skip story ${story.story_id}: ${err.message}`);
        v2Metrics.items_ignored_conflict++;
      }
    }
    v2Metrics.items_inserted = inserted;
    log(`✅ ${inserted} stories inserted/updated out of ${stories.length}`);

    // Report top stories to stderr (for human inspection)
    const topStories = await client.query(`
      SELECT title, author, points, num_comments
      FROM sofia.hackernews_stories
      ORDER BY points DESC LIMIT 5;
    `);
    log('🔥 Top 5:');
    topStories.rows.forEach((row, idx) => {
      log(`  ${idx + 1}. ${row.title} (${row.points}pt, ${row.num_comments} comments)`);
    });

  } catch (error: any) {
    log('❌ Fatal Error:', error);
    v2Metrics.status = 'fail';
    v2Metrics.meta = { error: error?.message || String(error) };
    exitCode = 1;
  } finally {
    await client.end().catch(() => { });
  }

  // SINGLE STDOUT OUTPUT POINT — V2 contract
  console.log(JSON.stringify(v2Metrics));
  process.exit(exitCode);
}

// ============================================================================
// DRY RUN MODE
// ============================================================================

async function dryRun() {
  console.log('🚀 Sofia Pulse - HackerNews Collector (DRY RUN)');
  console.log('='.repeat(60));
  console.log('');
  console.log('🔥 Fetching stories from HackerNews API...');
  console.log('');

  try {
    const stories = await fetchTopStories('24h');
    console.log(`✅ Fetched ${stories.length} stories from last 24 hours`);
    console.log('');

    // Top stories
    console.log('🔥 Top 10 Stories (by points):');
    console.log('');

    stories
      .sort((a, b) => b.points - a.points)
      .slice(0, 10)
      .forEach((story, idx) => {
        console.log(`   ${idx + 1}. ${story.title}`);
        console.log(`      Author: ${story.author}`);
        console.log(`      Points: ${story.points} | Comments: ${story.num_comments}`);
        console.log(`      Type: ${story.story_type}`);
        console.log(`      Tech: ${story.mentioned_technologies?.join(', ') || 'N/A'}`);
        console.log('');
      });

    // Story types
    console.log('📊 Stories by Type:');
    console.log('');

    const byType = stories.reduce((acc, story) => {
      acc[story.story_type] = (acc[story.story_type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    Object.entries(byType).forEach(([type, count]) => {
      console.log(`   ${type}: ${count} stories`);
    });

    console.log('');

    // Trending technologies
    console.log('🏷️  Trending Technologies:');
    console.log('');

    const techCount = stories.reduce((acc, story) => {
      (story.mentioned_technologies || []).forEach((tech) => {
        acc[tech] = (acc[tech] || 0) + 1;
      });
      return acc;
    }, {} as Record<string, number>);

    Object.entries(techCount)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 15)
      .forEach(([tech, count]) => {
        console.log(`   ${tech}: ${count} mentions`);
      });

    console.log('');

    // Companies mentioned
    console.log('🏢 Companies Mentioned:');
    console.log('');

    const companyCount = stories.reduce((acc, story) => {
      (story.mentioned_companies || []).forEach((company) => {
        acc[company] = (acc[company] || 0) + 1;
      });
      return acc;
    }, {} as Record<string, number>);

    Object.entries(companyCount)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .forEach(([company, count]) => {
        console.log(`   ${company}: ${count} mentions`);
      });

    console.log('');
    console.log('='.repeat(60));
    console.log('');
    console.log('💡 TECH INTELLIGENCE INSIGHTS:');
    console.log('');
    console.log(`   Total Stories: ${stories.length}`);
    console.log(`   Avg Points: ${Math.round(stories.reduce((sum, s) => sum + s.points, 0) / stories.length)}`);
    console.log(`   Avg Comments: ${Math.round(stories.reduce((sum, s) => sum + s.num_comments, 0) / stories.length)}`);
    console.log('');
    console.log('   HN buzz → NPM downloads (1-7 days)');
    console.log('   HN buzz → VC funding (2-8 weeks)');
    console.log('   Ask HN → Job postings (1-3 months)');
    console.log('');
    console.log('✅ Dry run complete!');
  } catch (error: any) {
    console.error('❌ Error:', error.message);
  }
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
        console.log('💡 TIP: Run with --dry-run to fetch from HackerNews API:');
        console.log('   npx tsx scripts/collect-hackernews.ts --dry-run');
        console.log('');
        process.exit(1);
      }
      throw error;
    });
  }
}

export { fetchTopStories, dryRun };
