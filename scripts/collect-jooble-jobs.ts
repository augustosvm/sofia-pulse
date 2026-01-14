#!/usr/bin/env npx tsx
/**
 * Jooble Jobs API Collector
 * Global job aggregator with 70+ countries
 * Free API with 500 requests/day
 * https://jooble.org/api/about
 */

import axios from 'axios';
import { Pool } from 'pg';
import dotenv from 'dotenv';
import { getKeywordsByLanguage } from './shared/keywords-config';
import { normalizeLocation } from './shared/geo-helpers.js';
import { getOrCreateOrganization } from './shared/org-helpers.js';

dotenv.config();

const dbConfig = {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB || 'sofia_db',
};

const JOOBLE_API_KEY = process.env.JOOBLE_API_KEY;

// Countries to collect from (Jooble supports 70+ countries)
// API uses single endpoint with location parameter
const COUNTRIES = [
    { code: 'br', name: 'Brazil', location: 'Brazil' },
    { code: 'us', name: 'United States', location: 'United States' },
    { code: 'gb', name: 'United Kingdom', location: 'United Kingdom' },
    { code: 'de', name: 'Germany', location: 'Germany' },
    { code: 'fr', name: 'France', location: 'France' },
    { code: 'ca', name: 'Canada', location: 'Canada' },
    { code: 'au', name: 'Australia', location: 'Australia' },
    { code: 'in', name: 'India', location: 'India' },
    { code: 'nl', name: 'Netherlands', location: 'Netherlands' },
    { code: 'es', name: 'Spain', location: 'Spain' },
    { code: 'pt', name: 'Portugal', location: 'Portugal' },
    { code: 'mx', name: 'Mexico', location: 'Mexico' },
];

// Jooble API endpoint (single global endpoint)
const JOOBLE_API_URL = 'https://jooble.org/api';

// Keywords for each language
const KEYWORDS_BY_LANG: Record<string, string[]> = {
    en: ['software engineer', 'developer', 'data scientist', 'devops', 'frontend', 'backend', 'fullstack', 'machine learning', 'cloud engineer', 'cybersecurity'],
    pt: ['desenvolvedor', 'programador', 'engenheiro de software', 'analista de sistemas', 'devops', 'frontend', 'backend', 'dados', 'segurança da informação'],
    de: ['softwareentwickler', 'entwickler', 'programmierer', 'devops', 'frontend', 'backend'],
    fr: ['développeur', 'ingénieur logiciel', 'programmeur', 'devops', 'frontend', 'backend'],
    es: ['desarrollador', 'programador', 'ingeniero de software', 'devops', 'frontend', 'backend'],
    it: ['sviluppatore', 'programmatore', 'ingegnere software', 'devops', 'frontend', 'backend'],
};

interface JoobleJob {
    title: string;
    location: string;
    snippet: string;
    salary: string;
    source: string;
    type: string;
    link: string;
    company: string;
    updated: string;
    id: string;
}

interface JoobleResponse {
    jobs: JoobleJob[];
    totalCount: number;
}

function getLanguageForCountry(countryCode: string): string {
    const langMap: Record<string, string> = {
        br: 'pt', pt: 'pt',
        us: 'en', gb: 'en', ca: 'en', au: 'en', in: 'en',
        de: 'de',
        fr: 'fr',
        es: 'es', mx: 'es', ar: 'es', cl: 'es',
        it: 'it',
        nl: 'en', // Dutch jobs often use English
    };
    return langMap[countryCode] || 'en';
}

function parseSalary(salaryStr: string): { min: number | null; max: number | null; currency: string; period: string } {
    if (!salaryStr) return { min: null, max: null, currency: 'USD', period: 'year' };

    // Try to extract numbers
    const numbers = salaryStr.match(/[\d,.]+/g);
    if (!numbers || numbers.length === 0) return { min: null, max: null, currency: 'USD', period: 'year' };

    const cleanNumbers = numbers.map(n => parseFloat(n.replace(/,/g, '')));

    // Detect currency
    let currency = 'USD';
    if (salaryStr.includes('R$') || salaryStr.includes('BRL')) currency = 'BRL';
    else if (salaryStr.includes('£') || salaryStr.includes('GBP')) currency = 'GBP';
    else if (salaryStr.includes('€') || salaryStr.includes('EUR')) currency = 'EUR';
    else if (salaryStr.includes('$')) currency = 'USD';

    // Detect period
    let period = 'year';
    const lowerSalary = salaryStr.toLowerCase();
    if (lowerSalary.includes('hour') || lowerSalary.includes('hora')) period = 'hour';
    else if (lowerSalary.includes('month') || lowerSalary.includes('mês') || lowerSalary.includes('mes')) period = 'month';
    else if (lowerSalary.includes('week') || lowerSalary.includes('semana')) period = 'week';

    return {
        min: cleanNumbers[0] || null,
        max: cleanNumbers.length > 1 ? cleanNumbers[1] : cleanNumbers[0],
        currency,
        period
    };
}

function detectRemoteType(title: string, snippet: string): string {
    const text = `${title} ${snippet}`.toLowerCase();
    if (text.includes('remote') || text.includes('remoto') || text.includes('home office') || text.includes('trabalho remoto')) {
        if (text.includes('hybrid') || text.includes('híbrido') || text.includes('hibrido')) return 'hybrid';
        return 'remote';
    }
    if (text.includes('on-site') || text.includes('presencial') || text.includes('onsite')) return 'onsite';
    return 'unknown';
}

function detectSeniority(title: string): string {
    const lowerTitle = title.toLowerCase();
    if (lowerTitle.includes('senior') || lowerTitle.includes('sr.') || lowerTitle.includes('sênior') || lowerTitle.includes('pleno')) return 'senior';
    if (lowerTitle.includes('junior') || lowerTitle.includes('jr.') || lowerTitle.includes('júnior') || lowerTitle.includes('trainee') || lowerTitle.includes('estágio') || lowerTitle.includes('intern')) return 'entry';
    if (lowerTitle.includes('lead') || lowerTitle.includes('principal') || lowerTitle.includes('staff') || lowerTitle.includes('architect')) return 'lead';
    if (lowerTitle.includes('manager') || lowerTitle.includes('director') || lowerTitle.includes('head') || lowerTitle.includes('gerente') || lowerTitle.includes('coordenador')) return 'manager';
    return 'mid';
}

function extractSkills(text: string): string[] {
    const skillPatterns = [
        'python', 'java', 'javascript', 'typescript', 'c#', 'c\\+\\+', 'go', 'golang', 'rust', 'ruby', 'php', 'swift', 'kotlin',
        'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'spring', 'rails', '.net', 'laravel',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'ci/cd',
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'nlp',
        'git', 'linux', 'agile', 'scrum'
    ];

    const lowerText = text.toLowerCase();
    return skillPatterns.filter(skill => {
        const regex = new RegExp(`\\b${skill}\\b`, 'i');
        return regex.test(lowerText);
    });
}

function detectSector(title: string, snippet: string): string {
    const text = `${title} ${snippet}`.toLowerCase();

    if (text.includes('frontend') || text.includes('front-end') || text.includes('react') || text.includes('angular') || text.includes('vue')) return 'Frontend';
    if (text.includes('backend') || text.includes('back-end') || text.includes('api') || text.includes('servidor')) return 'Backend';
    if (text.includes('fullstack') || text.includes('full-stack') || text.includes('full stack')) return 'Fullstack';
    if (text.includes('devops') || text.includes('sre') || text.includes('infrastructure') || text.includes('cloud')) return 'DevOps';
    if (text.includes('data') || text.includes('dados') || text.includes('analytics') || text.includes('bi ') || text.includes('business intelligence')) return 'Data';
    if (text.includes('machine learning') || text.includes('ml ') || text.includes('ai ') || text.includes('artificial intelligence') || text.includes('deep learning')) return 'AI/ML';
    if (text.includes('mobile') || text.includes('android') || text.includes('ios') || text.includes('flutter') || text.includes('react native')) return 'Mobile';
    if (text.includes('security') || text.includes('segurança') || text.includes('cyber') || text.includes('infosec')) return 'Security';
    if (text.includes('qa') || text.includes('test') || text.includes('quality') || text.includes('qualidade')) return 'QA';
    if (text.includes('manager') || text.includes('lead') || text.includes('gerente') || text.includes('coordenador') || text.includes('diretor')) return 'Leadership';

    return 'Other Tech';
}

async function collectJoobleJobs() {
    console.log('💼 Jooble Jobs API Collector');
    console.log('='.repeat(60));

    if (!JOOBLE_API_KEY) {
        console.error('❌ JOOBLE_API_KEY is required!');
        console.log('\n📝 Get your free API key at: https://jooble.org/api/about');
        process.exit(1);
    }

    const pool = new Pool(dbConfig);
    let totalCollected = 0;
    let totalSaved = 0;

    try {
        for (const country of COUNTRIES) {
            console.log(`\n🌍 Collecting from ${country.name}...`);

            const lang = getLanguageForCountry(country.code);
            const keywords = KEYWORDS_BY_LANG[lang] || KEYWORDS_BY_LANG['en'];

            // Limit keywords per country to avoid rate limits (500 requests/day total)
            const keywordsToUse = keywords.slice(0, 3);

            for (const keyword of keywordsToUse) {
                try {
                    // Jooble API endpoint (single global endpoint)
                    const url = `${JOOBLE_API_URL}/${JOOBLE_API_KEY}`;

                    const response = await axios.post<JoobleResponse>(url, {
                        keywords: keyword,
                        location: country.location,
                        page: 1
                    }, {
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        timeout: 30000
                    });

                    const jobs = response.data.jobs || [];
                    console.log(`   📋 ${keyword}: ${jobs.length} jobs`);
                    totalCollected += jobs.length;

                    for (const job of jobs) {
                        try {
                            // Generate unique job ID
                            const jobId = job.id || `jooble-${Buffer.from(job.link).toString('base64').substring(0, 32)}`;

                            // Parse location
                            const { countryId, stateId, cityId, city, state } = await normalizeLocation(
                                pool,
                                job.location || '',
                                country.name
                            );

                            // Get or create organization
                            const organizationId = job.company ?
                                await getOrCreateOrganization(pool, job.company, country.name) : null;

                            // Parse salary
                            const salary = parseSalary(job.salary);

                            // Detect job attributes
                            const remoteType = detectRemoteType(job.title, job.snippet);
                            const seniority = detectSeniority(job.title);
                            const skills = extractSkills(`${job.title} ${job.snippet}`);
                            const sector = detectSector(job.title, job.snippet);

                            // Parse date
                            let postedDate = null;
                            if (job.updated) {
                                const parsed = new Date(job.updated);
                                if (!isNaN(parsed.getTime())) {
                                    postedDate = parsed.toISOString().split('T')[0];
                                }
                            }

                            await pool.query(`
                                INSERT INTO sofia.jobs (
                                    job_id, title, company, location, city, state, country,
                                    country_id, state_id, city_id,
                                    url, platform, organization_id,
                                    description, salary_min, salary_max, salary_currency, salary_period,
                                    remote_type, seniority_level, employment_type, skills_required, sector,
                                    posted_date, collected_at
                                )
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, NOW())
                                ON CONFLICT (job_id, platform) DO UPDATE SET
                                    title = EXCLUDED.title,
                                    location = EXCLUDED.location,
                                    description = EXCLUDED.description,
                                    salary_min = EXCLUDED.salary_min,
                                    salary_max = EXCLUDED.salary_max,
                                    salary_currency = EXCLUDED.salary_currency,
                                    salary_period = EXCLUDED.salary_period,
                                    remote_type = EXCLUDED.remote_type,
                                    seniority_level = EXCLUDED.seniority_level,
                                    skills_required = EXCLUDED.skills_required,
                                    sector = EXCLUDED.sector,
                                    organization_id = COALESCE(EXCLUDED.organization_id, sofia.jobs.organization_id),
                                    country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
                                    state_id = COALESCE(EXCLUDED.state_id, sofia.jobs.state_id),
                                    city_id = COALESCE(EXCLUDED.city_id, sofia.jobs.city_id),
                                    posted_date = EXCLUDED.posted_date,
                                    collected_at = NOW()
                            `, [
                                jobId,
                                job.title?.substring(0, 500) || 'Unknown',
                                job.company?.substring(0, 255) || null,
                                job.location?.substring(0, 255) || null,
                                city,
                                state,
                                country.name,
                                countryId,
                                stateId,
                                cityId,
                                job.link,
                                'jooble',
                                organizationId,
                                job.snippet?.substring(0, 10000) || null,
                                salary.min,
                                salary.max,
                                salary.currency,
                                salary.period,
                                remoteType,
                                seniority,
                                job.type || 'full-time',
                                skills.length > 0 ? skills.join(', ') : null,
                                sector,
                                postedDate
                            ]);

                            totalSaved++;
                        } catch (error: any) {
                            // Ignore duplicate errors
                            if (error.code !== '23505') {
                                console.error(`   ⚠️ Error saving job: ${error.message}`);
                            }
                        }
                    }

                    // Rate limiting - 2 second delay between requests
                    await new Promise(resolve => setTimeout(resolve, 2000));

                } catch (error: any) {
                    console.error(`   ❌ Error fetching ${keyword}: ${error.message}`);
                }
            }
        }

        console.log('\n' + '='.repeat(60));
        console.log(`✅ Jooble collection complete!`);
        console.log(`   📊 Total collected: ${totalCollected}`);
        console.log(`   💾 Total saved: ${totalSaved}`);

    } catch (error: any) {
        console.error(`\n❌ Fatal error: ${error.message}`);
        throw error;
    } finally {
        await pool.end();
    }
}

// Run standalone if executed directly
collectJoobleJobs().catch(console.error);
