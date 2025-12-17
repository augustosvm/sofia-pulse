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

interface TrendingItem {
  name: string;
  stars?: number;
  downloads?: number;
  points?: number;
  description?: string;
  url?: string;
}

interface TrendingCache {
  github: TrendingItem[];
  npm: TrendingItem[];
  pypi: TrendingItem[];
  hackernews: TrendingItem[];
  period: string;
  generated_at: string;
  data_sources: {
    github_total: number;
    npm_total: number;
    pypi_total: number;
    hackernews_total: number;
  };
}

async function generateTrendingCache() {
  console.log('🚀 Generating Trending Tech Cache...\n');

  try {
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    const filterDate = thirtyDaysAgo.toISOString().split('T')[0];

    console.log(`📅 Period: ${filterDate} to ${new Date().toISOString().split('T')[0]}\n`);

    // ========================================================================
    // GITHUB TRENDING
    // ========================================================================
    console.log('📊 GitHub Trending Repos...');
    const githubQuery = await pool.query(`
      SELECT
        name,
        full_name,
        stars,
        description
      FROM sofia.github_trending
      WHERE collected_at >= $1
      ORDER BY stars DESC
      LIMIT 10
    `, [filterDate]);

    const github = githubQuery.rows.map(r => ({
      name: r.name,
      stars: r.stars,
      description: r.description,
      url: `https://github.com/${r.full_name}`,
    }));
    console.log(`   ✅ ${githubQuery.rows.length} repos (top: ${github[0]?.name || 'N/A'})`);

    // ========================================================================
    // NPM PACKAGES
    // ========================================================================
    console.log('📦 NPM Packages...');
    const npmQuery = await pool.query(`
      SELECT
        package_name as name,
        downloads_week as downloads,
        description
      FROM sofia.npm_stats
      WHERE collected_at >= $1
      ORDER BY downloads_week DESC
      LIMIT 10
    `, [filterDate]);

    const npm = npmQuery.rows.map(r => ({
      name: r.name,
      downloads: r.downloads,
      description: r.description,
      url: `https://www.npmjs.com/package/${r.name}`,
    }));
    console.log(`   ✅ ${npmQuery.rows.length} packages (top: ${npm[0]?.name || 'N/A'})`);

    // ========================================================================
    // PYPI PACKAGES
    // ========================================================================
    console.log('🐍 PyPI Packages...');
    const pypiQuery = await pool.query(`
      SELECT
        package_name as name,
        downloads_month as downloads,
        description
      FROM sofia.pypi_stats
      WHERE collected_at >= $1
      ORDER BY downloads_month DESC
      LIMIT 10
    `, [filterDate]);

    const pypi = pypiQuery.rows.map(r => ({
      name: r.name,
      downloads: r.downloads,
      description: r.description,
      url: `https://pypi.org/project/${r.name}`,
    }));
    console.log(`   ✅ ${pypiQuery.rows.length} packages (top: ${pypi[0]?.name || 'N/A'})`);

    // ========================================================================
    // HACKERNEWS
    // ========================================================================
    console.log('📰 HackerNews Stories...');
    const hnQuery = await pool.query(`
      SELECT
        title as name,
        points,
        url
      FROM sofia.hackernews_stories
      WHERE collected_at >= $1
      ORDER BY points DESC
      LIMIT 10
    `, [filterDate]);

    const hackernews = hnQuery.rows.map(r => ({
      name: r.name,
      points: r.points,
      url: r.url,
    }));
    console.log(`   ✅ ${hnQuery.rows.length} stories (top: ${hackernews[0]?.name || 'N/A'})`);

    // ========================================================================
    // SAVE CACHE
    // ========================================================================
    console.log('\n📊 Saving cache...\n');

    const cacheData: TrendingCache = {
      github,
      npm,
      pypi,
      hackernews,
      period: `${filterDate} to ${new Date().toISOString().split('T')[0]}`,
      generated_at: new Date().toISOString(),
      data_sources: {
        github_total: githubQuery.rows.length,
        npm_total: npmQuery.rows.length,
        pypi_total: pypiQuery.rows.length,
        hackernews_total: hnQuery.rows.length,
      },
    };

    const cacheDir = path.join(__dirname, '../cache');
    if (!fs.existsSync(cacheDir)) fs.mkdirSync(cacheDir, { recursive: true });

    const cacheFile = path.join(cacheDir, 'trending-tech.json');
    fs.writeFileSync(cacheFile, JSON.stringify(cacheData, null, 2));

    console.log('✅ Cache saved!\n');
    console.log('=' .repeat(80));
    console.log('📊 TRENDING TECH SUMMARY\n');

    console.log('🌟 GitHub Trending (Top 3):');
    github.slice(0, 3).forEach((r, idx) => {
      console.log(`   ${idx + 1}. ${r.name} (${r.stars?.toLocaleString()} ⭐)`);
    });

    console.log('\n📦 NPM Packages (Top 3):');
    npm.slice(0, 3).forEach((r, idx) => {
      console.log(`   ${idx + 1}. ${r.name} (${r.downloads?.toLocaleString()} downloads/week)`);
    });

    console.log('\n🐍 PyPI Packages (Top 3):');
    pypi.slice(0, 3).forEach((r, idx) => {
      console.log(`   ${idx + 1}. ${r.name} (${r.downloads?.toLocaleString()} downloads/month)`);
    });

    console.log('\n📰 HackerNews (Top 3):');
    hackernews.slice(0, 3).forEach((r, idx) => {
      console.log(`   ${idx + 1}. ${r.name} (${r.points} points)`);
    });

    console.log('\n' + '='.repeat(80));
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

generateTrendingCache();
