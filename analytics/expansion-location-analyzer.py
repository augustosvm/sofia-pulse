#!/usr/bin/env python3
"""
SOFIA PULSE - EXPANSION LOCATION ANALYZER
Recomenda melhores cidades para abrir filiais
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
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

def analyze_locations(conn):
    """Analisa melhores cidades para expansão"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Cidades estratégicas para monitorar
    cities = [
        # US
        {'name': 'Austin, TX', 'country': 'USA', 'cost': 'Medium'},
        {'name': 'Seattle, WA', 'country': 'USA', 'cost': 'High'},
        {'name': 'Boulder, CO', 'country': 'USA', 'cost': 'High'},
        {'name': 'Atlanta, GA', 'country': 'USA', 'cost': 'Medium'},
        # Canada
        {'name': 'Montreal, QC', 'country': 'Canada', 'cost': 'Low'},
        {'name': 'Toronto, ON', 'country': 'Canada', 'cost': 'Medium'},
        # Europe
        {'name': 'Berlin', 'country': 'Germany', 'cost': 'Medium'},
        {'name': 'Amsterdam', 'country': 'Netherlands', 'cost': 'High'},
        {'name': 'Lisbon', 'country': 'Portugal', 'cost': 'Low'},
        # Asia
        {'name': 'Singapore', 'country': 'Singapore', 'cost': 'High'},
        {'name': 'Bangalore', 'country': 'India', 'cost': 'Low'},
        {'name': 'Tel Aviv', 'country': 'Israel', 'cost': 'High'},
    ]

    city_scores = []

    for city in cities:
        score = 0
        advantages = []
        disadvantages = []

        # Universidades/Papers (proxy via país/região)
        cur.execute("""
            SELECT COUNT(*) as papers
            FROM sofia.openalex_papers
            WHERE publication_date >= CURRENT_DATE - INTERVAL '180 days'
        """)
        papers_data = cur.fetchone()
        if papers_data['papers'] > 50:
            score += 25
            advantages.append(f"Research output: {papers_data['papers']} papers (regional)")
        else:
            disadvantages.append(f"Limited research: {papers_data['papers']} papers only")

        # Funding activity - FILTRADO POR PAÍS
        cur.execute("""
            SELECT COUNT(*) as deals, SUM(amount_usd) as total_funding
            FROM sofia.funding_rounds
            WHERE announced_date >= CURRENT_DATE - INTERVAL '365 days'
            AND country = %s
        """, (city['country'],))
        funding_data = cur.fetchone()
        deals_count = funding_data['deals'] or 0

        if deals_count > 10:
            score += 25
            advantages.append(f"Strong startup ecosystem: {deals_count} funding deals")
        elif deals_count > 5:
            score += 15
            advantages.append(f"Moderate startup activity: {deals_count} deals")
        elif deals_count > 0:
            score += 5
            disadvantages.append(f"Limited startup ecosystem: only {deals_count} deals")
        else:
            disadvantages.append(f"No recent funding deals (weak ecosystem)")

        # Cost adjustment
        if city['cost'] == 'Low':
            score += 20
            advantages.append(f"Cost of living: Low (salary advantage)")
        elif city['cost'] == 'Medium':
            score += 10
            advantages.append(f"Cost of living: Medium (balanced)")
        else:  # High
            disadvantages.append(f"High cost of living (expensive salaries)")

        # Tech hub bonus
        if city['name'] in ['Austin, TX', 'Montreal, QC', 'Singapore', 'Berlin']:
            score += 15
            advantages.append(f"Recognized tech hub (established ecosystem)")
        else:
            disadvantages.append(f"Not a primary tech hub")

        city_scores.append({
            'city': city['name'],
            'country': city['country'],
            'score': score,
            'cost': city['cost'],
            'advantages': advantages,
            'disadvantages': disadvantages,
            'deals_count': deals_count
        })

    # Sort by score
    city_scores.sort(key=lambda x: x['score'], reverse=True)

    return city_scores[:10]  # Top 10

def generate_report(locations):
    """Gera relatório formatado"""
    report = []
    report.append("=" * 80)
    report.append("🌍 EXPANSION LOCATION ANALYZER - Sofia Pulse Intelligence")
    report.append("=" * 80)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("Recommends best cities for office expansion")
    report.append("Based on: Talent + Startups + Cost + Tech ecosystem")
    report.append("")
    report.append("=" * 80)
    report.append("")

    if not locations:
        report.append("⚠️  No location data available")
        return "\n".join(report)

    report.append(f"🏆 TOP {len(locations)} CITIES FOR EXPANSION (2025-2026)")
    report.append("")

    for i, loc in enumerate(locations, 1):
        report.append(f"{i}. {loc['city']} ({loc['country']})")
        report.append(f"   Expansion Score: {loc['score']}/100")
        report.append(f"   Cost Level: {loc['cost']}")
        report.append(f"   Funding Deals (12 months): {loc['deals_count']}")
        report.append("")

        # Advantages
        if loc['advantages']:
            report.append("   ✅ Advantages:")
            for advantage in loc['advantages']:
                report.append(f"   • {advantage}")
            report.append("")

        # Disadvantages
        if loc['disadvantages']:
            report.append("   ⚠️  Disadvantages:")
            for disadvantage in loc['disadvantages']:
                report.append(f"   • {disadvantage}")
            report.append("")

        # Recommendation
        if loc['score'] >= 75:
            recommendation = "🟢 EXCELLENT CHOICE - Strong ecosystem + Good cost"
        elif loc['score'] >= 60:
            recommendation = "🟡 GOOD OPTION - Solid fundamentals"
        else:
            recommendation = "🟠 CONSIDER CAREFULLY - Weigh tradeoffs"

        report.append(f"   📊 RATING: {recommendation}")
        report.append("")
        report.append("   " + "-" * 70)
        report.append("")

    report.append("=" * 80)
    report.append("📚 METHODOLOGY")
    report.append("=" * 80)
    report.append("")
    report.append("Scoring Factors:")
    report.append("  • Research Output: Papers published (25 points max)")
    report.append("  • Startup Activity: Funding deals (25 points max)")
    report.append("  • Cost of Living: Low/Medium/High (0-20 points)")
    report.append("  • Tech Hub Status: Recognized ecosystem (+15 bonus)")
    report.append("")
    report.append("Cost Levels:")
    report.append("  • Low: $50-80k avg engineer salary")
    report.append("  • Medium: $80-120k avg engineer salary")
    report.append("  • High: $120k+ avg engineer salary")
    report.append("")
    report.append("=" * 80)

    return "\n".join(report)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("📊 Analyzing expansion locations...")
        locations = analyze_locations(conn)

        print(f"✅ Analyzed {len(locations)} cities")

        report = generate_report(locations)

        output_file = 'analytics/expansion-locations-latest.txt'
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
