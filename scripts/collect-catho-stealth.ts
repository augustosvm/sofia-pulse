#!/usr/bin/env tsx

/**
 * Sofia Pulse - Catho Jobs Scraper (Stealth Mode)
 *
 * Website: https://www.catho.com.br/
 * Técnicas anti-detecção:
 * - Puppeteer-extra com stealth plugin
 * - User agents rotativos
 * - Delays aleatórios (5-10s entre páginas)
 * - Scroll simulation (comportamento humano)
 * - Limite de páginas (máx 20)
 * - Rate limiting agressivo
 *
 * Keywords: Tech jobs em todo Brasil + LATAM
 */

import { Client } from 'pg';
import { normalizeLocation } from './shared/geo-helpers';
import * as dotenv from 'dotenv';
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import { TECH_KEYWORDS_EXPANDED } from './job-keywords-expanded';

dotenv.config();

// Apply stealth plugin
puppeteer.use(StealthPlugin());

const DB_CONFIG = {
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD || 'sofia123strong',
  database: process.env.POSTGRES_DB || 'sofia_db',
};

interface CathoJob {
  job_id: string;
  platform: string;
  title: string;
  company: string;
  location: string;
  city: string | null;
  country: string;
  remote_type: string | null;
  description: string;
  posted_date: Date | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  salary_period: string | null;
  employment_type: string;
  seniority_level: string;
  skills_required: string[];
  url: string;
  job_niche: string;
}

// User agents rotativos
const USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
];

function randomDelay(min: number, max: number): Promise<void> {
  const delay = Math.floor(Math.random() * (max - min + 1)) + min;
  return new Promise(resolve => setTimeout(resolve, delay));
}

function getRandomUserAgent(): string {
  return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

/**
 * Scrape Catho.com.br
 * Busca por keywords tech em todo Brasil
 */
async function scrapeCatho(keywords: string[], maxPagesPerKeyword: number = 3): Promise<CathoJob[]> {
  console.log('   🔍 [Catho] Iniciando scraper stealth...');
  console.log(`   🎯 Keywords: ${keywords.length} | Máx páginas: ${maxPagesPerKeyword}`);

  const browser = await puppeteer.launch({
    headless: 'new', // Headless mode
    executablePath: '/usr/bin/chromium-browser', // Use system Chromium
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--disable-gpu',
      '--window-size=1920x1080',
      '--user-agent=' + getRandomUserAgent(),
    ],
  });

  const jobs: CathoJob[] = [];
  let totalCollected = 0;

  try {
    const page = await browser.newPage();

    // Set viewport and extra headers
    await page.setViewport({ width: 1920, height: 1080 });
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    });

    // Processar primeiras 10 keywords (limite para não sobrecarregar)
    const keywordsToProcess = keywords.slice(0, 10);

    for (const keyword of keywordsToProcess) {
      try {
        console.log(`      📋 Buscando: "${keyword}"`);

        // Catho search URL
        const searchUrl = `https://www.catho.com.br/vagas/${encodeURIComponent(keyword.toLowerCase().replace(/\s+/g, '-'))}/?page=1`;

        await page.goto(searchUrl, {
          waitUntil: 'networkidle2',
          timeout: 30000,
        });

        // Simulate human behavior: scroll
        await page.evaluate(() => {
          window.scrollTo(0, document.body.scrollHeight / 2);
        });
        await randomDelay(1000, 2000);

        // Extract job listings
        const pageJobs = await page.evaluate((kw) => {
          const results: any[] = [];

          // Catho usa diferentes seletores dependendo do layout
          const jobCards = document.querySelectorAll('article[data-testid="job-card"], .job-item, .sc-job-card');

          jobCards.forEach((card, index) => {
            if (index >= 20) return; // Limite de 20 por página

            try {
              // Título
              const titleEl = card.querySelector('h2, .job-title, [data-testid="job-title"]');
              const title = titleEl?.textContent?.trim() || '';

              // Company
              const companyEl = card.querySelector('.company-name, [data-testid="company-name"], .job-company');
              const company = companyEl?.textContent?.trim() || 'Unknown';

              // Location
              const locationEl = card.querySelector('.job-location, [data-testid="location"], .location');
              const location = locationEl?.textContent?.trim() || 'Brasil';

              // URL
              const linkEl = card.querySelector('a[href*="/vagas/"], a[data-testid="job-card-link"]');
              const url = linkEl?.getAttribute('href') || '';

              // Salary (se existir)
              const salaryEl = card.querySelector('.salary, [data-testid="salary"], .job-salary');
              const salaryText = salaryEl?.textContent?.trim() || '';

              // Description preview
              const descEl = card.querySelector('.job-description, .description-preview');
              const description = descEl?.textContent?.trim() || '';

              if (title && url) {
                results.push({
                  title,
                  company,
                  location,
                  url: url.startsWith('http') ? url : `https://www.catho.com.br${url}`,
                  salaryText,
                  description,
                  keyword: kw,
                });
              }
            } catch (err) {
              console.error('Erro extraindo job card:', err);
            }
          });

          return results;
        }, keyword);

        // Processar jobs extraídos
        for (const jobData of pageJobs) {
          // Parse salary
          const { min, max, period } = parseSalaryBRL(jobData.salaryText);

          // Parse location
          const { city, state } = parseLocationBR(jobData.location);

          // Detectar remote
          const remoteType = detectRemoteType(jobData.title + ' ' + jobData.description);

          // Generate unique ID
          const jobId = `catho-${Buffer.from(jobData.url).toString('base64').substring(0, 40)}`;

          const job: CathoJob = {
            job_id: jobId,
            platform: 'catho',
            title: jobData.title,
            company: jobData.company,
            location: jobData.location,
            city: city,
            country: 'Brasil',
            remote_type: remoteType,
            description: jobData.description,
            posted_date: null, // Catho não mostra data facilmente
            salary_min: min,
            salary_max: max,
            salary_currency: 'BRL',
            salary_period: period,
            employment_type: 'full-time',
            seniority_level: detectSeniority(jobData.title),
            skills_required: extractSkills(jobData.title + ' ' + jobData.description),
            url: jobData.url,
            job_niche: detectNiche(jobData.title),
          };

          jobs.push(job);
          totalCollected++;
        }

        console.log(`         ✅ ${pageJobs.length} vagas`);

        // Delay entre keywords (5-10s) - IMPORTANTE PARA NÃO SER BLOQUEADO
        await randomDelay(5000, 10000);

      } catch (error: any) {
        console.error(`         ❌ Erro em "${keyword}":`, error.message);
        await randomDelay(3000, 5000); // Delay mesmo em erro
      }
    }

    await page.close();

  } catch (error: any) {
    console.error(`      ❌ [Catho] Erro geral:`, error.message);
  } finally {
    await browser.close();
  }

  console.log(`      ✅ Total: ${totalCollected} vagas tech`);
  return jobs;
}

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

function parseLocationBR(location: string): { city: string | null; state: string | null } {
  if (!location) return { city: null, state: null };

  // Formato comum: "São Paulo, SP" ou "São Paulo - SP"
  const parts = location.split(/[,-]/).map(p => p.trim());

  if (parts.length >= 2) {
    return { city: parts[0], state: parts[1] };
  }

  return { city: parts[0], state: null };
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
    'Python', 'Java', 'JavaScript', 'TypeScript', 'React', 'Node.js', 'Angular',
    'AWS', 'Azure', 'Docker', 'Kubernetes', 'SQL', 'PostgreSQL', 'MongoDB',
    'Git', 'CI/CD', 'Scrum', 'Agile', 'REST API', 'GraphQL',
  ];

  for (const skill of commonSkills) {
    if (textLower.includes(skill.toLowerCase())) {
      skills.push(skill);
    }
  }

  return [...new Set(skills)];
}

function detectNiche(title: string): string {
  const titleLower = title.toLowerCase();

  if (/\b(ai|machine learning|ml|data scien)/i.test(titleLower)) return 'AI & ML';
  if (/\b(security|segurança|infosec)/i.test(titleLower)) return 'Security';
  if (/\b(devops|cloud|sre)/i.test(titleLower)) return 'DevOps & Cloud';
  if (/\b(gerente|manager|líder|coordenador|cto|cio)/i.test(titleLower)) return 'Liderança';
  if (/\b(backend|back-end)/i.test(titleLower)) return 'Backend';
  if (/\b(frontend|front-end)/i.test(titleLower)) return 'Frontend';
  if (/\b(mobile|ios|android)/i.test(titleLower)) return 'Mobile';
  if (/\b(data engineer|dados)/i.test(titleLower)) return 'Data Engineering';

  return 'Other Tech';
}

async function createTables(client: Client): Promise<void> {
  await client.query(`
    CREATE TABLE IF NOT EXISTS sofia.catho_jobs (
      id SERIAL PRIMARY KEY,
      job_id VARCHAR(200) UNIQUE NOT NULL,
      platform VARCHAR(50) NOT NULL,
      title VARCHAR(300) NOT NULL,
      company VARCHAR(200),
      location VARCHAR(300),
      city VARCHAR(100),
      country VARCHAR(100),
      remote_type VARCHAR(20),
      description TEXT,
      posted_date TIMESTAMPTZ,
      salary_min NUMERIC(12, 2),
      salary_max NUMERIC(12, 2),
      salary_currency VARCHAR(10),
      salary_period VARCHAR(20),
      employment_type VARCHAR(50),
      seniority_level VARCHAR(50),
      skills_required TEXT[],
      url TEXT,
      job_niche VARCHAR(100),
      collected_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_catho_jobs_city ON sofia.catho_jobs(city);
    CREATE INDEX IF NOT EXISTS idx_catho_jobs_niche ON sofia.catho_jobs(job_niche);
    CREATE INDEX IF NOT EXISTS idx_catho_jobs_remote ON sofia.catho_jobs(remote_type);
  `);

  console.log('✅ Tables ready');
}

async function upsertJob(client: Client, job: CathoJob): Promise<void> {
  await client.query(
    `
    INSERT INTO sofia.catho_jobs (
      job_id, platform, title, company, location, city, country, remote_type,
      description, posted_date, salary_min, salary_max, salary_currency, salary_period,
      employment_type, seniority_level, skills_required, url, job_niche
    , country_id)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
    ON CONFLICT (job_id) DO UPDATE SET
      title = EXCLUDED.title,
      description = EXCLUDED.description,
      salary_min = EXCLUDED.salary_min,
      salary_max = EXCLUDED.salary_max,
      collected_at = NOW()
    `,
    [
      job.job_id, job.platform, job.title, job.company, job.location, job.city,
      job.country, job.remote_type, job.description, job.posted_date,
      job.salary_min, job.salary_max, job.salary_currency, job.salary_period,
      job.employment_type, job.seniority_level, job.skills_required, job.url, job.job_niche,
    ]
  );
}

async function main() {
  console.log('🚀 Sofia Pulse - Catho Scraper (Stealth Mode)');
  console.log('='.repeat(60));
  console.log('');

  const client = new Client(DB_CONFIG);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');
    console.log('');

    await createTables(client);
    console.log('');

    // Selecionar keywords mais relevantes para o Brasil
    const brazilKeywords = [
      'Desenvolvedor',
      'Developer',
      'DevOps',
      'Cientista de Dados',
      'Gerente de TI',
      'Coordenador de TI',
      'Analista de Sistemas',
      'Engenheiro de Software',
      'Product Manager',
      'Scrum Master',
    ];

    const jobs = await scrapeCatho(brazilKeywords, 3);

    for (const job of jobs) {
      await upsertJob(client, job);
    }

    console.log('');
    console.log(`✅ Total salvo: ${jobs.length} vagas`);
    console.log('');

    // Stats
    const stats = await client.query(`
      SELECT
        COUNT(*) as total_jobs,
        COUNT(DISTINCT city) as cities,
        COUNT(DISTINCT job_niche) as niches,
        COUNT(*) FILTER (WHERE salary_min IS NOT NULL) as jobs_with_salary,
        ROUND(AVG(salary_min)) as avg_salary_min,
        COUNT(*) FILTER (WHERE remote_type = 'remote') as remote_jobs
      FROM sofia.catho_jobs
      WHERE collected_at >= NOW() - INTERVAL '7 days';
    `);

    const row = stats.rows[0];
    console.log('📊 Estatísticas (últimos 7 dias):');
    console.log(`   Total: ${row.total_jobs}`);
    console.log(`   Cidades: ${row.cities}`);
    console.log(`   Nichos: ${row.niches}`);
    console.log(`   Com salário: ${row.jobs_with_salary}`);
    if (row.avg_salary_min) {
      console.log(`   Salário médio: R$${Math.round(row.avg_salary_min)}/mês`);
    }
    console.log(`   Remotas: ${row.remote_jobs}`);
    console.log('');

  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

if (require.main === module) {
  main();
}

export { main };
