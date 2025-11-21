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
    'host': os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or 'localhost',
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5432'),
    'user': os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME') or 'sofia_db',
}

def get_papers_by_sector(conn, days_back=180):
    """Papers dos últimos N dias agrupados por setor"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    WITH flattened AS (
        SELECT
            primary_category,
            DATE_TRUNC('month', published_date) as month,
            unnest(keywords) as keyword
        FROM arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '%s days'
    )
    SELECT
        primary_category,
        month,
        COUNT(*) as paper_count,
        ARRAY_AGG(DISTINCT keyword) as keywords
    FROM flattened
    GROUP BY primary_category, month
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
        # AI/ML
        'cs.AI': 'Artificial Intelligence',
        'cs.LG': 'Artificial Intelligence',
        'cs.CV': 'Computer Vision',
        'cs.CL': 'NLP',
        'cs.NE': 'AI',

        # Robotics/Hardware
        'cs.RO': 'Robotics',
        'cs.SY': 'Systems',
        'cs.AR': 'Hardware',

        # Software/Web
        'cs.SE': 'Software',
        'cs.DC': 'Cloud',
        'cs.DB': 'Database',
        'cs.NI': 'Networking',
        'cs.CR': 'Cybersecurity',

        # Other CS
        'cs.HC': 'UX/Design',
        'cs.IR': 'Search',
        'cs.SI': 'Social Networks',

        # Physics/Math
        'quant-ph': 'Quantum Computing',
        'cond-mat': 'Materials',
        'physics': 'Physics',
        'math': 'Mathematics',

        # Bio/Health
        'q-bio': 'Biotech',
        'stat.ML': 'Artificial Intelligence',
    }

    # Tentar match parcial para categorias não mapeadas
    if primary_category not in mapping:
        if 'AI' in primary_category or 'ML' in primary_category:
            return 'Artificial Intelligence'
        elif 'bio' in primary_category.lower():
            return 'Biotech'
        elif 'quant' in primary_category.lower():
            return 'Quantum Computing'

    return mapping.get(primary_category, 'Technology')

def normalize_sector(sector):
    """Normaliza nome de setor para matching com keyword matching"""
    if not sector:
        return 'Other'

    sector_lower = sector.lower().strip()

    # Mapeamento fuzzy (exact matches)
    fuzzy_map = {
        'ai': 'Artificial Intelligence',
        'artificial intelligence': 'Artificial Intelligence',
        'machine learning': 'Artificial Intelligence',
        'ml': 'Artificial Intelligence',
        'deep learning': 'Artificial Intelligence',

        'robotics': 'Robotics',
        'robot': 'Robotics',
        'autonomous': 'Robotics',

        'biotech': 'Biotech',
        'biotechnology': 'Biotech',
        'healthcare': 'Biotech',
        'health': 'Biotech',
        'medical': 'Biotech',
        'pharma': 'Biotech',

        'fintech': 'Fintech',
        'finance': 'Fintech',
        'financial': 'Fintech',
        'payment': 'Fintech',
        'banking': 'Fintech',

        'cybersecurity': 'Cybersecurity',
        'security': 'Cybersecurity',
        'infosec': 'Cybersecurity',
        'cyber': 'Cybersecurity',

        'quantum': 'Quantum Computing',
        'quantum computing': 'Quantum Computing',

        'nlp': 'NLP',
        'natural language': 'NLP',

        'computer vision': 'Computer Vision',
        'vision': 'Computer Vision',
        'cv': 'Computer Vision',
        'image': 'Computer Vision',

        'cloud': 'Cloud',
        'devops': 'Cloud',
        'saas': 'Cloud',
        'infrastructure': 'Cloud',

        'space': 'Space',
        'aerospace': 'Space',
        'satellite': 'Space',

        'energy': 'Energy',
        'renewable': 'Energy',
        'solar': 'Energy',
        'battery': 'Energy',

        'ecommerce': 'E-commerce',
        'e-commerce': 'E-commerce',
        'marketplace': 'E-commerce',
        'retail': 'E-commerce',
    }

    # Try exact match first
    if sector_lower in fuzzy_map:
        return fuzzy_map[sector_lower]

    # Keyword matching (partial)
    keyword_map = {
        'ai': 'Artificial Intelligence',
        'machine': 'Artificial Intelligence',
        'learning': 'Artificial Intelligence',
        'neural': 'Artificial Intelligence',
        'robot': 'Robotics',
        'autonomous': 'Robotics',
        'bio': 'Biotech',
        'health': 'Biotech',
        'medic': 'Biotech',
        'pharma': 'Biotech',
        'fin': 'Fintech',
        'payment': 'Fintech',
        'bank': 'Fintech',
        'security': 'Cybersecurity',
        'cyber': 'Cybersecurity',
        'quantum': 'Quantum Computing',
        'language': 'NLP',
        'nlp': 'NLP',
        'vision': 'Computer Vision',
        'image': 'Computer Vision',
        'cloud': 'Cloud',
        'saas': 'Cloud',
        'space': 'Space',
        'satellite': 'Space',
        'energy': 'Energy',
        'solar': 'Energy',
        'battery': 'Energy',
        'commerce': 'E-commerce',
        'retail': 'E-commerce',
    }

    for keyword, mapped_sector in keyword_map.items():
        if keyword in sector_lower:
            return mapped_sector

    return sector.title()

def calculate_correlation(papers, funding):
    """Calcula correlação entre papers e funding com lag temporal (FLEXIBLE)"""

    # Agrupar por setor e mês
    papers_by_sector = defaultdict(lambda: defaultdict(int))
    funding_by_sector = defaultdict(lambda: defaultdict(float))

    for paper in papers:
        sector = map_paper_to_sector(paper['primary_category'])
        sector = normalize_sector(sector)
        month = paper['month']
        papers_by_sector[sector][month] += paper['paper_count']

    for fund in funding:
        sector = normalize_sector(fund['sector'])
        month = fund['month']
        funding_by_sector[sector][month] += float(fund['total_amount'] or 0)

    # Calcular lags (0-12 meses) com tolerância de ±1 mês
    correlations = []

    for sector in papers_by_sector.keys():
        # Se não tem funding neste setor, pular
        if sector not in funding_by_sector:
            continue

        for lag_months in range(0, 13):  # Expandido: 0-12 meses (era 1-6)
            lag_delta = timedelta(days=lag_months * 30)

            matches = 0
            total_papers = 0
            total_funding = 0

            for paper_month, paper_count in papers_by_sector[sector].items():
                # Janela flexível: ±1 mês de tolerância
                for month_offset in [-1, 0, 1]:
                    funding_month = paper_month + lag_delta + timedelta(days=month_offset * 30)

                    if funding_month in funding_by_sector[sector]:
                        matches += 1
                        total_papers += paper_count
                        total_funding += funding_by_sector[sector][funding_month]
                        break  # Conta apenas uma vez por paper_month

            if matches > 0:
                correlations.append({
                    'sector': sector,
                    'lag_months': lag_months,
                    'matches': matches,
                    'avg_papers': total_papers / matches,
                    'avg_funding': total_funding / matches,
                    'strength': matches * (total_funding / 1e9),  # Score
                })

    # Se não encontrou correlações temporais, criar correlações por setor (sem lag)
    if not correlations:
        for sector in papers_by_sector.keys():
            if sector in funding_by_sector:
                total_papers = sum(papers_by_sector[sector].values())
                total_funding = sum(funding_by_sector[sector].values())

                if total_papers > 0 and total_funding > 0:
                    correlations.append({
                        'sector': sector,
                        'lag_months': 0,  # No lag detected
                        'matches': len(papers_by_sector[sector]),
                        'avg_papers': total_papers / len(papers_by_sector[sector]),
                        'avg_funding': total_funding / len(funding_by_sector[sector]),
                        'strength': total_papers * (total_funding / 1e9),
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
    print("Método: Matching flexível com janela de ±1 mês, lag 0-12 meses")
    print()

    # Data summary
    papers_by_sector = defaultdict(int)
    for paper in papers:
        sector = map_paper_to_sector(paper['primary_category'])
        sector = normalize_sector(sector)
        papers_by_sector[sector] += paper['paper_count']

    funding_by_sector = defaultdict(float)
    for fund in funding:
        sector = normalize_sector(fund['sector'])
        funding_by_sector[sector] += float(fund['total_amount'] or 0)

    print(f"📊 DATA SUMMARY:")
    print(f"   Papers: {len(papers)} groups, {sum(papers_by_sector.values())} total papers")
    print(f"   Funding: {len(funding)} groups, ${sum(funding_by_sector.values())/1e9:.2f}B total")
    print(f"   Paper sectors: {len(papers_by_sector)}")
    print(f"   Funding sectors: {len(funding_by_sector)}")
    print(f"   Correlations found: {len(correlations)}")
    print()
    print("=" * 80)
    print()

    if not correlations:
        print("⚠️  NO CORRELATIONS FOUND")
        print()
        print("Possíveis razões:")
        print("   • Poucos dados históricos (precisa 6-12 meses)")
        print("   • Setores de papers e funding não coincidem")
        print("   • Timing ainda não permite detectar lag temporal")
        print()
        print("Setores em Papers:")
        for sector, count in sorted(papers_by_sector.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   • {sector}: {count} papers")
        print()
        print("Setores em Funding:")
        for sector, amount in sorted(funding_by_sector.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   • {sector}: ${amount/1e6:.1f}M")
        print()
        return

    # Top correlações
    print("🔥 TOP CORRELAÇÕES (Papers → Funding)")
    print("-" * 80)
    print(f"{'Sector':<30} {'Lag':<10} {'Matches':<10} {'Avg Papers':<12} {'Avg Funding':<15}")
    print("-" * 80)

    for corr in correlations[:15]:
        lag_str = f"{corr['lag_months']} months" if corr['lag_months'] > 0 else "concurrent"
        print(
            f"{corr['sector']:<30} "
            f"{lag_str:<10} "
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
