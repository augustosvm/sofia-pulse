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
 * Sofia Pulse - WIPO China Patents Collector
 *
 * Coleta patentes chinesas via WIPO (World Intellectual Property Organization)
 * com traduções em inglês disponíveis.
 *
 * POR QUE PATENTES CHINESAS SÃO CRÍTICAS:
 * - China registra MAIS PATENTES que EUA + Europa + Japão JUNTOS
 * - Liderança em: AI, 5G, batteries, solar, biotech
 * - WIPO API tem traduções em inglês (crucial!)
 * - Indicador leading de inovação tecnológica
 *
 * FONTE:
 * - API: WIPO PatentScope API (100% gratuita)
 * - URL: https://patentscope.wipo.int
 * - Volume: 1.5M+ patentes chinesas/ano
 * - Cobertura: CNIPA (China National Intellectual Property Administration)
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

interface WIPOPatent {
  application_number: string;
  title: string;
  title_cn?: string;
  applicant: string;
  inventors: string[];
  ipc_classification: string[];
  filing_date: string;
  publication_date: string;
  abstract: string;
  abstract_cn?: string;
  status: string;
  technology_field?: string;
}

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================


// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

function slugify(text: string): string {
  return text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^\w\-]+/g, '')
    .replace(/\-\-+/g, '-');
}

async function ensureOrganization(client: Client, name: string): Promise<number> {
  const findQuery = `SELECT id FROM sofia.organizations WHERE name = $1 LIMIT 1`;
  const findRes = await client.query(findQuery, [name]);

  if (findRes.rows.length > 0) return findRes.rows[0].id;

  const orgId = slugify(name) + '-' + Math.floor(Math.random() * 10000);
  const insertQuery = `
    INSERT INTO sofia.organizations (name, normalized_name, organization_id, created_at)
    VALUES ($1, $2, $3, NOW())
    RETURNING id
  `;
  const insertRes = await client.query(insertQuery, [name, name.toLowerCase(), orgId]);
  return insertRes.rows[0].id;
}

async function ensurePerson(client: Client, fullName: string): Promise<number> {
  const findQuery = `SELECT id FROM sofia.persons WHERE full_name = $1 LIMIT 1`;
  const findRes = await client.query(findQuery, [fullName]);

  if (findRes.rows.length > 0) return findRes.rows[0].id;

  const insertQuery = `
    INSERT INTO sofia.persons (full_name, normalized_name, first_seen)
    VALUES ($1, $2, NOW())
    RETURNING id
  `;
  const insertRes = await client.query(insertQuery, [fullName, fullName.toLowerCase()]);
  return insertRes.rows[0].id;
}

async function insertPatent(client: Client, patent: WIPOPatent): Promise<void> {
  const insertQuery = `
    INSERT INTO sofia.patents (
      source, patent_number, title, abstract, 
      ipc_classification, filing_date, publication_date,
      status, technology_field, country_code,
      inventors_count, collected_at, updated_at
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
    ON CONFLICT (source, patent_number)
    DO UPDATE SET
      status = EXCLUDED.status,
      updated_at = NOW()
    RETURNING id;
  `;

  const res = await client.query(insertQuery, [
    'WIPO',                       // source
    patent.application_number,    // patent_number
    patent.title,                 // title
    patent.abstract,              // abstract
    patent.ipc_classification,    // ipc_classification
    patent.filing_date,           // filing_date
    patent.publication_date,      // publication_date
    patent.status,                // status
    patent.technology_field,      // technology_field
    'CN',                         // country_code
    patent.inventors.length,      // inventors_count
  ]);

  const patentId = res.rows[0].id;

  if (patent.applicant) {
    const orgId = await ensureOrganization(client, patent.applicant);
    const checkLink = await client.query(
      `SELECT id FROM sofia.patent_applicants WHERE patent_id = $1 AND organization_id = $2`,
      [patentId, orgId]
    );
    if (checkLink.rowCount === 0) {
      await client.query(
        `INSERT INTO sofia.patent_applicants (patent_id, organization_id, is_assignee, created_at) VALUES ($1, $2, true, NOW())`,
        [patentId, orgId]
      );
    }
  }

  if (patent.inventors && patent.inventors.length > 0) {
    let order = 1;
    for (const inventorName of patent.inventors) {
      const personId = await ensurePerson(client, inventorName);
      const checkLink = await client.query(
        `SELECT id FROM sofia.patent_inventors WHERE patent_id = $1 AND person_id = $2`,
        [patentId, personId]
      );
      if (checkLink.rowCount === 0) {
        await client.query(
          `INSERT INTO sofia.patent_inventors (patent_id, person_id, inventor_order, is_primary, created_at) VALUES ($1, $2, $3, $4, NOW())`,
          [patentId, personId, order, order === 1]
        );
      }
      order++;
    }
  }
}


// ============================================================================
// COLLECTORS
// ============================================================================

/**
 * Classifica patente por campo tecnológico baseado em IPC
 */
function classifyTechnologyField(ipcCodes: string[]): string {
  if (!ipcCodes || ipcCodes.length === 0) return 'Other';

  const firstCode = ipcCodes[0].toUpperCase();

  // IPC Classification mapping
  // G06: Computing/Calculating/Counting
  // H01: Basic electric elements
  // H04: Electric communication
  // A61: Medical/Veterinary science
  // C12: Biochemistry/Microbiology
  // B60: Vehicles
  // H02: Generation/Conversion/Distribution of electric power

  if (firstCode.startsWith('G06N')) return 'Artificial Intelligence';
  if (firstCode.startsWith('G06')) return 'Computing';
  if (firstCode.startsWith('H04W')) return '5G/Wireless';
  if (firstCode.startsWith('H04')) return 'Telecommunications';
  if (firstCode.startsWith('H01M')) return 'Batteries/Energy Storage';
  if (firstCode.startsWith('H01L')) return 'Semiconductors';
  if (firstCode.startsWith('H02')) return 'Electric Power';
  if (firstCode.startsWith('A61')) return 'Medical/Pharma';
  if (firstCode.startsWith('C12')) return 'Biotechnology';
  if (firstCode.startsWith('B60')) return 'Automotive/EV';
  if (firstCode.startsWith('H05')) return 'Solar/Renewable Energy';

  return 'Other';
}

/**
 * Mock data - Em produção, isso seria chamada à WIPO API
 * WIPO PatentScope Search API: https://patentscope.wipo.int/search/en/help/data_products.jsf
 */
async function collectWIPOPatents(): Promise<WIPOPatent[]> {
  console.log('📋 Collecting WIPO China patents...');
  console.log('   (Mock data - production would call WIPO API)');

  // Mock data baseado em tendências reais de patentes chinesas
  const mockPatents: WIPOPatent[] = [
    // AI/Machine Learning
    {
      application_number: 'CN202410123456',
      title: 'Deep Learning System for Image Recognition in Autonomous Vehicles',
      title_cn: '用于自动驾驶车辆图像识别的深度学习系统',
      applicant: 'Baidu Inc.',
      inventors: ['Zhang Wei', 'Li Ming', 'Wang Fang'],
      ipc_classification: ['G06N3/08', 'G06T7/00'],
      filing_date: '2024-03-15',
      publication_date: '2024-09-15',
      abstract: 'A deep learning system for real-time image recognition in autonomous driving scenarios...',
      abstract_cn: '一种用于自动驾驶场景中实时图像识别的深度学习系统...',
      status: 'Published',
    },
    {
      application_number: 'CN202410234567',
      title: 'Natural Language Processing Model for Multi-lingual Translation',
      title_cn: '用于多语言翻译的自然语言处理模型',
      applicant: 'Alibaba Group',
      inventors: ['Chen Jing', 'Liu Yang'],
      ipc_classification: ['G06N3/04', 'G06F40/58'],
      filing_date: '2024-04-20',
      publication_date: '2024-10-20',
      abstract: 'A transformer-based NLP model optimized for Chinese-English translation...',
      status: 'Published',
    },

    // 5G/Telecommunications
    {
      application_number: 'CN202410345678',
      title: '5G Network Slicing Architecture for Ultra-Low Latency',
      title_cn: '用于超低延迟的5G网络切片架构',
      applicant: 'Huawei Technologies Co., Ltd.',
      inventors: ['Zhou Qiang', 'Xu Lan', 'Ma Hong'],
      ipc_classification: ['H04W28/02', 'H04W72/04'],
      filing_date: '2024-05-10',
      publication_date: '2024-11-10',
      abstract: 'A network slicing architecture enabling sub-millisecond latency for 5G applications...',
      status: 'Published',
    },
    {
      application_number: 'CN202410456789',
      title: 'Massive MIMO Antenna Array for 5G Base Stations',
      title_cn: '用于5G基站的大规模MIMO天线阵列',
      applicant: 'ZTE Corporation',
      inventors: ['Huang Lei', 'Zhao Min'],
      ipc_classification: ['H04W16/28', 'H01Q21/00'],
      filing_date: '2024-06-05',
      publication_date: '2024-12-05',
      abstract: 'A massive MIMO antenna configuration optimized for urban 5G deployment...',
      status: 'Published',
    },

    // Batteries/Energy Storage
    {
      application_number: 'CN202410567890',
      title: 'Lithium Iron Phosphate Battery with Extended Cycle Life',
      title_cn: '具有延长循环寿命的磷酸铁锂电池',
      applicant: 'CATL (Contemporary Amperex Technology)',
      inventors: ['Wu Kai', 'Sun Hua', 'Gao Feng'],
      ipc_classification: ['H01M10/0525', 'H01M4/58'],
      filing_date: '2024-02-28',
      publication_date: '2024-08-28',
      abstract: 'An improved LFP battery chemistry achieving 5000+ charge cycles...',
      status: 'Published',
    },
    {
      application_number: 'CN202410678901',
      title: 'Solid-State Battery Electrolyte with High Ionic Conductivity',
      title_cn: '具有高离子电导率的固态电池电解质',
      applicant: 'BYD Company Limited',
      inventors: ['Tang Yun', 'Luo Jie'],
      ipc_classification: ['H01M10/0562', 'C01B25/00'],
      filing_date: '2024-03-25',
      publication_date: '2024-09-25',
      abstract: 'A sulfide-based solid electrolyte for next-generation EV batteries...',
      status: 'Published',
    },

    // Semiconductors
    {
      application_number: 'CN202410789012',
      title: '3nm Process Chip Manufacturing Method',
      title_cn: '3纳米工艺芯片制造方法',
      applicant: 'SMIC (Semiconductor Manufacturing International Corporation)',
      inventors: ['Jiang Bo', 'Qian Xin', 'He Rong'],
      ipc_classification: ['H01L21/027', 'H01L29/78'],
      filing_date: '2024-01-15',
      publication_date: '2024-07-15',
      abstract: 'Advanced lithography process for 3nm node semiconductor manufacturing...',
      status: 'Published',
    },

    // Solar/Renewable Energy
    {
      application_number: 'CN202410890123',
      title: 'High-Efficiency Perovskite Solar Cell',
      title_cn: '高效钙钛矿太阳能电池',
      applicant: 'LONGi Green Energy Technology',
      inventors: ['Zhong Tao', 'Shi Yu'],
      ipc_classification: ['H01L51/42', 'H05B33/00'],
      filing_date: '2024-04-10',
      publication_date: '2024-10-10',
      abstract: 'A perovskite solar cell achieving >25% conversion efficiency...',
      status: 'Published',
    },

    // Biotechnology
    {
      application_number: 'CN202410901234',
      title: 'CRISPR Gene Editing System for Crop Improvement',
      title_cn: '用于作物改良的CRISPR基因编辑系统',
      applicant: 'Chinese Academy of Sciences',
      inventors: ['Deng Xia', 'Pan Shu', 'Kong Wei'],
      ipc_classification: ['C12N15/10', 'A01H1/00'],
      filing_date: '2024-05-20',
      publication_date: '2024-11-20',
      abstract: 'A CRISPR-based system for enhancing drought resistance in rice...',
      status: 'Published',
    },

    // Electric Vehicles
    {
      application_number: 'CN202411012345',
      title: 'Autonomous Driving Control System with V2X Integration',
      title_cn: '集成V2X的自动驾驶控制系统',
      applicant: 'NIO Inc.',
      inventors: ['Feng Chao', 'Yao Ling'],
      ipc_classification: ['B60W30/00', 'H04W4/40'],
      filing_date: '2024-06-15',
      publication_date: '2024-12-15',
      abstract: 'An AD system integrating vehicle-to-everything communication for enhanced safety...',
      status: 'Published',
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

async function runWIPOCollector() {
  console.log('🚀 Sofia Pulse - WIPO China Patents Collector');
  console.log('='.repeat(60));
  console.log('');
  console.log('🇨🇳 WHY CHINA PATENTS MATTER:');
  console.log('   - China files MORE patents than USA+EU+Japan COMBINED');
  console.log('   - Leading in: AI, 5G, batteries, solar, biotech');
  console.log('   - WIPO provides English translations (critical!)');
  console.log('   - Early indicator of technological leadership');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    // await createTableIfNotExists(client); // Unified table exists

    console.log('');
    console.log('📊 Collecting patents...');
    console.log('');

    const patents = await collectWIPOPatents();
    console.log(`   ✅ Collected ${patents.length} patents`);
    console.log('');

    console.log('💾 Inserting into database...');
    for (const patent of patents) {
      await insertPatent(client, patent);
    }
    console.log(`✅ ${patents.length} patents inserted/updated`);
    console.log('');

    // Mostrar resumo por campo tecnológico
    console.log('📊 Summary by technology field:');
    console.log('');

    const summaryQuery = `
      SELECT
        technology_field,
        COUNT(*) as patent_count
      FROM sofia.patents
      WHERE source = 'WIPO'
      GROUP BY technology_field
      ORDER BY patent_count DESC;
    `;

    const summary = await client.query(summaryQuery);

    summary.rows.forEach((row) => {
      console.log(`   ${row.technology_field}:`);
      console.log(`      Patents: ${row.patent_count}`);
      // console.log(`      Top Applicants: ${row.top_applicants.slice(0, 3).join(', ')}`); // removed as applicant not in simple query
      console.log('');
    });

    console.log('='.repeat(60));
    console.log('');
    console.log('💡 KEY INSIGHTS:');
    console.log('');
    console.log('   - Top innovators: Huawei, CATL, Baidu, Alibaba');
    console.log('   - Focus areas: 5G, AI, Batteries (EV supply chain)');
    console.log('   - Patent velocity indicates R&D investment');
    console.log('');
    console.log('✅ Collection complete!');
  } catch (error) {
    console.error('❌ Error:', error);
    throw error;
  } finally {
    await client.end();
  }
}

// ============================================================================
// DRY RUN MODE
// ============================================================================

async function dryRun() {
  console.log('🚀 Sofia Pulse - WIPO China Patents Collector (DRY RUN)');
  console.log('='.repeat(60));
  console.log('');
  console.log('🇨🇳 WHY CHINA PATENTS MATTER:');
  console.log('   - China files MORE patents than USA+EU+Japan COMBINED');
  console.log('   - Leading in: AI, 5G, batteries, solar, biotech');
  console.log('   - WIPO provides English translations (critical!)');
  console.log('   - Early indicator of technological leadership');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const patents = await collectWIPOPatents();
  console.log(`✅ Collected ${patents.length} patents`);
  console.log('');

  // Group by technology field
  const byTech = patents.reduce((acc, p) => {
    const field = p.technology_field || 'Other';
    if (!acc[field]) acc[field] = [];
    acc[field].push(p);
    return acc;
  }, {} as Record<string, WIPOPatent[]>);

  console.log('📊 Patents by Technology Field:');
  console.log('');

  Object.entries(byTech)
    .sort(([, a], [, b]) => b.length - a.length)
    .forEach(([field, pats]) => {
      console.log(`   ${field}: ${pats.length} patents`);
      const companies = [...new Set(pats.map((p) => p.applicant))];
      console.log(`      Companies: ${companies.join(', ')}`);
      console.log('');
    });

  // Show sample patents
  console.log('📋 Sample Patents:');
  console.log('');

  patents.slice(0, 3).forEach((patent) => {
    console.log(`   ${patent.title}`);
    console.log(`      Applicant: ${patent.applicant}`);
    console.log(`      Field: ${patent.technology_field}`);
    console.log(`      IPC: ${patent.ipc_classification.join(', ')}`);
    console.log(`      Filed: ${patent.filing_date}`);
    console.log('');
  });

  console.log('='.repeat(60));
  console.log('');
  console.log('💡 CHINA INNOVATION INSIGHTS:');
  console.log('');

  const topCompanies = [...new Set(patents.map((p) => p.applicant))];
  console.log(`   Total Companies: ${topCompanies.length}`);
  console.log(`   Top Innovators: ${topCompanies.slice(0, 5).join(', ')}`);
  console.log('');
  console.log('   Key Focus Areas:');
  Object.entries(byTech).forEach(([field, pats]) => {
    console.log(`      - ${field}: ${pats.length} patents`);
  });
  console.log('');
  console.log('   This data shows China\'s strategic tech priorities');
  console.log('   and R&D investment direction');
  console.log('');

  console.log('🎯 NEXT STEPS:');
  console.log('');
  console.log('   1. Start PostgreSQL: cd finance && ./docker-run.sh');
  console.log('   2. Run: npm run collect:wipo-china');
  console.log('   3. Correlate with:');
  console.log('      - Funding rounds (tech sector)');
  console.log('      - IPOs (tech companies)');
  console.log('      - Research papers (innovation pipeline)');
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
    runWIPOCollector().catch((error) => {
      if (error.code === 'ECONNREFUSED') {
        console.log('');
        console.log('⚠️  Database connection failed!');
        console.log('');
        console.log('💡 TIP: Run with --dry-run to see sample data:');
        console.log('   npm run collect:wipo-china -- --dry-run');
        console.log('');
        process.exit(1);
      }
      throw error;
    });
  }
}

export { collectWIPOPatents, runWIPOCollector, dryRun };
