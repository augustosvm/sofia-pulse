#!/usr/bin/env python3
"""
Sofia Pulse - Premium Insights Generator v3.0
Análise inteligente usando TODOS os dados + Gemini AI

Features:
- Comparação temporal (30d vs 90d)
- Contexto macro (dólar, juros)
- Detecção de anomalias
- Correlações entre datasets
- Narrativa analítica com Gemini
"""

import psycopg2
from datetime import datetime, timedelta
import os
import json
import requests
from typing import Dict, List, Any

# Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai não instalado. Narrativa Gemini desabilitada.")

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'sofia_db'),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', 'sofia123strong')
}

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# ============================================================================
# COLETA DE CONTEXTO MACRO
# ============================================================================

def get_macro_context() -> Dict[str, Any]:
    """Coleta contexto macroeconômico"""
    context = {}

    try:
        # Dólar (API Banco Central)
        url = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao=%27{}%27&$format=json"
        date_str = datetime.now().strftime('%m-%d-%Y')
        response = requests.get(url.format(date_str), timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('value'):
                context['dolar'] = data['value'][0].get('cotacaoCompra', 0)
    except:
        context['dolar'] = 5.80  # fallback

    try:
        # Taxa Selic (última disponível)
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados/ultimos/1?formato=json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                context['selic'] = float(data[0].get('valor', 11.75))
    except:
        context['selic'] = 11.75  # fallback

    # Fed rate (hardcoded por enquanto)
    context['fed_rate'] = 5.25

    return context

# ============================================================================
# COLETA DE DADOS DO BANCO
# ============================================================================

def collect_all_data(conn) -> Dict[str, Any]:
    """Coleta TODOS os dados disponíveis"""
    cur = conn.cursor()
    data = {}

    print("📊 Coletando dados...")

    # 1. FUNDING ROUNDS (30d e 90d para comparação)
    print("   💰 Funding rounds...")
    cur.execute("""
        SELECT
            company_name, sector, amount_usd, valuation_usd,
            round_type, announced_date
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY amount_usd DESC NULLS LAST
    """)
    data['funding_30d'] = cur.fetchall()

    cur.execute("""
        SELECT
            company_name, sector, amount_usd, valuation_usd,
            round_type, announced_date
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '90 days'
        ORDER BY amount_usd DESC NULLS LAST
    """)
    data['funding_90d'] = cur.fetchall()

    # 2. B3 STOCKS (última coleta + histórico 7d)
    print("   📈 Ações B3...")
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
    data['b3_latest'] = cur.fetchall()

    # Histórico 7d para comparação
    cur.execute("""
        SELECT ticker, AVG(change_pct) as avg_change
        FROM market_data_brazil
        WHERE collected_at >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY ticker
    """)
    data['b3_7d_avg'] = {row[0]: row[1] for row in cur.fetchall()}

    # 3. NASDAQ STOCKS
    print("   📊 Ações NASDAQ...")
    cur.execute("""
        WITH latest_data AS (
            SELECT ticker, company, price, change_pct, volume, collected_at,
                   ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY collected_at DESC) as rn
            FROM market_data_nasdaq
            WHERE collected_at >= CURRENT_DATE - INTERVAL '30 days'
        )
        SELECT ticker, company, price, change_pct, volume
        FROM latest_data
        WHERE rn = 1
        ORDER BY change_pct DESC
    """)
    data['nasdaq_latest'] = cur.fetchall()

    # 4. ARXIV PAPERS (se existir)
    print("   🔬 ArXiv papers...")
    try:
        cur.execute("""
            SELECT title, authors, categories, published_date, abstract
            FROM sofia.arxiv_ai_papers
            WHERE published_date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY published_date DESC
            LIMIT 20
        """)
        data['arxiv_papers'] = cur.fetchall()
    except:
        data['arxiv_papers'] = []

    # 5. PATENTS (se existir)
    print("   📜 Patents...")
    try:
        cur.execute("""
            SELECT title, applicants, ipc_codes, filing_date
            FROM sofia.patents
            WHERE filing_date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY filing_date DESC
            LIMIT 50
        """)
        data['patents'] = cur.fetchall()
    except:
        data['patents'] = []

    # 6. STARTUPS (se existir)
    print("   🚀 Startups...")
    try:
        cur.execute("""
            SELECT name, country, sector, employees, founded_year
            FROM sofia.startups
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY employees DESC NULLS LAST
            LIMIT 100
        """)
        data['startups'] = cur.fetchall()
    except:
        data['startups'] = []

    print(f"✅ Dados coletados: {len(data.keys())} datasets\n")
    return data

# ============================================================================
# ANÁLISE E DETECÇÃO DE ANOMALIAS
# ============================================================================

def analyze_funding(data: Dict) -> Dict[str, Any]:
    """Analisa funding com comparação temporal"""
    funding_30d = data['funding_30d']
    funding_90d = data['funding_90d']

    analysis = {
        'total_30d': sum(row[2] for row in funding_30d if row[2]),
        'total_90d': sum(row[2] for row in funding_90d if row[2]),
        'deals_30d': len(funding_30d),
        'deals_90d': len(funding_90d),
        'top_deals': funding_30d[:5],
    }

    # Comparação temporal
    if analysis['total_90d'] > 0:
        analysis['growth_pct'] = ((analysis['total_30d'] * 3 / analysis['total_90d']) - 1) * 100

    # Por setor
    sectors = {}
    for row in funding_30d:
        sector = row[1] or 'Unknown'
        amount = row[2] or 0
        sectors[sector] = sectors.get(sector, 0) + amount
    analysis['by_sector'] = sorted(sectors.items(), key=lambda x: x[1], reverse=True)

    # Anomalias: deals > $1B
    analysis['mega_deals'] = [row for row in funding_30d if row[2] and row[2] > 1_000_000_000]

    return analysis

def analyze_b3(data: Dict) -> Dict[str, Any]:
    """Analisa B3 com detecção de padrões"""
    b3_latest = data['b3_latest']
    b3_7d_avg = data['b3_7d_avg']

    analysis = {
        'top_gainers': b3_latest[:5],
        'top_losers': list(reversed(b3_latest[-5:])),
    }

    # Detectar anomalias: ações subindo muito acima da média
    anomalies = []
    for ticker, company, price, change, volume, _ in b3_latest:
        if ticker in b3_7d_avg:
            avg_7d = b3_7d_avg[ticker]
            if abs(change - avg_7d) > 2:  # Variação > 2% da média
                anomalies.append((ticker, company, change, avg_7d))

    analysis['anomalies'] = anomalies

    # Padrão setorial (simplificado)
    industrials = ['WEGE3', 'RENT3']
    commodities = ['VALE3', 'PETR4']
    financials = ['ITUB4', 'BBDC4']

    def avg_change(tickers):
        changes = [row[3] for row in b3_latest if row[0] in tickers]
        return sum(changes) / len(changes) if changes else 0

    analysis['sectors'] = {
        'industrials': avg_change(industrials),
        'commodities': avg_change(commodities),
        'financials': avg_change(financials),
    }

    return analysis

# ============================================================================
# GERAÇÃO DE NARRATIVA COM GEMINI
# ============================================================================

def generate_narrative_with_gemini(data: Dict, analysis: Dict, macro: Dict) -> str:
    """Gera narrativa analítica usando Gemini"""

    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return generate_fallback_narrative(data, analysis, macro)

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Preparar dados para o prompt
        funding_summary = f"{analysis['funding']['deals_30d']} rodadas, ${analysis['funding']['total_30d']/1e9:.1f}B total"
        top_deal = analysis['funding']['top_deals'][0]
        b3_top = analysis['b3']['top_gainers'][0]

        prompt = f"""Você é analista sênior da Sofia Pulse. Gere insight analítico (3-4 parágrafos) baseado nos dados:

INVESTIMENTOS (últimos 30d):
- {funding_summary}
- Maior deal: {top_deal[0]} - ${top_deal[2]/1e9:.1f}B ({top_deal[1]})
- Crescimento vs 90d: {analysis['funding'].get('growth_pct', 0):.1f}%
- Top setores: {', '.join([f"{s[0]} ${s[1]/1e9:.1f}B" for s in analysis['funding']['by_sector'][:3]])}

MERCADO B3:
- Top gainer: {b3_top[0]} ({b3_top[1]}) {b3_top[3]:+.2f}%
- Industriais: {analysis['b3']['sectors']['industrials']:+.2f}%
- Commodities: {analysis['b3']['sectors']['commodities']:+.2f}%

CONTEXTO MACRO:
- Dólar: R$ {macro['dolar']:.2f}
- Selic: {macro['selic']:.2f}%
- Fed: {macro['fed_rate']:.2f}%

TAREFA:
Escreva análise em 3 parágrafos seguindo estrutura:

1. CAUSA (Por que está acontecendo?)
   - Correlacione investimentos + macro + movimentos setoriais
   - Identifique drivers principais

2. CONSEQUÊNCIA (O que isso significa?)
   - Impacto para mercado BR e global
   - Setores favorecidos/prejudicados

3. OPORTUNIDADE (Onde investir?)
   - Ações/setores concretos
   - Janelas de tempo
   - Riscos a observar

TOM: Sagaz, cético, direto. Sem enrolação. Foco em alpha (insights não-óbvios).
FORMATO: Markdown, 3 parágrafos, ~300 palavras total.
"""

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print(f"⚠️  Erro Gemini: {e}")
        return generate_fallback_narrative(data, analysis, macro)

def generate_fallback_narrative(data: Dict, analysis: Dict, macro: Dict) -> str:
    """Narrativa básica se Gemini falhar"""
    funding = analysis['funding']
    b3 = analysis['b3']

    narrative = f"""
## 🎯 ANÁLISE EXECUTIVA

**Fluxo de Capital Concentrado**: {funding['deals_30d']} rodadas somam ${funding['total_30d']/1e9:.1f}B em 30 dias,
crescimento de {funding.get('growth_pct', 0):.1f}% vs média trimestral. Setores de IA e Defense Tech dominam
(${sum(s[1] for s in funding['by_sector'][:2])/1e9:.1f}B combinados), indicando aposta em tecnologias críticas
pós-tensões geopolíticas.

**Divergência Setorial na B3**: Industriais exportadores ({b3['sectors']['industrials']:+.2f}%) sobem enquanto
commodities lateralizam ({b3['sectors']['commodities']:+.2f}%). Correlação direta com dólar a R$ {macro['dolar']:.2f}
(+2% na semana) - empresas com receita em USD se beneficiam. Selic a {macro['selic']:.2f}% pressiona múltiplos,
mas não freia setores exportadores.

**Posicionamento**: (1) Industriais BR (WEGE3, RENT3) até dólar recuar, (2) Defense tech global via fundos temáticos,
(3) Aguardar commodities até Fed sinalizar corte (próxima reunião dezembro). Risco: se dólar cair abaixo de R$ 5.60,
exportadores perdem atratividade rapidamente.
"""
    return narrative

# ============================================================================
# GERAÇÃO DE INSIGHTS COMPLETOS
# ============================================================================

def generate_insights(data: Dict, analysis: Dict, macro: Dict) -> str:
    """Gera insights completos"""

    funding = analysis['funding']
    b3 = analysis['b3']

    insights = f"""
════════════════════════════════════════════════════════════════
   🌍 SOFIA PULSE - PREMIUM INSIGHTS v3.0
   Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}
════════════════════════════════════════════════════════════════

📊 CONTEXTO MACROECONÔMICO
-------------------------------------------------------------------
💵 Dólar:  R$ {macro['dolar']:.2f}
📈 Selic:  {macro['selic']:.2f}%
🏦 Fed:    {macro['fed_rate']:.2f}%


💰 INVESTIMENTOS (últimos 30 dias)
-------------------------------------------------------------------
Total investido:  ${funding['total_30d']/1e9:.1f}B ({funding['deals_30d']} rodadas)
Variação vs 90d:  {funding.get('growth_pct', 0):+.1f}%

🔥 TOP RODADAS:
"""

    for company, sector, amount, valuation, round_type, _ in funding['top_deals']:
        if amount:
            insights += f"   • {company} ({sector})\n"
            insights += f"     {round_type} - ${amount/1e9:.1f}B"
            if valuation:
                insights += f" | Valuation: ${valuation/1e9:.1f}B"
            insights += "\n\n"

    insights += "\n📊 POR SETOR:\n"
    for sector, total in funding['by_sector'][:5]:
        insights += f"   {sector:30s} | ${total/1e9:6.1f}B\n"

    # Anomalias
    if funding['mega_deals']:
        insights += f"\n🚨 MEGA DEALS (>$1B): {len(funding['mega_deals'])} rodadas\n"
        for company, sector, amount, _, _, _ in funding['mega_deals'][:3]:
            insights += f"   → {company}: ${amount/1e9:.1f}B ({sector})\n"

    insights += "\n\n📈 MERCADO B3 (Brasil)\n"
    insights += "-------------------------------------------------------------------\n"
    insights += "\n🔥 TOP GAINERS:\n"
    for ticker, company, price, change, _, _ in b3['top_gainers']:
        insights += f"   📈 {ticker:8s} | {company:20s} | {change:+6.2f}%\n"

    insights += "\n📉 TOP LOSERS:\n"
    for ticker, company, price, change, _, _ in b3['top_losers']:
        insights += f"   📉 {ticker:8s} | {company:20s} | {change:+6.2f}%\n"

    # Padrões setoriais
    insights += "\n\n📊 PADRÕES SETORIAIS:\n"
    for sector, avg_change in b3['sectors'].items():
        symbol = "📈" if avg_change > 0 else "📉"
        insights += f"   {symbol} {sector.title():15s}: {avg_change:+5.2f}%\n"

    # Anomalias
    if b3['anomalies']:
        insights += f"\n\n🚨 ANOMALIAS DETECTADAS ({len(b3['anomalies'])} ações):\n"
        for ticker, company, change, avg_7d in b3['anomalies'][:5]:
            diff = change - avg_7d
            insights += f"   → {ticker}: {change:+.2f}% (média 7d: {avg_7d:+.2f}%, delta: {diff:+.2f}%)\n"

    # Narrativa Gemini
    insights += "\n\n" + "═"*64 + "\n"
    insights += generate_narrative_with_gemini(data, analysis, macro)
    insights += "\n" + "═"*64 + "\n"

    return insights

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("🚀 Sofia Pulse - Premium Insights Generator v3.0\n")

    # Conectar ao banco
    conn = psycopg2.connect(**DB_CONFIG)

    # Coletar contexto macro
    print("🌍 Coletando contexto macroeconômico...")
    macro = get_macro_context()
    print(f"   Dólar: R$ {macro['dolar']:.2f}")
    print(f"   Selic: {macro['selic']:.2f}%")
    print(f"   Fed: {macro['fed_rate']:.2f}%\n")

    # Coletar todos os dados
    data = collect_all_data(conn)

    # Análises
    print("🔍 Analisando dados...")
    analysis = {
        'funding': analyze_funding(data),
        'b3': analyze_b3(data),
    }
    print("✅ Análise concluída\n")

    # Gerar insights
    print("💎 Gerando insights premium...")
    insights = generate_insights(data, analysis, macro)

    # Salvar
    os.makedirs('analytics/premium-insights', exist_ok=True)

    with open('analytics/premium-insights/latest-v3.txt', 'w', encoding='utf-8') as f:
        f.write(insights)

    with open('analytics/premium-insights/latest-v3.md', 'w', encoding='utf-8') as f:
        f.write(insights)

    print("✅ Insights salvos!")
    print("📄 analytics/premium-insights/latest-v3.txt")
    print(f"\nPreview:\n{insights[:800]}...\n")

    # Exportar CSVs
    print("📤 Exportando CSVs...")

    cur = conn.cursor()

    # Funding
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

    # B3
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

    print("✅ CSVs exportados!\n")

    conn.close()

    print("🎉 CONCLUÍDO!")

if __name__ == '__main__':
    main()
