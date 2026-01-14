#!/usr/bin/env python3
"""
================================================================================
ENTITY RESOLUTION & INTELLIGENCE CONNECTIONS
================================================================================
Connects research, open source, and funding data to find actionable patterns:

1. RESEARCH → FUNDING PIPELINE
   - Which research topics are attracting VC money?
   - Lag analysis: papers 6-12 months ago → funding now

2. TECHNOLOGY ADOPTION SIGNALS
   - GitHub trending tech → Companies getting funded
   - Open source momentum → Commercial adoption

3. GEOGRAPHIC INTELLIGENCE
   - Research hubs → Startup ecosystems
   - Where does research become companies?

4. SECTOR CONVERGENCE
   - Cross-domain connections (AI + Healthcare, etc.)
   - Emerging hybrid sectors

Output: Actionable intelligence for investors, founders, and talent
================================================================================
"""

import os
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
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

# Topic keywords for matching research to funding
TOPIC_KEYWORDS = {
    'AI/ML': ['machine learning', 'deep learning', 'neural network', 'transformer', 'llm',
              'large language model', 'gpt', 'diffusion', 'generative ai', 'reinforcement learning',
              'computer vision', 'nlp', 'natural language', 'artificial intelligence'],
    'Healthcare/Biotech': ['drug discovery', 'protein', 'genomic', 'clinical', 'medical',
                           'healthcare', 'biotech', 'pharma', 'therapeutic', 'diagnosis',
                           'patient', 'health', 'disease', 'cancer', 'treatment'],
    'Fintech': ['fintech', 'banking', 'payment', 'crypto', 'blockchain', 'defi',
                'trading', 'insurance', 'lending', 'financial'],
    'Cybersecurity': ['security', 'cyber', 'encryption', 'privacy', 'authentication',
                      'malware', 'threat', 'vulnerability', 'zero trust'],
    'Climate/Energy': ['climate', 'carbon', 'renewable', 'solar', 'battery', 'ev',
                       'sustainability', 'green', 'clean energy', 'emissions'],
    'Robotics/Hardware': ['robot', 'autonomous', 'sensor', 'hardware', 'chip', 'semiconductor',
                          'drone', 'manufacturing', 'iot', 'edge computing'],
    'Developer Tools': ['developer', 'devops', 'api', 'infrastructure', 'cloud', 'kubernetes',
                        'container', 'ci/cd', 'testing', 'monitoring', 'observability'],
    'Data/Analytics': ['data', 'analytics', 'warehouse', 'etl', 'visualization', 'bi',
                       'database', 'streaming', 'real-time', 'pipeline'],
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def classify_topic(text):
    """Classify text into topics based on keywords"""
    if not text:
        return []
    text_lower = text.lower()
    matches = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                matches.append(topic)
                break
    return matches

def analyze_research_to_funding(conn):
    """Find connections between research papers and funded companies by topic"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    results = {
        'topic_connections': [],
        'hot_research_topics': [],
        'funded_without_research': [],
        'research_without_funding': [],
    }

    # Get papers from last 12 months with their topics
    cursor.execute("""
        SELECT title, abstract, categories, published_date
        FROM sofia.arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '12 months'
        ORDER BY published_date DESC
        LIMIT 500
    """)
    papers = cursor.fetchall()

    # Get OpenAlex papers too
    cursor.execute("""
        SELECT title, abstract, concepts, publication_date
        FROM sofia.openalex_papers
        WHERE publication_date >= CURRENT_DATE - INTERVAL '12 months'
        ORDER BY publication_date DESC
        LIMIT 500
    """)
    openalex_papers = cursor.fetchall()

    # Get funding from last 6 months
    cursor.execute("""
        SELECT company_name, sector, amount_usd, round_type, announced_date, country
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '6 months'
        ORDER BY announced_date DESC
    """)
    funding = cursor.fetchall()

    # Classify papers by topic
    paper_topics = defaultdict(list)
    for p in papers:
        text = f"{p.get('title', '')} {p.get('abstract', '')} {p.get('categories', '')}"
        topics = classify_topic(text)
        for t in topics:
            paper_topics[t].append({
                'title': p['title'][:80] if p.get('title') else 'N/A',
                'date': p.get('published_date'),
                'source': 'ArXiv'
            })

    for p in openalex_papers:
        text = f"{p.get('title', '')} {p.get('abstract', '')} {str(p.get('concepts', ''))}"
        topics = classify_topic(text)
        for t in topics:
            paper_topics[t].append({
                'title': p['title'][:80] if p.get('title') else 'N/A',
                'date': p.get('publication_date'),
                'source': 'OpenAlex'
            })

    # Classify funding by topic
    funding_topics = defaultdict(list)
    for f in funding:
        text = f"{f.get('company_name', '')} {f.get('sector', '')}"
        topics = classify_topic(text)
        # Also use sector directly
        sector = f.get('sector', '')
        if sector:
            for topic in TOPIC_KEYWORDS.keys():
                if topic.lower() in sector.lower() or sector.lower() in topic.lower():
                    topics.append(topic)

        topics = list(set(topics))  # dedupe
        for t in topics:
            funding_topics[t].append({
                'company': f['company_name'],
                'amount': f.get('amount_usd', 0),
                'round': f.get('round_type', 'N/A'),
                'date': f.get('announced_date'),
                'country': f.get('country', 'Unknown')
            })

    # Find topic connections
    for topic in TOPIC_KEYWORDS.keys():
        paper_count = len(paper_topics.get(topic, []))
        funding_list = funding_topics.get(topic, [])
        funding_count = len(funding_list)
        total_funding = sum(f['amount'] or 0 for f in funding_list)

        if paper_count > 0 or funding_count > 0:
            results['topic_connections'].append({
                'topic': topic,
                'papers': paper_count,
                'funding_deals': funding_count,
                'total_funding': total_funding,
                'sample_papers': paper_topics.get(topic, [])[:3],
                'sample_companies': funding_list[:5],
                'pipeline_score': min(100, (paper_count * 2) + (funding_count * 10)),
            })

    # Sort by pipeline activity
    results['topic_connections'] = sorted(
        results['topic_connections'],
        key=lambda x: x['pipeline_score'],
        reverse=True
    )

    cursor.close()
    return results

def analyze_github_to_funding(conn):
    """Find connections between GitHub trends and funding"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    results = {
        'tech_to_funding': [],
        'hot_repos_in_funded_sectors': [],
    }

    # Get trending repos with their tech
    cursor.execute("""
        SELECT name, owner, description, language, stars, forks, topics, collected_at
        FROM sofia.github_trending
        WHERE collected_at >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY stars DESC
        LIMIT 200
    """)
    repos = cursor.fetchall()

    # Get recent funding
    cursor.execute("""
        SELECT company_name, sector, amount_usd, round_type
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '6 months'
          AND amount_usd > 0
    """)
    funding = cursor.fetchall()

    # Analyze by language/tech
    language_stats = defaultdict(lambda: {'repos': 0, 'total_stars': 0, 'sample_repos': []})
    for r in repos:
        lang = r.get('language') or 'Unknown'
        language_stats[lang]['repos'] += 1
        language_stats[lang]['total_stars'] += r.get('stars', 0) or 0
        if len(language_stats[lang]['sample_repos']) < 3:
            language_stats[lang]['sample_repos'].append({
                'name': f"{r.get('owner', '')}/{r.get('name', '')}",
                'stars': r.get('stars', 0),
                'description': (r.get('description') or '')[:60]
            })

    # Find repos in funded sectors
    for r in repos:
        desc = f"{r.get('description', '')} {str(r.get('topics', ''))}"
        topics = classify_topic(desc)
        if topics:
            results['hot_repos_in_funded_sectors'].append({
                'repo': f"{r.get('owner', '')}/{r.get('name', '')}",
                'stars': r.get('stars', 0),
                'topics': topics,
                'description': (r.get('description') or '')[:80]
            })

    # Sort by stars
    results['hot_repos_in_funded_sectors'] = sorted(
        results['hot_repos_in_funded_sectors'],
        key=lambda x: x['stars'],
        reverse=True
    )[:20]

    # Tech to funding mapping
    for lang, stats in sorted(language_stats.items(), key=lambda x: x[1]['total_stars'], reverse=True)[:10]:
        results['tech_to_funding'].append({
            'language': lang,
            'repos': stats['repos'],
            'total_stars': stats['total_stars'],
            'sample_repos': stats['sample_repos']
        })

    cursor.close()
    return results

def analyze_geographic_intelligence(conn):
    """Find geographic patterns in research and funding"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    results = {
        'funding_by_country': [],
        'sector_by_country': defaultdict(lambda: defaultdict(int)),
    }

    # Funding by country
    cursor.execute("""
        SELECT country,
               COUNT(*) as deals,
               SUM(COALESCE(amount_usd, 0)) as total_funding,
               COUNT(DISTINCT sector) as sectors
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '12 months'
          AND country IS NOT NULL
        GROUP BY country
        ORDER BY total_funding DESC
        LIMIT 15
    """)
    country_funding = cursor.fetchall()

    for cf in country_funding:
        results['funding_by_country'].append({
            'country': cf['country'],
            'deals': cf['deals'],
            'total_funding': cf['total_funding'] or 0,
            'sectors': cf['sectors']
        })

    # Sector by country
    cursor.execute("""
        SELECT country, sector, COUNT(*) as deals, SUM(COALESCE(amount_usd, 0)) as amount
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '12 months'
          AND country IS NOT NULL
          AND sector IS NOT NULL
        GROUP BY country, sector
        ORDER BY amount DESC
        LIMIT 50
    """)
    sector_country = cursor.fetchall()

    for sc in sector_country:
        results['sector_by_country'][sc['country']][sc['sector']] = {
            'deals': sc['deals'],
            'amount': sc['amount'] or 0
        }

    cursor.close()
    return results

def analyze_temporal_patterns(conn):
    """Find temporal patterns - research leading to funding"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    results = {
        'monthly_trends': [],
        'lag_analysis': [],
    }

    # Papers by month
    cursor.execute("""
        SELECT DATE_TRUNC('month', published_date) as month, COUNT(*) as papers
        FROM arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY DATE_TRUNC('month', published_date)
        ORDER BY month
    """)
    paper_months = {str(r['month'].date())[:7]: r['papers'] for r in cursor.fetchall()}

    # Funding by month
    cursor.execute("""
        SELECT DATE_TRUNC('month', announced_date) as month,
               COUNT(*) as deals,
               SUM(COALESCE(amount_usd, 0)) as amount
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY DATE_TRUNC('month', announced_date)
        ORDER BY month
    """)
    funding_months = {str(r['month'].date())[:7]: {'deals': r['deals'], 'amount': r['amount'] or 0}
                      for r in cursor.fetchall()}

    # Combine
    all_months = sorted(set(list(paper_months.keys()) + list(funding_months.keys())))
    for m in all_months:
        results['monthly_trends'].append({
            'month': m,
            'papers': paper_months.get(m, 0),
            'deals': funding_months.get(m, {}).get('deals', 0),
            'funding': funding_months.get(m, {}).get('amount', 0),
        })

    cursor.close()
    return results

def analyze_jobs_to_funding(conn):
    """Find connections between job market and funding"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    results = {
        'skills_in_demand': [],
        'hiring_sectors': [],
    }

    # Top skills from jobs
    cursor.execute("""
        SELECT skill, COUNT(*) as job_count
        FROM (
            SELECT UNNEST(skills) as skill
            FROM sofia.jobs
            WHERE posted_date >= CURRENT_DATE - INTERVAL '90 days'
              AND skills IS NOT NULL
        ) s
        GROUP BY skill
        ORDER BY job_count DESC
        LIMIT 20
    """)
    skills = cursor.fetchall()

    for s in skills:
        results['skills_in_demand'].append({
            'skill': s['skill'],
            'job_count': s['job_count']
        })

    # Jobs by sector
    cursor.execute("""
        SELECT sector, COUNT(*) as jobs
        FROM sofia.jobs
        WHERE posted_date >= CURRENT_DATE - INTERVAL '90 days'
          AND sector IS NOT NULL
        GROUP BY sector
        ORDER BY jobs DESC
        LIMIT 10
    """)
    sectors = cursor.fetchall()

    for s in sectors:
        results['hiring_sectors'].append({
            'sector': s['sector'],
            'jobs': s['jobs']
        })

    cursor.close()
    return results

def generate_report(research_funding, github_funding, geo_intel, temporal, jobs_funding):
    """Generate the intelligence report"""
    r = []

    r.append("=" * 80)
    r.append("ENTITY RESOLUTION & INTELLIGENCE CONNECTIONS")
    r.append("=" * 80)
    r.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    r.append("")
    r.append("Cross-referencing: Papers, GitHub, Funding, Jobs")
    r.append("Time window: Research (12 months) -> Funding (6 months) -> Jobs (90 days)")
    r.append("")

    # =========================================================================
    # 1. RESEARCH → FUNDING PIPELINE
    # =========================================================================
    r.append("=" * 80)
    r.append("1. RESEARCH -> FUNDING PIPELINE (Topic Analysis)")
    r.append("=" * 80)
    r.append("")
    r.append("Which research topics are attracting VC money?")
    r.append("")

    r.append(f"{'Topic':<25} {'Papers':>8} {'Deals':>8} {'Funding':>15} {'Score':>8}")
    r.append("-" * 70)

    for tc in research_funding['topic_connections'][:10]:
        funding_val = float(tc['total_funding'] or 0)
        funding_str = f"${funding_val/1e6:.1f}M" if funding_val > 0 else "N/A"
        r.append(f"{tc['topic']:<25} {tc['papers']:>8} {tc['funding_deals']:>8} {funding_str:>15} {tc['pipeline_score']:>8}")

    r.append("")

    # Show top connections with examples
    r.append("TOP RESEARCH-TO-FUNDING CONNECTIONS:")
    r.append("-" * 70)

    for tc in research_funding['topic_connections'][:3]:
        if tc['papers'] > 0 and tc['funding_deals'] > 0:
            r.append(f"\n  {tc['topic']}:")
            r.append(f"  Research Activity: {tc['papers']} papers in last 12 months")
            if tc['sample_papers']:
                r.append("  Sample Papers:")
                for p in tc['sample_papers'][:2]:
                    r.append(f"    - {p['title'][:70]}...")

            total_fund_val = float(tc['total_funding'] or 0)
            r.append(f"  Funding Activity: {tc['funding_deals']} deals, ${total_fund_val/1e6:.1f}M total")
            if tc['sample_companies']:
                r.append("  Funded Companies:")
                for c in tc['sample_companies'][:3]:
                    amt_val = float(c['amount'] or 0)
                    amt = f"${amt_val/1e6:.1f}M" if amt_val > 0 else "Undisclosed"
                    r.append(f"    - {c['company']} ({c['round']}, {amt})")

    r.append("")

    # =========================================================================
    # 2. GITHUB → FUNDING SIGNALS
    # =========================================================================
    r.append("=" * 80)
    r.append("2. GITHUB TRENDS -> FUNDING SIGNALS")
    r.append("=" * 80)
    r.append("")
    r.append("Open source momentum in funded sectors:")
    r.append("")

    if github_funding['hot_repos_in_funded_sectors']:
        r.append(f"{'Repository':<40} {'Stars':>10} {'Sectors':<30}")
        r.append("-" * 80)
        for repo in github_funding['hot_repos_in_funded_sectors'][:10]:
            topics = ', '.join(repo['topics'][:2])
            r.append(f"{repo['repo'][:38]:<40} {repo['stars']:>10,} {topics:<30}")
        r.append("")

    r.append("TECHNOLOGY STACK TRENDS (by GitHub stars):")
    r.append("-" * 50)
    for tech in github_funding['tech_to_funding'][:8]:
        r.append(f"  {tech['language']:<15} {tech['repos']:>5} repos, {tech['total_stars']:>10,} total stars")
    r.append("")

    # =========================================================================
    # 3. GEOGRAPHIC INTELLIGENCE
    # =========================================================================
    r.append("=" * 80)
    r.append("3. GEOGRAPHIC INTELLIGENCE")
    r.append("=" * 80)
    r.append("")
    r.append("Where is capital flowing?")
    r.append("")

    r.append(f"{'Country':<25} {'Deals':>8} {'Total Funding':>18} {'Sectors':>10}")
    r.append("-" * 65)
    for cf in geo_intel['funding_by_country'][:10]:
        funding_val = float(cf['total_funding'] or 0)
        funding_str = f"${funding_val/1e6:.1f}M" if funding_val > 0 else "N/A"
        r.append(f"{cf['country']:<25} {cf['deals']:>8} {funding_str:>18} {cf['sectors']:>10}")
    r.append("")

    # Top sector by country
    r.append("TOP SECTOR BY COUNTRY:")
    r.append("-" * 50)
    shown_countries = set()
    for country, sectors in geo_intel['sector_by_country'].items():
        if country in shown_countries or len(shown_countries) >= 8:
            continue
        if sectors:
            top_sector = max(sectors.items(), key=lambda x: float(x[1]['amount'] or 0))
            amt_val = float(top_sector[1]['amount'] or 0)
            amt = f"${amt_val/1e6:.1f}M" if amt_val > 0 else "N/A"
            r.append(f"  {country}: {top_sector[0]} ({top_sector[1]['deals']} deals, {amt})")
            shown_countries.add(country)
    r.append("")

    # =========================================================================
    # 4. TEMPORAL PATTERNS
    # =========================================================================
    r.append("=" * 80)
    r.append("4. TEMPORAL PATTERNS (Research -> Funding Lag)")
    r.append("=" * 80)
    r.append("")
    r.append("Monthly activity trends:")
    r.append("")

    r.append(f"{'Month':<12} {'Papers':>10} {'Deals':>10} {'Funding':>15}")
    r.append("-" * 50)
    for mt in temporal['monthly_trends'][-6:]:  # Last 6 months
        funding_val = float(mt['funding'] or 0)
        funding_str = f"${funding_val/1e6:.1f}M" if funding_val > 0 else "N/A"
        r.append(f"{mt['month']:<12} {mt['papers']:>10} {mt['deals']:>10} {funding_str:>15}")
    r.append("")

    # =========================================================================
    # 5. JOBS MARKET SIGNALS
    # =========================================================================
    r.append("=" * 80)
    r.append("5. JOBS MARKET SIGNALS")
    r.append("=" * 80)
    r.append("")

    if jobs_funding['skills_in_demand']:
        r.append("TOP SKILLS IN DEMAND (last 90 days):")
        r.append("-" * 40)
        for i, s in enumerate(jobs_funding['skills_in_demand'][:10], 1):
            r.append(f"  {i:2d}. {s['skill']:<25} {s['job_count']:>6} jobs")
        r.append("")

    if jobs_funding['hiring_sectors']:
        r.append("SECTORS HIRING MOST:")
        r.append("-" * 40)
        for s in jobs_funding['hiring_sectors'][:8]:
            r.append(f"  {s['sector']:<30} {s['jobs']:>6} jobs")
        r.append("")

    # =========================================================================
    # ACTIONABLE INSIGHTS
    # =========================================================================
    r.append("=" * 80)
    r.append("ACTIONABLE INSIGHTS")
    r.append("=" * 80)
    r.append("")

    # Find hottest topic (research + funding)
    if research_funding['topic_connections']:
        hottest = research_funding['topic_connections'][0]
        funding_val = float(hottest['total_funding'] or 0)
        r.append(f"HOTTEST SECTOR: {hottest['topic']}")
        r.append(f"  - {hottest['papers']} research papers in 12 months")
        r.append(f"  - {hottest['funding_deals']} funding deals in 6 months")
        r.append(f"  - ${funding_val/1e6:.1f}M total funding")
        r.append("  -> Strong research-to-commercialization pipeline")
        r.append("")

    # Research without funding (opportunity)
    research_only = [tc for tc in research_funding['topic_connections']
                     if tc['papers'] > 10 and tc['funding_deals'] < 3]
    if research_only:
        r.append("UNTAPPED RESEARCH (high papers, low funding):")
        for topic in research_only[:3]:
            r.append(f"  - {topic['topic']}: {topic['papers']} papers but only {topic['funding_deals']} deals")
        r.append("  -> Potential early-stage investment opportunities")
        r.append("")

    # Funding without research (market validation)
    funding_only = [tc for tc in research_funding['topic_connections']
                    if tc['funding_deals'] > 3 and tc['papers'] < 5]
    if funding_only:
        r.append("MARKET-VALIDATED (funding ahead of research):")
        for topic in funding_only[:3]:
            r.append(f"  - {topic['topic']}: {topic['funding_deals']} deals but only {topic['papers']} papers")
        r.append("  -> Market demand validated, research catching up")
        r.append("")

    r.append("FOR INVESTORS:")
    r.append("  - Follow topics with high research activity (6-12 month funding lag)")
    r.append("  - Geographic focus: see top countries by sector above")
    r.append("")

    r.append("FOR FOUNDERS:")
    r.append("  - Build in hot sectors with proven research pipeline")
    r.append("  - Check GitHub trends for validated technologies")
    r.append("")

    r.append("FOR TALENT:")
    r.append("  - Skills in demand: see jobs market signals above")
    r.append("  - Follow funded sectors for career growth")
    r.append("")

    r.append("=" * 80)
    r.append("Report complete.")
    r.append("=" * 80)

    return "\n".join(r)

def main():
    print("Connecting to database...")
    conn = get_connection()
    print("Connected.")
    print()

    print("Analyzing Research -> Funding pipeline...")
    research_funding = analyze_research_to_funding(conn)

    print("Analyzing GitHub -> Funding signals...")
    github_funding = analyze_github_to_funding(conn)

    print("Analyzing Geographic intelligence...")
    geo_intel = analyze_geographic_intelligence(conn)

    print("Analyzing Temporal patterns...")
    temporal = analyze_temporal_patterns(conn)

    print("Analyzing Jobs market...")
    jobs_funding = analyze_jobs_to_funding(conn)

    print()
    print("Generating report...")
    report = generate_report(research_funding, github_funding, geo_intel, temporal, jobs_funding)

    print(report)

    # Save
    output_path = 'analytics/entity-resolution-latest.txt'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nSaved to: {output_path}")

    conn.close()

if __name__ == '__main__':
    main()
