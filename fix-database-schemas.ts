#!/usr/bin/env tsx

import { Client } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

const dbConfig = {
  host: process.env.DB_HOST || process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || process.env.POSTGRES_PORT || '5432'),
  user: process.env.DB_USER || process.env.POSTGRES_USER || 'sofia',
  password: process.env.DB_PASSWORD || process.env.POSTGRES_PASSWORD || 'sofia123strong',
  database: process.env.DB_NAME || process.env.POSTGRES_DB || 'sofia_db',
};

async function fixDatabaseSchemas() {
  console.log('🔧 Fixing database schemas...\n');

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL\n');

    // 1. Fix OpenAlex (VARCHAR(10) -> TEXT)
    console.log('1️⃣  Fixing OpenAlex table...');
    await client.query(`DROP TABLE IF EXISTS openalex_papers CASCADE;`);

    await client.query(`
      CREATE TABLE openalex_papers (
        id SERIAL PRIMARY KEY,
        openalex_id VARCHAR(50) UNIQUE,
        doi VARCHAR(100),
        title TEXT NOT NULL,
        publication_date DATE,
        publication_year INT,
        authors TEXT[],
        author_institutions TEXT[],
        author_countries TEXT[],
        concepts TEXT[],
        primary_concept VARCHAR(255),
        cited_by_count INT DEFAULT 0,
        referenced_works_count INT DEFAULT 0,
        is_open_access BOOLEAN,
        journal VARCHAR(500),
        publisher VARCHAR(255),
        abstract TEXT,
        collected_at TIMESTAMP DEFAULT NOW()
      );
    `);

    await client.query(`CREATE INDEX IF NOT EXISTS idx_openalex_pub_year ON openalex_papers(publication_year DESC);`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_openalex_cited_by ON openalex_papers(cited_by_count DESC);`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_openalex_concepts ON openalex_papers USING GIN(concepts);`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_openalex_countries ON openalex_papers USING GIN(author_countries);`);

    console.log('   ✅ OpenAlex fixed\n');

    // 2. Fix PyPI Stats
    console.log('2️⃣  Fixing PyPI Stats table...');
    await client.query(`DROP TABLE IF EXISTS sofia.pypi_stats CASCADE;`);

    await client.query(`
      CREATE TABLE sofia.pypi_stats (
        id SERIAL PRIMARY KEY,
        package_name VARCHAR(200) NOT NULL,
        downloads_month INT DEFAULT 0,
        version VARCHAR(50),
        description TEXT,
        keywords TEXT[],
        collected_at TIMESTAMP DEFAULT NOW()
      );
    `);

    await client.query(`CREATE UNIQUE INDEX IF NOT EXISTS idx_pypi_package_date ON sofia.pypi_stats(package_name, DATE(collected_at));`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_pypi_package ON sofia.pypi_stats(package_name);`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_pypi_downloads ON sofia.pypi_stats(downloads_month DESC);`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_pypi_date ON sofia.pypi_stats(collected_at DESC);`);

    console.log('   ✅ PyPI Stats fixed\n');

    // 3. Fix NPM Stats
    console.log('3️⃣  Fixing NPM Stats table...');
    await client.query(`DROP TABLE IF EXISTS sofia.npm_stats CASCADE;`);

    await client.query(`
      CREATE TABLE sofia.npm_stats (
        id SERIAL PRIMARY KEY,
        package_name VARCHAR(200) NOT NULL,
        downloads_day INT DEFAULT 0,
        downloads_week INT DEFAULT 0,
        downloads_month INT DEFAULT 0,
        version VARCHAR(50),
        description TEXT,
        keywords TEXT[],
        collected_at TIMESTAMP DEFAULT NOW()
      );
    `);

    await client.query(`CREATE UNIQUE INDEX IF NOT EXISTS idx_npm_package_date ON sofia.npm_stats(package_name, DATE(collected_at));`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_npm_package ON sofia.npm_stats(package_name);`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_npm_downloads ON sofia.npm_stats(downloads_month DESC);`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_npm_date ON sofia.npm_stats(collected_at DESC);`);

    console.log('   ✅ NPM Stats fixed\n');

    // 4. Create cybersecurity_events table if not exists
    console.log('4️⃣  Creating cybersecurity_events table...');
    await client.query(`
      CREATE TABLE IF NOT EXISTS sofia.cybersecurity_events (
        id SERIAL PRIMARY KEY,
        event_type VARCHAR(50) NOT NULL,
        event_id VARCHAR(100) UNIQUE,
        title TEXT NOT NULL,
        description TEXT,
        severity VARCHAR(20),
        cvss_score DECIMAL(3,1),
        affected_products TEXT[],
        vendors TEXT[],
        published_date DATE NOT NULL,
        source VARCHAR(100),
        source_url TEXT,
        affected_count INTEGER,
        tags TEXT[],
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
      );
    `);

    await client.query(`CREATE INDEX IF NOT EXISTS idx_cyber_type ON sofia.cybersecurity_events(event_type);`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_cyber_severity ON sofia.cybersecurity_events(severity);`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_cyber_date ON sofia.cybersecurity_events(published_date);`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_cyber_cvss ON sofia.cybersecurity_events(cvss_score);`);

    console.log('   ✅ Cybersecurity Events table created\n');

    console.log('✅ Database schemas fixed successfully!\n');

  } catch (error) {
    console.error('❌ Error fixing schemas:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

fixDatabaseSchemas();
