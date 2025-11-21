#!/usr/bin/env python3
"""
SOFIA PULSE - CAREER TRENDS PREDICTOR
Prevê tendências de carreira ANTES das empresas
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

def analyze_career_trends(conn):
    """
    Cruza 4 fontes para detectar skills emergentes:
    1. GitHub Trending - Stars crescendo
    2. LinkedIn Jobs - Menções em vagas (simulado via descrições)
    3. Reddit/HN - Discussões crescendo
    4. Papers - Research acadêmico
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 1. GitHub: Tecnologias com crescimento explosivo
    cur.execute("""
        SELECT
            UNNEST(topics) as tech,
            COUNT(*) as repos,
            SUM(stars) as total_stars,
            AVG(stars) as avg_stars
        FROM sofia.github_trending
        WHERE collected_at >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY tech
        HAVING COUNT(*) >= 3
        ORDER BY total_stars DESC
        LIMIT 50
    """)
    github_trends = {row['tech']: {
        'repos': row['repos'],
        'stars': row['total_stars'],
        'avg_stars': row['avg_stars']
    } for row in cur.fetchall()}

    # 2. HackerNews: Discussões sobre tecnologias
    cur.execute("""
        SELECT
            title,
            score,
            url
        FROM sofia.hackernews_stories
        WHERE collected_at >= CURRENT_DATE - INTERVAL '30 days'
        AND score >= 50
        ORDER BY score DESC
        LIMIT 100
    """)
    hn_stories = cur.fetchall()

    # Extrair tecnologias das discussões
    tech_keywords = list(github_trends.keys())
    hn_mentions = defaultdict(int)
    for story in hn_stories:
        title_lower = story['title'].lower()
        for tech in tech_keywords:
            if tech.lower() in title_lower:
                hn_mentions[tech] += story['score']

    # 3. Papers: Research acadêmico
    cur.execute("""
        SELECT
            UNNEST(keywords) as keyword,
            COUNT(*) as paper_count
        FROM sofia.arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY keyword
        HAVING COUNT(*) >= 3
        ORDER BY paper_count DESC
        LIMIT 50
    """)
    paper_trends = {row['keyword']: row['paper_count'] for row in cur.fetchall()}

    # Cruzar dados e calcular score
    hot_skills = []

    for tech in github_trends.keys():
        score = 0
        signals = []

        # GitHub signal
        if github_trends[tech]['stars'] > 1000:
            score += 30
            signals.append(f"GitHub: {github_trends[tech]['stars']:,} stars ({github_trends[tech]['repos']} repos)")

        # HackerNews signal
        if tech in hn_mentions and hn_mentions[tech] > 100:
            score += 25
            signals.append(f"HackerNews: {hn_mentions[tech]} discussion score")

        # Papers signal
        tech_in_papers = False
        for keyword in paper_trends:
            if tech.lower() in keyword.lower() or keyword.lower() in tech.lower():
                score += 20
                signals.append(f"Papers: {paper_trends[keyword]} publications")
                tech_in_papers = True
                break

        # Multi-signal bonus
        if len(signals) >= 2:
            score += 25

        if score >= 50:  # Threshold para "hot skill"
            hot_skills.append({
                'tech': tech,
                'score': score,
                'signals': signals,
                'github': github_trends[tech]
            })

    # Sort by score
    hot_skills.sort(key=lambda x: x['score'], reverse=True)

    return hot_skills[:10]  # Top 10

def generate_report(hot_skills):
    """Gera relatório formatado"""
    report = []
    report.append("=" * 80)
    report.append("🎓 CAREER TRENDS PREDICTOR - Sofia Pulse Intelligence")
    report.append("=" * 80)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("Predicts hot skills 6-12 months BEFORE market explosion")
    report.append("Data sources: GitHub + HackerNews + ArXiv Papers")
    report.append("")
    report.append("=" * 80)
    report.append("")

    if not hot_skills:
        report.append("⚠️  No hot skills detected in current data.")
        report.append("")
        report.append("This may indicate:")
        report.append("  • Need more data collection cycles")
        report.append("  • Threshold too high")
        report.append("  • Market in consolidation phase")
        return "\n".join(report)

    report.append(f"🔥 TOP {len(hot_skills)} HOT SKILLS")
    report.append("")

    for i, skill in enumerate(hot_skills, 1):
        report.append(f"{i}. {skill['tech'].upper()}")
        report.append(f"   Intelligence Score: {skill['score']}/100")
        report.append("")
        report.append("   Signals detected:")
        for signal in skill['signals']:
            report.append(f"   • {signal}")
        report.append("")

        # Actionable insights
        if skill['score'] >= 80:
            urgency = "🔴 CRITICAL - Learn NOW"
            timeline = "Market explosion expected in 3-6 months"
        elif skill['score'] >= 70:
            urgency = "🟠 HIGH - Start this month"
            timeline = "Market explosion expected in 6-12 months"
        else:
            urgency = "🟡 MEDIUM - Monitor closely"
            timeline = "Early stage, watch for acceleration"

        report.append(f"   ✅ ACTION: {urgency}")
        report.append(f"   ⏱️  TIMELINE: {timeline}")
        report.append("")
        report.append("   " + "-" * 70)
        report.append("")

    report.append("=" * 80)
    report.append("📚 METHODOLOGY")
    report.append("=" * 80)
    report.append("")
    report.append("Signal Sources:")
    report.append("  • GitHub Trending: Stars, repos (30 points max)")
    report.append("  • HackerNews: Discussion scores (25 points max)")
    report.append("  • ArXiv Papers: Academic research (20 points max)")
    report.append("  • Multi-signal bonus: +25 points if 2+ sources")
    report.append("")
    report.append("Threshold: 50+ points = Hot Skill")
    report.append("Update frequency: Daily")
    report.append("")
    report.append("=" * 80)

    return "\n".join(report)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("📊 Analyzing career trends...")
        hot_skills = analyze_career_trends(conn)

        print(f"✅ Found {len(hot_skills)} hot skills")

        # Generate report
        report = generate_report(hot_skills)

        # Save report
        output_file = 'analytics/career-trends-latest.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ Report saved: {output_file}")
        print("")
        print("Preview:")
        print(report[:500] + "..." if len(report) > 500 else report)

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
