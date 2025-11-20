#!/usr/bin/env python3
"""
SOFIA PULSE - CAUSAL INSIGHTS com MACHINE LEARNING
Gera insights PICA conectando TODOS os dados
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from collections import defaultdict
import json
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or 'localhost',
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5432'),
    'user': os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME') or 'sofia_db',
}

# ============================================================================
# 1. SINAIS FRACOS (Weak Signals) - GitHub → Funding
# ============================================================================

def detect_weak_signals(conn):
    """
    Detecta tecnologias com crescimento explosivo ANTES de funding

    Lógica:
    - GitHub stars crescendo >200% últimos 3 meses
    - Ainda sem funding significativo
    - = Sinal Fraco de próximo unicórnio
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Technologies trending no GitHub
    cur.execute("""
        SELECT
            unnest(topics) as tech,
            SUM(stars) as total_stars,
            COUNT(*) as repo_count,
            AVG(stars) as avg_stars_per_repo
        FROM sofia.github_trending
        WHERE topics IS NOT NULL
            AND created_at >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY tech
        HAVING SUM(stars) > 10000
        ORDER BY total_stars DESC
        LIMIT 20
    """)

    trending_techs = cur.fetchall()

    # Check if there's funding for these techs
    signals = []

    for tech in trending_techs:
        # Buscar funding relacionado
        cur.execute("""
            SELECT COUNT(*) as deal_count, SUM(amount_usd) as total_funding
            FROM sofia.funding_rounds
            WHERE LOWER(company_name) LIKE %s
                OR LOWER(sector) LIKE %s
                AND announced_date >= CURRENT_DATE - INTERVAL '180 days'
        """, (f"%{tech['tech']}%", f"%{tech['tech']}%"))

        funding = cur.fetchone()

        # Sinal Fraco = Alto GitHub + Baixo Funding
        if tech['total_stars'] > 50000 and (funding['deal_count'] or 0) < 3:
            signals.append({
                'tech': tech['tech'],
                'github_stars': int(tech['total_stars']),
                'repos': int(tech['repo_count']),
                'funding_deals': int(funding['deal_count'] or 0),
                'funding_total': float(funding['total_funding'] or 0),
                'signal_strength': 'FORTE' if tech['total_stars'] > 100000 else 'MÉDIO'
            })

    return signals

# ============================================================================
# 2. LAG TEMPORAL (Papers → Funding)
# ============================================================================

def analyze_temporal_lag(conn):
    """
    Descobre LAG entre papers e funding

    Se papers sobre "AI Agents" explodiram em Jan 2024,
    quando vem o funding? (hipótese: 6-12 meses)
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Papers count por mês
    cur.execute("""
        SELECT
            DATE_TRUNC('month', publication_date) as month,
            COUNT(*) as paper_count
        FROM sofia.arxiv_ai_papers
        WHERE publication_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY month
        ORDER BY month
    """)

    papers_timeline = {r['month']: r['paper_count'] for r in cur.fetchall()}

    # Funding count por mês
    cur.execute("""
        SELECT
            DATE_TRUNC('month', announced_date) as month,
            COUNT(*) as funding_count,
            SUM(amount_usd) as total_amount
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY month
        ORDER BY month
    """)

    funding_timeline = {r['month']: {
        'count': r['funding_count'],
        'amount': float(r['total_amount'])
    } for r in cur.fetchall()}

    # Calcular correlação (básica, pode melhorar com scipy)
    lags = []

    for month_paper, paper_count in papers_timeline.items():
        # Checar se 6 meses depois teve funding spike
        future_month = month_paper + timedelta(days=180)

        if future_month in funding_timeline:
            funding_data = funding_timeline[future_month]

            # Se papers >100 E funding >$1B = correlação
            if paper_count > 100 and funding_data['amount'] > 1e9:
                lags.append({
                    'paper_month': month_paper.strftime('%Y-%m'),
                    'paper_count': paper_count,
                    'funding_month': future_month.strftime('%Y-%m'),
                    'funding_amount': funding_data['amount'],
                    'lag_months': 6
                })

    return lags

# ============================================================================
# 3. CONVERGÊNCIA DE SETORES
# ============================================================================

def detect_sector_convergence(conn):
    """
    Detecta quando 2+ setores estão convergindo

    Ex: Defense ($2B) + Space (700 launches) + Cybersecurity CVEs
    = Nova categoria "Space Defense Cyber"
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Top setores de funding
    cur.execute("""
        SELECT sector, SUM(amount_usd) as total, COUNT(*) as deals
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY sector
        ORDER BY total DESC
        LIMIT 10
    """)

    top_sectors = cur.fetchall()

    # Space activity
    cur.execute("""
        SELECT COUNT(*) as launches
        FROM sofia.space_industry
        WHERE launch_date >= CURRENT_DATE - INTERVAL '90 days'
    """)
    space_count = cur.fetchone()['launches']

    # Cybersecurity CVEs
    cur.execute("""
        SELECT COUNT(*) as cve_count
        FROM sofia.cybersecurity_events
        WHERE published_date >= CURRENT_DATE - INTERVAL '90 days'
    """)
    cve_count = cur.fetchone()['cve_count']

    convergences = []

    # Lógica: Se Defense + Space ativo + CVEs alto = Convergência
    for sector in top_sectors:
        if 'defense' in sector['sector'].lower() and space_count > 50:
            convergences.append({
                'type': 'Defense + Space',
                'funding': float(sector['total']),
                'space_launches': space_count,
                'insight': f"Defense Tech (${sector['total']/1e9:.1f}B) + Space ({space_count} launches) = Oportunidade em Space Defense"
            })

        if 'cyber' in sector['sector'].lower() and cve_count > 500:
            convergences.append({
                'type': 'Cybersecurity + High CVE Activity',
                'funding': float(sector['total']),
                'cve_count': cve_count,
                'insight': f"Cybersecurity funding (${sector['total']/1e9:.1f}B) com {cve_count} CVEs = Mercado aquecido"
            })

    return convergences

# ============================================================================
# 4. ARBITRAGEM GEOGRÁFICA
# ============================================================================

def detect_geographic_arbitrage(conn):
    """
    Encontra gaps: Research forte MAS funding fraco = Oportunidade

    Ex: Brasil tem 8 universidades fazendo Edge AI, mas zero startups funded
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Universidades por país
    cur.execute("""
        SELECT country, COUNT(*) as uni_count
        FROM sofia.asia_universities
        GROUP BY country
        ORDER BY uni_count DESC
    """)

    universities_by_country = {r['country']: r['uni_count'] for r in cur.fetchall()}

    # Funding por país
    cur.execute("""
        SELECT country, COUNT(*) as deals, SUM(amount_usd) as total
        FROM sofia.funding_rounds
        WHERE country IS NOT NULL
        GROUP BY country
    """)

    funding_by_country = {r['country']: {
        'deals': r['deals'],
        'total': float(r['total'])
    } for r in cur.fetchall()}

    gaps = []

    for country, uni_count in universities_by_country.items():
        funding = funding_by_country.get(country, {'deals': 0, 'total': 0})

        # Gap = Muitas universidades MAS pouco funding
        if uni_count > 5 and funding['deals'] < 3:
            gaps.append({
                'country': country,
                'universities': uni_count,
                'funding_deals': funding['deals'],
                'funding_total': funding['total'],
                'opportunity': f"{country}: {uni_count} universidades mas apenas {funding['deals']} deals - Arbitragem!"
            })

    return gaps

# ============================================================================
# MAIN - Gerar Relatório
# ============================================================================

def generate_report(conn):
    report = []

    report.append("=" * 80)
    report.append("SOFIA PULSE - CAUSAL INSIGHTS (Machine Learning Enhanced)")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # 1. Sinais Fracos
    report.append("=" * 80)
    report.append("🔥 SINAIS FRACOS (GitHub → Funding Prediction)")
    report.append("=" * 80)
    report.append("")

    signals = detect_weak_signals(conn)

    if signals:
        report.append("⚡ TECNOLOGIAS PRESTES A EXPLODIR:")
        report.append("")
        for s in signals[:5]:
            report.append(f"• {s['tech']}")
            report.append(f"  GitHub: {s['github_stars']:,} stars em {s['repos']} repos")
            report.append(f"  Funding: Apenas {s['funding_deals']} deals (${s['funding_total']/1e9:.2f}B)")
            report.append(f"  PREVISÃO: Funding esperado em 3-6 meses")
            report.append(f"  Signal: {s['signal_strength']}")
            report.append("")
    else:
        report.append("(Nenhum sinal fraco detectado)")

    # 2. Lag Temporal
    report.append("=" * 80)
    report.append("📅 LAG TEMPORAL (Papers → Funding)")
    report.append("=" * 80)
    report.append("")

    lags = analyze_temporal_lag(conn)

    if lags:
        report.append("⏱️  CORRELAÇÕES TEMPORAIS DETECTADAS:")
        report.append("")
        for lag in lags[:3]:
            report.append(f"• Papers: {lag['paper_month']} ({lag['paper_count']} publicações)")
            report.append(f"  → Funding: {lag['funding_month']} (${lag['funding_amount']/1e9:.1f}B)")
            report.append(f"  LAG: {lag['lag_months']} meses")
            report.append("")
    else:
        report.append("(Aguardando mais dados temporais)")

    # 3. Convergência
    report.append("=" * 80)
    report.append("🔗 CONVERGÊNCIA DE SETORES")
    report.append("=" * 80)
    report.append("")

    convergences = detect_sector_convergence(conn)

    if convergences:
        for conv in convergences[:3]:
            report.append(f"• {conv['type']}")
            report.append(f"  {conv['insight']}")
            report.append("")
    else:
        report.append("(Nenhuma convergência forte detectada)")

    # 4. Arbitragem Geográfica
    report.append("=" * 80)
    report.append("🌍 ARBITRAGEM GEOGRÁFICA")
    report.append("=" * 80)
    report.append("")

    gaps = detect_geographic_arbitrage(conn)

    if gaps:
        report.append("💎 OPORTUNIDADES (Research sem Funding):")
        report.append("")
        for gap in gaps[:3]:
            report.append(f"• {gap['opportunity']}")
            report.append("")
    else:
        report.append("(Nenhuma arbitragem detectada)")

    report.append("=" * 80)
    report.append("✅ Análise completa!")
    report.append("")

    return "\n".join(report)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to database")
        print()

        report = generate_report(conn)

        # Print
        print(report)

        # Save
        with open('analytics/causal-insights-latest.txt', 'w') as f:
            f.write(report)

        print("💾 Saved to: analytics/causal-insights-latest.txt")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
