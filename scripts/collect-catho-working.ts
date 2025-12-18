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

interface CathoJob {
  job_id: string;
  platform: string;
  title: string;
  company: string;
  location: string;
  url: string;
}

async function scrapeCatho(keywords: string[]): Promise<CathoJob[]> {
  console.log('   🔍 [Catho] Scraping vagas...');
  
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: '/usr/bin/chromium-browser',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  const jobs: CathoJob[] = [];

  try {
    const page = await browser.newPage();

    for (const keyword of keywords.slice(0, 5)) { // Max 5 keywords
      try {
        console.log(`      📋 Buscando: "${keyword}"`);
        
        await page.goto(`https://www.catho.com.br/vagas/${keyword.toLowerCase().replace(/\s+/g, '-')}/`, {
          waitUntil: 'networkidle0',
          timeout: 60000,
        });

        await delay(8000); // CRITICAL: wait for JS to load

        const pageJobs = await page.evaluate(() => {
          const results: any[] = [];
          const jobLinks = document.querySelectorAll('a[href*="/vagas/"][href*="/34"]'); // Job ID pattern
          
          jobLinks.forEach((link, i) => {
            if (i >= 20) return; // Max 20 per keyword
            
            const href = link.getAttribute('href');
            const title = link.textContent?.trim() || '';
            
            if (href && title && href.includes('/34') && !href.includes('anunciar')) {
              results.push({
                url: href.startsWith('http') ? href : `https://www.catho.com.br${href}`,
                title: title,
              });
            }
          });
          
          return results;
        });

        for (const jobData of pageJobs) {
          const jobId = `catho-${jobData.url.match(/\/(\d+)\//)?.[1] || Date.now()}`;
          
          jobs.push({
            job_id: jobId,
            platform: 'catho',
            title: jobData.title,
            company: 'Unknown', // Will need detail page for this
            location: 'Brasil',
            url: jobData.url,
          });
        }

        console.log(`         ✅ ${pageJobs.length} vagas`);
        await delay(Math.random() * 5000 + 5000); // 5-10s delay

      } catch (err: any) {
        console.error(`         ❌ Erro: ${err.message}`);
      }
    }

  } finally {
    await browser.close();
  }

  console.log(`      ✅ Total: ${jobs.length} vagas`);
  return jobs;
}

async function createTable(client: Client) {
  await client.query(`
    CREATE TABLE IF NOT EXISTS sofia.catho_jobs (
      id SERIAL PRIMARY KEY,
      job_id VARCHAR(200) UNIQUE NOT NULL,
      platform VARCHAR(50) NOT NULL,
      title VARCHAR(300) NOT NULL,
      company VARCHAR(200),
      location VARCHAR(300),
      url TEXT,
      collected_at TIMESTAMPTZ DEFAULT NOW()
    );
  `);
}

async function upsertJob(client: Client, job: CathoJob) {
  await client.query(
    `INSERT INTO sofia.catho_jobs (job_id, platform, title, company, location, url)
     VALUES ($1, $2, $3, $4, $5, $6)
     ON CONFLICT (job_id) DO UPDATE SET collected_at = NOW()`,
    [job.job_id, job.platform, job.title, job.company, job.location, job.url]
  );
}

async function main() {
  console.log('🚀 Sofia Pulse - Catho Scraper (Working Version)');
  console.log('='.repeat(60));
  
  const client = new Client(DB_CONFIG);
  await client.connect();
  console.log('✅ Connected');
  
  await createTable(client);
  
  const keywords = ['desenvolvedor', 'developer', 'devops', 'engenheiro-de-software'];
  const jobs = await scrapeCatho(keywords);
  
  for (const job of jobs) {
    await upsertJob(client, job);
  }
  
  console.log(`\n✅ Saved ${jobs.length} jobs!`);
  await client.end();
}

main();
