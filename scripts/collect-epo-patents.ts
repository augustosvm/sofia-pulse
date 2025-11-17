#!/usr/bin/env tsx

/**
 * Sofia Pulse - EPO Patents Collector (European Patent Office)
 *
 * Coleta patentes europeias via EPO Open Patent Services (OPS)
 *
 * POR QUE PATENTES EUROPEIAS SÃO IMPORTANTES:
 * - Europa: Segundo maior mercado de patentes (depois China)
 * - EPO cobre 38 países europeus
 * - Forte em: Automotivo, Farmacêutico, Química, Energia
 * - Indicador de competitividade tecnológica europeia
 *
 * FONTE:
 * - API: EPO Open Patent Services (OPS) - 100% GRATUITA
 * - URL: https://www.epo.org/searching-for-patents/data/web-services/ops.html
 * - Volume: 180k+ applications/ano
 * - Países: Alemanha, França, UK, Suíça, Holanda, etc.
 */

import { Client } from 'pg';
import * as dotenv from 'dotenv';

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

interface EPOPatent {
  application_number: string;
  title: string;
  applicant: string;
  applicant_country: string;
  inventors: string[];
  ipc_classification: string[];
  filing_date: string;
  publication_date: string;
  abstract: string;
  status: string;
  technology_field?: string;
  designated_states?: string[]; // Países onde patente é válida
}

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

async function createTableIfNotExists(client: Client): Promise<void> {
  const createTableQuery = `
    CREATE TABLE IF NOT EXISTS epo_patents (
      id SERIAL PRIMARY KEY,
      application_number VARCHAR(50) UNIQUE,
      title TEXT NOT NULL,
      applicant VARCHAR(255),
      applicant_country VARCHAR(100),
      inventors TEXT[],
      ipc_classification VARCHAR(50)[],
      filing_date DATE,
      publication_date DATE,
      abstract TEXT,
      status VARCHAR(50),
      technology_field VARCHAR(100),
      designated_states VARCHAR(10)[],
      collected_at TIMESTAMP DEFAULT NOW()
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_epo_applicant
      ON epo_patents(applicant);

    CREATE INDEX IF NOT EXISTS idx_epo_country
      ON epo_patents(applicant_country);

    CREATE INDEX IF NOT EXISTS idx_epo_filing_date
      ON epo_patents(filing_date DESC);

    CREATE INDEX IF NOT EXISTS idx_epo_tech_field
      ON epo_patents(technology_field);

    CREATE INDEX IF NOT EXISTS idx_epo_ipc
      ON epo_patents USING GIN(ipc_classification);
  `;

  await client.query(createTableQuery);
  console.log('✅ Table epo_patents ready');
}

async function insertPatent(client: Client, patent: EPOPatent): Promise<void> {
  const insertQuery = `
    INSERT INTO epo_patents (
      application_number, title, applicant, applicant_country,
      inventors, ipc_classification, filing_date, publication_date,
      abstract, status, technology_field, designated_states
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    ON CONFLICT (application_number)
    DO UPDATE SET
      status = EXCLUDED.status,
      collected_at = NOW();
  `;

  await client.query(insertQuery, [
    patent.application_number,
    patent.title,
    patent.applicant,
    patent.applicant_country,
    patent.inventors,
    patent.ipc_classification,
    patent.filing_date,
    patent.publication_date,
    patent.abstract,
    patent.status,
    patent.technology_field || null,
    patent.designated_states || [],
  ]);
}

// ============================================================================
// COLLECTORS
// ============================================================================

function classifyTechnologyField(ipcCodes: string[]): string {
  if (!ipcCodes || ipcCodes.length === 0) return 'Other';

  const firstCode = ipcCodes[0].toUpperCase();

  // European strengths
  if (firstCode.startsWith('A61')) return 'Pharmaceuticals';
  if (firstCode.startsWith('C07') || firstCode.startsWith('C08')) return 'Chemistry';
  if (firstCode.startsWith('B60')) return 'Automotive';
  if (firstCode.startsWith('F03')) return 'Wind/Hydro Energy';
  if (firstCode.startsWith('H01L')) return 'Semiconductors';
  if (firstCode.startsWith('H04')) return 'Telecommunications';
  if (firstCode.startsWith('G06')) return 'Computing/AI';
  if (firstCode.startsWith('H02')) return 'Electric Power';
  if (firstCode.startsWith('C12')) return 'Biotechnology';
  if (firstCode.startsWith('A01')) return 'Agriculture';

  return 'Other';
}

/**
 * Mock data - Em produção, seria EPO OPS API
 * Dados baseados em tendências reais de patentes europeias
 */
async function collectEPOPatents(): Promise<EPOPatent[]> {
  console.log('🇪🇺 Collecting EPO patents...');
  console.log('   (Mock data - production would use EPO OPS API)');

  const mockPatents: EPOPatent[] = [
    // Automotive - Europa lidera
    {
      application_number: 'EP24123456.0',
      title: 'Electric Vehicle Battery Management System with Predictive Thermal Control',
      applicant: 'Robert Bosch GmbH',
      applicant_country: 'Germany',
      inventors: ['Schmidt Hans', 'Müller Anna', 'Weber Klaus'],
      ipc_classification: ['B60L58/12', 'H01M10/42'],
      filing_date: '2024-03-10',
      publication_date: '2024-09-10',
      abstract: 'A battery management system with AI-driven thermal prediction for optimal EV performance...',
      status: 'Published',
      designated_states: ['DE', 'FR', 'IT', 'ES', 'NL', 'SE', 'PL'],
    },
    {
      application_number: 'EP24234567.1',
      title: 'Autonomous Driving Sensor Fusion System',
      applicant: 'Daimler AG',
      applicant_country: 'Germany',
      inventors: ['Becker Thomas', 'Fischer Marie'],
      ipc_classification: ['B60W30/095', 'G05D1/02'],
      filing_date: '2024-04-15',
      publication_date: '2024-10-15',
      abstract: 'Advanced sensor fusion combining LiDAR, radar, and cameras for Level 4 autonomy...',
      status: 'Published',
      designated_states: ['DE', 'FR', 'UK', 'IT', 'NL'],
    },
    {
      application_number: 'EP24345678.2',
      title: 'Lightweight Carbon Fiber Composite for Automotive Body',
      applicant: 'BMW AG',
      applicant_country: 'Germany',
      inventors: ['Hoffmann Peter', 'Schulz Lisa'],
      ipc_classification: ['B60J5/00', 'C08J5/04'],
      filing_date: '2024-05-20',
      publication_date: '2024-11-20',
      abstract: 'Carbon fiber reinforced polymer optimized for mass production and recyclability...',
      status: 'Published',
      designated_states: ['DE', 'FR', 'IT', 'ES', 'AT'],
    },

    // Pharmaceuticals - Europa tradicional
    {
      application_number: 'EP24456789.3',
      title: 'mRNA Vaccine Platform for Rapid Pathogen Response',
      applicant: 'BioNTech SE',
      applicant_country: 'Germany',
      inventors: ['Özlem Türeci', 'Uğur Şahin'],
      ipc_classification: ['A61K39/39', 'C12N15/11'],
      filing_date: '2024-02-25',
      publication_date: '2024-08-25',
      abstract: 'Modular mRNA platform enabling rapid vaccine development for emerging pathogens...',
      status: 'Published',
      designated_states: ['DE', 'FR', 'UK', 'IT', 'ES', 'NL', 'BE', 'CH'],
    },
    {
      application_number: 'EP24567890.4',
      title: 'Antibody-Drug Conjugate for Targeted Cancer Therapy',
      applicant: 'Roche Holding AG',
      applicant_country: 'Switzerland',
      inventors: ['Meier Stefan', 'Keller Julia'],
      ipc_classification: ['A61K47/68', 'C07K16/00'],
      filing_date: '2024-03-30',
      publication_date: '2024-09-30',
      abstract: 'Novel ADC with improved linker stability and tumor-selective payload release...',
      status: 'Published',
      designated_states: ['CH', 'DE', 'FR', 'UK', 'IT', 'NL'],
    },
    {
      application_number: 'EP24678901.5',
      title: 'Gene Editing Therapy for Inherited Blood Disorders',
      applicant: 'Novartis AG',
      applicant_country: 'Switzerland',
      inventors: ['Vogel Martin', 'Brunner Sophie'],
      ipc_classification: ['C12N15/90', 'A61K48/00'],
      filing_date: '2024-01-15',
      publication_date: '2024-07-15',
      abstract: 'CRISPR-based gene therapy for sickle cell disease and beta-thalassemia...',
      status: 'Published',
      designated_states: ['CH', 'DE', 'FR', 'UK', 'IT'],
    },

    // Renewable Energy - Europa forte
    {
      application_number: 'EP24789012.6',
      title: 'Offshore Wind Turbine with Floating Foundation',
      applicant: 'Siemens Gamesa Renewable Energy',
      applicant_country: 'Spain',
      inventors: ['García Carlos', 'López Elena'],
      ipc_classification: ['F03D13/20', 'B63B1/00'],
      filing_date: '2024-04-05',
      publication_date: '2024-10-05',
      abstract: 'Semi-submersible floating platform for deep-water wind farms up to 15MW turbines...',
      status: 'Published',
      designated_states: ['ES', 'DE', 'FR', 'UK', 'DK', 'NO'],
    },
    {
      application_number: 'EP24890123.7',
      title: 'Green Hydrogen Production via Electrolysis',
      applicant: 'Linde plc',
      applicant_country: 'Ireland',
      inventors: ['O\'Brien Sean', 'Murphy Aoife'],
      ipc_classification: ['C25B1/04', 'H01M8/18'],
      filing_date: '2024-06-10',
      publication_date: '2024-12-10',
      abstract: 'High-efficiency PEM electrolyzer for industrial-scale green hydrogen production...',
      status: 'Published',
      designated_states: ['IE', 'DE', 'FR', 'NL', 'UK'],
    },

    // Semiconductors
    {
      application_number: 'EP24901234.8',
      title: 'EUV Lithography System for Advanced Chip Manufacturing',
      applicant: 'ASML Holding N.V.',
      applicant_country: 'Netherlands',
      inventors: ['de Jong Pieter', 'van der Berg Emma'],
      ipc_classification: ['H01L21/027', 'G03F7/20'],
      filing_date: '2024-02-20',
      publication_date: '2024-08-20',
      abstract: 'Next-generation EUV system enabling sub-3nm node semiconductor manufacturing...',
      status: 'Published',
      designated_states: ['NL', 'DE', 'FR', 'BE', 'UK'],
    },

    // Chemistry
    {
      application_number: 'EP24012345.9',
      title: 'Sustainable Polymer from Biomass Feedstock',
      applicant: 'BASF SE',
      applicant_country: 'Germany',
      inventors: ['Zimmermann Frank', 'Koch Andrea'],
      ipc_classification: ['C08G63/00', 'C08L67/00'],
      filing_date: '2024-05-15',
      publication_date: '2024-11-15',
      abstract: 'Bio-based polyester with properties matching petroleum-derived plastics...',
      status: 'Published',
      designated_states: ['DE', 'FR', 'IT', 'NL', 'BE'],
    },

    // Aerospace
    {
      application_number: 'EP24123457.0',
      title: 'Electric Aircraft Propulsion System',
      applicant: 'Airbus SE',
      applicant_country: 'France',
      inventors: ['Dubois Pierre', 'Martin Claire'],
      ipc_classification: ['B64D27/24', 'H02K7/18'],
      filing_date: '2024-03-25',
      publication_date: '2024-09-25',
      abstract: 'Hybrid-electric propulsion for regional aircraft with 800km range...',
      status: 'Published',
      designated_states: ['FR', 'DE', 'UK', 'ES', 'IT'],
    },
  ];

  // Classificar tecnologia
  mockPatents.forEach((patent) => {
    patent.technology_field = classifyTechnologyField(patent.ipc_classification);
  });

  return mockPatents;
}

// ============================================================================
// MAIN FUNCTION
// ============================================================================

async function main() {
  console.log('🚀 Sofia Pulse - EPO Patents Collector');
  console.log('='.repeat(60));
  console.log('');
  console.log('🇪🇺 WHY EPO PATENTS MATTER:');
  console.log('   - Europe: 2nd largest patent market (after China)');
  console.log('   - Covers 38 European countries');
  console.log('   - Strong in: Automotive, Pharma, Chemicals, Energy');
  console.log('   - Indicator of European tech competitiveness');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    await createTableIfNotExists(client);

    console.log('');
    console.log('📊 Collecting patents...');
    console.log('');

    const patents = await collectEPOPatents();
    console.log(`   ✅ Collected ${patents.length} patents`);
    console.log('');

    console.log('💾 Inserting into database...');
    for (const patent of patents) {
      await insertPatent(client, patent);
    }
    console.log(`✅ ${patents.length} patents inserted/updated`);
    console.log('');

    // Summary
    console.log('📊 Summary:');
    console.log('');

    const summaryQuery = `
      SELECT
        technology_field,
        COUNT(*) as patent_count,
        array_agg(DISTINCT applicant_country) as countries
      FROM epo_patents
      GROUP BY technology_field
      ORDER BY patent_count DESC;
    `;

    const summary = await client.query(summaryQuery);

    summary.rows.forEach((row) => {
      console.log(`   ${row.technology_field}:`);
      console.log(`      Patents: ${row.patent_count}`);
      console.log(`      Countries: ${row.countries.join(', ')}`);
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
  console.log('🚀 Sofia Pulse - EPO Patents Collector (DRY RUN)');
  console.log('='.repeat(60));
  console.log('');
  console.log('🇪🇺 WHY EPO PATENTS MATTER:');
  console.log('   - Europe: 2nd largest patent market (after China)');
  console.log('   - Covers 38 European countries');
  console.log('   - Strong in: Automotive, Pharma, Chemicals, Energy');
  console.log('   - Germany, Switzerland, Netherlands lead innovation');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const patents = await collectEPOPatents();
  console.log(`✅ Collected ${patents.length} patents`);
  console.log('');

  // Group by country
  const byCountry = patents.reduce((acc, p) => {
    if (!acc[p.applicant_country]) acc[p.applicant_country] = [];
    acc[p.applicant_country].push(p);
    return acc;
  }, {} as Record<string, EPOPatent[]>);

  console.log('📊 Patents by Country:');
  console.log('');

  Object.entries(byCountry)
    .sort(([, a], [, b]) => b.length - a.length)
    .forEach(([country, pats]) => {
      console.log(`   ${country}: ${pats.length} patents`);
      const companies = [...new Set(pats.map((p) => p.applicant))];
      console.log(`      Companies: ${companies.join(', ')}`);
      console.log('');
    });

  // Group by technology
  const byTech = patents.reduce((acc, p) => {
    const field = p.technology_field || 'Other';
    if (!acc[field]) acc[field] = [];
    acc[field].push(p);
    return acc;
  }, {} as Record<string, EPOPatent[]>);

  console.log('🔬 Patents by Technology:');
  console.log('');

  Object.entries(byTech)
    .sort(([, a], [, b]) => b.length - a.length)
    .forEach(([field, pats]) => {
      console.log(`   ${field}: ${pats.length} patents`);
      console.log('');
    });

  // Show samples
  console.log('📋 Sample Patents:');
  console.log('');

  patents.slice(0, 3).forEach((patent) => {
    console.log(`   ${patent.title}`);
    console.log(`      Applicant: ${patent.applicant} (${patent.applicant_country})`);
    console.log(`      Field: ${patent.technology_field}`);
    console.log(`      Filed: ${patent.filing_date}`);
    console.log(`      States: ${patent.designated_states?.join(', ')}`);
    console.log('');
  });

  console.log('='.repeat(60));
  console.log('');
  console.log('💡 EUROPEAN INNOVATION INSIGHTS:');
  console.log('');

  console.log('   Top Innovators: Germany (Bosch, Daimler, BMW, BASF)');
  console.log('   Pharma Leaders: Switzerland (Roche, Novartis), Germany (BioNTech)');
  console.log('   Semiconductor: Netherlands (ASML - EUV monopoly)');
  console.log('   Automotive: Strong EV transition patents');
  console.log('   Renewable Energy: Wind, hydrogen leadership');
  console.log('');

  console.log('🌍 GLOBAL COMPARISON:');
  console.log('');
  console.log('   Compare EPO (Europe) vs USPTO (USA) vs CNIPA (China)');
  console.log('   Track technology transfer across regions');
  console.log('   Correlate with university research, IPOs, funding');
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
        console.log('   npm run collect:epo -- --dry-run');
        console.log('');
        process.exit(1);
      }
      throw error;
    });
  }
}

export { collectEPOPatents, dryRun };
