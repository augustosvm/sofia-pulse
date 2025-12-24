#!/usr/bin/env npx tsx
/**
 * Sofia Pulse - Monitoring Dashboard
 *
 * Gera relatório diário de saúde dos 69+ collectors:
 * - Quantos rodaram hoje
 * - Quantos tiveram sucesso vs falha
 * - Total de registros coletados
 * - Coletores problemáticos (não rodaram ou falharam repetidamente)
 */

import { Pool } from 'pg';
import { readdir } from 'fs/promises';
import { join } from 'path';
import dotenv from 'dotenv';

dotenv.config();

const dbConfig = {
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD,
  database: process.env.POSTGRES_DB || 'sofia_db',
};

interface CollectorLog {
  name: string;
  lastRun: Date | null;
  status: 'success' | 'failed' | 'never_ran';
  recordsCollected: number;
  errorMessage?: string;
}

async function getLogFiles(): Promise<string[]> {
  const logsDir = join(process.cwd(), 'logs');
  try {
    const files = await readdir(logsDir);
    return files.filter(f => f.endsWith('-collector.log'));
  } catch {
    return [];
  }
}

async function parseLogFile(logPath: string): Promise<CollectorLog> {
  const fs = await import('fs/promises');
  const collectorName = logPath.replace('-collector.log', '');

  try {
    const content = await fs.readFile(join(process.cwd(), 'logs', logPath), 'utf-8');
    const lines = content.split('\n');

    // Get last run timestamp from file mtime
    const stats = await fs.stat(join(process.cwd(), 'logs', logPath));
    const lastRun = stats.mtime;

    // Check if last run was successful
    const hasError = lines.some(l => l.includes('❌') || l.includes('Error') || l.includes('Failed'));
    const hasSuccess = lines.some(l => l.includes('✅'));

    // Extract collected count
    const collectedLine = lines.reverse().find(l => l.match(/Collected:\s*\d+/));
    const match = collectedLine?.match(/Collected:\s*(\d+)/);
    const recordsCollected = match ? parseInt(match[1]) : 0;

    // Extract error message if any
    const errorLine = lines.find(l => l.includes('Error:') || l.includes('❌'));
    const errorMessage = errorLine?.slice(0, 100);

    return {
      name: collectorName,
      lastRun,
      status: hasError ? 'failed' : hasSuccess ? 'success' : 'never_ran',
      recordsCollected,
      errorMessage,
    };
  } catch (error) {
    return {
      name: collectorName,
      lastRun: null,
      status: 'never_ran',
      recordsCollected: 0,
    };
  }
}

async function generateDashboard() {
  console.log('🎯 Sofia Pulse - Monitoring Dashboard');
  console.log('='.repeat(80));
  console.log(`📅 Report Date: ${new Date().toISOString().split('T')[0]}`);
  console.log('='.repeat(80));

  const pool = new Pool(dbConfig);

  try {
    // Get all log files
    const logFiles = await getLogFiles();
    console.log(`\n📊 Found ${logFiles.length} collector logs\n`);

    // Parse all logs
    const collectors = await Promise.all(
      logFiles.map(f => parseLogFile(f))
    );

    // Calculate statistics
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    const ranToday = collectors.filter(c => c.lastRun && c.lastRun >= today);
    const successful = collectors.filter(c => c.status === 'success');
    const failed = collectors.filter(c => c.status === 'failed');
    const neverRan = collectors.filter(c => c.status === 'never_ran');

    const totalRecords = collectors.reduce((sum, c) => sum + c.recordsCollected, 0);

    // Print summary
    console.log('📈 SUMMARY');
    console.log('-'.repeat(80));
    console.log(`Total Collectors: ${collectors.length}`);
    console.log(`Ran Today: ${ranToday.length} (${((ranToday.length / collectors.length) * 100).toFixed(1)}%)`);
    console.log(`Successful: ${successful.length} ✅`);
    console.log(`Failed: ${failed.length} ❌`);
    console.log(`Never Ran: ${neverRan.length} ⚠️`);
    console.log(`Total Records Collected: ${totalRecords.toLocaleString()}`);

    // Print failed collectors
    if (failed.length > 0) {
      console.log('\n❌ FAILED COLLECTORS');
      console.log('-'.repeat(80));
      failed.forEach(c => {
        const lastRunStr = c.lastRun ? c.lastRun.toISOString().split('T')[0] : 'Never';
        console.log(`• ${c.name}`);
        console.log(`  Last Run: ${lastRunStr}`);
        if (c.errorMessage) {
          console.log(`  Error: ${c.errorMessage}`);
        }
      });
    }

    // Print never ran collectors
    if (neverRan.length > 0) {
      console.log('\n⚠️  NEVER RAN');
      console.log('-'.repeat(80));
      neverRan.forEach(c => {
        console.log(`• ${c.name}`);
      });
    }

    // Print top performers
    const topPerformers = [...collectors]
      .filter(c => c.recordsCollected > 0)
      .sort((a, b) => b.recordsCollected - a.recordsCollected)
      .slice(0, 10);

    if (topPerformers.length > 0) {
      console.log('\n🏆 TOP 10 COLLECTORS (by records collected)');
      console.log('-'.repeat(80));
      topPerformers.forEach((c, i) => {
        console.log(`${i + 1}. ${c.name}: ${c.recordsCollected.toLocaleString()} records`);
      });
    }

    // Database statistics
    console.log('\n💾 DATABASE STATISTICS');
    console.log('-'.repeat(80));

    const tables = [
      'tech_trends',
      'jobs',
      'organizations',
      'funding_rounds',
      'industry_signals',
    ];

    for (const table of tables) {
      try {
        const result = await pool.query(`
          SELECT COUNT(*) as total,
                 MAX(collected_at) as last_update
          FROM sofia.${table}
          WHERE collected_at IS NOT NULL
        `);

        const total = parseInt(result.rows[0].total);
        const lastUpdate = result.rows[0].last_update;
        const lastUpdateStr = lastUpdate
          ? new Date(lastUpdate).toISOString().split('T')[0]
          : 'Never';

        console.log(`${table}: ${total.toLocaleString()} records (last update: ${lastUpdateStr})`);
      } catch (error) {
        console.log(`${table}: Error reading table`);
      }
    }

    console.log('\n' + '='.repeat(80));
    console.log('✅ Dashboard Generated Successfully');
    console.log('='.repeat(80));

  } catch (error) {
    console.error('❌ Error generating dashboard:', error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

if (require.main === module) {
  generateDashboard()
    .then(() => process.exit(0))
    .catch(err => {
      console.error('Fatal error:', err);
      process.exit(1);
    });
}

export { generateDashboard };
