#!/usr/bin/env tsx
/**
 * Research Papers Collector V2 - Sofia Pulse (UNIFIED TABLE)
 *
 * UPDATED: Uses consolidated sofia.research_papers table
 * Replaces: arxiv_ai_papers, openalex_papers, bdtd_theses
 *
 * Core engine para coletar research papers de APIs acadêmicas.
 * Centraliza: HTTP requests, rate limiting, error handling, logging, inserção no banco.
 *
 * Features:
 * - Usa ResearchPapersInserter (unified table)
 * - Suporta múltiplas sources: arxiv, openalex, nih, bdtd
 * - Schema rico: authors[], abstract, categories[], citations, etc.
 *
 * Usage:
 *   npx tsx scripts/collect.ts arxiv
 *   npx tsx scripts/collect.ts openalex
 *   npx tsx scripts/collect.ts --all-papers
 */

import { Pool } from 'pg';
import * as dotenv from 'dotenv';
import axios, { AxiosRequestConfig } from 'axios';
import { rateLimiters } from '../utils/rate-limiter.js';
import { ResearchPapersInserter } from '../shared/research-papers-inserter.js';

dotenv.config();

// ============================================================================
// TYPES
// ============================================================================

export interface PaperData {
  // Source (UPDATED: unified table)
  source: 'arxiv' | 'openalex' | 'nih' | 'bdtd' | 'scielo' | 'openalex_brazil';

  // Common fields (all papers have these)
  source_id: string;    // arxiv_id, openalex_id, grant_id, thesis_id
  title: string;
  authors: string[];
  published_date?: string;

  // Paper-specific data (stored as-is)
  data: Record<string, any>;
}

export interface ResearchPapersConfig {
  /** Nome único do collector (ex: 'arxiv', 'openalex') */
  name: string;

  /** Nome para display nos logs */
  displayName: string;

  /** URL da API ou função que retorna URL */
  url: string | ((params?: any) => string);

  /** Headers HTTP (pode incluir API keys) */
  headers?: Record<string, string> | ((env: NodeJS.ProcessEnv) => Record<string, string>);

  /** Timeout em ms (padrão: 30000) */
  timeout?: number;

  /** Rate limiter a usar ou tempo em ms */
  rateLimit?: keyof typeof rateLimiters | number;

  /** Função que parseia a resposta da API e retorna PaperData[] */
  parseResponse: (data: any, env: NodeJS.ProcessEnv) => PaperData[] | Promise<PaperData[]>;

  /** Schedule cron (ex: '0 8 * * 1' for weekly on Monday at 8am) */
  schedule?: string;

  /** Descrição do que esse collector faz */
  description?: string;

  /** Se true, roda mesmo sem API keys */
  allowWithoutAuth?: boolean;
}

// ============================================================================
// DATABASE CONFIG
// ============================================================================

const dbConfig = {
  host: process.env.POSTGRES_HOST || process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || process.env.DB_PORT || '5432'),
  user: process.env.POSTGRES_USER || process.env.DB_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD || process.env.DB_PASSWORD,
  database: process.env.POSTGRES_DB || process.env.DB_NAME || 'sofia_db',
};

// ============================================================================
// RESEARCH PAPERS COLLECTOR ENGINE
// ============================================================================

export class ResearchPapersCollector {
  private pool: Pool;
  private inserter: ResearchPapersInserter;

  constructor() {
    this.pool = new Pool(dbConfig);
    this.inserter = new ResearchPapersInserter(this.pool);
  }

  /**
   * Insere um paper no banco usando ResearchPapersInserter (unified table)
   */
  private async insertPaper(paper: PaperData): Promise<void> {
    // Convert to ResearchPaperData format
    await this.inserter.insertPaper({
      title: paper.title,
      source: paper.source,
      source_id: paper.source_id,
      abstract: paper.data.abstract,
      authors: paper.authors,
      keywords: paper.data.keywords || paper.data.concepts,
      publication_date: paper.published_date || paper.data.publication_date,
      publication_year: paper.data.publication_year,
      doi: paper.data.doi,
      primary_category: paper.data.primary_category || paper.data.primary_concept,
      categories: paper.data.categories || paper.data.concepts,
      area: paper.data.area,
      pdf_url: paper.data.pdf_url,
      journal: paper.data.journal,
      publisher: paper.data.publisher,
      is_open_access: paper.data.is_open_access,
      university: paper.data.university,
      program: paper.data.program,
      degree_type: paper.data.degree_type,
      language: paper.data.language,
      author_institutions: paper.data.author_institutions,
      author_countries: paper.data.author_countries,
      cited_by_count: paper.data.cited_by_count,
      referenced_works_count: paper.data.referenced_works_count,
      is_breakthrough: paper.data.is_breakthrough,
    });
  }

  /**
   * Executa um collector baseado em sua configuração
   */
  async collect(config: ResearchPapersConfig): Promise<{
    success: boolean;
    collected: number;
    errors: number;
    duration: number;
  }> {
    const startTime = Date.now();

    console.log('');
    console.log('='.repeat(70));
    console.log(`📚 ${config.displayName}`);
    if (config.description) {
      console.log(`   ${config.description}`);
    }
    console.log('='.repeat(70));
    console.log('');

    let collected = 0;
    let errors = 0;
    let runId: number | null = null;

    try {
      // Start tracking
      const hostname = require('os').hostname();
      const result = await this.pool.query(
        'SELECT sofia.start_collector_run($1, $2) as run_id',
        [config.name, hostname]
      );
      runId = result.rows[0]?.run_id;
      console.log(`🔍 Run ID: ${runId}`);
      console.log('');

      // 1. Preparar URL
      const url = typeof config.url === 'function'
        ? config.url(process.env)
        : config.url;

      // 2. Preparar headers
      let headers: Record<string, string> = {
        'User-Agent': 'Sofia-Pulse-Collector/2.0',
      };

      if (config.headers) {
        const configHeaders = typeof config.headers === 'function'
          ? config.headers(process.env)
          : config.headers;
        headers = { ...headers, ...configHeaders };
      }

      // 3. Fazer request (com rate limiting se especificado)
      console.log(`🔍 Fetching from API...`);
      console.log(`   URL: ${url.substring(0, 100)}${url.length > 100 ? '...' : ''}`);

      let response;
      const requestConfig: AxiosRequestConfig = {
        headers,
        timeout: config.timeout || 30000,
        validateStatus: (status) => status >= 200 && status < 500,
      };

      if (config.rateLimit && typeof config.rateLimit === 'string' && config.rateLimit in rateLimiters) {
        // Usa rate limiter específico
        response = await rateLimiters[config.rateLimit as keyof typeof rateLimiters].get(url, requestConfig);
      } else {
        // Request direto (com delay opcional)
        if (config.rateLimit && typeof config.rateLimit === 'number') {
          await this.delay(config.rateLimit);
        }
        response = await axios.get(url, requestConfig);
      }

      if (response.status !== 200) {
        throw new Error(`API returned status ${response.status}`);
      }

      console.log(`   ✅ Response received (${response.status})`);
      console.log('');

      // 4. Parsear resposta
      console.log(`🔄 Parsing response...`);
      const papers = await config.parseResponse(response.data, process.env);
      console.log(`   ✅ Parsed ${papers.length} papers`);
      console.log('');

      // 5. Inserir no banco
      console.log(`💾 Inserting into database...`);
      for (const paper of papers) {
        try {
          await this.insertPaper(paper);
          collected++;
        } catch (error: any) {
          console.error(`   ❌ Error inserting ${paper.title}:`, error.message);
          errors++;
        }
      }

      console.log(`   ✅ Inserted ${collected} papers`);
      if (errors > 0) {
        console.log(`   ⚠️  ${errors} errors during insertion`);
      }

    } catch (error: any) {
      console.error('');
      console.error(`❌ Collection failed:`, error.message);

      if (axios.isAxiosError(error)) {
        if (error.response?.status === 403) {
          console.error('   💡 Hint: Check if API key is set in .env');
        } else if (error.response?.status === 429) {
          console.error('   💡 Hint: Rate limit exceeded, try again later');
        }
      }

      // Finish tracking (failed)
      if (runId) {
        await this.pool.query(
          'SELECT sofia.finish_collector_run($1, $2, $3, $4, $5, $6)',
          [runId, 'failed', 0, 1, error.message, error.stack]
        );
      }

      return {
        success: false,
        collected: 0,
        errors: 1,
        duration: Date.now() - startTime,
      };
    }

    const duration = Date.now() - startTime;

    // Finish tracking (success)
    if (runId) {
      await this.pool.query(
        'SELECT sofia.finish_collector_run($1, $2, $3, $4)',
        [runId, 'success', collected, errors]
      );
    }

    console.log('');
    console.log('='.repeat(70));
    console.log(`✅ Collection complete!`);
    console.log(`   Run ID: ${runId}`);
    console.log(`   Collected: ${collected} papers`);
    console.log(`   Errors: ${errors}`);
    console.log(`   Duration: ${(duration / 1000).toFixed(2)}s`);
    console.log('='.repeat(70));
    console.log('');

    return {
      success: true,
      collected,
      errors,
      duration,
    };
  }

  /**
   * Executa múltiplos collectors em sequência
   */
  async collectAll(configs: ResearchPapersConfig[]): Promise<void> {
    console.log('');
    console.log('🚀 Running all research papers collectors...');
    console.log(`   Total: ${configs.length} collectors`);
    console.log('');

    const results = [];

    for (const config of configs) {
      const result = await this.collect(config);
      results.push({ config: config.name, ...result });

      // Pequeno delay entre collectors
      await this.delay(1000);
    }

    // Summary
    console.log('');
    console.log('='.repeat(70));
    console.log('📊 SUMMARY');
    console.log('='.repeat(70));

    const successful = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;
    const totalCollected = results.reduce((sum, r) => sum + r.collected, 0);
    const totalErrors = results.reduce((sum, r) => sum + r.errors, 0);
    const totalDuration = results.reduce((sum, r) => sum + r.duration, 0);

    console.log('');
    console.log(`✅ Successful: ${successful}/${configs.length}`);
    console.log(`❌ Failed: ${failed}/${configs.length}`);
    console.log(`📚 Total papers: ${totalCollected}`);
    console.log(`⚠️  Total errors: ${totalErrors}`);
    console.log(`⏱️  Total duration: ${(totalDuration / 1000).toFixed(2)}s`);
    console.log('');

    if (failed > 0) {
      console.log('Failed collectors:');
      results
        .filter(r => !r.success)
        .forEach(r => console.log(`   - ${r.config}`));
      console.log('');
    }
  }

  /**
   * Fecha conexões
   */
  async close(): Promise<void> {
    await this.pool.end();
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// ============================================================================
// CLI
// ============================================================================

export async function runPapersCLI(configs: Record<string, ResearchPapersConfig>) {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    console.log('');
    console.log('📚 Research Papers Collector - Sofia Pulse');
    console.log('');
    console.log('Usage:');
    console.log('  npx tsx scripts/collect.ts <collector>');
    console.log('  npx tsx scripts/collect.ts --all-papers');
    console.log('');
    console.log('Available papers collectors:');
    Object.keys(configs).forEach(name => {
      const config = configs[name];
      console.log(`  - ${name.padEnd(20)} ${config.description || ''}`);
    });
    console.log('');
    process.exit(0);
  }

  const collector = new ResearchPapersCollector();

  try {
    if (args.includes('--all-papers')) {
      await collector.collectAll(Object.values(configs));
    } else {
      const collectorName = args[0];
      const config = configs[collectorName];

      if (!config) {
        console.error(`❌ Unknown collector: ${collectorName}`);
        console.error('');
        console.error('Available collectors:');
        Object.keys(configs).forEach(name => console.error(`  - ${name}`));
        process.exit(1);
      }

      await collector.collect(config);
    }
  } catch (error: any) {
    console.error('❌ Fatal error:', error.message);
    process.exit(1);
  } finally {
    await collector.close();
  }
}
