#!/usr/bin/env python3
"""
Correlação Papers ↔ Funding (Lag Analysis)

Detecta quanto tempo leva entre:
- Papers acadêmicos publicados
- Funding rounds em startups do mesmo setor

LAG ESPERADO: 6-12 meses (papers → funding)
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
    'database': os.getenv('POSTGRES_DB', 'sofia_db'),
}

def get_papers_by_sector(conn, days_back=180):
    """Papers dos últimos N dias agrupados por setor"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT
        primary_category,
        DATE_TRUNC('month', published_date) as month,
        COUNT(*) as paper_count,
        ARRAY_AGG(DISTINCT unnest(keywords)) as keywords
    FROM arxiv_ai_papers
    WHERE published_date >= CURRENT_DATE - INTERVAL '%s days'
    GROUP BY primary_category, DATE_TRUNC('month', published_date)
    ORDER BY month DESC, paper_count DESC;
    """ % days_back

    cursor.execute(query)
    return cursor.fetchall()

def get_funding_by_sector(conn, days_back=180):
    """Funding rounds dos últimos N dias agrupados por setor"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT
        sector,
        DATE_TRUNC('month', announced_date) as month,
        COUNT(*) as deal_count,
        SUM(amount_usd) as total_amount,
        AVG(amount_usd) as avg_amount
    FROM sofia.funding_rounds
    WHERE announced_date >= CURRENT_DATE - INTERVAL '%s days'
        AND amount_usd > 0
    GROUP BY sector, DATE_TRUNC('month', announced_date)
    ORDER BY month DESC, total_amount DESC;
    """ % days_back

    cursor.execute(query)
    return cursor.fetchall()

def map_paper_to_sector(primary_category):
    """Mapeia categoria ArXiv para setor de mercado"""
    mapping = {
        'cs.AI': 'Artificial Intelligence',
        'cs.LG': 'Artificial Intelligence',
        'cs.CV': 'Artificial Intelligence',
        'cs.CL': 'Artificial Intelligence',
        'cs.RO': 'Robotics',
        'cs.NE': 'Artificial Intelligence',
    }
    return mapping.get(primary_category, 'Technology')

def calculate_correlation(papers, funding):
    """Calcula correlação entre papers e funding com lag temporal"""

    # Agrupar por setor e mês
    papers_by_sector = defaultdict(lambda: defaultdict(int))
    funding_by_sector = defaultdict(lambda: defaultdict(float))

    for paper in papers:
        sector = map_paper_to_sector(paper['primary_category'])
        month = paper['month']
        papers_by_sector[sector][month] += paper['paper_count']

    for fund in funding:
        sector = fund['sector']
        month = fund['month']
        funding_by_sector[sector][month] += float(fund['total_amount'] or 0)

    # Calcular lags (1-6 meses)
    correlations = []

    for sector in papers_by_sector.keys():
        for lag_months in range(1, 7):
            lag_delta = timedelta(days=lag_months * 30)

            matches = 0
            total_papers = 0
            total_funding = 0

            for paper_month, paper_count in papers_by_sector[sector].items():
                funding_month = paper_month + lag_delta

                if funding_month in funding_by_sector[sector]:
                    matches += 1
                    total_papers += paper_count
                    total_funding += funding_by_sector[sector][funding_month]

            if matches > 0:
                correlations.append({
                    'sector': sector,
                    'lag_months': lag_months,
                    'matches': matches,
                    'avg_papers': total_papers / matches,
                    'avg_funding': total_funding / matches,
                    'strength': matches * (total_funding / 1e9),  # Score
                })

    return sorted(correlations, key=lambda x: x['strength'], reverse=True)

def print_report(correlations, papers, funding):
    """Imprime relatório de correlações"""

    print("=" * 80)
    print("CORRELAÇÃO: PAPERS ↔ FUNDING (Lag Analysis)")
    print("=" * 80)
    print()
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Hipótese: Papers acadêmicos precedem funding em 6-12 meses")
    print()
    print("=" * 80)
    print()

    # Top correlações
    print("🔥 TOP CORRELAÇÕES (Papers → Funding)")
    print("-" * 80)
    print(f"{'Sector':<30} {'Lag':<10} {'Matches':<10} {'Avg Papers':<12} {'Avg Funding':<15}")
    print("-" * 80)

    for corr in correlations[:15]:
        print(
            f"{corr['sector']:<30} "
            f"{corr['lag_months']} months  "
            f"{corr['matches']:<10} "
            f"{corr['avg_papers']:<12.1f} "
            f"${corr['avg_funding']/1e6:<14.1f}M"
        )

    print()
    print("=" * 80)
    print()

    # Insights por lag
    print("📊 INSIGHTS POR LAG TEMPORAL:")
    print()

    lag_summary = defaultdict(lambda: {'count': 0, 'total_funding': 0})
    for corr in correlations:
        lag_summary[corr['lag_months']]['count'] += corr['matches']
        lag_summary[corr['lag_months']]['total_funding'] += corr['avg_funding'] * corr['matches']

    for lag in sorted(lag_summary.keys()):
        data = lag_summary[lag]
        print(f"   {lag} months lag: {data['count']} correlations, ${data['total_funding']/1e9:.2f}B total funding")

    print()
    print("=" * 80)
    print()

    # Papers sem funding
    print("💡 DARK HORSES (Papers SEM funding correspondente):")
    print()
    print("Setores com muitos papers mas pouco funding = oportunidades!")
    print()

    papers_by_sector = defaultdict(int)
    for paper in papers:
        sector = map_paper_to_sector(paper['primary_category'])
        papers_by_sector[sector] += paper['paper_count']

    funding_by_sector = defaultdict(float)
    for fund in funding:
        funding_by_sector[fund['sector']] += float(fund['total_amount'] or 0)

    dark_horses = []
    for sector, paper_count in papers_by_sector.items():
        funding_amt = funding_by_sector.get(sector, 0)
        ratio = paper_count / (funding_amt / 1e9 + 0.1)  # Papers per $1B

        if paper_count >= 5:
            dark_horses.append({
                'sector': sector,
                'papers': paper_count,
                'funding': funding_amt,
                'ratio': ratio,
            })

    for dh in sorted(dark_horses, key=lambda x: x['ratio'], reverse=True)[:10]:
        print(
            f"   {dh['sector']}: "
            f"{dh['papers']} papers, "
            f"${dh['funding']/1e9:.2f}B funding "
            f"(ratio: {dh['ratio']:.1f} papers/$1B)"
        )

    print()
    print("=" * 80)
    print()
    print("✅ Analysis complete!")
    print()

def main():
    print("🔗 Connecting to database...")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected")
        print()

        print("📊 Collecting papers data...")
        papers = get_papers_by_sector(conn, days_back=365)
        print(f"   ✅ {len(papers)} paper groups")
        print()

        print("💰 Collecting funding data...")
        funding = get_funding_by_sector(conn, days_back=365)
        print(f"   ✅ {len(funding)} funding groups")
        print()

        print("🧮 Calculating correlations...")
        correlations = calculate_correlation(papers, funding)
        print(f"   ✅ {len(correlations)} correlations found")
        print()

        print_report(correlations, papers, funding)

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
