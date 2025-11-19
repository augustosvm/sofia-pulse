#!/usr/bin/env python3
"""
Entity Resolution - Fuzzy Matching

Liga researchers → GitHub repos → Companies → Funding
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
    'database': os.getenv('POSTGRES_DB', 'sofia_db'),
}

def fuzzy_match(str1, str2):
    """Simple fuzzy matching"""
    str1 = str1.lower().strip()
    str2 = str2.lower().strip()

    if str1 == str2:
        return 100

    # Exact substring
    if str1 in str2 or str2 in str1:
        return 80

    # Word overlap
    words1 = set(str1.split())
    words2 = set(str2.split())
    overlap = len(words1 & words2)
    total = len(words1 | words2)

    if total == 0:
        return 0

    return int((overlap / total) * 60)

def resolve_entities(conn):
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Papers authors
    cursor.execute("""
        SELECT DISTINCT unnest(authors) as author
        FROM arxiv_ai_papers
        WHERE authors IS NOT NULL
        LIMIT 100;
    """)
    authors = [r['author'] for r in cursor.fetchall()]

    # GitHub repo owners
    cursor.execute("""
        SELECT DISTINCT owner
        FROM sofia.github_trending
        WHERE owner IS NOT NULL
        LIMIT 100;
    """)
    github_owners = [r['owner'] for r in cursor.fetchall()]

    # Companies from funding
    cursor.execute("""
        SELECT DISTINCT company_name
        FROM sofia.funding_rounds
        WHERE company_name IS NOT NULL
        LIMIT 100;
    """)
    companies = [r['company_name'] for r in cursor.fetchall()]

    cursor.close()

    # Match authors → GitHub
    author_to_github = []
    for author in authors[:50]:
        for owner in github_owners[:50]:
            score = fuzzy_match(author, owner)
            if score >= 60:
                author_to_github.append({
                    'author': author,
                    'github': owner,
                    'score': score,
                })

    # Match GitHub → Companies
    github_to_company = []
    for owner in github_owners[:50]:
        for company in companies[:50]:
            score = fuzzy_match(owner, company)
            if score >= 60:
                github_to_company.append({
                    'github': owner,
                    'company': company,
                    'score': score,
                })

    return {
        'author_to_github': sorted(author_to_github, key=lambda x: x['score'], reverse=True)[:20],
        'github_to_company': sorted(github_to_company, key=lambda x: x['score'], reverse=True)[:20],
    }

def print_report(matches):
    print("=" * 80)
    print("ENTITY RESOLUTION - FUZZY MATCHING")
    print("=" * 80)
    print()
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Threshold: 60% similarity")
    print()
    print("=" * 80)
    print()

    print("🔗 RESEARCHERS → GITHUB")
    print("-" * 80)

    for match in matches['author_to_github'][:10]:
        print(f"   {match['author']} → {match['github']} ({match['score']}%)")

    print()
    print("🏢 GITHUB → COMPANIES")
    print("-" * 80)

    for match in matches['github_to_company'][:10]:
        print(f"   {match['github']} → {match['company']} ({match['score']}%)")

    print()
    print("=" * 80)
    print()
    print("✅ Resolution complete!")
    print()

def main():
    print("🔗 Entity Resolution...")
    print()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected")
        print()

        matches = resolve_entities(conn)
        print(f"📊 Matches found:")
        print(f"   Authors → GitHub: {len(matches['author_to_github'])}")
        print(f"   GitHub → Companies: {len(matches['github_to_company'])}")
        print()

        print_report(matches)

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
