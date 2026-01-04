#!/usr/bin/env python3
"""
SOFIA PULSE - CAPITAL FLOW PREDICTOR
Prevê setores onde capital vai entrar ANTES dos VCs
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or 'localhost',
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5432'),
    'user': os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME') or 'sofia_db',
}

def analyze_capital_flow(conn):
    """
    Cruza 9 fontes para prever onde capital vai entrar:
    1. Funding - Tendências atuais
    2. ArXiv Papers - Research acadêmico
    3. GitHub Trending - Atividade técnica REAL
    4. GDELT - Geopolítica (regulações, incentivos)
    5. HackerNews - Community discussions
    6. StackOverflow - Developer interest
    7. NPM - JavaScript ecosystem adoption
    8. PyPI - Python ecosystem adoption
    9. OpenAlex - High-citation research
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 1. Funding atual por setor
    cur.execute("""
        SELECT
            sector,
            COUNT(*) as deal_count,
            SUM(amount_usd) as total_usd,
            AVG(amount_usd) as avg_usd
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '180 days'
        AND amount_usd / 1000000.0 IS NOT NULL
        GROUP BY sector
        ORDER BY total_usd DESC
        LIMIT 20
    """)
    funding_by_sector = {row['sector']: {
        'deals': row['deal_count'],
        'total': float(row['total_usd']) / 1000000.0 if row['total_usd'] else 0,
        'avg': float(row['avg_usd']) / 1000000.0 if row['avg_usd'] else 0
    } for row in cur.fetchall()}

    # 2. Papers por área (proxy para setores)
    cur.execute("""
        SELECT
            UNNEST(keywords) as topic,
            COUNT(*) as paper_count
        FROM sofia.arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY topic
        HAVING COUNT(*) >= 5
        ORDER BY paper_count DESC
        LIMIT 30
    """)
    research_trends = {row['topic']: row['paper_count'] for row in cur.fetchall()}

    # 3. GDELT eventos (geopolitical attention)
    cur.execute("""
        SELECT
            COUNT(*) as event_count
        FROM sofia.gdelt_events
        WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
    """)
    gdelt_activity = cur.fetchone()['event_count']

    # 4. GitHub Trending (real technical activity by sector)
    cur.execute("""
        SELECT
            UNNEST(topics) as tech,
            SUM(stars) as total_stars,
            COUNT(*) as repos
        FROM sofia.github_trending
        WHERE collected_at >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY tech
        ORDER BY total_stars DESC
        LIMIT 100
    """)
    github_by_tech = {row['tech']: {
        'stars': row['total_stars'],
        'repos': row['repos']
    } for row in cur.fetchall()}

    # 5. HackerNews discussions by sector keywords
    cur.execute("""
        SELECT
            title,
            points,
            url
        FROM sofia.hackernews_stories
        WHERE collected_at >= CURRENT_DATE - INTERVAL '30 days'
            AND points >= 50
        ORDER BY points DESC
        LIMIT 200
    """)
    hn_stories = cur.fetchall()

    # 6. StackOverflow trending tags
    cur.execute("""
        SELECT
            tag_name,
            SUM(count) as total_questions
        FROM sofia.stackoverflow_trends
        WHERE collected_at >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY tag_name
        ORDER BY total_questions DESC NULLS LAST
        LIMIT 200
    """)
    stackoverflow_by_tag = {row['tag_name']: row['total_questions'] for row in cur.fetchall()}

    # 7. NPM ecosystem adoption (JavaScript)
    cur.execute("""
        SELECT
            UNNEST(keywords) as keyword,
            SUM(downloads_week) as total_downloads
        FROM sofia.npm_stats
        WHERE collected_at >= CURRENT_DATE - INTERVAL '30 days'
            AND keywords IS NOT NULL
        GROUP BY keyword
        ORDER BY total_downloads DESC NULLS LAST
        LIMIT 200
    """)
    npm_by_keyword = {row['keyword']: row['total_downloads'] for row in cur.fetchall() if row['total_downloads']}

    # 8. PyPI ecosystem adoption (Python)
    cur.execute("""
        SELECT
            package_name,
            SUM(downloads_month) as total_downloads
        FROM sofia.pypi_stats
        WHERE collected_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY package_name
        ORDER BY total_downloads DESC NULLS LAST
        LIMIT 200
    """)
    pypi_by_package = {row['package_name']: row['total_downloads'] for row in cur.fetchall() if row['total_downloads']}

    # 9. OpenAlex high-citation research
    cur.execute("""
        SELECT
            title,
            cited_by_count,
            UNNEST(concepts) as concept
        FROM sofia.openalex_papers
        WHERE cited_by_count > 100
            AND concepts IS NOT NULL
        ORDER BY cited_by_count DESC
        LIMIT 100
    """)
    openalex_concepts = defaultdict(int)
    for row in cur.fetchall():
        if row['concept']:
            openalex_concepts[row['concept']] += row['cited_by_count']

    # Map setores para análise preditiva
    sector_predictions = []

    # Setores críticos para monitorar
    target_sectors = [
        'Quantum Computing', 'AI/ML', 'Cybersecurity', 'Climate Tech',
        'Biotech', 'Space Tech', 'Semiconductors', 'Renewable Energy',
        'EdTech', 'HealthTech', 'FinTech', 'Robotics'
    ]

    for sector in target_sectors:
        score = 0
        signals = []
        sector_lower = sector.lower().replace(' ', '').replace('/', '')

        # 1. Funding signal (lowered threshold: $100M → $10M)
        if sector in funding_by_sector:
            funding_data = funding_by_sector[sector]
            if funding_data['total'] > 10:  # >$10M (more realistic)
                score += 25
                signals.append(f"Current funding: ${funding_data['total']:.1f}M ({funding_data['deals']} deals)")

        # 2. ArXiv Research signal
        research_count = 0
        for topic in research_trends:
            topic_clean = topic.lower().replace(' ', '').replace('/', '')
            if sector_lower in topic_clean or topic_clean in sector_lower:
                research_count += research_trends[topic]

        if research_count >= 5:  # Lowered from 10
            score += 20
            signals.append(f"ArXiv papers: {research_count} publications")

        # 3. GitHub REAL signal (technical momentum)
        github_stars = 0
        github_repos = 0
        for tech in github_by_tech:
            tech_clean = tech.lower().replace(' ', '').replace('/', '')
            if sector_lower in tech_clean or tech_clean in sector_lower:
                github_stars += github_by_tech[tech]['stars']
                github_repos += github_by_tech[tech]['repos']

        if github_stars > 1000:
            score += 20
            signals.append(f"GitHub: {github_stars:,} stars ({github_repos} repos)")

        # 4. HackerNews signal (community buzz)
        hn_score = 0
        for story in hn_stories:
            title_clean = story['title'].lower().replace(' ', '').replace('/', '')
            if sector_lower in title_clean or any(word in title_clean for word in sector.lower().split()):
                hn_score += story['points']

        if hn_score > 100:
            score += 15
            signals.append(f"HackerNews: {hn_score} discussion points")

        # 5. StackOverflow signal (developer interest)
        so_questions = 0
        for tag in stackoverflow_by_tag:
            tag_clean = tag.lower().replace(' ', '').replace('/', '')
            if sector_lower in tag_clean or tag_clean in sector_lower:
                so_questions += stackoverflow_by_tag[tag]

        if so_questions > 5000:
            score += 15
            signals.append(f"StackOverflow: {so_questions:,} questions")

        # 6. NPM signal (JavaScript ecosystem)
        npm_downloads = 0
        for keyword in npm_by_keyword:
            keyword_clean = keyword.lower().replace(' ', '').replace('/', '')
            if sector_lower in keyword_clean or keyword_clean in sector_lower:
                npm_downloads += npm_by_keyword[keyword]

        if npm_downloads > 1000000:  # >1M downloads/week
            score += 10
            signals.append(f"NPM: {npm_downloads:,} downloads/week")

        # 7. PyPI signal (Python ecosystem)
        pypi_downloads = 0
        for package in pypi_by_package:
            package_clean = package.lower().replace(' ', '').replace('/', '')
            if sector_lower in package_clean or package_clean in sector_lower:
                pypi_downloads += pypi_by_package[package]

        if pypi_downloads > 100000:  # >100k downloads/month
            score += 10
            signals.append(f"PyPI: {pypi_downloads:,} downloads/month")

        # 8. OpenAlex signal (high-citation research)
        openalex_citations = 0
        for concept in openalex_concepts:
            concept_clean = concept.lower().replace(' ', '').replace('/', '')
            if sector_lower in concept_clean or concept_clean in sector_lower:
                openalex_citations += openalex_concepts[concept]

        if openalex_citations > 500:
            score += 10
            signals.append(f"OpenAlex: {openalex_citations:,} citations")

        # 9. GDELT signal (geopolitical attention)
        if gdelt_activity > 100:
            score += 5
            signals.append(f"GDELT: {gdelt_activity} global events")

        # Multi-signal bonus (strong indicator!)
        if len(signals) >= 4:
            score += 20
            signals.append("Multi-source confirmation (4+ signals)")
        elif len(signals) >= 3:
            score += 15
            signals.append("Multi-source confirmation (3 signals)")

        # Lowered threshold: 50 → 40
        if score >= 40:
            sector_predictions.append({
                'sector': sector,
                'score': score,
                'signals': signals,
                'funding': funding_by_sector.get(sector, {'total': 0})
            })

    # Sort by score
    sector_predictions.sort(key=lambda x: x['score'], reverse=True)

    return sector_predictions

def generate_report(predictions):
    """Gera relatório formatado"""
    report = []
    report.append("=" * 80)
    report.append("💰 CAPITAL FLOW PREDICTOR - Sofia Pulse Intelligence")
    report.append("=" * 80)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("Predicts where capital will flow in next 12-18 months")
    report.append("BEFORE venture capitalists move in")
    report.append("")
    report.append("Data sources: Funding + ArXiv + GitHub + GDELT + HackerNews + StackOverflow + NPM + PyPI + OpenAlex")
    report.append("")
    report.append("=" * 80)
    report.append("")

    if not predictions:
        report.append("⚠️  No high-confidence predictions at this time.")
        return "\n".join(report)

    report.append(f"🎯 TOP {len(predictions)} SECTORS FOR CAPITAL INFLOW")
    report.append("")

    for i, pred in enumerate(predictions, 1):
        report.append(f"{i}. {pred['sector'].upper()}")
        report.append(f"   Capital Flow Score: {pred['score']}/100")
        report.append("")
        report.append("   Signals detected:")
        for signal in pred['signals']:
            report.append(f"   • {signal}")
        report.append("")

        # Prediction
        if pred['score'] >= 85:
            prediction = "🔴 EXPLOSION IMMINENT (Next 6-12 months)"
            capital = "$1-3B in new funding expected"
        elif pred['score'] >= 70:
            prediction = "🟠 HIGH GROWTH EXPECTED (Next 12-18 months)"
            capital = "$500M-$1B in new funding expected"
        else:
            prediction = "🟡 STEADY GROWTH (Next 18-24 months)"
            capital = "$100-500M in new funding expected"

        report.append(f"   ✅ PREDICTION: {prediction}")
        report.append(f"   💰 CAPITAL ESTIMATE: {capital}")
        report.append("")
        report.append("   " + "-" * 70)
        report.append("")

    report.append("=" * 80)
    report.append("📚 METHODOLOGY")
    report.append("=" * 80)
    report.append("")
    report.append("Signal Sources (9 data streams):")
    report.append("  • Current Funding: Deal flow (25 points max)")
    report.append("  • ArXiv Papers: Academic research (20 points max)")
    report.append("  • GitHub Trending: Technical momentum (20 points max)")
    report.append("  • HackerNews: Community buzz (15 points max)")
    report.append("  • StackOverflow: Developer interest (15 points max)")
    report.append("  • NPM Downloads: JavaScript ecosystem (10 points max)")
    report.append("  • PyPI Downloads: Python ecosystem (10 points max)")
    report.append("  • OpenAlex: High-citation research (10 points max)")
    report.append("  • GDELT Events: Geopolitical attention (5 points max)")
    report.append("  • Multi-signal bonus: +15-20 if 3-4+ sources")
    report.append("")
    report.append("Threshold: 40+ points = High-confidence prediction")
    report.append("Lag time: Research → Technical Activity → Funding (6-18 months)")
    report.append("")
    report.append("=" * 80)

    return "\n".join(report)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("📊 Analyzing capital flow patterns...")
        predictions = analyze_capital_flow(conn)

        print(f"✅ Generated {len(predictions)} predictions")

        # Generate report
        report = generate_report(predictions)

        # Save report
        output_file = 'analytics/capital-flow-latest.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ Report saved: {output_file}")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
