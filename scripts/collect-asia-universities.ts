#!/usr/bin/env tsx

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
 * Sofia Pulse - Asian Universities Data Collector
 *
 * Coleta dados de universidades da Ásia, Japão e Austrália
 *
 * POR QUE UNIVERSIDADES ASIÁTICAS SÃO CRÍTICAS:
 * - China: Maior produtor de PhDs em STEM do mundo
 * - Japão: Líder em pesquisa em materiais e robótica
 * - Coreia: Semiconductores e displays
 * - Singapura: Hub de biotecnologia e fintech
 * - Austrália: Pesquisa biomédica e mineração
 *
 * FONTES:
 * - QS World University Rankings (gratuito)
 * - Times Higher Education (THE) Rankings
 * - Academic Ranking of World Universities (ARWU/Shanghai Ranking)
 * - Scopus/Web of Science data via APIs
 */

import { Client } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

// ============================================================================
// DATABASE SETUP
// ============================================================================

const dbConfig = {
  host: process.env.POSTGRES_HOST || process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || process.env.DB_PORT || '5432'),
  user: process.env.POSTGRES_USER || process.env.DB_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || process.env.DB_PASSWORD || 'postgres',
  database: process.env.POSTGRES_DB || process.env.DB_NAME || 'sofia_db',
};

// ============================================================================
// TYPES
// ============================================================================

interface University {
  name: string;
  name_local?: string; // Nome em língua nativa
  country: string;
  city: string;
  founded_year: number;
  type: string; // 'Public' | 'Private' | 'Research'
  qs_rank?: number;
  the_rank?: number;
  arwu_rank?: number;
  research_output_papers_year: number;
  citations_total: number;
  h_index: number;
  strong_fields: string[]; // Areas de pesquisa forte
  notable_alumni?: string[];
  international_students_pct?: number;
  faculty_count?: number;
  student_count?: number;
}

// ============================================================================
// DATABASE FUNCTIONS
// ============================================================================

async function createTableIfNotExists(client: Client): Promise<void> {
  const createTableQuery = `
    CREATE TABLE IF NOT EXISTS asia_universities (
      id SERIAL PRIMARY KEY,
      name VARCHAR(255) NOT NULL,
      name_local VARCHAR(255),
      country VARCHAR(100) NOT NULL,
      city VARCHAR(100),
      founded_year INT,
      type VARCHAR(50),
      qs_rank INT,
      the_rank INT,
      arwu_rank INT,
      research_output_papers_year INT,
      citations_total BIGINT,
      h_index INT,
      strong_fields TEXT[],
      notable_alumni TEXT[],
      international_students_pct DECIMAL(5,2),
      faculty_count INT,
      student_count INT,
      collected_at TIMESTAMP DEFAULT NOW(),
      UNIQUE(name, country)
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_asia_uni_country
      ON asia_universities(country);

    CREATE INDEX IF NOT EXISTS idx_asia_uni_qs_rank
      ON asia_universities(qs_rank);

    CREATE INDEX IF NOT EXISTS idx_asia_uni_research_output
      ON asia_universities(research_output_papers_year DESC);

    CREATE INDEX IF NOT EXISTS idx_asia_uni_strong_fields
      ON asia_universities USING GIN(strong_fields);
  `;

  await client.query(createTableQuery);
  console.log('✅ Table asia_universities ready');
}

async function insertUniversity(client: Client, uni: University): Promise<void> {
  const insertQuery = `
    INSERT INTO asia_universities (
      name, name_local, country, city, founded_year, type,
      qs_rank, the_rank, arwu_rank,
      research_output_papers_year, citations_total, h_index,
      strong_fields, notable_alumni,
      international_students_pct, faculty_count, student_count
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
    ON CONFLICT (name, country)
    DO UPDATE SET
      qs_rank = EXCLUDED.qs_rank,
      research_output_papers_year = EXCLUDED.research_output_papers_year,
      citations_total = EXCLUDED.citations_total,
      collected_at = NOW();
  `;

  await client.query(insertQuery, [
    uni.name,
    uni.name_local || null,
    uni.country,
    uni.city,
    uni.founded_year,
    uni.type,
    uni.qs_rank || null,
    uni.the_rank || null,
    uni.arwu_rank || null,
    uni.research_output_papers_year,
    uni.citations_total,
    uni.h_index,
    uni.strong_fields,
    uni.notable_alumni || [],
    uni.international_students_pct || null,
    uni.faculty_count || null,
    uni.student_count || null,
  ]);
}

// ============================================================================
// COLLECTORS
// ============================================================================

/**
 * Mock data baseado em rankings reais de 2024
 * Em produção, seria scraping de QS, THE, ARWU websites
 */
async function collectAsianUniversities(): Promise<University[]> {
  console.log('🎓 Collecting Asian universities data...');
  console.log('   (Mock data based on real 2024 rankings)');

  const universities: University[] = [
    // ========== CHINA ==========
    {
      name: 'Tsinghua University',
      name_local: '清华大学',
      country: 'China',
      city: 'Beijing',
      founded_year: 1911,
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
    {
      name: 'Peking University',
      name_local: '北京大学',
      country: 'China',
      city: 'Beijing',
      founded_year: 1898,
      type: 'Public Research',
      qs_rank: 14,
      the_rank: 13,
      arwu_rank: 29,
      research_output_papers_year: 16800,
      citations_total: 2650000,
      h_index: 298,
      strong_fields: ['Mathematics', 'Chemistry', 'Life Sciences', 'Economics'],
      notable_alumni: ['Tu Youyou (Nobel Prize)'],
      international_students_pct: 15.2,
      faculty_count: 3200,
      student_count: 47000,
    },
    {
      name: 'Fudan University',
      name_local: '复旦大学',
      country: 'China',
      city: 'Shanghai',
      founded_year: 1905,
      type: 'Public Research',
      qs_rank: 50,
      the_rank: 51,
      arwu_rank: 67,
      research_output_papers_year: 12500,
      citations_total: 1850000,
      h_index: 245,
      strong_fields: ['Medicine', 'Physics', 'Finance', 'Public Health'],
      international_students_pct: 11.8,
      faculty_count: 2800,
      student_count: 35000,
    },
    {
      name: 'Shanghai Jiao Tong University',
      name_local: '上海交通大学',
      country: 'China',
      city: 'Shanghai',
      founded_year: 1896,
      type: 'Public Research',
      qs_rank: 46,
      the_rank: 43,
      arwu_rank: 54,
      research_output_papers_year: 14200,
      citations_total: 2100000,
      h_index: 268,
      strong_fields: ['Engineering', 'Naval Architecture', 'Robotics', 'Biomedicine'],
      international_students_pct: 10.5,
      faculty_count: 3100,
      student_count: 42000,
    },
    {
      name: 'Zhejiang University',
      name_local: '浙江大学',
      country: 'China',
      city: 'Hangzhou',
      founded_year: 1897,
      type: 'Public Research',
      qs_rank: 42,
      the_rank: 38,
      arwu_rank: 58,
      research_output_papers_year: 15600,
      citations_total: 2250000,
      h_index: 272,
      strong_fields: ['Agriculture', 'Computer Science', 'AI', 'Energy'],
      international_students_pct: 9.8,
      faculty_count: 3400,
      student_count: 62000,
    },

    // ========== JAPÃO ==========
    {
      name: 'University of Tokyo',
      name_local: '東京大学',
      country: 'Japan',
      city: 'Tokyo',
      founded_year: 1877,
      type: 'Public Research',
      qs_rank: 28,
      the_rank: 29,
      arwu_rank: 26,
      research_output_papers_year: 14800,
      citations_total: 3200000,
      h_index: 342,
      strong_fields: ['Physics', 'Materials Science', 'Robotics', 'Earthquake Engineering'],
      notable_alumni: ['16 Nobel Prize winners', '17 Japanese Prime Ministers'],
      international_students_pct: 14.2,
      faculty_count: 4200,
      student_count: 28000,
    },
    {
      name: 'Kyoto University',
      name_local: '京都大学',
      country: 'Japan',
      city: 'Kyoto',
      founded_year: 1897,
      type: 'Public Research',
      qs_rank: 36,
      the_rank: 55,
      arwu_rank: 32,
      research_output_papers_year: 13200,
      citations_total: 2980000,
      h_index: 328,
      strong_fields: ['Chemistry', 'Biology', 'Primatology', 'Philosophy'],
      notable_alumni: ['19 Nobel Prize winners', 'Shinya Yamanaka'],
      international_students_pct: 11.5,
      faculty_count: 3800,
      student_count: 22500,
    },
    {
      name: 'Tokyo Institute of Technology',
      name_local: '東京工業大学',
      country: 'Japan',
      city: 'Tokyo',
      founded_year: 1881,
      type: 'Public Research',
      qs_rank: 91,
      the_rank: 201,
      arwu_rank: 168,
      research_output_papers_year: 8500,
      citations_total: 1650000,
      h_index: 215,
      strong_fields: ['Engineering', 'Materials', 'Nanotechnology', 'Superconductors'],
      international_students_pct: 18.5,
      faculty_count: 1200,
      student_count: 10000,
    },

    // ========== COREIA DO SUL ==========
    {
      name: 'Seoul National University',
      name_local: '서울대학교',
      country: 'South Korea',
      city: 'Seoul',
      founded_year: 1946,
      type: 'Public Research',
      qs_rank: 41,
      the_rank: 56,
      arwu_rank: 101,
      research_output_papers_year: 11200,
      citations_total: 1850000,
      h_index: 256,
      strong_fields: ['Semiconductors', 'Displays', 'Materials', 'Medicine'],
      notable_alumni: ['Ban Ki-moon', 'Multiple Korean Presidents'],
      international_students_pct: 13.8,
      faculty_count: 2500,
      student_count: 28000,
    },
    {
      name: 'KAIST',
      name_local: '한국과학기술원',
      country: 'South Korea',
      city: 'Daejeon',
      founded_year: 1971,
      type: 'Public Research',
      qs_rank: 56,
      the_rank: 83,
      arwu_rank: 201,
      research_output_papers_year: 9800,
      citations_total: 1550000,
      h_index: 238,
      strong_fields: ['Semiconductors', 'Robotics', 'AI', 'Battery Technology'],
      international_students_pct: 16.2,
      faculty_count: 1800,
      student_count: 11000,
    },
    {
      name: 'Yonsei University',
      name_local: '연세대학교',
      country: 'South Korea',
      city: 'Seoul',
      founded_year: 1885,
      type: 'Private',
      qs_rank: 76,
      the_rank: 151,
      arwu_rank: 301,
      research_output_papers_year: 7500,
      citations_total: 1250000,
      h_index: 198,
      strong_fields: ['Medicine', 'Business', 'International Studies'],
      international_students_pct: 19.5,
      faculty_count: 2200,
      student_count: 38000,
    },

    // ========== SINGAPURA ==========
    {
      name: 'National University of Singapore',
      name_local: 'NUS',
      country: 'Singapore',
      city: 'Singapore',
      founded_year: 1905,
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
    {
      name: 'Nanyang Technological University',
      name_local: 'NTU',
      country: 'Singapore',
      city: 'Singapore',
      founded_year: 1991,
      type: 'Public Research',
      qs_rank: 26,
      the_rank: 32,
      arwu_rank: 92,
      research_output_papers_year: 11800,
      citations_total: 2150000,
      h_index: 268,
      strong_fields: ['Materials Science', 'AI', 'Renewable Energy', 'Communications'],
      international_students_pct: 28.5,
      faculty_count: 2400,
      student_count: 33000,
    },

    // ========== AUSTRÁLIA ==========
    {
      name: 'University of Melbourne',
      country: 'Australia',
      city: 'Melbourne',
      founded_year: 1853,
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
    {
      name: 'Australian National University',
      country: 'Australia',
      city: 'Canberra',
      founded_year: 1946,
      type: 'Public Research',
      qs_rank: 34,
      the_rank: 62,
      arwu_rank: 67,
      research_output_papers_year: 9800,
      citations_total: 2150000,
      h_index: 268,
      strong_fields: ['Astronomy', 'Physics', 'Political Science', 'Economics'],
      notable_alumni: ['6 Nobel Prize winners', 'Brian Schmidt'],
      international_students_pct: 38.5,
      faculty_count: 1800,
      student_count: 25000,
    },
    {
      name: 'University of Sydney',
      country: 'Australia',
      city: 'Sydney',
      founded_year: 1850,
      type: 'Public Research',
      qs_rank: 19,
      the_rank: 60,
      arwu_rank: 71,
      research_output_papers_year: 12200,
      citations_total: 2550000,
      h_index: 282,
      strong_fields: ['Medicine', 'Engineering', 'Veterinary Science', 'Architecture'],
      international_students_pct: 44.2,
      faculty_count: 3000,
      student_count: 73000,
    },
    {
      name: 'University of Queensland',
      country: 'Australia',
      city: 'Brisbane',
      founded_year: 1909,
      type: 'Public Research',
      qs_rank: 43,
      the_rank: 70,
      arwu_rank: 54,
      research_output_papers_year: 11500,
      citations_total: 2350000,
      h_index: 275,
      strong_fields: ['Mining Engineering', 'Biotechnology', 'Marine Biology', 'Agriculture'],
      international_students_pct: 39.8,
      faculty_count: 2700,
      student_count: 54000,
    },

    // ========== TAIWAN ==========
    {
      name: 'National Taiwan University',
      name_local: '國立臺灣大學',
      country: 'Taiwan',
      city: 'Taipei',
      founded_year: 1928,
      type: 'Public Research',
      qs_rank: 69,
      the_rank: 187,
      arwu_rank: 201,
      research_output_papers_year: 8500,
      citations_total: 1450000,
      h_index: 218,
      strong_fields: ['Semiconductors', 'Medicine', 'Agriculture', 'Engineering'],
      international_students_pct: 10.5,
      faculty_count: 2100,
      student_count: 32000,
    },
    {
      name: 'National Tsing Hua University',
      name_local: '國立清華大學',
      country: 'Taiwan',
      city: 'Hsinchu',
      founded_year: 1911,
      type: 'Public Research',
      qs_rank: 180,
      arwu_rank: 401,
      research_output_papers_year: 6200,
      citations_total: 985000,
      h_index: 185,
      strong_fields: ['Semiconductors', 'Materials Science', 'Engineering', 'Nanotechnology'],
      international_students_pct: 12.8,
      faculty_count: 1400,
      student_count: 16000,
    },

    // ========== ÍNDIA (expandida) ==========
    {
      name: 'Indian Institute of Science',
      name_local: 'IISc',
      country: 'India',
      city: 'Bangalore',
      founded_year: 1909,
      type: 'Public Research',
      qs_rank: 225,
      the_rank: 251,
      arwu_rank: 501,
      research_output_papers_year: 7800,
      citations_total: 1250000,
      h_index: 195,
      strong_fields: ['Materials Science', 'AI', 'Aerospace', 'Biotechnology'],
      international_students_pct: 8.5,
      faculty_count: 550,
      student_count: 4500,
    },
    {
      name: 'Indian Institute of Technology Bombay',
      name_local: 'IIT Bombay',
      country: 'India',
      city: 'Mumbai',
      founded_year: 1958,
      type: 'Public',
      qs_rank: 149,
      the_rank: 401,
      arwu_rank: 601,
      research_output_papers_year: 5800,
      citations_total: 850000,
      h_index: 168,
      strong_fields: ['Software Engineering', 'Civil Engineering', 'Management', 'Energy'],
      international_students_pct: 6.2,
      faculty_count: 650,
      student_count: 11000,
    },
    {
      name: 'Indian Institute of Technology Delhi',
      name_local: 'IIT Delhi',
      country: 'India',
      city: 'New Delhi',
      founded_year: 1961,
      type: 'Public',
      qs_rank: 197,
      the_rank: 401,
      research_output_papers_year: 5200,
      citations_total: 780000,
      h_index: 158,
      strong_fields: ['Mechanical Engineering', 'Computer Science', 'Electrical Engineering'],
      international_students_pct: 5.8,
      faculty_count: 580,
      student_count: 9500,
    },

    // ========== VIETNÃ ==========
    {
      name: 'Vietnam National University, Hanoi',
      name_local: 'Đại học Quốc gia Hà Nội',
      country: 'Vietnam',
      city: 'Hanoi',
      founded_year: 1906,
      type: 'Public',
      qs_rank: 801,
      research_output_papers_year: 3200,
      citations_total: 285000,
      h_index: 98,
      strong_fields: ['Computer Science', 'Materials', 'Environmental Science', 'Economics'],
      international_students_pct: 4.5,
      faculty_count: 1800,
      student_count: 45000,
    },
    {
      name: 'Vietnam National University, Ho Chi Minh City',
      name_local: 'Đại học Quốc gia TP. Hồ Chí Minh',
      country: 'Vietnam',
      city: 'Ho Chi Minh City',
      founded_year: 1995,
      type: 'Public',
      qs_rank: 901,
      research_output_papers_year: 2800,
      citations_total: 245000,
      h_index: 88,
      strong_fields: ['Social Sciences', 'Engineering', 'Medicine', 'IT'],
      international_students_pct: 5.2,
      faculty_count: 1500,
      student_count: 42000,
    },

    // ========== INDONÉSIA ==========
    {
      name: 'Universitas Indonesia',
      name_local: 'UI',
      country: 'Indonesia',
      city: 'Jakarta',
      founded_year: 1849,
      type: 'Public',
      qs_rank: 237,
      the_rank: 601,
      research_output_papers_year: 4500,
      citations_total: 485000,
      h_index: 128,
      strong_fields: ['Medicine', 'Engineering', 'Social Sciences', 'Public Health'],
      international_students_pct: 7.8,
      faculty_count: 2200,
      student_count: 52000,
    },
    {
      name: 'Gadjah Mada University',
      name_local: 'Universitas Gadjah Mada',
      country: 'Indonesia',
      city: 'Yogyakarta',
      founded_year: 1949,
      type: 'Public',
      qs_rank: 263,
      research_output_papers_year: 3800,
      citations_total: 420000,
      h_index: 115,
      strong_fields: ['Agriculture', 'Forestry', 'Engineering', 'Medicine'],
      international_students_pct: 6.5,
      faculty_count: 1900,
      student_count: 48000,
    },
    {
      name: 'Institut Teknologi Bandung',
      name_local: 'ITB',
      country: 'Indonesia',
      city: 'Bandung',
      founded_year: 1920,
      type: 'Public',
      qs_rank: 280,
      research_output_papers_year: 3500,
      citations_total: 395000,
      h_index: 108,
      strong_fields: ['Engineering', 'Architecture', 'Earth Sciences', 'Energy'],
      international_students_pct: 5.5,
      faculty_count: 1600,
      student_count: 24000,
    },

    // ========== TAILÂNDIA ==========
    {
      name: 'Chulalongkorn University',
      name_local: 'จุฬาลงกรณ์มหาวิทยาลัย',
      country: 'Thailand',
      city: 'Bangkok',
      founded_year: 1917,
      type: 'Public',
      qs_rank: 211,
      the_rank: 601,
      research_output_papers_year: 5200,
      citations_total: 625000,
      h_index: 145,
      strong_fields: ['Medicine', 'Engineering', 'Political Science', 'Chemistry'],
      international_students_pct: 8.5,
      faculty_count: 2100,
      student_count: 37000,
    },
    {
      name: 'Mahidol University',
      name_local: 'มหาวิทยาลัยมหิดล',
      country: 'Thailand',
      city: 'Bangkok',
      founded_year: 1888,
      type: 'Public',
      qs_rank: 382,
      research_output_papers_year: 4800,
      citations_total: 580000,
      h_index: 138,
      strong_fields: ['Medicine', 'Public Health', 'Tropical Medicine', 'Pharmacy'],
      international_students_pct: 12.2,
      faculty_count: 1800,
      student_count: 30000,
    },

    // ========== MALÁSIA ==========
    {
      name: 'Universiti Malaya',
      name_local: 'UM',
      country: 'Malaysia',
      city: 'Kuala Lumpur',
      founded_year: 1905,
      type: 'Public Research',
      qs_rank: 65,
      the_rank: 301,
      research_output_papers_year: 7200,
      citations_total: 895000,
      h_index: 172,
      strong_fields: ['Engineering', 'Computer Science', 'Medicine', 'Social Sciences'],
      international_students_pct: 18.5,
      faculty_count: 2000,
      student_count: 27000,
    },
    {
      name: 'Universiti Teknologi Malaysia',
      name_local: 'UTM',
      country: 'Malaysia',
      city: 'Johor Bahru',
      founded_year: 1904,
      type: 'Public',
      qs_rank: 188,
      research_output_papers_year: 5500,
      citations_total: 685000,
      h_index: 152,
      strong_fields: ['Engineering', 'Architecture', 'IT', 'Management'],
      international_students_pct: 15.8,
      faculty_count: 1700,
      student_count: 32000,
    },
    {
      name: 'Universiti Kebangsaan Malaysia',
      name_local: 'UKM',
      country: 'Malaysia',
      city: 'Bangi',
      founded_year: 1970,
      type: 'Public Research',
      qs_rank: 159,
      research_output_papers_year: 6200,
      citations_total: 755000,
      h_index: 162,
      strong_fields: ['Medicine', 'Islamic Studies', 'Engineering', 'Environmental Science'],
      international_students_pct: 11.5,
      faculty_count: 1850,
      student_count: 26000,
    },

    // ========== COREIA (expandida) ==========
    {
      name: 'Sungkyunkwan University',
      name_local: '성균관대학교',
      country: 'South Korea',
      city: 'Seoul',
      founded_year: 1398,
      type: 'Private',
      qs_rank: 145,
      the_rank: 201,
      research_output_papers_year: 8800,
      citations_total: 1350000,
      h_index: 208,
      strong_fields: ['Semiconductors', 'Materials', 'Business', 'Medicine'],
      notable_alumni: ['Samsung partnership'],
      international_students_pct: 14.5,
      faculty_count: 2100,
      student_count: 32000,
    },
    {
      name: 'Pohang University of Science and Technology',
      name_local: '포항공과대학교 (POSTECH)',
      country: 'South Korea',
      city: 'Pohang',
      founded_year: 1986,
      type: 'Private Research',
      qs_rank: 100,
      the_rank: 201,
      research_output_papers_year: 6500,
      citations_total: 1150000,
      h_index: 192,
      strong_fields: ['Materials Science', 'Chemistry', 'Physics', 'Nanotechnology'],
      international_students_pct: 11.2,
      faculty_count: 450,
      student_count: 4500,
    },

    // ========== HONG KONG ==========
    {
      name: 'University of Hong Kong',
      name_local: '香港大學',
      country: 'Hong Kong',
      city: 'Hong Kong',
      founded_year: 1911,
      type: 'Public Research',
      qs_rank: 26,
      the_rank: 35,
      arwu_rank: 88,
      research_output_papers_year: 9500,
      citations_total: 1950000,
      h_index: 252,
      strong_fields: ['Medicine', 'Law', 'Architecture', 'Public Health'],
      international_students_pct: 43.5,
      faculty_count: 2200,
      student_count: 30000,
    },
    {
      name: 'Hong Kong University of Science and Technology',
      name_local: '香港科技大學',
      country: 'Hong Kong',
      city: 'Hong Kong',
      founded_year: 1991,
      type: 'Public Research',
      qs_rank: 60,
      the_rank: 58,
      arwu_rank: 201,
      research_output_papers_year: 7800,
      citations_total: 1550000,
      h_index: 228,
      strong_fields: ['Engineering', 'Business', 'Computer Science', 'Fintech'],
      international_students_pct: 35.8,
      faculty_count: 1500,
      student_count: 16000,
    },
  ];

  return universities;
}

// ============================================================================
// MAIN FUNCTION
// ============================================================================

async function main() {
  console.log('🚀 Sofia Pulse - Asian Universities Collector');
  console.log('='.repeat(60));
  console.log('');
  console.log('🎓 WHY ASIAN UNIVERSITIES MATTER:');
  console.log('   - China: Largest producer of STEM PhDs globally');
  console.log('   - Japan: Nobel Prize leaders in Asia');
  console.log('   - Singapore: Biotech and AI hub');
  console.log('   - Australia: Top research institutions');
  console.log('   - Research output indicator of future innovation');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    await createTableIfNotExists(client);

    console.log('');
    console.log('📊 Collecting universities...');
    console.log('');

    const universities = await collectAsianUniversities();
    console.log(`   ✅ Collected ${universities.length} universities`);
    console.log('');

    console.log('💾 Inserting into database...');
    for (const uni of universities) {
      await insertUniversity(client, uni);
    }
    console.log(`✅ ${universities.length} universities inserted/updated`);
    console.log('');

    // Summary
    console.log('📊 Summary by country:');
    console.log('');

    const summaryQuery = `
      SELECT
        country,
        COUNT(*) as university_count,
        AVG(qs_rank)::INT as avg_qs_rank,
        SUM(research_output_papers_year) as total_papers_year
      FROM asia_universities
      WHERE qs_rank IS NOT NULL
      GROUP BY country
      ORDER BY avg_qs_rank;
    `;

    const summary = await client.query(summaryQuery);

    summary.rows.forEach((row) => {
      console.log(`   ${row.country}:`);
      console.log(`      Universities: ${row.university_count}`);
      console.log(`      Avg QS Rank: ${row.avg_qs_rank}`);
      console.log(`      Total Papers/Year: ${row.total_papers_year.toLocaleString()}`);
      console.log('');
    });

    console.log('✅ Collection complete!');
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

// ============================================================================
// DRY RUN MODE
// ============================================================================

async function dryRun() {
  console.log('🚀 Sofia Pulse - Asian Universities Collector (DRY RUN)');
  console.log('='.repeat(60));
  console.log('');
  console.log('🎓 WHY ASIAN UNIVERSITIES MATTER:');
  console.log('   - China: Largest producer of STEM PhDs globally');
  console.log('   - Japan: Nobel Prize leaders in Asia (41 winners)');
  console.log('   - Singapore: Biotech and AI innovation hub');
  console.log('   - Australia: Top research in mining, agriculture');
  console.log('   - Research output = Future innovation pipeline');
  console.log('');
  console.log('='.repeat(60));
  console.log('');

  const universities = await collectAsianUniversities();
  console.log(`✅ Collected ${universities.length} universities`);
  console.log('');

  // Group by country
  const byCountry = universities.reduce((acc, uni) => {
    if (!acc[uni.country]) acc[uni.country] = [];
    acc[uni.country].push(uni);
    return acc;
  }, {} as Record<string, University[]>);

  console.log('📊 Universities by Country:');
  console.log('');

  Object.entries(byCountry)
    .sort(([, a], [, b]) => {
      const aRank = Math.min(...a.map((u) => u.qs_rank || 999));
      const bRank = Math.min(...b.map((u) => u.qs_rank || 999));
      return aRank - bRank;
    })
    .forEach(([country, unis]) => {
      const totalPapers = unis.reduce((sum, u) => sum + u.research_output_papers_year, 0);
      const avgRank = unis.reduce((sum, u) => sum + (u.qs_rank || 0), 0) / unis.length;

      console.log(`   ${country}: ${unis.length} universities`);
      console.log(`      Avg QS Rank: ${avgRank.toFixed(0)}`);
      console.log(`      Total Papers/Year: ${totalPapers.toLocaleString()}`);
      console.log(`      Top Unis: ${unis.slice(0, 2).map((u) => u.name).join(', ')}`);
      console.log('');
    });

  // Top universities overall
  console.log('🏆 Top 10 Asian Universities (QS Rank):');
  console.log('');

  const sorted = [...universities].sort((a, b) => (a.qs_rank || 999) - (b.qs_rank || 999));
  sorted.slice(0, 10).forEach((uni, idx) => {
    console.log(`   ${idx + 1}. ${uni.name} (${uni.country})`);
    console.log(`      QS Rank: #${uni.qs_rank}`);
    console.log(`      Papers/Year: ${uni.research_output_papers_year.toLocaleString()}`);
    console.log(`      Strong Fields: ${uni.strong_fields.slice(0, 3).join(', ')}`);
    console.log('');
  });

  // Research output by field
  console.log('🔬 Research Output by Field:');
  console.log('');

  const fieldMap = universities.reduce((acc, uni) => {
    uni.strong_fields.forEach((field) => {
      if (!acc[field]) acc[field] = { count: 0, papers: 0, unis: [] };
      acc[field].count++;
      acc[field].papers += uni.research_output_papers_year / uni.strong_fields.length;
      acc[field].unis.push(uni.name);
    });
    return acc;
  }, {} as Record<string, { count: number; papers: number; unis: string[] }>);

  Object.entries(fieldMap)
    .sort(([, a], [, b]) => b.count - a.count)
    .slice(0, 10)
    .forEach(([field, data]) => {
      console.log(`   ${field}:`);
      console.log(`      Universities: ${data.count}`);
      console.log(`      Est. Papers/Year: ${Math.round(data.papers).toLocaleString()}`);
      console.log('');
    });

  console.log('='.repeat(60));
  console.log('');
  console.log('💡 KEY INSIGHTS:');
  console.log('');

  const totalPapers = universities.reduce((sum, u) => sum + u.research_output_papers_year, 0);
  const avgIntl = universities.reduce((sum, u) => sum + (u.international_students_pct || 0), 0) / universities.length;

  console.log(`   Total Research Output: ${totalPapers.toLocaleString()} papers/year`);
  console.log(`   Average International Students: ${avgIntl.toFixed(1)}%`);
  console.log('');
  console.log('   China: Massive research output, rapid growth');
  console.log('   Japan: Nobel Prize history, quality over quantity');
  console.log('   Singapore: Small but highly international');
  console.log('   Australia: Strong international collaboration');
  console.log('');

  console.log('🎯 CORRELATIONS:');
  console.log('');
  console.log('   - University papers → Patents filed');
  console.log('   - Research fields → Startup sectors');
  console.log('   - International % → Knowledge transfer');
  console.log('   - Rankings → Government R&D funding');
  console.log('');
  console.log('✅ Dry run complete!');
}

// ============================================================================
// RUN
// ============================================================================

if (require.main === module) {
  const args = process.argv.slice(2);
  const isDryRun = args.includes('--dry-run') || args.includes('-d');

  if (isDryRun) {
    dryRun().catch(console.error);
  } else {
    main().catch((error) => {
      if (error.code === 'ECONNREFUSED') {
        console.log('');
        console.log('⚠️  Database connection failed!');
        console.log('');
        console.log('💡 TIP: Run with --dry-run to see sample data:');
        console.log('   npm run collect:asia-universities -- --dry-run');
        console.log('');
        process.exit(1);
      }
      throw error;
    });
  }
}

export { collectAsianUniversities, dryRun };
