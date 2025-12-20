#!/usr/bin/env tsx
/**
 * Collector Entry Point - Sofia Pulse
 *
 * Suporta múltiplos tipos de collectors:
 * - Tech Trends (GitHub, NPM, PyPI, HackerNews)
 * - Research Papers (ArXiv, OpenAlex, NIH)
 * - Jobs (Himalayas, RemoteOK, Arbeitnow)
 * - Organizations (AI Companies, Universities, NGOs)
 * - Funding (Crunchbase, YC) - futuro
 *
 * Usage:
 *   npx tsx scripts/collect.ts github              # Tech trend
 *   npx tsx scripts/collect.ts arxiv               # Research paper
 *   npx tsx scripts/collect.ts himalayas           # Jobs
 *   npx tsx scripts/collect.ts ai-companies        # Organizations
 *   npx tsx scripts/collect.ts --all               # Todos tech trends
 *   npx tsx scripts/collect.ts --all-papers        # Todos papers
 *   npx tsx scripts/collect.ts --all-jobs          # Todos jobs
 *   npx tsx scripts/collect.ts --all-organizations # Todas organizações
 *   npx tsx scripts/collect.ts --help
 */

import { runCLI as runTechTrendsCLI } from './collectors/tech-trends-collector.js';
import { runPapersCLI as runResearchPapersCLI } from './collectors/research-papers-collector.js';
import { runJobsCLI } from './collectors/jobs-collector.js';
import { runOrganizationsCLI } from './collectors/organizations-collector.js';
import { collectors as techTrendsCollectors } from './configs/tech-trends-config.js';
import { researchPapersCollectors } from './configs/research-papers-config.js';
import { jobsCollectors } from './configs/jobs-config.js';
import { organizationsCollectors } from './configs/organizations-config.js';

// ============================================================================
// UNIFIED CLI
// ============================================================================

async function main() {
  const args = process.argv.slice(2);

  // Help
  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    showHelp();
    process.exit(0);
  }

  // Detectar tipo de collector baseado no nome ou flag
  const collectorName = args[0];

  // Flags especiais
  if (collectorName === '--all') {
    // Roda todos tech trends
    await runTechTrendsCLI(techTrendsCollectors);
    return;
  }

  if (collectorName === '--all-papers') {
    // Roda todos research papers
    await runResearchPapersCLI(researchPapersCollectors);
    return;
  }

  if (collectorName === '--all-jobs') {
    // Roda todos jobs
    await runJobsCLI(jobsCollectors);
    return;
  }

  if (collectorName === '--all-organizations') {
    // Roda todas organizações
    await runOrganizationsCLI(organizationsCollectors);
    return;
  }

  // Verifica se é tech trends collector
  if (collectorName in techTrendsCollectors) {
    await runTechTrendsCLI(techTrendsCollectors);
    return;
  }

  // Verifica se é research papers collector
  if (collectorName in researchPapersCollectors) {
    await runResearchPapersCLI(researchPapersCollectors);
    return;
  }

  // Verifica se é jobs collector
  if (collectorName in jobsCollectors) {
    await runJobsCLI(jobsCollectors);
    return;
  }

  // Verifica se é organizations collector
  if (collectorName in organizationsCollectors) {
    await runOrganizationsCLI(organizationsCollectors);
    return;
  }

  // Collector não encontrado
  console.error(`❌ Unknown collector: ${collectorName}`);
  console.error('');
  showHelp();
  process.exit(1);
}

function showHelp() {
  console.log('');
  console.log('📡 Sofia Pulse - Unified Collector System');
  console.log('');
  console.log('Usage:');
  console.log('  npx tsx scripts/collect.ts <collector>');
  console.log('  npx tsx scripts/collect.ts --all                # All tech trends');
  console.log('  npx tsx scripts/collect.ts --all-papers         # All research papers');
  console.log('  npx tsx scripts/collect.ts --all-jobs           # All jobs');
  console.log('  npx tsx scripts/collect.ts --all-organizations  # All organizations');
  console.log('');
  console.log('📊 Tech Trends Collectors:');
  Object.entries(techTrendsCollectors).forEach(([name, config]) => {
    console.log(`  ${name.padEnd(20)} - ${config.description || config.displayName}`);
  });
  console.log('');
  console.log('📚 Research Papers Collectors:');
  Object.entries(researchPapersCollectors).forEach(([name, config]) => {
    console.log(`  ${name.padEnd(20)} - ${config.description || config.displayName}`);
  });
  console.log('');
  console.log('💼 Jobs Collectors:');
  Object.entries(jobsCollectors).forEach(([name, config]) => {
    console.log(`  ${name.padEnd(20)} - ${config.description || config.displayName}`);
  });
  console.log('');
  console.log('🏢 Organizations Collectors:');
  Object.entries(organizationsCollectors).forEach(([name, config]) => {
    console.log(`  ${name.padEnd(20)} - ${config.description || config.displayName}`);
  });
  console.log('');
  console.log('Examples:');
  console.log('  npx tsx scripts/collect.ts github              # Collect GitHub trending');
  console.log('  npx tsx scripts/collect.ts arxiv               # Collect ArXiv papers');
  console.log('  npx tsx scripts/collect.ts himalayas           # Collect Himalayas jobs');
  console.log('  npx tsx scripts/collect.ts ai-companies        # Collect AI Companies');
  console.log('  npx tsx scripts/collect.ts --all               # All tech trends');
  console.log('  npx tsx scripts/collect.ts --all-organizations # All organizations');
  console.log('');
}

// Run
main().catch((error) => {
  console.error('❌ Fatal error:', error.message);
  process.exit(1);
});
