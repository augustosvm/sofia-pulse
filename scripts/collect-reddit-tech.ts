// Fix for Node.js 18 + undici - MUST BE FIRST!
// @ts-ignore
if (typeof File === 'undefined') {
  // @ts-ignore
  globalThis.File = class File extends Blob {
    constructor(bits: any[], name: string, options?: any) {
      super(bits, options);
    }
  };
}

#!/usr/bin/env tsx

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

interface RedditPost {
  post_id: string;
  subreddit: string;
  title: string;
  author: string;
  score: number;
  num_comments: number;
  url: string;
  created_utc: string;
  technologies: string[];
  sentiment: string;
}

async function fetchReddit(subreddit: string): Promise<RedditPost[]> {
  const url = `https://www.reddit.com/r/${subreddit}/hot.json?limit=50`;

  try {
    const response = await axios.get(url, {
      headers: { 'User-Agent': 'SofiaPulse/1.0' },
      timeout: 30000,
    });

    const posts: RedditPost[] = [];

    for (const child of response.data.data.children) {
      const post = child.data;

      const technologies = extractTechnologies(post.title + ' ' + (post.selftext || ''));
      const sentiment = post.score > 100 ? 'positive' : post.score < 10 ? 'negative' : 'neutral';

      posts.push({
        post_id: post.id,
        subreddit: subreddit,
        title: post.title,
        author: post.author,
        score: post.score,
        num_comments: post.num_comments,
        url: post.url,
        created_utc: new Date(post.created_utc * 1000).toISOString(),
        technologies,
        sentiment,
      });
    }

    return posts;
  } catch (error: any) {
    console.error(`Error fetching r/${subreddit}:`, error.message);
    return [];
  }
}

function extractTechnologies(text: string): string[] {
  const tech = [];
  const lower = text.toLowerCase();

  const techs = [
    'python', 'javascript', 'typescript', 'rust', 'go', 'java', 'cpp',
    'react', 'vue', 'angular', 'svelte', 'nextjs',
    'tensorflow', 'pytorch', 'keras', 'scikit-learn',
    'kubernetes', 'docker', 'aws', 'azure', 'gcp',
    'postgresql', 'mongodb', 'redis', 'elasticsearch',
    'llm', 'gpt', 'ai', 'ml', 'deep learning', 'neural network'
  ];

  for (const t of techs) {
    if (lower.includes(t)) tech.push(t);
  }

  return [...new Set(tech)];
}

async function insertPost(client: Client, post: RedditPost): Promise<void> {
  const query = `
    INSERT INTO sofia.reddit_tech (
      post_id, subreddit, title, author, score, num_comments,
      url, created_utc, technologies, sentiment
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    ON CONFLICT (post_id) DO UPDATE SET
      score = EXCLUDED.score,
      num_comments = EXCLUDED.num_comments,
      collected_at = NOW();
  `;

  await client.query(query, [
    post.post_id,
    post.subreddit,
    post.title,
    post.author,
    post.score,
    post.num_comments,
    post.url,
    post.created_utc,
    post.technologies,
    post.sentiment,
  ]);
}

async function main() {
  console.log('🔥 Reddit Tech Collector');
  console.log('='.repeat(60));

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    const fs = await import('fs/promises');
    const migrationSQL = await fs.readFile('db/migrations/012_create_reddit_tech.sql', 'utf-8');
    await client.query(migrationSQL);

    const subreddits = ['programming', 'MachineLearning', 'artificial', 'golang', 'rust', 'javascript'];

    let totalPosts = 0;
    for (const subreddit of subreddits) {
      console.log(`📊 Fetching r/${subreddit}...`);
      const posts = await fetchReddit(subreddit);

      for (const post of posts) {
        await insertPost(client, post);
      }

      totalPosts += posts.length;
      console.log(`   ✅ ${posts.length} posts`);

      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    console.log(`✅ Total: ${totalPosts} posts collected`);

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
