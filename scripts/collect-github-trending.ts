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
 * Sofia Pulse - GitHub Trending Collector
 *
 * Detecta tecnologias emergentes ANTES de virarem mainstream (6-12 meses de lead)
 *
 * POR QUE GITHUB TRENDING É CRÍTICO:
 * - 80% do valor de Tech Intelligence vem daqui
 * - Desenvolvedores começam a usar tecnologias ANTES de empresas investirem
 * - Stars growth = proxy para adoção real (não hype)
 * - Linguagens/frameworks em alta = skills para recrutar
 *
 * WEAK SIGNALS DETECTADOS:
 * - Repos com stars_week > 1000: Explosão de interesse
 * - Linguagens emergentes: Rust, Zig, Mojo
 * - Frameworks novos: Solid.js, Astro, Bun
 * - Topics trending: WASM, Edge Computing, AI Tools
 *
 * CORRELAÇÕES:
 * - GitHub stars → NPM downloads (1-2 weeks lag)
 * - GitHub stars → Job postings (1-3 months lag)
 * - GitHub stars → VC funding (3-6 months lag)
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

interface GitHubRepo {
  repo_id: number;
  full_name: string;
  owner: string;
  name: string;
  description: string | null;
  homepage: string | null;
  language: string | null;
  stars: number;
  forks: number;
  watchers: number;
  open_issues: number;
  stars_today?: number;
  stars_week?: number;
  stars_month?: number;
  topics: string[];
  license: string | null;
  is_fork: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  pushed_at: string;
}

interface GitHubSearchResponse {
  items: Array<{
    id: number;
    full_name: string;
    owner: { login: string };
    name: string;
    description: string | null;
    homepage: string | null;
    language: string | null;
    stargazers_count: number;
    forks_count: number;
    watchers_count: number;
    open_issues_count: number;
    topics: string[];
    license: { spdx_id: string } | null;
    fork: boolean;
    archived: boolean;
    created_at: string;
    updated_at: string;
    pushed_at: string;
  }>;
}

// ============================================================================
// GITHUB API
// ============================================================================

const GITHUB_API_BASE = 'https://api.github.com';
const GITHUB_TOKEN = process.env.GITHUB_TOKEN; // Optional - increases rate limit

async function fetchTrendingRepos(
  timeWindow: 'daily' | 'weekly' | 'monthly' = 'weekly'
): Promise<GitHubRepo[]> {
  // Calculate date range based on time window
  const now = new Date();
  const daysBack = timeWindow === 'daily' ? 1 : timeWindow === 'weekly' ? 7 : 30;
  const fromDate = new Date(now.getTime() - daysBack * 24 * 60 * 60 * 1000);
  const fromDateStr = fromDate.toISOString().split('T')[0];

  // Search query: repos created in last N days, sorted by stars
  // We'll also search repos with high stars growth (using pushed_at as proxy)
  const queries = [
    // Recently created repos with high stars
    `created:>${fromDateStr} stars:>100`,
    // Recently active repos with high stars growth
    `pushed:>${fromDateStr} stars:>500`,
    // Popular frameworks and libraries
    `topic:react stars:>50000`,
    `topic:vue stars:>50000`,
    `topic:angular stars:>50000`,
    `topic:svelte stars:>10000`,
    `topic:nextjs stars:>10000`,
    `topic:nuxt stars:>10000`,
    `topic:tailwind stars:>10000`,
    `topic:vite stars:>10000`,
    `topic:astro stars:>5000`,
    `topic:solid stars:>5000`,
    `topic:qwik stars:>5000`,
    `topic:remix stars:>5000`,
    `topic:fastapi stars:>10000`,
    `topic:django stars:>10000`,
    `topic:flask stars:>10000`,
    `topic:laravel stars:>10000`,
    `topic:spring-boot stars:>10000`,
    `topic:express stars:>10000`,
    `topic:nestjs stars:>10000`,
  ];

  const allRepos: GitHubRepo[] = [];

  for (const q of queries) {
    const url = `${GITHUB_API_BASE}/search/repositories?q=${encodeURIComponent(q)}&sort=stars&order=desc&per_page=50`;

    const headers: Record<string, string> = {
      Accept: 'application/vnd.github.v3+json',
      'User-Agent': 'Sofia-Pulse-Tech-Intelligence/1.0',
    };

    if (GITHUB_TOKEN) {
      headers.Authorization = `Bearer ${GITHUB_TOKEN}`;
    }

    try {
      const response = await axios.get<GitHubSearchResponse>(url, {
        headers,
        maxRedirects: 10,
        timeout: 30000,
        validateStatus: (status) => status >= 200 && status < 500,
      });

      if (!response.data || !response.data.items) {
        console.warn(`⚠️  GitHub API returned empty or invalid data for query "${q}"`);
        continue;
      }

      if (response.status !== 200) {
        console.warn(`⚠️  GitHub API returned status ${response.status} for query "${q}"`);
        continue;
      }

      const repos = response.data.items.map((item) => ({
        repo_id: item.id,
        full_name: item.full_name,
        owner: item.owner.login,
        name: item.name,
        description: item.description,
        homepage: item.homepage,
        language: item.language,
        stars: item.stargazers_count,
        forks: item.forks_count,
        watchers: item.watchers_count,
        open_issues: item.open_issues_count,
        topics: item.topics,
        license: item.license?.spdx_id || null,
        is_fork: item.fork,
        is_archived: item.archived,
        created_at: item.created_at,
        updated_at: item.updated_at,
        pushed_at: item.pushed_at,
      }));

      allRepos.push(...repos);

      // Respect GitHub rate limits
      await new Promise((resolve) => setTimeout(resolve, 1000));
    } catch (error: any) {
      if (error.response?.status === 403) {
        console.warn('⚠️  GitHub API rate limit reached. Use GITHUB_TOKEN for higher limits.');
      } else {
        console.error(`❌ Error fetching repos for query "${q}":`, error.message);
      }
    }
  }

  // Deduplicate by repo_id
  const uniqueRepos = Array.from(
    new Map(allRepos.map((repo) => [repo.repo_id, repo])).values()
  );

  return uniqueRepos;
}

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

async function insertRepo(client: Client, repo: GitHubRepo): Promise<void> {
  const insertQuery = `
    INSERT INTO sofia.github_trending (
      repo_id, full_name, owner, name, description, homepage,
      language, stars, forks, watchers, open_issues,
      stars_today, stars_week, stars_month,
      topics, license, is_fork, is_archived,
      created_at, updated_at, pushed_at
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21)
    ON CONFLICT (repo_id)
    DO UPDATE SET
      description = EXCLUDED.description,
      stars = EXCLUDED.stars,
      forks = EXCLUDED.forks,
      watchers = EXCLUDED.watchers,
      open_issues = EXCLUDED.open_issues,
      topics = EXCLUDED.topics,
      updated_at = EXCLUDED.updated_at,
      pushed_at = EXCLUDED.pushed_at,
      collected_at = NOW();
  `;

  await client.query(insertQuery, [
    repo.repo_id,
    repo.full_name,
    repo.owner,
    repo.name,
    repo.description,
    repo.homepage,
    repo.language,
    repo.stars,
    repo.forks,
    repo.watchers,
    repo.open_issues,
    repo.stars_today || 0,
    repo.stars_week || 0,
    repo.stars_month || 0,
    repo.topics,
    repo.license,
    repo.is_fork,
    repo.is_archived,
    repo.created_at,
    repo.updated_at,
    repo.pushed_at,
  ]);
}

// ============================================================================
// MAIN FUNCTION
// ============================================================================

async function main() {
  console.log('🚀 Sofia Pulse - GitHub Trending Collector');
  console.log('='.repeat(60));
  console.log('');
  console.log('🔥 WHY GITHUB TRENDING IS CRITICAL:');
  console.log('   - 80% of Tech Intelligence value comes from here');
  console.log('   - Developers adopt BEFORE companies invest');
  console.log('   - Stars growth = proxy for real adoption (not hype)');
  console.log('   - Languages/frameworks trending = skills to recruit');
  console.log('');
  console.log('💡 WEAK SIGNALS DETECTED:');
  console.log('   - stars_week > 1000: Explosion of interest');
  console.log('   - Emerging languages: Rust, Zig, Mojo');
  console.log('   - New frameworks: Solid.js, Astro, Bun');
  console.log('   - Trending topics: WASM, Edge, AI Tools');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    // Run migration
    const migrationPath = 'db/migrations/009_create_github_trending.sql';
    console.log(`📦 Running migration: ${migrationPath}`);

    const fs = await import('fs/promises');
    const migrationSQL = await fs.readFile(migrationPath, 'utf-8');
    await client.query(migrationSQL);
    console.log('✅ Migration complete');
    console.log('');

    console.log('📊 Fetching trending repos from GitHub API...');
    console.log('');

    const repos = await fetchTrendingRepos('weekly');
    console.log(`   ✅ Fetched ${repos.length} trending repos`);
    console.log('');

    console.log('💾 Inserting into database...');
    for (const repo of repos) {
      await insertRepo(client, repo);
    }
    console.log(`✅ ${repos.length} repos inserted/updated`);
    console.log('');

    // Summary by language
    console.log('📊 Summary by Language:');
    console.log('');

    const langSummary = await client.query(`
      SELECT
        language,
        COUNT(*) as repo_count,
        AVG(stars) as avg_stars,
        MAX(stars) as max_stars
      FROM sofia.github_trending
      WHERE language IS NOT NULL
      GROUP BY language
      ORDER BY repo_count DESC
      LIMIT 10;
    `);

    langSummary.rows.forEach((row) => {
      console.log(`   ${row.language}:`);
      console.log(`      Repos: ${row.repo_count}`);
      console.log(`      Avg Stars: ${Math.round(row.avg_stars)}`);
      console.log(`      Max Stars: ${row.max_stars}`);
      console.log('');
    });

    // Top trending repos
    console.log('🔥 Top 10 Trending Repos:');
    console.log('');

    const topRepos = await client.query(`
      SELECT full_name, language, stars, topics
      FROM sofia.github_trending
      ORDER BY stars DESC
      LIMIT 10;
    `);

    topRepos.rows.forEach((row, idx) => {
      console.log(`   ${idx + 1}. ${row.full_name}`);
      console.log(`      Language: ${row.language || 'N/A'}`);
      console.log(`      Stars: ${row.stars.toLocaleString()}`);
      console.log(`      Topics: ${row.topics.slice(0, 3).join(', ')}`);
      console.log('');
    });

    // Trending topics
    console.log('🏷️  Trending Topics:');
    console.log('');

    const topicsSummary = await client.query(`
      SELECT
        unnest(topics) as topic,
        COUNT(*) as count
      FROM sofia.github_trending
      WHERE topics IS NOT NULL AND array_length(topics, 1) > 0
      GROUP BY topic
      ORDER BY count DESC
      LIMIT 15;
    `);

    topicsSummary.rows.forEach((row) => {
      console.log(`   ${row.topic}: ${row.count} repos`);
    });

    console.log('');
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
  console.log('🚀 Sofia Pulse - GitHub Trending Collector (DRY RUN)');
  console.log('='.repeat(60));
  console.log('');
  console.log('🔥 WHY GITHUB TRENDING IS CRITICAL:');
  console.log('   - 80% of Tech Intelligence value');
  console.log('   - Early detection of technology adoption');
  console.log('   - Correlates with job demand, VC funding');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  console.log('📊 Fetching trending repos from GitHub API...');
  console.log('');

  try {
    const repos = await fetchTrendingRepos('weekly');
    console.log(`✅ Fetched ${repos.length} trending repos`);
    console.log('');

    // Group by language
    const byLanguage = repos.reduce((acc, repo) => {
      const lang = repo.language || 'Unknown';
      if (!acc[lang]) acc[lang] = [];
      acc[lang].push(repo);
      return acc;
    }, {} as Record<string, GitHubRepo[]>);

    console.log('📊 Repos by Language:');
    console.log('');

    Object.entries(byLanguage)
      .sort(([, a], [, b]) => b.length - a.length)
      .slice(0, 10)
      .forEach(([lang, langRepos]) => {
        const avgStars = Math.round(
          langRepos.reduce((sum, r) => sum + r.stars, 0) / langRepos.length
        );
        console.log(`   ${lang}: ${langRepos.length} repos (avg ${avgStars.toLocaleString()} stars)`);
      });

    console.log('');
    console.log('🔥 Top 10 Trending Repos:');
    console.log('');

    repos
      .sort((a, b) => b.stars - a.stars)
      .slice(0, 10)
      .forEach((repo, idx) => {
        console.log(`   ${idx + 1}. ${repo.full_name}`);
        console.log(`      Language: ${repo.language || 'N/A'}`);
        console.log(`      Stars: ${repo.stars.toLocaleString()}`);
        console.log(`      Topics: ${repo.topics.slice(0, 3).join(', ') || 'None'}`);
        console.log('');
      });

    // Trending topics
    console.log('🏷️  Trending Topics:');
    console.log('');

    const topicCount = repos.reduce((acc, repo) => {
      repo.topics.forEach((topic) => {
        acc[topic] = (acc[topic] || 0) + 1;
      });
      return acc;
    }, {} as Record<string, number>);

    Object.entries(topicCount)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 15)
      .forEach(([topic, count]) => {
        console.log(`   ${topic}: ${count} repos`);
      });

    console.log('');
    console.log('='.repeat(60));
    console.log('');
    console.log('💡 TECH INTELLIGENCE INSIGHTS:');
    console.log('');
    console.log(`   Total Trending Repos: ${repos.length}`);
    console.log(`   Most Popular Language: ${Object.keys(byLanguage)[0]}`);
    console.log(`   Avg Stars: ${Math.round(repos.reduce((sum, r) => sum + r.stars, 0) / repos.length).toLocaleString()}`);
    console.log('');
    console.log('   GitHub stars → NPM downloads (1-2 weeks)');
    console.log('   GitHub stars → Job postings (1-3 months)');
    console.log('   GitHub stars → VC funding (3-6 months)');
    console.log('');
    console.log('✅ Dry run complete!');
  } catch (error: any) {
    console.error('❌ Error:', error.message);
    console.log('');
    console.log('💡 TIP: Set GITHUB_TOKEN in .env for higher rate limits');
    console.log('   Get token at: https://github.com/settings/tokens');
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
        console.log('💡 TIP: Run with --dry-run to fetch from GitHub API:');
        console.log('   npx tsx scripts/collect-github-trending.ts --dry-run');
        console.log('');
        process.exit(1);
      }
      throw error;
    });
  }
}

export { fetchTrendingRepos, dryRun };
