#!/usr/bin/env tsx

/**
 * Research Papers Collector - Sofia Pulse (UNIFIED VERSION)
 *
 * Usa a arquitetura unificada:
 * - 1 Engine: research-papers-collector.ts
 * - N Configs: research-papers-config.ts (arxiv, openalex, nih)
 * - 1 Inserter: research-papers-inserter.ts
 *
 * Features:
 * - Tabela unificada: sofia.research_papers
 * - AUTO-INSERT AUTHORS: Autores vão para sofia.persons
 * - Deduplicação automática via (source, source_id)
 * - Suporta múltiplas fontes: arxiv, openalex, nih
 *
 * Usage:
 *   npx tsx scripts/collect-research-papers.ts arxiv
 *   npx tsx scripts/collect-research-papers.ts openalex
 *   npx tsx scripts/collect-research-papers.ts --all
 *
 * Exemplo de cron:
 *   0 8 * * 1  cd /home/ubuntu/sofia-pulse && npx tsx scripts/collect-research-papers.ts --all
 */

import { ResearchPapersCollector, runPapersCLI } from './collectors/research-papers-collector.js';
import { researchPapersCollectors } from './configs/research-papers-config.js';

// ============================================================================
// MAIN
// ============================================================================

if (require.main === module) {
  runPapersCLI(researchPapersCollectors);
}
