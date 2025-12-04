#!/usr/bin/env tsx
/**
 * AI Technology GitHub Trends Collector
 *
 * Tracks GitHub activity (repos, stars, forks) for AI technologies
 * across LLMs, agents, RAG, inference, multimodal, audio, devtools, data, and edge categories.
 *
 * Data source: GitHub Search API
 * Rate limiting: Uses rateLimiters.github with exponential backoff
 * Storage: sofia.ai_github_trends table
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
import { rateLimiters } from './utils/rate-limiter.js';
import * as fs from 'fs/promises';
import * as path from 'path';

dotenv.config();

// Database configuration
const dbConfig = {
  host: process.env.POSTGRES_HOST || process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || process.env.DB_PORT || '5432'),
  user: process.env.POSTGRES_USER || process.env.DB_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || process.env.DB_PASSWORD,
  database: process.env.POSTGRES_DB || process.env.DB_NAME || 'sofia_db',
};

// GitHub API configuration
const GITHUB_TOKEN = process.env.GITHUB_TOKEN || '';

if (!GITHUB_TOKEN) {
  console.warn('⚠️  No GITHUB_TOKEN found - API will be limited to 60 req/hour');
}

// AI Technology definitions (loaded from database or hardcoded)
interface AITechnology {
  tech_key: string;
  category: string;
  display_name: string;
  aliases: string[];
}

// GitHub search result interfaces
interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  html_url: string;
  description: string | null;
  stargazers_count: number;
  forks_count: number;
  language: string | null;
  topics: string[];
  created_at: string;
  updated_at: string;
  pushed_at: string;
}

interface GitHubSearchResponse {
  total_count: number;
  incomplete_results: boolean;
  items: GitHubRepo[];
}

interface AIGitHubTrend {
  tech_key: string;
  category: string;
  search_query: string;
  total_repos: number;
  total_stars: number;
  total_forks: number;
  stars_7d: number;
  stars_30d: number;
  forks_7d: number;
  forks_30d: number;
  top_repo_name?: string;
  top_repo_url?: string;
  top_repo_stars?: number;
  top_repo_description?: string;
  metadata: Record<string, any>;
}

/**
 * Load AI technologies from database
 */
async function loadAITechnologies(client: Client): Promise<AITechnology[]> {
  try {
    const result = await client.query(`
      SELECT tech_key, category, display_name, aliases
      FROM sofia.ai_tech_categories
      ORDER BY category, tech_key
    `);

    return result.rows;
  } catch (error) {
    console.warn('⚠️  Could not load from database, using hardcoded list');
    // Fallback to hardcoded list
    return getHardcodedTechnologies();
  }
}

/**
 * Hardcoded technologies (fallback if database is empty)
 */
function getHardcodedTechnologies(): AITechnology[] {
  return [
    // LLMs
    { tech_key: 'llama-3', category: 'llm', display_name: 'Llama 3', aliases: ['llama', 'meta-llama', 'llama3', 'llama 3'] },
    { tech_key: 'deepseek', category: 'llm', display_name: 'DeepSeek', aliases: ['deepseek', 'deepseek-r1', 'deepseek-v3'] },
    { tech_key: 'mistral', category: 'llm', display_name: 'Mistral', aliases: ['mistral', 'mixtral', 'codestral'] },
    { tech_key: 'phi-4', category: 'llm', display_name: 'Phi-4', aliases: ['phi-4', 'microsoft/phi', 'phi'] },
    { tech_key: 'gemma', category: 'llm', display_name: 'Gemma', aliases: ['gemma', 'google/gemma', 'gemma-2'] },
    { tech_key: 'qwen', category: 'llm', display_name: 'Qwen', aliases: ['qwen', 'qwen2.5', 'qwen2.5-coder'] },

    // Agent Frameworks
    { tech_key: 'langgraph', category: 'agents', display_name: 'LangGraph', aliases: ['langgraph', 'lang-graph'] },
    { tech_key: 'autogen', category: 'agents', display_name: 'AutoGen', aliases: ['autogen', 'autogen-2'] },
    { tech_key: 'crewai', category: 'agents', display_name: 'CrewAI', aliases: ['crewai', 'crew-ai'] },
    { tech_key: 'pydantic-ai', category: 'agents', display_name: 'Pydantic AI', aliases: ['pydantic-ai', 'pydantic_ai'] },

    // Inference
    { tech_key: 'vllm', category: 'inference', display_name: 'vLLM', aliases: ['vllm'] },
    { tech_key: 'tensorrt-llm', category: 'inference', display_name: 'TensorRT-LLM', aliases: ['tensorrt-llm', 'tensorrt'] },
    { tech_key: 'onnxruntime', category: 'inference', display_name: 'ONNX Runtime', aliases: ['onnxruntime', 'onnxruntime-gpu'] },
    { tech_key: 'transformers-js', category: 'inference', display_name: 'Transformers.js', aliases: ['transformers.js', 'transformersjs'] },

    // RAG
    { tech_key: 'graphrag', category: 'rag', display_name: 'GraphRAG', aliases: ['graphrag', 'graph-rag'] },
    { tech_key: 'chromadb', category: 'rag', display_name: 'ChromaDB', aliases: ['chromadb', 'chroma'] },
    { tech_key: 'pgvector', category: 'rag', display_name: 'pgvector', aliases: ['pgvector', 'pg-vector'] },

    // Dev Tools
    { tech_key: 'aider', category: 'devtools', display_name: 'Aider', aliases: ['aider', 'aider-chat'] },
    { tech_key: 'continue-dev', category: 'devtools', display_name: 'Continue', aliases: ['continue', 'continue-dev'] },
    { tech_key: 'cursor-ai', category: 'devtools', display_name: 'Cursor', aliases: ['cursor'] },
  ];
}

/**
 * Search GitHub for a technology
 */
async function searchGitHub(query: string, createdAfter?: string): Promise<GitHubSearchResponse> {
  let searchQuery = query;

  if (createdAfter) {
    searchQuery += ` created:>=${createdAfter}`;
  }

  const url = `https://api.github.com/search/repositories?q=${encodeURIComponent(searchQuery)}&sort=stars&order=desc&per_page=100`;

  try {
    const response = await rateLimiters.github.get<GitHubSearchResponse>(url, {
      headers: {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'Sofia-Pulse-AI-Tech-Radar/1.0',
        ...(GITHUB_TOKEN && { 'Authorization': `Bearer ${GITHUB_TOKEN}` }),
      },
      timeout: 30000,
    });

    return response.data;
  } catch (error: any) {
    console.error(`❌ GitHub search failed for "${query}":`, error.message);
    return { total_count: 0, incomplete_results: false, items: [] };
  }
}

/**
 * Calculate stars/forks gained in time period
 */
function calculateDelta(repos: GitHubRepo[], daysAgo: number): { stars: number; forks: number } {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - daysAgo);

  // Filter repos created/updated after cutoff
  const recentRepos = repos.filter(repo => {
    const updatedAt = new Date(repo.updated_at || repo.created_at);
    return updatedAt >= cutoffDate;
  });

  const stars = recentRepos.reduce((sum, repo) => sum + repo.stargazers_count, 0);
  const forks = recentRepos.reduce((sum, repo) => sum + repo.forks_count, 0);

  return { stars, forks };
}

/**
 * Collect trends for a single technology
 */
async function collectTechTrends(tech: AITechnology): Promise<AIGitHubTrend | null> {
  console.log(`  📊 Collecting: ${tech.display_name} (${tech.tech_key})`);

  // Build search query from aliases
  const searchTerms = tech.aliases.map(alias => `"${alias}"`).join(' OR ');
  const searchQuery = `(${searchTerms}) in:name,description,readme`;

  try {
    // Search all repos
    const allRepos = await searchGitHub(searchQuery);
    await new Promise(resolve => setTimeout(resolve, 2000)); // Rate limiting

    // Search repos created in last 30 days
    const cutoff30d = new Date();
    cutoff30d.setDate(cutoff30d.getDate() - 30);
    const recent30d = await searchGitHub(searchQuery, cutoff30d.toISOString().split('T')[0]);
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Search repos created in last 7 days
    const cutoff7d = new Date();
    cutoff7d.setDate(cutoff7d.getDate() - 7);
    const recent7d = await searchGitHub(searchQuery, cutoff7d.toISOString().split('T')[0]);
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Calculate metrics
    const totalStars = allRepos.items.reduce((sum, repo) => sum + repo.stargazers_count, 0);
    const totalForks = allRepos.items.reduce((sum, repo) => sum + repo.forks_count, 0);

    const stars30d = recent30d.items.reduce((sum, repo) => sum + repo.stargazers_count, 0);
    const forks30d = recent30d.items.reduce((sum, repo) => sum + repo.forks_count, 0);

    const stars7d = recent7d.items.reduce((sum, repo) => sum + repo.stargazers_count, 0);
    const forks7d = recent7d.items.reduce((sum, repo) => sum + repo.forks_count, 0);

    // Get top repository
    const topRepo = allRepos.items[0];

    const trend: AIGitHubTrend = {
      tech_key: tech.tech_key,
      category: tech.category,
      search_query: searchQuery,
      total_repos: allRepos.total_count,
      total_stars: totalStars,
      total_forks: totalForks,
      stars_7d: stars7d,
      stars_30d: stars30d,
      forks_7d: forks7d,
      forks_30d: forks30d,
      top_repo_name: topRepo?.full_name,
      top_repo_url: topRepo?.html_url,
      top_repo_stars: topRepo?.stargazers_count,
      top_repo_description: topRepo?.description || undefined,
      metadata: {
        incomplete_results: allRepos.incomplete_results,
        top_repos_count: Math.min(allRepos.items.length, 10),
      },
    };

    console.log(`    ✅ ${tech.display_name}: ${trend.total_repos} repos, ${trend.total_stars.toLocaleString()} stars, ${trend.stars_30d} stars/30d`);

    return trend;
  } catch (error: any) {
    console.error(`    ❌ Failed to collect ${tech.display_name}:`, error.message);
    return null;
  }
}

/**
 * Insert trend data into database
 */
async function insertTrend(client: Client, trend: AIGitHubTrend): Promise<void> {
  await client.query(`
    INSERT INTO sofia.ai_github_trends (
      tech_key, category, search_query,
      total_repos, total_stars, total_forks,
      stars_7d, stars_30d, forks_7d, forks_30d,
      top_repo_name, top_repo_url, top_repo_stars, top_repo_description,
      metadata, date
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, CURRENT_DATE)
    ON CONFLICT (tech_key, date) DO UPDATE SET
      search_query = EXCLUDED.search_query,
      total_repos = EXCLUDED.total_repos,
      total_stars = EXCLUDED.total_stars,
      total_forks = EXCLUDED.total_forks,
      stars_7d = EXCLUDED.stars_7d,
      stars_30d = EXCLUDED.stars_30d,
      forks_7d = EXCLUDED.forks_7d,
      forks_30d = EXCLUDED.forks_30d,
      top_repo_name = EXCLUDED.top_repo_name,
      top_repo_url = EXCLUDED.top_repo_url,
      top_repo_stars = EXCLUDED.top_repo_stars,
      top_repo_description = EXCLUDED.top_repo_description,
      metadata = EXCLUDED.metadata,
      collected_at = NOW()
  `, [
    trend.tech_key,
    trend.category,
    trend.search_query,
    trend.total_repos,
    trend.total_stars,
    trend.total_forks,
    trend.stars_7d,
    trend.stars_30d,
    trend.forks_7d,
    trend.forks_30d,
    trend.top_repo_name,
    trend.top_repo_url,
    trend.top_repo_stars,
    trend.top_repo_description,
    JSON.stringify(trend.metadata),
  ]);
}

/**
 * Main function
 */
async function main() {
  console.log('='.repeat(80));
  console.log('🚀 AI TECHNOLOGY GITHUB TRENDS COLLECTOR');
  console.log('='.repeat(80));

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    // Run migration
    console.log('📦 Running migration...');
    const migrationPath = path.join(__dirname, '..', 'db', 'migrations', '020_create_ai_tech_radar.sql');
    try {
      const migrationSQL = await fs.readFile(migrationPath, 'utf-8');
      await client.query(migrationSQL);
      console.log('✅ Migration complete');
    } catch (error: any) {
      console.warn('⚠️  Migration failed (tables may already exist):', error.message);
    }

    // Load technologies
    console.log('\n📚 Loading AI technologies...');
    const technologies = await loadAITechnologies(client);
    console.log(`✅ Loaded ${technologies.length} technologies across ${new Set(technologies.map(t => t.category)).size} categories`);

    // Collect trends
    console.log('\n📊 Collecting GitHub trends...\n');
    let successCount = 0;
    let failCount = 0;

    for (const tech of technologies) {
      const trend = await collectTechTrends(tech);

      if (trend) {
        await insertTrend(client, trend);
        successCount++;
      } else {
        failCount++;
      }
    }

    // Summary
    console.log('\n' + '='.repeat(80));
    console.log('✅ AI GITHUB TRENDS COLLECTION COMPLETE');
    console.log('='.repeat(80));
    console.log(`✅ Success: ${successCount} technologies`);
    console.log(`❌ Failed: ${failCount} technologies`);
    console.log(`📊 Total: ${technologies.length} technologies`);
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
