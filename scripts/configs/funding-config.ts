/**
 * Funding Rounds Collector Configs
 *
 * Configs for multiple funding data sources:
 * - Y Combinator Companies (5500+ startups)
 * - Product Hunt (daily product launches + funding)
 * - SEC Edgar (IPOs, Form D, S-1 filings)
 *
 * Each config specifies:
 * - API endpoint
 * - Rate limiting
 * - Response parsing
 * - Schedule (cron)
 */

import type { FundingCollectorConfig } from '../collectors/funding-collector.js';

// ============================================================================
// Y COMBINATOR COMPANIES
// ============================================================================

export const ycCompanies: FundingCollectorConfig = {
  name: 'yc-companies',
  displayName: '🚀 Y Combinator Companies',
  url: 'https://yc-oss.github.io/api/companies/all.json',
  timeout: 30000,
  parseResponse: async (data) => {
    // Helper: Parse YC batch to date (W24 → 2024-01-15, S23 → 2023-06-15)
    const parseYCBatchDate = (batch: string): Date | null => {
      if (!batch || batch.length < 3) return null;
      const season = batch[0].toUpperCase();
      const year = parseInt(batch.slice(1), 10);
      if (isNaN(year)) return null;
      const fullYear = year < 100 ? year + 2000 : year;
      const month = season === 'W' ? 1 : season === 'S' ? 6 : 1; // Winter=Jan, Summer=Jun
      return new Date(fullYear, month - 1, 15); // Mid-month
    };

    // Filter for recent batches and active companies
    const recentCompanies = data
      .filter((company: any) => company.name && company.batch)
      .map((company: any) => ({
        company_name: company.name,
        round_type: `YC ${company.batch}`,
        sector: company.tags?.join(', ').slice(0, 255) || null,
        country: company.location?.includes('USA') ? 'USA' : company.location || 'USA',
        website: company.website || null,
        description: company.description?.slice(0, 500) || null,
        announced_date: parseYCBatchDate(company.batch), // FIXED: Infer from batch
        source: 'yc-companies',
      }));

    // Return up to 500 most recent (to avoid duplicates)
    return recentCompanies.slice(0, 500);
  },
  schedule: '0 10 * * 1', // Weekly on Monday at 10am UTC
  description: 'Y Combinator startups database (5500+ companies)',
  allowWithoutAuth: true, // No API key required
};

// ============================================================================
// PRODUCT HUNT (PRODUCTS + FUNDING INFO)
// ============================================================================

export const productHunt: FundingCollectorConfig = {
  name: 'producthunt',
  displayName: '🔥 Product Hunt Launches',
  url: 'https://api.producthunt.com/v2/api/graphql',
  method: 'POST',
  graphqlQuery: `
    query {
      posts(first: 50, order: VOTES) {
        edges {
          node {
            id
            name
            tagline
            description
            website
            votesCount
            createdAt
            topics {
              edges {
                node {
                  name
                }
              }
            }
          }
        }
      }
    }
  `,
  headers: (env) => ({
    'Authorization': `Bearer ${env.PRODUCTHUNT_TOKEN}`,
    'Content-Type': 'application/json',
  }),
  timeout: 30000,
  parseResponse: async (data) => {
    // Product Hunt GraphQL response parsing
    if (data?.errors) {
      console.log(`   ❌ GraphQL Errors:`, JSON.stringify(data.errors, null, 2));
      return [];
    }

    const posts = data?.data?.posts?.edges || [];

    return posts.map((edge: any) => {
      const post = edge.node;
      return {
        company_name: post.name,
        round_type: 'Product Launch',
        sector: post.topics?.edges?.map((t: any) => t.node.name).join(', ').slice(0, 255) || null,
        country: null, // ProductHunt doesn't provide location
        website: post.website || null,
        description: post.tagline?.slice(0, 500) || null,
        announced_date: post.createdAt ? new Date(post.createdAt) : null,
        source: 'producthunt',
        metadata: {
          votes: post.votesCount || 0,
        },
      };
    });
  },
  schedule: '0 11 * * *', // Daily at 11am UTC
  description: 'Product Hunt daily launches and startup data',
  allowWithoutAuth: false, // Requires API token
};

// ============================================================================
// CRUNCHBASE FREE API (500 req/month)
// ============================================================================

export const crunchbase: FundingCollectorConfig = {
  name: 'crunchbase',
  displayName: '💰 Crunchbase Funding Rounds',
  url: 'https://api.crunchbase.com/api/v4/searches/funding_rounds',
  method: 'POST',
  headers: (env) => ({
    'X-cb-user-key': env.CRUNCHBASE_API_KEY || '',
    'Content-Type': 'application/json',
  }),
  body: (env) => JSON.stringify({
    field_ids: [
      'identifier',
      'announced_on',
      'funded_organization_identifier',
      'funding_type',
      'money_raised',
      'investor_identifiers',
      'lead_investor_identifiers',
    ],
    order: [{ field_id: 'announced_on', sort: 'desc' }],
    query: [
      {
        type: 'predicate',
        field_id: 'announced_on',
        operator_id: 'gte',
        values: [new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]],
      },
      {
        type: 'predicate',
        field_id: 'funding_type',
        operator_id: 'includes',
        values: ['seed', 'series_a', 'series_b', 'series_c', 'series_d', 'series_e', 'venture', 'pre_seed'],
      },
    ],
    limit: 15, // 15 rounds/day = 450/month (leaves buffer for 500 limit)
  }),
  timeout: 30000,
  parseResponse: async (data) => {
    const entities = data?.entities || [];

    return entities.map((entity: any) => {
      const props = entity?.properties || {};
      const org = props.funded_organization_identifier || {};
      const money = props.money_raised || {};
      const investors = (props.investor_identifiers || []).map((inv: any) => inv.value).filter(Boolean);
      const leadInvestors = (props.lead_investor_identifiers || []).map((inv: any) => inv.value).filter(Boolean);

      return {
        company_name: org.value || 'Unknown',
        round_type: props.funding_type || 'Unknown',
        amount_usd: money.value_usd || null,
        announced_date: props.announced_on?.value || null,
        investors: [...investors, ...leadInvestors].slice(0, 10), // Limit investors
        source: 'crunchbase',
        metadata: {
          uuid: props.identifier?.uuid,
          permalink: props.identifier?.permalink,
        },
      };
    });
  },
  schedule: '0 12 * * *', // Daily at 12pm UTC (15 rounds/day)
  description: 'Crunchbase funding rounds (15 recent rounds daily, free tier)',
  allowWithoutAuth: false,
};

// ============================================================================
// TECHCRUNCH RSS FEED (Funding News)
// ============================================================================

export const techcrunch: FundingCollectorConfig = {
  name: 'techcrunch',
  displayName: '📰 TechCrunch Funding News',
  url: 'https://techcrunch.com/feed/',
  timeout: 30000,
  parseResponse: async (xmlData) => {
    // Parse XML RSS feed using regex (simple approach, no external deps)
    const itemMatches = xmlData.matchAll(/<item>([\s\S]*?)<\/item>/g);
    const items = Array.from(itemMatches).map(match => match[1]);

    const fundingKeywords = [
      'raises', 'raised', 'funding', 'series a', 'series b', 'series c',
      'seed round', 'venture capital', 'million', 'billion', 'ipo', 'acquisition',
    ];

    return items
      .map((itemXml) => {
        // Extract fields using regex
        const title = itemXml.match(/<title><!\[CDATA\[(.*?)\]\]><\/title>/)?.[1] ||
                      itemXml.match(/<title>(.*?)<\/title>/)?.[1] || '';
        const description = itemXml.match(/<description><!\[CDATA\[(.*?)\]\]><\/description>/)?.[1] ||
                            itemXml.match(/<description>(.*?)<\/description>/)?.[1] || '';
        const link = itemXml.match(/<link>(.*?)<\/link>/)?.[1] || '';
        const pubDate = itemXml.match(/<pubDate>(.*?)<\/pubDate>/)?.[1] || '';

        const text = `${title} ${description}`.toLowerCase();

        // Check if funding-related
        const hasFundingKeyword = fundingKeywords.some((keyword) => text.includes(keyword));
        if (!hasFundingKeyword) return null;

        // Extract company name (first capitalized word)
        const companyMatch = title.match(/([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)/);
        const companyName = companyMatch?.[1] || 'Unknown';

        // Extract amount (e.g., "$10M", "$450 million")
        const amountMatch = text.match(/\$(\d+(?:\.\d+)?)\s?(million|billion|m|b)\b/i);
        let amountUsd: number | null = null;
        if (amountMatch) {
          const value = parseFloat(amountMatch[1]);
          const unit = amountMatch[2].toLowerCase();
          amountUsd = unit.startsWith('m') ? value * 1_000_000 : value * 1_000_000_000;
        }

        // Extract round type
        let roundType = 'VC Funding';
        if (text.includes('series a')) roundType = 'Series A';
        else if (text.includes('series b')) roundType = 'Series B';
        else if (text.includes('series c')) roundType = 'Series C';
        else if (text.includes('seed')) roundType = 'Seed';
        else if (text.includes('ipo')) roundType = 'IPO';
        else if (text.includes('acquisition') || text.includes('acquired')) roundType = 'Acquisition';

        // Parse date
        let announcedDate: Date | null = null;
        if (pubDate) {
          try {
            announcedDate = new Date(pubDate);
          } catch (e) {
            // Ignore invalid dates
          }
        }

        return {
          company_name: companyName,
          round_type: roundType,
          amount_usd: amountUsd,
          announced_date: announcedDate,
          source: 'techcrunch',
          metadata: {
            article_title: title.slice(0, 500),
            article_link: link,
          },
        };
      })
      .filter(Boolean); // Remove nulls
  },
  schedule: '0 13 * * *', // Daily at 1pm UTC
  description: 'TechCrunch RSS feed for funding announcements',
  allowWithoutAuth: true,
};

// ============================================================================
// EXPORT ALL COLLECTORS
// ============================================================================

export const fundingCollectors = {
  'yc-companies': ycCompanies,
  'producthunt': productHunt,
  'crunchbase': crunchbase,
  'techcrunch': techcrunch,
};
