#!/usr/bin/env tsx
/**
 * AI Technology NPM Packages Collector
 *
 * Tracks NPM download statistics for AI/ML JavaScript packages
 *
 * Data source: NPM Registry API + npm-stat.com API
 * Storage: sofia.ai_npm_packages table
 */

// Fix for Node.js 18 + undici compatibility
if (typeof File === 'undefined') {
  globalThis.File = class File extends Blob {
    name: string;
    lastModified: number;
    constructor(bits: BlobPart[], name: string, options?: FilePropertyBag) {
      super(bits, options);
      this.name = name;
      this.lastModified = options?.lastModified ?? Date.now();
    }
  };
}

import { Client } from 'pg';
import * as dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

// Database configuration
const dbConfig = {
  host: process.env.POSTGRES_HOST || process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || process.env.DB_PORT || '5432'),
  user: process.env.POSTGRES_USER || process.env.DB_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || process.env.DB_PASSWORD,
  database: process.env.POSTGRES_DB || process.env.DB_NAME || 'sofia_db',
};

// NPM package mappings
// Format: [package_name, tech_key, category]
const NPM_PACKAGES: Array<[string, string, string]> = [
  // AI APIs
  ['@google/generative-ai', 'gemini', 'llm'],
  ['openai', 'gpt-4', 'llm'],
  ['@anthropic-ai/sdk', 'claude', 'llm'],
  ['groq-sdk', 'grok', 'llm'],

  // Agent Frameworks
  ['langchain', 'langchain', 'agents'],
  ['@langchain/core', 'langchain', 'agents'],
  ['@langchain/community', 'langchain', 'agents'],
  ['langgraph', 'langgraph', 'agents'],
  ['llamaindex', 'llamaindex', 'rag'],

  // Inference
  ['onnxruntime-web', 'onnxruntime', 'inference'],
  ['onnxruntime-node', 'onnxruntime', 'inference'],
  ['@xenova/transformers', 'transformers-js', 'inference'],
  ['@mlc-ai/web-llm', 'mlc-llm', 'inference'],

  // Vector Databases
  ['chromadb', 'chromadb', 'rag'],
  ['hnswlib-node', 'faiss', 'rag'],
  ['pinecone-client', 'pinecone', 'rag'],
  ['@qdrant/js-client-rest', 'qdrant', 'rag'],
  ['weaviate-ts-client', 'weaviate', 'rag'],
  ['lancedb', 'lancedb', 'rag'],

  // Data Processing
  ['duckdb', 'duckdb', 'data'],

  // Observability
  ['langfuse', 'langfuse', 'observability'],
  ['langsmith', 'langsmith', 'observability'],

  // Embeddings
  ['@xenova/transformers', 'sentence-transformers', 'rag'],
];

interface PackageStats {
  package_name: string;
  tech_key: string;
  category: string;
  downloads_7d: number;
  downloads_30d: number;
  downloads_90d: number;
  version?: string;
  description?: string;
  homepage_url?: string;
  repository_url?: string;
}

/**
 * Get NPM package statistics
 */
async function getNPMStats(packageName: string): Promise<Partial<PackageStats> | null> {
  try {
    const stats: Partial<PackageStats> = {
      package_name: packageName,
      downloads_7d: 0,
      downloads_30d: 0,
      downloads_90d: 0,
    };

    // 1. Get download stats from NPM API
    const now = new Date();
    const last7d = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const last30d = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    // NPM stats API
    const downloadsUrl = `https://api.npmjs.org/downloads/point/last-month/${packageName}`;
    const downloadsResponse = await axios.get(downloadsUrl, { timeout: 10000 });

    if (downloadsResponse.status === 200) {
      stats.downloads_30d = downloadsResponse.data.downloads || 0;
      // Estimate 7d as ~25% of monthly, 90d as 3x monthly
      stats.downloads_7d = Math.round(stats.downloads_30d * 0.25);
      stats.downloads_90d = stats.downloads_30d * 3;
    }

    // 2. Get package metadata
    const metadataUrl = `https://registry.npmjs.org/${packageName}`;
    const metadataResponse = await axios.get(metadataUrl, { timeout: 10000 });

    if (metadataResponse.status === 200) {
      const data = metadataResponse.data;
      const latest = data['dist-tags']?.latest;

      if (latest && data.versions && data.versions[latest]) {
        const versionData = data.versions[latest];
        stats.version = latest;
        stats.description = versionData.description || '';
        stats.homepage_url = versionData.homepage || data.homepage;

        // Extract repository URL
        if (versionData.repository) {
          const repo = versionData.repository;
          if (typeof repo === 'string') {
            stats.repository_url = repo;
          } else if (repo.url) {
            stats.repository_url = repo.url.replace(/^git\+/, '').replace(/\.git$/, '');
          }
        }
      }
    }

    console.log(`  ✅ ${packageName}: ${stats.downloads_30d?.toLocaleString()} downloads/month`);
    return stats;

  } catch (error: any) {
    if (error.response?.status === 404) {
      console.log(`  ⚠️  ${packageName}: Not found on NPM`);
    } else {
      console.error(`  ❌ ${packageName}: ${error.message}`);
    }
    return null;
  }
}

/**
 * Insert data into database
 */
async function insertStats(client: Client, stats: PackageStats[]): Promise<number> {
  if (stats.length === 0) return 0;

  const query = `
    INSERT INTO sofia.ai_npm_packages (
      package_name, tech_key, category,
      downloads_7d, downloads_30d, downloads_90d,
      version, description, homepage_url, repository_url,
      date
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, CURRENT_DATE)
    ON CONFLICT (package_name, date) DO UPDATE SET
      tech_key = EXCLUDED.tech_key,
      category = EXCLUDED.category,
      downloads_7d = EXCLUDED.downloads_7d,
      downloads_30d = EXCLUDED.downloads_30d,
      downloads_90d = EXCLUDED.downloads_90d,
      version = EXCLUDED.version,
      description = EXCLUDED.description,
      homepage_url = EXCLUDED.homepage_url,
      repository_url = EXCLUDED.repository_url,
      collected_at = NOW()
  `;

  let inserted = 0;
  for (const stat of stats) {
    await client.query(query, [
      stat.package_name,
      stat.tech_key,
      stat.category,
      stat.downloads_7d,
      stat.downloads_30d,
      stat.downloads_90d,
      stat.version,
      stat.description,
      stat.homepage_url,
      stat.repository_url,
    ]);
    inserted++;
  }

  return inserted;
}

/**
 * Main function
 */
async function main() {
  console.log('='.repeat(80));
  console.log('🚀 AI NPM PACKAGES COLLECTOR');
  console.log('='.repeat(80));

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    console.log(`\n📦 Collecting stats for ${NPM_PACKAGES.length} NPM packages...\n`);

    const allStats: PackageStats[] = [];
    let successCount = 0;
    let failCount = 0;

    for (const [packageName, techKey, category] of NPM_PACKAGES) {
      const stats = await getNPMStats(packageName);

      if (stats && stats.downloads_30d !== undefined) {
        allStats.push({
          package_name: packageName,
          tech_key: techKey,
          category: category,
          downloads_7d: stats.downloads_7d || 0,
          downloads_30d: stats.downloads_30d || 0,
          downloads_90d: stats.downloads_90d || 0,
          version: stats.version,
          description: stats.description,
          homepage_url: stats.homepage_url,
          repository_url: stats.repository_url,
        });
        successCount++;
      } else {
        failCount++;
      }

      // Rate limiting
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    // Insert into database
    if (allStats.length > 0) {
      const inserted = await insertStats(client, allStats);
      console.log(`\n✅ Inserted ${inserted} NPM package records`);
    }

    // Summary
    console.log('\n' + '='.repeat(80));
    console.log('✅ AI NPM COLLECTION COMPLETE');
    console.log('='.repeat(80));
    console.log(`✅ Success: ${successCount} packages`);
    console.log(`❌ Failed: ${failCount} packages`);
    console.log(`📊 Total: ${NPM_PACKAGES.length} packages`);

    // Top packages
    if (allStats.length > 0) {
      console.log('\n📈 TOP 10 PACKAGES BY DOWNLOADS (30d):');
      const sorted = allStats.sort((a, b) => b.downloads_30d - a.downloads_30d).slice(0, 10);
      sorted.forEach((stat, i) => {
        console.log(`  ${i + 1}. ${stat.package_name}: ${stat.downloads_30d.toLocaleString()} downloads/month`);
      });
    }

    console.log('='.repeat(80));

  } catch (error) {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

if (require.main === module) {
  main();
}
