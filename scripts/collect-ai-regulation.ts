#!/usr/bin/env node
/**
 * AI Regulation Collector - Sofia Pulse
 *
 * Coleta dados de regulamentações de IA:
 * - EU AI Act
 * - Brazil LGPD/ANPD
 * - US AI Executive Orders
 * - Global AI policies
 *
 * Nota: Dados são semi-estruturados. Idealmente usar web scraping ou feeds RSS oficiais.
 * Por enquanto, base de dados estática com updates manuais importantes.
 */

import { Pool } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  user: process.env.DB_USER || 'sofia',
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME || 'sofia_db',
});

interface RegulationEvent {
  regulation_type: string;
  title: string;
  jurisdiction: string;
  regulatory_body: string | null;
  status: string;
  effective_date: Date | null;
  announced_date: Date;
  scope: string[] | null;
  impact_level: string;
  penalties_max: number | null;
  description: string | null;
  key_requirements: string[] | null;
  affected_sectors: string[] | null;
  source: string;
  source_url: string | null;
}

/**
 * Regulamentações importantes (base de dados estática)
 * TODO: Automatizar com web scraping de fontes oficiais
 */
function getKnownRegulations(): RegulationEvent[] {
  return [
    // EU AI Act
    {
      regulation_type: 'law',
      title: 'EU Artificial Intelligence Act',
      jurisdiction: 'EU',
      regulatory_body: 'European Commission',
      status: 'enacted',
      effective_date: new Date('2026-01-01'),
      announced_date: new Date('2024-03-13'),
      scope: ['AI systems', 'high-risk AI', 'biometric identification', 'critical infrastructure'],
      impact_level: 'high',
      penalties_max: 35000000, // €35M or 7% of global revenue
      description: 'Comprehensive AI regulation framework for the European Union. Establishes requirements for AI systems based on risk levels.',
      key_requirements: [
        'Risk assessment for AI systems',
        'Transparency obligations',
        'Human oversight requirements',
        'Data governance',
        'Technical documentation',
        'Conformity assessments for high-risk AI'
      ],
      affected_sectors: ['tech', 'healthcare', 'finance', 'law enforcement', 'education', 'employment'],
      source: 'eu_official',
      source_url: 'https://artificialintelligenceact.eu/'
    },

    // Brazil LGPD
    {
      regulation_type: 'law',
      title: 'Lei Geral de Proteção de Dados (LGPD)',
      jurisdiction: 'Brazil',
      regulatory_body: 'ANPD - Autoridade Nacional de Proteção de Dados',
      status: 'enforced',
      effective_date: new Date('2020-09-18'),
      announced_date: new Date('2018-08-14'),
      scope: ['personal data', 'data processing', 'AI systems using personal data'],
      impact_level: 'high',
      penalties_max: 50000000, // R$50M
      description: 'Brazilian data protection law. Affects AI systems that process personal data.',
      key_requirements: [
        'Lawful basis for data processing',
        'Data subject rights',
        'Data protection officer',
        'Privacy by design',
        'Automated decision-making transparency'
      ],
      affected_sectors: ['tech', 'finance', 'healthcare', 'retail', 'telecom'],
      source: 'br_official',
      source_url: 'https://www.gov.br/anpd/pt-br'
    },

    // US AI Executive Order
    {
      regulation_type: 'policy',
      title: 'Executive Order on Safe, Secure, and Trustworthy AI',
      jurisdiction: 'USA',
      regulatory_body: 'White House / NIST',
      status: 'enforced',
      effective_date: new Date('2023-10-30'),
      announced_date: new Date('2023-10-30'),
      scope: ['AI safety', 'critical infrastructure', 'national security', 'civil rights'],
      impact_level: 'high',
      penalties_max: null,
      description: 'Biden administration executive order establishing AI safety and security standards.',
      key_requirements: [
        'Safety testing for powerful AI models',
        'Red-team testing',
        'Watermarking AI-generated content',
        'Privacy-preserving techniques',
        'Equity and civil rights protections'
      ],
      affected_sectors: ['tech', 'defense', 'healthcare', 'finance', 'critical infrastructure'],
      source: 'us_official',
      source_url: 'https://www.whitehouse.gov/briefing-room/presidential-actions/2023/10/30/executive-order-on-the-safe-secure-and-trustworthy-development-and-use-of-artificial-intelligence/'
    },

    // China AI Regulations
    {
      regulation_type: 'law',
      title: 'Generative AI Measures',
      jurisdiction: 'China',
      regulatory_body: 'Cyberspace Administration of China (CAC)',
      status: 'enforced',
      effective_date: new Date('2023-08-15'),
      announced_date: new Date('2023-07-13'),
      scope: ['generative AI', 'large language models', 'content generation'],
      impact_level: 'high',
      penalties_max: null,
      description: 'China regulations on generative AI services and content.',
      key_requirements: [
        'Content must reflect socialist core values',
        'Security assessments',
        'User verification',
        'Watermarking generated content',
        'Prohibited content filtering'
      ],
      affected_sectors: ['tech', 'media', 'social platforms'],
      source: 'cn_official',
      source_url: 'http://www.cac.gov.cn/'
    },

    // UK AI Regulation (Pro-innovation)
    {
      regulation_type: 'policy',
      title: 'UK AI Regulation - Pro-Innovation Approach',
      jurisdiction: 'UK',
      regulatory_body: 'UK Government / DSIT',
      status: 'proposed',
      effective_date: null,
      announced_date: new Date('2023-03-29'),
      scope: ['AI governance', 'sector-specific regulation'],
      impact_level: 'medium',
      penalties_max: null,
      description: 'UK approach to AI regulation emphasizing innovation while managing risks.',
      key_requirements: [
        'Safety and robustness',
        'Transparency and explainability',
        'Fairness',
        'Accountability and governance',
        'Contestability and redress'
      ],
      affected_sectors: ['tech', 'all sectors'],
      source: 'uk_official',
      source_url: 'https://www.gov.uk/government/publications/ai-regulation-a-pro-innovation-approach'
    },

    // California AI Bill (SB 1047)
    {
      regulation_type: 'law',
      title: 'California SB 1047 - Safe and Secure Innovation for Frontier AI Models Act',
      jurisdiction: 'USA-California',
      regulatory_body: 'California State Legislature',
      status: 'proposed',
      effective_date: null,
      announced_date: new Date('2024-02-15'),
      scope: ['frontier AI models', 'AI safety'],
      impact_level: 'high',
      penalties_max: null,
      description: 'Proposed California law requiring safety testing for large AI models.',
      key_requirements: [
        'Safety testing before deployment',
        'Kill switch for AI models',
        'Whistleblower protections',
        'Liability for AI harms',
        'Third-party audits'
      ],
      affected_sectors: ['tech', 'AI companies'],
      source: 'ca_official',
      source_url: 'https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202320240SB1047'
    }
  ];
}

/**
 * Salva regulamentações no banco
 */
async function saveRegulations(regulations: RegulationEvent[]): Promise<void> {
  if (regulations.length === 0) {
    console.log('   ⚠️  No regulations to save');
    return;
  }

  const client = await pool.connect();

  try {
    let inserted = 0;
    let updated = 0;

    for (const reg of regulations) {
      try {
        const result = await client.query(
          `
          INSERT INTO sofia.ai_regulation (
            regulation_type, title, jurisdiction, regulatory_body,
            status, effective_date, announced_date, scope,
            impact_level, penalties_max, description,
            key_requirements, affected_sectors, source, source_url
          )
          VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
          ON CONFLICT (title, jurisdiction) DO UPDATE SET
            status = EXCLUDED.status,
            effective_date = EXCLUDED.effective_date,
            description = EXCLUDED.description,
            key_requirements = EXCLUDED.key_requirements
          RETURNING (xmax = 0) AS inserted
          `,
          [
            reg.regulation_type,
            reg.title,
            reg.jurisdiction,
            reg.regulatory_body,
            reg.status,
            reg.effective_date,
            reg.announced_date,
            reg.scope,
            reg.impact_level,
            reg.penalties_max,
            reg.description,
            reg.key_requirements,
            reg.affected_sectors,
            reg.source,
            reg.source_url,
          ]
        );

        if (result.rows[0].inserted) {
          inserted++;
        } else {
          updated++;
        }
      } catch (err: any) {
        console.error(`   ⚠️  Error saving regulation: ${err.message}`);
      }
    }

    console.log(`   ✅ Inserted: ${inserted}, Updated: ${updated}`);

  } finally {
    client.release();
  }
}

/**
 * Get summary statistics
 */
async function getSummary(): Promise<void> {
  const client = await pool.connect();

  try {
    const result = await client.query(`
      SELECT
        jurisdiction,
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status = 'enforced') as enforced,
        COUNT(*) FILTER (WHERE status = 'enacted') as enacted,
        COUNT(*) FILTER (WHERE status = 'proposed') as proposed
      FROM sofia.ai_regulation
      GROUP BY jurisdiction
      ORDER BY total DESC
    `);

    console.log('');
    console.log('📊 REGULATIONS BY JURISDICTION:');
    console.log('─'.repeat(60));

    for (const row of result.rows) {
      console.log(
        `   ${row.jurisdiction}: ${row.total} total ` +
        `(${row.enforced} enforced, ${row.enacted} enacted, ${row.proposed} proposed)`
      );
    }

  } finally {
    client.release();
  }
}

async function main() {
  console.log('════════════════════════════════════════════════════════════════');
  console.log('⚖️  AI REGULATION TRACKER');
  console.log('════════════════════════════════════════════════════════════════');
  console.log('');

  try {
    // Get known regulations
    const regulations = getKnownRegulations();

    console.log(`📋 Tracking ${regulations.length} major AI regulations`);
    console.log('');

    // Save to database
    console.log('💾 Saving to database...');
    await saveRegulations(regulations);

    // Show summary
    await getSummary();

    console.log('');
    console.log('✅ AI regulation tracking complete!');
    console.log('');
    console.log('💡 Note: This collector uses a curated database.');
    console.log('   For real-time updates, integrate with official sources.');
    console.log('');

  } catch (error: any) {
    console.error(`❌ Error: ${error.message}`);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
