#!/usr/bin/env python3
"""
Cria tabelas manualmente usando Python (sem precisar de psql)
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or 'localhost',
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5432'),
    'user': os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME') or 'sofia_db',
}

print("=" * 80)
print("🔧 CRIANDO TABELAS - Sofia Pulse")
print("=" * 80)
print()
print(f"📊 Database: {DB_CONFIG['user']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
print()

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Create space_industry table
    print("🚀 Creating space_industry table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.space_industry (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(50) NOT NULL,
            mission_name VARCHAR(200),
            company VARCHAR(100),
            launch_date TIMESTAMP,
            launch_site VARCHAR(200),
            rocket_type VARCHAR(100),
            payload_type VARCHAR(100),
            payload_count INTEGER,
            orbit_type VARCHAR(50),
            status VARCHAR(50),
            customers TEXT[],
            contract_value_usd BIGINT,
            country VARCHAR(100),
            description TEXT,
            source VARCHAR(100),
            source_url TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_space_type ON sofia.space_industry(event_type);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_space_company ON sofia.space_industry(company);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_space_date ON sofia.space_industry(launch_date);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_space_status ON sofia.space_industry(status);
    """)

    conn.commit()
    print("   ✅ space_industry criada")
    print()

    # Create ai_regulation table
    print("⚖️  Creating ai_regulation table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.ai_regulation (
            id SERIAL PRIMARY KEY,
            regulation_type VARCHAR(50) NOT NULL,
            title TEXT NOT NULL,
            jurisdiction VARCHAR(100),
            regulatory_body VARCHAR(200),
            status VARCHAR(50),
            effective_date DATE,
            announced_date DATE,
            scope TEXT[],
            impact_level VARCHAR(20),
            penalties_max BIGINT,
            description TEXT,
            key_requirements TEXT[],
            affected_sectors TEXT[],
            source VARCHAR(100),
            source_url TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(title, jurisdiction)
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reg_type ON sofia.ai_regulation(regulation_type);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reg_jurisdiction ON sofia.ai_regulation(jurisdiction);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reg_status ON sofia.ai_regulation(status);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reg_date ON sofia.ai_regulation(announced_date);
    """)

    conn.commit()
    print("   ✅ ai_regulation criada")
    print()

    # Create gdelt_events table
    print("🌍 Creating gdelt_events table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.gdelt_events (
            id SERIAL PRIMARY KEY,
            event_id VARCHAR(100) UNIQUE NOT NULL,
            event_date DATE NOT NULL,
            event_time TIMESTAMP,

            actor1_name VARCHAR(500),
            actor1_country VARCHAR(10),
            actor2_name VARCHAR(500),
            actor2_country VARCHAR(10),

            event_code VARCHAR(10),
            event_base_code VARCHAR(10),
            event_root_code VARCHAR(10),
            quad_class INT,
            goldstein_scale DECIMAL(5,2),
            num_mentions INT DEFAULT 0,
            num_sources INT DEFAULT 0,
            num_articles INT DEFAULT 0,
            avg_tone DECIMAL(6,3),

            action_geo_country VARCHAR(10),
            action_geo_lat DECIMAL(10,6),
            action_geo_lon DECIMAL(10,6),
            action_geo_fullname TEXT,

            categories TEXT[],
            is_tech_related BOOLEAN DEFAULT FALSE,
            is_market_relevant BOOLEAN DEFAULT FALSE,

            source_url TEXT,
            collected_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_gdelt_date ON sofia.gdelt_events(event_date DESC);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_gdelt_countries ON sofia.gdelt_events(actor1_country, actor2_country);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_gdelt_goldstein ON sofia.gdelt_events(goldstein_scale);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_gdelt_tone ON sofia.gdelt_events(avg_tone);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_gdelt_categories ON sofia.gdelt_events USING GIN(categories);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_gdelt_tech ON sofia.gdelt_events(is_tech_related) WHERE is_tech_related = TRUE;
    """)

    conn.commit()
    print("   ✅ gdelt_events criada")
    print()

    # Create energy_global table
    print("🌍 Creating energy_global table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.energy_global (
            id SERIAL PRIMARY KEY,
            country VARCHAR(100) NOT NULL,
            year INTEGER NOT NULL,
            iso_code VARCHAR(10),
            population BIGINT,
            gdp BIGINT,

            electricity_generation_twh DECIMAL(10,2),
            solar_generation_twh DECIMAL(10,2),
            wind_generation_twh DECIMAL(10,2),
            hydro_generation_twh DECIMAL(10,2),
            nuclear_generation_twh DECIMAL(10,2),
            coal_generation_twh DECIMAL(10,2),
            gas_generation_twh DECIMAL(10,2),
            oil_generation_twh DECIMAL(10,2),

            renewables_share_pct DECIMAL(5,2),
            low_carbon_share_pct DECIMAL(5,2),

            energy_per_capita DECIMAL(10,2),
            energy_per_gdp DECIMAL(10,4),

            co2_mt DECIMAL(12,2),
            co2_per_capita DECIMAL(10,2),

            solar_capacity_gw DECIMAL(10,2),
            wind_capacity_gw DECIMAL(10,2),

            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(country, year)
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_energy_country ON sofia.energy_global(country);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_energy_year ON sofia.energy_global(year DESC);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_energy_renewables ON sofia.energy_global(renewables_share_pct DESC);
    """)

    conn.commit()
    print("   ✅ energy_global criada")
    print()

    # Create electricity_consumption table
    print("⚡ Creating electricity_consumption table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.electricity_consumption (
            id SERIAL PRIMARY KEY,
            country VARCHAR(100) NOT NULL,
            year INTEGER NOT NULL,
            iso_code VARCHAR(10),
            consumption_twh DECIMAL(10,2),
            generation_twh DECIMAL(10,2),
            per_capita_kwh DECIMAL(8,2),
            population BIGINT,
            data_source VARCHAR(100),
            collected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country, year)
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_elec_country ON sofia.electricity_consumption(country);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_elec_year ON sofia.electricity_consumption(year DESC);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_elec_consumption ON sofia.electricity_consumption(consumption_twh DESC);
    """)

    conn.commit()
    print("   ✅ electricity_consumption criada")
    print()

    # Create port_traffic table
    print("🚢 Creating port_traffic table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.port_traffic (
            id SERIAL PRIMARY KEY,
            country VARCHAR(100) NOT NULL,
            country_code VARCHAR(10),
            year INTEGER NOT NULL,
            teu BIGINT,
            collected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country, year)
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_port_country ON sofia.port_traffic(country);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_port_year ON sofia.port_traffic(year DESC);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_port_teu ON sofia.port_traffic(teu DESC);
    """)

    conn.commit()
    print("   ✅ port_traffic criada")
    print()

    # Create commodity_prices table
    print("📈 Creating commodity_prices table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.commodity_prices (
            id SERIAL PRIMARY KEY,
            commodity VARCHAR(100) NOT NULL,
            price DECIMAL(12,4),
            unit VARCHAR(50),
            data_source VARCHAR(100),
            price_date DATE NOT NULL,
            collected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(commodity, price_date)
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_commodity_name ON sofia.commodity_prices(commodity);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_commodity_date ON sofia.commodity_prices(price_date DESC);
    """)

    conn.commit()
    print("   ✅ commodity_prices criada")
    print()

    # Create semiconductor_sales table
    print("💾 Creating semiconductor_sales table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.semiconductor_sales (
            id SERIAL PRIMARY KEY,
            region VARCHAR(100) NOT NULL,
            year INTEGER NOT NULL,
            quarter VARCHAR(10) DEFAULT '',
            month VARCHAR(20) DEFAULT '',
            sales_usd_billions DECIMAL(10,2),
            yoy_growth_pct DECIMAL(6,2),
            qoq_growth_pct DECIMAL(6,2),
            data_source VARCHAR(100),
            notes TEXT,
            collected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(region, year, quarter, month)
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_semi_region ON sofia.semiconductor_sales(region);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_semi_year ON sofia.semiconductor_sales(year DESC);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_semi_sales ON sofia.semiconductor_sales(sales_usd_billions DESC);
    """)

    conn.commit()
    print("   ✅ semiconductor_sales criada")
    print()

    # Verify tables exist
    print("🔍 Verificando tabelas...")
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'sofia'
          AND table_name IN (
              'space_industry', 'ai_regulation', 'cybersecurity_events', 'gdelt_events',
              'energy_global', 'electricity_consumption', 'port_traffic',
              'commodity_prices', 'semiconductor_sales'
          )
        ORDER BY table_name;
    """)

    tables = cursor.fetchall()
    for table in tables:
        print(f"   ✅ {table[0]}")

    cursor.close()
    conn.close()

    print()
    print("=" * 80)
    print("✅ TABELAS CRIADAS COM SUCESSO!")
    print("=" * 80)
    print()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
