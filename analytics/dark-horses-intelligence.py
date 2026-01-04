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
    Detecta tecnologias com sinais conflitantes usando 9 fontes:

    DARK HORSE PATTERNS:
    - Papers ↑ + Funding ↓ = Research forte mas sem hype comercial
    - GitHub ↓ + OpenAlex ↑ = Academia forte, implementação fraca
    - StackOverflow ↑ + Funding ↓ = Developers usando, VCs ignorando
    - PyPI/NPM ↑ + Papers ↓ = Prática sem teoria (underdog tools)
    - GDELT ↑ + Funding ↓ = Governo investindo, VCs não (strategic tech)
    - HackerNews ↑ + GitHub ↓ = Buzz sem código (vaporware ou early)
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Áreas emergentes para monitorar (expandido)
    emerging_areas = [
        # Computing paradigms
        'Neuromorphic Computing', 'Photonic Computing', 'DNA Storage',
        'Quantum Networking', 'Molecular Computing', 'Optical Computing',
        'Reversible Computing', 'Probabilistic Computing',

        # Biology & Health
        'Brain-Computer Interface', 'Synthetic Biology', 'Lab-grown Materials',
        'Longevity Tech', 'Gene Therapy', 'CRISPR', 'Organoids',
        'Biohacking', 'Neurotechnology', 'Precision Medicine',

        # Energy & Environment
        'Carbon Capture', 'Fusion Energy', 'Hydrogen Storage',
        'Nuclear Batteries', 'Perovskite Solar', 'Geothermal',
        'Wave Energy', 'Thorium Reactors',

        # Space & Materials
        'Space Mining', 'Asteroid Mining', 'Lunar Resources',
        'Graphene', 'Metamaterials', 'Aerogel', 'Self-healing Materials',

        # Agriculture & Food
        'Vertical Farming', 'Cellular Agriculture', 'Algae Farming',
        'Insect Protein', 'Lab-grown Meat', 'Mycoprotein',

        # Computing & AI
        'Edge AI', 'Federated Learning', 'Homomorphic Encryption',
        'Zero-Knowledge Proofs', 'Digital Twins', 'Neuromorphic Chips',
        'Analog AI', 'Spiking Neural Networks'
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

        # 5. StackOverflow (Developer interest)
        cur.execute("""
            SELECT SUM(count) as questions
            FROM sofia.stackoverflow_trends
            WHERE collected_at >= CURRENT_DATE - INTERVAL '90 days'
            AND LOWER(tag_name) LIKE %s
        """, (f'%{area.lower()}%',))
        so_data = cur.fetchone()
        so_questions = int(so_data['questions'] or 0)

        if so_questions > 1000:
            high_signals.append(f"StackOverflow: {so_questions:,} questions")
        elif so_questions > 0:
            low_signals.append(f"StackOverflow: Only {so_questions} questions")

        # 6. HackerNews (Community buzz)
        cur.execute("""
            SELECT SUM(points) as total_points, COUNT(*) as stories
            FROM sofia.hackernews_stories
            WHERE collected_at >= CURRENT_DATE - INTERVAL '30 days'
            AND LOWER(title) LIKE %s
        """, (f'%{area.lower()}%',))
        hn_data = cur.fetchone()
        hn_points = int(hn_data['total_points'] or 0)
        hn_stories = int(hn_data['stories'] or 0)

        if hn_points > 100:
            high_signals.append(f"HackerNews: {hn_points} points ({hn_stories} stories)")
        elif hn_stories > 0:
            low_signals.append(f"HackerNews: Minimal buzz ({hn_points} points)")

        # 7. NPM (JavaScript ecosystem)
        cur.execute("""
            SELECT SUM(downloads_week) as downloads, COUNT(*) as packages
            FROM sofia.npm_stats
            WHERE collected_at >= CURRENT_DATE - INTERVAL '30 days'
            AND (LOWER(package_name) LIKE %s OR LOWER(description) LIKE %s)
        """, (f'%{area.lower()}%', f'%{area.lower()}%'))
        npm_data = cur.fetchone()
        npm_downloads = int(npm_data['downloads'] or 0)
        npm_packages = int(npm_data['packages'] or 0)

        if npm_downloads > 100000:  # >100k/week
            high_signals.append(f"NPM: {npm_downloads:,} downloads/week ({npm_packages} packages)")
        elif npm_packages > 0:
            low_signals.append(f"NPM: Low adoption ({npm_downloads:,} downloads)")

        # 8. PyPI (Python ecosystem)
        cur.execute("""
            SELECT SUM(downloads_month) as downloads, COUNT(*) as packages
            FROM sofia.pypi_stats
            WHERE collected_at >= CURRENT_DATE - INTERVAL '30 days'
            AND (LOWER(package_name) LIKE %s OR LOWER(description) LIKE %s)
        """, (f'%{area.lower()}%', f'%{area.lower()}%'))
        pypi_data = cur.fetchone()
        pypi_downloads = int(pypi_data['downloads'] or 0)
        pypi_packages = int(pypi_data['packages'] or 0)

        if pypi_downloads > 50000:  # >50k/month
            high_signals.append(f"PyPI: {pypi_downloads:,} downloads/month ({pypi_packages} packages)")
        elif pypi_packages > 0:
            low_signals.append(f"PyPI: Low adoption ({pypi_downloads:,} downloads)")

        # 9. OpenAlex (High-citation research)
        cur.execute("""
            SELECT SUM(cited_by_count) as total_citations, COUNT(*) as papers
            FROM sofia.openalex_papers
            WHERE LOWER(title) LIKE %s
        """, (f'%{area.lower()}%',))
        openalex_data = cur.fetchone()
        openalex_citations = int(openalex_data['total_citations'] or 0)
        openalex_papers = int(openalex_data['papers'] or 0)

        if openalex_citations > 100:
            high_signals.append(f"OpenAlex: {openalex_citations:,} citations ({openalex_papers} papers)")
        elif openalex_papers > 0:
            low_signals.append(f"OpenAlex: Low citations ({openalex_citations})")

        # Detect dark horse patterns with 9 sources (lowered thresholds)
        is_dark_horse = False
        stealth_score = 0
        analysis_parts = []

        # Pattern 1: Research ↑ + Funding ↓ (Academia strong, VCs ignoring)
        if papers_count >= 3 and funding_data['deals'] == 0:  # Lowered: 5→3
            is_dark_horse = True
            stealth_score += 35
            analysis_parts.append("Research strong BUT no VC funding = Stealth/Early")

        # Pattern 2: Papers ↑ + GitHub ↓ (Theory without practice)
        if papers_count >= 3 and github_data['repos'] == 0:
            is_dark_horse = True
            stealth_score += 30
            analysis_parts.append("Papers BUT no GitHub = Corporate R&D")

        # Pattern 3: OpenAlex ↑ + GitHub ↓ (Academia strong, implementation weak)
        if openalex_citations > 100 and github_data['repos'] == 0:
            is_dark_horse = True
            stealth_score += 25
            analysis_parts.append("High citations BUT no code = Academic only")

        # Pattern 4: StackOverflow ↑ + Funding ↓ (Devs using, VCs ignoring)
        if so_questions > 1000 and funding_data['deals'] == 0:
            is_dark_horse = True
            stealth_score += 30
            analysis_parts.append("Devs using BUT no VC = Undervalued tool")

        # Pattern 5: PyPI/NPM ↑ + Papers ↓ (Practice without theory - underdog!)
        if (pypi_downloads > 50000 or npm_downloads > 100000) and papers_count < 3:
            is_dark_horse = True
            stealth_score += 25
            analysis_parts.append("High downloads BUT no papers = Pragmatic underdog")

        # Pattern 6: GDELT ↑ + Funding ↓ (Gov investing, VCs not)
        if gdelt_count > 100 and funding_data['deals'] == 0:
            is_dark_horse = True
            stealth_score += 20
            analysis_parts.append("Gov interest BUT no VC = Strategic tech")

        # Pattern 7: HackerNews ↑ + GitHub ↓ (Buzz without code)
        if hn_points > 100 and github_data['repos'] == 0:
            is_dark_horse = True
            stealth_score += 20
            analysis_parts.append("HN buzz BUT no code = Vaporware or very early")

        # Pattern 8: High diversity of signals (many sources = emerging broadly)
        total_signals = len(high_signals) + len(low_signals)
        if total_signals >= 5 and len(high_signals) >= 2 and len(low_signals) >= 2:
            is_dark_horse = True
            stealth_score += 15
            analysis_parts.append(f"Diverse signals ({len(high_signals)}↑ {len(low_signals)}↓) = Emerging")

        analysis = " | ".join(analysis_parts) if analysis_parts else ""

        # Lowered threshold: 40 → 30
        if is_dark_horse and stealth_score >= 30:
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
    report.append("Detects technologies in STEALTH MODE using 9 data sources")
    report.append("Conflicting signals = Hidden opportunities")
    report.append("")
    report.append("Sources: ArXiv + Funding + GitHub + GDELT + StackOverflow + HackerNews + NPM + PyPI + OpenAlex")
    report.append("Patterns: 8 dark horse patterns (Academia-VC gap, Dev-VC gap, Theory-Practice gap, etc.)")
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
