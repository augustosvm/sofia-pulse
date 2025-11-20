#!/usr/bin/env tsx

/**
 * Sofia Pulse - GitHub Niches Collector
 *
 * Coleta repos de GitHub para nichos específicos:
 * - Gestão de Projetos (PMI, Agile, Scrum)
 * - Governança (COBIT, ITIL, ISO)
 * - Carreira Tech (Interview prep, Resume, Learning paths)
 * - Cloud Computing (AWS, Azure, GCP, Kubernetes)
 * - Big Data (Hadoop, Spark, Kafka)
 *
 * API: https://api.github.com/search/repositories
 */

import { Client } from 'pg';
import * as dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

const DB_CONFIG = {
  host: process.env.POSTGRES_HOST || process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || process.env.DB_PORT || '5432'),
  user: process.env.POSTGRES_USER || process.env.DB_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD || process.env.DB_PASSWORD || 'sofia123strong',
  database: process.env.POSTGRES_DB || process.env.DB_NAME || 'sofia_db',
};

interface GitHubRepo {
  niche: string;
  repo_name: string;
  full_name: string;
  description: string | null;
  stars: number;
  forks: number;
  watchers: number;
  language: string | null;
  topics: string[];
  created_at: string;
  updated_at: string;
  pushed_at: string;
  url: string;
  homepage: string | null;
  is_archived: boolean;
  is_fork: boolean;
  license: string | null;
}

// Nichos para buscar (topic:keyword no GitHub)
const NICHES = {
  'Project Management': ['project-management', 'agile', 'scrum', 'kanban', 'jira', 'trello'],
  'Governance': ['governance', 'cobit', 'itil', 'iso27001', 'compliance', 'soc2'],
  'Tech Career': ['interview-preparation', 'resume', 'career-development', 'tech-interview', 'coding-interview'],
  'Cloud Computing': ['aws', 'azure', 'google-cloud', 'kubernetes', 'docker', 'terraform'],
  'Big Data': ['hadoop', 'spark', 'kafka', 'flink', 'databricks', 'airflow'],
  'Data Engineering': ['data-engineering', 'etl', 'data-pipeline', 'data-warehouse', 'dbt'],
  'DevOps': ['devops', 'cicd', 'jenkins', 'github-actions', 'gitlab-ci'],
};

async function createTable(client: Client): Promise<void> {
  await client.query(`
    CREATE TABLE IF NOT EXISTS sofia.github_niches (
      id SERIAL PRIMARY KEY,
      niche VARCHAR(100) NOT NULL,
      repo_name VARCHAR(255) NOT NULL,
      full_name VARCHAR(255) UNIQUE NOT NULL,
      description TEXT,
      stars INTEGER DEFAULT 0,
      forks INTEGER DEFAULT 0,
      watchers INTEGER DEFAULT 0,
      language VARCHAR(50),
      topics TEXT[],
      created_at TIMESTAMPTZ,
      updated_at TIMESTAMPTZ,
      pushed_at TIMESTAMPTZ,
      url TEXT,
      homepage TEXT,
      is_archived BOOLEAN DEFAULT FALSE,
      is_fork BOOLEAN DEFAULT FALSE,
      license VARCHAR(100),
      collected_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_github_niches_niche ON sofia.github_niches(niche);
    CREATE INDEX IF NOT EXISTS idx_github_niches_stars ON sofia.github_niches(stars DESC);
    CREATE INDEX IF NOT EXISTS idx_github_niches_topics ON sofia.github_niches USING GIN(topics);
  `);

  console.log('✅ Table github_niches ready');
}

async function searchGitHub(niche: string, topic: string): Promise<any[]> {
  try {
    // GitHub API: search repos by topic
    const url = `https://api.github.com/search/repositories?q=topic:${topic}+stars:>100&sort=stars&order=desc&per_page=10`;

    const response = await axios.get(url, {
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Sofia-Pulse-Collector',
      },
    });

    const repos = response.data.items || [];
    console.log(`   ✅ ${repos.length} repos for ${niche} (${topic})`);

    return repos.map((repo: any) => ({
      niche,
      repo_name: repo.name,
      full_name: repo.full_name,
      description: repo.description,
      stars: repo.stargazers_count,
      forks: repo.forks_count,
      watchers: repo.watchers_count,
      language: repo.language,
      topics: repo.topics || [],
      created_at: repo.created_at,
      updated_at: repo.updated_at,
      pushed_at: repo.pushed_at,
      url: repo.html_url,
      homepage: repo.homepage,
      is_archived: repo.archived,
      is_fork: repo.fork,
      license: repo.license?.spdx_id || null,
    }));

  } catch (error: any) {
    console.log(`   ⚠️  Error fetching ${niche} (${topic}):`, error.message);
    return [];
  }
}

async function insertRepo(client: Client, repo: GitHubRepo): Promise<void> {
  await client.query(`
    INSERT INTO sofia.github_niches (
      niche, repo_name, full_name, description, stars, forks, watchers,
      language, topics, created_at, updated_at, pushed_at, url, homepage,
      is_archived, is_fork, license
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
    ON CONFLICT (full_name) DO UPDATE SET
      stars = EXCLUDED.stars,
      forks = EXCLUDED.forks,
      watchers = EXCLUDED.watchers,
      updated_at = EXCLUDED.updated_at,
      pushed_at = EXCLUDED.pushed_at,
      collected_at = NOW()
  `, [
    repo.niche, repo.repo_name, repo.full_name, repo.description,
    repo.stars, repo.forks, repo.watchers, repo.language, repo.topics,
    repo.created_at, repo.updated_at, repo.pushed_at, repo.url,
    repo.homepage, repo.is_archived, repo.is_fork, repo.license
  ]);
}

async function main() {
  console.log('🚀 Sofia Pulse - GitHub Niches Collector');
  console.log('='.repeat(60));
  console.log('');
  console.log('🎯 Nichos:');
  Object.keys(NICHES).forEach(niche => {
    console.log(`   • ${niche}`);
  });
  console.log('');

  const client = new Client(DB_CONFIG);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    await createTable(client);

    let totalRepos = 0;

    for (const [niche, topics] of Object.entries(NICHES)) {
      console.log(`\n📊 Collecting ${niche}...`);

      for (const topic of topics) {
        const repos = await searchGitHub(niche, topic);

        for (const repo of repos) {
          await insertRepo(client, repo);
        }

        totalRepos += repos.length;

        // Rate limit: 1 request per second (GitHub allows 60/hour unauthenticated)
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }

    console.log('');
    console.log('='.repeat(60));
    console.log(`✅ Collection complete! Total: ${totalRepos} repos`);

  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

main().catch(console.error);
