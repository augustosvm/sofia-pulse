#!/usr/bin/env python3
"""Recreate country_aliases table with alias_norm column."""
import psycopg2
import os
import re
from pathlib import Path

def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v

def normalize_text(text):
    """Normalize text: lowercase + alphanumeric only."""
    if not text:
        return ""
    return re.sub(r'[^a-z0-9]+', '', text.lower())

load_env()
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    database=os.getenv("POSTGRES_DB", "sofia_db")
)
cur = conn.cursor()

print("Dropping old tables...")
cur.execute("DROP TABLE IF EXISTS sofia.signal_country_map CASCADE")
cur.execute("DROP TABLE IF EXISTS sofia.cyber_event_country_map CASCADE")
cur.execute("DROP TABLE IF EXISTS sofia.trial_country_map CASCADE")
cur.execute("DROP TABLE IF EXISTS sofia.country_aliases CASCADE")
conn.commit()

print("Creating country_aliases with alias_norm...")
cur.execute("""
    CREATE TABLE sofia.country_aliases (
        id BIGSERIAL PRIMARY KEY,
        country_code CHAR(2) NOT NULL,
        alias TEXT NOT NULL,
        alias_norm TEXT NOT NULL,
        alias_type TEXT NOT NULL DEFAULT 'common',
        UNIQUE(country_code, alias_norm)
    )
""")

# Seed from countries table
print("Seeding from countries table...")
cur.execute("SELECT iso_alpha2, common_name FROM sofia.countries WHERE iso_alpha2 IS NOT NULL AND common_name IS NOT NULL")
for row in cur.fetchall():
    code, name = row
    norm = normalize_text(name)
    cur.execute("""
        INSERT INTO sofia.country_aliases (country_code, alias, alias_norm, alias_type)
        VALUES (%s, %s, %s, 'common')
        ON CONFLICT DO NOTHING
    """, (code, name, norm))

# Add manual variants
print("Adding manual variants...")
variants = [
    ('US','USA','usa','variant'),
    ('US','United States of America','unitedstatesofamerica','variant'),
    ('GB','UK','uk','variant'),
    ('GB','Britain','britain','variant'),
    ('GB','United Kingdom','unitedkingdom','variant'),
    ('GB','England','england','variant'),
    ('BR','Brasil','brasil','variant'),
    ('RU','Russia','russia','common'),
    ('RU','Russian Federation','russianfederation','official'),
    ('CN','China','china','common'),
    ('CN','PRC','prc','variant'),
    ('DE','Germany','germany','common'),
    ('DE','Deutschland','deutschland','variant'),
    ('FR','France','france','common'),
    ('JP','Japan','japan','common'),
    ('IN','India','india','common'),
    ('KR','South Korea','southkorea','common'),
    ('KR','Korea','korea','variant'),
    ('AU','Australia','australia','common'),
    ('CA','Canada','canada','common'),
    ('IL','Israel','israel','common'),
    ('SG','Singapore','singapore','common'),
    ('NL','Netherlands','netherlands','common'),
    ('NL','Holland','holland','variant'),
    ('CH','Switzerland','switzerland','common'),
    ('SE','Sweden','sweden','common'),
    ('ES','Spain','spain','common'),
    ('IT','Italy','italy','common'),
    ('MX','Mexico','mexico','common'),
    ('AR','Argentina','argentina','common'),
    ('ZA','South Africa','southafrica','common'),
    ('AE','UAE','uae','variant'),
    ('AE','United Arab Emirates','unitedarabemirates','official'),
    ('SA','Saudi Arabia','saudiarabia','common'),
    ('TW','Taiwan','taiwan','common'),
    ('HK','Hong Kong','hongkong','common'),
    ('PL','Poland','poland','common'),
    ('ID','Indonesia','indonesia','common'),
    ('TH','Thailand','thailand','common'),
    ('VN','Vietnam','vietnam','common'),
    ('PH','Philippines','philippines','common'),
    ('MY','Malaysia','malaysia','common'),
    ('NZ','New Zealand','newzealand','common'),
    ('IE','Ireland','ireland','common'),
    ('AT','Austria','austria','common'),
    ('BE','Belgium','belgium','common'),
    ('DK','Denmark','denmark','common'),
    ('FI','Finland','finland','common'),
    ('NO','Norway','norway','common'),
    ('PT','Portugal','portugal','common'),
    ('CZ','Czechia','czechia','variant'),
    ('CZ','Czech Republic','czechrepublic','common'),
    ('GR','Greece','greece','common'),
    ('HU','Hungary','hungary','common'),
    ('RO','Romania','romania','common'),
    ('UA','Ukraine','ukraine','common'),
    ('EG','Egypt','egypt','common'),
    ('NG','Nigeria','nigeria','common'),
    ('KE','Kenya','kenya','common'),
    ('CO','Colombia','colombia','common'),
    ('CL','Chile','chile','common'),
    ('PE','Peru','peru','common'),
]

for v in variants:
    cur.execute("""
        INSERT INTO sofia.country_aliases (country_code, alias, alias_norm, alias_type)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, v)

conn.commit()

# Create indexes
print("Creating indexes...")
cur.execute("CREATE INDEX idx_country_aliases_norm ON sofia.country_aliases(alias_norm)")
cur.execute("CREATE INDEX idx_country_aliases_code ON sofia.country_aliases(country_code)")
conn.commit()

# Create mapping tables
print("Creating signal_country_map...")
cur.execute("""
    CREATE TABLE sofia.signal_country_map (
        signal_id BIGINT PRIMARY KEY,
        country_code CHAR(2) NOT NULL,
        match_method TEXT NOT NULL,
        confidence_hint NUMERIC(3,2) NOT NULL DEFAULT 0.70,
        matched_text TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
""")
cur.execute("CREATE INDEX idx_signal_map_country ON sofia.signal_country_map(country_code)")

print("Creating cyber_event_country_map...")
cur.execute("""
    CREATE TABLE sofia.cyber_event_country_map (
        event_id BIGINT PRIMARY KEY,
        country_code CHAR(2) NOT NULL,
        match_method TEXT NOT NULL,
        confidence_hint NUMERIC(3,2) NOT NULL DEFAULT 0.50,
        matched_text TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
""")
cur.execute("CREATE INDEX idx_cyber_map_country ON sofia.cyber_event_country_map(country_code)")

print("Creating trial_country_map...")
cur.execute("""
    CREATE TABLE sofia.trial_country_map (
        nct_id VARCHAR(20) PRIMARY KEY,
        country_code CHAR(2) NOT NULL,
        match_method TEXT NOT NULL,
        confidence_hint NUMERIC(3,2) NOT NULL DEFAULT 0.50,
        matched_text TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
""")
cur.execute("CREATE INDEX idx_trial_map_country ON sofia.trial_country_map(country_code)")

conn.commit()

# Verify
cur.execute("SELECT COUNT(*) FROM sofia.country_aliases")
count = cur.fetchone()[0]
print(f"\n✅ country_aliases created with {count} entries")

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='sofia' AND table_name='country_aliases'")
print("Columns:", [r[0] for r in cur.fetchall()])

cur.close()
conn.close()
print("\nDone!")
