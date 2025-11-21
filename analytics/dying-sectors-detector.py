#!/usr/bin/env python3
"""
SOFIA PULSE - DYING SECTORS DETECTOR
Detecta setores tecnológicos que estão morrendo
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
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME') or 'sofia_db',
}

def detect_dying_sectors(conn):
    """Detecta tecnologias/setores em declínio"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Tecnologias legacy conhecidas
    legacy_tech = [
        'AngularJS', 'Angular.js', 'Backbone', 'Ember', 'Knockout',
        'Hadoop', 'MapReduce', 'Hive', 'Pig',
        'PHP 5', 'PHP Enterprise', 'CakePHP',
        'Ruby on Rails', 'Rails',
        'jQuery', 'Prototype.js',
        'Flash', 'Silverlight',
        'Perl', 'CGI',
        'Teradata', 'Oracle Database', 'SQL Server',
        'MongoDB < 4', 'CouchDB',
        'SOAP', 'XML-RPC',
        'SVN', 'CVS'
    ]

    dying_tech = []

    for tech in legacy_tech:
        signals = []
        death_score = 0

        # GitHub activity (simulado - verificar stars caindo)
        cur.execute("""
            SELECT COUNT(*) as repos, SUM(stars) as total_stars
            FROM sofia.github_trending
            WHERE collected_at >= CURRENT_DATE - INTERVAL '90 days'
            AND (LOWER(name) LIKE %s OR LOWER(description) LIKE %s)
        """, (f'%{tech.lower()}%', f'%{tech.lower()}%'))
        github_data = cur.fetchone()

        if github_data['repos'] == 0:
            death_score += 30
            signals.append(f"GitHub: 0 repos trending (90 days)")
        elif github_data['total_stars'] < 100:
            death_score += 20
            signals.append(f"GitHub: Only {github_data['total_stars']} stars (declining)")

        # Funding (ausência = morte)
        cur.execute("""
            SELECT COUNT(*) as deals
            FROM sofia.funding_rounds
            WHERE deal_date >= CURRENT_DATE - INTERVAL '365 days'
            AND (LOWER(company) LIKE %s OR LOWER(sector) LIKE %s)
        """, (f'%{tech.lower()}%', f'%{tech.lower()}%'))
        funding_data = cur.fetchone()

        if funding_data['deals'] == 0:
            death_score += 25
            signals.append(f"Funding: $0 in last 12 months")

        # Papers (ausência de research = morte)
        cur.execute("""
            SELECT COUNT(*) as papers
            FROM sofia.arxiv_ai_papers
            WHERE published_date >= CURRENT_DATE - INTERVAL '180 days'
            AND (LOWER(title) LIKE %s OR %s = ANY(keywords))
        """, (f'%{tech.lower()}%', tech.lower()))
        papers_data = cur.fetchone()

        if papers_data['papers'] == 0:
            death_score += 20
            signals.append(f"Papers: 0 publications (180 days)")

        # HackerNews mentions
        cur.execute("""
            SELECT COUNT(*) as mentions
            FROM sofia.hackernews_stories
            WHERE collected_at >= CURRENT_DATE - INTERVAL '90 days'
            AND LOWER(title) LIKE %s
        """, (f'%{tech.lower()}%',))
        hn_data = cur.fetchone()

        if hn_data['mentions'] == 0:
            death_score += 15
            signals.append(f"HackerNews: 0 discussions (90 days)")

        if death_score >= 50:  # Threshold de morte
            status = "💀 DEAD" if death_score >= 80 else "☠️  DYING" if death_score >= 65 else "📉 DECLINING"

            dying_tech.append({
                'tech': tech,
                'death_score': death_score,
                'status': status,
                'signals': signals
            })

    # Sort by death score
    dying_tech.sort(key=lambda x: x['death_score'], reverse=True)

    return dying_tech

def generate_report(dying_tech):
    """Gera relatório formatado"""
    report = []
    report.append("=" * 80)
    report.append("💀 DYING SECTORS DETECTOR - Sofia Pulse Intelligence")
    report.append("=" * 80)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("Detects technology sectors in terminal decline")
    report.append("AVOID INVESTING TIME/MONEY IN THESE TECHNOLOGIES")
    report.append("")
    report.append("=" * 80)
    report.append("")

    if not dying_tech:
        report.append("✅ No dying sectors detected (good news!)")
        return "\n".join(report)

    report.append(f"⚠️  {len(dying_tech)} TECHNOLOGIES IN DECLINE")
    report.append("")

    for tech in dying_tech:
        report.append(f"{tech['status']} {tech['tech'].upper()}")
        report.append(f"   Death Score: {tech['death_score']}/100")
        report.append("")
        report.append("   Death Signals:")
        for signal in tech['signals']:
            report.append(f"   • {signal}")
        report.append("")

        # Recommendations
        if tech['death_score'] >= 80:
            action = "🔴 ABANDON IMMEDIATELY - No future"
            timeline = "Already obsolete"
        elif tech['death_score'] >= 65:
            action = "🟠 PLAN MIGRATION (6-12 months)"
            timeline = "Will be obsolete soon"
        else:
            action = "🟡 FREEZE NEW PROJECTS"
            timeline = "Still has 1-2 years"

        report.append(f"   ✅ RECOMMENDATION: {action}")
        report.append(f"   ⏱️  TIMELINE: {timeline}")
        report.append("")
        report.append("   " + "-" * 70)
        report.append("")

    report.append("=" * 80)
    report.append("📚 METHODOLOGY")
    report.append("=" * 80)
    report.append("")
    report.append("Death Signals:")
    report.append("  • GitHub: No repos/low stars (30 points max)")
    report.append("  • Funding: No deals (25 points max)")
    report.append("  • Papers: No research (20 points max)")
    report.append("  • HackerNews: No discussions (15 points max)")
    report.append("")
    report.append("Death Score Thresholds:")
    report.append("  • 80+: DEAD (abandon now)")
    report.append("  • 65-79: DYING (migrate within 12 months)")
    report.append("  • 50-64: DECLINING (freeze new projects)")
    report.append("")
    report.append("=" * 80)

    return "\n".join(report)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("📊 Detecting dying sectors...")
        dying_tech = detect_dying_sectors(conn)

        print(f"⚠️  Found {len(dying_tech)} dying technologies")

        report = generate_report(dying_tech)

        output_file = 'analytics/dying-sectors-latest.txt'
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
