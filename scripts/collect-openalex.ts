#!/usr/bin/env tsx

// Fix for Node.js 18 + undici - MUST BE AFTER SHEBANG!
// @ts-ignore
if (typeof File === 'undefined') {
  // @ts-ignore
  globalThis.File = class File extends Blob {
    constructor(bits: any[], name: string, options?: any) {
      super(bits, options);
    }
  };
}


/**
 * Sofia Pulse - OpenAlex Research Papers Collector
 *
 * Coleta papers de TODAS as áreas da OpenAlex (250M+ papers!)
 *
 * POR QUE OPENALEX É A MELHOR FONTE:
 * - 250M+ papers (vs ArXiv ~2M, PubMed ~35M)
 * - 100% GRATUITO, SEM LIMITES! 🎉
 * - Substitui Microsoft Academic (descontinuado)
 * - Cobertura: TUDO - STEM, medicina, ciências sociais
 * - Metadata rica: autores, instituições, citações, conceitos AI
 * - API super rápida e confiável
 *
 * CATEGORIAS MONITORADAS:
 * - AI & Machine Learning
 * - Biotechnology & Medicine
 * - Physics & Engineering
 * - Chemistry & Materials
 * - ALL FIELDS disponíveis
 */

import { Client } from 'pg';
import * as dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

// ============================================================================
// DATABASE SETUP
// ============================================================================

const dbConfig = {
  host: process.env.POSTGRES_HOST || process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || process.env.DB_PORT || '5432'),
  user: process.env.POSTGRES_USER || process.env.DB_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || process.env.DB_PASSWORD || 'postgres',
  database: process.env.POSTGRES_DB || process.env.DB_NAME || 'sofia_db',
};

// ============================================================================
// TYPES
// ============================================================================

interface OpenAlexPaper {
  openalex_id: string; // W1234567890
  doi?: string;
  title: string;
  publication_date: string;
  publication_year: number;
  authors: string[]; // Author names
  author_institutions: string[]; // Institution names
  author_countries: string[]; // Countries
  concepts: string[]; // AI-generated topics
  primary_concept: string;
  cited_by_count: number;
  referenced_works_count: number;
  is_open_access: boolean;
  journal?: string;
  publisher?: string;
  abstract?: string;
}

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

async function createTableIfNotExists(client: Client): Promise<void> {
  const createTableQuery = `
    CREATE TABLE IF NOT EXISTS openalex_papers (
      id SERIAL PRIMARY KEY,
      openalex_id VARCHAR(50) UNIQUE,
      doi VARCHAR(100),
      title TEXT NOT NULL,
      publication_date DATE,
      publication_year INT,
      authors TEXT[],
      author_institutions TEXT[],
      author_countries TEXT[],
      concepts TEXT[],
      primary_concept VARCHAR(255),
      cited_by_count INT DEFAULT 0,
      referenced_works_count INT DEFAULT 0,
      is_open_access BOOLEAN,
      journal VARCHAR(500),
      publisher VARCHAR(255),
      abstract TEXT,
      collected_at TIMESTAMP DEFAULT NOW()
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_openalex_pub_year
      ON openalex_papers(publication_year DESC);

    CREATE INDEX IF NOT EXISTS idx_openalex_cited_by
      ON openalex_papers(cited_by_count DESC);

    CREATE INDEX IF NOT EXISTS idx_openalex_concepts
      ON openalex_papers USING GIN(concepts);

    CREATE INDEX IF NOT EXISTS idx_openalex_countries
      ON openalex_papers USING GIN(author_countries);

    CREATE INDEX IF NOT EXISTS idx_openalex_primary_concept
      ON openalex_papers(primary_concept);
  `;

  await client.query(createTableQuery);
  console.log('✅ Table openalex_papers ready');
}

async function insertPaper(client: Client, paper: OpenAlexPaper): Promise<void> {
  const insertQuery = `
    INSERT INTO openalex_papers (
      openalex_id, doi, title, publication_date, publication_year,
      authors, author_institutions, author_countries,
      concepts, primary_concept, cited_by_count, referenced_works_count,
      is_open_access, journal, publisher, abstract
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
    ON CONFLICT (openalex_id)
    DO UPDATE SET
      cited_by_count = EXCLUDED.cited_by_count,
      collected_at = NOW();
  `;

  await client.query(insertQuery, [
    paper.openalex_id,
    paper.doi || null,
    paper.title,
    paper.publication_date,
    paper.publication_year,
    paper.authors,
    paper.author_institutions,
    paper.author_countries,
    paper.concepts,
    paper.primary_concept,
    paper.cited_by_count,
    paper.referenced_works_count,
    paper.is_open_access,
    paper.journal || null,
    paper.publisher || null,
    paper.abstract || null,
  ]);
}

// ============================================================================
// COLLECTORS
// ============================================================================

/**
 * Coleta papers REAIS do OpenAlex API (GRATUITA!)
 * API: https://api.openalex.org/works
 * Docs: https://docs.openalex.org
 *
 * Conceitos buscados:
 * - Artificial Intelligence
 * - Machine Learning
 * - Deep Learning
 * - Natural Language Processing
 * - Biotechnology
 */
async function collectOpenAlex(): Promise<OpenAlexPaper[]> {
  console.log('📚 Collecting OpenAlex papers from REAL API...');

  const papers: OpenAlexPaper[] = [];

  // Conceitos para buscar (IDs do OpenAlex)
  const concepts = [
    { id: 'C154945302', name: 'Artificial Intelligence' },
    { id: 'C119857082', name: 'Machine Learning' },
    { id: 'C204787440', name: 'Deep Learning' },
    { id: 'C41008148', name: 'Computer Science' },
    { id: 'C17744445', name: 'Biotechnology' },
  ];

  for (const concept of concepts) {
    try {
      // OpenAlex API - top cited papers from last year
      const url = `https://api.openalex.org/works?filter=concepts.id:${concept.id},from_publication_date:2023-01-01&sort=cited_by_count:desc&per-page=20&mailto=augustosvm@gmail.com`;

      console.log(`   Fetching ${concept.name}...`);

      const response = await axios.get(url);
      const results = response.data.results || [];

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
        const conceptsList = (work.concepts || [])
          .slice(0, 8)
          .map((c: any) => c.display_name);

        // Primary concept
        const primaryConcept = work.concepts?.[0]?.display_name || concept.name;

        // Publication date
        const pubDate = work.publication_date || '';
        const pubYear = work.publication_year || parseInt(pubDate.split('-')[0]) || 2024;

        papers.push({
          openalex_id: work.id?.replace('https://openalex.org/', '') || '',
          doi: work.doi?.replace('https://doi.org/', '') || null,
          title: work.title || '',
          publication_date: pubDate,
          publication_year: pubYear,
          authors: authors.length > 0 ? authors : ['Unknown'],
          author_institutions: institutions.length > 0 ? institutions : null,
          author_countries: countries.length > 0 ? countries : null,
          concepts: conceptsList.length > 0 ? conceptsList : [concept.name],
          primary_concept: primaryConcept,
          cited_by_count: work.cited_by_count || 0,
          referenced_works_count: work.referenced_works_count || 0,
          is_open_access: work.open_access?.is_oa || false,
          journal: work.primary_location?.source?.display_name || null,
          publisher: work.primary_location?.source?.host_organization_name || null,
          abstract: work.abstract || null,
        });
      }

      console.log(`   ✅ ${results.length} papers from ${concept.name}`);

      // Rate limit: 10 requests per second (safe: 1 per second)
      await new Promise(resolve => setTimeout(resolve, 1000));

    } catch (error) {
      console.log(`   ⚠️  Error fetching ${concept.name}:`, error);
    }
  }

  console.log(`   ✅ Total: ${papers.length} papers collected`);

  return papers;
}

/**
 * FALLBACK: Mock data case API falhar
 */
async function collectOpenAlex_MOCK(): Promise<OpenAlexPaper[]> {
  console.log('📚 Using MOCK data (API unavailable)...');

  // Mock papers cobrindo várias áreas
  const mockPapers: OpenAlexPaper[] = [
    // AI & Machine Learning
    {
      openalex_id: 'W4385820562',
      doi: '10.1038/s41586-024-07234-5',
      title: 'Attention Is All You Need: Transformers for Sequence-to-Sequence Learning',
      publication_date: '2024-06-15',
      publication_year: 2024,
      authors: ['Vaswani Ashish', 'Shazeer Noam', 'Parmar Niki'],
      author_institutions: ['Google Brain', 'Google Research'],
      author_countries: ['USA'],
      concepts: ['Artificial Intelligence', 'Machine Learning', 'Natural Language Processing', 'Transformers'],
      primary_concept: 'Artificial Intelligence',
      cited_by_count: 95432,
      referenced_works_count: 48,
      is_open_access: true,
      journal: 'Nature',
      publisher: 'Springer Nature',
      abstract: 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...',
    },
    {
      openalex_id: 'W4385820563',
      doi: '10.1126/science.abi5432',
      title: 'AlphaFold: Highly Accurate Protein Structure Prediction with Deep Learning',
      publication_date: '2024-05-20',
      publication_year: 2024,
      authors: ['Jumper John', 'Evans Richard', 'Hassabis Demis'],
      author_institutions: ['DeepMind', 'Google'],
      author_countries: ['UK', 'USA'],
      concepts: ['Protein Folding', 'Deep Learning', 'Structural Biology', 'AI Drug Discovery'],
      primary_concept: 'Protein Folding',
      cited_by_count: 12845,
      referenced_works_count: 125,
      is_open_access: false,
      journal: 'Science',
      publisher: 'AAAS',
      abstract: 'Predicting protein structure from amino acid sequence is a grand challenge...',
    },

    // Biotechnology
    {
      openalex_id: 'W4385820564',
      doi: '10.1056/NEJMoa2024671',
      title: 'Safety and Efficacy of the BNT162b2 mRNA COVID-19 Vaccine',
      publication_date: '2024-04-10',
      publication_year: 2024,
      authors: ['Polack Fernando', 'Thomas Stephen', 'Sahin Ugur'],
      author_institutions: ['Pfizer', 'BioNTech', 'University of Pennsylvania'],
      author_countries: ['USA', 'Germany'],
      concepts: ['mRNA Vaccines', 'COVID-19', 'Immunology', 'Clinical Trials'],
      primary_concept: 'mRNA Vaccines',
      cited_by_count: 28734,
      referenced_works_count: 86,
      is_open_access: false,
      journal: 'New England Journal of Medicine',
      publisher: 'Massachusetts Medical Society',
      abstract: 'Severe acute respiratory syndrome coronavirus 2 (SARS-CoV-2) infection...',
    },
    {
      openalex_id: 'W4385820565',
      doi: '10.1038/s41591-024-02856-4',
      title: 'CRISPR-Cas9 Gene Editing for Sickle Cell Disease: A Phase 1/2 Trial',
      publication_date: '2024-03-28',
      publication_year: 2024,
      authors: ['Frangoul Haydar', 'Dever Daniel', 'Porteus Matthew'],
      author_institutions: ['Stanford Medicine', 'UCSF'],
      author_countries: ['USA'],
      concepts: ['CRISPR', 'Gene Therapy', 'Sickle Cell Disease', 'Hematology'],
      primary_concept: 'CRISPR',
      cited_by_count: 4521,
      referenced_works_count: 72,
      is_open_access: true,
      journal: 'Nature Medicine',
      publisher: 'Springer Nature',
      abstract: 'Sickle cell disease (SCD) is caused by a single nucleotide mutation...',
    },

    // Physics & Materials
    {
      openalex_id: 'W4385820566',
      doi: '10.1103/PhysRevLett.130.261001',
      title: 'Room-Temperature Superconductivity in Lutetium Hydride at Near-Ambient Pressure',
      publication_date: '2024-07-22',
      publication_year: 2024,
      authors: ['Dias Ranga', 'Salamat Ashkan'],
      author_institutions: ['University of Rochester', 'University of Nevada Las Vegas'],
      author_countries: ['USA'],
      concepts: ['Superconductivity', 'Condensed Matter Physics', 'Materials Science'],
      primary_concept: 'Superconductivity',
      cited_by_count: 892,
      referenced_works_count: 54,
      is_open_access: false,
      journal: 'Physical Review Letters',
      publisher: 'American Physical Society',
      abstract: 'The search for room-temperature superconductors has been one of the most challenging problems...',
    },
    {
      openalex_id: 'W4385820567',
      doi: '10.1039/D4EE00234H',
      title: 'Perovskite Solar Cells Achieving 28% Power Conversion Efficiency',
      publication_date: '2024-08-05',
      publication_year: 2024,
      authors: ['Park Nam-Gyu', 'Grätzel Michael', 'Miyasaka Tsutomu'],
      author_institutions: ['EPFL', 'Toin University', 'Sungkyunkwan University'],
      author_countries: ['Switzerland', 'Japan', 'South Korea'],
      concepts: ['Perovskite', 'Solar Cells', 'Renewable Energy', 'Materials Science'],
      primary_concept: 'Perovskite',
      cited_by_count: 1245,
      referenced_works_count: 98,
      is_open_access: true,
      journal: 'Energy & Environmental Science',
      publisher: 'Royal Society of Chemistry',
      abstract: 'Perovskite solar cells have emerged as a promising photovoltaic technology...',
    },

    // Chemistry
    {
      openalex_id: 'W4385820568',
      doi: '10.1021/jacs.4c02341',
      title: 'Catalytic Conversion of CO2 to Methanol at Ambient Conditions',
      publication_date: '2024-09-12',
      publication_year: 2024,
      authors: ['Nørskov Jens', 'Jaramillo Thomas'],
      author_institutions: ['Stanford University', 'DTU Denmark'],
      author_countries: ['USA', 'Denmark'],
      concepts: ['Catalysis', 'CO2 Reduction', 'Green Chemistry', 'Sustainability'],
      primary_concept: 'Catalysis',
      cited_by_count: 634,
      referenced_works_count: 67,
      is_open_access: false,
      journal: 'Journal of the American Chemical Society',
      publisher: 'American Chemical Society',
      abstract: 'Converting CO2 to valuable chemicals is crucial for carbon neutrality...',
    },

    // Neuroscience
    {
      openalex_id: 'W4385820569',
      doi: '10.1038/s41593-024-01543-2',
      title: 'Brain-Computer Interfaces: Decoding Speech from Neural Activity',
      publication_date: '2024-10-01',
      publication_year: 2024,
      authors: ['Chang Edward', 'Chartier Josh'],
      author_institutions: ['UCSF', 'UC Berkeley'],
      author_countries: ['USA'],
      concepts: ['Brain-Computer Interface', 'Neuroscience', 'Machine Learning', 'Neural Decoding'],
      primary_concept: 'Brain-Computer Interface',
      cited_by_count: 423,
      referenced_works_count: 89,
      is_open_access: true,
      journal: 'Nature Neuroscience',
      publisher: 'Springer Nature',
      abstract: 'Brain-computer interfaces (BCIs) that decode speech from neural activity...',
    },

    // Climate Science
    {
      openalex_id: 'W4385820570',
      doi: '10.1038/s41558-024-01892-3',
      title: 'Global Temperature Increase of 1.5°C Reached in 2024',
      publication_date: '2024-11-15',
      publication_year: 2024,
      authors: ['Hansen James', 'Schmidt Gavin'],
      author_institutions: ['NASA GISS', 'Columbia University'],
      author_countries: ['USA'],
      concepts: ['Climate Change', 'Global Warming', 'Earth Sciences'],
      primary_concept: 'Climate Change',
      cited_by_count: 2145,
      referenced_works_count: 156,
      is_open_access: false,
      journal: 'Nature Climate Change',
      publisher: 'Springer Nature',
      abstract: 'Analysis of temperature records confirms that global mean surface temperature...',
    },

    // Quantum Computing
    {
      openalex_id: 'W4385820571',
      doi: '10.1038/s41586-024-07654-z',
      title: 'Quantum Error Correction Below the Surface Code Threshold',
      publication_date: '2024-12-01',
      publication_year: 2024,
      authors: ['Martinis John', 'Neven Hartmut'],
      author_institutions: ['Google Quantum AI'],
      author_countries: ['USA'],
      concepts: ['Quantum Computing', 'Quantum Error Correction', 'Physics'],
      primary_concept: 'Quantum Computing',
      cited_by_count: 745,
      referenced_works_count: 92,
      is_open_access: true,
      journal: 'Nature',
      publisher: 'Springer Nature',
      abstract: 'Quantum error correction is essential for building reliable quantum computers...',
    },
  ];

  return mockPapers;
}

// ============================================================================
// MAIN FUNCTION
// ============================================================================

async function main() {
  console.log('🚀 Sofia Pulse - OpenAlex Papers Collector');
  console.log('='.repeat(60));
  console.log('');
  console.log('📚 WHY OPENALEX IS THE BEST:');
  console.log('   - 250M+ papers (largest open database!)');
  console.log('   - 100% FREE, NO LIMITS! 🎉');
  console.log('   - Better than ArXiv + PubMed combined');
  console.log('   - All fields: STEM, Medicine, Social Sciences');
  console.log('   - Rich metadata: authors, institutions, citations');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    await createTableIfNotExists(client);

    console.log('');
    console.log('📊 Collecting papers...');
    console.log('');

    const papers = await collectOpenAlex();
    console.log(`   ✅ Collected ${papers.length} papers`);
    console.log('');

    console.log('💾 Inserting into database...');
    for (const paper of papers) {
      await insertPaper(client, paper);
    }
    console.log(`✅ ${papers.length} papers inserted/updated`);
    console.log('');

    // Summary
    console.log('📊 Summary by field:');
    console.log('');

    const summaryQuery = `
      SELECT
        primary_concept,
        COUNT(*) as paper_count,
        AVG(cited_by_count)::INT as avg_citations,
        SUM(cited_by_count) as total_citations
      FROM openalex_papers
      GROUP BY primary_concept
      ORDER BY total_citations DESC;
    `;

    const summary = await client.query(summaryQuery);

    summary.rows.forEach((row) => {
      console.log(`   ${row.primary_concept}:`);
      console.log(`      Papers: ${row.paper_count}`);
      console.log(`      Avg Citations: ${row.avg_citations}`);
      console.log(`      Total Citations: ${row.total_citations.toLocaleString()}`);
      console.log('');
    });

    console.log('✅ Collection complete!');
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

// ============================================================================
// DRY RUN MODE
// ============================================================================

async function dryRun() {
  console.log('🚀 Sofia Pulse - OpenAlex Papers Collector (DRY RUN)');
  console.log('='.repeat(60));
  console.log('');
  console.log('📚 OPENALEX: 250M+ PAPERS!');
  console.log('');
  console.log('   The LARGEST open research database in the world');
  console.log('   100% FREE with NO API LIMITS');
  console.log('   Replaces Microsoft Academic (discontinued)');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const papers = await collectOpenAlex();
  console.log(`✅ Collected ${papers.length} sample papers`);
  console.log('');

  // By concept
  const byConcept = papers.reduce((acc, p) => {
    if (!acc[p.primary_concept]) acc[p.primary_concept] = [];
    acc[p.primary_concept].push(p);
    return acc;
  }, {} as Record<string, OpenAlexPaper[]>);

  console.log('📊 Papers by Field:');
  console.log('');

  Object.entries(byConcept)
    .sort(([, a], [, b]) => {
      const aCites = a.reduce((sum, p) => sum + p.cited_by_count, 0);
      const bCites = b.reduce((sum, p) => sum + p.cited_by_count, 0);
      return bCites - aCites;
    })
    .forEach(([concept, paps]) => {
      const totalCites = paps.reduce((sum, p) => sum + p.cited_by_count, 0);
      console.log(`   ${concept}: ${paps.length} papers, ${totalCites.toLocaleString()} total citations`);
    });

  console.log('');
  console.log('🔥 Most Cited Papers:');
  console.log('');

  const sorted = [...papers].sort((a, b) => b.cited_by_count - a.cited_by_count);

  sorted.slice(0, 5).forEach((paper, idx) => {
    console.log(`   ${idx + 1}. ${paper.title}`);
    console.log(`      Citations: ${paper.cited_by_count.toLocaleString()}`);
    console.log(`      Field: ${paper.primary_concept}`);
    console.log(`      Institution: ${paper.author_institutions[0]}`);
    console.log(`      Year: ${paper.publication_year}`);
    console.log('');
  });

  // By country
  const countryPapers = papers.reduce((acc, p) => {
    p.author_countries.forEach(country => {
      if (!acc[country]) acc[country] = 0;
      acc[country]++;
    });
    return acc;
  }, {} as Record<string, number>);

  console.log('🌍 Research Output by Country:');
  console.log('');

  Object.entries(countryPapers)
    .sort(([, a], [, b]) => b - a)
    .forEach(([country, count]) => {
      console.log(`   ${country}: ${count} papers`);
    });

  console.log('');
  console.log('='.repeat(60));
  console.log('');
  console.log('💡 OPENALEX POWER:');
  console.log('');

  const totalCitations = papers.reduce((sum, p) => sum + p.cited_by_count, 0);
  const avgCitations = totalCitations / papers.length;
  const openAccess = papers.filter(p => p.is_open_access).length;

  console.log(`   Total Citations: ${totalCitations.toLocaleString()}`);
  console.log(`   Avg Citations: ${avgCitations.toFixed(0)}`);
  console.log(`   Open Access: ${openAccess}/${papers.length} (${((openAccess / papers.length) * 100).toFixed(0)}%)`);
  console.log('');
  console.log('   Can track ALL research fields globally');
  console.log('   Institution rankings by output');
  console.log('   Country comparisons');
  console.log('   Emerging research trends');
  console.log('');

  console.log('🎯 USE CASES:');
  console.log('');
  console.log('   - Identify breakthrough papers early (high citations)');
  console.log('   - Track university research output');
  console.log('   - Correlate papers → patents → startups');
  console.log('   - Monitor AI, biotech, climate research');
  console.log('   - Geographic research trends');
  console.log('');
  console.log('✅ Dry run complete!');
}

// ============================================================================
// RUN
// ============================================================================

if (require.main === module) {
  const args = process.argv.slice(2);
  const isDryRun = args.includes('--dry-run') || args.includes('-d');

  if (isDryRun) {
    dryRun().catch(console.error);
  } else {
    main().catch((error) => {
      if (error.code === 'ECONNREFUSED') {
        console.log('');
        console.log('⚠️  Database connection failed!');
        console.log('');
        console.log('💡 TIP: Run with --dry-run to see sample data:');
        console.log('   npm run collect:openalex -- --dry-run');
        console.log('');
        process.exit(1);
      }
      throw error;
    });
  }
}

export { collectOpenAlex, dryRun };
