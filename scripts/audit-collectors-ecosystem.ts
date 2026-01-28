#!/usr/bin/env tsx
/**
 * Collector Ecosystem Wiring Audit - Sofia Pulse
 *
 * Validates compliance with NEW STANDARD:
 * Collector -> Registry -> Cron -> DB Table -> Analytics/Builder
 *
 * Exit codes:
 * - 0: Core health passes
 * - 1: Core health fails or critical errors
 *
 * Usage:
 *   npx tsx scripts/audit-collectors-ecosystem.ts
 */

import fs from 'fs';
import path from 'path';
import { Pool } from 'pg';
import dotenv from 'dotenv';

// For ESM compatibility
const __filename = new URL('', import.meta.url).pathname;
const __dirname = new URL('.', import.meta.url).pathname;

dotenv.config();

console.log('Imports successful');

// Types
interface CollectorAuditRecord {
  collector_id: string;
  language: 'ts' | 'py';
  path: string;
  registry_status: 'registered_ts' | 'registered_legacy_py' | 'unregistered';
  schedule_status: 'scheduled' | 'unscheduled' | 'unknown';
  schedule?: string;
  destination_tables: Array<{
    table: string;
    confidence: number;
    method: string;
  }>;
  db_status: Array<{
    table: string;
    exists: boolean;
    row_count?: number;
    last_update?: string;
    timestamp_field?: string;
    error?: string;
  }>;
  analytics_usage: {
    used_by_cross_signals_builder: boolean;
    used_by_insights_pipeline: boolean;
    used_by_consumers: string[];
  };
  mock_flags: {
    mock_detected: boolean;
    evidence_lines: string[];
  };
  overall_status: 'PASS' | 'PARTIAL' | 'ORPHAN' | 'DEAD' | 'MISMATCH';
}

interface AuditSummary {
  total_collectors: number;
  registered: number;
  unregistered: number;
  scheduled: number;
  unscheduled: number;
  status_counts: Record<string, number>;
  core_health: {
    pass: boolean;
    failures: string[];
  };
}

interface AuditReport {
  generated_at: string;
  schema_version: string;
  summary: AuditSummary;
  collectors: CollectorAuditRecord[];
}

// Core sources that MUST be present
const CORE_SOURCES = [
  { pattern: /ga4/i, name: 'GA4' },
  { pattern: /vscode/i, name: 'VSCode' },
  { pattern: /patent/i, name: 'Patents' },
  { pattern: /hackernews|news_items/i, name: 'HackerNews/News' }
];

// Core tables expected by cross-signals builder
const CORE_TABLES = [
  'sofia.analytics_events',
  'sofia.vscode_extensions_daily',
  'sofia.patents',
  'sofia.news_items'
];

// Database connection
const pool = new Pool({
  host: process.env.POSTGRES_HOST || process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || process.env.DB_PORT || '5432'),
  database: process.env.POSTGRES_DB || process.env.DB_NAME || 'sofia_db',
  user: process.env.POSTGRES_USER || process.env.DB_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD || process.env.DB_PASSWORD || 'sofia123strong'
});

// Helper: Read file content
function readFileContent(filePath: string): string {
  try {
    return fs.readFileSync(filePath, 'utf-8');
  } catch {
    return '';
  }
}

// Helper: Recursively find files
function findFiles(dir: string, pattern: RegExp): string[] {
  const results: string[] = [];

  if (!fs.existsSync(dir)) return results;

  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      results.push(...findFiles(fullPath, pattern));
    } else if (pattern.test(entry.name)) {
      results.push(fullPath);
    }
  }

  return results;
}

// Parse collect.ts to extract registered collectors
function parseRegisteredCollectors(): Map<string, { language: 'ts', schedule?: string }> {
  const collectors = new Map();
  const repoRoot = path.resolve(__dirname, '..');

  // Load all config files
  const configFiles = [
    'configs/tech-trends-config.js',
    'configs/research-papers-config.js',
    'configs/jobs-config.js',
    'configs/organizations-config.js',
    'configs/funding-config.js',
    'configs/developer-tools-config.js',
    'configs/tech-conferences-config.js',
    'configs/brazil-config.js',
    'configs/industry-signals-config.js'
  ];

  for (const configFile of configFiles) {
    const configPath = path.join(repoRoot, 'scripts', configFile);
    if (!fs.existsSync(configPath)) continue;

    try {
      // Dynamic import would be better but use simple parsing
      const content = readFileContent(configPath);

      // Extract collector names and schedules
      const collectorMatches = Array.from(content.matchAll(/'([^']+)':\s*{[^}]*schedule:\s*'([^']+)'/g));
      for (const match of collectorMatches) {
        collectors.set(match[1], { language: 'ts' as const, schedule: match[2] });
      }

      // Also try double quotes
      const collectorMatches2 = Array.from(content.matchAll(/"([^"]+)":\s*{[^}]*schedule:\s*"([^"]+)"/g));
      for (const match of collectorMatches2) {
        collectors.set(match[1], { language: 'ts' as const, schedule: match[2] });
      }
    } catch (err) {
      console.error(`Error parsing ${configFile}:`, err);
    }
  }

  // Add standalone collectors from collect.ts
  const collectTsPath = path.join(repoRoot, 'scripts', 'collect.ts');
  const collectContent = readFileContent(collectTsPath);

  // Find standalone collectors like greenhouse, catho, currency-rates, etc.
  const standaloneMatches = Array.from(collectContent.matchAll(/if \(collectorName === '([^']+)'\)/g));
  for (const match of standaloneMatches) {
    if (!collectors.has(match[1])) {
      collectors.set(match[1], { language: 'ts' as const });
    }
  }

  return collectors;
}

// Parse legacy-python-config.ts
function parseLegacyPythonCollectors(): Map<string, { language: 'py', schedule?: string, script: string }> {
  const collectors = new Map();
  const repoRoot = path.resolve(__dirname, '..');
  const configPath = path.join(repoRoot, 'scripts', 'configs', 'legacy-python-config.ts');

  if (!fs.existsSync(configPath)) return collectors;

  const content = readFileContent(configPath);

  // Extract Python collectors
  const matches = Array.from(content.matchAll(/'([^']+)':\s*{\s*name:\s*'[^']+',\s*description:\s*'[^']+',\s*script:\s*'([^']+)',\s*schedule:\s*'([^']+)'/g));
  for (const match of matches) {
    collectors.set(match[1], {
      language: 'py' as const,
      schedule: match[3],
      script: match[2]
    });
  }

  return collectors;
}

// Scan filesystem for all collectors
function scanFilesystemCollectors(): Array<{ path: string, language: 'ts' | 'py' }> {
  const repoRoot = path.resolve(__dirname, '..');
  const scriptsDir = path.join(repoRoot, 'scripts');

  const results: Array<{ path: string, language: 'ts' | 'py' }> = [];

  // Find TypeScript collectors
  const tsCollectors = findFiles(scriptsDir, /^collect.*\.ts$/);
  for (const tsPath of tsCollectors) {
    results.push({ path: tsPath, language: 'ts' });
  }

  // Find Python collectors
  const pyCollectors = findFiles(scriptsDir, /^collect.*\.py$/);
  for (const pyPath of pyCollectors) {
    results.push({ path: pyPath, language: 'py' });
  }

  return results;
}

// Infer destination tables from collector script
function inferDestinationTables(filePath: string, language: 'ts' | 'py'): Array<{ table: string, confidence: number, method: string }> {
  const content = readFileContent(filePath);
  const tables: Array<{ table: string, confidence: number, method: string }> = [];
  const seen = new Set<string>();

  // High confidence: explicit INSERT/COPY statements
  const insertMatches = Array.from(content.matchAll(/(?:INSERT\s+INTO|COPY)\s+sofia\.(\w+)/gi));
  for (const match of insertMatches) {
    const table = `sofia.${match[1]}`;
    if (!seen.has(table)) {
      tables.push({ table, confidence: 0.9, method: 'INSERT/COPY statement' });
      seen.add(table);
    }
  }

  // Medium confidence: table references
  const tableMatches = Array.from(content.matchAll(/sofia\.(\w+)/gi));
  for (const match of tableMatches) {
    const table = `sofia.${match[1]}`;
    if (!seen.has(table)) {
      tables.push({ table, confidence: 0.6, method: 'table reference' });
      seen.add(table);
    }
  }

  // Low confidence: table names in comments or strings
  const commentMatches = Array.from(content.matchAll(/['"`]sofia\.(\w+)['"`]/gi));
  for (const match of commentMatches) {
    const table = `sofia.${match[1]}`;
    if (!seen.has(table)) {
      tables.push({ table, confidence: 0.3, method: 'string literal' });
      seen.add(table);
    }
  }

  return tables;
}

// Check database status for tables
async function checkDatabaseStatus(tables: string[]): Promise<Array<{
  table: string;
  exists: boolean;
  row_count?: number;
  last_update?: string;
  timestamp_field?: string;
  error?: string;
}>> {
  const results = [];

  for (const table of tables) {
    const [schema, tableName] = table.split('.');

    try {
      // Check if table exists
      const existsResult = await pool.query(
        `SELECT EXISTS (
          SELECT FROM information_schema.tables
          WHERE table_schema = $1 AND table_name = $2
        )`,
        [schema || 'sofia', tableName]
      );

      const exists = existsResult.rows[0].exists;

      if (!exists) {
        results.push({ table, exists: false });
        continue;
      }

      // Get row count
      const countResult = await pool.query(`SELECT COUNT(*) as count FROM ${table}`);
      const rowCount = parseInt(countResult.rows[0].count);

      // Try to find last update timestamp
      let lastUpdate: string | undefined;
      let timestampField: string | undefined;

      const timestampFields = ['collected_at', 'created_at', 'inserted_at', 'updated_at', 'event_timestamp', 'snapshot_date', 'date', 'published'];

      for (const field of timestampFields) {
        try {
          const tsResult = await pool.query(`SELECT MAX(${field}) as max_ts FROM ${table}`);
          if (tsResult.rows[0].max_ts) {
            lastUpdate = tsResult.rows[0].max_ts;
            timestampField = field;
            break;
          }
        } catch {
          // Field doesn't exist, try next
        }
      }

      results.push({
        table,
        exists: true,
        row_count: rowCount,
        last_update: lastUpdate,
        timestamp_field: timestampField
      });

    } catch (error: any) {
      results.push({
        table,
        exists: false,
        error: error.message
      });
    }
  }

  return results;
}

// Check if table is used by analytics
function checkAnalyticsUsage(tableName: string): {
  used_by_cross_signals_builder: boolean;
  used_by_insights_pipeline: boolean;
  used_by_consumers: string[];
} {
  const repoRoot = path.resolve(__dirname, '..');
  const consumers: string[] = [];

  // Check cross-signals builder
  const crossSignalsPath = path.join(repoRoot, 'scripts', 'build-cross-signals.py');
  const crossSignalsContent = readFileContent(crossSignalsPath);
  const usedByCrossSignals = crossSignalsContent.includes(tableName);

  // Check insights pipelines
  const insightsFiles = findFiles(path.join(repoRoot, 'scripts'), /generate_insights.*\.py$/);
  let usedByInsights = false;

  for (const insightsFile of insightsFiles) {
    const content = readFileContent(insightsFile);
    if (content.includes(tableName)) {
      usedByInsights = true;
      consumers.push(path.basename(insightsFile));
    }
  }

  // Check other analytics scripts
  const analyticsDir = path.join(repoRoot, 'analytics');
  if (fs.existsSync(analyticsDir)) {
    const analyticsFiles = findFiles(analyticsDir, /\.py$/);
    for (const analyticsFile of analyticsFiles) {
      const content = readFileContent(analyticsFile);
      if (content.includes(tableName)) {
        consumers.push(path.basename(analyticsFile));
      }
    }
  }

  return {
    used_by_cross_signals_builder: usedByCrossSignals,
    used_by_insights_pipeline: usedByInsights,
    used_by_consumers: [...new Set(consumers)]
  };
}

// Detect mock/placeholder data
function detectMockFlags(filePath: string): {
  mock_detected: boolean;
  evidence_lines: string[];
} {
  const content = readFileContent(filePath);
  const lines = content.split('\n');
  const evidence: string[] = [];

  const mockPatterns = [
    /MOCK/i,
    /PLACEHOLDER/i,
    /TODO:?\s*mock/i,
    /FIXME:?\s*(mock|placeholder|hardcoded)/i,
    /hardcoded\s*data/i,
    /fake\s*data/i,
    /dummy\s*data/i
  ];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    for (const pattern of mockPatterns) {
      if (pattern.test(line)) {
        evidence.push(`Line ${i + 1}: ${line.trim().substring(0, 100)}`);
        break;
      }
    }
  }

  return {
    mock_detected: evidence.length > 0,
    evidence_lines: evidence.slice(0, 5) // Max 5 evidence lines
  };
}

// Determine overall status
function determineOverallStatus(record: Omit<CollectorAuditRecord, 'overall_status'>): CollectorAuditRecord['overall_status'] {
  // ORPHAN: unregistered or unscheduled
  if (record.registry_status === 'unregistered' || record.schedule_status === 'unscheduled') {
    return 'ORPHAN';
  }

  const isRegistered = record.registry_status === 'registered_ts' || record.registry_status === 'registered_legacy_py';

  // DEAD: registered + scheduled but table missing or empty
  if (isRegistered && record.schedule_status === 'scheduled') {
    const hasData = record.db_status.some(db => db.exists && (db.row_count ?? 0) > 0);
    if (!hasData) {
      return 'DEAD';
    }
  }

  // PASS: registered + scheduled + table exists with data + (used by analytics OR collector-only)
  const hasData = record.db_status.some(db => db.exists && (db.row_count ?? 0) > 0);
  const usedByAnalytics = record.analytics_usage.used_by_cross_signals_builder ||
                          record.analytics_usage.used_by_insights_pipeline ||
                          record.analytics_usage.used_by_consumers.length > 0;

  if (isRegistered &&
      record.schedule_status === 'scheduled' &&
      hasData &&
      usedByAnalytics) {
    return 'PASS';
  }

  // PARTIAL: some links exist but missing others
  return 'PARTIAL';
}

// Main audit function
async function auditCollectorEcosystem(): Promise<AuditReport> {
  console.log('Starting collector ecosystem audit...');

  // Test database connection
  let dbAvailable = true;
  try {
    await pool.query('SELECT 1');
    console.log('Database connection: OK');
  } catch (error: any) {
    console.warn('Database connection: FAILED');
    console.warn('Continuing with limited audit (no DB checks)');
    console.warn(`DB Error: ${error.message}`);
    dbAvailable = false;
  }

  const registeredTs = parseRegisteredCollectors();
  const registeredPy = parseLegacyPythonCollectors();
  const filesystemCollectors = scanFilesystemCollectors();

  console.log(`Found ${registeredTs.size} registered TypeScript collectors`);
  console.log(`Found ${registeredPy.size} registered Python collectors`);
  console.log(`Found ${filesystemCollectors.length} collector files in filesystem`);

  const allCollectors: CollectorAuditRecord[] = [];
  const processedIds = new Set<string>();

  // Process registered TypeScript collectors
  for (const [id, info] of registeredTs) {
    if (processedIds.has(id)) continue;
    processedIds.add(id);

    const collectorPath = filesystemCollectors.find(c =>
      c.language === 'ts' && (c.path.includes(id) || c.path.includes('collect.ts'))
    )?.path || `scripts/collect-${id}.ts`;

    const destinationTables = inferDestinationTables(collectorPath, 'ts');
    const dbStatus = dbAvailable ? await checkDatabaseStatus(destinationTables.map(t => t.table)) : [];

    const analyticsUsage = {
      used_by_cross_signals_builder: false,
      used_by_insights_pipeline: false,
      used_by_consumers: [] as string[]
    };

    for (const table of destinationTables) {
      const usage = checkAnalyticsUsage(table.table);
      if (usage.used_by_cross_signals_builder) analyticsUsage.used_by_cross_signals_builder = true;
      if (usage.used_by_insights_pipeline) analyticsUsage.used_by_insights_pipeline = true;
      analyticsUsage.used_by_consumers.push(...usage.used_by_consumers);
    }
    analyticsUsage.used_by_consumers = Array.from(new Set(analyticsUsage.used_by_consumers));

    const mockFlags = fs.existsSync(collectorPath) ? detectMockFlags(collectorPath) : { mock_detected: false, evidence_lines: [] };

    const record: Omit<CollectorAuditRecord, 'overall_status'> = {
      collector_id: id,
      language: 'ts',
      path: collectorPath,
      registry_status: 'registered_ts',
      schedule_status: info.schedule ? 'scheduled' : 'unknown',
      schedule: info.schedule,
      destination_tables: destinationTables,
      db_status: dbStatus,
      analytics_usage: analyticsUsage,
      mock_flags: mockFlags
    };

    allCollectors.push({
      ...record,
      overall_status: determineOverallStatus(record)
    });
  }

  // Process registered Python collectors
  for (const [id, info] of registeredPy) {
    if (processedIds.has(id)) continue;
    processedIds.add(id);

    const collectorPath = path.resolve(__dirname, '..', info.script);

    const destinationTables = fs.existsSync(collectorPath) ? inferDestinationTables(collectorPath, 'py') : [];
    const dbStatus = dbAvailable ? await checkDatabaseStatus(destinationTables.map(t => t.table)) : [];

    const analyticsUsage = {
      used_by_cross_signals_builder: false,
      used_by_insights_pipeline: false,
      used_by_consumers: [] as string[]
    };

    for (const table of destinationTables) {
      const usage = checkAnalyticsUsage(table.table);
      if (usage.used_by_cross_signals_builder) analyticsUsage.used_by_cross_signals_builder = true;
      if (usage.used_by_insights_pipeline) analyticsUsage.used_by_insights_pipeline = true;
      analyticsUsage.used_by_consumers.push(...usage.used_by_consumers);
    }
    analyticsUsage.used_by_consumers = Array.from(new Set(analyticsUsage.used_by_consumers));

    const mockFlags = fs.existsSync(collectorPath) ? detectMockFlags(collectorPath) : { mock_detected: false, evidence_lines: [] };

    const record: Omit<CollectorAuditRecord, 'overall_status'> = {
      collector_id: id,
      language: 'py',
      path: collectorPath,
      registry_status: 'registered_legacy_py',
      schedule_status: info.schedule ? 'scheduled' : 'unknown',
      schedule: info.schedule,
      destination_tables: destinationTables,
      db_status: dbStatus,
      analytics_usage: analyticsUsage,
      mock_flags: mockFlags
    };

    allCollectors.push({
      ...record,
      overall_status: determineOverallStatus(record)
    });
  }

  // Process unregistered collectors
  for (const { path: collectorPath, language } of filesystemCollectors) {
    const basename = path.basename(collectorPath, path.extname(collectorPath));
    const id = `unregistered::${basename}`;

    if (processedIds.has(basename) || processedIds.has(id)) continue;

    // Check if this collector is referenced in collect.ts
    const isStandalone = registeredTs.has(basename) || registeredPy.has(basename);
    if (isStandalone) continue;

    processedIds.add(id);

    const destinationTables = inferDestinationTables(collectorPath, language);
    const dbStatus = dbAvailable ? await checkDatabaseStatus(destinationTables.map(t => t.table)) : [];

    const analyticsUsage = {
      used_by_cross_signals_builder: false,
      used_by_insights_pipeline: false,
      used_by_consumers: [] as string[]
    };

    for (const table of destinationTables) {
      const usage = checkAnalyticsUsage(table.table);
      if (usage.used_by_cross_signals_builder) analyticsUsage.used_by_cross_signals_builder = true;
      if (usage.used_by_insights_pipeline) analyticsUsage.used_by_insights_pipeline = true;
      analyticsUsage.used_by_consumers.push(...usage.used_by_consumers);
    }
    analyticsUsage.used_by_consumers = Array.from(new Set(analyticsUsage.used_by_consumers));

    const mockFlags = detectMockFlags(collectorPath);

    const record: Omit<CollectorAuditRecord, 'overall_status'> = {
      collector_id: id,
      language,
      path: collectorPath,
      registry_status: 'unregistered',
      schedule_status: 'unscheduled',
      destination_tables: destinationTables,
      db_status: dbStatus,
      analytics_usage: analyticsUsage,
      mock_flags: mockFlags
    };

    allCollectors.push({
      ...record,
      overall_status: determineOverallStatus(record)
    });
  }

  // Compute summary and core health
  const summary: AuditSummary = {
    total_collectors: allCollectors.length,
    registered: allCollectors.filter(c => c.registry_status !== 'unregistered').length,
    unregistered: allCollectors.filter(c => c.registry_status === 'unregistered').length,
    scheduled: allCollectors.filter(c => c.schedule_status === 'scheduled').length,
    unscheduled: allCollectors.filter(c => c.schedule_status === 'unscheduled').length,
    status_counts: {
      PASS: allCollectors.filter(c => c.overall_status === 'PASS').length,
      PARTIAL: allCollectors.filter(c => c.overall_status === 'PARTIAL').length,
      ORPHAN: allCollectors.filter(c => c.overall_status === 'ORPHAN').length,
      DEAD: allCollectors.filter(c => c.overall_status === 'DEAD').length,
      MISMATCH: allCollectors.filter(c => c.overall_status === 'MISMATCH').length
    },
    core_health: {
      pass: true,
      failures: []
    }
  };

  // Check core health
  if (!dbAvailable) {
    summary.core_health.pass = false;
    summary.core_health.failures.push('Database unavailable - cannot verify core health');
  } else {
    for (const coreSource of CORE_SOURCES) {
      const found = allCollectors.some(c => coreSource.pattern.test(c.collector_id) && c.overall_status !== 'ORPHAN');
      if (!found) {
        summary.core_health.pass = false;
        summary.core_health.failures.push(`Core source missing: ${coreSource.name}`);
      }
    }

    // Check core tables in cross-signals builder
    const crossSignalsPath = path.join(path.resolve(__dirname, '..'), 'scripts', 'build-cross-signals.py');
    const crossSignalsContent = readFileContent(crossSignalsPath);

    for (const coreTable of CORE_TABLES) {
      if (!crossSignalsContent.includes(coreTable)) {
        summary.core_health.pass = false;
        summary.core_health.failures.push(`Core table not referenced in builder: ${coreTable}`);
      }
    }
  }

  return {
    generated_at: new Date().toISOString(),
    schema_version: '1.0.0',
    summary,
    collectors: allCollectors
  };
}

// Generate Markdown report
function generateMarkdownReport(report: AuditReport): string {
  const lines: string[] = [];

  lines.push('# Collector Ecosystem Wiring Audit Report');
  lines.push('');
  lines.push('## How to Run');
  lines.push('```bash');
  lines.push('npx tsx scripts/audit-collectors-ecosystem.ts');
  lines.push('```');
  lines.push('');
  lines.push('## What PASS Means');
  lines.push('A collector has PASS status when:');
  lines.push('- Registered in config (TypeScript or Python)');
  lines.push('- Has a cron schedule defined');
  lines.push('- Destination table(s) exist in database');
  lines.push('- Table(s) contain data (row_count > 0)');
  lines.push('- Used by analytics/builder (cross-signals, insights, or consumers)');
  lines.push('');
  lines.push('---');
  lines.push('');
  lines.push(`**Generated:** ${report.generated_at}`);
  lines.push(`**Schema Version:** ${report.schema_version}`);
  lines.push('');

  // Executive Summary
  lines.push('## Executive Summary');
  lines.push('');
  lines.push(`- Total Collectors: ${report.summary.total_collectors}`);
  lines.push(`- Registered: ${report.summary.registered}`);
  lines.push(`- Unregistered: ${report.summary.unregistered}`);
  lines.push(`- Scheduled: ${report.summary.scheduled}`);
  lines.push(`- Unscheduled: ${report.summary.unscheduled}`);
  lines.push('');
  lines.push('### Status Distribution');
  lines.push('');
  lines.push(`- PASS: ${report.summary.status_counts.PASS}`);
  lines.push(`- PARTIAL: ${report.summary.status_counts.PARTIAL}`);
  lines.push(`- ORPHAN: ${report.summary.status_counts.ORPHAN}`);
  lines.push(`- DEAD: ${report.summary.status_counts.DEAD}`);
  lines.push(`- MISMATCH: ${report.summary.status_counts.MISMATCH}`);
  lines.push('');

  // Core Health
  lines.push('## Core Health Gate');
  lines.push('');
  if (report.summary.core_health.pass) {
    lines.push('**Status:** PASS');
  } else {
    lines.push('**Status:** FAIL');
    lines.push('');
    lines.push('### Failures:');
    for (const failure of report.summary.core_health.failures) {
      lines.push(`- ${failure}`);
    }
  }
  lines.push('');

  // Top 20 Failures
  const failures = report.collectors.filter(c => c.overall_status !== 'PASS').slice(0, 20);
  if (failures.length > 0) {
    lines.push('## Top 20 Failures');
    lines.push('');
    for (const collector of failures) {
      lines.push(`### ${collector.collector_id}`);
      lines.push(`- Status: ${collector.overall_status}`);
      lines.push(`- Language: ${collector.language}`);
      lines.push(`- Registry: ${collector.registry_status}`);
      lines.push(`- Schedule: ${collector.schedule_status}${collector.schedule ? ` (${collector.schedule})` : ''}`);
      if (collector.destination_tables.length > 0) {
        lines.push(`- Destination Tables: ${collector.destination_tables.map(t => t.table).join(', ')}`);
      }
      if (collector.db_status.length > 0) {
        const missingTables = collector.db_status.filter(db => !db.exists);
        if (missingTables.length > 0) {
          lines.push(`- Missing Tables: ${missingTables.map(db => db.table).join(', ')}`);
        }
      }
      lines.push('');
    }
  }

  // ORPHAN collectors
  const orphans = report.collectors.filter(c => c.overall_status === 'ORPHAN');
  if (orphans.length > 0) {
    lines.push('## ORPHAN Collectors (Unregistered or Unscheduled)');
    lines.push('');
    for (const collector of orphans) {
      lines.push(`- **${collector.collector_id}**`);
      lines.push(`  - Path: ${collector.path}`);
      lines.push(`  - Registry: ${collector.registry_status}`);
      lines.push(`  - Schedule: ${collector.schedule_status}`);
      lines.push('');
    }
  }

  // Mock detected
  const mocks = report.collectors.filter(c => c.mock_flags.mock_detected);
  if (mocks.length > 0) {
    lines.push('## Collectors with MOCK/Placeholder Data Detected');
    lines.push('');
    for (const collector of mocks) {
      lines.push(`### ${collector.collector_id}`);
      lines.push('Evidence:');
      for (const evidence of collector.mock_flags.evidence_lines) {
        lines.push(`- ${evidence}`);
      }
      lines.push('');
    }
  }

  return lines.join('\n');
}

// Main execution
async function main() {
  try {
    const report = await auditCollectorEcosystem();

    // Write JSON report
    const outputDir = path.resolve(__dirname, '..', 'outputs', 'audit');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    const jsonPath = path.join(outputDir, 'collectors_ecosystem_report.json');
    fs.writeFileSync(jsonPath, JSON.stringify(report, null, 2));
    console.log(`JSON report written to: ${jsonPath}`);

    // Write Markdown report
    const markdown = generateMarkdownReport(report);
    const mdPath = path.join(outputDir, 'collectors_ecosystem_report.md');
    fs.writeFileSync(mdPath, markdown);
    console.log(`Markdown report written to: ${mdPath}`);

    // Print summary
    console.log('\nSummary:');
    console.log(`- Total: ${report.summary.total_collectors}`);
    console.log(`- PASS: ${report.summary.status_counts.PASS}`);
    console.log(`- PARTIAL: ${report.summary.status_counts.PARTIAL}`);
    console.log(`- ORPHAN: ${report.summary.status_counts.ORPHAN}`);
    console.log(`- DEAD: ${report.summary.status_counts.DEAD}`);
    console.log(`- Core Health: ${report.summary.core_health.pass ? 'PASS' : 'FAIL'}`);

    // Exit code based on core health
    if (!report.summary.core_health.pass) {
      console.error('\nCore health gate FAILED');
      process.exit(1);
    }

    console.log('\nAudit completed successfully');
    process.exit(0);

  } catch (error) {
    console.error('Fatal error during audit:', error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

// Run if executed directly
console.log('Script starting...');

main().catch(err => {
  console.error('Unhandled error in main:', err);
  process.exit(1);
});
