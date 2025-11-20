#!/usr/bin/env node

// Fix for Node.js 18 + undici - MUST BE AFTER SHEBANG!
// @ts-ignore
if (typeof File === 'undefined') {
  // @ts-ignore
  globalThis.File = class File extends Blob {
    constructor(bits: any[], name: string, options?: any) {
      super(bits, options);
    }
  };
}

/**
 * Cybersecurity Collector - Sofia Pulse
 *
 * Coleta dados de:
 * - CVE Database (National Vulnerability Database)
 * - GitHub Security Advisories
 * - CISA Known Exploited Vulnerabilities
 */

import { Pool } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  user: process.env.DB_USER || 'sofia',
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME || 'sofia_db',
});

interface CyberEvent {
  event_type: string;
  event_id: string;
  title: string;
  description: string | null;
  severity: string | null;
  cvss_score: number | null;
  affected_products: string[] | null;
  vendors: string[] | null;
  published_date: Date;
  source: string;
  source_url: string | null;
  tags: string[] | null;
}

/**
 * Coleta CVEs recentes do NVD (via API pública)
 */
async function collectCVEs(): Promise<CyberEvent[]> {
  console.log('📡 Fetching CVEs from NVD...');

  try {
    const response = await fetch(
      'https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=100'
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    const events: CyberEvent[] = [];

    for (const item of data.vulnerabilities || []) {
      const cve = item.cve;

      // Extract CVSS score
      let cvssScore = null;
      let severity = null;

      if (cve.metrics?.cvssMetricV31?.[0]) {
        cvssScore = cve.metrics.cvssMetricV31[0].cvssData.baseScore;
        severity = cve.metrics.cvssMetricV31[0].cvssData.baseSeverity?.toLowerCase();
      } else if (cve.metrics?.cvssMetricV2?.[0]) {
        cvssScore = cve.metrics.cvssMetricV2[0].cvssData.baseScore;
        severity = cve.metrics.cvssMetricV2[0].baseSeverity?.toLowerCase();
      }

      // Extract description
      const description = cve.descriptions?.find((d: any) => d.lang === 'en')?.value || null;

      // Extract vendors/products
      const vendors: string[] = [];
      const products: string[] = [];

      if (cve.configurations) {
        for (const config of cve.configurations) {
          for (const node of config.nodes || []) {
            for (const cpeMatch of node.cpeMatch || []) {
              const cpe = cpeMatch.criteria || '';
              const parts = cpe.split(':');
              if (parts.length >= 5) {
                if (parts[3] && !vendors.includes(parts[3])) {
                  vendors.push(parts[3]);
                }
                if (parts[4] && !products.includes(parts[4])) {
                  products.push(parts[4]);
                }
              }
            }
          }
        }
      }

      events.push({
        event_type: 'cve',
        event_id: cve.id,
        title: cve.id,
        description,
        severity,
        cvss_score: cvssScore,
        affected_products: products.length > 0 ? products : null,
        vendors: vendors.length > 0 ? vendors : null,
        published_date: new Date(cve.published),
        source: 'nvd',
        source_url: `https://nvd.nist.gov/vuln/detail/${cve.id}`,
        tags: null,
      });
    }

    console.log(`   ✅ Collected ${events.length} CVEs`);
    return events;

  } catch (error: any) {
    console.error(`   ❌ Error collecting CVEs: ${error.message}`);
    return [];
  }
}

/**
 * Coleta GitHub Security Advisories
 */
async function collectGitHubAdvisories(): Promise<CyberEvent[]> {
  console.log('📡 Fetching GitHub Security Advisories...');

  try {
    // GitHub Advisory Database (public RSS/API)
    const response = await fetch(
      'https://api.github.com/advisories?per_page=100',
      {
        headers: {
          'Accept': 'application/vnd.github+json',
          'User-Agent': 'Sofia-Pulse/1.0'
        }
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const advisories = await response.json();
    const events: CyberEvent[] = [];

    for (const adv of advisories) {
      events.push({
        event_type: 'advisory',
        event_id: adv.ghsa_id,
        title: adv.summary || adv.ghsa_id,
        description: adv.description,
        severity: adv.severity?.toLowerCase(),
        cvss_score: adv.cvss?.score || null,
        affected_products: adv.identifiers
          ?.filter((i: any) => i.type === 'PACKAGE')
          .map((i: any) => i.value) || null,
        vendors: null,
        published_date: new Date(adv.published_at),
        source: 'github',
        source_url: adv.html_url,
        tags: adv.cwe_ids || null,
      });
    }

    console.log(`   ✅ Collected ${events.length} GitHub advisories`);
    return events;

  } catch (error: any) {
    console.error(`   ❌ Error collecting GitHub advisories: ${error.message}`);
    return [];
  }
}

/**
 * Coleta CISA Known Exploited Vulnerabilities
 */
async function collectCISAVulnerabilities(): Promise<CyberEvent[]> {
  console.log('📡 Fetching CISA Known Exploited Vulnerabilities...');

  try {
    const response = await fetch(
      'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json'
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    const events: CyberEvent[] = [];

    // Get only recent ones (last 90 days)
    const ninetyDaysAgo = new Date();
    ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);

    for (const vuln of data.vulnerabilities || []) {
      const dateAdded = new Date(vuln.dateAdded);

      if (dateAdded >= ninetyDaysAgo) {
        events.push({
          event_type: 'cve',
          event_id: vuln.cveID,
          title: vuln.vulnerabilityName,
          description: vuln.shortDescription,
          severity: 'high', // CISA KEV are all high/critical
          cvss_score: null,
          affected_products: vuln.product ? [vuln.product] : null,
          vendors: vuln.vendorProject ? [vuln.vendorProject] : null,
          published_date: dateAdded,
          source: 'cisa',
          source_url: `https://www.cisa.gov/known-exploited-vulnerabilities-catalog`,
          tags: ['exploited', 'active-threat'],
        });
      }
    }

    console.log(`   ✅ Collected ${events.length} CISA vulnerabilities`);
    return events;

  } catch (error: any) {
    console.error(`   ❌ Error collecting CISA vulnerabilities: ${error.message}`);
    return [];
  }
}

/**
 * Salva eventos no banco
 */
async function saveEvents(events: CyberEvent[]): Promise<void> {
  if (events.length === 0) {
    console.log('   ⚠️  No events to save');
    return;
  }

  const client = await pool.connect();

  try {
    let inserted = 0;
    let skipped = 0;

    for (const event of events) {
      try {
        await client.query(
          `
          INSERT INTO sofia.cybersecurity_events (
            event_type, event_id, title, description, severity,
            cvss_score, affected_products, vendors, published_date,
            source, source_url, tags
          )
          VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
          ON CONFLICT (event_id) DO UPDATE SET
            description = EXCLUDED.description,
            severity = EXCLUDED.severity,
            cvss_score = EXCLUDED.cvss_score,
            affected_products = EXCLUDED.affected_products,
            vendors = EXCLUDED.vendors,
            tags = EXCLUDED.tags
          `,
          [
            event.event_type,
            event.event_id,
            event.title,
            event.description,
            event.severity,
            event.cvss_score,
            event.affected_products,
            event.vendors,
            event.published_date,
            event.source,
            event.source_url,
            event.tags,
          ]
        );
        inserted++;
      } catch (err: any) {
        skipped++;
      }
    }

    console.log(`   ✅ Inserted: ${inserted}, Skipped: ${skipped}`);

  } finally {
    client.release();
  }
}

async function main() {
  console.log('════════════════════════════════════════════════════════════════');
  console.log('🔒 CYBERSECURITY COLLECTOR');
  console.log('════════════════════════════════════════════════════════════════');
  console.log('');

  try {
    // Collect from all sources
    const [cves, advisories, cisaVulns] = await Promise.all([
      collectCVEs(),
      collectGitHubAdvisories(),
      collectCISAVulnerabilities(),
    ]);

    // Combine all
    const allEvents = [...cves, ...advisories, ...cisaVulns];

    console.log('');
    console.log(`📊 Total collected: ${allEvents.length} events`);
    console.log('');

    // Save to database
    console.log('💾 Saving to database...');
    await saveEvents(allEvents);

    console.log('');
    console.log('✅ Cybersecurity collection complete!');
    console.log('');

  } catch (error: any) {
    console.error(`❌ Error: ${error.message}`);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
