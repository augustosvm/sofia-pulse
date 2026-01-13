#!/usr/bin/env tsx
/**
 * TechCrunch RSS Funding Collector
 *
 * Collects funding announcements from TechCrunch RSS feed
 * Uses NLP/regex to extract:
 * - Company names
 * - Funding amounts ($10M, $450 million, etc)
 * - Round types (Seed, Series A/B/C, IPO, Acquisition)
 *
 * Schedule: Daily 13:00 UTC
 * Source: https://techcrunch.com/feed/
 */

import { Pool } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD || '',
  database: process.env.POSTGRES_DB || 'sofia_db',
});

interface FundingRound {
  company_name: string;
  round_type: string;
  amount_usd: number | null;
  announced_date: Date | null;
  article_title: string;
  article_link: string;
}

const FUNDING_KEYWORDS = [
  'raises', 'raised', 'funding', 'series a', 'series b', 'series c', 'series d', 'series e',
  'seed round', 'venture capital', 'million', 'billion', 'ipo', 'acquisition', 'acquired',
  'closes', 'secures', 'lands', 'gets', 'snags', 'scores',
];

async function fetchTechCrunchRSS(): Promise<string> {
  const response = await fetch('https://techcrunch.com/feed/', {
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; SofiaPulse/1.0; +https://github.com/augustosvm/sofia-pulse)',
    },
  });

  if (!response.ok) {
    throw new Error(`TechCrunch RSS fetch failed: ${response.status}`);
  }

  return await response.text();
}

function parseRSSFeed(xmlData: string): FundingRound[] {
  // Parse XML RSS feed using regex (simple approach, no external deps)
  const itemMatches = xmlData.matchAll(/<item>([\s\S]*?)<\/item>/g);
  const items = Array.from(itemMatches).map(match => match[1]);

  const fundingRounds: FundingRound[] = [];

  for (const itemXml of items) {
    // Extract fields using regex
    const title = itemXml.match(/<title><!\[CDATA\[(.*?)\]\]><\/title>/)?.[1] ||
                  itemXml.match(/<title>(.*?)<\/title>/)?.[1] || '';
    const description = itemXml.match(/<description><!\[CDATA\[(.*?)\]\]><\/description>/)?.[1] ||
                        itemXml.match(/<description>(.*?)<\/description>/)?.[1] || '';
    const link = itemXml.match(/<link>(.*?)<\/link>/)?.[1] || '';
    const pubDate = itemXml.match(/<pubDate>(.*?)<\/pubDate>/)?.[1] || '';

    const text = `${title} ${description}`.toLowerCase();

    // Check if funding-related
    const hasFundingKeyword = FUNDING_KEYWORDS.some((keyword) => text.includes(keyword));
    if (!hasFundingKeyword) continue;

    // Extract company name (first capitalized word/phrase before "raises" or "gets")
    let companyName = 'Unknown';
    const companyPatterns = [
      // "Acme Corp raises $10M"
      /^([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s+(?:raises|raised|gets|lands|closes|secures|snags|scores)/,
      // "Startup Acme Corp raises"
      /\b([A-Z][A-Za-z]+(?:\.[A-Za-z]+)?)\s+(?:raises|raised|gets)/,
      // First capitalized phrase in title
      /([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,3})/,
    ];

    for (const pattern of companyPatterns) {
      const match = title.match(pattern);
      if (match?.[1]) {
        companyName = match[1].trim();
        break;
      }
    }

    // Extract amount (e.g., "$10M", "$450 million", "$1.5B")
    const amountPatterns = [
      /\$(\d+(?:\.\d+)?)\s?(million|billion|m|b)\b/i,
      /(\d+(?:\.\d+)?)\s?\$(million|m)\b/i, // "10 million" or "10M"
    ];

    let amountUsd: number | null = null;
    for (const pattern of amountPatterns) {
      const match = text.match(pattern);
      if (match) {
        const value = parseFloat(match[1]);
        const unit = match[2].toLowerCase();
        amountUsd = unit.startsWith('b') ? value * 1_000_000_000 : value * 1_000_000;
        break;
      }
    }

    // Extract round type
    let roundType = 'VC Funding';
    if (text.includes('series a') || text.includes('series-a')) roundType = 'Series A';
    else if (text.includes('series b') || text.includes('series-b')) roundType = 'Series B';
    else if (text.includes('series c') || text.includes('series-c')) roundType = 'Series C';
    else if (text.includes('series d') || text.includes('series-d')) roundType = 'Series D';
    else if (text.includes('series e') || text.includes('series-e')) roundType = 'Series E';
    else if (text.includes('seed') || text.includes('pre-seed')) roundType = 'Seed';
    else if (text.includes('ipo') || text.includes('goes public')) roundType = 'IPO';
    else if (text.includes('acquisition') || text.includes('acquired') || text.includes('acquires')) roundType = 'Acquisition';

    // Parse date
    let announcedDate: Date | null = null;
    if (pubDate) {
      try {
        announcedDate = new Date(pubDate);
      } catch (e) {
        // Ignore invalid dates
      }
    }

    fundingRounds.push({
      company_name: companyName,
      round_type: roundType,
      amount_usd: amountUsd,
      announced_date: announcedDate,
      article_title: title.slice(0, 500),
      article_link: link,
    });
  }

  return fundingRounds;
}

async function saveToDatabase(fundingRounds: FundingRound[]): Promise<number> {
  if (fundingRounds.length === 0) return 0;

  const client = await pool.connect();
  let saved = 0;

  try {
    for (const round of fundingRounds) {
      try {
        // Get or create organization (simplified - just use normalized name)
        let organizationId: number | null = null;
        if (round.company_name !== 'Unknown') {
          const normalized = round.company_name.toLowerCase().replace(/[^a-z0-9]/g, '_');
          const orgResult = await client.query(
            `INSERT INTO sofia.organizations (name, normalized_name, type, created_at)
             VALUES ($1, $2, $3, NOW())
             ON CONFLICT (normalized_name) DO UPDATE SET name = EXCLUDED.name
             RETURNING id`,
            [round.company_name, normalized, 'startup']
          );
          organizationId = orgResult.rows[0]?.id || null;
        }

        // Insert funding round
        await client.query(
          `INSERT INTO sofia.funding_rounds (
            company_name, organization_id, round_type, amount_usd,
            announced_date, country, source, collected_at
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
          ON CONFLICT (company_name, round_type, announced_date)
          DO UPDATE SET
            amount_usd = COALESCE(EXCLUDED.amount_usd, sofia.funding_rounds.amount_usd),
            organization_id = COALESCE(EXCLUDED.organization_id, sofia.funding_rounds.organization_id),
            collected_at = NOW()`,
          [
            round.company_name,
            organizationId,
            round.round_type,
            round.amount_usd,
            round.announced_date,
            'USA', // TechCrunch primarily covers US companies
            'techcrunch',
          ]
        );

        saved++;
        console.log(`  ✅ ${round.company_name} - ${round.round_type}${round.amount_usd ? ` ($${(round.amount_usd / 1_000_000).toFixed(1)}M)` : ''}`);
      } catch (error: any) {
        console.error(`  ❌ Error saving ${round.company_name}: ${error.message}`);
      }
    }

    await client.query('COMMIT');
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }

  return saved;
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('📰 TECHCRUNCH FUNDING NEWS COLLECTOR');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('Fetching RSS feed...\n');

  try {
    // Fetch RSS feed
    const xmlData = await fetchTechCrunchRSS();
    console.log('✅ RSS feed fetched\n');

    // Parse funding announcements
    const fundingRounds = parseRSSFeed(xmlData);
    console.log(`📊 Found ${fundingRounds.length} funding-related articles\n`);

    if (fundingRounds.length === 0) {
      console.log('⚠️  No funding announcements found in recent articles');
      return;
    }

    // Show what we found
    console.log('Funding rounds detected:');
    fundingRounds.forEach(round => {
      const amount = round.amount_usd ? `$${(round.amount_usd / 1_000_000).toFixed(1)}M` : 'Amount N/A';
      console.log(`  • ${round.company_name} - ${round.round_type} - ${amount}`);
    });
    console.log('');

    // Save to database
    console.log('💾 Saving to database...\n');
    const saved = await saveToDatabase(fundingRounds);

    console.log('');
    console.log('═══════════════════════════════════════════════════════════════');
    console.log(`✅ Saved ${saved}/${fundingRounds.length} funding rounds`);
    console.log('═══════════════════════════════════════════════════════════════');
  } catch (error: any) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
