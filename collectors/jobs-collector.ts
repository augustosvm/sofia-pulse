/**
 * Sofia Pulse - Jobs Collector
 * Coleta vagas de emprego tech por país e setor
 *
 * Fontes:
 * - LinkedIn Jobs API (precisa API key)
 * - Indeed Web Scraping
 * - GitHub Jobs (descontinuado mas tem arquivo)
 * - AngelList/Wellfound
 */

import axios from 'axios';
import * as cheerio from 'cheerio';
import { pool } from '../src/db';

interface Job {
  title: string;
  company: string;
  location: string;
  country: string;
  sector: string;
  description?: string;
  salary_range?: string;
  remote: boolean;
  posted_date: Date;
  url: string;
  source: string;
}

// Mapear locations para países
const LOCATION_TO_COUNTRY: Record<string, string> = {
  'São Paulo': 'Brasil',
  'Rio de Janeiro': 'Brasil',
  'Belo Horizonte': 'Brasil',
  'Brasília': 'Brasil',
  'Curitiba': 'Brasil',
  'Porto Alegre': 'Brasil',
  'Recife': 'Brasil',
  'Florianópolis': 'Brasil',
  'New York': 'USA',
  'San Francisco': 'USA',
  'Austin': 'USA',
  'Seattle': 'USA',
  'Boston': 'USA',
  'London': 'UK',
  'Berlin': 'Germany',
  'Paris': 'France',
  'Amsterdam': 'Netherlands',
  'Singapore': 'Singapore',
  'Tokyo': 'Japan',
  'Seoul': 'South Korea',
  'Bangalore': 'India',
  'Remote': 'Remote',
};

// Mapear keywords de título para setores
const TITLE_TO_SECTOR: Record<string, string> = {
  'AI': 'AI/ML',
  'Machine Learning': 'AI/ML',
  'Data Scientist': 'Data Science',
  'Data Engineer': 'Data Engineering',
  'Software Engineer': 'Software Engineering',
  'Frontend': 'Frontend',
  'Backend': 'Backend',
  'Full Stack': 'Full Stack',
  'DevOps': 'DevOps',
  'Security': 'Cybersecurity',
  'Blockchain': 'Blockchain/Web3',
  'Mobile': 'Mobile Development',
  'React': 'Frontend',
  'Python': 'Backend',
  'Java': 'Backend',
  'Cloud': 'Cloud/Infrastructure',
  'Product Manager': 'Product Management',
  'Designer': 'Design/UX',
  'Agro': 'Agro-tech',
  'Fintech': 'Fintech',
  'Healthcare': 'Healthcare Tech',
};

function extractCountry(location: string): string {
  for (const [city, country] of Object.entries(LOCATION_TO_COUNTRY)) {
    if (location.includes(city)) {
      return country;
    }
  }

  // Fallback: procurar país direto
  if (location.includes('Brazil') || location.includes('Brasil')) return 'Brasil';
  if (location.includes('USA') || location.includes('United States')) return 'USA';
  if (location.includes('UK') || location.includes('United Kingdom')) return 'UK';
  if (location.includes('Germany') || location.includes('Alemanha')) return 'Germany';

  return 'Unknown';
}

function extractSector(title: string, description?: string): string {
  const text = `${title} ${description || ''}`.toLowerCase();

  for (const [keyword, sector] of Object.entries(TITLE_TO_SECTOR)) {
    if (text.includes(keyword.toLowerCase())) {
      return sector;
    }
  }

  return 'General Tech';
}

/**
 * Coletar vagas do Indeed (Web Scraping)
 */
async function collectIndeedJobs(country: string = 'Brasil'): Promise<Job[]> {
  const jobs: Job[] = [];

  const queries = [
    'software engineer',
    'desenvolvedor',
    'data scientist',
    'devops',
    'product manager',
  ];

  const countryDomains: Record<string, string> = {
    'Brasil': 'indeed.com.br',
    'USA': 'indeed.com',
    'UK': 'indeed.co.uk',
    'Germany': 'de.indeed.com',
  };

  const domain = countryDomains[country] || 'indeed.com';

  for (const query of queries) {
    try {
      const url = `https://www.${domain}/jobs?q=${encodeURIComponent(query)}&l=&sort=date`;

      const response = await axios.get(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          'Accept-Language': 'en-US,en;q=0.9',
        },
        timeout: 10000,
      });

      const $ = cheerio.load(response.data);

      $('.job_seen_beacon, .jobsearch-SerpJobCard').each((_, card) => {
        try {
          const title = $(card).find('.jobTitle, h2.title').text().trim();
          const company = $(card).find('.companyName').text().trim();
          const location = $(card).find('.companyLocation').text().trim();
          const summary = $(card).find('.job-snippet').text().trim();
          const jobKey = $(card).find('a').attr('data-jk') || '';
          const jobUrl = `https://www.${domain}/viewjob?jk=${jobKey}`;

          if (!title || !company) return;

          const extractedCountry = extractCountry(location) || country;
          const sector = extractSector(title, summary);

          jobs.push({
            title,
            company,
            location,
            country: extractedCountry,
            sector,
            description: summary,
            remote: location.toLowerCase().includes('remote') || location.toLowerCase().includes('remoto'),
            posted_date: new Date(),
            url: jobUrl,
            source: 'Indeed',
          });
        } catch (err) {
          console.error('Erro ao processar job card:', err);
        }
      });

      console.log(`  ✅ Indeed ${country} (${query}): ${jobs.length} vagas`);

      // Delay entre requests
      await new Promise(resolve => setTimeout(resolve, 2000));
    } catch (error: any) {
      console.error(`  ❌ Indeed ${query}:`, error.message);
    }
  }

  return jobs;
}

/**
 * Coletar vagas do LinkedIn (precisa API key)
 * https://www.linkedin.com/developers/
 */
async function collectLinkedInJobs(): Promise<Job[]> {
  const jobs: Job[] = [];

  const LINKEDIN_API_KEY = process.env.LINKEDIN_API_KEY;

  if (!LINKEDIN_API_KEY) {
    console.log('  ⚠️  LINKEDIN_API_KEY não configurada, pulando LinkedIn');
    return jobs;
  }

  try {
    // LinkedIn Jobs API v2
    const response = await axios.get('https://api.linkedin.com/v2/jobs', {
      headers: {
        'Authorization': `Bearer ${LINKEDIN_API_KEY}`,
        'X-Restli-Protocol-Version': '2.0.0',
      },
      params: {
        keywords: 'software engineer',
        locationId: '106057199', // Brasil
        count: 50,
      },
    });

    for (const job of response.data.elements || []) {
      jobs.push({
        title: job.title,
        company: job.companyName,
        location: job.location,
        country: extractCountry(job.location),
        sector: extractSector(job.title, job.description),
        description: job.description,
        remote: job.workRemoteAllowed || false,
        posted_date: new Date(job.listedAt),
        url: `https://www.linkedin.com/jobs/view/${job.id}`,
        source: 'LinkedIn',
      });
    }

    console.log(`  ✅ LinkedIn: ${jobs.length} vagas`);
  } catch (error: any) {
    console.error('  ❌ LinkedIn API:', error.message);
  }

  return jobs;
}

/**
 * Coletar vagas do AngelList/Wellfound (startups)
 */
async function collectAngelListJobs(): Promise<Job[]> {
  const jobs: Job[] = [];

  try {
    // AngelList/Wellfound API (ou scraping)
    const url = 'https://wellfound.com/jobs';

    const response = await axios.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      },
      timeout: 10000,
    });

    const $ = cheerio.load(response.data);

    // AngelList tem estrutura diferente, precisa ajustar seletores
    $('.job-listing, .jobListing').each((_, card) => {
      try {
        const title = $(card).find('.jobTitle, h2').text().trim();
        const company = $(card).find('.company-name').text().trim();
        const location = $(card).find('.location').text().trim();

        if (!title || !company) return;

        jobs.push({
          title,
          company,
          location,
          country: extractCountry(location),
          sector: extractSector(title),
          remote: location.toLowerCase().includes('remote'),
          posted_date: new Date(),
          url: $(card).find('a').attr('href') || '',
          source: 'AngelList',
        });
      } catch (err) {
        console.error('Erro ao processar AngelList job:', err);
      }
    });

    console.log(`  ✅ AngelList: ${jobs.length} vagas`);
  } catch (error: any) {
    console.error('  ❌ AngelList:', error.message);
  }

  return jobs;
}

/**
 * Salvar vagas no banco
 */
async function saveJobs(jobs: Job[]): Promise<void> {
  if (jobs.length === 0) {
    console.log('  ⚠️  Nenhuma vaga para salvar');
    return;
  }

  const client = await pool.connect();

  try {
    await client.query('BEGIN');

    for (const job of jobs) {
      await client.query(
        `
        INSERT INTO sofia.jobs (
          title, company, location, country, sector, description,
          salary_range, remote, posted_date, url, source, created_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
        ON CONFLICT (url) DO UPDATE SET
          title = EXCLUDED.title,
          company = EXCLUDED.company,
          updated_at = NOW()
        `,
        [
          job.title,
          job.company,
          job.location,
          job.country,
          job.sector,
          job.description,
          job.salary_range,
          job.remote,
          job.posted_date,
          job.url,
          job.source,
        ]
      );
    }

    await client.query('COMMIT');
    console.log(`✅ ${jobs.length} vagas salvas no banco`);
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('❌ Erro ao salvar vagas:', error);
    throw error;
  } finally {
    client.release();
  }
}

/**
 * Coletar todas as vagas
 */
async function collectAllJobs(): Promise<void> {
  console.log('🔍 Coletando vagas de emprego...\n');

  const allJobs: Job[] = [];

  // Indeed - Brasil (principal)
  console.log('📊 Indeed Brasil...');
  const indeedBR = await collectIndeedJobs('Brasil');
  allJobs.push(...indeedBR);

  // Indeed - USA
  console.log('📊 Indeed USA...');
  const indeedUS = await collectIndeedJobs('USA');
  allJobs.push(...indeedUS);

  // LinkedIn
  console.log('📊 LinkedIn...');
  const linkedin = await collectLinkedInJobs();
  allJobs.push(...linkedin);

  // AngelList
  console.log('📊 AngelList/Wellfound...');
  const angellist = await collectAngelListJobs();
  allJobs.push(...angellist);

  console.log(`\n📊 Total coletado: ${allJobs.length} vagas`);

  // Salvar no banco
  await saveJobs(allJobs);

  // Estatísticas
  const byCountry: Record<string, number> = {};
  const bySector: Record<string, number> = {};

  for (const job of allJobs) {
    byCountry[job.country] = (byCountry[job.country] || 0) + 1;
    bySector[job.sector] = (bySector[job.sector] || 0) + 1;
  }

  console.log('\n📍 Por País:');
  Object.entries(byCountry)
    .sort((a, b) => b[1] - a[1])
    .forEach(([country, count]) => {
      console.log(`  ${country}: ${count} vagas`);
    });

  console.log('\n💼 Por Setor:');
  Object.entries(bySector)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .forEach(([sector, count]) => {
      console.log(`  ${sector}: ${count} vagas`);
    });
}

// Executar se chamado diretamente
if (require.main === module) {
  collectAllJobs()
    .then(() => {
      console.log('\n✅ Coleta de vagas concluída!');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n❌ Erro na coleta:', error);
      process.exit(1);
    });
}

export { collectAllJobs, collectIndeedJobs, collectLinkedInJobs };
