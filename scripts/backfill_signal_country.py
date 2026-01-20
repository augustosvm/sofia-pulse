#!/usr/bin/env python3
"""
Backfill Industry Signal Country Mapping (Enterprise)
Purpose: Populate sofia.signal_country_map with deterministic country extraction
Uses alias_norm for matching and validates country_code via FK lookup
Run: python scripts/backfill_signal_country.py
"""

import psycopg2
import os
import re
import sys
from pathlib import Path
from datetime import datetime

BATCH_SIZE = 1000

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
    """Normalize text to match alias_norm format (lowercase, alphanumeric only)."""
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

def extract_country_from_metadata(metadata, aliases, valid_countries):
    """Extract country from metadata JSON with priority order."""
    if not metadata or not isinstance(metadata, dict):
        return None, None, 0.0
    
    # 1. Check jurisdiction (often ISO2)
    jurisdiction = metadata.get('jurisdiction', '')
    if jurisdiction and len(jurisdiction) == 2 and jurisdiction.upper() in valid_countries:
        return jurisdiction.upper(), 'metadata_jurisdiction', 0.90
    
    # 2. Check explicit country_code
    country_code = metadata.get('country_code', '')
    if country_code and len(country_code) == 2 and country_code.upper() in valid_countries:
        return country_code.upper(), 'metadata_country_code', 0.90
    
    # 3. Check country name via alias_norm
    country = metadata.get('country', '')
    if country:
        country_norm = normalize_text(country)
        if country_norm in aliases:
            return aliases[country_norm], 'metadata_country', 0.85
    
    # 4. Extract from actor/source domain patterns (.br .de .cn)
    for key in ['actor1', 'actor2', 'source', 'url']:
        val = str(metadata.get(key, ''))
        match = re.search(r'\.([a-z]{2})(?:[/\s]|$)', val.lower())
        if match:
            code = match.group(1).upper()
            if code in valid_countries:
                return code, 'url_tld', 0.80
    
    return None, None, 0.0

def extract_country_from_title(title, aliases):
    """Fallback: extract country from title text via alias_norm."""
    if not title:
        return None, None, 0.0
    
    title_norm = normalize_text(title)
    best_match = None
    best_code = None
    best_len = 0
    
    for alias_norm, code in aliases.items():
        if len(alias_norm) >= 4 and alias_norm in title_norm:
            if len(alias_norm) > best_len:
                best_match = alias_norm
                best_code = code
                best_len = len(alias_norm)
    
    if best_code:
        return best_code, 'alias_exact', 0.75
    
    return None, None, 0.0

def main():
    start_time = datetime.now()
    print("=" * 60)
    print("BACKFILL: Industry Signal Country Mapping (Enterprise)")
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
    cur.execute("SELECT COUNT(*) FROM sofia.industry_signals")
    total = cur.fetchone()[0]
    print(f"Total signals to process: {total}")
    
    # Clear existing mappings
    cur.execute("DELETE FROM sofia.signal_country_map")
    conn.commit()
    print("Cleared existing mappings")
    
    # Process in batches
    mapped = 0
    offset = 0
    
    while offset < total:
        cur.execute("""
            SELECT id, title, metadata 
            FROM sofia.industry_signals
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (BATCH_SIZE, offset))
        
        batch = cur.fetchall()
        inserts = []
        
        for row in batch:
            signal_id, title, metadata = row
            
            # Try metadata first
            code, method, confidence = extract_country_from_metadata(metadata, aliases, valid_countries)
            
            if not code:
                # Fallback to title
                code, method, confidence = extract_country_from_title(title, aliases)
            
            if code and code in valid_countries:
                inserts.append((signal_id, code, method, confidence))
                mapped += 1
        
        # Batch insert
        if inserts:
            cur.executemany("""
                INSERT INTO sofia.signal_country_map 
                (signal_id, country_code, match_method, confidence_hint)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (signal_id) DO UPDATE SET
                    country_code = EXCLUDED.country_code,
                    match_method = EXCLUDED.match_method,
                    confidence_hint = EXCLUDED.confidence_hint,
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
    print(f"\n✅ Mapped {mapped}/{total} signals ({rate:.1f}%)")
    print(f"Duration: {duration}")
    
    # Top countries
    cur.execute("""
        SELECT country_code, COUNT(*) as cnt 
        FROM sofia.signal_country_map 
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
