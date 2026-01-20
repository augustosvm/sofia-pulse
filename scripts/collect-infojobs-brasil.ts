#!/usr/bin/env npx tsx
/**
 * InfoJobs Brasil Collector - Sofia Pulse
 *
 * Coleta vagas tech do InfoJobs Brasil via Puppeteer (headless browser).
 * A API oficial requer OAuth2, então usamos scraping com browser.
 *
 * Features:
 * - Extrai salário quando disponível
 * - Extrai skills da descrição
 * - Detecta remote_type
 * - Detecta seniority_level
 * - Normaliza localização (city_id, state_id, country_id)
 */

import puppeteer from 'puppeteer';
import { Pool } from 'pg';
import * as dotenv from 'dotenv';
import { getKeywordsByLanguage } from './shared/keywords-config';
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

// Use unified keywords in Portuguese (Brazil)
const KEYWORDS = getKeywordsByLanguage('pt');

// Brazilian states
const BRAZILIAN_STATES: Record<string, string> = {
  'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas', 'BA': 'Bahia',
  'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo', 'GO': 'Goiás',
  'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais',
  'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná', 'PE': 'Pernambuco', 'PI': 'Piauí',
  'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte', 'RS': 'Rio Grande do Sul',
  'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina', 'SP': 'São Paulo',
  'SE': 'Sergipe', 'TO': 'Tocantins',
};

// Skill patterns
const SKILL_PATTERNS = [
  'python', 'java', 'javascript', 'typescript', 'c#', 'c\\+\\+', 'go', 'golang', 'rust', 'ruby', 'php', 'swift', 'kotlin',
  'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'spring', '.net', 'laravel',
  'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'ci/cd',
  'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
  'machine learning', 'deep learning', 'tensorflow', 'pytorch',
  'git', 'linux', 'agile', 'scrum',
];

interface InfoJobsJob {
  id: string;
  title: string;
  company: string;
  location: string;
  city: string | null;
  state: string | null;
  description: string;
  salary: string | null;
  url: string;
}

function extractSkills(text: string): string[] {
  if (!text) return [];
  const lowerText = text.toLowerCase();
  const foundSkills: string[] = [];

  for (const pattern of SKILL_PATTERNS) {
    const regex = new RegExp(`\\b${pattern}\\b`, 'i');
    if (regex.test(lowerText)) {
      let skill = pattern.replace(/\\\+/g, '+').replace(/\\\./g, '.');
      if (skill === 'golang') skill = 'go';
      foundSkills.push(skill);
    }
  }

  return [...new Set(foundSkills)];
}

function detectSeniority(title: string): string {
  const lowerTitle = title.toLowerCase();

  if (lowerTitle.includes('estágio') || lowerTitle.includes('estagiário') || lowerTitle.includes('trainee') || lowerTitle.includes('aprendiz')) return 'entry';
  if (lowerTitle.includes('junior') || lowerTitle.includes('júnior') || lowerTitle.includes('jr')) return 'entry';
  if (lowerTitle.includes('senior') || lowerTitle.includes('sênior') || lowerTitle.includes('sr') || lowerTitle.includes('pleno')) return 'senior';
  if (lowerTitle.includes('lead') || lowerTitle.includes('líder') || lowerTitle.includes('tech lead')) return 'lead';
  if (lowerTitle.includes('gerente') || lowerTitle.includes('coordenador') || lowerTitle.includes('diretor') || lowerTitle.includes('head')) return 'manager';

  return 'mid';
}

function detectRemoteType(text: string): string {
  const lowerText = text.toLowerCase();

  if (lowerText.includes('remoto') || lowerText.includes('remote') || lowerText.includes('home office') || lowerText.includes('trabalho remoto')) {
    if (lowerText.includes('híbrido') || lowerText.includes('hibrido') || lowerText.includes('hybrid')) return 'hybrid';
    return 'remote';
  }
  if (lowerText.includes('presencial') || lowerText.includes('on-site')) return 'onsite';

  return 'unknown';
}

function detectSector(title: string): string {
  const lowerTitle = title.toLowerCase();

  if (lowerTitle.includes('frontend') || lowerTitle.includes('front-end')) return 'Frontend';
  if (lowerTitle.includes('backend') || lowerTitle.includes('back-end')) return 'Backend';
  if (lowerTitle.includes('fullstack') || lowerTitle.includes('full-stack')) return 'Fullstack';
  if (lowerTitle.includes('devops') || lowerTitle.includes('sre') || lowerTitle.includes('cloud')) return 'DevOps';
  if (lowerTitle.includes('dados') || lowerTitle.includes('data') || lowerTitle.includes('bi')) return 'Data';
  if (lowerTitle.includes('machine learning') || lowerTitle.includes('ia') || lowerTitle.includes('ml')) return 'AI/ML';
  if (lowerTitle.includes('mobile') || lowerTitle.includes('android') || lowerTitle.includes('ios')) return 'Mobile';
  if (lowerTitle.includes('segurança') || lowerTitle.includes('security')) return 'Security';
  if (lowerTitle.includes('qa') || lowerTitle.includes('teste') || lowerTitle.includes('quality')) return 'QA';

  return 'Other Tech';
}

function parseSalary(salaryStr: string): { min: number | null; max: number | null } {
  if (!salaryStr) return { min: null, max: null };

  // Try to extract numbers (R$ 5.000, R$ 5.000 - R$ 8.000, etc)
  const numbers = salaryStr.match(/[\d.,]+/g);
  if (!numbers || numbers.length === 0) return { min: null, max: null };

  const cleanNumbers = numbers.map(n => {
    // Convert Brazilian format to number (5.000,00 -> 5000)
    return parseFloat(n.replace(/\./g, '').replace(',', '.'));
  });

  return {
    min: cleanNumbers[0] || null,
    max: cleanNumbers.length > 1 ? cleanNumbers[1] : cleanNumbers[0],
  };
}

function parseLocation(location: string): { city: string | null; state: string | null } {
  if (!location) return { city: null, state: null };

  // Pattern: "São Paulo - SP", "Rio de Janeiro, RJ", "Curitiba/PR"
  const match = location.match(/([A-Za-zÀ-ú\s]+)[,\-\/]\s*([A-Z]{2})/);
  if (match) {
    const city = match[1].trim();
    const stateCode = match[2];
    if (BRAZILIAN_STATES[stateCode]) {
      return { city, state: stateCode };
    }
  }

  return { city: location.trim(), state: null };
}

async function scrapeInfoJobs(keyword: string): Promise<InfoJobsJob[]> {
  const jobs: InfoJobsJob[] = [];
  let browser;

  try {
    browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--disable-gpu',
        '--window-size=1920x1080',
      ],
    });

    const page = await browser.newPage();

    // Set user agent
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');

    // Navigate to search page
    const url = `https://www.infojobs.com.br/vagas-de-emprego-${keyword.replace(/\s+/g, '-')}.aspx`;
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });

    // Wait for job listings to load
    await page.waitForSelector('[data-qa="vacancy-item"], .ij-Box-root, .vacante', { timeout: 10000 }).catch(() => { });

    // Extract job data
    const jobsData = await page.evaluate(() => {
      const items: any[] = [];

      // Try multiple selectors
      const selectors = [
        '[data-qa="vacancy-item"]',
        '.ij-Box-root',
        '.vacante',
        'article',
        '[class*="vacancy"]',
        '[class*="offer"]',
      ];

      for (const selector of selectors) {
        const elements = document.querySelectorAll(selector);
        if (elements.length > 0) {
          elements.forEach((el) => {
            const titleEl = el.querySelector('[data-qa="vacancy-title"], h2, h3, .title, [class*="title"]');
            const companyEl = el.querySelector('[data-qa="vacancy-company"], [class*="company"], [class*="empresa"]');
            const locationEl = el.querySelector('[data-qa="vacancy-location"], [class*="location"], [class*="local"]');
            const salaryEl = el.querySelector('[data-qa="vacancy-salary"], [class*="salary"], [class*="salario"]');
            const linkEl = el.querySelector('a[href*="oferta"]') || el.querySelector('a');

            const title = titleEl?.textContent?.trim();
            const company = companyEl?.textContent?.trim();
            const location = locationEl?.textContent?.trim();
            const salary = salaryEl?.textContent?.trim();
            const link = linkEl?.getAttribute('href');

            if (title && title.length > 3) {
              items.push({ title, company, location, salary, link });
            }
          });
          if (items.length > 0) break;
        }
      }

      return items;
    });

    for (const data of jobsData) {
      const id = `infojobs-${Buffer.from(data.link || data.title + data.company).toString('base64').substring(0, 20)}`;
      const { city, state } = parseLocation(data.location || '');

      jobs.push({
        id,
        title: data.title,
        company: data.company || 'Confidencial',
        location: data.location || '',
        city,
        state,
        description: '',
        salary: data.salary,
        url: data.link?.startsWith('http') ? data.link : `https://www.infojobs.com.br${data.link || ''}`,
      });
    }

  } catch (error: any) {
    console.error(`   ❌ Error scraping ${keyword}: ${error.message}`);
  } finally {
    if (browser) await browser.close();
  }

  return jobs;
}

async function collectInfoJobsBrasil(): Promise<void> {
  console.log('🇧🇷 InfoJobs Brasil Collector (Puppeteer)');
  console.log('='.repeat(60));
  console.log(`📋 ${KEYWORDS.length} keywords to search`);
  console.log('');

  const pool = new Pool(dbConfig);
  let totalCollected = 0;
  let totalSaved = 0;
  const seenIds = new Set<string>();

  try {
    for (const keyword of KEYWORDS) {
      console.log(`   📋 ${keyword}...`);
      const jobs = await scrapeInfoJobs(keyword);
      console.log(`      ✅ ${jobs.length} vagas`);

      for (const job of jobs) {
        // Skip duplicates
        if (seenIds.has(job.id)) continue;
        seenIds.add(job.id);

        try {
          totalCollected++;

          // Normalize location
          const { countryId, stateId, cityId } = await normalizeLocation(pool, job.location, 'Brazil');

          // Get or create organization
          const organizationId = job.company !== 'Confidencial'
            ? await getOrCreateOrganization(pool, job.company, 'Brazil')
            : null;

          // Extract skills
          const skills = extractSkills(`${job.title} ${job.description}`);

          // Detect attributes
          const remoteType = detectRemoteType(`${job.title} ${job.location}`);
          const seniority = detectSeniority(job.title);
          const sector = detectSector(job.title);

          // Parse salary
          const { min: salaryMin, max: salaryMax } = parseSalary(job.salary || '');

          await pool.query(`
            INSERT INTO sofia.jobs (
              job_id, title, company, raw_location, raw_city, raw_state, country,
              country_id, state_id, city_id,
              url, platform, source, organization_id,
              description, salary_min, salary_max, salary_currency, salary_period,
              remote_type, seniority_level, employment_type, skills_required, sector,
              collected_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, NOW())
            ON CONFLICT (job_id) DO UPDATE SET
              title = EXCLUDED.title,
              raw_location = EXCLUDED.raw_location,
              source = EXCLUDED.source,
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
              collected_at = NOW()
          `, [
            job.id,
            job.title.substring(0, 500),
            job.company,
            job.location,
            job.city,
            job.state,
            'Brazil',
            countryId,
            stateId,
            cityId,
            job.url,
            'infojobs-br',
            'infojobs',
            organizationId,
            job.description?.substring(0, 10000) || null,
            salaryMin,
            salaryMax,
            'BRL',
            'month',
            remoteType,
            seniority,
            'full-time',
            skills.length > 0 ? `{${skills.join(',')}}` : null,
            sector
          ]);

          totalSaved++;
        } catch (error: any) {
          if (error.code !== '23505') { // Ignore duplicate errors
            console.error(`   ⚠️ Error saving job: ${error.message}`);
          }
        }
      }

      // Rate limiting - 5 seconds between keywords (to avoid blocking)
      await new Promise(resolve => setTimeout(resolve, 5000));
    }

    console.log('');
    console.log('='.repeat(60));
    console.log('✅ InfoJobs Brasil collection complete!');
    console.log(`   📊 Total collected: ${totalCollected}`);
    console.log(`   💾 Total saved: ${totalSaved}`);
    console.log('='.repeat(60));

  } finally {
    await pool.end();
  }
}

// Run
collectInfoJobsBrasil().catch(console.error);
