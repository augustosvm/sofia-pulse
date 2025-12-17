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
 * Sofia Pulse - ArXiv AI/ML Papers Collector
 *
 * Coleta papers de IA e Machine Learning do ArXiv ANTES de serem publicados
 *
 * POR QUE ARXIV AI É CRÍTICO:
 * - Papers aparecem 6-12 MESES ANTES de journals
 * - Todos os breakthroughs de IA aparecem aqui PRIMEIRO
 * - GPT, BERT, Transformers, Diffusion - todos no ArXiv primeiro
 * - Rastrear tendências: LLMs, Computer Vision, Robotics
 *
 * CATEGORIAS MONITORADAS:
 * - cs.AI: Artificial Intelligence
 * - cs.LG: Machine Learning
 * - cs.CV: Computer Vision
 * - cs.CL: Computation and Language (NLP)
 * - cs.NE: Neural and Evolutionary Computing
 * - cs.RO: Robotics
 */

import { Client } from 'pg';
import * as dotenv from 'dotenv';
import axios from 'axios';
import * as cheerio from 'cheerio';

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

interface ArxivAIPaper {
  arxiv_id: string;
  title: string;
  authors: string[];
  categories: string[]; // cs.AI, cs.LG, etc
  abstract: string;
  published_date: string;
  updated_date?: string;
  pdf_url: string;
  primary_category: string;
  keywords?: string[]; // Extracted from title/abstract
  is_breakthrough?: boolean; // High citation potential
}

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

async function createTableIfNotExists(client: Client): Promise<void> {
  const createTableQuery = `
    CREATE TABLE IF NOT EXISTS arxiv_ai_papers (
      id SERIAL PRIMARY KEY,
      arxiv_id VARCHAR(50) UNIQUE,
      title TEXT NOT NULL,
      authors TEXT[],
      categories VARCHAR(20)[],
      abstract TEXT,
      published_date DATE,
      updated_date DATE,
      pdf_url TEXT,
      primary_category VARCHAR(20),
      keywords TEXT[],
      is_breakthrough BOOLEAN DEFAULT FALSE,
      collected_at TIMESTAMP DEFAULT NOW()
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_arxiv_ai_published
      ON arxiv_ai_papers(published_date DESC);

    CREATE INDEX IF NOT EXISTS idx_arxiv_ai_category
      ON arxiv_ai_papers USING GIN(categories);

    CREATE INDEX IF NOT EXISTS idx_arxiv_ai_keywords
      ON arxiv_ai_papers USING GIN(keywords);

    CREATE INDEX IF NOT EXISTS idx_arxiv_ai_breakthrough
      ON arxiv_ai_papers(is_breakthrough)
      WHERE is_breakthrough = TRUE;
  `;

  await client.query(createTableQuery);
  console.log('✅ Table arxiv_ai_papers ready');
}

async function insertPaper(client: Client, paper: ArxivAIPaper): Promise<void> {
  const insertQuery = `
    INSERT INTO arxiv_ai_papers (
      arxiv_id, title, authors, categories, abstract,
      published_date, updated_date, pdf_url,
      primary_category, keywords, is_breakthrough
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
    ON CONFLICT (arxiv_id)
    DO UPDATE SET
      updated_date = EXCLUDED.updated_date,
      collected_at = NOW();
  `;

  await client.query(insertQuery, [
    paper.arxiv_id,
    paper.title,
    paper.authors,
    paper.categories,
    paper.abstract,
    paper.published_date,
    paper.updated_date || null,
    paper.pdf_url,
    paper.primary_category,
    paper.keywords || [],
    paper.is_breakthrough || false,
  ]);
}

// ============================================================================
// KEYWORD EXTRACTION
// ============================================================================

function extractKeywords(title: string, abstract: string): string[] {
  const text = `${title} ${abstract}`.toLowerCase();

  const keywords: string[] = [];

  // AI/ML Keywords
  if (text.match(/\b(gpt|llm|large language model|transformer)\b/)) keywords.push('LLM');
  if (text.match(/\b(diffusion|stable diffusion|imagen|dall-e)\b/)) keywords.push('Diffusion Models');
  if (text.match(/\b(bert|roberta|xlnet|electra)\b/)) keywords.push('BERT Family');
  if (text.match(/\b(cnn|convolutional neural|resnet|vgg)\b/)) keywords.push('CNN');
  if (text.match(/\b(gan|generative adversarial)\b/)) keywords.push('GAN');
  if (text.match(/\b(reinforcement learning|rl|dqn|ppo|a3c)\b/)) keywords.push('Reinforcement Learning');
  if (text.match(/\b(vision transformer|vit|swin)\b/)) keywords.push('Vision Transformer');
  if (text.match(/\b(multimodal|clip|align|flamingo)\b/)) keywords.push('Multimodal');
  if (text.match(/\b(agi|artificial general intelligence)\b/)) keywords.push('AGI');
  if (text.match(/\b(neural architecture search|nas|automl)\b/)) keywords.push('NAS/AutoML');
  if (text.match(/\b(graph neural network|gnn|gcn)\b/)) keywords.push('GNN');
  if (text.match(/\b(self-supervised|contrastive learning|simclr)\b/)) keywords.push('Self-Supervised');
  if (text.match(/\b(few-shot|zero-shot|meta-learning)\b/)) keywords.push('Few-Shot Learning');
  if (text.match(/\b(chatbot|conversational|dialogue)\b/)) keywords.push('Chatbots');
  if (text.match(/\b(robotic|robot|manipulation|grasping)\b/)) keywords.push('Robotics');

  return [...new Set(keywords)];
}

function isPotentialBreakthrough(title: string, abstract: string, authors: string[]): boolean {
  const text = `${title} ${abstract}`.toLowerCase();

  // Heuristics for breakthrough potential
  const breakthroughIndicators = [
    /\b(state-of-the-art|sota|outperform|surpass|achieve)\b/,
    /\b(novel|new|first|breakthrough|fundamental)\b/,
    /\b(scale|largest|100b|trillion)\b/,
    /\b(gpt-\d|claude|llama|palm|gemini)\b/,
  ];

  const matchCount = breakthroughIndicators.filter(regex => regex.test(text)).length;

  // Big lab authors (OpenAI, Google, Meta, etc - would be in author affiliations)
  const bigLabKeywords = ['openai', 'google', 'deepmind', 'meta', 'facebook', 'anthropic'];
  const hasBigLab = bigLabKeywords.some(lab =>
    authors.some(author => author.toLowerCase().includes(lab))
  );

  return matchCount >= 2 || hasBigLab;
}

// ============================================================================
// COLLECTORS
// ============================================================================

/**
 * Coleta papers REAIS do ArXiv API (GRATUITA!)
 * API: http://export.arxiv.org/api/query
 *
 * Categorias:
 * - cs.AI: Artificial Intelligence
 * - cs.LG: Machine Learning
 * - cs.CV: Computer Vision
 * - cs.CL: NLP
 * - cs.RO: Robotics
 */
async function collectArxivAI(): Promise<ArxivAIPaper[]> {
  console.log('🤖 Collecting ArXiv AI/ML papers from REAL API...');

  const papers: ArxivAIPaper[] = [];

  // Categorias para buscar
  const categories = ['cs.AI', 'cs.LG', 'cs.CV', 'cs.CL', 'cs.RO'];

  for (const category of categories) {
    try {
      // ArXiv API URL
      // max_results=20 por categoria = 100 papers total
      const url = `http://export.arxiv.org/api/query?search_query=cat:${category}&sortBy=submittedDate&sortOrder=descending&max_results=20`;

      console.log(`   Fetching ${category}...`);

      const response = await axios.get(url);
      const xml = response.data;

      // Parse XML (simple regex - production would use xml2js)
      const entries = xml.match(/<entry>([\s\S]*?)<\/entry>/g) || [];

      for (const entry of entries) {
        // Extract fields with regex
        const arxiv_id = entry.match(/<id>http:\/\/arxiv.org\/abs\/(.*?)<\/id>/)?.[1] || '';
        const title = entry.match(/<title>([\s\S]*?)<\/title>/)?.[1]?.trim().replace(/\n/g, ' ') || '';
        const abstract = entry.match(/<summary>([\s\S]*?)<\/summary>/)?.[1]?.trim().replace(/\n/g, ' ') || '';
        const published = entry.match(/<published>(.*?)<\/published>/)?.[1]?.split('T')[0] || '';
        const updated = entry.match(/<updated>(.*?)<\/updated>/)?.[1]?.split('T')[0] || '';

        // Authors
        const authorMatches = entry.match(/<author>[\s\S]*?<name>(.*?)<\/name>[\s\S]*?<\/author>/g) || [];
        const authors = authorMatches.map(a => a.match(/<name>(.*?)<\/name>/)?.[1] || '');

        // Categories
        const catMatches = entry.match(/<category term="(.*?)"\/>/g) || [];
        const cats = catMatches.map(c => c.match(/term="(.*?)"/)?.[1] || '');

        // PDF URL
        const pdf_url = `https://arxiv.org/pdf/${arxiv_id}.pdf`;

        // Extract keywords and check breakthrough
        const keywords = extractKeywords(title, abstract);
        const is_breakthrough = isPotentialBreakthrough(title, abstract, authors);

        papers.push({
          arxiv_id,
          title,
          authors,
          categories: cats,
          abstract,
          published_date: published,
          updated_date: updated,
          pdf_url,
          primary_category: category,
          keywords,
          is_breakthrough,
        });
      }

      console.log(`   ✅ ${entries.length} papers from ${category}`);

      // Rate limit: 1 request per second
      await new Promise(resolve => setTimeout(resolve, 1000));

    } catch (error) {
      console.log(`   ⚠️  Error fetching ${category}:`, error);
    }
  }

  console.log(`   ✅ Total: ${papers.length} papers collected`);

  return papers;
}

/**
 * FALLBACK: Mock data case API falhar
 */
async function collectArxivAI_MOCK(): Promise<ArxivAIPaper[]> {
  console.log('🤖 Using MOCK data (API unavailable)...');

  // Mock papers baseados em papers reais recentes
  const mockPapers: ArxivAIPaper[] = [
    // LLMs
    {
      arxiv_id: '2024.11234',
      title: 'Scaling Laws for Large Language Models: Beyond 100 Billion Parameters',
      authors: ['OpenAI Research', 'John Smith', 'Jane Doe'],
      categories: ['cs.AI', 'cs.LG', 'cs.CL'],
      primary_category: 'cs.AI',
      abstract: 'We investigate scaling laws for transformer-based language models with up to 175B parameters. Our findings suggest that performance continues to improve predictably with scale, following power-law relationships across model size, dataset size, and compute budget. We provide empirical evidence for optimal allocation of computational resources...',
      published_date: '2024-11-01',
      pdf_url: 'https://arxiv.org/pdf/2024.11234',
      keywords: ['LLM', 'AGI'],
      is_breakthrough: true,
    },
    {
      arxiv_id: '2024.11235',
      title: 'Efficient Attention Mechanisms for Long-Context Language Models',
      authors: ['Google Research', 'Alice Wang', 'Bob Chen'],
      categories: ['cs.LG', 'cs.CL'],
      primary_category: 'cs.LG',
      abstract: 'Traditional transformers have quadratic complexity in sequence length, limiting their application to long documents. We propose FlashAttention-3, which reduces attention complexity to O(n log n) while maintaining accuracy. Our approach enables processing of 100k+ token contexts on consumer GPUs...',
      published_date: '2024-10-28',
      pdf_url: 'https://arxiv.org/pdf/2024.11235',
      keywords: ['LLM'],
      is_breakthrough: false,
    },

    // Computer Vision
    {
      arxiv_id: '2024.11236',
      title: 'Diffusion Transformers: Scaling Text-to-Image Generation to 10 Billion Parameters',
      authors: ['Stability AI', 'Emily Brown', 'David Lee'],
      categories: ['cs.CV', 'cs.AI'],
      primary_category: 'cs.CV',
      abstract: 'We introduce DiT-XL, a diffusion transformer architecture scaled to 10B parameters for high-resolution image generation. Our model achieves state-of-the-art FID scores on COCO and demonstrates unprecedented photorealism and prompt adherence. We analyze the scaling behavior and provide insights...',
      published_date: '2024-10-25',
      pdf_url: 'https://arxiv.org/pdf/2024.11236',
      keywords: ['Diffusion Models', 'Vision Transformer'],
      is_breakthrough: true,
    },
    {
      arxiv_id: '2024.11237',
      title: 'Self-Supervised Learning for Medical Image Analysis',
      authors: ['Stanford AI Lab', 'Sarah Kim', 'Michael Zhang'],
      categories: ['cs.CV', 'cs.LG'],
      primary_category: 'cs.CV',
      abstract: 'Medical imaging datasets are often small and expensive to label. We propose MedCLIP, a self-supervised contrastive learning approach that learns robust representations from unlabeled medical images. Our method achieves 95% accuracy on chest X-ray classification using only 1% labeled data...',
      published_date: '2024-10-20',
      pdf_url: 'https://arxiv.org/pdf/2024.11237',
      keywords: ['Self-Supervised', 'CNN'],
      is_breakthrough: false,
    },

    // Multimodal
    {
      arxiv_id: '2024.11238',
      title: 'Unified Multimodal Foundation Models: Vision, Language, and Audio',
      authors: ['Meta AI', 'Thomas Anderson', 'Lisa Martinez'],
      categories: ['cs.AI', 'cs.CV', 'cs.CL'],
      primary_category: 'cs.AI',
      abstract: 'We present Meta-GPT-4, a unified foundation model that processes vision, language, and audio modalities within a single transformer architecture. Our model achieves state-of-the-art performance across 20+ benchmarks including VQA, captioning, speech recognition, and cross-modal retrieval...',
      published_date: '2024-10-15',
      pdf_url: 'https://arxiv.org/pdf/2024.11238',
      keywords: ['Multimodal', 'LLM'],
      is_breakthrough: true,
    },

    // Reinforcement Learning
    {
      arxiv_id: '2024.11239',
      title: 'Learning to Play Go at Superhuman Level with Pure Self-Play',
      authors: ['DeepMind', 'Robert Wilson', 'Anna Taylor'],
      categories: ['cs.AI', 'cs.LG'],
      primary_category: 'cs.AI',
      abstract: 'We introduce AlphaGo Zero 2.0, which learns to play Go from scratch through pure self-play reinforcement learning, without human data. Our agent surpasses previous AlphaGo versions and human world champions. We analyze the learned strategies and discover novel joseki patterns...',
      published_date: '2024-10-10',
      pdf_url: 'https://arxiv.org/pdf/2024.11239',
      keywords: ['Reinforcement Learning', 'AGI'],
      is_breakthrough: true,
    },

    // Robotics
    {
      arxiv_id: '2024.11240',
      title: 'Dexterous Manipulation with Sim-to-Real Transfer',
      authors: ['OpenAI Robotics', 'Kevin Moore', 'Jessica White'],
      categories: ['cs.RO', 'cs.AI'],
      primary_category: 'cs.RO',
      abstract: 'We demonstrate that robots can learn complex manipulation skills entirely in simulation and transfer to real hardware with minimal fine-tuning. Our approach combines domain randomization with differentiable physics simulation, achieving 90% success on previously unseen objects...',
      published_date: '2024-10-05',
      pdf_url: 'https://arxiv.org/pdf/2024.11240',
      keywords: ['Robotics', 'Reinforcement Learning'],
      is_breakthrough: false,
    },

    // Graph Neural Networks
    {
      arxiv_id: '2024.11241',
      title: 'Graph Transformers for Molecular Property Prediction',
      authors: ['MIT CSAIL', 'Daniel Garcia', 'Olivia Johnson'],
      categories: ['cs.LG', 'cs.AI'],
      primary_category: 'cs.LG',
      abstract: 'We propose GraphFormer, a graph transformer architecture for predicting molecular properties. By incorporating 3D geometric information and chemical bond types, our model achieves state-of-the-art results on QM9 and drug discovery benchmarks...',
      published_date: '2024-09-30',
      pdf_url: 'https://arxiv.org/pdf/2024.11241',
      keywords: ['GNN'],
      is_breakthrough: false,
    },

    // NAS/AutoML
    {
      arxiv_id: '2024.11242',
      title: 'Neural Architecture Search for Efficient Large Language Models',
      authors: ['Google Brain', 'Christopher Davis', 'Amanda Rodriguez'],
      categories: ['cs.LG', 'cs.AI'],
      primary_category: 'cs.LG',
      abstract: 'We apply neural architecture search to discover efficient LLM architectures that match GPT-3 performance with 10x fewer parameters. Our search space includes novel attention patterns, activation functions, and layer configurations. The discovered architectures generalize well to unseen tasks...',
      published_date: '2024-09-25',
      pdf_url: 'https://arxiv.org/pdf/2024.11242',
      keywords: ['NAS/AutoML', 'LLM'],
      is_breakthrough: true,
    },

    // Few-Shot Learning
    {
      arxiv_id: '2024.11243',
      title: 'Meta-Learning for Few-Shot Image Classification',
      authors: ['Berkeley AI Research', 'Matthew Harris', 'Sophia Clark'],
      categories: ['cs.LG', 'cs.CV'],
      primary_category: 'cs.LG',
      abstract: 'We introduce MAML++, an improved meta-learning algorithm for few-shot classification. Our approach learns task-agnostic representations that adapt quickly to new tasks with only 1-5 examples. We achieve 95%+ accuracy on miniImageNet with 5-shot learning...',
      published_date: '2024-09-20',
      pdf_url: 'https://arxiv.org/pdf/2024.11243',
      keywords: ['Few-Shot Learning'],
      is_breakthrough: false,
    },
  ];

  // Extract keywords and detect breakthroughs
  mockPapers.forEach(paper => {
    if (!paper.keywords) {
      paper.keywords = extractKeywords(paper.title, paper.abstract);
    }
    if (paper.is_breakthrough === undefined) {
      paper.is_breakthrough = isPotentialBreakthrough(paper.title, paper.abstract, paper.authors);
    }
  });

  return mockPapers;
}

// ============================================================================
// MAIN FUNCTION
// ============================================================================

async function main() {
  console.log('🚀 Sofia Pulse - ArXiv AI/ML Papers Collector');
  console.log('='.repeat(60));
  console.log('');
  console.log('🤖 WHY ARXIV AI IS CRITICAL:');
  console.log('   - Papers appear 6-12 MONTHS before journals');
  console.log('   - ALL AI breakthroughs published here FIRST');
  console.log('   - GPT, BERT, Transformers, Diffusion - all ArXiv first');
  console.log('   - Track trends: LLMs, Vision, Robotics, RL');
  console.log('');
  console.log('📚 Categories monitored:');
  console.log('   cs.AI, cs.LG, cs.CV, cs.CL, cs.NE, cs.RO');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    await createTableIfNotExists(client);

    console.log('');
    console.log('📊 Collecting papers...');
    console.log('');

    const papers = await collectArxivAI();
    console.log(`   ✅ Collected ${papers.length} papers`);
    console.log('');

    console.log('💾 Inserting into database...');
    for (const paper of papers) {
      await insertPaper(client, paper);
    }
    console.log(`✅ ${papers.length} papers inserted/updated`);
    console.log('');

    // Summary
    console.log('📊 Summary:');
    console.log('');

    const summaryQuery = `
      SELECT
        primary_category,
        COUNT(*) as paper_count,
        COUNT(*) FILTER (WHERE is_breakthrough) as breakthroughs
      FROM arxiv_ai_papers
      GROUP BY primary_category
      ORDER BY paper_count DESC;
    `;

    const summary = await client.query(summaryQuery);

    summary.rows.forEach((row) => {
      console.log(`   ${row.primary_category}:`);
      console.log(`      Papers: ${row.paper_count}`);
      console.log(`      Breakthroughs: ${row.breakthroughs}`);
      console.log('');
    });

    // Breakthrough papers
    console.log('🌟 Potential Breakthrough Papers:');
    console.log('');

    const breakthroughQuery = `
      SELECT arxiv_id, title, authors[1] as first_author
      FROM arxiv_ai_papers
      WHERE is_breakthrough = TRUE
      ORDER BY published_date DESC
      LIMIT 5;
    `;

    const breakthroughs = await client.query(breakthroughQuery);

    breakthroughs.rows.forEach((row, idx) => {
      console.log(`   ${idx + 1}. ${row.title}`);
      console.log(`      ArXiv: ${row.arxiv_id}`);
      console.log(`      Lead: ${row.first_author}`);
      console.log('');
    });

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
  console.log('🚀 Sofia Pulse - ArXiv AI/ML Papers Collector (DRY RUN)');
  console.log('='.repeat(60));
  console.log('');
  console.log('🤖 WHY ARXIV AI IS CRITICAL:');
  console.log('   - Papers appear 6-12 MONTHS before journals');
  console.log('   - ALL AI breakthroughs published here FIRST');
  console.log('   - GPT-3, BERT, Transformers, Diffusion - all ArXiv first');
  console.log('   - Early detection of trends and breakthroughs');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const papers = await collectArxivAI();
  console.log(`✅ Collected ${papers.length} AI/ML papers`);
  console.log('');

  // Group by category
  const byCategory = papers.reduce((acc, p) => {
    if (!acc[p.primary_category]) acc[p.primary_category] = [];
    acc[p.primary_category].push(p);
    return acc;
  }, {} as Record<string, ArxivAIPaper[]>);

  console.log('📊 Papers by Category:');
  console.log('');

  Object.entries(byCategory)
    .sort(([, a], [, b]) => b.length - a.length)
    .forEach(([cat, paps]) => {
      const breakthroughs = paps.filter(p => p.is_breakthrough).length;
      console.log(`   ${cat}: ${paps.length} papers (${breakthroughs} breakthroughs)`);
    });

  console.log('');
  console.log('🌟 Potential Breakthrough Papers:');
  console.log('');

  const breakthroughs = papers.filter(p => p.is_breakthrough);
  breakthroughs.slice(0, 5).forEach((paper, idx) => {
    console.log(`   ${idx + 1}. ${paper.title}`);
    console.log(`      ArXiv: ${paper.arxiv_id}`);
    console.log(`      Category: ${paper.primary_category}`);
    console.log(`      Keywords: ${paper.keywords?.join(', ')}`);
    console.log(`      Authors: ${paper.authors.slice(0, 2).join(', ')}${paper.authors.length > 2 ? ', et al.' : ''}`);
    console.log('');
  });

  // Keyword trends
  console.log('🔥 Trending Keywords:');
  console.log('');

  const keywordCount = papers.reduce((acc, p) => {
    (p.keywords || []).forEach(k => {
      acc[k] = (acc[k] || 0) + 1;
    });
    return acc;
  }, {} as Record<string, number>);

  Object.entries(keywordCount)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10)
    .forEach(([keyword, count]) => {
      console.log(`   ${keyword}: ${count} papers`);
    });

  console.log('');
  console.log('='.repeat(60));
  console.log('');
  console.log('💡 AI RESEARCH INSIGHTS:');
  console.log('');
  console.log(`   Total Papers: ${papers.length}`);
  console.log(`   Breakthroughs: ${breakthroughs.length}`);
  console.log(`   Top Category: ${Object.keys(byCategory)[0]}`);
  console.log('');
  console.log('   LLMs dominate current research');
  console.log('   Multimodal models gaining traction');
  console.log('   Efficiency improvements critical for deployment');
  console.log('');

  console.log('🎯 CORRELATIONS:');
  console.log('');
  console.log('   - ArXiv papers → Patents (6-12 month lag)');
  console.log('   - Breakthrough papers → Startup funding');
  console.log('   - Author affiliations → Company valuations');
  console.log('   - Keyword trends → GPU demand');
  console.log('');
  console.log('✅ Dry run complete!');
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
        console.log('💡 TIP: Run with --dry-run to see sample data:');
        console.log('   npm run collect:arxiv-ai -- --dry-run');
        console.log('');
        process.exit(1);
      }
      throw error;
    });
  }
}

export { collectArxivAI, dryRun };
