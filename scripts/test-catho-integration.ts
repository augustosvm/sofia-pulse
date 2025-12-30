#!/usr/bin/env tsx
import { Pool } from 'pg';
import * as dotenv from 'dotenv';
import { normalizeLocation } from './shared/geo-helpers.js';
import { getOrCreateOrganization } from './shared/org-helpers.js';

dotenv.config();

const DB_CONFIG = {
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD || 'sofia123strong',
  database: process.env.POSTGRES_DB || 'sofia_db',
};

// ========== PARSE HELPERS ==========

function parseSalaryBRL(text: string): { min: number | null; max: number | null; period: string | null } {
  let min: number | null = null;
  let max: number | null = null;
  let period: string | null = null;

  if (!text) return { min, max, period };

  if (/mês|mensal|\/mês/i.test(text)) period = 'monthly';
  else if (/ano|anual|\/ano/i.test(text)) period = 'yearly';
  else if (/hora|\/h/i.test(text)) period = 'hourly';

  const numbers = text.match(/R?\$?\s*([\d.]+)/gi) || [];
  const parsed = numbers.map(n => parseFloat(n.replace(/[^\d]/g, '')));

  if (parsed.length >= 2) {
    min = Math.min(...parsed);
    max = Math.max(...parsed);
  } else if (parsed.length === 1) {
    min = parsed[0];
  }

  return { min, max, period };
}

function detectRemoteType(text: string): string | null {
  const textLower = text.toLowerCase();
  if (/remoto|remote|home office|trabalho remoto/i.test(textLower)) return 'remote';
  if (/híbrido|hybrid/i.test(textLower)) return 'hybrid';
  return null;
}

function detectSeniority(title: string): string {
  const titleLower = title.toLowerCase();
  if (/sênior|senior|sr\.|pleno sênior/i.test(titleLower)) return 'senior';
  if (/júnior|junior|jr\.|trainee|estágio/i.test(titleLower)) return 'entry';
  if (/pleno|mid|intermediário/i.test(titleLower)) return 'mid';
  if (/staff|principal|arquiteto/i.test(titleLower)) return 'principal';
  return 'mid';
}

function extractSkills(text: string): string[] {
  const skills: string[] = [];
  const textLower = text.toLowerCase();

  const commonSkills = [
    'Python', 'Java', 'JavaScript', 'TypeScript', 'React', 'Node.js', 'Angular', 'Vue',
    'AWS', 'Azure', 'Docker', 'Kubernetes', 'PostgreSQL', 'MongoDB',
  ];

  for (const skill of commonSkills) {
    if (textLower.includes(skill.toLowerCase())) {
      skills.push(skill);
    }
  }

  return [...new Set(skills)];
}

function detectSector(title: string): string {
  const titleLower = title.toLowerCase();

  if (/\b(ai|machine learning|ml|data scien)/i.test(titleLower)) return 'AI & ML';
  if (/\b(backend|back-end)/i.test(titleLower)) return 'Backend';
  if (/\b(frontend|front-end)/i.test(titleLower)) return 'Frontend';
  if (/\b(devops|cloud|sre)/i.test(titleLower)) return 'DevOps & Cloud';

  return 'Other Tech';
}

// ========== MOCK DATA ==========

const mockJobs = [
  {
    title: 'Desenvolvedor Backend Sênior - Python/Django',
    company: 'Tech Corp Brasil',
    location: 'São Paulo - SP',
    salary: 'R$ 8.000 - R$ 12.000 / mês',
    description: 'Vaga remota para desenvolvedor Python com Django, AWS, PostgreSQL e Docker. Experiência com REST APIs e Kubernetes.',
    url: 'https://www.catho.com.br/vagas/12345678/34'
  },
  {
    title: 'Desenvolvedor Frontend Pleno - React',
    company: 'StartupXYZ',
    location: 'Rio de Janeiro - RJ',
    salary: 'R$ 6.000 / mês',
    description: 'Híbrido. Trabalhar com React, TypeScript, Node.js. Conhecimentos em AWS e MongoDB são diferenciais.',
    url: 'https://www.catho.com.br/vagas/23456789/34'
  },
  {
    title: 'Engenheiro de Machine Learning Júnior',
    company: 'AI Solutions',
    location: 'Belo Horizonte - MG',
    salary: '',
    description: 'Trabalho remoto. Python, TensorFlow, PyTorch, Scikit-learn. Experiência com dados e ML.',
    url: 'https://www.catho.com.br/vagas/34567890/34'
  }
];

// ========== MAIN ==========

async function main() {
  console.log('🧪 Test: Catho Integration - Parse Helpers + Database\n');
  console.log('='.repeat(60));

  const pool = new Pool(DB_CONFIG);

  try {
    console.log('\n📋 Testing with 3 mock jobs...\n');

    for (const job of mockJobs) {
      console.log(`\n🔹 Processing: ${job.title}`);
      console.log(`   Company: ${job.company}`);
      console.log(`   Location: ${job.location}`);

      const jobId = `catho-test-${job.url.match(/\/(\d+)\//)?.[1] || Date.now()}`;

      // Parse city and state
      const [city, state] = job.location.includes('-')
        ? job.location.split('-').map((s: string) => s.trim())
        : [null, null];

      console.log(`   City: ${city}, State: ${state}`);

      // Normalize geographic data
      const { countryId, stateId, cityId } = await normalizeLocation(pool, {
        country: 'Brazil',
        state: state,
        city: city
      });

      console.log(`   Geo IDs: country=${countryId}, state=${stateId}, city=${cityId}`);

      // Get or create organization
      const organizationId = await getOrCreateOrganization(
        pool,
        job.company,
        null,
        job.location,
        'Brazil',
        'catho'
      );

      console.log(`   Organization ID: ${organizationId}`);

      // ========== PARSE USING HELPERS ==========
      const { min: salaryMin, max: salaryMax, period: salaryPeriod } = parseSalaryBRL(job.salary);
      const remoteType = detectRemoteType(job.title + ' ' + job.description);
      const seniority = detectSeniority(job.title);
      const skills = extractSkills(job.title + ' ' + job.description);
      const sector = detectSector(job.title);

      console.log(`   Parsed Data:`);
      console.log(`     Salary: R$${salaryMin || 0} - R$${salaryMax || 0} (${salaryPeriod || 'N/A'})`);
      console.log(`     Remote: ${remoteType || 'on-site'}`);
      console.log(`     Seniority: ${seniority}`);
      console.log(`     Skills: ${skills.join(', ') || 'none detected'}`);
      console.log(`     Sector: ${sector}`);

      // Save to database
      await pool.query(
        `INSERT INTO sofia.jobs (
           job_id, title, company, location, city, state, country, country_id, state_id, city_id,
           url, platform, organization_id,
           description, salary_min, salary_max, salary_currency, salary_period,
           remote_type, seniority_level, employment_type, skills_required, sector,
           collected_at
         )
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, NOW())
         ON CONFLICT (job_id) DO UPDATE SET
           title = EXCLUDED.title,
           description = EXCLUDED.description,
           salary_min = EXCLUDED.salary_min,
           salary_max = EXCLUDED.salary_max,
           collected_at = NOW()`,
        [
          jobId, job.title, job.company, job.location, city, state, 'Brazil', countryId, stateId, cityId,
          job.url, 'catho', organizationId,
          job.description, salaryMin, salaryMax, 'BRL', salaryPeriod,
          remoteType, seniority, 'full-time', skills, sector
        ]
      );

      console.log(`   ✅ Saved to database!`);
    }

    console.log('\n\n📊 Checking database...\n');

    const result = await pool.query(`
      SELECT
        job_id, title, company, city, state,
        salary_min, salary_max, salary_period,
        remote_type, seniority_level, sector,
        array_length(skills_required, 1) as skills_count
      FROM sofia.jobs
      WHERE platform = 'catho'
      AND job_id LIKE 'catho-test-%'
      ORDER BY collected_at DESC
      LIMIT 5;
    `);

    console.log(`Found ${result.rows.length} jobs in database:\n`);
    result.rows.forEach((row, i) => {
      console.log(`${i + 1}. ${row.title}`);
      console.log(`   Company: ${row.company} | Location: ${row.city}, ${row.state}`);
      console.log(`   Salary: R$${row.salary_min || 0}-${row.salary_max || 0}/${row.salary_period || 'N/A'}`);
      console.log(`   Remote: ${row.remote_type || 'on-site'} | Seniority: ${row.seniority_level} | Sector: ${row.sector}`);
      console.log(`   Skills: ${row.skills_count || 0} detected\n`);
    });

    console.log('='.repeat(60));
    console.log('✅ ALL TESTS PASSED!\n');

  } catch (error: any) {
    console.error('\n❌ ERROR:', error.message);
    console.error(error.stack);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
