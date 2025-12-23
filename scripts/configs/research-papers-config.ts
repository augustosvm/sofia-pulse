/**
 * Research Papers Collectors Configuration - V2 (UNIFIED TABLE)
 *
 * UPDATED: Uses consolidated sofia.research_papers table
 * Replaces: arxiv_ai_papers, openalex_papers, bdtd_theses
 *
 * Configurações para collectors de papers acadêmicos:
 * - ArXiv AI/ML Papers
 * - OpenAlex Research Papers
 * - NIH Grants
 *
 * Schedule format (cron):
 *   '0 8 * * 1'     = Toda segunda às 8h (papers não mudam rápido)
 *   '0 8 1 * *'     = Primeiro dia do mês às 8h
 */

import { ResearchPapersConfig, PaperData } from '../collectors/research-papers-collector.js';

// ============================================================================
// ARXIV AI/ML PAPERS
// ============================================================================

export const arxivAIPapers: ResearchPapersConfig = {
  name: 'arxiv',
  displayName: '🤖 ArXiv AI/ML Papers',
  description: 'Papers de IA/ML antes de journals - GPT, BERT, Transformers aparecem aqui PRIMEIRO',

  url: 'http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CV+OR+cat:cs.CL+OR+cat:cs.RO&sortBy=submittedDate&sortOrder=descending&max_results=1000',

  rateLimit: 3000, // ArXiv recomenda 3s entre requests

  parseResponse: async (data: string) => {
    const papers: PaperData[] = [];

    // Parse XML (ArXiv retorna XML)
    const entries = data.match(/<entry>([\s\S]*?)<\/entry>/g) || [];

    for (const entry of entries) {
      // Extract fields with regex (simples, produção usaria xml2js)
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
      const categories = catMatches.map(c => c.match(/term="(.*?)"/)?.[1] || '');

      // Primary category (first one)
      const primary_category = categories[0] || 'cs.AI';

      // PDF URL
      const pdf_url = `https://arxiv.org/pdf/${arxiv_id}.pdf`;

      // Extract keywords (simplified)
      const text = `${title} ${abstract}`.toLowerCase();
      const keywords: string[] = [];

      if (text.match(/\b(gpt|llm|large language model|transformer)\b/)) keywords.push('LLM');
      if (text.match(/\b(diffusion|stable diffusion)\b/)) keywords.push('Diffusion Models');
      if (text.match(/\b(bert|roberta)\b/)) keywords.push('BERT Family');
      if (text.match(/\b(reinforcement learning|rl)\b/)) keywords.push('Reinforcement Learning');
      if (text.match(/\b(multimodal|clip)\b/)) keywords.push('Multimodal');

      // Breakthrough detection (simplified)
      const breakthroughIndicators = [
        /\b(state-of-the-art|sota|outperform)\b/,
        /\b(novel|new|first|breakthrough)\b/,
      ];
      const is_breakthrough = breakthroughIndicators.filter(r => r.test(text)).length >= 2;

      papers.push({
        source: 'arxiv', // UPDATED: unified table
        source_id: arxiv_id,
        title,
        authors,
        published_date: published,
        data: {
          arxiv_id,
          title,
          authors,
          categories,
          abstract,
          published_date: published,
          updated_date: updated || null,
          pdf_url,
          primary_category,
          keywords,
          is_breakthrough,
        },
      });
    }

    return papers;
  },

  schedule: '0 8 * * 1', // 1x/semana (segunda-feira 8h) - papers não mudam tanto
  allowWithoutAuth: true,
};

// ============================================================================
// OPENALEX RESEARCH PAPERS
// ============================================================================

export const openAlexPapers: ResearchPapersConfig = {
  name: 'openalex',
  displayName: '📚 OpenAlex Research Papers',
  description: '250M+ papers, 100% FREE - Substitui Microsoft Academic',

  // Busca top cited papers recentes em AI/ML/Biotech
  url: 'https://api.openalex.org/works?filter=concepts.id:C154945302|C119857082,from_publication_date:2023-01-01&sort=cited_by_count:desc&per-page=200&mailto=augustosvm@gmail.com',

  rateLimit: 1000, // OpenAlex permite 10 req/s, usamos 1/s para ser gentil

  parseResponse: async (data: any) => {
    const papers: PaperData[] = [];
    const results = data.results || [];

    for (const work of results) {
      // Extract authors
      const authors = (work.authorships || [])
        .slice(0, 10)
        .map((a: any) => a.author?.display_name || 'Unknown')
        .filter((n: string) => n !== 'Unknown');

      // Extract institutions
      const institutions = (work.authorships || [])
        .flatMap((a: any) => (a.institutions || []).map((i: any) => i.display_name))
        .filter((i: string) => i)
        .slice(0, 5);

      // Extract countries
      const countries = (work.authorships || [])
        .flatMap((a: any) => (a.institutions || []).map((i: any) => i.country_code))
        .filter((c: string) => c)
        .slice(0, 5);

      // Extract concepts
      const concepts = (work.concepts || [])
        .slice(0, 8)
        .map((c: any) => c.display_name);

      const primary_concept = work.concepts?.[0]?.display_name || 'Unknown';

      // Publication date
      const pubDate = work.publication_date || '';
      const pubYear = work.publication_year || parseInt(pubDate.split('-')[0]) || 2024;

      const openalex_id = work.id?.replace('https://openalex.org/', '') || '';
      const doi = work.doi?.replace('https://doi.org/', '') || null;

      papers.push({
        source: 'openalex', // UPDATED: unified table
        source_id: openalex_id,
        title: work.title || '',
        authors: authors.length > 0 ? authors : ['Unknown'],
        published_date: pubDate,
        data: {
          openalex_id,
          doi,
          title: work.title || '',
          publication_date: pubDate,
          publication_year: pubYear,
          authors,
          author_institutions: institutions.length > 0 ? institutions : null,
          author_countries: countries.length > 0 ? countries : null,
          concepts: concepts.length > 0 ? concepts : ['Unknown'],
          primary_concept,
          cited_by_count: work.cited_by_count || 0,
          referenced_works_count: work.referenced_works_count || 0,
          is_open_access: work.open_access?.is_oa || false,
          journal: work.primary_location?.source?.display_name || null,
          publisher: work.primary_location?.source?.host_organization_name || null,
          abstract: work.abstract || null,
        },
      });
    }

    return papers;
  },

  schedule: '0 8 * * 1', // 1x/semana (segunda-feira 8h)
  allowWithoutAuth: true,
};

// ============================================================================
// NIH GRANTS (placeholder - precisa de API key)
// ============================================================================

export const nihGrants: ResearchPapersConfig = {
  name: 'nih',
  displayName: '🏥 NIH Research Grants',
  description: 'Grants de pesquisa biomédica - prediz tendências antes de startups',

  // NIH Reporter API (exemplo)
  url: 'https://api.reporter.nih.gov/v2/projects/search',

  headers: {
    'Content-Type': 'application/json',
  },

  rateLimit: 2000, // 2s entre requests

  parseResponse: async (data: any) => {
    // TODO: Implementar quando tiver acesso à API
    // Por enquanto retorna vazio
    return [];
  },

  schedule: '0 8 1 * *', // 1x/mês (dia 1 às 8h) - grants mudam devagar
  allowWithoutAuth: false, // Precisa de configuração
};

// ============================================================================
// EXPORTS
// ============================================================================

/**
 * Registry de todos os research papers collectors
 */
export const researchPapersCollectors: Record<string, ResearchPapersConfig> = {
  arxiv: arxivAIPapers,
  openalex: openAlexPapers,
  // nih: nihGrants, // Comentado até implementar
};

/**
 * Filtra collectors por schedule
 */
export function getPapersCollectorsBySchedule(schedule: string): ResearchPapersConfig[] {
  return Object.values(researchPapersCollectors).filter(c => c.schedule === schedule);
}
