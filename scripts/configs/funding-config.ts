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
        announced_date: null, // YC doesn't provide exact dates
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
// EXPORT ALL COLLECTORS
// ============================================================================

export const fundingCollectors = {
  'yc-companies': ycCompanies,
  'producthunt': productHunt,
};
