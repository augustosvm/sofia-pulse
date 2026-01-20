#!/usr/bin/env npx tsx
/**
 * Greenhouse Jobs Collector - Sofia Pulse
 *
 * Coleta vagas das maiores tech companies que usam Greenhouse ATS.
 * API pública, sem auth necessário.
 *
 * Melhorias vs versão anterior:
 * - Extrai salário quando disponível
 * - Extrai skills do conteúdo usando NLP
 * - Detecta remote_type
 * - Detecta seniority_level
 * - Normaliza localização (city_id, state_id, country_id)
 */

import axios from 'axios';
import { Pool } from 'pg';
import * as dotenv from 'dotenv';
import { normalizeLocation, getOrCreateCity } from './shared/geo-helpers.js';
import { getOrCreateOrganization } from './shared/org-helpers.js';

dotenv.config();

const dbConfig = {
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD,
  database: process.env.POSTGRES_DB || 'sofia_db',
};

// Top tech companies using Greenhouse (expanded list)
const TECH_COMPANIES = [
  // Big Tech & Unicorns
  'airbnb', 'stripe', 'gitlab', 'coinbase', 'dropbox', 'doordash',
  'notion', 'airtable', 'figma', 'vercel', 'netlify', 'hashicorp',
  'carta', 'databricks', 'redis', 'fastly', 'sourcegraph', 'sentry',
  'postman', 'grammarly', 'amplitude', 'segment', 'miro', 'canva',
  'gusto', 'intercom', 'asana', 'webflow', 'loom', 'calendly',
  // AI/ML Companies
  'openai', 'anthropic', 'huggingface', 'cohere', 'replicate', 'weights-and-biases',
  // Fintech
  'brex', 'ramp', 'mercury', 'plaid', 'affirm', 'chime',
  // Developer Tools
  'supabase', 'planetscale', 'railway', 'render', 'fly', 'deno',
  // Security
  '1password', 'snyk', 'lacework', 'crowdstrike',
];

// Skill patterns for NLP extraction
const SKILL_PATTERNS = [
  // Languages
  'python', 'java', 'javascript', 'typescript', 'go', 'golang', 'rust', 'ruby', 'php', 'c\\+\\+', 'c#', 'swift', 'kotlin', 'scala',
  // Frontend
  'react', 'vue', 'angular', 'svelte', 'next\\.js', 'nextjs', 'nuxt', 'remix',
  // Backend
  'node', 'express', 'django', 'flask', 'rails', 'spring', 'fastapi', 'graphql',
  // Cloud & DevOps
  'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'k8s', 'terraform', 'ansible', 'jenkins', 'ci/cd',
  // Data
  'sql', 'postgresql', 'postgres', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'kafka', 'spark', 'airflow', 'dbt',
  // AI/ML
  'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'nlp', 'llm', 'computer vision',
  // Other
  'git', 'linux', 'agile', 'scrum',
];

interface GreenhouseJob {
  id: number;
  title: string;
  content?: string;
  location?: {
    name: string;
  };
  departments?: Array<{ name: string }>;
  absolute_url?: string;
  updated_at?: string;
  metadata?: Array<{
    name: string;
    value: string | number;
  }>;
}

function extractSkills(text: string): string[] {
  if (!text) return [];
  const lowerText = text.toLowerCase();
  const foundSkills: string[] = [];

  for (const pattern of SKILL_PATTERNS) {
    const regex = new RegExp(`\\b${pattern}\\b`, 'i');
    if (regex.test(lowerText)) {
      // Normalize skill name
      let skill = pattern.replace(/\\\+/g, '+').replace(/\\\./g, '.');
      if (skill === 'golang') skill = 'go';
      if (skill === 'k8s') skill = 'kubernetes';
      if (skill === 'postgres') skill = 'postgresql';
      if (skill === 'nextjs') skill = 'next.js';
      foundSkills.push(skill);
    }
  }

  return [...new Set(foundSkills)]; // Remove duplicates
}

function detectSeniority(title: string): string {
  const lowerTitle = title.toLowerCase();

  if (lowerTitle.includes('intern') || lowerTitle.includes('trainee') || lowerTitle.includes('entry')) return 'entry';
  if (lowerTitle.includes('junior') || lowerTitle.includes('jr.') || lowerTitle.includes('jr ')) return 'entry';
  if (lowerTitle.includes('senior') || lowerTitle.includes('sr.') || lowerTitle.includes('sr ')) return 'senior';
  if (lowerTitle.includes('staff')) return 'staff';
  if (lowerTitle.includes('principal')) return 'principal';
  if (lowerTitle.includes('lead') || lowerTitle.includes('tech lead')) return 'lead';
  if (lowerTitle.includes('manager') || lowerTitle.includes('director') || lowerTitle.includes('head of') || lowerTitle.includes('vp ')) return 'manager';
  if (lowerTitle.includes('architect')) return 'architect';

  return 'mid';
}

function detectRemoteType(location: string, title: string, content: string): string {
  const text = `${location} ${title} ${content}`.toLowerCase();

  if (text.includes('remote') || text.includes('anywhere') || text.includes('work from home')) {
    if (text.includes('hybrid')) return 'hybrid';
    return 'remote';
  }
  if (text.includes('on-site') || text.includes('onsite') || text.includes('in-office')) return 'onsite';

  return 'unknown';
}

function detectSector(title: string, departments: string[]): string {
  const text = `${title} ${departments.join(' ')}`.toLowerCase();

  if (text.includes('frontend') || text.includes('front-end') || text.includes('ui ')) return 'Frontend';
  if (text.includes('backend') || text.includes('back-end') || text.includes('api')) return 'Backend';
  if (text.includes('fullstack') || text.includes('full-stack') || text.includes('full stack')) return 'Fullstack';
  if (text.includes('devops') || text.includes('sre') || text.includes('infrastructure') || text.includes('platform')) return 'DevOps';
  if (text.includes('data') || text.includes('analytics') || text.includes('bi ')) return 'Data';
  if (text.includes('machine learning') || text.includes('ml ') || text.includes('ai ')) return 'AI/ML';
  if (text.includes('mobile') || text.includes('ios') || text.includes('android')) return 'Mobile';
  if (text.includes('security') || text.includes('infosec')) return 'Security';
  if (text.includes('qa') || text.includes('quality') || text.includes('test')) return 'QA';
  if (text.includes('design') || text.includes('ux')) return 'Design';

  return 'Engineering';
}

function parseLocation(location: string): { city: string | null; state: string | null; country: string } {
  if (!location) return { city: null, state: null, country: 'United States' };

  // Common patterns: "San Francisco, CA", "New York, NY, USA", "Remote - US"
  const parts = location.split(/[,;]/);
  const city = parts[0]?.trim() || null;
  const state = parts[1]?.trim() || null;

  // Detect country
  let country = 'United States';
  const lowerLoc = location.toLowerCase();
  if (lowerLoc.includes('uk') || lowerLoc.includes('london') || lowerLoc.includes('united kingdom')) country = 'United Kingdom';
  else if (lowerLoc.includes('canada') || lowerLoc.includes('toronto') || lowerLoc.includes('vancouver')) country = 'Canada';
  else if (lowerLoc.includes('germany') || lowerLoc.includes('berlin') || lowerLoc.includes('munich')) country = 'Germany';
  else if (lowerLoc.includes('ireland') || lowerLoc.includes('dublin')) country = 'Ireland';
  else if (lowerLoc.includes('remote')) country = 'Remote';

  return { city, state, country };
}

export async function collectGreenhouseJobs(): Promise<void> {
  console.log('🏢 Greenhouse Jobs Collector');
  console.log('='.repeat(60));
  console.log(`📋 ${TECH_COMPANIES.length} companies to scrape`);
  console.log('');

  const pool = new Pool(dbConfig);
  let totalCollected = 0;
  let totalSaved = 0;
  let totalErrors = 0;

  try {
    for (const company of TECH_COMPANIES) {
      try {
        const url = `https://boards-api.greenhouse.io/v1/boards/${company}/jobs?content=true`;

        const response = await axios.get<{ jobs: GreenhouseJob[] }>(url, {
          headers: {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (compatible; SofiaPulse/2.0)',
          },
          timeout: 15000,
        });

        const jobs = response.data.jobs || [];
        console.log(`   📋 ${company}: ${jobs.length} jobs`);
        totalCollected += jobs.length;

        for (const job of jobs) {
          try {
            if (!job.title || !job.id) continue;

            const jobId = `greenhouse-${job.id}`;
            const location = job.location?.name || 'Remote';
            const content = job.content || '';
            const departments = job.departments?.map(d => d.name) || [];

            // Parse location
            const { city, state, country } = parseLocation(location);

            // Normalize geographic data
            const { countryId, stateId, cityId } = await normalizeLocation(pool, location, country);

            // Get or create organization
            const organizationId = await getOrCreateOrganization(pool, company, country);

            // Extract skills from content
            const skills = extractSkills(`${job.title} ${content}`);

            // Detect attributes
            const remoteType = detectRemoteType(location, job.title, content);
            const seniority = detectSeniority(job.title);
            const sector = detectSector(job.title, departments);

            // Check for salary in metadata
            let salaryMin: number | null = null;
            let salaryMax: number | null = null;
            let salaryCurrency = 'USD';

            if (job.metadata) {
              for (const meta of job.metadata) {
                if (meta.name.toLowerCase().includes('salary') && typeof meta.value === 'number') {
                  if (meta.name.toLowerCase().includes('min')) salaryMin = meta.value;
                  if (meta.name.toLowerCase().includes('max')) salaryMax = meta.value;
                }
              }
            }

            // Parse date
            let postedDate = null;
            if (job.updated_at) {
              postedDate = new Date(job.updated_at).toISOString().split('T')[0];
            }

            await pool.query(`
              INSERT INTO sofia.jobs (
                job_id, title, company, location, city, state, country,
                country_id, state_id, city_id,
                url, platform, organization_id,
                description, salary_min, salary_max, salary_currency, salary_period,
                remote_type, seniority_level, employment_type, skills_required, sector,
                posted_date, collected_at
              )
              VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, NOW())
              ON CONFLICT (job_id, platform) DO UPDATE SET
                title = EXCLUDED.title,
                location = EXCLUDED.location,
                description = EXCLUDED.description,
                salary_min = COALESCE(EXCLUDED.salary_min, sofia.jobs.salary_min),
                salary_max = COALESCE(EXCLUDED.salary_max, sofia.jobs.salary_max),
                remote_type = EXCLUDED.remote_type,
                seniority_level = EXCLUDED.seniority_level,
                skills_required = EXCLUDED.skills_required,
                sector = EXCLUDED.sector,
                organization_id = COALESCE(EXCLUDED.organization_id, sofia.jobs.organization_id),
                country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
                state_id = COALESCE(EXCLUDED.state_id, sofia.jobs.state_id),
                city_id = COALESCE(EXCLUDED.city_id, sofia.jobs.city_id),
                posted_date = EXCLUDED.posted_date,
                collected_at = NOW()
            `, [
              jobId,
              job.title.substring(0, 500),
              company,
              location,
              city,
              state,
              country,
              countryId,
              stateId,
              cityId,
              job.absolute_url || `https://boards.greenhouse.io/${company}/jobs/${job.id}`,
              'greenhouse',
              organizationId,
              content.substring(0, 10000),
              salaryMin,
              salaryMax,
              salaryCurrency,
              'year',
              remoteType,
              seniority,
              'full-time',
              skills.length > 0 ? `{${skills.join(',')}}` : null,
              sector,
              postedDate
            ]);

            totalSaved++;
          } catch (error: any) {
            if (error.code !== '23505') { // Ignore duplicate errors
              totalErrors++;
            }
          }
        }

        // Rate limiting - 1 second between companies
        await new Promise(resolve => setTimeout(resolve, 1000));

      } catch (error: any) {
        if (error.response?.status === 404) {
          // Company doesn't have Greenhouse board
          console.log(`   ⚠️  ${company}: No Greenhouse board`);
        } else {
          console.error(`   ❌ ${company}: ${error.message}`);
          totalErrors++;
        }
      }
    }

    console.log('');
    console.log('='.repeat(60));
    console.log('✅ Greenhouse collection complete!');
    console.log(`   📊 Total collected: ${totalCollected}`);
    console.log(`   💾 Total saved: ${totalSaved}`);
    console.log(`   ⚠️  Errors: ${totalErrors}`);
    console.log('='.repeat(60));

  } finally {
    await pool.end();
  }
}

// Run if executed directly
if (require.main === module) {
  collectGreenhouseJobs().catch(console.error);
}
