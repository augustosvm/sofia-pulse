#!/usr/bin/env tsx
import { Pool } from 'pg';
import * as dotenv from 'dotenv';
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import { normalizeLocation } from './shared/geo-helpers';

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

interface LinkedInJob {
    url: string;
    title: string;
    company: string;
    location: string;
    description?: string;
    posted_date?: string;
}

async function scrapeLinkedIn(keywords: string[], location: string = 'Brazil') {
    const browser = await puppeteer.launch({
        headless: 'new',
        executablePath: '/usr/bin/chromium-browser',
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ],
    });

    const jobs: LinkedInJob[] = [];

    try {
        const page = await browser.newPage();

        // Set extra headers to avoid detection
        await page.setExtraHTTPHeaders({
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        });

        for (const keyword of keywords) {
            console.log(`   📋 ${keyword}`);

            // LinkedIn jobs URL (public, no login required)
            const searchUrl = `https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(keyword)}&location=${encodeURIComponent(location)}&f_TPR=r86400`;

            try {
                await page.goto(searchUrl, {
                    waitUntil: 'networkidle2',
                    timeout: 60000,
                });

                // Wait for job listings to load
                await delay(5000);

                // Try to scroll to load more jobs
                await page.evaluate(() => {
                    window.scrollTo(0, document.body.scrollHeight / 2);
                });
                await delay(2000);

                const pageJobs = await page.evaluate(() => {
                    const results: any[] = [];

                    // LinkedIn job cards selectors (public view)
                    const jobCards = document.querySelectorAll('.base-card, .job-search-card, [data-job-id]');

                    jobCards.forEach((card, i) => {
                        if (i >= 25) return; // Limit per keyword

                        try {
                            // Try multiple selectors for title
                            const titleEl = card.querySelector('.base-search-card__title, .job-search-card__title, h3');
                            const title = titleEl?.textContent?.trim() || '';

                            // Company name
                            const companyEl = card.querySelector('.base-search-card__subtitle, .job-search-card__company-name, h4');
                            const company = companyEl?.textContent?.trim() || '';

                            // Location
                            const locationEl = card.querySelector('.job-search-card__location, .base-search-card__metadata span');
                            const location = locationEl?.textContent?.trim() || '';

                            // Job URL
                            const linkEl = card.querySelector('a[href*="/jobs/view/"]');
                            const href = linkEl?.getAttribute('href') || '';

                            // Posted date
                            const dateEl = card.querySelector('time');
                            const posted_date = dateEl?.getAttribute('datetime') || '';

                            if (title && href) {
                                results.push({
                                    url: href.startsWith('http') ? href : `https://www.linkedin.com${href.split('?')[0]}`,
                                    title,
                                    company: company || 'LinkedIn',
                                    location: location || 'Brasil',
                                    posted_date,
                                });
                            }
                        } catch (err) {
                            // Skip problematic cards
                        }
                    });

                    return results;
                });

                jobs.push(...pageJobs);
                console.log(`      ✅ ${pageJobs.length} vagas`);

                // Random delay to avoid rate limiting
                await delay(Math.random() * 5000 + 8000);

            } catch (err) {
                console.log(`      ⚠️  Erro ao buscar "${keyword}": ${err instanceof Error ? err.message : 'Unknown error'}`);
            }
        }

    } finally {
        await browser.close();
    }

    return jobs;
}

async function saveToDatabase(jobs: LinkedInJob[]) {
    const pool = new Pool(DB_CONFIG);

    try {
        // Ensure jobs table exists with all necessary columns
        await pool.query(`
      CREATE TABLE IF NOT EXISTS sofia.jobs (
        id SERIAL PRIMARY KEY,
        job_id VARCHAR(500) UNIQUE,
        title VARCHAR(500),
        company VARCHAR(300),
        location VARCHAR(300),
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

        let saved = 0;

        for (const job of jobs) {
            try {
                // Extract job ID from URL
                const jobIdMatch = job.url.match(/\/jobs\/view\/(\d+)/);
                const jobId = jobIdMatch ? `linkedin-${jobIdMatch[1]}` : `linkedin-${Date.now()}-${Math.random()}`;

                // Parse location
                const locationParts = job.location.split(',').map(s => s.trim());
                const city = locationParts[0] || null;
                const country = locationParts[locationParts.length - 1] || 'Brazil';

                // Normalize geographic data
                const { countryId, cityId } = await normalizeLocation(pool, {
                    country: country,
                    city: city
                });

                await pool.query(
                    `INSERT INTO sofia.jobs (job_id, title, company, location, city, country, country_id, city_id, url, platform, posted_date, collected_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
           ON CONFLICT (job_id) DO UPDATE SET
             title = EXCLUDED.title,
             company = EXCLUDED.company,
             location = EXCLUDED.location,
             collected_at = NOW()`,
                    [jobId, job.title, job.company, job.location, city, country, countryId, cityId, job.url, 'linkedin', job.posted_date]
                );

                saved++;
            } catch (err) {
                console.log(`      ⚠️  Erro ao salvar vaga: ${err instanceof Error ? err.message : 'Unknown'}`);
            }
        }

        return saved;

    } finally {
        await pool.end();
    }
}

async function main() {
    console.log('🚀 LinkedIn Jobs Scraper');
    console.log('='.repeat(50));

    const keywords = [
        'desenvolvedor',
        'developer',
        'software engineer',
        'devops',
        'data scientist',
        'frontend developer',
        'backend developer',
        'full stack',
        'tech lead',
        'engineering manager',
    ];

    const jobs = await scrapeLinkedIn(keywords, 'Brazil');

    console.log(`\n💾 Salvando ${jobs.length} vagas no banco...`);
    const saved = await saveToDatabase(jobs);

    console.log(`\n✅ Total salvo: ${saved} vagas`);
    console.log('='.repeat(50));
}

main().catch(err => {
    console.error('❌ Erro fatal:', err);
    process.exit(1);
});
