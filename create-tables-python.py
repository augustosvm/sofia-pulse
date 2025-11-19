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

    # Verify tables exist
    print("🔍 Verificando tabelas...")
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'sofia'
          AND table_name IN ('space_industry', 'ai_regulation', 'cybersecurity_events')
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
