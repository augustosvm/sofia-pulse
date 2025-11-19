#!/usr/bin/env python3
"""
Sofia Pulse - Gerador de Insights Simples
Gera insights básicos com os dados coletados
"""

import psycopg2
from datetime import datetime, timedelta
import os
import json

# Conectar ao banco
conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432'),
    database=os.getenv('DB_NAME', 'sofia_db'),
    user=os.getenv('DB_USER', 'sofia'),
    password=os.getenv('DB_PASSWORD', 'sofia123strong')
)

cur = conn.cursor()

# Criar diretório de insights
os.makedirs('analytics/premium-insights', exist_ok=True)

# Coletar dados
print("📊 Coletando dados...")

# Funding rounds
cur.execute("""
    SELECT company_name, sector, amount_usd, valuation_usd, round_type
    FROM sofia.funding_rounds
    WHERE announced_date >= CURRENT_DATE - INTERVAL '30 days'
    ORDER BY amount_usd DESC
""")
funding_data = cur.fetchall()

# B3 stocks (última coleta de cada ticker)
cur.execute("""
    WITH latest_data AS (
        SELECT ticker, company, price, change_pct, volume,
               ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY collected_at DESC) as rn
        FROM market_data_brazil
        WHERE collected_at >= CURRENT_DATE - INTERVAL '30 days'
    )
    SELECT ticker, company, price, change_pct, volume
    FROM latest_data
    WHERE rn = 1
    ORDER BY change_pct DESC
""")
b3_data = cur.fetchall()

# Gerar insights
insights = f"""
════════════════════════════════════════════════════════════════
   🌍 SOFIA PULSE - PREMIUM INSIGHTS
   Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}
════════════════════════════════════════════════════════════════

📈 RESUMO EXECUTIVO
-------------------------------------------------------------------
Análise dos últimos 30 dias de atividade no mercado global de
inovação, investimentos e ações de alta performance.


💰 INVESTIMENTOS RECENTES ({len(funding_data)} rodadas)
-------------------------------------------------------------------
"""

if funding_data:
    # Dividir em oceano vermelho (>$100M), growth ($10M-$100M) e seed (<$10M)
    red_ocean = [(c, s, a, v, r) for c, s, a, v, r in funding_data if a and a >= 100_000_000]
    growth_stage = [(c, s, a, v, r) for c, s, a, v, r in funding_data if a and 10_000_000 <= a < 100_000_000]
    seed_stage = [(c, s, a, v, r) for c, s, a, v, r in funding_data if a and a < 10_000_000]

    insights += "\n🔥 OCEANO VERMELHO (>$100M) - Late Stage:\n\n"
    for company, sector, amount, valuation, round_type in red_ocean[:8]:
        amount_m = amount / 1_000_000 if amount else 0
        val_b = valuation / 1_000_000_000 if valuation else 0
        insights += f"   • {company} ({sector})\n"
        insights += f"     {round_type} - ${amount_m:.0f}M"
        if val_b > 0:
            insights += f" | Valuation: ${val_b:.1f}B"
        insights += "\n\n"

    insights += "\n📈 GROWTH STAGE ($10M-$100M) - Series A/B:\n\n"
    for company, sector, amount, valuation, round_type in growth_stage[:12]:
        amount_m = amount / 1_000_000 if amount else 0
        insights += f"   • {company} ({sector})\n"
        insights += f"     {round_type} - ${amount_m:.1f}M\n\n"

    insights += "\n💎 SEED/ANGEL (<$10M) - Early Stage:\n\n"
    for company, sector, amount, valuation, round_type in seed_stage[:20]:
        amount_m = amount / 1_000_000 if amount else 0
        insights += f"   • {company} ({sector})\n"
        insights += f"     {round_type} - ${amount_m:.2f}M\n\n"

    # Análise por setor
    cur.execute("""
        SELECT sector,
               COUNT(*) as deals,
               SUM(amount_usd) as total_invested
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY sector
        ORDER BY total_invested DESC
        LIMIT 15
    """)
    sectors = cur.fetchall()

    insights += "\n📊 INVESTIMENTO POR SETOR (Top 15):\n\n"
    for sector, deals, total in sectors:
        total_b = total / 1_000_000_000 if total else 0
        insights += f"   {sector:35s} | {deals:2d} deals | ${total_b:6.2f}B\n"

insights += "\n\n📈 MERCADO B3 (BRASIL)\n"
insights += "-------------------------------------------------------------------\n"

if b3_data:
    insights += "\n🔥 TOP AÇÕES POR PERFORMANCE:\n\n"
    for ticker, name, price, change, volume in b3_data[:10]:
        symbol = "📈" if change > 0 else "📉"
        insights += f"   {symbol} {ticker:8s} | {name:20s} | {change:+6.2f}%\n"
else:
    insights += "\n⚠️  Sem dados de B3 coletados recentemente\n"

insights += "\n\n💎 INSIGHTS ESTRATÉGICOS\n"
insights += "-------------------------------------------------------------------\n\n"

if funding_data:
    # Análise profunda por categoria
    from collections import defaultdict

    sector_analysis = defaultdict(lambda: {'count': 0, 'total': 0, 'avg': 0, 'companies': []})

    for company, sector, amount, valuation, round_type in funding_data:
        if sector:
            sector_analysis[sector]['count'] += 1
            sector_analysis[sector]['total'] += amount if amount else 0
            sector_analysis[sector]['companies'].append(company)

    # Calcular médias
    for sector in sector_analysis:
        if sector_analysis[sector]['count'] > 0:
            sector_analysis[sector]['avg'] = sector_analysis[sector]['total'] / sector_analysis[sector]['count']

    # Ordenar por total investido
    top_sectors = sorted(sector_analysis.items(), key=lambda x: x[1]['total'], reverse=True)[:10]

    insights += f"🎯 SETORES EM ALTA (Top 10 por capital investido):\n\n"

    # Insights dinâmicos baseados em keywords
    sector_insights = {
        'AI': 'Competição acirrada entre OpenAI, Anthropic, DeepMind',
        'Intelligence': 'Empresas de LLM dominam valuations bilionárias',
        'Defense': 'Geopolítica global impulsiona demanda por autonomia militar',
        'Military': 'Drones e AI tactical systems em crescimento exponencial',
        'Fintech': 'América Latina e África como novos hubs de inovação',
        'Finance': 'Automação bancária e embedded finance em alta',
        'Biotech': 'CRISPR e AI drug discovery convergindo',
        'Health': 'Telemedicina e wearables pós-pandemia',
        'Climate': 'Carbon capture e green hydrogen atraindo capital',
        'Energy': 'Transição energética: baterias, solar, nuclear modular',
        'Robotics': 'Humanoides (Tesla Optimus, Figure AI) virando realidade',
        'Automation': 'RPA + AI agents substituindo workflows manuais',
        'Quantum': 'Corrida quântica: IBM, Google, startups chinesas',
        'Space': 'SpaceX consolidado, Blue Origin/Rocket Lab emergindo',
        'Crypto': 'Após crash: foco em infraestrutura e stablecoins',
        'Web3': 'Social graphs descentralizados ganhando tração',
        'Gaming': 'AAA studios + AI-generated content',
        'EdTech': 'AI tutors personalizados democratizando educação',
        'Agro': 'Vertical farming e precision agriculture com drones',
        'Manufacturing': 'Indústria 4.0: digital twins e predictive maintenance'
    }

    for sector, data in top_sectors:
        total_b = data['total'] / 1_000_000_000
        avg_m = data['avg'] / 1_000_000

        insights += f"   • {sector}: {data['count']} rodadas | ${total_b:.2f}B total\n"
        insights += f"     Ticket médio: ${avg_m:.1f}M\n"

        # Buscar insight relevante
        insight_found = False
        for keyword, insight in sector_insights.items():
            if keyword.lower() in sector.lower():
                insights += f"     → {insight}\n"
                insight_found = True
                break

        if not insight_found:
            # Insight genérico baseado em dados
            if data['count'] >= 3:
                insights += f"     → Setor aquecido com múltiplos players competindo\n"
            elif total_b >= 1.0:
                insights += f"     → Mega-rounds indicam maturidade e consolidação\n"
            else:
                insights += f"     → Oportunidade emergente para early investors\n"

        insights += "\n"

insights += """

═══════════════════════════════════════════════════════════════
Gerado por Sofia Pulse - Premium Insights Engine
═══════════════════════════════════════════════════════════════
"""

# Salvar insights
with open('analytics/premium-insights/latest-geo.txt', 'w') as f:
    f.write(insights)

with open('analytics/premium-insights/latest-geo.md', 'w') as f:
    f.write(insights)

print("✅ Insights gerados com sucesso!")
print(f"📄 Arquivo: analytics/premium-insights/latest-geo.txt")
print(f"\nPreview:\n{insights[:500]}...\n")

# Exportar CSVs para email
print("\n📤 Exportando CSVs...")

# Funding CSV
cur.execute("""
    SELECT company_name, sector, amount_usd, valuation_usd, round_type, announced_date
    FROM sofia.funding_rounds
    WHERE announced_date >= CURRENT_DATE - INTERVAL '30 days'
    ORDER BY announced_date DESC
""")
with open('analytics/premium-insights/funding_rounds_30d.csv', 'w') as f:
    f.write("company_name,sector,amount_usd,valuation_usd,round_type,announced_date\n")
    for row in cur.fetchall():
        f.write(','.join(str(x) if x is not None else '' for x in row) + '\n')

# B3 CSV (última coleta de cada ticker)
cur.execute("""
    WITH latest_data AS (
        SELECT ticker, company, price, change_pct, volume, collected_at,
               ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY collected_at DESC) as rn
        FROM market_data_brazil
        WHERE collected_at >= CURRENT_DATE - INTERVAL '30 days'
    )
    SELECT ticker, company, price, change_pct, volume, collected_at
    FROM latest_data
    WHERE rn = 1
    ORDER BY change_pct DESC
""")
with open('analytics/premium-insights/market_b3_30d.csv', 'w') as f:
    f.write("ticker,company,price,change_pct,volume,collected_at\n")
    for row in cur.fetchall():
        f.write(','.join(str(x) if x is not None else '' for x in row) + '\n')

print("✅ CSVs exportados!")

conn.close()
