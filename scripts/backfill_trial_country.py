#!/usr/bin/env python3
"""
Backfill Clinical Trial Country Mapping (Enterprise)
Purpose: Populate sofia.trial_country_map with deterministic country extraction
Uses pharma company lookup and alias_norm matching with FK validation
Run: python scripts/backfill_trial_country.py
"""

import psycopg2
import os
import re
import sys
from pathlib import Path
from datetime import datetime

BATCH_SIZE = 500

# Known pharma company -> country mappings (high confidence)
PHARMA_COUNTRY_MAP = {
    'pfizer': 'US',
    'merck': 'US',
    'johnson': 'US',  # Johnson & Johnson
    'abbvie': 'US',
    'eli lilly': 'US',
    'lilly': 'US',
    'bristol': 'US',  # Bristol-Myers Squibb
    'amgen': 'US',
    'gilead': 'US',
    'regeneron': 'US',
    'biogen': 'US',
    'vertex': 'US',
    'moderna': 'US',
    'novartis': 'CH',
    'roche': 'CH',
    'astrazeneca': 'GB',
    'glaxosmithkline': 'GB',
    'gsk': 'GB',
    'sanofi': 'FR',
    'bayer': 'DE',
    'boehringer': 'DE',
    'takeda': 'JP',
    'daiichi': 'JP',
    'astellas': 'JP',
    'otsuka': 'JP',
    'eisai': 'JP',
    'shionogi': 'JP',
    'novo nordisk': 'DK',
    'novonordisk': 'DK',
    'lundbeck': 'DK',
    'teva': 'IL',
    'samsung': 'KR',
    'celltrion': 'KR',
    'sun pharma': 'IN',
    'sunpharma': 'IN',
    'dr reddys': 'IN',
    'cipla': 'IN',
    'lupin': 'IN',
    'biocon': 'IN',
}

def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v

def get_db():
    load_env()
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("POSTGRES_DB", "sofia_db")
    )

def normalize_text(text):
    """Normalize text to match alias_norm format."""
    if not text:
        return ""
    return re.sub(r'[^a-z0-9]+', '', text.lower())

def load_aliases(conn):
    """Load country aliases from DB with alias_norm."""
    cur = conn.cursor()
    cur.execute("SELECT country_code, alias_norm FROM sofia.country_aliases")
    aliases = {}
    for row in cur.fetchall():
        aliases[row[1]] = row[0]
    cur.close()
    return aliases

def load_valid_countries(conn):
    """Load set of valid ISO2 country codes."""
    cur = conn.cursor()
    cur.execute("SELECT iso_alpha2 FROM sofia.countries WHERE iso_alpha2 IS NOT NULL")
    valid = set(row[0] for row in cur.fetchall())
    cur.close()
    return valid

def extract_country(sponsor, aliases, valid_countries):
    """
    Extract country from sponsor name.
    Priority:
    1. Known pharma company mapping (high confidence)
    2. Country in parentheses: "Company (Country)"
    3. Country alias_norm in sponsor text
    """
    if not sponsor:
        return None, None, 0.0
    
    sponsor_norm = normalize_text(sponsor)
    sponsor_lower = sponsor.lower()
    
    # 1. Check known pharma companies
    for company, code in PHARMA_COUNTRY_MAP.items():
        company_norm = normalize_text(company)
        if company_norm in sponsor_norm and code in valid_countries:
            return code, company, 0.90
    
    # 2. Check for (Country) pattern
    paren_match = re.search(r'\(([^)]+)\)', sponsor)
    if paren_match:
        country_text = paren_match.group(1).strip()
        country_norm = normalize_text(country_text)
        if country_norm in aliases and aliases[country_norm] in valid_countries:
            return aliases[country_norm], country_text, 0.85
    
    # 3. General alias_norm match
    for alias_norm, code in aliases.items():
        if len(alias_norm) >= 4 and alias_norm in sponsor_norm:
            if code in valid_countries:
                return code, alias_norm, 0.75
    
    return None, None, 0.0

def main():
    start_time = datetime.now()
    print("=" * 60)
    print("BACKFILL: Clinical Trial Country Mapping (Enterprise)")
    print(f"Started at: {start_time}")
    print("=" * 60)
    
    conn = get_db()
    
    # Load aliases and valid countries
    print("Loading country aliases...")
    aliases = load_aliases(conn)
    print(f"  Loaded {len(aliases)} aliases")
    
    print("Loading valid country codes...")
    valid_countries = load_valid_countries(conn)
    print(f"  Loaded {len(valid_countries)} valid ISO2 codes")
    
    # Get total count
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sofia.clinical_trials")
    total = cur.fetchone()[0]
    print(f"Total trials to process: {total}")
    
    # Clear existing mappings
    cur.execute("DELETE FROM sofia.trial_country_map")
    conn.commit()
    print("Cleared existing mappings")
    
    # Process in batches
    mapped = 0
    offset = 0
    
    while offset < total:
        cur.execute("""
            SELECT nct_id, sponsor 
            FROM sofia.clinical_trials
            ORDER BY nct_id
            LIMIT %s OFFSET %s
        """, (BATCH_SIZE, offset))
        
        batch = cur.fetchall()
        inserts = []
        
        for row in batch:
            nct_id, sponsor = row
            code, matched_text, confidence = extract_country(sponsor, aliases, valid_countries)
            
            if code and code in valid_countries:
                method = 'pharma_known' if confidence >= 0.85 else 'sponsor_alias'
                inserts.append((nct_id, code, method, confidence, matched_text[:100] if matched_text else None))
                mapped += 1
        
        # Batch insert
        if inserts:
            cur.executemany("""
                INSERT INTO sofia.trial_country_map 
                (nct_id, country_code, match_method, confidence_hint, matched_text)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (nct_id) DO UPDATE SET
                    country_code = EXCLUDED.country_code,
                    match_method = EXCLUDED.match_method,
                    confidence_hint = EXCLUDED.confidence_hint,
                    matched_text = EXCLUDED.matched_text,
                    updated_at = NOW()
            """, inserts)
            conn.commit()
        
        offset += BATCH_SIZE
        pct = 100 * offset / total
        print(f"  Progress: {min(offset, total)}/{total} ({pct:.1f}%) - Mapped: {mapped}", end='\r')
        sys.stdout.flush()
    
    print()
    
    # Summary
    duration = datetime.now() - start_time
    rate = (100 * mapped / total) if total > 0 else 0
    print(f"\n✅ Mapped {mapped}/{total} trials ({rate:.1f}%)")
    print(f"Duration: {duration}")
    
    # Top countries
    cur.execute("""
        SELECT country_code, COUNT(*) as cnt 
        FROM sofia.trial_country_map 
        GROUP BY country_code 
        ORDER BY cnt DESC 
        LIMIT 10
    """)
    print("\nTop 10 countries:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    cur.close()
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
