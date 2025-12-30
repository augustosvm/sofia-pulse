#!/usr/bin/env tsx
import { Pool } from 'pg';
import * as dotenv from 'dotenv';
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import { getKeywordsByLanguage } from './shared/keywords-config';
import { normalizeLocation } from './shared/geo-helpers.js';
import { getOrCreateOrganization } from './shared/org-helpers.js';

dotenv.config();
puppeteer.use(StealthPlugin());

const delay = (ms: number) => new Promise(r => setTimeout(r, ms));

const DB_CONFIG = {
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD || 'sofia123strong',
  database: process.env.POSTGRES_DB || 'sofia_db',
};

// ========== PARSE HELPERS (from collect-catho-stealth.ts) ==========

function parseSalaryBRL(text: string): { min: number | null; max: number | null; period: string | null } {
  let min: number | null = null;
  let max: number | null = null;
  let period: string | null = null;

  if (!text) return { min, max, period };

  // Detectar período
  if (/mês|mensal|\/mês/i.test(text)) period = 'monthly';
  else if (/ano|anual|\/ano/i.test(text)) period = 'yearly';
  else if (/hora|\/h/i.test(text)) period = 'hourly';

  // Extrair números (ex: "R$ 5.000 - R$ 8.000" ou "até R$ 10.000")
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
    'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'SQL', 'PostgreSQL', 'MongoDB', 'MySQL',
    'Git', 'CI/CD', 'Scrum', 'Agile', 'REST API', 'GraphQL', 'Redis', 'Kafka',
    'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn',
    'Spring', 'Django', 'Flask', 'FastAPI', 'Express',
    'HTML', 'CSS', 'Sass', 'Tailwind', 'Bootstrap',
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

  if (/\b(ai|machine learning|ml|data scien|deep learning)/i.test(titleLower)) return 'AI & ML';
  if (/\b(security|segurança|infosec|cyber)/i.test(titleLower)) return 'Security';
  if (/\b(devops|cloud|sre|infrastructure)/i.test(titleLower)) return 'DevOps & Cloud';
  if (/\b(gerente|manager|líder|coordenador|cto|cio|director)/i.test(titleLower)) return 'Leadership';
  if (/\b(backend|back-end)/i.test(titleLower)) return 'Backend';
  if (/\b(frontend|front-end)/i.test(titleLower)) return 'Frontend';
  if (/\b(mobile|ios|android|react native|flutter)/i.test(titleLower)) return 'Mobile';
  if (/\b(data engineer|dados|etl|pipeline)/i.test(titleLower)) return 'Data Engineering';
  if (/\b(qa|quality|test|tester)/i.test(titleLower)) return 'QA & Testing';
  if (/\b(product|product manager|pm)/i.test(titleLower)) return 'Product';

  return 'Other Tech';
}

async function scrapeCatho(keywords: string[]) {
  const browser = await puppeteer.launch({
    headless: 'new',
    // Use bundled Chromium (auto-detected by puppeteer)
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  const jobs: any[] = [];

  try {
    const page = await browser.newPage();

    for (const keyword of keywords) {
      console.log(`   📋 ${keyword}`);

      await page.goto(`https://www.catho.com.br/vagas/${keyword.toLowerCase().replace(/\s+/g, '-')}/`, {
        waitUntil: 'networkidle0',
        timeout: 60000,
      });

      await delay(8000);

      const pageJobs = await page.evaluate(() => {
        const results: any[] = [];
        const jobLinks = document.querySelectorAll('a[href*="/vagas/"][href*="/34"]');

        jobLinks.forEach((link, i) => {
          if (i >= 20) return;

          const href = link.getAttribute('href');
          const title = link.textContent?.trim() || '';

          // Try to find parent container with more info
          let parent: any = link.parentElement;
          let company = '';
          let location = '';
          let salary = '';
          let description = '';

          // Walk up to find company/location/salary/description
          for (let j = 0; j < 5; j++) {
            if (!parent) break;

            const text = parent.textContent || '';

            // Look for location patterns (cidade - UF)
            const locMatch = text.match(/([A-Z][a-zà-ú\s]+)\s*-\s*([A-Z]{2})/);
            if (locMatch && !location) {
              location = locMatch[0];
            }

            // Look for company name (often in a specific class/tag)
            const companyEl = parent.querySelector('.company-name, [data-testid="company-name"], .job-company');
            if (companyEl && !company) {
              company = companyEl.textContent?.trim() || '';
            }

            // Look for salary
            const salaryEl = parent.querySelector('.salary, [data-testid="salary"], .job-salary');
            if (salaryEl && !salary) {
              salary = salaryEl.textContent?.trim() || '';
            }

            // Look for description
            const descEl = parent.querySelector('.job-description, .description-preview, .description');
            if (descEl && !description) {
              description = descEl.textContent?.trim() || '';
            }

            parent = parent.parentElement;
          }

          if (href && title && !href.includes('anunciar')) {
            results.push({
              url: href.startsWith('http') ? href : `https://www.catho.com.br${href}`,
              title,
              location: location || 'Brasil',
              company: company || 'Unknown',
              salary: salary || '',
              description: description || '',
            });
          }
        });

        return results;
      });

      jobs.push(...pageJobs);
      console.log(`      ✅ ${pageJobs.length} vagas`);
      await delay(Math.random() * 3000 + 5000);
    }

  } finally {
    await browser.close();
  }

  return jobs;
}

async function main() {
  console.log('🚀 Catho Scraper - Centralized Keywords');
  console.log('='.repeat(50));

  const pool = new Pool(DB_CONFIG);

  // Ensure unified jobs table exists
  await pool.query(`
    CREATE TABLE IF NOT EXISTS sofia.jobs (
      id SERIAL PRIMARY KEY,
      job_id VARCHAR(500) UNIQUE,
      title VARCHAR(500),
      company VARCHAR(300),
      location VARCHAR(300),
      city VARCHAR(200),
      state VARCHAR(100),
      description TEXT,
      url TEXT,
      platform VARCHAR(100),
      posted_date VARCHAR(100),
      salary_min NUMERIC,
      salary_max NUMERIC,
      search_keyword VARCHAR(200),
      collected_at TIMESTAMPTZ DEFAULT NOW()
    );
  `);

  // Usar keywords centralizadas em português (Brasil)
  const keywords = getKeywordsByLanguage('pt');
  console.log(`📋 Total de keywords: ${keywords.length}`);

  const jobs = await scrapeCatho(keywords);

  for (const job of jobs) {
    const jobId = `catho-${job.url.match(/\/(\d+)\//)?.[1] || Date.now()}`;

    // Parse city and state
    const [city, state] = job.location.includes('-')
      ? job.location.split('-').map((s: string) => s.trim())
      : [null, null];

    // Normalize geographic data
    const { countryId, stateId, cityId } = await normalizeLocation(pool, {
      country: 'Brazil',
      state: state,
      city: city
    });

    // Get or create organization
    const organizationId = await getOrCreateOrganization(
      pool,
      job.company,
      null,
      job.location,
      'Brazil',
      'catho'
    );

    // ========== PARSE USING HELPERS ==========
    const { min: salaryMin, max: salaryMax, period: salaryPeriod } = parseSalaryBRL(job.salary);
    const remoteType = detectRemoteType(job.title + ' ' + job.description);
    const seniority = detectSeniority(job.title);
    const skills = extractSkills(job.title + ' ' + job.description);
    const sector = detectSector(job.title);

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
         location = EXCLUDED.location,
         description = EXCLUDED.description,
         salary_min = EXCLUDED.salary_min,
         salary_max = EXCLUDED.salary_max,
         salary_period = EXCLUDED.salary_period,
         remote_type = EXCLUDED.remote_type,
         seniority_level = EXCLUDED.seniority_level,
         skills_required = EXCLUDED.skills_required,
         sector = EXCLUDED.sector,
         organization_id = COALESCE(EXCLUDED.organization_id, sofia.jobs.organization_id),
         country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
         state_id = COALESCE(EXCLUDED.state_id, sofia.jobs.state_id),
         city_id = COALESCE(EXCLUDED.city_id, sofia.jobs.city_id),
         collected_at = NOW()`,
      [
        jobId, job.title, job.company, job.location, city, state, 'Brazil', countryId, stateId, cityId,
        job.url, 'catho', organizationId,
        job.description, salaryMin, salaryMax, 'BRL', salaryPeriod,
        remoteType, seniority, 'full-time', skills, sector
      ]
    );
  }

  console.log(`\n✅ Saved ${jobs.length} jobs!`);
  await pool.end();
}

main();
