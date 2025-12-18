#!/usr/bin/env tsx
import { Client } from 'pg';
import * as dotenv from 'dotenv';
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

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

async function scrapeCatho(keywords: string[]) {
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: '/usr/bin/chromium-browser',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  const jobs: any[] = [];

  try {
    const page = await browser.newPage();

    for (const keyword of keywords.slice(0, 10)) {
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

          // Walk up to find company/location
          for (let j = 0; j < 5; j++) {
            if (!parent) break;

            const text = parent.textContent || '';

            // Look for location patterns (cidade - UF)
            const locMatch = text.match(/([A-Z][a-zà-ú\s]+)\s*-\s*([A-Z]{2})/);
            if (locMatch && !location) {
              location = locMatch[0];
            }

            parent = parent.parentElement;
          }

          if (href && title && !href.includes('anunciar')) {
            results.push({
              url: href.startsWith('http') ? href : `https://www.catho.com.br${href}`,
              title,
              location: location || 'Brasil',
              company: 'Catho', // Will extract later if needed
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
  console.log('🚀 Catho Scraper - Final Version');
  console.log('='.repeat(50));

  const client = new Client(DB_CONFIG);
  await client.connect();

  // Ensure unified jobs table exists
  await client.query(`
    CREATE TABLE IF NOT EXISTS sofia.jobs (
      id SERIAL PRIMARY KEY,
      job_id VARCHAR(500) UNIQUE,
      title VARCHAR(500),
      company VARCHAR(300),
      location VARCHAR(300),
      city VARCHAR(100),
      state VARCHAR(50),
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

  const keywords = [
    // Desenvolvimento geral
    'desenvolvedor', 'developer', 'programador', 'software-engineer',
    'engenheiro-de-software', 'analista-de-sistemas',

    // Frontend
    'frontend', 'front-end', 'react', 'nextjs', 'vue', 'angular',

    // Backend
    'backend', 'back-end', 'nodejs', 'java', 'python', 'dotnet',

    // Full Stack
    'full-stack', 'fullstack',

    // IA e ML
    'inteligencia-artificial', 'machine-learning', 'data-scientist',
    'cientista-de-dados', 'ai-engineer', 'ml-engineer', 'llm',
    'deep-learning', 'nlp',

    // DevOps e Cloud
    'devops', 'sre', 'cloud-engineer', 'aws', 'azure', 'gcp',
    'kubernetes', 'docker',

    // Dados
    'data-engineer', 'engenheiro-de-dados', 'dba', 'database-administrator',
    'arquiteto-de-dados', 'big-data', 'analytics',

    // QA e Testes
    'qa', 'quality-assurance', 'tester', 'test-automation',
    'analista-de-testes',

    // Segurança
    'seguranca-da-informacao', 'cybersecurity', 'security-engineer',
    'infosec', 'pentest',

    // Redes
    'network-engineer', 'engenheiro-de-redes', 'infraestrutura',

    // Gestão e Liderança
    'tech-lead', 'engineering-manager', 'scrum-master', 'product-owner',
    'agile-coach', 'cto',

    // Tecnologias/Plataformas específicas
    'salesforce', 'sap', 'oracle', 'ibm', 'totvs',

    // Mobile
    'mobile', 'android', 'ios', 'react-native', 'flutter'
  ];

  const jobs = await scrapeCatho(keywords);

  for (const job of jobs) {
    const jobId = `catho-${job.url.match(/\/(\d+)\//)?.[1] || Date.now()}`;

    // Parse city and state
    const [city, state] = job.location.includes('-')
      ? job.location.split('-').map((s: string) => s.trim())
      : [null, null];

    await client.query(
      `INSERT INTO sofia.jobs (job_id, title, company, location, city, state, url, platform, collected_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
       ON CONFLICT (job_id) DO UPDATE SET 
         title = EXCLUDED.title,
         location = EXCLUDED.location,
         collected_at = NOW()`,
      [jobId, job.title, job.company, job.location, city, state, job.url, 'catho']
    );
  }

  console.log(`\n✅ Saved ${jobs.length} jobs!`);
  await client.end();
}

main();

