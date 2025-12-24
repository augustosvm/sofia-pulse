#!/usr/bin/env tsx
/**
 * Collector Status Dashboard - Sofia Pulse
 *
 * Mostra status de TODOS os collectors: última execução, taxa de sucesso, etc.
 *
 * Usage:
 *   npx tsx scripts/collector-status.ts                # Status geral
 *   npx tsx scripts/collector-status.ts --stats        # Estatísticas detalhadas
 *   npx tsx scripts/collector-status.ts --health       # Health check
 *   npx tsx scripts/collector-status.ts --failures     # Falhas recentes
 *   npx tsx scripts/collector-status.ts --history npm  # Histórico de um collector
 */

import { Pool } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD,
  database: process.env.POSTGRES_DB || 'sofia_db',
});

// ============================================================================
// STATUS GERAL
// ============================================================================

async function showStatus() {
  console.log('');
  console.log('📊 COLLECTOR STATUS');
  console.log('='.repeat(80));
  console.log('');

  const result = await pool.query(`
    SELECT
      collector_name,
      last_run_at,
      last_status,
      last_items_collected,
      last_duration_ms,
      last_error
    FROM sofia.collector_last_run
    ORDER BY last_run_at DESC NULLS LAST
  `);

  if (result.rows.length === 0) {
    console.log('No collectors have run yet.');
    return;
  }

  const now = new Date();

  result.rows.forEach(row => {
    const status = row.last_status;
    const icon = status === 'success' ? '✅' :
                 status === 'failed' ? '❌' :
                 status === 'running' ? '⏳' : '⚠️';

    const lastRun = row.last_run_at ? new Date(row.last_run_at) : null;
    const timeSince = lastRun ?
      formatTimeSince(now.getTime() - lastRun.getTime()) :
      'never';

    console.log(`${icon} ${row.collector_name.padEnd(25)} Last: ${timeSince.padEnd(15)} Items: ${row.last_items_collected || 0}`);

    if (row.last_error) {
      console.log(`   Error: ${row.last_error.substring(0, 60)}...`);
    }
  });

  console.log('');
}

// ============================================================================
// ESTATÍSTICAS
// ============================================================================

async function showStats() {
  console.log('');
  console.log('📈 COLLECTOR STATISTICS');
  console.log('='.repeat(80));
  console.log('');

  const result = await pool.query(`
    SELECT
      collector_name,
      total_runs,
      successful_runs,
      failed_runs,
      success_rate,
      avg_duration_ms,
      total_items_collected
    FROM sofia.collector_stats
    ORDER BY total_runs DESC
  `);

  if (result.rows.length === 0) {
    console.log('No statistics available yet.');
    return;
  }

  console.log('Collector'.padEnd(25) + 'Runs'.padEnd(10) + 'Success'.padEnd(12) + 'Avg Time'.padEnd(12) + 'Total Items');
  console.log('-'.repeat(80));

  result.rows.forEach(row => {
    const avgTime = row.avg_duration_ms ? `${(row.avg_duration_ms / 1000).toFixed(1)}s` : 'N/A';
    const successRate = row.success_rate ? `${row.success_rate}%` : 'N/A';

    console.log(
      row.collector_name.padEnd(25) +
      row.total_runs.toString().padEnd(10) +
      successRate.padEnd(12) +
      avgTime.padEnd(12) +
      (row.total_items_collected || 0).toLocaleString()
    );
  });

  console.log('');
}

// ============================================================================
// HEALTH CHECK
// ============================================================================

async function showHealth() {
  console.log('');
  console.log('🏥 HEALTH CHECK');
  console.log('='.repeat(80));
  console.log('');

  // Collectors que não rodaram há muito tempo
  const stale = await pool.query(`
    SELECT
      collector_name,
      last_run_at,
      EXTRACT(EPOCH FROM (NOW() - last_run_at)) / 3600 as hours_since
    FROM sofia.collector_last_run
    WHERE last_run_at < NOW() - INTERVAL '2 days'
       OR last_run_at IS NULL
    ORDER BY last_run_at NULLS LAST
  `);

  if (stale.rows.length > 0) {
    console.log('⚠️  Stale collectors (not run in > 2 days):');
    console.log('');

    stale.rows.forEach(row => {
      const lastRun = row.last_run_at ? new Date(row.last_run_at).toISOString() : 'never';
      const hoursSince = row.hours_since ? Math.floor(row.hours_since) : 'N/A';

      console.log(`   ${row.collector_name.padEnd(25)} Last run: ${lastRun.padEnd(30)} (${hoursSince}h ago)`);
    });

    console.log('');
  } else {
    console.log('✅ All collectors are healthy (ran in last 2 days)');
    console.log('');
  }

  // Collectors com taxa de falha alta
  const failing = await pool.query(`
    SELECT
      collector_name,
      total_runs,
      failed_runs,
      success_rate
    FROM sofia.collector_stats
    WHERE success_rate < 80
      AND total_runs >= 5
    ORDER BY success_rate ASC
  `);

  if (failing.rows.length > 0) {
    console.log('❌ Collectors with high failure rate (<80%):');
    console.log('');

    failing.rows.forEach(row => {
      console.log(`   ${row.collector_name.padEnd(25)} ${row.failed_runs}/${row.total_runs} failed (${row.success_rate}% success)`);
    });

    console.log('');
  }

  // Collectors rodando agora
  const running = await pool.query(`
    SELECT
      collector_name,
      started_at,
      EXTRACT(EPOCH FROM (NOW() - started_at)) / 60 as minutes_running
    FROM sofia.collector_runs
    WHERE status = 'running'
      AND started_at > NOW() - INTERVAL '1 hour'
  `);

  if (running.rows.length > 0) {
    console.log('⏳ Currently running:');
    console.log('');

    running.rows.forEach(row => {
      const minutes = Math.floor(row.minutes_running);
      console.log(`   ${row.collector_name.padEnd(25)} Running for ${minutes} minutes`);
    });

    console.log('');
  }
}

// ============================================================================
// FALHAS RECENTES
// ============================================================================

async function showFailures() {
  console.log('');
  console.log('❌ RECENT FAILURES (last 7 days)');
  console.log('='.repeat(80));
  console.log('');

  const result = await pool.query(`
    SELECT
      collector_name,
      started_at,
      error_message,
      items_collected,
      items_failed
    FROM sofia.collector_recent_failures
    ORDER BY started_at DESC
    LIMIT 20
  `);

  if (result.rows.length === 0) {
    console.log('✅ No failures in the last 7 days!');
    console.log('');
    return;
  }

  result.rows.forEach(row => {
    const date = new Date(row.started_at).toISOString().replace('T', ' ').substring(0, 19);
    console.log(`[${date}] ${row.collector_name}`);
    console.log(`   Error: ${row.error_message || 'Unknown error'}`);
    console.log(`   Collected: ${row.items_collected}, Failed: ${row.items_failed}`);
    console.log('');
  });
}

// ============================================================================
// HISTÓRICO DE UM COLLECTOR
// ============================================================================

async function showHistory(collectorName: string) {
  console.log('');
  console.log(`📜 HISTORY: ${collectorName}`);
  console.log('='.repeat(80));
  console.log('');

  const result = await pool.query(`
    SELECT
      started_at,
      finished_at,
      status,
      items_collected,
      items_failed,
      duration_ms,
      error_message
    FROM sofia.collector_runs
    WHERE collector_name = $1
    ORDER BY started_at DESC
    LIMIT 20
  `, [collectorName]);

  if (result.rows.length === 0) {
    console.log(`No history found for ${collectorName}`);
    console.log('');
    return;
  }

  result.rows.forEach(row => {
    const date = new Date(row.started_at).toISOString().replace('T', ' ').substring(0, 19);
    const status = row.status === 'success' ? '✅' :
                   row.status === 'failed' ? '❌' : '⏳';
    const duration = row.duration_ms ? `${(row.duration_ms / 1000).toFixed(1)}s` : 'N/A';

    console.log(`${status} ${date}  Duration: ${duration.padEnd(8)}  Items: ${row.items_collected || 0}`);

    if (row.error_message) {
      console.log(`   Error: ${row.error_message.substring(0, 70)}`);
    }
  });

  console.log('');
}

// ============================================================================
// HELPERS
// ============================================================================

function formatTimeSince(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return `${seconds}s ago`;
}

// ============================================================================
// CLI
// ============================================================================

async function main() {
  const args = process.argv.slice(2);

  try {
    if (args.includes('--help') || args.includes('-h')) {
      console.log('');
      console.log('📊 Collector Status Dashboard');
      console.log('');
      console.log('Usage:');
      console.log('  npx tsx scripts/collector-status.ts                # General status');
      console.log('  npx tsx scripts/collector-status.ts --stats        # Detailed statistics');
      console.log('  npx tsx scripts/collector-status.ts --health       # Health check');
      console.log('  npx tsx scripts/collector-status.ts --failures     # Recent failures');
      console.log('  npx tsx scripts/collector-status.ts --history npm  # History of specific collector');
      console.log('');
    } else if (args.includes('--stats')) {
      await showStats();
    } else if (args.includes('--health')) {
      await showHealth();
    } else if (args.includes('--failures')) {
      await showFailures();
    } else if (args.includes('--history')) {
      const collectorName = args[args.indexOf('--history') + 1];
      if (!collectorName) {
        console.error('❌ Please specify collector name: --history <name>');
        process.exit(1);
      }
      await showHistory(collectorName);
    } else {
      await showStatus();
    }
  } catch (error: any) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
