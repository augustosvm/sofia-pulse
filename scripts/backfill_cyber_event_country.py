#!/usr/bin/env python3
"""
Backfill Cyber Event Country Mapping (Enterprise)
Purpose: Populate sofia.cyber_event_country_map with deterministic country extraction
Uses alias_norm for matching and validates country_code via FK lookup
Run: python scripts/backfill_cyber_event_country.py
"""

import psycopg2
import os
import re
import sys
from pathlib import Path
from datetime import datetime

BATCH_SIZE = 500

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

def extract_country(title, description, aliases, valid_countries):
    """
    Extract country from cyber event text.
    Priority:
    1. Explicit ISO2 pattern in text
    2. Exact alias_norm match in title (higher confidence)
    3. Exact alias_norm match in description (lower confidence)
    """
    title_text = title or ''
    desc_text = description or ''
    combined = f"{title_text} {desc_text}"
    
    if not combined.strip():
        return None, None, 0.0
    
    # 1. Check for explicit ISO2 patterns
    iso_patterns = [
        r'country[:\s]+([A-Z]{2})\b',
        r'\(([A-Z]{2})\)',
        r'\b([A-Z]{2})\s*(?:based|located|headquartered)\b',
    ]
    for pattern in iso_patterns:
        match = re.search(pattern, combined, re.IGNORECASE)
        if match:
            code = match.group(1).upper()
            if code in valid_countries:
                return code, match.group(0)[:50], 0.80
    
    # 2. Alias_norm match in title (higher confidence)
    title_norm = normalize_text(title_text)
    best_match = None
    best_code = None
    best_len = 0
    
    for alias_norm, code in aliases.items():
        if len(alias_norm) >= 4 and alias_norm in title_norm:
            if len(alias_norm) > best_len:
                best_match = alias_norm
                best_code = code
                best_len = len(alias_norm)
    
    if best_code and best_code in valid_countries:
        return best_code, best_match, 0.80
    
    # 3. Alias_norm match in description (lower confidence)
    desc_norm = normalize_text(desc_text)
    best_match = None
    best_code = None
    best_len = 0
    
    for alias_norm, code in aliases.items():
        if len(alias_norm) >= 4 and alias_norm in desc_norm:
            if len(alias_norm) > best_len:
                best_match = alias_norm
                best_code = code
                best_len = len(alias_norm)
    
    if best_code and best_code in valid_countries:
        return best_code, best_match, 0.65
    
    return None, None, 0.0

def main():
    start_time = datetime.now()
    print("=" * 60)
    print("BACKFILL: Cyber Event Country Mapping (Enterprise)")
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
    cur.execute("SELECT COUNT(*) FROM sofia.cybersecurity_events")
    total = cur.fetchone()[0]
    print(f"Total events to process: {total}")
    
    # Clear existing mappings
    cur.execute("DELETE FROM sofia.cyber_event_country_map")
    conn.commit()
    print("Cleared existing mappings")
    
    # Process in batches
    mapped = 0
    offset = 0
    
    while offset < total:
        cur.execute("""
            SELECT id, title, description 
            FROM sofia.cybersecurity_events
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (BATCH_SIZE, offset))
        
        batch = cur.fetchall()
        inserts = []
        
        for row in batch:
            event_id, title, description = row
            code, matched_text, confidence = extract_country(title, description, aliases, valid_countries)
            
            if code and code in valid_countries:
                method = 'alias_exact' if confidence >= 0.75 else 'alias_partial'
                inserts.append((event_id, code, method, confidence, matched_text[:100] if matched_text else None))
                mapped += 1
        
        # Batch insert
        if inserts:
            cur.executemany("""
                INSERT INTO sofia.cyber_event_country_map 
                (event_id, country_code, match_method, confidence_hint, matched_text)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO UPDATE SET
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
    print(f"\n✅ Mapped {mapped}/{total} events ({rate:.1f}%)")
    print(f"Duration: {duration}")
    
    # Top countries
    cur.execute("""
        SELECT country_code, COUNT(*) as cnt 
        FROM sofia.cyber_event_country_map 
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
