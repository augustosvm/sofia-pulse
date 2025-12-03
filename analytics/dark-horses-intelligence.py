#!/usr/bin/env python3
"""
SOFIA PULSE - DARK HORSES INTELLIGENCE
Detecta tecnologias em "stealth mode" com sinais conflitantes
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

def detect_dark_horses(conn):
    """
    Detecta tecnologias com sinais conflitantes:
    - Papers ↑ mas Funding ↓ = Research forte mas sem hype
    - Patents ↑ mas GitHub ↓ = Corporações em stealth mode
    - GDELT ↑ mas Funding ↓ = Governo investindo, VCs não
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Áreas emergentes para monitorar
    emerging_areas = [
        'Neuromorphic Computing', 'Photonic Computing', 'DNA Storage',
        'Quantum Networking', 'Molecular Computing', 'Brain-Computer Interface',
        'Synthetic Biology', 'Lab-grown Materials', 'Carbon Capture',
        'Fusion Energy', 'Space Mining', 'Vertical Farming',
        'Longevity Tech', 'Digital Twins', 'Edge AI'
    ]

    dark_horses = []

    for area in emerging_areas:
        high_signals = []
        low_signals = []
        analysis = ""

        # 1. Papers (Research strength)
        cur.execute("""
            SELECT COUNT(*) as papers
            FROM sofia.arxiv_ai_papers
            WHERE published_date >= CURRENT_DATE - INTERVAL '180 days'
            AND (LOWER(title) LIKE %s OR %s = ANY(keywords))
        """, (f'%{area.lower()}%', area.lower()))
        papers_count = cur.fetchone()['papers']

        if papers_count >= 5:
            high_signals.append(f"Research: {papers_count} papers (high academic interest)")
        else:
            low_signals.append(f"Research: Only {papers_count} papers")

        # 2. Funding (Market hype)
        cur.execute("""
            SELECT COUNT(*) as deals, SUM(CAST(amount_usd / 1000000.0 AS NUMERIC)) as total
            FROM sofia.funding_rounds
            WHERE announced_date >= CURRENT_DATE - INTERVAL '365 days'
            AND (LOWER(company_name) LIKE %s OR LOWER(sector) LIKE %s)
        """, (f'%{area.lower()}%', f'%{area.lower()}%'))
        funding_data = cur.fetchone()

        if funding_data['deals'] == 0:
            low_signals.append(f"Funding: $0 (no VC attention)")
        else:
            high_signals.append(f"Funding: ${float(funding_data['total'] or 0) / 1000000.0:.1f}M")

        # 3. GitHub (Public technical activity)
        cur.execute("""
            SELECT COUNT(*) as repos, SUM(stars) as stars
            FROM sofia.github_trending
            WHERE collected_at >= CURRENT_DATE - INTERVAL '90 days'
            AND (LOWER(name) LIKE %s OR LOWER(description) LIKE %s)
        """, (f'%{area.lower()}%', f'%{area.lower()}%'))
        github_data = cur.fetchone()

        if github_data['repos'] == 0 or github_data['stars'] < 100:
            low_signals.append(f"GitHub: Minimal public activity")
        else:
            high_signals.append(f"GitHub: {github_data['repos']} repos, {github_data['stars']} stars")

        # 4. GDELT (Geopolitical attention)
        cur.execute("""
            SELECT COUNT(*) as events
            FROM sofia.gdelt_events
            WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
        """)
        gdelt_count = cur.fetchone()['events']

        if gdelt_count > 100:
            high_signals.append(f"Geopolitics: High activity ({gdelt_count} events)")

        # Detect dark horse pattern: HIGH research/patents BUT LOW funding/github
        is_dark_horse = False
        stealth_score = 0

        if papers_count >= 5 and funding_data['deals'] == 0:
            is_dark_horse = True
            stealth_score += 40
            analysis = "Strong research BUT no VC funding = Stealth mode or too early"

        if papers_count >= 5 and github_data['repos'] == 0:
            is_dark_horse = True
            stealth_score += 30
            analysis += " | High papers BUT low GitHub = Corporate R&D"

        if gdelt_count > 100 and funding_data['deals'] == 0:
            is_dark_horse = True
            stealth_score += 30
            analysis += " | Government interest BUT no VC = Strategic tech"

        if is_dark_horse and stealth_score >= 40:
            dark_horses.append({
                'area': area,
                'stealth_score': stealth_score,
                'high_signals': high_signals,
                'low_signals': low_signals,
                'analysis': analysis
            })

    # Sort by stealth score
    dark_horses.sort(key=lambda x: x['stealth_score'], reverse=True)

    return dark_horses

def generate_report(dark_horses):
    """Gera relatório formatado"""
    report = []
    report.append("=" * 80)
    report.append("🐴 DARK HORSES INTELLIGENCE - Sofia Pulse")
    report.append("=" * 80)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("Detects technologies in STEALTH MODE")
    report.append("Conflicting signals = Hidden opportunities")
    report.append("")
    report.append("=" * 80)
    report.append("")

    if not dark_horses:
        report.append("✅ No dark horses detected at this time")
        report.append("This means:")
        report.append("  • Market signals are aligned")
        report.append("  • No hidden opportunities OR")
        report.append("  • Need more data coverage")
        return "\n".join(report)

    report.append(f"🔍 {len(dark_horses)} DARK HORSE TECHNOLOGIES DETECTED")
    report.append("")

    for i, horse in enumerate(dark_horses, 1):
        fire_rating = "🔥🔥🔥" if horse['stealth_score'] >= 70 else "🔥🔥" if horse['stealth_score'] >= 50 else "🔥"

        report.append(f"{i}. {horse['area'].upper()} {fire_rating}")
        report.append(f"   Stealth Score: {horse['stealth_score']}/100")
        report.append("")
        report.append("   ✅ HIGH Signals:")
        for signal in horse['high_signals']:
            report.append(f"      • {signal}")
        report.append("")
        report.append("   ⚠️  LOW Signals:")
        for signal in horse['low_signals']:
            report.append(f"      • {signal}")
        report.append("")
        report.append(f"   🎯 ANALYSIS:")
        report.append(f"      {horse['analysis']}")
        report.append("")

        # Recommendation
        if horse['stealth_score'] >= 70:
            prediction = "🟢 HIGH PROBABILITY - Will explode 2026-2027"
            action = "Monitor closely. Prepare to move fast."
        elif horse['stealth_score'] >= 50:
            action = "🟡 MEDIUM PROBABILITY - Watch for inflection point"
            prediction = "Keep on radar. May breakout 2027-2028"
        else:
            prediction = "🟠 SPECULATIVE - Long-term play"
            action = "Background monitoring only"

        report.append(f"   ✅ PREDICTION: {prediction}")
        report.append(f"   💡 ACTION: {action}")
        report.append("")
        report.append("   " + "-" * 70)
        report.append("")

    report.append("=" * 80)
    report.append("📚 DARK HORSE PATTERNS")
    report.append("=" * 80)
    report.append("")
    report.append("Pattern 1: Papers ↑ + Funding ↓")
    report.append("  → Too early OR Academic only")
    report.append("")
    report.append("Pattern 2: Papers ↑ + GitHub ↓")
    report.append("  → Corporate R&D in stealth mode")
    report.append("")
    report.append("Pattern 3: GDELT ↑ + Funding ↓")
    report.append("  → Government/strategic tech, VCs ignoring")
    report.append("")
    report.append("=" * 80)

    return "\n".join(report)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("📊 Detecting dark horse technologies...")
        dark_horses = detect_dark_horses(conn)

        print(f"🔍 Found {len(dark_horses)} dark horses")

        report = generate_report(dark_horses)

        output_file = 'analytics/dark-horses-intelligence-latest.txt'
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
