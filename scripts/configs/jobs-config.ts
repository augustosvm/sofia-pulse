/**
 * Jobs Collectors Configuration - Sofia Pulse
 *
 * Configurações para collectors de vagas de emprego:
 * - Himalayas (API pública)
 * - RemoteOK (API pública)
 * - Arbeitnow (API pública)
 * - GitHub Jobs (Scraping)
 *
 * Cada config define: URL, parsing, schedule, rate limits, etc.
 *
 * Schedule format (cron):
 *   '0 6 * * *'     = Daily at 6am - fast-changing data
 *   '0 12 * * *'    = Daily at noon
 *   '0 8 * * *'     = Daily at 8am
 */

import { JobsCollectorConfig, JobData } from '../collectors/jobs-collector.js';

// ============================================================================
// HIMALAYAS JOBS
// ============================================================================

export const himalayasJobs: JobsCollectorConfig = {
  name: 'himalayas',
  displayName: '🏔️ Himalayas Remote Jobs',
  description: 'Remote tech jobs com dados de salário',

  url: 'https://himalayas.app/jobs/api',

  rateLimit: 2000, // 2s entre requests (API pública)

  parseResponse: async (data: any) => {
    const jobs: JobData[] = [];
    const apiJobs = data.jobs || [];

    for (const job of apiJobs) {
      // Skip jobs sem required fields
      if (!job.companyName || !job.title) continue;

      // Extract location
      const locations = job.locationRestrictions || ['Remote'];
      const location = locations.join(', ');
      const country = locations[0] || 'REMOTE';
      const isRemote = locations.some((loc: string) => /anywhere|worldwide|remote/i.test(loc));

      // Extract skills from categories
      const skills = (job.categories || []).filter((cat: string) => cat.length > 0);

      // Convert Unix timestamp to Date
      const postedDate = job.pubDate ? new Date(job.pubDate * 1000).toISOString() : undefined;

      jobs.push({
        job_id: job.guid,
        platform: 'himalayas',
        title: job.title,
        company: job.companyName,
        location: location,
        country: country,
        remote_type: isRemote ? 'remote' : 'onsite',
        description: job.description || '',
        url: job.applicationLink,
        posted_date: postedDate,
        salary_min: job.minSalary || undefined,
        salary_max: job.maxSalary || undefined,
        salary_currency: job.currency || 'USD',
        salary_period: 'yearly',
        employment_type: job.employmentType?.toLowerCase() || 'full-time',
        skills_required: skills.length > 0 ? skills : undefined,
      });
    }

    return jobs;
  },

  schedule: '0 6,18 * * *', // 2x/dia - 6h e 18h
  allowWithoutAuth: true,
};

// ============================================================================
// REMOTEOK JOBS
// ============================================================================

export const remoteokJobs: JobsCollectorConfig = {
  name: 'remoteok',
  displayName: '🌎 RemoteOK Jobs',
  description: 'Remote jobs worldwide - API pública',

  url: 'https://remoteok.com/api',

  rateLimit: 3000, // 3s entre requests (para evitar rate limit)

  parseResponse: async (data: any) => {
    const jobs: JobData[] = [];

    // RemoteOK retorna array, primeiro item é metadata
    const apiJobs = Array.isArray(data) ? data.slice(1) : [];

    for (const job of apiJobs) {
      // Skip jobs sem required fields
      if (!job.company || !job.position) continue;

      // Extract salary (RemoteOK tem salary_min/salary_max)
      const salaryMin = job.salary_min || undefined;
      const salaryMax = job.salary_max || undefined;

      // Extract location
      const location = job.location || 'Remote';
      const isRemote = !job.location || /anywhere|worldwide|remote/i.test(job.location);

      // Extract tags as skills
      const skills = job.tags || [];

      // Posted date (epoch timestamp)
      const postedDate = job.date ? new Date(job.date * 1000).toISOString() : undefined;

      jobs.push({
        job_id: job.id || `remoteok-${job.slug}`,
        platform: 'remoteok',
        title: job.position,
        company: job.company,
        location: location,
        remote_type: isRemote ? 'remote' : 'onsite',
        description: job.description || '',
        url: job.url || `https://remoteok.com/remote-jobs/${job.slug}`,
        posted_date: postedDate,
        salary_min: salaryMin,
        salary_max: salaryMax,
        salary_currency: 'USD', // RemoteOK usa USD
        salary_period: 'yearly',
        employment_type: 'full-time',
        skills_required: skills.length > 0 ? skills : undefined,
      });
    }

    return jobs;
  },

  schedule: '0 8,20 * * *', // 2x/dia - 8h e 20h
  allowWithoutAuth: true,
};

// ============================================================================
// ARBEITNOW JOBS
// ============================================================================

export const arbeitnowJobs: JobsCollectorConfig = {
  name: 'arbeitnow',
  displayName: '🇪🇺 Arbeitnow Jobs',
  description: 'Europe tech jobs - API grátis',

  url: 'https://www.arbeitnow.com/api/job-board-api',

  rateLimit: 2000, // 2s entre requests

  parseResponse: async (data: any) => {
    const jobs: JobData[] = [];
    const apiJobs = data.data || [];

    for (const job of apiJobs) {
      // Skip jobs sem required fields
      if (!job.company_name || !job.title) continue;

      // Extract location
      const location = job.location || 'Remote';
      const isRemote = job.remote || /remote/i.test(job.location);

      // Extract tags as skills
      const skills = job.tags || [];

      // Posted date
      const postedDate = job.created_at || undefined;

      jobs.push({
        job_id: job.slug || `arbeitnow-${Date.now()}`,
        platform: 'arbeitnow',
        title: job.title,
        company: job.company_name,
        location: location,
        remote_type: isRemote ? 'remote' : 'onsite',
        description: job.description || '',
        url: job.url,
        posted_date: postedDate,
        employment_type: 'full-time',
        skills_required: skills.length > 0 ? skills : undefined,
      });
    }

    return jobs;
  },

  schedule: '0 10,22 * * *', // 2x/dia - 10h e 22h
  allowWithoutAuth: true,
};

// ============================================================================
// GITHUB JOBS (via GraphQL)
// ============================================================================

export const githubJobs: JobsCollectorConfig = {
  name: 'github-jobs',
  displayName: '🐙 GitHub Jobs',
  description: 'Tech jobs from GitHub - Requires GITHUB_TOKEN',

  // GitHub Jobs usa GraphQL search
  url: 'https://api.github.com/search/repositories?q=hiring+in:readme+in:description&sort=updated&per_page=100',

  headers: (env) => ({
    'Authorization': `token ${env.GITHUB_TOKEN}`,
    'Accept': 'application/vnd.github.v3+json',
  }),

  rateLimit: 'github', // Usa rate limiter do GitHub

  parseResponse: async (data: any) => {
    const jobs: JobData[] = [];
    const repos = data.items || [];

    for (const repo of repos) {
      // Repos com "hiring" no README/description = possível vaga
      if (!repo.owner?.login) continue;

      // Extrai info básica
      const title = `Hiring at ${repo.owner.login}`;
      const company = repo.owner.login;
      const description = repo.description || '';
      const url = repo.html_url;

      // Detecta remote
      const isRemote = /remote/i.test(description);

      // Extract skills from language + topics
      const skills: string[] = [];
      if (repo.language) skills.push(repo.language.toLowerCase());
      if (repo.topics) skills.push(...repo.topics);

      jobs.push({
        job_id: `github-${repo.id}`,
        platform: 'github-jobs',
        title: title,
        company: company,
        location: 'Remote',
        remote_type: isRemote ? 'remote' : 'onsite',
        description: description,
        url: url,
        posted_date: repo.updated_at,
        employment_type: 'full-time',
        skills_required: skills.length > 0 ? skills : undefined,
      });
    }

    return jobs;
  },

  schedule: '0 8 * * *', // 1x/dia (GitHub hiring não muda tanto)
  allowWithoutAuth: false, // Precisa de GITHUB_TOKEN
};

// ============================================================================
// EXPORTS
// ============================================================================

/**
 * Registry de todos os jobs collectors
 */
export const jobsCollectors: Record<string, JobsCollectorConfig> = {
  himalayas: himalayasJobs,
  remoteok: remoteokJobs,
  arbeitnow: arbeitnowJobs,
  // github-jobs: githubJobs, // Comentado até configurar GITHUB_TOKEN
};

/**
 * Filtra collectors por schedule
 */
export function getJobsCollectorsBySchedule(schedule: string): JobsCollectorConfig[] {
  return Object.values(jobsCollectors).filter(c => c.schedule === schedule);
}
