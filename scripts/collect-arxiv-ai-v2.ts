#!/usr/bin/env tsx

// Fix for Node.js 18 + undici
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
 * Sofia Pulse - ArXiv AI/ML Papers Collector V2
 *
 * UPDATED: Uses consolidated research_papers table
 * Replaces: collect-arxiv-ai.ts (used arxiv_ai_papers)
 *
 * Collects AI/ML papers from ArXiv 6-12 MONTHS BEFORE journal publication
 *
 * Categories monitored:
 * - cs.AI, cs.LG, cs.CV, cs.CL, cs.NE, cs.RO
 */

import { Pool } from 'pg';
import * as dotenv from 'dotenv';
import axios from 'axios';
import * as cheerio from 'cheerio';
import { ResearchPapersInserter } from './shared/research-papers-inserter.js';

dotenv.config();

// ============================================================================
// DATABASE SETUP
// ============================================================================

const pool = new Pool({
  host: process.env.POSTGRES_HOST || process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || process.env.DB_PORT || '5432'),
  user: process.env.POSTGRES_USER || process.env.DB_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || process.env.DB_PASSWORD || 'postgres',
  database: process.env.POSTGRES_DB || process.env.DB_NAME || 'sofia_db',
});

// ============================================================================
// TYPES
// ============================================================================

interface ArxivAIPaper {
  arxiv_id: string;
  title: string;
  authors: string[];
  categories: string[];
  abstract: string;
  published_date: string;
  updated_date?: string;
  pdf_url: string;
  primary_category: string;
  keywords?: string[];
  is_breakthrough?: boolean;
}

// ============================================================================
// KEYWORD EXTRACTION
// ============================================================================

function extractKeywords(title: string, abstract: string): string[] {
  const text = `${title} ${abstract}`.toLowerCase();
  const keywords: string[] = [];

  // AI/ML keywords
  const aiKeywords = [
    'gpt', 'llm', 'large language model', 'transformer', 'bert', 'attention',
    'diffusion', 'stable diffusion', 'gan', 'generative',
    'reinforcement learning', 'deep learning', 'neural network',
    'computer vision', 'nlp', 'natural language',
    'chatbot', 'ai agent', 'multimodal',
    'zero-shot', 'few-shot', 'prompt', 'fine-tuning',
    'embedding', 'retrieval', 'rag', 'knowledge graph',
    'robotics', 'autonomous', 'self-driving'
  ];

  for (const keyword of aiKeywords) {
    if (text.includes(keyword)) {
      keywords.push(keyword.toUpperCase().replace(/ /g, '_'));
    }
  }

  return keywords.length > 0 ? keywords : [];
}

function isBreakthrough(paper: ArxivAIPaper): boolean {
  const title = paper.title.toLowerCase();
  const abstract = paper.abstract.toLowerCase();

  // Breakthrough indicators
  const breakthroughTerms = [
    'state-of-the-art', 'sota', 'breakthrough', 'novel',
    'outperform', 'significantly better', 'first time',
    'surpass', 'achieve', 'record', 'benchmark'
  ];

  const hasBre akthrough = breakthroughTerms.some(term =>
    title.includes(term) || abstract.includes(term)
  );

  // High-impact topics
  const hotTopics = [
    'gpt', 'llm', 'large language model', 'diffusion',
    'multimodal', 'reinforcement learning from human feedback',
    'self-supervised', 'foundation model'
  ];

  const hasHotTopic = hotTopics.some(topic =>
    title.includes(topic) || abstract.includes(topic)
  );

  return hasBreakthrough || hasHotTopic;
}

// ============================================================================
// ARXIV API
// ============================================================================

async function fetchArxivPapers(maxResults: number = 100): Promise<ArxivAIPaper[]> {
  const categories = ['cs.AI', 'cs.LG', 'cs.CV', 'cs.CL', 'cs.NE', 'cs.RO'];
  const query = categories.map(cat => `cat:${cat}`).join(' OR ');

  const url = `http://export.arxiv.org/api/query?search_query=${encodeURIComponent(query)}&sortBy=submittedDate&sortOrder=descending&max_results=${maxResults}`;

  try {
    const response = await axios.get(url, {
      headers: { 'User-Agent': 'SofiaPulse/1.0' },
      timeout: 30000,
    });

    const $ = cheerio.load(response.data, { xmlMode: true });
    const papers: ArxivAIPaper[] = [];

    $('entry').each((_, entry) => {
      const $entry = $(entry);

      const arxiv_id = $entry.find('id').text().split('/abs/')[1] || '';
      const title = $entry.find('title').text().trim();
      const abstract = $entry.find('summary').text().trim();

      // Parse authors
      const authors: string[] = [];
      $entry.find('author name').each((_, author) => {
        authors.push($(author).text().trim());
      });

      // Parse categories
      const categories: string[] = [];
      $entry.find('category').each((_, cat) => {
        const term = $(cat).attr('term');
        if (term) categories.push(term);
      });

      const published_date = $entry.find('published').text().split('T')[0];
      const updated = $entry.find('updated').text().split('T')[0];
      const updated_date = updated !== published_date ? updated : undefined;

      const pdf_url = `https://arxiv.org/pdf/${arxiv_id}`;
      const primary_category = categories[0] || 'cs.AI';

      const keywords = extractKeywords(title, abstract);
      const is_breakthrough = isBreakthrough({
        arxiv_id,
        title,
        authors,
        categories,
        abstract,
        published_date,
        pdf_url,
        primary_category,
        keywords,
      });

      papers.push({
        arxiv_id,
        title,
        authors,
        categories,
        abstract,
        published_date,
        updated_date,
        pdf_url,
        primary_category,
        keywords,
        is_breakthrough,
      });
    });

    return papers;
  } catch (error: any) {
    console.error('❌ Error fetching ArXiv:', error.message);
    throw error;
  }
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  console.log('🔬 ArXiv AI Papers Collector V2 (Unified Table)');
  console.log('================================================\n');

  try {
    const inserter = new ResearchPapersInserter(pool);

    // Fetch papers
    console.log('📡 Fetching latest AI/ML papers from ArXiv...');
    const papers = await fetchArxivPapers(100);
    console.log(`✅ Fetched ${papers.length} papers\n`);

    // Insert papers into unified research_papers table
    console.log('💾 Inserting into research_papers table...');
    let inserted = 0;

    for (const paper of papers) {
      try {
        await inserter.insertPaper({
          title: paper.title,
          source: 'arxiv',
          source_id: paper.arxiv_id,
          abstract: paper.abstract,
          authors: paper.authors,
          keywords: paper.keywords,
          publication_date: paper.published_date,
          publication_year: new Date(paper.published_date).getFullYear(),
          primary_category: paper.primary_category,
          categories: paper.categories,
          pdf_url: paper.pdf_url,
          is_breakthrough: paper.is_breakthrough,
          is_open_access: true, // ArXiv is always open access
        });
        inserted++;
      } catch (error: any) {
        console.error(`❌ Error inserting ${paper.arxiv_id}:`, error.message);
      }
    }

    console.log(`\n✅ Inserted/Updated ${inserted} papers`);

    // Show stats
    const stats = await inserter.getStats();
    console.log('\n📊 Research Papers Stats:');
    console.table(stats);

  } catch (error: any) {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
