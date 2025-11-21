#!/usr/bin/env python3
"""
Top 10 Tech Trends - Weekly Report

Combina TODAS as fontes para rankeamento final
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv
import math

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
    'database': os.getenv('POSTGRES_DB', 'sofia_db'),
}

def normalize(value, max_value):
    if max_value == 0:
        return 0
    return min(100, (value / max_value) * 100)

def get_tech_scores(conn):
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # GitHub
    cursor.execute("""
        SELECT language as tech, SUM(stars) as stars
        FROM sofia.github_trending
        WHERE language IS NOT NULL
        GROUP BY language
        ORDER BY stars DESC LIMIT 50;
    """)
    github = {r['tech']: float(r['stars']) for r in cursor.fetchall()}

    # HackerNews
    cursor.execute("""
        SELECT unnest(mentioned_technologies) as tech, COUNT(*) as mentions
        FROM sofia.hackernews_stories
        GROUP BY tech ORDER BY mentions DESC LIMIT 50;
    """)
    hn = {r['tech']: float(r['mentions']) for r in cursor.fetchall()}

    # Reddit
    cursor.execute("""
        SELECT unnest(technologies) as tech, COUNT(*) as mentions
        FROM sofia.reddit_tech
        GROUP BY tech ORDER BY mentions DESC LIMIT 50;
    """)
    reddit = {r['tech']: float(r['mentions']) for r in cursor.fetchall()}

    # NPM
    cursor.execute("""
        SELECT package_name as tech, MAX(downloads_month) as downloads
        FROM sofia.npm_stats
        GROUP BY package_name ORDER BY downloads DESC LIMIT 50;
    """)
    npm = {r['tech']: float(r['downloads']) for r in cursor.fetchall()}

    # PyPI
    cursor.execute("""
        SELECT package_name as tech, MAX(downloads_month) as downloads
        FROM sofia.pypi_stats
        GROUP BY package_name ORDER BY downloads DESC LIMIT 50;
    """)
    pypi = {r['tech']: float(r['downloads']) for r in cursor.fetchall()}

    cursor.close()

    # Normalize
    max_github = max(github.values()) if github else 1
    max_hn = max(hn.values()) if hn else 1
    max_reddit = max(reddit.values()) if reddit else 1
    max_npm = max(npm.values()) if npm else 1
    max_pypi = max(pypi.values()) if pypi else 1

    all_techs = set(github.keys()) | set(hn.keys()) | set(reddit.keys()) | set(npm.keys()) | set(pypi.keys())

    scores = []
    for tech in all_techs:
        github_score = normalize(github.get(tech, 0), max_github) * 0.3
        hn_score = normalize(hn.get(tech, 0), max_hn) * 0.2
        reddit_score = normalize(reddit.get(tech, 0), max_reddit) * 0.15
        npm_score = normalize(npm.get(tech, 0), max_npm) * 0.175
        pypi_score = normalize(pypi.get(tech, 0), max_pypi) * 0.175

        total = github_score + hn_score + reddit_score + npm_score + pypi_score

        if total > 0:
            scores.append({
                'tech': tech,
                'score': total,
                'github': github.get(tech, 0),
                'hn': hn.get(tech, 0),
                'reddit': reddit.get(tech, 0),
                'npm': npm.get(tech, 0),
                'pypi': pypi.get(tech, 0),
            })

    return sorted(scores, key=lambda x: x['score'], reverse=True)

def print_report(scores):
    print("=" * 80)
    print("TOP 10 TECH TRENDS - WEEKLY REPORT")
    print("=" * 80)
    print()
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Formula: GitHub(30%) + HN(20%) + Reddit(15%) + NPM(17.5%) + PyPI(17.5%)")
    print()
    print("=" * 80)
    print()

    print("🏆 TOP 10 TECH TRENDS")
    print("-" * 80)
    print(f"{'Rank':<6} {'Technology':<25} {'Score':<10} {'Sources':<30}")
    print("-" * 80)

    for idx, tech in enumerate(scores[:10], 1):
        sources = []
        if tech['github'] > 0:
            sources.append(f"GH:{int(tech['github']):,}")
        if tech['hn'] > 0:
            sources.append(f"HN:{int(tech['hn'])}")
        if tech['reddit'] > 0:
            sources.append(f"R:{int(tech['reddit'])}")
        if tech['npm'] > 0:
            sources.append(f"NPM:{int(tech['npm']/1000)}k")
        if tech['pypi'] > 0:
            sources.append(f"PyPI:{int(tech['pypi']/1000)}k")

        sources_str = " | ".join(sources)

        print(f"{idx:<6} {tech['tech']:<25} {tech['score']:<10.1f} {sources_str:<30}")

    print()
    print("=" * 80)
    print()

    # Rising stars
    print("🚀 RISING STARS (High growth, multiple sources)")
    print()

    rising = [t for t in scores[:20] if sum([
        1 if t['github'] > 0 else 0,
        1 if t['hn'] > 0 else 0,
        1 if t['reddit'] > 0 else 0,
        1 if t['npm'] > 0 else 0,
        1 if t['pypi'] > 0 else 0,
    ]) >= 3]

    for tech in rising[:5]:
        print(f"   • {tech['tech']}: Score {tech['score']:.1f}")

    print()
    print("=" * 80)
    print()
    print("✅ Report complete!")
    print()

def main():
    print("🔥 Connecting to database...")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected")
        print()

        scores = get_tech_scores(conn)
        print(f"📊 {len(scores)} technologies analyzed")
        print()

        # Capture report output
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()

        print_report(scores)

        # Get report content
        report_content = buffer.getvalue()
        sys.stdout = old_stdout

        # Print to console
        print(report_content)

        # Save to file
        output_file = 'analytics/top10-latest.txt'
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
