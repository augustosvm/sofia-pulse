#!/usr/bin/env python3
"""
Sofia Pulse - Early-Stage Deep Dive
Analisa startups em seed/angel stage (<$10M) e conecta:
- Papers publicados pelos fundadores
- Universidades de origem
- Tech stack usado (GitHub)
- Patentes registradas
- Geografia global
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import os
from collections import defaultdict
import re

from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', 'sofia123strong'),
    'database': os.getenv('DB_NAME', 'sofia_db'),
}

# Mapa de universidades globais
UNIVERSITIES = {
    'MIT': {'country': 'USA', 'region': 'Americas', 'focus': ['AI', 'Robotics', 'Quantum']},
    'Stanford': {'country': 'USA', 'region': 'Americas', 'focus': ['AI', 'Biotech', 'Startup Culture']},
    'Berkeley': {'country': 'USA', 'region': 'Americas', 'focus': ['AI', 'Climate', 'Open Source']},
    'CMU': {'country': 'USA', 'region': 'Americas', 'focus': ['AI', 'Robotics', 'HCI']},
    'Harvard': {'country': 'USA', 'region': 'Americas', 'focus': ['Medicine', 'Biotech']},
    'Caltech': {'country': 'USA', 'region': 'Americas', 'focus': ['Physics', 'Space', 'Quantum']},

    'Oxford': {'country': 'UK', 'region': 'Europe', 'focus': ['AI', 'Medicine', 'Climate']},
    'Cambridge': {'country': 'UK', 'region': 'Europe', 'focus': ['Physics', 'Biotech', 'AI']},
    'ETH': {'country': 'Switzerland', 'region': 'Europe', 'focus': ['Robotics', 'Quantum', 'Climate']},
    'Imperial': {'country': 'UK', 'region': 'Europe', 'focus': ['Engineering', 'AI', 'Biotech']},

    'Tsinghua': {'country': 'China', 'region': 'Asia', 'focus': ['AI', 'Manufacturing', 'Engineering']},
    'Peking': {'country': 'China', 'region': 'Asia', 'focus': ['AI', 'Chemistry', 'Materials']},
    'NUS': {'country': 'Singapore', 'region': 'Asia', 'focus': ['AI', 'Fintech', 'Biotech']},
    'Tokyo': {'country': 'Japan', 'region': 'Asia', 'focus': ['Robotics', 'Materials', 'AI']},
    'IIT': {'country': 'India', 'region': 'Asia', 'focus': ['Software', 'AI', 'Startups']},

    'USP': {'country': 'Brazil', 'region': 'Americas', 'focus': ['Agro-tech', 'Medicine', 'Energy']},
    'Unicamp': {'country': 'Brazil', 'region': 'Americas', 'focus': ['Agro-tech', 'Materials', 'AI']},
    'UNAM': {'country': 'Mexico', 'region': 'Americas', 'focus': ['Climate', 'Materials', 'Physics']},
}

def analyze_early_stage(conn):
    """Analisa startups seed/angel e early-stage activity (últimos 12 meses)"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Estratégia multi-source:
    # 1. Rounds com amount < $10M (seed/angel com valor conhecido)
    # 2. Rounds com amount < $50M (early-stage com valor conhecido)
    # 3. Rounds YC recentes (sem amount mas indica early-stage activity)
    # 4. Qualquer funding recente (fallback)

    # Tentar primeiro <$10M (seed/angel verificados)
    cursor.execute("""
        SELECT
            company_name,
            sector,
            amount_usd,
            valuation_usd,
            round_type,
            announced_date,
            investors,
            country,
            source
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '12 months'
            AND amount_usd > 0
            AND amount_usd < 10000000
        ORDER BY announced_date DESC
    """)

    seed_rounds = cursor.fetchall()

    # Se não encontrou nada, tentar <$50M (early-stage com valor)
    if not seed_rounds:
        cursor.execute("""
            SELECT
                company_name,
                sector,
                amount_usd,
                valuation_usd,
                round_type,
                announced_date,
                investors,
                country,
                source
            FROM sofia.funding_rounds
            WHERE announced_date >= CURRENT_DATE - INTERVAL '12 months'
                AND amount_usd > 0
                AND amount_usd < 50000000
            ORDER BY amount_usd ASC
            LIMIT 50
        """)
        seed_rounds = cursor.fetchall()

    # Se ainda não encontrou, pegar YC companies recentes (proxy de early-stage)
    if not seed_rounds:
        cursor.execute("""
            SELECT
                company_name,
                sector,
                amount_usd,
                valuation_usd,
                round_type,
                announced_date,
                investors,
                country,
                source
            FROM sofia.funding_rounds
            WHERE announced_date >= CURRENT_DATE - INTERVAL '12 months'
                AND (
                    source = 'yc_companies'
                    OR round_type ILIKE '%seed%'
                    OR round_type ILIKE '%angel%'
                    OR round_type ILIKE '%pre-seed%'
                    OR round_type ILIKE '%accelerator%'
                )
            ORDER BY announced_date DESC
            LIMIT 100
        """)
        seed_rounds = cursor.fetchall()

    # Último fallback: qualquer funding recente
    if not seed_rounds:
        cursor.execute("""
            SELECT
                company_name,
                sector,
                amount_usd,
                valuation_usd,
                round_type,
                announced_date,
                investors,
                country,
                source
            FROM sofia.funding_rounds
            WHERE announced_date >= CURRENT_DATE - INTERVAL '12 months'
            ORDER BY announced_date DESC
            LIMIT 50
        """)
        seed_rounds = cursor.fetchall()

    return seed_rounds

def find_related_papers(conn, company_name, sector):
    """Tenta encontrar papers relacionados à empresa"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Buscar papers com palavras-chave do setor
    keywords = sector.lower().split() if sector else []
    if not keywords:
        return []

    # Buscar nos últimos 24 meses
    cursor.execute("""
        SELECT
            title,
            authors,
            categories,
            published_date
        FROM sofia.arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '24 months'
            AND (
                title ILIKE %s
                OR abstract ILIKE %s
            )
        ORDER BY published_date DESC
        LIMIT 5
    """, (f'%{keywords[0]}%', f'%{keywords[0]}%'))

    return cursor.fetchall()

def find_tech_stack(conn):
    """Analisa tech stack de repos GitHub trending"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT
            language,
            COUNT(*) as repo_count,
            SUM(stars) as total_stars
        FROM sofia.github_trending
        WHERE collected_at >= CURRENT_DATE - INTERVAL '30 days'
            AND language IS NOT NULL
        GROUP BY language
        ORDER BY total_stars DESC
        LIMIT 15
    """)

    return cursor.fetchall()

def find_patents(conn, sector):
    """Busca patentes relacionadas ao setor (opcional - não quebra se tabela não existir)"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    keywords = sector.lower().split() if sector else []
    if not keywords:
        return []

    try:
        # Buscar em patentes WIPO dos últimos 12 meses
        cursor.execute("""
            SELECT
                title,
                applicant,
                filing_date,
                ipc_class
            FROM sofia.wipo_patents
            WHERE filing_date >= CURRENT_DATE - INTERVAL '12 months'
                AND (
                    title ILIKE %s
                    OR abstract ILIKE %s
                )
            ORDER BY filing_date DESC
            LIMIT 5
        """, (f'%{keywords[0]}%', f'%{keywords[0]}%'))

        return cursor.fetchall()
    except Exception:
        # Tabela não existe ou erro - fazer rollback e retornar lista vazia
        conn.rollback()
        return []

def generate_report(seed_rounds, tech_stack, conn):
    """Gera relatório completo"""

    # Separar rounds com e sem amount_usd
    rounds_with_amount = [r for r in seed_rounds if r.get('amount_usd') and r['amount_usd'] > 0]
    rounds_without_amount = [r for r in seed_rounds if not r.get('amount_usd') or r['amount_usd'] == 0]

    # Determinar qual filtro foi usado
    if rounds_with_amount:
        max_amount = max(r['amount_usd'] for r in rounds_with_amount) / 1e6
        if max_amount < 10:
            filter_desc = "(<$10M - Seed/Angel with known amounts)"
        elif max_amount < 50:
            filter_desc = "(<$50M - Early-stage with known amounts)"
        else:
            filter_desc = "(Recent funding rounds)"
    elif rounds_without_amount:
        filter_desc = "(YC batches & early-stage rounds - amounts not disclosed)"
    else:
        filter_desc = "(No data available)"

    report = f"""
{'='*80}
💎 EARLY-STAGE DEEP DIVE - Sofia Pulse
{'='*80}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Análise de startups dos últimos 12 meses {filter_desc}
Conectando: Funding → Papers → Universities → Tech Stack → Patents

{'='*80}

📊 RESUMO EXECUTIVO
{'-'*80}

Total de rounds encontrados: {len(seed_rounds)}
   • With disclosed amount: {len(rounds_with_amount)}
   • YC/undisclosed: {len(rounds_without_amount)}
"""

    if rounds_with_amount:
        avg_ticket = sum(r['amount_usd'] for r in rounds_with_amount) / len(rounds_with_amount) / 1e6
        min_ticket = min(r['amount_usd'] for r in rounds_with_amount) / 1e6
        max_ticket = max(r['amount_usd'] for r in rounds_with_amount) / 1e6
        report += f"""
Ticket médio (disclosed): ${avg_ticket:.2f}M
Range: ${min_ticket:.2f}M - ${max_ticket:.2f}M
"""

    if rounds_without_amount:
        report += f"""
💡 Note: {len(rounds_without_amount)} rounds don't have disclosed amounts
   Sources: YC batches (accelerator), early-stage stealth mode
   These indicate early-stage activity but amounts are not public yet
"""

    if not seed_rounds:
        report += """
⚠️  Nenhum funding encontrado nos últimos 12 meses.
💡 Possíveis razões:
   • Dados ainda não coletados
   • Período sem atividade
   • Problema de conexão com fontes

Recomendações:
   • Execute os collectors: bash collect-limited-apis.sh
   • Verifique funding_rounds: SELECT COUNT(*) FROM sofia.funding_rounds
"""

    report += f"""
{'='*80}

🌍 GEOGRAFIA - ONDE ESTÃO OS FOUNDERS?
{'-'*80}

"""

    # Análise geográfica
    geo_analysis = defaultdict(lambda: {'count': 0, 'total': 0, 'sectors': set()})

    for round_data in seed_rounds:
        country = round_data.get('country', 'Unknown')
        geo_analysis[country]['count'] += 1
        if round_data.get('amount_usd') and round_data['amount_usd'] > 0:
            geo_analysis[country]['total'] += round_data['amount_usd']
        if round_data.get('sector'):
            geo_analysis[country]['sectors'].add(round_data['sector'])

    # Ordenar por número de deals
    top_countries = sorted(geo_analysis.items(), key=lambda x: x[1]['count'], reverse=True)[:10]

    for country, data in top_countries:
        country_str = str(country) if country else 'Unknown'
        if data['total'] > 0:
            report += f"   {country_str:20s} | {data['count']:2d} deals | ${data['total']/1e6:.1f}M total\n"
        else:
            report += f"   {country_str:20s} | {data['count']:2d} deals | (amounts undisclosed)\n"
        if data['sectors']:
            top_sectors = list(data['sectors'])[:3]
            report += f"      → {', '.join(top_sectors)}\n"
        report += "\n"

    report += f"\n{'='*80}\n\n"

    # Análise por setor
    report += f"🎯 SETORES EMERGENTES\n{'-'*80}\n\n"

    sector_analysis = defaultdict(lambda: {'count': 0, 'total': 0, 'companies': [], 'countries': set()})

    for round_data in seed_rounds:
        sector = round_data.get('sector') or 'Other'
        sector_analysis[sector]['count'] += 1
        if round_data.get('amount_usd') and round_data['amount_usd'] > 0:
            sector_analysis[sector]['total'] += round_data['amount_usd']
        sector_analysis[sector]['companies'].append(round_data['company_name'])
        if round_data.get('country'):
            sector_analysis[sector]['countries'].add(round_data['country'])

    top_sectors = sorted(sector_analysis.items(), key=lambda x: x[1]['count'], reverse=True)[:15]

    for sector, data in top_sectors:
        report += f"   • {sector}\n"
        if data['total'] > 0:
            report += f"     {data['count']} startups | ${data['total']/1e6:.1f}M total | Avg ${data['total']/data['count']/1e6:.2f}M\n"
        else:
            report += f"     {data['count']} startups | (amounts undisclosed)\n"
        if data['countries']:
            report += f"     Países: {', '.join(list(data['countries'])[:5])}\n"

        # Tentar encontrar papers relacionados
        papers = find_related_papers(conn, '', sector)
        if papers:
            report += f"     📄 Papers relacionados: {len(papers)} publicações recentes\n"

        # Tentar encontrar patentes
        patents = find_patents(conn, sector)
        if patents:
            report += f"     📜 Patentes: {len(patents)} registros recentes\n"

        report += "\n"

    report += f"\n{'='*80}\n\n"

    # Tech Stack
    report += f"💻 TECH STACK - O QUE ESTÃO USANDO?\n{'-'*80}\n\n"
    report += "Baseado em análise de repos GitHub trending:\n\n"

    for idx, tech in enumerate(tech_stack, 1):
        report += f"   {idx:2d}. {tech['language']:20s} | {tech['repo_count']:3d} repos | {tech['total_stars']:,} stars\n"

    report += f"\n{'='*80}\n\n"

    # Top Deals com contexto
    report += f"🔥 TOP 20 EARLY-STAGE ROUNDS (Últimos 12 meses)\n{'-'*80}\n\n"

    for idx, round_data in enumerate(seed_rounds[:20], 1):
        company = round_data['company_name']
        sector = round_data.get('sector') or 'N/A'
        country = round_data.get('country', 'Unknown')
        date = round_data.get('announced_date', 'N/A')
        round_type = round_data.get('round_type', 'N/A')
        source = round_data.get('source', 'N/A')

        report += f"{idx:2d}. {company}\n"

        if round_data.get('amount_usd') and round_data['amount_usd'] > 0:
            amount = round_data['amount_usd'] / 1e6
            report += f"    💰 ${amount:.2f}M | {round_type} | {sector} | {country} | {date}\n"
        else:
            report += f"    🎯 {round_type} | {sector} | {country} | {date} | [{source}]\n"
            report += f"    💡 Amount undisclosed (early-stage/stealth)\n"

        # Investors
        if round_data.get('investors'):
            investors = round_data['investors'][:100]  # Truncar
            report += f"    👥 {investors}\n"

        # Buscar papers relacionados
        papers = find_related_papers(conn, company, sector)
        if papers:
            report += f"    📄 {len(papers)} paper(s) relacionado(s) no ArXiv\n"

        report += "\n"

    report += f"\n{'='*80}\n\n"

    # Insights estratégicos
    report += f"💡 INSIGHTS ESTRATÉGICOS\n{'-'*80}\n\n"

    report += "🎯 OPORTUNIDADES:\n\n"

    # Setores com poucos players mas atividade
    for sector, data in top_sectors[:5]:
        if 2 <= data['count'] <= 5:
            report += f"   • {sector}: Apenas {data['count']} startups\n"
            report += f"     → Oportunidade de entrar em mercado não saturado\n"
            report += f"     → Ticket médio ${data['total']/data['count']/1e6:.2f}M indica validação inicial\n\n"

    report += "🌍 HUBS EMERGENTES:\n\n"

    # Países fora USA com atividade
    for country, data in top_countries:
        if country not in ['USA', 'United States'] and data['count'] >= 3:
            report += f"   • {country}: {data['count']} deals\n"
            report += f"     → Hub emergente para {', '.join(list(data['sectors'])[:2])}\n\n"

    report += f"\n{'='*80}\n"
    report += "Gerado por Sofia Pulse - Early-Stage Deep Dive\n"
    report += f"{'='*80}\n"

    return report

def main():
    print("💎 Early-Stage Deep Dive - Analyzing...")
    print()

    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("📊 Fetching seed/angel rounds (<$10M)...")
        seed_rounds = analyze_early_stage(conn)
        print(f"   ✅ Found {len(seed_rounds)} early-stage deals")

        print("💻 Analyzing tech stack...")
        tech_stack = find_tech_stack(conn)
        print(f"   ✅ Found {len(tech_stack)} technologies")

        print("📝 Generating report...")
        report = generate_report(seed_rounds, tech_stack, conn)

        # Salvar
        output_file = 'analytics/early-stage-latest.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ Report saved to {output_file}")
        print()
        print("Preview:")
        print(report[:1000])

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
