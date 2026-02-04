#!/usr/bin/env python3
"""
Gemini LLM Enrichment Pipeline for HackerNews Items
Fills extracted_topics and extracted_entities to enable cross-signals insights.

Usage:
    python3 scripts/enrich-hackernews-items-gemini.py --limit 200
    python3 scripts/enrich-hackernews-items-gemini.py --limit 500 --dry-run

Environment Variables:
    GEMINI_API_KEY           - Required: Google Gemini API key
    GEMINI_MODEL             - Optional: Model name (default: gemini-2.0-flash-exp)
    GEMINI_DAILY_CALL_LIMIT  - Optional: Max API calls per day (default: 500)
    POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

import psycopg2
import requests

# Database connection
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "sofia"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "database": os.getenv("POSTGRES_DB", "sofia_db"),
}

# Gemini configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
GEMINI_DAILY_CALL_LIMIT = int(os.getenv("GEMINI_DAILY_CALL_LIMIT", "500"))
PROMPT_VERSION = "v1"

# Gemini API endpoint
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"


def create_cache_key(title: str, url: str) -> str:
    """Generate SHA256 cache key from title + url"""
    data = f"{title}|{url}"
    return hashlib.sha256(data.encode()).hexdigest()


def check_daily_budget(conn, run_id: str) -> bool:
    """Check if we've exceeded daily API call limit"""
    cursor = conn.cursor()

    # Count API calls made today
    cursor.execute("""
        SELECT COALESCE(SUM(llm_calls), 0) as calls_today
        FROM sofia.llm_enrichment_runs
        WHERE started_at >= CURRENT_DATE
          AND run_id != %s
    """, (run_id,))

    calls_today = cursor.fetchone()[0]
    cursor.close()

    if calls_today >= GEMINI_DAILY_CALL_LIMIT:
        print(f"⚠️  Daily budget exceeded: {calls_today}/{GEMINI_DAILY_CALL_LIMIT} calls made today")
        return False

    return True


def get_from_cache(conn, cache_key: str, source: str, model: str, prompt_version: str) -> Optional[Dict]:
    """Retrieve cached result if exists"""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT result
        FROM sofia.llm_enrichment_cache
        WHERE cache_key = %s
          AND source = %s
          AND model = %s
          AND prompt_version = %s
    """, (cache_key, source, model, prompt_version))

    row = cursor.fetchone()
    cursor.close()

    if row:
        return row[0]
    return None


def save_to_cache(conn, cache_key: str, source: str, model: str, prompt_version: str,
                  input_data: Dict, result: Dict, tokens_used: int = 0, cost_usd: float = 0.0):
    """Save enrichment result to cache"""
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sofia.llm_enrichment_cache (
            cache_key, source, model, prompt_version, input_data, result, tokens_used, cost_usd
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (cache_key) DO UPDATE SET
            result = EXCLUDED.result,
            created_at = NOW()
    """, (cache_key, source, model, prompt_version, json.dumps(input_data),
          json.dumps(result), tokens_used, cost_usd))

    conn.commit()
    cursor.close()


def call_gemini(title: str, url: str, text_content: Optional[str] = None) -> Optional[Dict]:
    """
    Call Gemini API to extract topics and entities from HN item.

    Returns:
        {
            "topics": ["rust", "webassembly", "performance", ...],
            "entities": {
                "companies": ["Google", "Amazon"],
                "technologies": ["Rust", "WASM", "Kubernetes"],
                "products": ["Chrome", "VS Code"],
                "people": ["Linus Torvalds"],
                "countries": ["USA", "China"],
                "projects": ["Linux Kernel", "LLVM"]
            }
        }
    """

    # Truncate text_content if too long
    snippet = ""
    if text_content:
        snippet = text_content[:300] + "..." if len(text_content) > 300 else text_content

    prompt = f"""Extract tech topics and named entities from this HackerNews item.

TITLE: {title}
URL: {url}
{f'SNIPPET: {snippet}' if snippet else ''}

Return ONLY valid JSON in this exact format (no markdown, no extra text):
{{
  "topics": ["topic1", "topic2", ...],
  "entities": {{
    "companies": ["Company1", "Company2"],
    "technologies": ["Tech1", "Tech2"],
    "products": ["Product1"],
    "people": ["Person1"],
    "countries": ["Country1"],
    "projects": ["Project1"]
  }}
}}

Rules:
- topics: 3-12 items, lowercase, single words or short phrases (e.g., "rust", "machine learning", "webassembly")
- companies: Title Case (e.g., "OpenAI", "Google")
- technologies: Can be lowercase (e.g., "rust", "kubernetes") or mixed case for acronyms (e.g., "LLM", "AWS")
- Keep arrays empty [] if nothing found
- Max 10 items per entity category
- Be concise and relevant to tech/startups/engineering
"""

    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json"
        }
    }

    try:
        response = requests.post(
            GEMINI_API_URL,
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 429:
            print(f"      ⚠️  Rate limit hit, retrying in 5s...")
            time.sleep(5)
            response = requests.post(GEMINI_API_URL, json=payload, timeout=30)

        response.raise_for_status()

        data = response.json()

        # Extract text from response
        if "candidates" in data and len(data["candidates"]) > 0:
            text = data["candidates"][0]["content"]["parts"][0]["text"]

            # Parse JSON
            result = json.loads(text)

            # Normalize topics (lowercase, trim, unique)
            if "topics" in result:
                result["topics"] = list(set([
                    t.strip().lower() for t in result["topics"] if t.strip()
                ]))

            # Normalize entities
            if "entities" in result:
                for key in ["companies", "technologies", "products", "people", "countries", "projects"]:
                    if key in result["entities"]:
                        result["entities"][key] = list(set([
                            e.strip() for e in result["entities"][key] if e.strip()
                        ]))[:10]  # Max 10 per category
                    else:
                        result["entities"][key] = []

            return result

        return None

    except requests.exceptions.Timeout:
        print(f"      ⚠️  Timeout calling Gemini API")
        return None
    except requests.exceptions.RequestException as e:
        print(f"      ❌ API Error: {str(e)[:100]}")
        return None
    except json.JSONDecodeError as e:
        print(f"      ❌ JSON Parse Error: {str(e)[:100]}")
        return None
    except Exception as e:
        print(f"      ❌ Unexpected Error: {str(e)[:100]}")
        return None


def enrich_item(conn, item: Dict, run_id: str, dry_run: bool = False) -> Dict:
    """
    Enrich single news item with topics and entities.

    Returns stats: {"cache_hit": bool, "llm_call": bool, "enriched": bool, "error": str or None}
    """
    item_id = item["id"]
    title = item["title"] or ""
    url = item["url"] or ""
    text_content = item.get("text_content")

    cache_key = create_cache_key(title, url)

    # Check cache first
    cached_result = get_from_cache(conn, cache_key, "hackernews", GEMINI_MODEL, PROMPT_VERSION)

    if cached_result:
        print(f"      ✅ Cache hit (id={item_id})")

        if not dry_run:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sofia.news_items
                SET extracted_topics = %s,
                    extracted_entities = %s
                WHERE id = %s
            """, (cached_result.get("topics", []),
                  json.dumps(cached_result.get("entities", {})),
                  item_id))
            conn.commit()
            cursor.close()

        return {"cache_hit": True, "llm_call": False, "enriched": True, "error": None}

    # Check daily budget before API call
    if not check_daily_budget(conn, run_id):
        return {"cache_hit": False, "llm_call": False, "enriched": False, "error": "budget_exceeded"}

    # Call Gemini API
    print(f"      🔄 Calling Gemini API (id={item_id}): {title[:60]}...")

    result = call_gemini(title, url, text_content)

    if not result:
        return {"cache_hit": False, "llm_call": True, "enriched": False, "error": "llm_failed"}

    # Save to cache
    input_data = {"title": title, "url": url}
    if not dry_run:
        save_to_cache(conn, cache_key, "hackernews", GEMINI_MODEL, PROMPT_VERSION, input_data, result)

    # Update news_items
    topics = result.get("topics", [])
    entities = result.get("entities", {})

    print(f"      ✅ Enriched: {len(topics)} topics, {sum(len(v) for v in entities.values())} entities")

    if not dry_run:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sofia.news_items
            SET extracted_topics = %s,
                extracted_entities = %s
            WHERE id = %s
        """, (topics, json.dumps(entities), item_id))
        conn.commit()
        cursor.close()

    return {"cache_hit": False, "llm_call": True, "enriched": True, "error": None}


def main():
    parser = argparse.ArgumentParser(description="Enrich HackerNews items with Gemini LLM")
    parser.add_argument("--limit", type=int, default=200, help="Max items to process (default: 200)")
    parser.add_argument("--dry-run", action="store_true", help="Don't update database")
    args = parser.parse_args()

    if not GEMINI_API_KEY:
        print("❌ Error: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    print("=" * 80)
    print("GEMINI LLM ENRICHMENT - HACKERNEWS ITEMS")
    print("=" * 80)
    print(f"Model: {GEMINI_MODEL}")
    print(f"Prompt Version: {PROMPT_VERSION}")
    print(f"Limit: {args.limit}")
    print(f"Dry Run: {args.dry_run}")
    print(f"Daily Budget: {GEMINI_DAILY_CALL_LIMIT} calls")
    print("=" * 80)
    print()

    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    # Create run record
    run_id = str(uuid4())
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sofia.llm_enrichment_runs (
            run_id, source, model, prompt_version, limit_requested
        ) VALUES (%s, %s, %s, %s, %s)
    """, (run_id, "hackernews", GEMINI_MODEL, PROMPT_VERSION, args.limit))
    conn.commit()
    cursor.close()

    # Select items to enrich
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, url, text_content
        FROM sofia.news_items
        WHERE source = 'hackernews'
          AND (
              extracted_topics IS NULL
              OR array_length(extracted_topics, 1) IS NULL
              OR extracted_entities IS NULL
          )
        ORDER BY published_at DESC NULLS LAST
        LIMIT %s
    """, (args.limit,))

    items = []
    for row in cursor.fetchall():
        items.append({
            "id": row[0],
            "title": row[1],
            "url": row[2],
            "text_content": row[3]
        })

    cursor.close()

    print(f"📊 Found {len(items)} items to enrich")
    print()

    if len(items) == 0:
        print("✅ All items already enriched!")
        conn.close()
        return

    # Process items
    stats = {
        "processed": 0,
        "enriched": 0,
        "cache_hits": 0,
        "llm_calls": 0,
        "errors": 0,
        "error_details": []
    }

    for i, item in enumerate(items, 1):
        print(f"[{i}/{len(items)}] Processing item {item['id']}...")

        result = enrich_item(conn, item, run_id, args.dry_run)

        stats["processed"] += 1

        if result["cache_hit"]:
            stats["cache_hits"] += 1

        if result["llm_call"]:
            stats["llm_calls"] += 1

        if result["enriched"]:
            stats["enriched"] += 1

        if result["error"]:
            stats["errors"] += 1
            stats["error_details"].append({
                "id": item["id"],
                "error": result["error"]
            })

            if result["error"] == "budget_exceeded":
                print()
                print("⚠️  Daily budget exceeded! Stopping.")
                break

        # Rate limiting (1 request per second when calling API)
        if result["llm_call"] and i < len(items):
            time.sleep(1)

    # Update run record
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE sofia.llm_enrichment_runs
        SET finished_at = NOW(),
            processed = %s,
            enriched = %s,
            cache_hits = %s,
            llm_calls = %s,
            errors = %s,
            error_details = %s,
            budget_limit_hit = %s,
            status = CASE
                WHEN %s > 0 THEN 'budget_exceeded'
                WHEN %s > 0 THEN 'completed_with_errors'
                ELSE 'completed'
            END
        WHERE run_id = %s
    """, (
        stats["processed"],
        stats["enriched"],
        stats["cache_hits"],
        stats["llm_calls"],
        stats["errors"],
        json.dumps(stats["error_details"]),
        any(e["error"] == "budget_exceeded" for e in stats["error_details"]),
        1 if any(e["error"] == "budget_exceeded" for e in stats["error_details"]) else 0,
        stats["errors"],
        run_id
    ))
    conn.commit()
    cursor.close()

    conn.close()

    # Print summary
    print()
    print("=" * 80)
    print("ENRICHMENT COMPLETE")
    print("=" * 80)
    print(f"Processed:    {stats['processed']}")
    print(f"Enriched:     {stats['enriched']}")
    print(f"Cache Hits:   {stats['cache_hits']}")
    print(f"LLM Calls:    {stats['llm_calls']}")
    print(f"Errors:       {stats['errors']}")
    print(f"Dry Run:      {args.dry_run}")
    print("=" * 80)

    if stats["errors"] > 0:
        print()
        print("⚠️  Errors encountered:")
        for e in stats["error_details"][:5]:
            print(f"  - Item {e['id']}: {e['error']}")
        if len(stats["error_details"]) > 5:
            print(f"  ... and {len(stats['error_details']) - 5} more")


if __name__ == "__main__":
    main()
