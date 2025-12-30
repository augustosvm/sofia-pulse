
import { SignalData } from '../collectors/industry-signals-inserter.js';
import axios from 'axios';

export interface SignalCollectorConfig {
    name: string;
    displayName: string;
    description: string;
    url?: string;
    parseResponse: (data: any) => Promise<SignalData[]> | SignalData[];
    schedule: string;
    allowWithoutAuth?: boolean;
}

// ============================================================================
// GDELT
// ============================================================================
export const gdeltEvents: SignalCollectorConfig = {
    name: 'gdelt',
    displayName: '🌍 GDELT Events',
    description: 'Global geopolitical and tech events',
    schedule: '0 * * * *', // Hourly

    // Custom fetch logic to handle multiple keywords
    // Placeholder URL as we construct it dynamically
    url: 'https://api.gdeltproject.org/api/v2/doc/doc',

    parseResponse: async () => {
        const keywords = [
            'technology', 'AI', 'artificial intelligence', 'semiconductor',
            'cybersecurity', 'data breach', 'regulation tech'
        ];

        const now = new Date();
        const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        const dateStr = yesterday.toISOString().slice(0, 10).replace(/-/g, '');

        const allEvents: SignalData[] = [];

        // Fetch for each keyword (sequential to be nice to API)
        for (const keyword of keywords.slice(0, 4)) {
            try {
                const url = `https://api.gdeltproject.org/api/v2/doc/doc?query=${encodeURIComponent(keyword)}&mode=artlist&format=json&maxrecords=20&startdatetime=${dateStr}000000&enddatetime=${dateStr}235959`;
                const response = await axios.get(url, { timeout: 10000 });

                if (response.data?.articles) {
                    const events = response.data.articles.map((art: any): SignalData => ({
                        source: 'gdelt',
                        external_id: `${dateStr}-${art.url_hash || Math.random().toString(36).substr(2, 9)}`,
                        title: art.title || art.domain || 'Unknown Event',
                        summary: `GDELT Event involving ${art.domain}. Tone: ${art.tone}`,
                        url: art.url,
                        category: 'geopolitics',
                        signal_type: 'event',
                        impact_score: parseFloat(art.tone) > 0 ? parseFloat(art.tone) : parseFloat(art.tone) * -1,
                        sentiment_score: parseFloat(art.tone),
                        metadata: {
                            actor1: art.domain,
                            language: art.sourcelang,
                            keyword: keyword
                        },
                        published_at: new Date()
                    }));
                    allEvents.push(...events);
                }
                // tiny delay
                await new Promise(r => setTimeout(r, 500));
            } catch (err) {
                console.error(`Error fetching GDELT for ${keyword}:`, err);
            }
        }
        return allEvents;
    }
};

// ============================================================================
// AI REGULATION
// ============================================================================
export const aiRegulation: SignalCollectorConfig = {
    name: 'ai_regulation',
    displayName: '⚖️ AI Regulation',
    description: 'Global AI laws and policies',
    schedule: '0 0 * * *', // Daily
    url: '', // Static list for now

    parseResponse: async () => {
        // Static list from original script
        return [
            {
                source: 'ai-reg-tracker',
                external_id: 'eu-ai-act',
                title: 'EU Artificial Intelligence Act',
                summary: 'Comprehensive AI regulation framework for the European Union.',
                url: 'https://artificialintelligenceact.eu/',
                category: 'ai_regulation',
                signal_type: 'law',
                impact_score: 10,
                sentiment_score: 0,
                metadata: { jurisdiction: 'EU', status: 'enacted', effective: '2026-01-01' },
                published_at: new Date('2024-03-13')
            },
            {
                source: 'ai-reg-tracker',
                external_id: 'br-lgpd',
                title: 'Lei Geral de Proteção de Dados (LGPD)',
                summary: 'Brazilian data protection law affecting AI.',
                url: 'https://www.gov.br/anpd/pt-br',
                category: 'ai_regulation',
                signal_type: 'law',
                impact_score: 8,
                sentiment_score: 0,
                metadata: { jurisdiction: 'Brazil', status: 'enforced' },
                published_at: new Date('2020-09-18')
            },
            {
                source: 'ai-reg-tracker',
                external_id: 'us-ai-eo-2023',
                title: 'US Executive Order on Safe AI',
                summary: 'Biden administration executive order on AI safety.',
                url: 'https://whitehouse.gov',
                category: 'ai_regulation',
                signal_type: 'policy',
                impact_score: 9,
                sentiment_score: 5,
                metadata: { jurisdiction: 'USA', status: 'enforced' },
                published_at: new Date('2023-10-30')
            }
        ];
    }
};

// ============================================================================
// CYBERSECURITY: NVD (CVEs)
// ============================================================================
export const nvdCves: SignalCollectorConfig = {
    name: 'nvd_cve',
    displayName: '🔒 NVD Vulnerabilities',
    description: 'National Vulnerability Database CVEs',
    schedule: '0 */4 * * *', // Every 4h
    url: 'https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=100',

    parseResponse: (data: any) => {
        const events: SignalData[] = [];
        if (!data.vulnerabilities) return [];

        for (const item of data.vulnerabilities) {
            const cve = item.cve;
            // Extract metrics
            let score = null;
            let severity = 'unknown';

            if (cve.metrics?.cvssMetricV31?.[0]) {
                score = cve.metrics.cvssMetricV31[0].cvssData.baseScore;
                severity = cve.metrics.cvssMetricV31[0].cvssData.baseSeverity;
            }

            events.push({
                source: 'nvd',
                external_id: cve.id,
                title: cve.id,
                summary: cve.descriptions?.[0]?.value || null,
                url: `https://nvd.nist.gov/vuln/detail/${cve.id}`,
                category: 'security',
                signal_type: 'vulnerability',
                impact_score: score,
                sentiment_score: null, // neutral
                metadata: {
                    severity: severity,
                    published: cve.published,
                    lastModified: cve.lastModified
                },
                published_at: new Date(cve.published)
            });
        }
        return events;
    }
};

// ============================================================================
// CYBERSECURITY: CISA KEV
// ============================================================================
export const cisaKev: SignalCollectorConfig = {
    name: 'cisa_kev',
    displayName: '🚨 CISA Known Exploited',
    description: 'Known Exploited Vulnerabilities Catalog',
    schedule: '0 12 * * *', // Daily
    url: 'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json',

    parseResponse: (data: any) => {
        if (!data.vulnerabilities) return [];

        // Filter last 30 days to avoid massive re-imports
        const limitDate = new Date();
        limitDate.setDate(limitDate.getDate() - 30);

        return data.vulnerabilities
            .filter((v: any) => new Date(v.dateAdded) >= limitDate)
            .map((v: any): SignalData => ({
                source: 'cisa-kev',
                external_id: v.cveID,
                title: v.vulnerabilityName,
                summary: v.shortDescription,
                url: `https://www.cisa.gov/known-exploited-vulnerabilities-catalog`,
                category: 'security',
                signal_type: 'exploit',
                impact_score: 10, // KEV is always critical
                sentiment_score: -10, // Bad news
                metadata: {
                    vendor: v.vendorProject,
                    product: v.product,
                    dateAdded: v.dateAdded
                },
                published_at: new Date(v.dateAdded)
            }));
    }
};

// ============================================================================
// SPACE: Launch Library
// ============================================================================
export const spaceLaunches: SignalCollectorConfig = {
    name: 'space_launches',
    displayName: '🚀 Space Launches',
    description: 'Upcoming and recent rocket launches',
    schedule: '0 */6 * * *',
    url: 'https://ll.thespacedevs.com/2.2.0/launch/?limit=50&mode=detailed',

    parseResponse: (data: any) => {
        if (!data.results) return [];

        return data.results.map((launch: any): SignalData => {
            const company = launch.launch_service_provider?.name || 'Unknown';
            return {
                source: 'launch-library',
                external_id: launch.id,
                title: `${launch.name} (${company})`,
                summary: launch.mission?.description,
                url: launch.url,
                category: 'space',
                signal_type: 'launch',
                impact_score: launch.status?.id === 3 ? 10 : 5, // 3=Success
                sentiment_score: null,
                metadata: {
                    rocket: launch.rocket?.configuration?.name,
                    pad: launch.pad?.name,
                    status: launch.status?.name,
                    orbit: launch.mission?.orbit?.name
                },
                published_at: new Date(launch.net)
            };
        });
    }
};

// ============================================================================
// EXPORTS
// ============================================================================
export const collectors: Record<string, SignalCollectorConfig> = {
    nvd: nvdCves,
    cisa: cisaKev,
    space: spaceLaunches,
    gdelt: gdeltEvents,
    ai_regulation: aiRegulation
};
