#!/usr/bin/env python3
"""
================================================================================
EARLY-STAGE DEEP DIVE - Sofia Pulse
================================================================================
Intelligent analysis of early-stage startup ecosystem using ALL available data.

Strategy:
1. Detect data date range (not hardcoded to "last 12 months")
2. Use full historical data for meaningful analysis
3. Cross-reference: Funding -> YC -> GitHub -> Papers
4. Provide insights regardless of data volume

Connects:
- Funding rounds (all stages, with focus on early-stage)
- YC batches (proxy for early-stage activity)
- GitHub trending repos (tech stack signals)
- Research papers (R&D pipeline)
- Geographic patterns
================================================================================
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from collections import defaultdict

from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', os.getenv('POSTGRES_HOST', 'localhost')),
    'port': int(os.getenv('DB_PORT', os.getenv('POSTGRES_PORT', '5432'))),
    'user': os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'postgres')),
    'password': os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', '')),
    'database': os.getenv('DB_NAME', os.getenv('POSTGRES_DB', 'sofia_db')),
}

def get_data_overview(conn):
    """Get overview of all available data with date ranges"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    overview = {}

    # Funding rounds
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN amount_usd > 0 AND amount_usd < 10000000 THEN 1 END) as seed_angel,
            COUNT(CASE WHEN amount_usd > 0 AND amount_usd < 50000000 THEN 1 END) as early_stage,
            COUNT(CASE WHEN source = 'yc_companies' THEN 1 END) as yc_companies,
            MIN(announced_date) as earliest_date,
            MAX(announced_date) as latest_date,
            SUM(COALESCE(amount_usd, 0)) as total_funding
        FROM sofia.funding_rounds
        WHERE announced_date IS NOT NULL
    """)
    overview['funding'] = cursor.fetchone()

    # GitHub trending
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(DISTINCT language) as languages,
            MIN(collected_at) as earliest_date,
            MAX(collected_at) as latest_date,
            SUM(COALESCE(stars, 0)) as total_stars
        FROM sofia.github_trending
    """)
    overview['github'] = cursor.fetchone()

    # Research papers
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            MIN(published_date) as earliest_date,
            MAX(published_date) as latest_date
        FROM sofia.arxiv_ai_papers
    """)
    overview['papers'] = cursor.fetchone()

    # OpenAlex papers
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            MIN(publication_date) as earliest_date,
            MAX(publication_date) as latest_date
        FROM sofia.openalex_papers
    """)
    overview['openalex'] = cursor.fetchone()

    cursor.close()
    return overview

def get_all_funding_data(conn):
    """Get ALL funding data, sorted by date (oldest first for historical context)"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT
            company_name,
            sector,
            amount_usd,
            valuation_usd,
            round_type,
            announced_date,
            investors,
            country,
            source
        FROM sofia.funding_rounds
        WHERE announced_date IS NOT NULL
        ORDER BY announced_date DESC
    """)

    all_rounds = cursor.fetchall()
    cursor.close()
    return all_rounds

def get_github_tech_stack(conn):
    """Get tech stack from ALL GitHub trending data"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT
            language,
            COUNT(*) as repo_count,
            SUM(COALESCE(stars, 0)) as total_stars,
            MAX(collected_at) as last_seen
        FROM sofia.github_trending
        WHERE language IS NOT NULL
        GROUP BY language
        ORDER BY total_stars DESC
        LIMIT 15
    """)

    tech_stack = cursor.fetchall()
    cursor.close()
    return tech_stack

def get_top_github_repos(conn, limit=20):
    """Get top GitHub repos by stars"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT DISTINCT ON (name, owner)
            name,
            owner,
            description,
            language,
            stars,
            forks,
            topics
        FROM sofia.github_trending
        ORDER BY name, owner, stars DESC
    """)

    repos = cursor.fetchall()
    # Sort by stars and take top N
    repos = sorted(repos, key=lambda x: x['stars'] or 0, reverse=True)[:limit]
    cursor.close()
    return repos

def get_research_papers(conn, limit=20):
    """Get recent research papers"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT
            title,
            authors,
            categories,
            published_date,
            primary_category
        FROM sofia.arxiv_ai_papers
        ORDER BY published_date DESC
        LIMIT %s
    """, (limit,))

    papers = cursor.fetchall()
    cursor.close()
    return papers

def classify_round_stage(amount, round_type):
    """Classify funding round into stage"""
    round_type_lower = (round_type or '').lower()

    if 'pre-seed' in round_type_lower or 'preseed' in round_type_lower:
        return 'Pre-Seed'
    elif 'seed' in round_type_lower:
        return 'Seed'
    elif 'angel' in round_type_lower:
        return 'Angel'
    elif 'series a' in round_type_lower:
        return 'Series A'
    elif 'series b' in round_type_lower:
        return 'Series B'
    elif 'series c' in round_type_lower:
        return 'Series C'
    elif 'series d' in round_type_lower or 'series e' in round_type_lower:
        return 'Series D+'
    elif amount:
        if amount < 1000000:
            return 'Pre-Seed'
        elif amount < 5000000:
            return 'Seed'
        elif amount < 15000000:
            return 'Series A'
        elif amount < 50000000:
            return 'Series B'
        else:
            return 'Series C+'
    else:
        return 'Unknown'

def generate_report(overview, all_rounds, tech_stack, top_repos, papers):
    """Generate intelligent report based on all available data"""
    r = []

    r.append("=" * 80)
    r.append("EARLY-STAGE DEEP DIVE - Sofia Pulse")
    r.append("=" * 80)
    r.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    r.append("")

    # =========================================================================
    # DATA OVERVIEW
    # =========================================================================
    r.append("=" * 80)
    r.append("1. DATA OVERVIEW (Full Historical Range)")
    r.append("=" * 80)
    r.append("")

    funding = overview['funding']
    github = overview['github']
    papers_ov = overview['papers']
    openalex = overview['openalex']

    r.append("FUNDING DATA:")
    r.append("-" * 50)
    if funding and funding['total'] > 0:
        r.append(f"  Total Rounds: {funding['total']:,}")
        r.append(f"  Seed/Angel (<$10M): {funding['seed_angel'] or 0:,}")
        r.append(f"  Early-Stage (<$50M): {funding['early_stage'] or 0:,}")
        r.append(f"  YC Companies: {funding['yc_companies'] or 0:,}")
        total_funding = float(funding['total_funding'] or 0)
        r.append(f"  Total Capital: ${total_funding/1e9:.2f}B")
        if funding['earliest_date']:
            r.append(f"  Date Range: {funding['earliest_date']} to {funding['latest_date']}")
    else:
        r.append("  No funding data available yet")
    r.append("")

    r.append("GITHUB DATA:")
    r.append("-" * 50)
    if github and github['total'] > 0:
        r.append(f"  Trending Repos: {github['total']:,}")
        r.append(f"  Languages: {github['languages'] or 0}")
        total_stars = int(github['total_stars'] or 0)
        r.append(f"  Total Stars: {total_stars:,}")
        if github['earliest_date']:
            r.append(f"  Date Range: {str(github['earliest_date'])[:10]} to {str(github['latest_date'])[:10]}")
    else:
        r.append("  No GitHub data available yet")
    r.append("")

    r.append("RESEARCH PAPERS:")
    r.append("-" * 50)
    total_papers = (papers_ov['total'] if papers_ov else 0) + (openalex['total'] if openalex else 0)
    r.append(f"  ArXiv Papers: {papers_ov['total'] if papers_ov else 0:,}")
    r.append(f"  OpenAlex Papers: {openalex['total'] if openalex else 0:,}")
    r.append(f"  Total: {total_papers:,}")
    r.append("")

    # =========================================================================
    # FUNDING ANALYSIS
    # =========================================================================
    r.append("=" * 80)
    r.append("2. FUNDING ECOSYSTEM ANALYSIS")
    r.append("=" * 80)
    r.append("")

    if not all_rounds:
        r.append("No funding data available yet.")
        r.append("Run collectors to populate: npx tsx scripts/collect.ts funding")
        r.append("")
    else:
        # Classify rounds by stage
        stage_stats = defaultdict(lambda: {'count': 0, 'total': 0, 'companies': []})
        for round_data in all_rounds:
            stage = classify_round_stage(round_data.get('amount_usd'), round_data.get('round_type'))
            stage_stats[stage]['count'] += 1
            if round_data.get('amount_usd'):
                stage_stats[stage]['total'] += float(round_data['amount_usd'])
            stage_stats[stage]['companies'].append(round_data['company_name'])

        r.append("FUNDING BY STAGE:")
        r.append("-" * 70)
        r.append(f"{'Stage':<15} {'Deals':>8} {'Total Funding':>18} {'Avg Deal':>15}")
        r.append("-" * 70)

        stage_order = ['Pre-Seed', 'Seed', 'Angel', 'Series A', 'Series B', 'Series C', 'Series C+', 'Series D+', 'Unknown']
        for stage in stage_order:
            if stage in stage_stats:
                data = stage_stats[stage]
                total = data['total']
                avg = total / data['count'] if data['count'] > 0 else 0
                total_str = f"${total/1e6:.1f}M" if total > 0 else "N/A"
                avg_str = f"${avg/1e6:.1f}M" if avg > 0 else "N/A"
                r.append(f"{stage:<15} {data['count']:>8} {total_str:>18} {avg_str:>15}")
        r.append("")

        # Early-stage focus
        early_rounds = [rd for rd in all_rounds if classify_round_stage(rd.get('amount_usd'), rd.get('round_type')) in ['Pre-Seed', 'Seed', 'Angel', 'Series A']]

        if early_rounds:
            r.append(f"EARLY-STAGE FOCUS ({len(early_rounds)} deals):")
            r.append("-" * 50)

            # By sector
            sector_stats = defaultdict(lambda: {'count': 0, 'total': 0})
            for rd in early_rounds:
                sector = rd.get('sector') or 'Unknown'
                sector_stats[sector]['count'] += 1
                if rd.get('amount_usd'):
                    sector_stats[sector]['total'] += float(rd['amount_usd'])

            r.append("\nTop Sectors (Early-Stage):")
            for sector, data in sorted(sector_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:10]:
                total_str = f"${data['total']/1e6:.1f}M" if data['total'] > 0 else "undisclosed"
                r.append(f"  {sector:<30} {data['count']:>4} deals ({total_str})")
            r.append("")

            # By country
            country_stats = defaultdict(lambda: {'count': 0, 'total': 0})
            for rd in early_rounds:
                country = rd.get('country') or 'Unknown'
                country_stats[country]['count'] += 1
                if rd.get('amount_usd'):
                    country_stats[country]['total'] += float(rd['amount_usd'])

            r.append("Top Countries (Early-Stage):")
            for country, data in sorted(country_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:10]:
                total_str = f"${data['total']/1e6:.1f}M" if data['total'] > 0 else "undisclosed"
                r.append(f"  {country:<25} {data['count']:>4} deals ({total_str})")
            r.append("")

        # Top recent deals
        r.append("RECENT NOTABLE DEALS:")
        r.append("-" * 70)
        for idx, rd in enumerate(all_rounds[:15], 1):
            company = rd['company_name']
            sector = rd.get('sector') or 'N/A'
            country = rd.get('country') or 'Unknown'
            date = rd.get('announced_date', 'N/A')
            round_type = rd.get('round_type') or 'N/A'

            if rd.get('amount_usd') and rd['amount_usd'] > 0:
                amount = float(rd['amount_usd']) / 1e6
                r.append(f"{idx:2d}. {company[:30]:<30} ${amount:>8.1f}M | {round_type} | {sector[:15]} | {country}")
            else:
                r.append(f"{idx:2d}. {company[:30]:<30} {'undisclosed':>10} | {round_type} | {sector[:15]} | {country}")
        r.append("")

    # =========================================================================
    # TECH STACK SIGNALS
    # =========================================================================
    r.append("=" * 80)
    r.append("3. TECH STACK SIGNALS (GitHub Trending)")
    r.append("=" * 80)
    r.append("")

    if tech_stack:
        r.append("LANGUAGES BY POPULARITY:")
        r.append("-" * 60)
        r.append(f"{'Language':<20} {'Repos':>10} {'Total Stars':>15}")
        r.append("-" * 60)
        for tech in tech_stack:
            stars = int(tech['total_stars'] or 0)
            r.append(f"{tech['language']:<20} {tech['repo_count']:>10} {stars:>15,}")
        r.append("")

        # Top repos
        if top_repos:
            r.append("TOP TRENDING REPOSITORIES:")
            r.append("-" * 70)
            for idx, repo in enumerate(top_repos[:10], 1):
                name = f"{repo['owner']}/{repo['name']}"
                stars = repo['stars'] or 0
                lang = repo.get('language') or 'N/A'
                desc = (repo.get('description') or '')[:40]
                r.append(f"{idx:2d}. {name[:35]:<35} {stars:>10,} stars | {lang}")
                if desc:
                    r.append(f"    {desc}...")
            r.append("")
    else:
        r.append("No GitHub data available yet.")
        r.append("Run collectors to populate: npx tsx scripts/collect.ts github")
        r.append("")

    # =========================================================================
    # RESEARCH PIPELINE
    # =========================================================================
    r.append("=" * 80)
    r.append("4. RESEARCH PIPELINE (ArXiv)")
    r.append("=" * 80)
    r.append("")

    if papers:
        r.append("RECENT AI/ML RESEARCH:")
        r.append("-" * 70)
        for idx, paper in enumerate(papers[:10], 1):
            title = (paper['title'] or '')[:60]
            date = paper.get('published_date', 'N/A')
            category = paper.get('primary_category') or paper.get('categories') or 'N/A'
            if isinstance(category, list):
                category = category[0] if category else 'N/A'
            r.append(f"{idx:2d}. {title}...")
            r.append(f"    Category: {category} | Date: {date}")
        r.append("")

        # Category distribution
        category_stats = defaultdict(int)
        for paper in papers:
            cat = paper.get('primary_category') or 'Unknown'
            category_stats[cat] += 1

        r.append("RESEARCH CATEGORIES:")
        r.append("-" * 40)
        for cat, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            r.append(f"  {cat:<25} {count:>5} papers")
        r.append("")
    else:
        r.append("No research paper data available yet.")
        r.append("Run collectors to populate: npx tsx scripts/collect.ts arxiv")
        r.append("")

    # =========================================================================
    # INSIGHTS & OPPORTUNITIES
    # =========================================================================
    r.append("=" * 80)
    r.append("5. STRATEGIC INSIGHTS")
    r.append("=" * 80)
    r.append("")

    if all_rounds:
        # Find emerging patterns
        early_stage = [rd for rd in all_rounds if classify_round_stage(rd.get('amount_usd'), rd.get('round_type')) in ['Pre-Seed', 'Seed', 'Angel']]

        if early_stage:
            # Sectors with small # of deals but validation
            sector_counts = defaultdict(int)
            for rd in early_stage:
                sector_counts[rd.get('sector') or 'Unknown'] += 1

            emerging = [(s, c) for s, c in sector_counts.items() if 2 <= c <= 5 and s != 'Unknown']
            if emerging:
                r.append("EMERGING SECTORS (2-5 early-stage deals = market validation):")
                r.append("-" * 50)
                for sector, count in sorted(emerging, key=lambda x: x[1], reverse=True)[:5]:
                    r.append(f"  {sector}: {count} deals")
                    r.append(f"    -> Early market, room for new entrants")
                r.append("")

        # Geographic opportunities
        country_counts = defaultdict(int)
        for rd in all_rounds:
            country_counts[rd.get('country') or 'Unknown'] += 1

        non_us = [(c, cnt) for c, cnt in country_counts.items() if c not in ['USA', 'United States', 'Unknown'] and cnt >= 2]
        if non_us:
            r.append("EMERGING GEOGRAPHIC HUBS (outside USA):")
            r.append("-" * 50)
            for country, count in sorted(non_us, key=lambda x: x[1], reverse=True)[:8]:
                r.append(f"  {country}: {count} deals")
            r.append("")

    # Tech stack insights
    if tech_stack:
        r.append("TECH STACK INSIGHTS:")
        r.append("-" * 50)
        top_langs = [t['language'] for t in tech_stack[:5]]
        r.append(f"  Dominant: {', '.join(top_langs)}")
        r.append("  -> Skills in demand for startups")
        r.append("")

    r.append("FOR FOUNDERS:")
    r.append("-" * 50)
    r.append("  - Check emerging sectors for less competition")
    r.append("  - Geographic hubs outside USA may offer advantages")
    r.append("  - Tech stack: align with trending technologies")
    r.append("")

    r.append("FOR INVESTORS:")
    r.append("-" * 50)
    r.append("  - Early-stage sectors with 2-5 deals = validated but not crowded")
    r.append("  - Watch research pipeline for next wave of startups")
    r.append("  - Geographic diversification opportunities")
    r.append("")

    r.append("FOR TALENT:")
    r.append("-" * 50)
    r.append("  - Learn trending languages/frameworks from GitHub data")
    r.append("  - Follow funded sectors for job opportunities")
    r.append("  - Research papers indicate future skill demands")
    r.append("")

    r.append("=" * 80)
    r.append("Report complete.")
    r.append("=" * 80)

    return "\n".join(r)

def main():
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("Connected.")
    print()

    print("Getting data overview...")
    overview = get_data_overview(conn)

    print("Fetching all funding data...")
    all_rounds = get_all_funding_data(conn)
    print(f"  Found {len(all_rounds)} funding rounds")

    print("Analyzing tech stack...")
    tech_stack = get_github_tech_stack(conn)
    print(f"  Found {len(tech_stack)} languages")

    print("Getting top GitHub repos...")
    top_repos = get_top_github_repos(conn)

    print("Fetching research papers...")
    papers = get_research_papers(conn)
    print(f"  Found {len(papers)} papers")

    print()
    print("Generating report...")
    report = generate_report(overview, all_rounds, tech_stack, top_repos, papers)

    # Print with safe encoding for Windows terminals
    try:
        print(report)
    except UnicodeEncodeError:
        print(report.encode('ascii', errors='replace').decode('ascii'))

    # Save
    output_file = 'analytics/early-stage-latest.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nSaved to: {output_file}")

    conn.close()

if __name__ == '__main__':
    main()
