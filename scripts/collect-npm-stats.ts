#!/usr/bin/env tsx

import { Client } from 'pg';
import * as dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

const dbConfig = {
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || 'postgres',
  database: process.env.POSTGRES_DB || 'sofia_db',
};

interface NPMStats {
  package_name: string;
  downloads_day: number;
  downloads_week: number;
  downloads_month: number;
  version: string;
  description: string;
  keywords: string[];
}

const POPULAR_PACKAGES = [
  'react', 'vue', 'angular', 'svelte', 'next', 'nuxt',
  'express', 'fastify', 'nestjs', 'koa',
  'typescript', 'webpack', 'vite', 'esbuild',
  'axios', 'lodash', 'moment', 'dayjs',
  'jest', 'vitest', 'mocha', 'chai',
  'eslint', 'prettier', 'babel',
  'tailwindcss', 'styled-components', 'emotion',
  '@tensorflow/tfjs', 'three', 'd3',
];

async function fetchNPMDownloads(pkg: string): Promise<{ day: number; week: number; month: number } | null> {
  try {
    const ranges = {
      day: `last-day`,
      week: `last-week`,
      month: `last-month`,
    };

    const results: any = {};

    for (const [period, range] of Object.entries(ranges)) {
      const url = `https://api.npmjs.org/downloads/point/${range}/${pkg}`;
      const response = await axios.get(url, { timeout: 10000 });
      results[period] = response.data.downloads || 0;
      await new Promise(resolve => setTimeout(resolve, 200));
    }

    return {
      day: results.day,
      week: results.week,
      month: results.month,
    };
  } catch (error: any) {
    return null;
  }
}

async function fetchNPMPackageInfo(pkg: string): Promise<{ version: string; description: string; keywords: string[] } | null> {
  try {
    const url = `https://registry.npmjs.org/${pkg}/latest`;
    const response = await axios.get(url, { timeout: 10000 });

    return {
      version: response.data.version || 'unknown',
      description: response.data.description || '',
      keywords: response.data.keywords || [],
    };
  } catch (error: any) {
    return null;
  }
}

async function insertStats(client: Client, stats: NPMStats): Promise<void> {
  const query = `
    INSERT INTO sofia.npm_stats (
      package_name, downloads_day, downloads_week, downloads_month,
      version, description, keywords
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    ON CONFLICT (package_name, DATE(collected_at)) DO UPDATE SET
      downloads_day = EXCLUDED.downloads_day,
      downloads_week = EXCLUDED.downloads_week,
      downloads_month = EXCLUDED.downloads_month,
      collected_at = NOW();
  `;

  await client.query(query, [
    stats.package_name,
    stats.downloads_day,
    stats.downloads_week,
    stats.downloads_month,
    stats.version,
    stats.description,
    stats.keywords,
  ]);
}

async function main() {
  console.log('📦 NPM Stats Collector');
  console.log('='.repeat(60));

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    const fs = await import('fs/promises');
    const migrationSQL = await fs.readFile('db/migrations/013_create_npm_stats.sql', 'utf-8');
    await client.query(migrationSQL);

    let collected = 0;

    for (const pkg of POPULAR_PACKAGES) {
      console.log(`📊 Fetching ${pkg}...`);

      const downloads = await fetchNPMDownloads(pkg);
      if (!downloads) {
        console.log(`   ⚠️  Failed`);
        continue;
      }

      const info = await fetchNPMPackageInfo(pkg);

      const stats: NPMStats = {
        package_name: pkg,
        downloads_day: downloads.day,
        downloads_week: downloads.week,
        downloads_month: downloads.month,
        version: info?.version || 'unknown',
        description: info?.description || '',
        keywords: info?.keywords || [],
      };

      await insertStats(client, stats);
      console.log(`   ✅ ${downloads.month.toLocaleString()} downloads/month`);

      collected++;
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    console.log(`✅ Total: ${collected} packages collected`);

  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

if (require.main === module) {
  main();
}
