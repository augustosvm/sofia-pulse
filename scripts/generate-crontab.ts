#!/usr/bin/env tsx
/**
 * Crontab Generator - Sofia Pulse
 *
 * Gera automaticamente o crontab baseado nos schedules definidos nas configs.
 * Suporta: Tech Trends + Research Papers + Jobs + Organizations + Funding + Developer Tools
 * Isso garante que os crons estão sempre corretos e sincronizados com as configs.
 *
 * Usage:
 *   npx tsx scripts/generate-crontab.ts           # Mostra o crontab
 *   npx tsx scripts/generate-crontab.ts --install # Instala no crontab
 */

import { collectors as techTrendsCollectors } from './configs/tech-trends-config.js';
import { researchPapersCollectors } from './configs/research-papers-config.js';
import { jobsCollectors } from './configs/jobs-config.js';
import { organizationsCollectors } from './configs/organizations-config.js';
import { fundingCollectors } from './configs/funding-config.js';
import { developerToolsCollectors } from './configs/developer-tools-config.js';
import { techConferencesCollectors } from './configs/tech-conferences-config.js';
import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

// ============================================================================
// CRONTAB GENERATION
// ============================================================================

function generateCrontab(): string {
  const lines: string[] = [];

  // Header
  lines.push('# ============================================================================');
  lines.push('# Sofia Pulse - Auto-generated Crontab');
  lines.push('# Generated: ' + new Date().toISOString());
  lines.push('# DO NOT EDIT MANUALLY - Run: npx tsx scripts/generate-crontab.ts --install');
  lines.push('# ============================================================================');
  lines.push('');

  // Environment
  lines.push('# Environment');
  lines.push('SHELL=/bin/bash');
  lines.push('PATH=/usr/local/bin:/usr/bin:/bin');
  lines.push('');

  // Group collectors by schedule (ALL types)
  const bySchedule = new Map<string, string[]>();

  // Add tech trends collectors
  Object.values(techTrendsCollectors).forEach(config => {
    if (!config.schedule) return;

    if (!bySchedule.has(config.schedule)) {
      bySchedule.set(config.schedule, []);
    }

    bySchedule.get(config.schedule)!.push(config.name);
  });

  // Add research papers collectors
  Object.values(researchPapersCollectors).forEach(config => {
    if (!config.schedule) return;

    if (!bySchedule.has(config.schedule)) {
      bySchedule.set(config.schedule, []);
    }

    bySchedule.get(config.schedule)!.push(config.name);
  });

  // Add jobs collectors
  Object.values(jobsCollectors).forEach(config => {
    if (!config.schedule) return;

    if (!bySchedule.has(config.schedule)) {
      bySchedule.set(config.schedule, []);
    }

    bySchedule.get(config.schedule)!.push(config.name);
  });

  // Add organizations collectors
  Object.values(organizationsCollectors).forEach(config => {
    if (!config.schedule) return;

    if (!bySchedule.has(config.schedule)) {
      bySchedule.set(config.schedule, []);
    }

    bySchedule.get(config.schedule)!.push(config.name);
  });

  // Add funding collectors
  Object.values(fundingCollectors).forEach(config => {
    if (!config.schedule) return;

    if (!bySchedule.has(config.schedule)) {
      bySchedule.set(config.schedule, []);
    }

    bySchedule.get(config.schedule)!.push(config.name);
  });

  // Add developer tools collectors
  Object.values(developerToolsCollectors).forEach(config => {
    if (!config.schedule) return;

    if (!bySchedule.has(config.schedule)) {
      bySchedule.set(config.schedule, []);
    }

    bySchedule.get(config.schedule)!.push(config.name);
  });

  // Add tech conferences collectors
  Object.values(techConferencesCollectors).forEach(config => {
    if (!config.schedule) return;

    if (!bySchedule.has(config.schedule)) {
      bySchedule.set(config.schedule, []);
    }

    bySchedule.get(config.schedule)!.push(config.name);
  });

  // Generate cron entries
  const projectPath = process.cwd();

  bySchedule.forEach((collectorNames, schedule) => {
    // Determine frequency description
    let description = '';
    if (schedule.includes('*/12')) description = '2x/day (0h, 12h)';
    else if (schedule.includes('*/6')) description = '4x/day (0h, 6h, 12h, 18h)';
    else if (schedule.match(/0 \d+ \*/)) description = '1x/day';
    else if (schedule.match(/0 \d+ \* \* 1/)) description = '1x/week (Monday)';
    else if (schedule.match(/0 \d+ 1 \*/)) description = '1x/month (1st day)';
    else description = 'Custom schedule';

    lines.push(`# ${description} - ${collectorNames.join(', ')}`);

    collectorNames.forEach(name => {
      const logFile = `${projectPath}/logs/${name}-collector.log`;
      const command = `cd ${projectPath} && npx tsx scripts/collect.ts ${name} >> ${logFile} 2>&1`;
      lines.push(`${schedule} ${command}`);
    });

    lines.push('');
  });

  // Summary comment
  const totalCollectors = Object.keys(techTrendsCollectors).length +
                         Object.keys(researchPapersCollectors).length +
                         Object.keys(jobsCollectors).length +
                         Object.keys(organizationsCollectors).length +
                         Object.keys(fundingCollectors).length +
                         Object.keys(developerToolsCollectors).length +
                         Object.keys(techConferencesCollectors).length;
  lines.push('# ============================================================================');
  lines.push(`# Total collectors: ${totalCollectors} (${Object.keys(techTrendsCollectors).length} tech + ${Object.keys(researchPapersCollectors).length} papers + ${Object.keys(jobsCollectors).length} jobs + ${Object.keys(organizationsCollectors).length} orgs + ${Object.keys(fundingCollectors).length} funding + ${Object.keys(developerToolsCollectors).length} devtools + ${Object.keys(techConferencesCollectors).length} conf)`);
  lines.push(`# Unique schedules: ${bySchedule.size}`);
  lines.push('# ============================================================================');

  return lines.join('\n');
}

// ============================================================================
// INSTALL CRONTAB
// ============================================================================

function installCrontab(crontabContent: string): void {
  const tmpFile = '/tmp/sofia-pulse-crontab.txt';

  try {
    // Write to temp file
    fs.writeFileSync(tmpFile, crontabContent);

    // Backup existing crontab
    try {
      const existing = execSync('crontab -l', { encoding: 'utf-8' });
      const backupFile = path.join(process.cwd(), 'crontab-backup-' + Date.now() + '.txt');
      fs.writeFileSync(backupFile, existing);
      console.log(`✅ Backed up existing crontab to: ${backupFile}`);
    } catch (error) {
      console.log('ℹ️  No existing crontab to backup');
    }

    // Install new crontab
    execSync(`crontab ${tmpFile}`);
    console.log('✅ Crontab installed successfully!');

    // Give execute permissions to scripts (IMPORTANT!)
    try {
      execSync('chmod +x scripts/collect.ts scripts/generate-crontab.ts scripts/collectors/*.ts scripts/shared/*.ts scripts/configs/*.ts', { cwd: process.cwd() });
      console.log('✅ Execute permissions granted to scripts');
    } catch (error) {
      console.warn('⚠️  Warning: Could not set execute permissions (may not be needed)');
    }

    console.log('');
    console.log('Verify with: crontab -l');

    // Cleanup
    fs.unlinkSync(tmpFile);

  } catch (error: any) {
    console.error('❌ Failed to install crontab:', error.message);
    process.exit(1);
  }
}

// ============================================================================
// STATISTICS
// ============================================================================

function showStatistics(): void {
  const schedules = new Map<string, number>();

  // Count all collectors
  Object.values(techTrendsCollectors).forEach(config => {
    if (!config.schedule) return;
    schedules.set(config.schedule, (schedules.get(config.schedule) || 0) + 1);
  });

  Object.values(researchPapersCollectors).forEach(config => {
    if (!config.schedule) return;
    schedules.set(config.schedule, (schedules.get(config.schedule) || 0) + 1);
  });

  Object.values(jobsCollectors).forEach(config => {
    if (!config.schedule) return;
    schedules.set(config.schedule, (schedules.get(config.schedule) || 0) + 1);
  });

  Object.values(organizationsCollectors).forEach(config => {
    if (!config.schedule) return;
    schedules.set(config.schedule, (schedules.get(config.schedule) || 0) + 1);
  });

  Object.values(fundingCollectors).forEach(config => {
    if (!config.schedule) return;
    schedules.set(config.schedule, (schedules.get(config.schedule) || 0) + 1);
  });

  Object.values(developerToolsCollectors).forEach(config => {
    if (!config.schedule) return;
    schedules.set(config.schedule, (schedules.get(config.schedule) || 0) + 1);
  });

  Object.values(techConferencesCollectors).forEach(config => {
    if (!config.schedule) return;
    schedules.set(config.schedule, (schedules.get(config.schedule) || 0) + 1);
  });

  const totalCollectors = Object.keys(techTrendsCollectors).length +
                         Object.keys(researchPapersCollectors).length +
                         Object.keys(jobsCollectors).length +
                         Object.keys(organizationsCollectors).length +
                         Object.keys(fundingCollectors).length +
                         Object.keys(developerToolsCollectors).length +
                         Object.keys(techConferencesCollectors).length;

  console.log('');
  console.log('📊 Crontab Statistics');
  console.log('='.repeat(70));
  console.log('');
  console.log(`Total collectors: ${totalCollectors}`);
  console.log(`With schedule: ${Array.from(schedules.values()).reduce((a, b) => a + b, 0)}`);
  console.log(`Unique schedules: ${schedules.size}`);
  console.log('');
  console.log('Breakdown by frequency:');

  const byFrequency = new Map<string, string[]>();

  schedules.forEach((count, schedule) => {
    let freq = '';
    if (schedule.includes('*/12')) freq = '2x/day';
    else if (schedule.includes('*/6')) freq = '4x/day';
    else if (schedule.match(/0 \d+ \*/)) freq = '1x/day';
    else if (schedule.match(/0 \d+ \* \* 1/)) freq = '1x/week';
    else if (schedule.match(/0 \d+ 1 \*/)) freq = '1x/month';
    else freq = 'Custom';

    if (!byFrequency.has(freq)) byFrequency.set(freq, []);
    byFrequency.get(freq)!.push(`${count} collectors`);
  });

  byFrequency.forEach((items, freq) => {
    console.log(`  ${freq}: ${items.join(', ')}`);
  });

  console.log('');
}

// ============================================================================
// CLI
// ============================================================================

const args = process.argv.slice(2);

if (args.includes('--help') || args.includes('-h')) {
  console.log('');
  console.log('📅 Crontab Generator - Sofia Pulse');
  console.log('');
  console.log('Usage:');
  console.log('  npx tsx scripts/generate-crontab.ts              # Show crontab');
  console.log('  npx tsx scripts/generate-crontab.ts --install    # Install crontab');
  console.log('  npx tsx scripts/generate-crontab.ts --stats      # Show statistics');
  console.log('');
  process.exit(0);
}

const crontabContent = generateCrontab();

if (args.includes('--stats')) {
  showStatistics();
} else if (args.includes('--install')) {
  console.log('');
  console.log('📅 Installing crontab...');
  console.log('');
  installCrontab(crontabContent);
  showStatistics();
} else {
  // Just show the crontab
  console.log(crontabContent);
  console.log('');
  console.log('💡 To install: npx tsx scripts/generate-crontab.ts --install');
  console.log('');
}
