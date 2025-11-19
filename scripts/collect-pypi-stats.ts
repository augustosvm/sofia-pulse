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


import { Client } from 'pg';
import * as dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

const dbConfig = {
  host: process.env.DB_HOST || process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || process.env.POSTGRES_PORT || '5432'),
  user: process.env.DB_USER || process.env.POSTGRES_USER || 'sofia',
  password: process.env.DB_PASSWORD || process.env.POSTGRES_PASSWORD,
  database: process.env.DB_NAME || process.env.POSTGRES_DB || 'sofia_db',
};

interface PyPIStats {
  package_name: string;
  downloads_month: number;
  version: string;
  description: string;
  keywords: string[];
}

const POPULAR_PACKAGES = [
  'numpy', 'pandas', 'matplotlib', 'scipy', 'scikit-learn',
  'tensorflow', 'pytorch', 'keras', 'transformers',
  'requests', 'flask', 'django', 'fastapi',
  'pytest', 'black', 'mypy', 'pylint',
  'sqlalchemy', 'pydantic', 'click', 'typer',
  'pillow', 'opencv-python', 'beautifulsoup4',
  'selenium', 'scrapy', 'aiohttp',
];

async function fetchPyPIStats(pkg: string): Promise<{ downloads: number; version: string; description: string } | null> {
  try {
    // PyPI stats API (via pypistats.org)
    const statsUrl = `https://pypistats.org/api/packages/${pkg}/recent?period=month`;
    const statsResponse = await axios.get(statsUrl, { timeout: 10000 });

    const downloads = statsResponse.data?.data?.last_month || 0;

    // PyPI package info
    const infoUrl = `https://pypi.org/pypi/${pkg}/json`;
    const infoResponse = await axios.get(infoUrl, { timeout: 10000 });

    return {
      downloads,
      version: infoResponse.data.info.version,
      description: infoResponse.data.info.summary || '',
    };
  } catch (error: any) {
    return null;
  }
}

async function insertStats(client: Client, stats: PyPIStats): Promise<void> {
  const query = `
    INSERT INTO sofia.pypi_stats (
      package_name, downloads_month, version, description, keywords
    )
    VALUES ($1, $2, $3, $4, $5)
    ON CONFLICT (package_name, DATE(collected_at)) DO UPDATE SET
      downloads_month = EXCLUDED.downloads_month,
      collected_at = NOW();
  `;

  await client.query(query, [
    stats.package_name,
    stats.downloads_month,
    stats.version,
    stats.description,
    stats.keywords,
  ]);
}

async function main() {
  console.log('🐍 PyPI Stats Collector');
  console.log('='.repeat(60));

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    const fs = await import('fs/promises');
    const migrationSQL = await fs.readFile('db/migrations/014_create_pypi_stats.sql', 'utf-8');
    await client.query(migrationSQL);

    let collected = 0;

    for (const pkg of POPULAR_PACKAGES) {
      console.log(`📊 Fetching ${pkg}...`);

      const data = await fetchPyPIStats(pkg);
      if (!data) {
        console.log(`   ⚠️  Failed`);
        continue;
      }

      const stats: PyPIStats = {
        package_name: pkg,
        downloads_month: data.downloads,
        version: data.version,
        description: data.description,
        keywords: [],
      };

      await insertStats(client, stats);
      console.log(`   ✅ ${data.downloads.toLocaleString()} downloads/month`);

      collected++;
      await new Promise(resolve => setTimeout(resolve, 1500));
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
