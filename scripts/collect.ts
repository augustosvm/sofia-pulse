#!/usr/bin/env tsx
/**
 * Collector Entry Point - Sofia Pulse
 *
 * Suporta múltiplos tipos de collectors:
 * - Tech Trends (GitHub, NPM, PyPI, HackerNews)
 * - Research Papers (ArXiv, OpenAlex, NIH)
 * - Jobs (Himalayas, RemoteOK, Arbeitnow)
 * - Organizations (AI Companies, Universities, NGOs)
 * - Funding (YC, Product Hunt, SEC Edgar)
 * - Developer Tools (VS Code, JetBrains Marketplace)
 * - Tech Conferences (Confs.tech, Meetup.com)
 * - Brazil Data (MDIC, FIESP)
 * - Industry Signals (NVD, CISA, Space, GDELT)
 * - Legacy Python Collectors (Bridge)
 *
 * Usage:
 *   npx tsx scripts/collect.ts github              # Tech trend
 *   npx tsx scripts/collect.ts arxiv               # Research paper
 *   npx tsx scripts/collect.ts himalayas           # Jobs
 *   npx tsx scripts/collect.ts ai-companies        # Organizations
 *   npx tsx scripts/collect.ts yc-companies        # Funding
 *   npx tsx scripts/collect.ts mdic-regional       # Brazil MDIC
 *   npx tsx scripts/collect.ts energy-global       # Legacy Python
 *   npx tsx scripts/collect.ts --all               # Todos os collectors
 *   npx tsx scripts/collect.ts --all-legacy        # Todos os legacy python
 *   npx tsx scripts/collect.ts --help
 */

import { runCLI as runTechTrendsCLI } from './collectors/tech-trends-collector.js';
import { runPapersCLI as runResearchPapersCLI } from './collectors/research-papers-collector.js';
import { runJobsCLI } from './collectors/jobs-collector.js';
import { runOrganizationsCLI } from './collectors/organizations-collector.js';
import { runFundingCLI } from './collectors/funding-collector.js';
import { runDeveloperToolsCLI } from './collectors/developer-tools-collector.js';
import { runTechConferencesCLI } from './collectors/tech-conferences-collector.js';
import { runBrazilCLI } from './collectors/brazil-collector.js';
import { runIndustrySignalsCLI } from './collectors/industry-signals-collector.js';
import { runPythonBridgeCLI } from './collectors/python-bridge-collector.js';
import { NGOsCollector } from './collectors/ngos-collector.js';
import { collectGreenhouseJobs } from './collect-greenhouse-jobs.js';
import { collectCathoJobs } from './collect-catho-final.js';
import { collectCurrencyRates } from './collect-currency-rates.js';
import { collectEPOPatents } from './collect-epo-patents.js';
import { collectGitGuardianIncidents } from './collect-gitguardian-incidents.js';
import { collectHKEXipos } from './collect-hkex-ipos.js';
import { collectWIPOPatents } from './collect-wipo-china-patents.js';

import { collectors as techTrendsCollectors } from './configs/tech-trends-config.js';
import { researchPapersCollectors } from './configs/research-papers-config.js';
import { jobsCollectors } from './configs/jobs-config.js';
import { organizationsCollectors } from './configs/organizations-config.js';
import { fundingCollectors } from './configs/funding-config.js';
import { developerToolsCollectors } from './configs/developer-tools-config.js';
import { techConferencesCollectors } from './configs/tech-conferences-config.js';
import { collectors as brazilCollectors } from './configs/brazil-config.js';
import { collectors as industrySignalsCollectors } from './configs/industry-signals-config.js';
import * as legacyConfig from './configs/legacy-python-config.js';

const legacyPythonCollectors = legacyConfig.collectors || {};
console.log(`🐍 Legacy Python Collectors Loaded: ${Object.keys(legacyPythonCollectors).length}`);


async function main() {
  const args = process.argv.slice(2);

  // Help
  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    showHelp();
    process.exit(0);
  }

  // Detectar tipo de collector baseado no nome ou flag
  const collectorName = args[0];

  try {
    // Flags especiais
    if (collectorName === '--all') {
      console.log('🚀 Running ALL collectors...');
      await runTechTrendsCLI(techTrendsCollectors);
      await runResearchPapersCLI(researchPapersCollectors);
      await runJobsCLI(jobsCollectors);
      await runOrganizationsCLI(organizationsCollectors);
      await runFundingCLI(fundingCollectors);
      await runDeveloperToolsCLI(developerToolsCollectors);
      await runTechConferencesCLI(techConferencesCollectors);
      await runBrazilCLI(brazilCollectors);
      await runIndustrySignalsCLI(industrySignalsCollectors);
      await runPythonBridgeCLI(legacyPythonCollectors);
      return;
    }

    if (collectorName === '--all-papers') {
      await runResearchPapersCLI(researchPapersCollectors);
      return;
    }

    if (collectorName === '--all-jobs') {
      await runJobsCLI(jobsCollectors);
      return;
    }

    if (collectorName === '--all-organizations') {
      await runOrganizationsCLI(organizationsCollectors);
      return;
    }

    if (collectorName === '--all-funding') {
      await runFundingCLI(fundingCollectors);
      return;
    }

    if (collectorName === '--all-developer-tools') {
      await runDeveloperToolsCLI(developerToolsCollectors);
      return;
    }

    if (collectorName === '--all-conferences') {
      await runTechConferencesCLI(techConferencesCollectors);
      return;
    }

    if (collectorName === '--all-brazil') {
      await runBrazilCLI(brazilCollectors);
      return;
    }

    if (collectorName === '--all-legacy') {
      await runPythonBridgeCLI(legacyPythonCollectors);
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

    // Special case: NGOs (standalone bulk download collector)
    if (collectorName === 'ngos') {
      const collector = new NGOsCollector();
      try {
        const result = await collector.collect();
        if (!result.success || result.saved === 0) {
          process.exit(1);
        }
        process.exit(0);
      } finally {
        await collector.close();
      }
      return;
    }

    // Verifica se é organizations collector
    if (collectorName in organizationsCollectors) {
      await runOrganizationsCLI(organizationsCollectors);
      return;
    }

    // Verifica se é funding collector
    if (collectorName in fundingCollectors) {
      await runFundingCLI(fundingCollectors);
      return;
    }

    // Verifica se é developer tools collector
    if (collectorName in developerToolsCollectors) {
      await runDeveloperToolsCLI(developerToolsCollectors);
      return;
    }

    // Verifica se é tech conferences collector
    if (collectorName in techConferencesCollectors) {
      await runTechConferencesCLI(techConferencesCollectors);
      return;
    }

    // Verifica se é Brazil collector
    if (collectorName in brazilCollectors) {
      await runBrazilCLI(brazilCollectors);
      return;
    }

    // Verifica se é Industry Signals collector
    if (collectorName in industrySignalsCollectors) {
      await runIndustrySignalsCLI(industrySignalsCollectors);
      return;
    }

    // Verifica se é Legacy Python Collector
    if (collectorName in legacyPythonCollectors) {
      await runPythonBridgeCLI(legacyPythonCollectors);
      return;
    }

    // Special case: Greenhouse (standalone collector)
    if (collectorName === 'greenhouse') {
      await collectGreenhouseJobs();
      return;
    }

    // Special case: Catho (standalone collector)
    if (collectorName === 'catho' || collectorName === 'catho-final') {
      await collectCathoJobs();
      return;
    }

    // Special case: Currency Rates (economic data collector)
    if (collectorName === 'currency-rates') {
      await collectCurrencyRates();
      return;
    }

    // Special case: EPO Patents (European Patent Office)
    if (collectorName === 'epo-patents') {
      await collectEPOPatents();
      return;
    }

    // Special case: GitGuardian Incidents (Security)
    if (collectorName === 'gitguardian-incidents') {
      await collectGitGuardianIncidents();
      return;
    }

    // Special case: HKEX IPOs (Hong Kong Stock Exchange)
    if (collectorName === 'hkex-ipos') {
      await collectHKEXipos();
      return;
    }

    // Special case: WIPO China Patents (World Intellectual Property Org)
    if (collectorName === 'wipo-china-patents') {
      await collectWIPOPatents();
      return;
    }

    // Collector não encontrado
    console.error(`❌ Unknown collector: ${collectorName}`);
    console.error('');
    showHelp();
    process.exit(1);


  } catch (err) {
    console.error('❌ Critical Error:', err);
    process.exit(1);
  }
}

function showHelp() {
  console.log('');
  console.log('📡 Sofia Pulse - Unified Collector System');
  console.log('');
  console.log('Usage:');
  console.log('  npx tsx scripts/collect.ts <collector>');
  console.log('  npx tsx scripts/collect.ts --all                 # All collectors');
  console.log('  npx tsx scripts/collect.ts --all-papers          # All research papers');
  console.log('  npx tsx scripts/collect.ts --all-jobs            # All jobs');
  console.log('  npx tsx scripts/collect.ts --all-organizations   # All organizations');
  console.log('  npx tsx scripts/collect.ts --all-funding         # All funding');
  console.log('  npx tsx scripts/collect.ts --all-developer-tools # All developer tools');
  console.log('  npx tsx scripts/collect.ts --all-conferences     # All conferences');
  console.log('  npx tsx scripts/collect.ts --all-brazil          # All Brazil data');
  console.log('  npx tsx scripts/collect.ts --all-legacy          # All Legacy Python');
  console.log('');

  const printCollectors = (title: string, collection: Record<string, any>) => {
    console.log(`${title}:`);
    Object.entries(collection).forEach(([name, config]) => {
      console.log(`  ${name.padEnd(30)} - ${config.description || config.displayName}`);
    });
    console.log('');
  };

  printCollectors('📊 Tech Trends Collectors', techTrendsCollectors);
  printCollectors('📚 Research Papers Collectors', researchPapersCollectors);
  printCollectors('💼 Jobs Collectors', jobsCollectors);
  printCollectors('🏢 Organizations Collectors', organizationsCollectors);
  printCollectors('💰 Funding Collectors', fundingCollectors);
  printCollectors('🔧 Developer Tools Collectors', developerToolsCollectors);
  printCollectors('🎤 Tech Conferences Collectors', techConferencesCollectors);
  printCollectors('🇧🇷 Brazil Data Collectors', brazilCollectors);
  printCollectors('📡 Industry Signals Collectors', industrySignalsCollectors);
  printCollectors('🐍 Legacy Python Collectors (Bridge)', legacyPythonCollectors);

  console.log('Examples:');
  console.log('  npx tsx scripts/collect.ts github              # Collect GitHub trending');
  console.log('  npx tsx scripts/collect.ts energy-global       # Collect Global Energy');
  console.log('');
}

// Run
main().catch((error) => {
  console.error('❌ Fatal error:', error.message);
  process.exit(1);
});
