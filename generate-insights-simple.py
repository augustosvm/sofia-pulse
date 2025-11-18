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
    insights += "\n🔥 TOP RODADAS DE INVESTIMENTO:\n\n"
    for company, sector, amount, valuation, round_type in funding_data[:10]:
        amount_b = amount / 1_000_000_000 if amount else 0
        val_b = valuation / 1_000_000_000 if valuation else 0
        insights += f"   • {company} ({sector})\n"
        insights += f"     {round_type} - ${amount_b:.1f}B | Valuation: ${val_b:.1f}B\n\n"

    # Análise por setor
    cur.execute("""
        SELECT sector,
               COUNT(*) as deals,
               SUM(amount_usd) as total_invested
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY sector
        ORDER BY total_invested DESC
    """)
    sectors = cur.fetchall()

    insights += "\n📊 INVESTIMENTO POR SETOR:\n\n"
    for sector, deals, total in sectors:
        total_b = total / 1_000_000_000 if total else 0
        insights += f"   {sector:30s} | {deals:2d} deals | ${total_b:6.1f}B\n"

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
    # Encontrar tendências
    ai_deals = sum(1 for _, sector, _, _, _ in funding_data if sector and ('AI' in sector or 'Intelligence' in sector))
    defense_deals = sum(1 for _, sector, _, _, _ in funding_data if sector and ('Defense' in sector or 'Military' in sector))
    fintech_deals = sum(1 for _, sector, _, _, _ in funding_data if sector and ('Fintech' in sector or 'Finance' in sector))

    insights += f"🎯 SETORES EM ALTA:\n\n"
    if ai_deals > 0:
        insights += f"   • Inteligência Artificial: {ai_deals} rodadas\n"
        insights += f"     > IA está dominando os investimentos globais\n"
        insights += f"     > Grandes valuations (>$10B) indicam maturidade do setor\n\n"

    if defense_deals > 0:
        insights += f"   • Defense Tech: {defense_deals} rodadas\n"
        insights += f"     > Drones militares e AI defense em alta\n"
        insights += f"     > Oportunidade: empresas com contratos governamentais\n\n"

    if fintech_deals > 0:
        insights += f"   • Fintech: {fintech_deals} rodadas\n"
        insights += f"     > América Latina continua atraindo capital\n"
        insights += f"     > Nubank como unicórnio regional consolidado\n\n"

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
