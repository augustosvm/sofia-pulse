/**
 * Organizations Collectors Configuration - Sofia Pulse
 *
 * Configurações para collectors de organizações:
 * - AI Companies (OpenAI, Anthropic, Mistral, etc.)
 * - Universities (Tsinghua, MIT, USP, etc.)
 * - NGOs (Red Cross, UNICEF, Greenpeace, etc.)
 * - Startups (early-stage companies)
 * - VC Firms (Sequoia, a16z, etc.)
 *
 * Cada config define: URL, parsing, schedule, rate limits, etc.
 *
 * Schedule format (cron):
 *   '0 8 * * *'     = Daily at 8am
 *   '0 8 * * 1'     = Weekly on Monday at 8am
 *   '0 8 1 * *'     = Monthly on 1st at 8am
 */

import { OrganizationsCollectorConfig } from '../collectors/organizations-collector.js';
import { OrganizationData, normalizeOrgType } from '../shared/organizations-inserter.js';

// ============================================================================
// AI COMPANIES
// ============================================================================

export const aiCompanies: OrganizationsCollectorConfig = {
  name: 'ai-companies',
  displayName: '🤖 AI Companies Tracker',
  description: 'LLMs, Computer Vision, AI Chips - USA vs China race',

  // Mock data (em produção usaria Crunchbase/PitchBook API)
  // URL null triggers fallback to parseResponse with mock data
  url: (env) => null as any,

  parseResponse: async (_, env) => {
    // Mock data baseado em dados reais de 2024
    const companies: OrganizationData[] = [
      // USA - LLMs
      {
        org_id: 'aicompanies-openai',
        name: 'OpenAI',
        type: 'ai_company',
        source: 'ai-companies',
        industry: 'Artificial Intelligence',
        location: 'San Francisco, CA',
        city: 'San Francisco',
        country: 'USA',
        country_code: 'US',
        founded_date: '2015-12-01',
        website: 'https://openai.com',
        description: 'Leading AI research lab creating GPT models and ChatGPT',
        tags: ['AI', 'LLM', 'Research', 'ChatGPT'],
        metadata: {
          category: 'LLM',
          total_funding_usd: 11300000000,
          last_valuation_usd: 80000000000,
          funding_stage: 'Series C',
          models: ['GPT-3.5', 'GPT-4', 'GPT-4 Turbo', 'DALL-E 3'],
          products: ['ChatGPT', 'API Platform', 'Enterprise'],
          investors: ['Microsoft', 'Sequoia Capital', 'Andreessen Horowitz'],
          employee_count: 750,
          status: 'active',
        },
      },
      {
        org_id: 'aicompanies-anthropic',
        name: 'Anthropic',
        type: 'ai_company',
        source: 'ai-companies',
        industry: 'Artificial Intelligence',
        location: 'San Francisco, CA',
        city: 'San Francisco',
        country: 'USA',
        country_code: 'US',
        founded_date: '2021-01-01',
        website: 'https://anthropic.com',
        description: 'AI safety focused company building Claude LLMs',
        tags: ['AI', 'LLM', 'Safety', 'Claude'],
        metadata: {
          category: 'LLM',
          total_funding_usd: 7300000000,
          last_valuation_usd: 15000000000,
          funding_stage: 'Series C',
          models: ['Claude', 'Claude 2', 'Claude 3 Opus/Sonnet/Haiku'],
          products: ['Claude API', 'Claude Pro'],
          investors: ['Google', 'Spark Capital', 'Salesforce Ventures'],
          employee_count: 500,
          status: 'active',
        },
      },

      // Europe - LLMs
      {
        org_id: 'aicompanies-mistral',
        name: 'Mistral AI',
        type: 'ai_company',
        source: 'ai-companies',
        industry: 'Artificial Intelligence',
        location: 'Paris',
        city: 'Paris',
        country: 'France',
        country_code: 'FR',
        founded_date: '2023-05-01',
        website: 'https://mistral.ai',
        description: 'European open-source LLM leader',
        tags: ['AI', 'LLM', 'Open Source', 'Europe'],
        metadata: {
          category: 'LLM',
          total_funding_usd: 640000000,
          last_valuation_usd: 2000000000,
          funding_stage: 'Series A',
          models: ['Mistral 7B', 'Mixtral 8x7B'],
          products: ['Open-source models', 'Enterprise platform'],
          investors: ['Andreessen Horowitz', 'Lightspeed', 'NVIDIA'],
          employee_count: 60,
          status: 'active',
        },
      },

      // China - LLMs
      {
        org_id: 'aicompanies-baidu',
        name: 'Baidu AI',
        type: 'ai_company',
        source: 'ai-companies',
        industry: 'Artificial Intelligence',
        location: 'Beijing',
        city: 'Beijing',
        country: 'China',
        country_code: 'CN',
        founded_date: '2000-01-01',
        website: 'https://www.baidu.com',
        description: 'Chinese tech giant with ERNIE LLM competing with GPT',
        tags: ['AI', 'LLM', 'China', 'ERNIE'],
        metadata: {
          category: 'LLM',
          total_funding_usd: 0,
          last_valuation_usd: 45000000000,
          funding_stage: 'Public',
          models: ['ERNIE Bot', 'ERNIE 3.0', 'ERNIE 4.0'],
          products: ['ERNIE Bot', 'Apollo'],
          investors: ['Public (NASDAQ: BIDU)'],
          employee_count: 38000,
          status: 'public',
        },
      },

      // AI Chips
      {
        org_id: 'aicompanies-cerebras',
        name: 'Cerebras',
        type: 'ai_company',
        source: 'ai-companies',
        industry: 'AI Hardware',
        location: 'Sunnyvale, CA',
        city: 'Sunnyvale',
        country: 'USA',
        country_code: 'US',
        founded_date: '2016-01-01',
        website: 'https://cerebras.net',
        description: 'Wafer-scale AI chip manufacturer',
        tags: ['AI', 'Hardware', 'Chips', 'WSE'],
        metadata: {
          category: 'AI Chips',
          total_funding_usd: 720000000,
          last_valuation_usd: 4000000000,
          funding_stage: 'Series F',
          products: ['Wafer-Scale Engine (WSE-2)', 'CS-2 system'],
          investors: ['Benchmark', 'Eclipse Ventures', 'Coatue'],
          employee_count: 400,
          status: 'active',
        },
      },
    ];

    return companies;
  },

  schedule: '0 8 * * 1', // Weekly on Monday at 8am
  allowWithoutAuth: true,
};

// ============================================================================
// UNIVERSITIES
// ============================================================================

export const universities: OrganizationsCollectorConfig = {
  name: 'universities',
  displayName: '🎓 Global Universities Tracker',
  description: 'Top research universities - QS/THE/ARWU rankings',

  // Mock data (em produção usaria QS/THE APIs)
  // URL null triggers fallback to parseResponse with mock data
  url: (env) => null as any,

  parseResponse: async (_, env) => {
    // Mock data baseado em rankings reais de 2024
    const universities: OrganizationData[] = [
      // China
      {
        org_id: 'universities-tsinghua',
        name: 'Tsinghua University',
        type: 'university',
        source: 'universities',
        industry: 'Higher Education',
        location: 'Beijing',
        city: 'Beijing',
        country: 'China',
        country_code: 'CN',
        founded_date: '1911-04-26',
        website: 'https://www.tsinghua.edu.cn',
        description: 'Top Chinese university for engineering and AI research',
        tags: ['University', 'Research', 'Engineering', 'AI'],
        employee_count: 3500,
        metadata: {
          name_local: '清华大学',
          type: 'Public Research',
          qs_rank: 17,
          the_rank: 12,
          arwu_rank: 22,
          research_output_papers_year: 18500,
          citations_total: 2850000,
          h_index: 312,
          strong_fields: ['Computer Science', 'Engineering', 'AI', 'Materials Science'],
          notable_alumni: ['Xi Jinping', 'Zhu Rongji'],
          international_students_pct: 12.5,
          faculty_count: 3500,
          student_count: 53000,
        },
      },

      // Japan
      {
        org_id: 'universities-tokyo',
        name: 'University of Tokyo',
        type: 'university',
        source: 'universities',
        industry: 'Higher Education',
        location: 'Tokyo',
        city: 'Tokyo',
        country: 'Japan',
        country_code: 'JP',
        founded_date: '1877-04-12',
        website: 'https://www.u-tokyo.ac.jp',
        description: 'Top Japanese university, 16 Nobel Prize winners',
        tags: ['University', 'Research', 'Nobel Prize', 'Japan'],
        employee_count: 4200,
        metadata: {
          name_local: '東京大学',
          type: 'Public Research',
          qs_rank: 28,
          the_rank: 29,
          arwu_rank: 26,
          research_output_papers_year: 14800,
          citations_total: 3200000,
          h_index: 342,
          strong_fields: ['Physics', 'Materials Science', 'Robotics', 'Engineering'],
          notable_alumni: ['16 Nobel Prize winners', '17 Japanese Prime Ministers'],
          international_students_pct: 14.2,
          faculty_count: 4200,
          student_count: 28000,
        },
      },

      // Singapore
      {
        org_id: 'universities-nus',
        name: 'National University of Singapore',
        type: 'university',
        source: 'universities',
        industry: 'Higher Education',
        location: 'Singapore',
        city: 'Singapore',
        country: 'Singapore',
        country_code: 'SG',
        founded_date: '1905-07-01',
        website: 'https://www.nus.edu.sg',
        description: 'Top Asian university, global leader in engineering and CS',
        tags: ['University', 'Research', 'Engineering', 'Asia'],
        employee_count: 2800,
        metadata: {
          name_local: 'NUS',
          type: 'Public Research',
          qs_rank: 8,
          the_rank: 19,
          arwu_rank: 71,
          research_output_papers_year: 12500,
          citations_total: 2450000,
          h_index: 285,
          strong_fields: ['Engineering', 'Computer Science', 'Biotechnology', 'Business'],
          international_students_pct: 33.5,
          faculty_count: 2800,
          student_count: 40000,
        },
      },

      // Australia
      {
        org_id: 'universities-melbourne',
        name: 'University of Melbourne',
        type: 'university',
        source: 'universities',
        industry: 'Higher Education',
        location: 'Melbourne',
        city: 'Melbourne',
        country: 'Australia',
        country_code: 'AU',
        founded_date: '1853-01-01',
        website: 'https://www.unimelb.edu.au',
        description: 'Top Australian university, strong in medicine and biomedicine',
        tags: ['University', 'Research', 'Medicine', 'Australia'],
        employee_count: 3200,
        metadata: {
          type: 'Public Research',
          qs_rank: 14,
          the_rank: 34,
          arwu_rank: 35,
          research_output_papers_year: 13500,
          citations_total: 2850000,
          h_index: 298,
          strong_fields: ['Medicine', 'Law', 'Education', 'Biomedicine'],
          international_students_pct: 42.5,
          faculty_count: 3200,
          student_count: 50000,
        },
      },
    ];

    return universities;
  },

  schedule: '0 8 1 * *', // Monthly on 1st at 8am
  allowWithoutAuth: true,
};

// ============================================================================
// NGOS
// ============================================================================

export const ngos: OrganizationsCollectorConfig = {
  name: 'ngos',
  displayName: '🌍 Global NGOs Tracker',
  description: 'Global NGOs extracted from GlobalGiving projects (50k+ projects → unique orgs)',

  // GlobalGiving API - Projects endpoint
  // Docs: https://www.globalgiving.org/api/
  // FREE API Key: https://www.globalgiving.org/api/keys/new/
  url: (env) => {
    const apiKey = env.GLOBALGIVING_API_KEY || '';
    if (!apiKey) {
      console.warn('⚠️  GLOBALGIVING_API_KEY not set. Using fallback to world-ngos data.');
      return null as any; // Will trigger fallback in parseResponse
    }
    // Projects endpoint (returns 50k+ projects with organization data)
    return `https://api.globalgiving.org/api/public/projectservice/all/projects?api_key=${apiKey}`;
  },

  // Force JSON response (API defaults to XML)
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  },

  parseResponse: async (data, env) => {
    // Fallback if API key missing
    if (!env.GLOBALGIVING_API_KEY) {
      console.warn('⚠️  GLOBALGIVING_API_KEY missing. Using fallback to world-ngos data.');
      console.warn('   Get FREE API key: https://www.globalgiving.org/api/keys/new/');
      console.warn('   Note: world-ngos.py already provides 200 major NGOs.');
      return [];
    }

    // GlobalGiving returns XML, but axios with Accept: application/json gets JSON
    // If data is string (XML), we need to parse it - but axios should auto-convert
    if (typeof data === 'string') {
      console.warn('⚠️  Received XML response (expected JSON). Check axios config.');
      return [];
    }

    // Handle API response (JSON format)
    if (!data || !data.projects || !data.projects.project) {
      console.warn('⚠️  No projects found in API response');
      return [];
    }

    const projects = Array.isArray(data.projects.project)
      ? data.projects.project
      : [data.projects.project];

    console.log(`   📊 Found ${projects.length} projects from GlobalGiving`);

    // Extract unique organizations from projects
    const orgsMap = new Map<string, OrganizationData>();

    for (const project of projects) {
      // Use contact info as organization identifier
      const orgName = project.organization?.name || project.contactTitle || 'Unknown Organization';
      const orgId = `globalgiving-${orgName.toLowerCase().replace(/[^a-z0-9]/g, '-')}`;

      // Skip if already processed
      if (orgsMap.has(orgId)) continue;

      // Extract organization data
      const org: OrganizationData = {
        org_id: orgId,
        name: orgName,
        type: 'ngo' as const,
        source: 'globalgiving',
        industry: project.themeName || project.themes?.theme?.[0]?.name || 'Nonprofit',
        location: project.contactCity && project.contactCountry
          ? `${project.contactCity}, ${project.contactCountry}`
          : project.contactCountry || project.country || undefined,
        city: project.contactCity || undefined,
        country: project.contactCountry || project.country || undefined,
        country_code: project.iso3166CountryCode || undefined,
        website: project.contactUrl || undefined,
        description: project.organization?.mission?.substring(0, 500) || project.summary?.substring(0, 500) || undefined,
        tags: project.themes?.theme
          ? (Array.isArray(project.themes.theme) ? project.themes.theme : [project.themes.theme]).map((t: any) => t.name)
          : project.themeName ? [project.themeName] : [],
        metadata: {
          globalgiving_source: 'projects_endpoint',
          contact_name: project.contactName,
          contact_address: project.contactAddress,
          contact_address2: project.contactAddress2,
          contact_postal: project.contactPostal,
          contact_state: project.contactState,
          region: project.region,
          sample_project_id: project.id,
          sample_project_title: project.title,
          themes: project.themes?.theme || [],
        },
      };

      orgsMap.set(orgId, org);
    }

    const ngos = Array.from(orgsMap.values());
    console.log(`   🏢 Extracted ${ngos.length} unique organizations`);

    return ngos;
  },

  schedule: '0 8 1 * *', // Monthly on 1st at 8am
  allowWithoutAuth: false, // Requires API key
};

// ============================================================================
// EXPORTS
// ============================================================================

/**
 * Registry de todos os organizations collectors
 */
export const organizationsCollectors: Record<string, OrganizationsCollectorConfig> = {
  'ai-companies': aiCompanies,
  universities: universities,
  ngos: ngos,

  // TODO: Adicionar mais collectors:
  // startups: startupsCollector,
  // vc-firms: vcFirmsCollector,
  // research-labs: researchLabsCollector,
};

/**
 * Filtra collectors por schedule
 */
export function getOrganizationsCollectorsBySchedule(schedule: string): OrganizationsCollectorConfig[] {
  return Object.values(organizationsCollectors).filter(c => c.schedule === schedule);
}
