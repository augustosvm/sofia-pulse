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

def levenshtein_distance(s1, s2):
    """Calculate Levenshtein distance between two strings"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def fuzzy_match(str1, str2):
    """Enhanced fuzzy matching with Levenshtein distance"""
    str1 = str1.lower().strip()
    str2 = str2.lower().strip()

    # Exact match
    if str1 == str2:
        return 100

    # Exact substring match
    if str1 in str2 or str2 in str1:
        return 90

    # Extract initials (for author names like "John D. Smith" → "jdsmith")
    initials1 = ''.join([word[0] for word in str1.split() if word])
    initials2 = ''.join([word[0] for word in str2.split() if word])
    if initials1 and initials2 and (initials1 in str2 or initials2 in str1):
        return 75

    # Word overlap (Jaccard similarity)
    words1 = set(str1.split())
    words2 = set(str2.split())
    overlap = len(words1 & words2)
    total = len(words1 | words2)

    if total > 0:
        jaccard = (overlap / total) * 100
        if jaccard >= 50:
            return int(jaccard)

    # Levenshtein similarity (for typos, abbreviations)
    max_len = max(len(str1), len(str2))
    if max_len > 0:
        distance = levenshtein_distance(str1, str2)
        similarity = (1 - distance / max_len) * 100
        if similarity >= 50:
            return int(similarity)

    return 0

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

    # Match authors → GitHub (increased sample size, lower threshold)
    author_to_github = []
    for author in authors[:100]:  # More comparisons
        for owner in github_owners[:100]:
            score = fuzzy_match(author, owner)
            if score >= 50:  # Lower threshold from 60 to 50
                author_to_github.append({
                    'author': author,
                    'github': owner,
                    'score': score,
                })

    # Match GitHub → Companies
    github_to_company = []
    for owner in github_owners[:100]:
        for company in companies[:100]:
            score = fuzzy_match(owner, company)
            if score >= 50:  # Lower threshold from 60 to 50
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
    print("Threshold: 50% similarity (Levenshtein + Jaccard + Initials matching)")
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

        # Capture report output
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()

        print_report(matches)

        # Get report content
        report_content = buffer.getvalue()
        sys.stdout = old_stdout

        # Print to console
        print(report_content)

        # Save to file
        output_file = 'analytics/entity-resolution-latest.txt'
        with open(output_file, 'w') as f:
            f.write(report_content)

        print(f"💾 Saved to: {output_file}")
        print()

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
