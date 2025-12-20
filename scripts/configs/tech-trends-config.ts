/**
 * Collectors Configuration - Sofia Pulse
 *
 * Todas as configurações dos 88 collectors em um único arquivo.
 * Cada config define: URL, parsing, schedule, rate limits, etc.
 *
 * Schedule format (cron):
 *   '0 12 * * *'    = Daily at noon
 *   '0 8 * * *'     = Daily at 8am
 *   '0 8 * * 1'     = Weekly on Monday at 8am
 *   '0 8 1 * *'     = Monthly on 1st at 8am
 */

import { CollectorConfig } from '../collectors/tech-trends-collector.js';
import { TrendData } from '../shared/trends-inserter.js';

// ============================================================================
// TECH TRENDS COLLECTORS
// ============================================================================

export const githubTrending: CollectorConfig = {
  name: 'github',
  displayName: '🐙 GitHub Trending Repositories',
  description: 'Trending repos - 80% do valor de Tech Intelligence',

  url: 'https://api.github.com/search/repositories?q=created:>2024-01-01%20stars:>500&sort=stars&order=desc&per_page=100',

  headers: (env) => {
    const headers: Record<string, string> = {
      'Accept': 'application/vnd.github.v3+json',
    };
    if (env.GITHUB_TOKEN) {
      headers['Authorization'] = `Bearer ${env.GITHUB_TOKEN}`;
    }
    return headers;
  },

  rateLimit: 'github', // Usa rateLimiters.github (com backoff)

  parseResponse: (data) => {
    if (!data.items || !Array.isArray(data.items)) {
      return [];
    }

    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    return data.items.map((item: any): TrendData => ({
      source: 'github',
      name: item.full_name,
      category: item.language || undefined,
      trend_type: 'repository',
      score: item.stargazers_count,
      stars: item.stargazers_count,
      forks: item.forks_count,
      period_start: weekAgo,
      period_end: now,
      metadata: {
        repo_id: item.id,
        owner: item.owner.login,
        description: item.description,
        homepage: item.homepage,
        watchers: item.watchers_count,
        open_issues: item.open_issues_count,
        topics: item.topics || [],
        license: item.license?.spdx_id || null,
        is_fork: item.fork,
        is_archived: item.archived,
        created_at: item.created_at,
        updated_at: item.updated_at,
        pushed_at: item.pushed_at,
      }
    }));
  },

  schedule: '0 */12 * * *', // 2x/dia (0h e 12h)
  allowWithoutAuth: false, // Precisa de GITHUB_TOKEN
};

export const npmStats: CollectorConfig = {
  name: 'npm',
  displayName: '📦 NPM Package Stats',
  description: 'Top packages JavaScript - downloads mensais',

  // NPM requer múltiplas requests (1 por package)
  // Por isso usamos uma função que retorna um array de packages
  url: 'https://api.npmjs.org/downloads/point/last-month/react', // Placeholder

  parseResponse: async (_, env) => {
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

    const now = new Date();
    const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    const trends: TrendData[] = [];

    // Fetch stats for each package
    const axios = (await import('axios')).default;

    for (const pkg of POPULAR_PACKAGES) {
      try {
        const url = `https://api.npmjs.org/downloads/point/last-month/${pkg}`;
        const response = await axios.get(url, { timeout: 10000 });

        if (response.data && response.data.downloads) {
          trends.push({
            source: 'npm',
            name: pkg,
            trend_type: 'package',
            category: 'javascript',
            score: response.data.downloads,
            mentions: response.data.downloads,
            period_start: monthAgo,
            period_end: now,
            metadata: {
              downloads: response.data.downloads,
              period: response.data.start + ' to ' + response.data.end,
            }
          });
        }

        // Rate limiting: 1 req/segundo
        await new Promise(resolve => setTimeout(resolve, 1000));
      } catch (error) {
        console.warn(`   ⚠️  Failed to fetch ${pkg}`);
      }
    }

    return trends;
  },

  schedule: '0 8 * * *', // 1x/dia às 8h
  timeout: 60000, // 60s (porque faz múltiplas requests)
  allowWithoutAuth: true,
};

export const pypiStats: CollectorConfig = {
  name: 'pypi',
  displayName: '🐍 PyPI Package Stats',
  description: 'Top packages Python - downloads mensais',

  url: 'https://pypi.org/pypi/numpy/json', // Placeholder

  parseResponse: async (_, env) => {
    const POPULAR_PACKAGES = [
      'numpy', 'pandas', 'matplotlib', 'scipy', 'scikit-learn',
      'tensorflow', 'pytorch', 'keras', 'transformers',
      'requests', 'flask', 'django', 'fastapi',
      'pytest', 'black', 'mypy', 'pylint',
      'sqlalchemy', 'pydantic', 'click', 'typer',
      'pillow', 'opencv-python', 'beautifulsoup4',
      'selenium', 'scrapy', 'aiohttp',
    ];

    const now = new Date();
    const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    const trends: TrendData[] = [];
    const axios = (await import('axios')).default;

    for (const pkg of POPULAR_PACKAGES) {
      try {
        // PyPI stats via pypistats.org
        const statsUrl = `https://pypistats.org/api/packages/${pkg}/recent?period=month`;
        const statsResponse = await axios.get(statsUrl, { timeout: 10000 });

        const downloads = statsResponse.data?.data?.last_month || 0;

        if (downloads > 0) {
          trends.push({
            source: 'pypi',
            name: pkg,
            trend_type: 'package',
            category: 'python',
            score: downloads,
            mentions: downloads,
            period_start: monthAgo,
            period_end: now,
            metadata: {
              downloads_month: downloads,
            }
          });
        }

        // Rate limiting: 1.5s entre requests
        await new Promise(resolve => setTimeout(resolve, 1500));
      } catch (error) {
        console.warn(`   ⚠️  Failed to fetch ${pkg}`);
      }
    }

    return trends;
  },

  schedule: '0 20 * * *', // 1x/dia às 20h (diferente do NPM)
  timeout: 90000, // 90s
  allowWithoutAuth: true,
};

export const hackerNews: CollectorConfig = {
  name: 'hackernews',
  displayName: '🔥 HackerNews Top Stories',
  description: 'Buzz tecnológico - termômetro da comunidade tech',

  url: 'https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=100',

  parseResponse: (data) => {
    if (!data.hits || !Array.isArray(data.hits)) {
      return [];
    }

    const now = new Date();
    const dayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    return data.hits
      .filter((hit: any) => hit.points && hit.points >= 10)
      .map((hit: any): TrendData => {
        const storyId = hit.objectID.match(/\d+/)?.[0] || '0';

        return {
          source: 'hackernews',
          name: hit.title,
          trend_type: 'story',
          score: hit.points || 0,
          mentions: hit.num_comments || 0,
          period_start: dayAgo,
          period_end: now,
          metadata: {
            story_id: parseInt(storyId),
            object_id: hit.objectID,
            author: hit.author,
            url: hit.url,
            created_at: hit.created_at,
            tags: hit._tags || [],
          }
        };
      });
  },

  schedule: '0 */12 * * *', // 2x/dia (mesma freq que GitHub)
  allowWithoutAuth: true,
};

// ============================================================================
// EXPORTS
// ============================================================================

/**
 * Registry de todos os collectors
 * Adicionar novos collectors aqui!
 */
export const collectors: Record<string, CollectorConfig> = {
  github: githubTrending,
  npm: npmStats,
  pypi: pypiStats,
  hackernews: hackerNews,

  // TODO: Adicionar os outros 84 collectors
  // arxiv: arxivCollector,
  // openalex: openalexCollector,
  // reddit: redditCollector,
  // ...
};

/**
 * Filtra collectors por schedule/categoria
 */
export function getCollectorsBySchedule(schedule: string): CollectorConfig[] {
  return Object.values(collectors).filter(c => c.schedule === schedule);
}

export function getCollectorsByCategory(category: 'tech' | 'research' | 'jobs' | 'funding'): CollectorConfig[] {
  const categories = {
    tech: ['github', 'npm', 'pypi', 'hackernews'],
    research: ['arxiv', 'openalex', 'nih'],
    jobs: ['linkedin', 'github-jobs', 'stackoverflow-jobs'],
    funding: ['crunchbase', 'yc', 'angellist'],
  };

  return Object.values(collectors).filter(c => categories[category]?.includes(c.name));
}
