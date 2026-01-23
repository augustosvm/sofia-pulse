#!/usr/bin/env python3
"""
Content Meta Builder

Extracts metadata from pages (word_count, reading_time) for deep read scoring.

Approach:
1. Get top 500 pages from GA4 (last 30 days)
2. Fetch HTML and parse word_count
3. Calculate reading_time = ceil((word_count / 200) * 60) seconds
4. Upsert to sofia.content_meta table
5. Cache locally to avoid re-fetching
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from bs4 import BeautifulSoup
import json
import hashlib
from datetime import datetime
import time
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'sofia_db'),
}

BASE_URL = "https://www.tiespecialistas.com.br"
WORDS_PER_MINUTE = 200
MAX_PAGES = 500
CACHE_DIR = "cache/content_meta"
REQUEST_TIMEOUT = 10

def ensure_table_exists(conn):
    """Create content_meta table if not exists"""
    cursor = conn.cursor()

    query = """
    CREATE TABLE IF NOT EXISTS sofia.content_meta (
        page_path TEXT PRIMARY KEY,
        url TEXT NOT NULL,
        title TEXT,
        author TEXT,
        publish_date DATE,
        word_count INTEGER NOT NULL,
        reading_time_sec INTEGER NOT NULL,
        last_scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_content_meta_word_count ON sofia.content_meta(word_count);
    CREATE INDEX IF NOT EXISTS idx_content_meta_reading_time ON sofia.content_meta(reading_time_sec);
    """

    cursor.execute(query)
    conn.commit()
    cursor.close()

def get_top_pages(conn, days=30, limit=500):
    """Get top pages from GA4 analytics_events"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = f"""
    SELECT
        page_path,
        COUNT(DISTINCT user_pseudo_id) as users,
        COUNT(*) as events
    FROM sofia.analytics_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '{days} days'
        AND page_path IS NOT NULL
        AND page_path NOT IN ('/', '/blog/', '/cursos/')
        AND page_path NOT LIKE '%%?%%'  -- Exclude query params
    GROUP BY page_path
    ORDER BY users DESC
    LIMIT {limit}
    """

    cursor.execute(query)
    return cursor.fetchall()

def load_cache():
    """Load local cache of scraped pages"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = f"{CACHE_DIR}/pages.json"

    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    return {}

def save_cache(cache):
    """Save cache to disk"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = f"{CACHE_DIR}/pages.json"

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def scrape_page(url, cache):
    """Scrape page and extract metadata"""

    # Check cache
    cache_key = hashlib.md5(url.encode()).hexdigest()
    if cache_key in cache:
        cached = cache[cache_key]
        # Use cache if less than 7 days old
        cache_age = (datetime.now() - datetime.fromisoformat(cached['scraped_at'])).days
        if cache_age < 7:
            return cached['meta']

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT, headers={
            'User-Agent': 'Mozilla/5.0 (Sofia Pulse Content Analyzer)'
        })

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title
        title_tag = soup.find('title') or soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else None

        # Extract author (common WordPress selectors)
        author = None
        author_tag = soup.find(class_=['author', 'author-name', 'entry-author']) or \
                     soup.find('meta', {'name': 'author'})
        if author_tag:
            if author_tag.name == 'meta':
                author = author_tag.get('content')
            else:
                author = author_tag.get_text(strip=True)

        # Extract publish date
        publish_date = None
        date_tag = soup.find('time') or \
                   soup.find('meta', {'property': 'article:published_time'}) or \
                   soup.find('meta', {'name': 'pubdate'})
        if date_tag:
            if date_tag.name == 'meta':
                publish_date = date_tag.get('content')
            else:
                publish_date = date_tag.get('datetime') or date_tag.get_text(strip=True)

        # Extract main content and count words
        # Try common content selectors
        content = soup.find('article') or \
                 soup.find(class_=['entry-content', 'post-content', 'article-content', 'content']) or \
                 soup.find('main')

        if not content:
            content = soup.find('body')

        # Remove script, style, nav, footer, header
        for tag in content.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        # Get text and count words
        text = content.get_text(separator=' ', strip=True)
        words = text.split()
        word_count = len(words)

        # Calculate reading time
        reading_time_sec = int((word_count / WORDS_PER_MINUTE) * 60)

        meta = {
            'title': title,
            'author': author,
            'publish_date': publish_date,
            'word_count': word_count,
            'reading_time_sec': reading_time_sec
        }

        # Update cache
        cache[cache_key] = {
            'url': url,
            'meta': meta,
            'scraped_at': datetime.now().isoformat()
        }

        return meta

    except Exception as e:
        print(f"  [ERROR] Failed to scrape {url}: {e}")
        return None

def upsert_content_meta(conn, page_path, url, meta):
    """Upsert content metadata to database"""
    cursor = conn.cursor()

    query = """
    INSERT INTO sofia.content_meta (
        page_path,
        url,
        title,
        author,
        publish_date,
        word_count,
        reading_time_sec,
        last_scraped_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
    ON CONFLICT (page_path) DO UPDATE SET
        url = EXCLUDED.url,
        title = EXCLUDED.title,
        author = EXCLUDED.author,
        publish_date = EXCLUDED.publish_date,
        word_count = EXCLUDED.word_count,
        reading_time_sec = EXCLUDED.reading_time_sec,
        last_scraped_at = NOW()
    """

    try:
        cursor.execute(query, (
            page_path,
            url,
            meta['title'],
            meta['author'],
            meta['publish_date'],
            meta['word_count'],
            meta['reading_time_sec']
        ))
        conn.commit()
        return True

    except Exception as e:
        print(f"  [ERROR] Failed to upsert {page_path}: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()

def main():
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        print("[OK] Connected to database")

        # Ensure table exists
        ensure_table_exists(conn)
        print("[OK] content_meta table ready")
        print("")

        # Get top pages
        print("Fetching top pages from GA4...")
        pages = get_top_pages(conn, days=30, limit=MAX_PAGES)
        print(f"[OK] Found {len(pages)} pages to process")
        print("")

        # Load cache
        cache = load_cache()
        print(f"[OK] Loaded cache with {len(cache)} entries")
        print("")

        # Process pages
        processed = 0
        skipped = 0
        failed = 0

        for i, page in enumerate(pages, 1):
            page_path = page['page_path']
            url = f"{BASE_URL}{page_path}"

            print(f"[{i}/{len(pages)}] Processing: {page_path}")

            # Scrape page
            meta = scrape_page(url, cache)

            if meta:
                # Upsert to database
                if upsert_content_meta(conn, page_path, url, meta):
                    processed += 1
                    print(f"  OK: {meta['word_count']} words, {meta['reading_time_sec']}s reading time")
                else:
                    failed += 1
            else:
                skipped += 1
                print(f"  SKIP: Could not scrape")

            # Rate limiting
            time.sleep(0.5)

        # Save cache
        save_cache(cache)
        print("")
        print("[OK] Cache saved")

        # Close connection
        conn.close()

        # Summary
        print("")
        print("=" * 80)
        print("CONTENT META BUILDER COMPLETE")
        print("=" * 80)
        print("")
        print(f"Total pages: {len(pages)}")
        print(f"Processed: {processed}")
        print(f"Skipped: {skipped}")
        print(f"Failed: {failed}")
        print("")

        if processed > 0:
            print("[OK] Content metadata updated successfully")
        else:
            print("[WARNING] No pages processed")

    except Exception as e:
        print(f"[ERROR] Failed to build content metadata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
