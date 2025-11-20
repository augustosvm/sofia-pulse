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
 * Sofia Pulse - NIH Grants Collector
 *
 * Coleta grants do NIH (National Institutes of Health) - $42B+/ano!
 *
 * POR QUE NIH GRANTS SÃO CRÍTICOS:
 * - $42B+ investidos em pesquisa ANUALMENTE
 * - Leading indicator: Grants HOJE → Breakthroughs em 2-5 anos
 * - Rastrear: Cancer, COVID, CRISPR, mRNA, Longevity
 * - Universidades top recebem mais (Stanford, MIT, Harvard)
 * - Correlação: NIH grant → Paper → Patent → Biotech startup
 *
 * FONTE:
 * - API: NIH RePORTER (Research Portfolio Online Reporting Tools)
 * - URL: https://reporter.nih.gov
 * - 100% GRATUITA!
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

interface NIHGrant {
  project_number: string; // R01CA123456
  title: string;
  principal_investigator: string;
  organization: string;
  city: string;
  state: string;
  country: string;
  fiscal_year: number;
  award_amount_usd: number;
  nih_institute: string; // NCI, NIAID, NHLBI, etc
  project_start_date: string;
  project_end_date: string;
  funding_mechanism: string; // R01, R21, P01, etc
  research_area: string;
  abstract: string;
  keywords?: string[];
}

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

async function createTableIfNotExists(client: Client): Promise<void> {
  const createTableQuery = `
    CREATE TABLE IF NOT EXISTS nih_grants (
      id SERIAL PRIMARY KEY,
      project_number VARCHAR(50) UNIQUE,
      title TEXT NOT NULL,
      principal_investigator VARCHAR(255),
      organization VARCHAR(255),
      city VARCHAR(100),
      state VARCHAR(50),
      country VARCHAR(100),
      fiscal_year INT,
      award_amount_usd BIGINT,
      nih_institute VARCHAR(50),
      project_start_date DATE,
      project_end_date DATE,
      funding_mechanism VARCHAR(20),
      research_area VARCHAR(255),
      abstract TEXT,
      keywords TEXT[],
      collected_at TIMESTAMP DEFAULT NOW()
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_nih_organization
      ON nih_grants(organization);

    CREATE INDEX IF NOT EXISTS idx_nih_institute
      ON nih_grants(nih_institute);

    CREATE INDEX IF NOT EXISTS idx_nih_fiscal_year
      ON nih_grants(fiscal_year DESC);

    CREATE INDEX IF NOT EXISTS idx_nih_award_amount
      ON nih_grants(award_amount_usd DESC);

    CREATE INDEX IF NOT EXISTS idx_nih_research_area
      ON nih_grants(research_area);

    CREATE INDEX IF NOT EXISTS idx_nih_keywords
      ON nih_grants USING GIN(keywords);
  `;

  await client.query(createTableQuery);
  console.log('✅ Table nih_grants ready');
}

async function insertGrant(client: Client, grant: NIHGrant): Promise<void> {
  const insertQuery = `
    INSERT INTO nih_grants (
      project_number, title, principal_investigator,
      organization, city, state, country,
      fiscal_year, award_amount_usd, nih_institute,
      project_start_date, project_end_date,
      funding_mechanism, research_area, abstract, keywords
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
    ON CONFLICT (project_number)
    DO UPDATE SET
      award_amount_usd = EXCLUDED.award_amount_usd,
      collected_at = NOW();
  `;

  await client.query(insertQuery, [
    grant.project_number,
    grant.title,
    grant.principal_investigator,
    grant.organization,
    grant.city,
    grant.state,
    grant.country,
    grant.fiscal_year,
    grant.award_amount_usd,
    grant.nih_institute,
    grant.project_start_date,
    grant.project_end_date,
    grant.funding_mechanism,
    grant.research_area,
    grant.abstract,
    grant.keywords || [],
  ]);
}

// ============================================================================
// COLLECTORS
// ============================================================================

function extractKeywords(title: string, abstract: string): string[] {
  const text = `${title} ${abstract}`.toLowerCase();
  const keywords: string[] = [];

  // Biotech/Medical Keywords
  if (text.match(/\b(crispr|gene editing|cas9)\b/)) keywords.push('CRISPR');
  if (text.match(/\b(mrna|messenger rna|vaccine)\b/)) keywords.push('mRNA');
  if (text.match(/\b(car-t|chimeric antigen receptor)\b/)) keywords.push('CAR-T');
  if (text.match(/\b(cancer|oncology|tumor|carcinoma)\b/)) keywords.push('Cancer');
  if (text.match(/\b(alzheimer|dementia|neurodegeneration)\b/)) keywords.push('Alzheimers');
  if (text.match(/\b(parkinson)\b/)) keywords.push('Parkinsons');
  if (text.match(/\b(diabetes|insulin|glucose)\b/)) keywords.push('Diabetes');
  if (text.match(/\b(covid|sars-cov-2|coronavirus)\b/)) keywords.push('COVID-19');
  if (text.match(/\b(longevity|aging|senescence)\b/)) keywords.push('Longevity');
  if (text.match(/\b(stem cell|pluripotent)\b/)) keywords.push('Stem Cells');
  if (text.match(/\b(antibody|immunotherapy|immune)\b/)) keywords.push('Immunotherapy');
  if (text.match(/\b(drug discovery|small molecule)\b/)) keywords.push('Drug Discovery');
  if (text.match(/\b(ai|artificial intelligence|machine learning)\b/)) keywords.push('AI');

  return [...new Set(keywords)];
}

/**
 * Coleta grants REAIS do NIH RePORTER API (GRATUITA!)
 * API: https://api.reporter.nih.gov/v2/projects/search
 * Docs: https://api.reporter.nih.gov/
 */
async function collectNIHGrants(): Promise<NIHGrant[]> {
  console.log('💊 Collecting NIH grants from REAL API...');

  const grants: NIHGrant[] = [];
  const currentYear = new Date().getFullYear();

  // Research areas para buscar (keywords mais relevantes)
  const searchTerms = [
    'CRISPR gene editing',
    'mRNA vaccine',
    'CAR-T immunotherapy',
    'artificial intelligence drug discovery',
    'stem cell therapy',
  ];

  for (const term of searchTerms) {
    try {
      const url = 'https://api.reporter.nih.gov/v2/projects/search';

      console.log(`   Fetching grants for: ${term}...`);

      // NIH API usa POST com JSON payload
      const payload = {
        criteria: {
          advanced_text_search: {
            operator: 'advanced',
            search_field: 'terms',
            search_text: term,
          },
          fiscal_years: [currentYear, currentYear - 1], // Last 2 years
        },
        offset: 0,
        limit: 20, // 20 per term = 100 total
        sort_field: 'award_amount',
        sort_order: 'desc',
      };

      const response = await axios.post(url, payload, {
        headers: { 'Content-Type': 'application/json' },
      });

      const results = response.data.results || [];

      for (const project of results) {
        // Extract org info
        const org = project.organization || {};
        const pi = project.principal_investigators?.[0] || {};

        // Extract keywords from abstract and title
        const abstract = project.abstract_text || '';
        const title = project.project_title || '';
        const keywords = extractKeywords(title, abstract);

        grants.push({
          project_number: project.core_project_num || project.appl_id?.toString() || '',
          title: title,
          principal_investigator: pi.full_name || 'Unknown',
          organization: org.org_name || 'Unknown',
          city: org.org_city || null,
          state: org.org_state || null,
          country: org.org_country || 'USA',
          fiscal_year: project.fiscal_year || currentYear,
          award_amount_usd: project.award_amount || 0,
          nih_institute: project.agency_ic_admin || 'NIH',
          project_start_date: project.project_start_date || null,
          project_end_date: project.project_end_date || null,
          funding_mechanism: project.activity_code || 'R01',
          research_area: keywords[0] || term.split(' ')[0], // First keyword or search term
          abstract: abstract || null,
          keywords: keywords.length > 0 ? keywords : null,
        });
      }

      console.log(`   ✅ ${results.length} grants from "${term}"`);

      // Rate limit: Be nice to NIH servers
      await new Promise(resolve => setTimeout(resolve, 1000));

    } catch (error: any) {
      console.log(`   ⚠️  Error fetching "${term}":`, error.message);
    }
  }

  console.log(`   ✅ Total: ${grants.length} grants collected`);

  return grants;
}

/**
 * FALLBACK: Mock data case API falhar
 */
async function collectNIHGrants_MOCK(): Promise<NIHGrant[]> {
  console.log('💊 Using MOCK data (API unavailable)...');

  const currentYear = new Date().getFullYear();

  const mockGrants: NIHGrant[] = [
    // CRISPR/Gene Editing
    {
      project_number: 'R01HG012345',
      title: 'CRISPR Base Editing for Treatment of Sickle Cell Disease',
      principal_investigator: 'Jennifer Doudna',
      organization: 'University of California, Berkeley',
      city: 'Berkeley',
      state: 'CA',
      country: 'USA',
      fiscal_year: currentYear,
      award_amount_usd: 2500000,
      nih_institute: 'NHGRI', // National Human Genome Research Institute
      project_start_date: `${currentYear}-07-01`,
      project_end_date: `${currentYear + 5}-06-30`,
      funding_mechanism: 'R01', // Research Project Grant
      research_area: 'Gene Therapy',
      abstract: 'We propose to develop CRISPR base editing approaches to correct the sickle cell mutation...',
      keywords: ['CRISPR', 'Stem Cells'],
    },
    {
      project_number: 'R01GM098765',
      title: 'Prime Editing for Hereditary Disease Treatment',
      principal_investigator: 'David Liu',
      organization: 'Harvard University',
      city: 'Cambridge',
      state: 'MA',
      country: 'USA',
      fiscal_year: currentYear,
      award_amount_usd: 3200000,
      nih_institute: 'NIGMS',
      project_start_date: `${currentYear}-09-01`,
      project_end_date: `${currentYear + 5}-08-31`,
      funding_mechanism: 'R01',
      research_area: 'Gene Editing',
      abstract: 'Prime editing enables precise genomic modifications without double-strand breaks...',
      keywords: ['CRISPR'],
    },

    // mRNA/Vaccines
    {
      project_number: 'R01AI087654',
      title: 'mRNA Vaccine Platform for Rapid Pandemic Response',
      principal_investigator: 'Katalin Karikó',
      organization: 'University of Pennsylvania',
      city: 'Philadelphia',
      state: 'PA',
      country: 'USA',
      fiscal_year: currentYear,
      award_amount_usd: 4500000,
      nih_institute: 'NIAID', // National Institute of Allergy and Infectious Diseases
      project_start_date: `${currentYear}-01-01`,
      project_end_date: `${currentYear + 4}-12-31`,
      funding_mechanism: 'R01',
      research_area: 'Vaccines',
      abstract: 'Developing modular mRNA vaccine platforms for emerging infectious diseases...',
      keywords: ['mRNA', 'COVID-19'],
    },

    // Cancer/Immunotherapy
    {
      project_number: 'R01CA234567',
      title: 'CAR-T Cell Therapy for Solid Tumors',
      principal_investigator: 'Carl June',
      organization: 'University of Pennsylvania',
      city: 'Philadelphia',
      state: 'PA',
      country: 'USA',
      fiscal_year: currentYear,
      award_amount_usd: 5000000,
      nih_institute: 'NCI', // National Cancer Institute
      project_start_date: `${currentYear}-04-01`,
      project_end_date: `${currentYear + 5}-03-31`,
      funding_mechanism: 'R01',
      research_area: 'Cancer Immunotherapy',
      abstract: 'Engineering CAR-T cells to overcome the immunosuppressive tumor microenvironment...',
      keywords: ['CAR-T', 'Cancer', 'Immunotherapy'],
    },
    {
      project_number: 'P01CA345678',
      title: 'AI-Driven Cancer Drug Discovery Program',
      principal_investigator: 'Eric Lander',
      organization: 'MIT/Broad Institute',
      city: 'Cambridge',
      state: 'MA',
      country: 'USA',
      fiscal_year: currentYear,
      award_amount_usd: 8000000,
      nih_institute: 'NCI',
      project_start_date: `${currentYear}-10-01`,
      project_end_date: `${currentYear + 5}-09-30`,
      funding_mechanism: 'P01', // Program Project Grant
      research_area: 'Drug Discovery',
      abstract: 'Using AI and high-throughput screening to identify novel cancer therapeutics...',
      keywords: ['Cancer', 'Drug Discovery', 'AI'],
    },

    // Alzheimers/Neuroscience
    {
      project_number: 'R01AG056789',
      title: 'Targeting Tau Protein for Alzheimers Disease Treatment',
      principal_investigator: 'Li-Huei Tsai',
      organization: 'MIT',
      city: 'Cambridge',
      state: 'MA',
      country: 'USA',
      fiscal_year: currentYear,
      award_amount_usd: 3500000,
      nih_institute: 'NIA', // National Institute on Aging
      project_start_date: `${currentYear}-05-01`,
      project_end_date: `${currentYear + 5}-04-30`,
      funding_mechanism: 'R01',
      research_area: 'Neurodegenerative Disease',
      abstract: 'Investigating tau pathology and therapeutic strategies for Alzheimers disease...',
      keywords: ['Alzheimers'],
    },

    // Longevity/Aging
    {
      project_number: 'R01AG067890',
      title: 'Cellular Senescence and Anti-Aging Interventions',
      principal_investigator: 'Judith Campisi',
      organization: 'Buck Institute for Research on Aging',
      city: 'Novato',
      state: 'CA',
      country: 'USA',
      fiscal_year: currentYear,
      award_amount_usd: 2800000,
      nih_institute: 'NIA',
      project_start_date: `${currentYear}-08-01`,
      project_end_date: `${currentYear + 5}-07-31`,
      funding_mechanism: 'R01',
      research_area: 'Aging Biology',
      abstract: 'Understanding cellular senescence and developing senolytic therapies for healthy aging...',
      keywords: ['Longevity'],
    },

    // COVID/Infectious Disease
    {
      project_number: 'U19AI178901',
      title: 'Pan-Coronavirus Vaccine Development',
      principal_investigator: 'Barney Graham',
      organization: 'NIH Vaccine Research Center',
      city: 'Bethesda',
      state: 'MD',
      country: 'USA',
      fiscal_year: currentYear,
      award_amount_usd: 10000000,
      nih_institute: 'NIAID',
      project_start_date: `${currentYear}-03-01`,
      project_end_date: `${currentYear + 7}-02-28`,
      funding_mechanism: 'U19', // Cooperative Agreement
      research_area: 'Infectious Disease',
      abstract: 'Developing universal coronavirus vaccines to protect against future pandemics...',
      keywords: ['COVID-19', 'mRNA'],
    },

    // Diabetes
    {
      project_number: 'R01DK123456',
      title: 'Stem Cell-Derived Beta Cells for Type 1 Diabetes',
      principal_investigator: 'Douglas Melton',
      organization: 'Harvard University',
      city: 'Cambridge',
      state: 'MA',
      country: 'USA',
      fiscal_year: currentYear,
      award_amount_usd: 4200000,
      nih_institute: 'NIDDK', // National Institute of Diabetes and Digestive and Kidney Diseases
      project_start_date: `${currentYear}-06-01`,
      project_end_date: `${currentYear + 5}-05-31`,
      funding_mechanism: 'R01',
      research_area: 'Diabetes',
      abstract: 'Generating functional insulin-producing beta cells from stem cells for diabetes treatment...',
      keywords: ['Diabetes', 'Stem Cells'],
    },

    // AI/Computational Biology
    {
      project_number: 'R35GM234567',
      title: 'Deep Learning for Protein Structure Prediction and Drug Design',
      principal_investigator: 'John Jumper',
      organization: 'DeepMind/Google',
      city: 'Mountain View',
      state: 'CA',
      country: 'USA',
      fiscal_year: currentYear,
      award_amount_usd: 6000000,
      nih_institute: 'NIGMS',
      project_start_date: `${currentYear}-09-15`,
      project_end_date: `${currentYear + 8}-09-14`,
      funding_mechanism: 'R35', // Maximizing Investigators' Research Award
      research_area: 'Computational Biology',
      abstract: 'Advancing AlphaFold and related AI methods for protein structure prediction and drug discovery...',
      keywords: ['AI', 'Drug Discovery'],
    },
  ];

  // Extract keywords for all grants
  mockGrants.forEach(grant => {
    if (!grant.keywords || grant.keywords.length === 0) {
      grant.keywords = extractKeywords(grant.title, grant.abstract);
    }
  });

  return mockGrants;
}

// ============================================================================
// MAIN FUNCTION
// ============================================================================

async function main() {
  console.log('🚀 Sofia Pulse - NIH Grants Collector');
  console.log('='.repeat(60));
  console.log('');
  console.log('💊 WHY NIH GRANTS ARE CRITICAL:');
  console.log('   - $42B+ invested in research ANNUALLY');
  console.log('   - Leading indicator: Grants → Breakthroughs in 2-5 years');
  console.log('   - Track: Cancer, COVID, CRISPR, mRNA, Longevity');
  console.log('   - Top universities: Stanford, MIT, Harvard, Penn');
  console.log('   - Pipeline: Grant → Paper → Patent → Startup');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    await createTableIfNotExists(client);

    console.log('');
    console.log('📊 Collecting grants...');
    console.log('');

    const grants = await collectNIHGrants();
    console.log(`   ✅ Collected ${grants.length} grants`);
    console.log('');

    console.log('💾 Inserting into database...');
    for (const grant of grants) {
      await insertGrant(client, grant);
    }
    console.log(`✅ ${grants.length} grants inserted/updated`);
    console.log('');

    // Summary
    console.log('📊 Summary:');
    console.log('');

    const summaryQuery = `
      SELECT
        research_area,
        COUNT(*) as grant_count,
        SUM(award_amount_usd) / 1e6 as total_funding_millions,
        array_agg(DISTINCT organization) as top_orgs
      FROM nih_grants
      GROUP BY research_area
      ORDER BY total_funding_millions DESC;
    `;

    const summary = await client.query(summaryQuery);

    summary.rows.forEach((row) => {
      console.log(`   ${row.research_area}:`);
      console.log(`      Grants: ${row.grant_count}`);
      console.log(`      Total Funding: $${parseFloat(row.total_funding_millions).toFixed(1)}M`);
      console.log(`      Organizations: ${row.top_orgs.slice(0, 2).join(', ')}`);
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
  console.log('🚀 Sofia Pulse - NIH Grants Collector (DRY RUN)');
  console.log('='.repeat(60));
  console.log('');
  console.log('💊 NIH: $42B+ RESEARCH FUNDING');
  console.log('');
  console.log('   Largest biomedical research funder in the world');
  console.log('   Grants TODAY → Breakthroughs in 2-5 years');
  console.log('   Track which areas getting most investment');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const grants = await collectNIHGrants();
  console.log(`✅ Collected ${grants.length} grants`);
  console.log('');

  // By research area
  const byArea = grants.reduce((acc, g) => {
    if (!acc[g.research_area]) acc[g.research_area] = [];
    acc[g.research_area].push(g);
    return acc;
  }, {} as Record<string, NIHGrant[]>);

  console.log('📊 Grants by Research Area:');
  console.log('');

  Object.entries(byArea)
    .sort(([, a], [, b]) => {
      const aTotal = a.reduce((sum, g) => sum + g.award_amount_usd, 0);
      const bTotal = b.reduce((sum, g) => sum + g.award_amount_usd, 0);
      return bTotal - aTotal;
    })
    .forEach(([area, grs]) => {
      const totalFunding = grs.reduce((sum, g) => sum + g.award_amount_usd, 0);
      console.log(`   ${area}: ${grs.length} grants, $${(totalFunding / 1e6).toFixed(1)}M`);
    });

  console.log('');
  console.log('💰 Largest Grants:');
  console.log('');

  const sorted = [...grants].sort((a, b) => b.award_amount_usd - a.award_amount_usd);

  sorted.slice(0, 5).forEach((grant, idx) => {
    console.log(`   ${idx + 1}. ${grant.title}`);
    console.log(`      Amount: $${(grant.award_amount_usd / 1e6).toFixed(1)}M`);
    console.log(`      PI: ${grant.principal_investigator}`);
    console.log(`      Organization: ${grant.organization}`);
    console.log(`      Area: ${grant.research_area}`);
    console.log('');
  });

  // Top organizations
  const orgFunding = grants.reduce((acc, g) => {
    if (!acc[g.organization]) acc[g.organization] = 0;
    acc[g.organization] += g.award_amount_usd;
    return acc;
  }, {} as Record<string, number>);

  console.log('🏛️  Top Organizations by Funding:');
  console.log('');

  Object.entries(orgFunding)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
    .forEach(([org, funding], idx) => {
      console.log(`   ${idx + 1}. ${org}: $${(funding / 1e6).toFixed(1)}M`);
    });

  console.log('');
  console.log('🔬 Hot Research Keywords:');
  console.log('');

  const keywordCount = grants.reduce((acc, g) => {
    (g.keywords || []).forEach(k => {
      acc[k] = (acc[k] || 0) + 1;
    });
    return acc;
  }, {} as Record<string, number>);

  Object.entries(keywordCount)
    .sort(([, a], [, b]) => b - a)
    .forEach(([keyword, count]) => {
      console.log(`   ${keyword}: ${count} grants`);
    });

  console.log('');
  console.log('='.repeat(60));
  console.log('');
  console.log('💡 BIOTECH PIPELINE INSIGHTS:');
  console.log('');

  const totalFunding = grants.reduce((sum, g) => sum + g.award_amount_usd, 0);
  console.log(`   Total Funding Tracked: $${(totalFunding / 1e6).toFixed(1)}M`);
  console.log('');
  console.log('   CRISPR: Next-generation gene therapies');
  console.log('   mRNA: Platform for rapid vaccine development');
  console.log('   CAR-T: Expanding to solid tumors');
  console.log('   AI: Accelerating drug discovery');
  console.log('');

  console.log('🎯 CORRELATIONS:');
  console.log('');
  console.log('   - NIH grant → Papers published (1-2 year lag)');
  console.log('   - Grant areas → Biotech startup sectors');
  console.log('   - Top PIs → Spinout companies');
  console.log('   - University funding → Patent filings');
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
        console.log('   npm run collect:nih-grants -- --dry-run');
        console.log('');
        process.exit(1);
      }
      throw error;
    });
  }
}

export { collectNIHGrants, dryRun };
