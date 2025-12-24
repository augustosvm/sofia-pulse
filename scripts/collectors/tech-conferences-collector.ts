#!/usr/bin/env tsx
/**
 * Tech Conferences & Events Collector - Sofia Pulse
 *
 * Core engine for collecting tech conference and event data.
 * Tracks conferences as a leading indicator for tech trends.
 *
 * Supports:
 * - Confs.tech (open source conference tracker)
 * - Future: Meetup.com, Eventbrite, regional calendars
 *
 * Usage:
 *   npx tsx scripts/collectors/tech-conferences-collector.ts confs-tech
 *   npx tsx scripts/collectors/tech-conferences-collector.ts --all
 */

import { Pool } from 'pg';
import * as dotenv from 'dotenv';
import axios, { AxiosRequestConfig } from 'axios';
import { TechConferencesInserter, TechConferenceData } from '../shared/tech-conferences-inserter.js';
import { rateLimiters } from '../utils/rate-limiter.js';

dotenv.config();

// ============================================================================
// TYPES
// ============================================================================

export interface TechConferenceCollectorConfig {
  /** Nome único do collector (ex: 'confs-tech') */
  name: string;

  /** Nome para display nos logs */
  displayName: string;

  /** URL da API ou função que retorna URL */
  url: string | ((params?: any) => string);

  /** HTTP method (default: GET) */
  method?: 'GET' | 'POST';

  /** Headers HTTP */
  headers?: Record<string, string> | ((env: NodeJS.ProcessEnv) => Record<string, string>);

  /** Query parameters */
  params?: Record<string, any>;

  /** Timeout em ms (padrão: 30000) */
  timeout?: number;

  /** Rate limiter a usar ou tempo em ms */
  rateLimit?: keyof typeof rateLimiters | number;

  /** Função que parseia a resposta da API e retorna TechConferenceData[] */
  parseResponse: (data: any, env: NodeJS.ProcessEnv) => TechConferenceData[] | Promise<TechConferenceData[]>;

  /** Schedule cron (ex: '0 6 * * 1' for weekly Monday 6am) */
  schedule?: string | null;

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
// TECH CONFERENCES COLLECTOR ENGINE
// ============================================================================

export class TechConferencesCollector {
  private pool: Pool;
  private inserter: TechConferencesInserter;

  constructor() {
    this.pool = new Pool(dbConfig);
    this.inserter = new TechConferencesInserter(this.pool);
  }

  /**
   * Executa um collector baseado em sua configuração
   */
  async collect(config: TechConferenceCollectorConfig): Promise<{
    success: boolean;
    collected: number;
    errors: number;
    duration: number;
  }> {
    const startTime = Date.now();

    console.log('');
    console.log('='.repeat(70));
    console.log(`🎤 ${config.displayName}`);
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

      // 3. Preparar request config
      const requestConfig: AxiosRequestConfig = {
        headers,
        timeout: config.timeout || 30000,
        validateStatus: (status) => status >= 200 && status < 500,
      };

      if (config.params) {
        requestConfig.params = config.params;
      }

      // 4. Fazer request
      console.log(`🔍 Fetching from API...`);
      console.log(`   Method: ${config.method || 'GET'}`);
      console.log(`   URL: ${url.substring(0, 100)}${url.length > 100 ? '...' : ''}`);

      let response;

      if (config.rateLimit && typeof config.rateLimit === 'string' && config.rateLimit in rateLimiters) {
        // Usa rate limiter específico
        const rateLimiter = rateLimiters[config.rateLimit as keyof typeof rateLimiters];
        response = await rateLimiter.get(url, requestConfig);
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

      // 5. Parsear resposta
      console.log(`🔄 Parsing response...`);
      const conferences = await config.parseResponse(response.data, process.env);
      console.log(`   ✅ Parsed ${conferences.length} conferences/events`);
      console.log('');

      // 6. Inserir no banco
      console.log(`💾 Inserting into database...`);
      for (const conference of conferences) {
        try {
          await this.inserter.insertTechConference(conference);
          collected++;
        } catch (error: any) {
          console.error(`   ❌ Error inserting ${conference.event_name}:`, error.message);
          errors++;
        }
      }

      console.log(`   ✅ Inserted ${collected} conferences/events`);
      if (errors > 0) {
        console.log(`   ⚠️  ${errors} errors during insertion`);
      }

    } catch (error: any) {
      console.error('');
      console.error(`❌ Collection failed:`, error.message);

      if (axios.isAxiosError(error)) {
        if (error.response?.status === 403) {
          console.error('   💡 Hint: Check if API key is set or access denied');
        } else if (error.response?.status === 429) {
          console.error('   💡 Hint: Rate limit exceeded, try again later');
        } else if (error.response?.status === 404) {
          console.error('   💡 Hint: API endpoint not found or year/data unavailable');
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
    console.log(`   Collected: ${collected} conferences/events`);
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
  async collectAll(configs: TechConferenceCollectorConfig[]): Promise<void> {
    console.log('');
    console.log('🚀 Running all tech conferences collectors...');
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
    console.log(`🎤 Total collected: ${totalCollected} conferences/events`);
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

export async function runTechConferencesCLI(configs: Record<string, TechConferenceCollectorConfig>) {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    console.log('');
    console.log('🎤 Tech Conferences & Events Collector - Sofia Pulse');
    console.log('');
    console.log('Usage:');
    console.log('  npx tsx scripts/collectors/tech-conferences-collector.ts <collector>');
    console.log('  npx tsx scripts/collectors/tech-conferences-collector.ts --all');
    console.log('');
    console.log('Available collectors:');
    Object.keys(configs).forEach(name => {
      const config = configs[name];
      console.log(`  - ${name.padEnd(25)} ${config.description || ''}`);
    });
    console.log('');
    process.exit(0);
  }

  const collector = new TechConferencesCollector();

  try {
    if (args.includes('--all')) {
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
