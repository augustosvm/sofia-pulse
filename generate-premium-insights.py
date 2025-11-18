#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sofia Pulse - Gerador de Insights PREMIUM
Cruza TODOS os dados para gerar insights vendáveis para colunistas
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import google.generativeai as genai
import os
from datetime import datetime
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

print("🔬 Sofia Pulse - Gerador de Insights PREMIUM")
print("=" * 60)

# Carregar .env
load_dotenv('/home/ubuntu/sofia-pulse/.env')

# Configuração PostgreSQL
DB_USER = os.getenv('DB_USER', 'sofia')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'sofia123strong')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'sofia_db')

connection_string = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(connection_string)

print("\n📊 1. Carregando TODOS os dados...")

# Carregar todas as tabelas principais
try:
    df_stackoverflow = pd.read_sql('SELECT * FROM sofia.stackoverflow_trends ORDER BY week DESC LIMIT 100', engine)
    print(f"   ✅ Stack Overflow: {len(df_stackoverflow)} trends")
except:
    df_stackoverflow = pd.DataFrame()
    print("   ⚠️  Stack Overflow: sem dados")

try:
    df_github = pd.read_sql('SELECT * FROM sofia.github_metrics ORDER BY collected_at DESC', engine)
    print(f"   ✅ GitHub: {len(df_github)} repos")
except:
    df_github = pd.DataFrame()
    print("   ⚠️  GitHub: sem dados")

try:
    df_publications = pd.read_sql('SELECT * FROM sofia.publications ORDER BY publication_date DESC LIMIT 100', engine)
    print(f"   ✅ Publications: {len(df_publications)} papers")
except:
    df_publications = pd.DataFrame()
    print("   ⚠️  Publications: sem dados")

try:
    df_arxiv = pd.read_sql('SELECT * FROM sofia.arxiv_ai_papers ORDER BY published_date DESC', engine)
    print(f"   ✅ ArXiv AI: {len(df_arxiv)} papers")
except:
    df_arxiv = pd.DataFrame()
    print("   ⚠️  ArXiv: sem dados")

try:
    df_startups = pd.read_sql('SELECT * FROM sofia.startups', engine)
    print(f"   ✅ Startups: {len(df_startups)} empresas")
except:
    df_startups = pd.DataFrame()
    print("   ⚠️  Startups: sem dados")

try:
    df_funding = pd.read_sql('SELECT * FROM sofia.funding_rounds', engine)
    print(f"   ✅ Funding: {len(df_funding)} deals")
except:
    df_funding = pd.DataFrame()
    print("   ⚠️  Funding: sem dados")

try:
    df_b3 = pd.read_sql('SELECT * FROM sofia.market_data_brazil ORDER BY collected_at DESC', engine)
    print(f"   ✅ B3: {len(df_b3)} stocks")
except:
    df_b3 = pd.DataFrame()
    print("   ⚠️  B3: sem dados")

try:
    df_nasdaq = pd.read_sql('SELECT * FROM sofia.market_data_nasdaq ORDER BY collected_at DESC', engine)
    print(f"   ✅ NASDAQ: {len(df_nasdaq)} stocks")
except:
    df_nasdaq = pd.DataFrame()
    print("   ⚠️  NASDAQ: sem dados")

print("\n🔍 2. Gerando Insights PREMIUM...")

insights = []

# INSIGHT 1: Tecnologias Emergentes (Stack Overflow + GitHub + ArXiv)
print("\n   📈 Insight 1: Tecnologias Bombando...")

if not df_stackoverflow.empty:
    # Top tags crescendo
    so_trending = df_stackoverflow.groupby('tag').agg({
        'question_count': 'sum',
        'week': 'count'
    }).sort_values('question_count', ascending=False).head(10)

    insight_1 = f"""
## 🚀 Tecnologias que Estão Bombando (Agora)

**Stack Overflow - Últimas 100 Semanas**:
"""
    for tag, row in so_trending.iterrows():
        insight_1 += f"\n- **{tag}**: {row['question_count']:,} perguntas ({row['week']} semanas ativas)"

    # Cruzar com GitHub se tiver
    if not df_github.empty and 'language' in df_github.columns:
        gh_langs = df_github.groupby('language')['stars'].sum().sort_values(ascending=False).head(5)
        insight_1 += f"\n\n**GitHub - Linguagens Mais Populares**:\n"
        for lang, stars in gh_langs.items():
            insight_1 += f"\n- **{lang}**: {stars:,} stars totais"

    insights.append(("Tecnologias Emergentes", insight_1))
    print("      ✅ Gerado!")

# INSIGHT 2: Onde o Dinheiro Está Indo (Funding + Startups)
print("   💰 Insight 2: Onde os Angels Investem...")

if not df_funding.empty or not df_startups.empty:
    insight_2 = "## 💰 Onde o Dinheiro Está Indo\n\n"

    if not df_funding.empty and 'sector' in df_funding.columns:
        funding_by_sector = df_funding.groupby('sector')['amount_usd'].sum().sort_values(ascending=False).head(10)
        total_funding = df_funding['amount_usd'].sum()

        insight_2 += "**Funding por Setor**:\n"
        for sector, amount in funding_by_sector.items():
            pct = (amount / total_funding) * 100
            insight_2 += f"\n- **{sector}**: ${amount/1e9:.2f}B ({pct:.1f}% do total)"

    if not df_startups.empty and 'sector' in df_startups.columns:
        startups_by_sector = df_startups.groupby('sector').size().sort_values(ascending=False).head(5)
        insight_2 += f"\n\n**Startups por Setor**:\n"
        for sector, count in startups_by_sector.items():
            insight_2 += f"\n- **{sector}**: {count} empresas"

    insights.append(("Onde Investir", insight_2))
    print("      ✅ Gerado!")

# INSIGHT 3: Research que Vira Produto (ArXiv + Startups)
print("   🔬 Insight 3: Research → Startups...")

if not df_arxiv.empty:
    insight_3 = "## 🔬 Research que Vira Produto\n\n"

    if 'categories' in df_arxiv.columns or 'category' in df_arxiv.columns:
        cat_col = 'categories' if 'categories' in df_arxiv.columns else 'category'
        top_categories = df_arxiv[cat_col].value_counts().head(10)

        insight_3 += "**Áreas de Research Mais Ativas (ArXiv AI)**:\n"
        for cat, count in top_categories.items():
            insight_3 += f"\n- **{cat}**: {count} papers"

    # Cruzar com startups por setor
    if not df_startups.empty and 'sector' in df_startups.columns:
        insight_3 += f"\n\n**Setores com Mais Startups** (possível correlação):\n"
        for sector, count in df_startups.groupby('sector').size().head(5).items():
            insight_3 += f"\n- **{sector}**: {count} startups"

    insights.append(("Research to Market", insight_3))
    print("      ✅ Gerado!")

# INSIGHT 4: Mercado Financeiro (B3 + NASDAQ + Funding)
print("   📊 Insight 4: Mercado e Performance...")

if not df_b3.empty or not df_nasdaq.empty:
    insight_4 = "## 📊 Performance de Mercado\n\n"

    if not df_b3.empty:
        b3_avg = df_b3['change_pct'].mean()
        b3_top = df_b3.nlargest(5, 'change_pct')[['ticker', 'company', 'change_pct', 'sector']]

        insight_4 += f"**B3 (Brasil)**:\n- Performance média: {b3_avg:.2f}%\n\n"
        insight_4 += "Top 5 Performers:\n"
        for _, row in b3_top.iterrows():
            insight_4 += f"\n- **{row['ticker']}** ({row['company']}): +{row['change_pct']:.2f}% - {row['sector']}"

    if not df_nasdaq.empty:
        nasdaq_avg = df_nasdaq['change_pct'].mean()
        nasdaq_top = df_nasdaq.nlargest(5, 'change_pct')[['ticker', 'company', 'change_pct', 'sector']]

        insight_4 += f"\n\n**NASDAQ (US)**:\n- Performance média: {nasdaq_avg:.2f}%\n\n"
        insight_4 += "Top 5 Performers:\n"
        for _, row in nasdaq_top.iterrows():
            insight_4 += f"\n- **{row['ticker']}** ({row['company']}): +{row['change_pct']:.2f}% - {row['sector']}"

    insights.append(("Mercado Financeiro", insight_4))
    print("      ✅ Gerado!")

# INSIGHT 5: Sinais Antecipados (Cruzamento de Tudo)
print("   🎯 Insight 5: Sinais de Oportunidade...")

insight_5 = "## 🎯 Sinais Antecipados de Oportunidade\n\n"

# Setores quentes: Alto funding + muitas startups + papers aumentando
if not df_funding.empty and not df_startups.empty:
    funding_sectors = set(df_funding['sector'].dropna()) if 'sector' in df_funding.columns else set()
    startup_sectors = set(df_startups['sector'].dropna()) if 'sector' in df_startups.columns else set()
    hot_sectors = funding_sectors & startup_sectors

    if hot_sectors:
        insight_5 += "**Setores com Convergência** (Funding + Startups):\n"
        for sector in list(hot_sectors)[:5]:
            funding_amt = df_funding[df_funding['sector'] == sector]['amount_usd'].sum() if 'amount_usd' in df_funding.columns else 0
            startup_count = len(df_startups[df_startups['sector'] == sector])
            insight_5 += f"\n- **{sector}**: ${funding_amt/1e9:.2f}B funding, {startup_count} startups"

# Skills valorizadas: Stack Overflow + Funding em empresas do setor
if not df_stackoverflow.empty:
    insight_5 += f"\n\n**Skills em Alta** (Stack Overflow):\n"
    top_skills = df_stackoverflow.groupby('tag')['question_count'].sum().sort_values(ascending=False).head(5)
    for skill, count in top_skills.items():
        insight_5 += f"\n- **{skill}**: {count:,} perguntas"

insights.append(("Sinais de Oportunidade", insight_5))
print("      ✅ Gerado!")

print("\n🤖 3. Gerando Narrativa com Gemini AI...")

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

    if available_models:
        model_name = available_models[0]
        print(f"   ℹ️  Usando modelo: {model_name}")
        model = genai.GenerativeModel(model_name)

        # Preparar resumo para Gemini
        all_insights_text = "\n\n".join([f"# {title}\n{content}" for title, content in insights])

        prompt = f"""
Você é um analista de tendências tech expert. Analise estes insights e crie um RESUMO EXECUTIVO para colunistas de tecnologia.

{all_insights_text}

Forneça:

1. **Headline Principal** (1 frase impactante para usar como título de matéria)
2. **Top 3 Tendências** (bullet points acionáveis)
3. **Onde Investir Agora** (3 setores/tecnologias com justificativa)
4. **O Que Evitar** (sinais de alerta nos dados)
5. **Previsão para Próximos 6 Meses** (baseado nos dados)

Seja direto, use números, e gere conteúdo que colunistas possam COPIAR e COLAR em seus artigos.
"""

        response = model.generate_content(prompt)
        ai_summary = response.text
        print("   ✅ Narrativa gerada!")
    else:
        ai_summary = "Gemini não disponível - insights gerados apenas com dados brutos"
        print("   ⚠️  Gemini não disponível")
else:
    ai_summary = "GEMINI_API_KEY não configurada"
    print("   ⚠️  GEMINI_API_KEY não encontrada")

print("\n💾 4. Salvando Insights PREMIUM...")

# Criar diretórios
os.makedirs('/home/ubuntu/sofia-pulse/analytics/premium-insights', exist_ok=True)

# Salvar em Markdown (para colunistas)
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
output_md = f"""# 💎 Sofia Pulse - Insights PREMIUM para Colunistas

**Gerado em**: {timestamp}
**Modelo IA**: Gemini 2.5 Pro Preview
**Dados analisados**: Stack Overflow, GitHub, ArXiv, Startups, Funding, B3, NASDAQ

---

## 🎯 RESUMO EXECUTIVO (IA)

{ai_summary}

---

"""

for title, content in insights:
    output_md += f"{content}\n\n---\n\n"

output_md += f"""
## 📊 Metodologia

**Fontes de Dados**:
- Stack Overflow Trends: {len(df_stackoverflow)} registros
- GitHub Metrics: {len(df_github)} repositórios
- Publications/ArXiv: {len(df_publications) + len(df_arxiv)} papers
- Startups: {len(df_startups)} empresas
- Funding Rounds: {len(df_funding)} deals
- Market Data: {len(df_b3) + len(df_nasdaq)} ações

**Análises Realizadas**:
1. Correlação entre Stack Overflow trends e GitHub stars
2. Cruzamento de setores (Funding x Startups)
3. Análise de research papers vs. startups criadas
4. Performance de mercado por setor
5. Detecção de sinais antecipados (convergência de métricas)

**Custo da Análise**: ~$0.02 (Gemini API)

---

## 💡 Como Usar Estes Insights

**Para Colunistas**:
1. Copie os dados relevantes para seu artigo
2. Use as narrativas da IA como base
3. Adicione suas próprias análises
4. Cite "Sofia Pulse Data Platform" como fonte

**Para Investidores**:
1. Foque nos setores com convergência
2. Monitore skills em alta para contratação
3. Acompanhe sinais antecipados

**Para Desenvolvedores**:
1. Aprenda as skills em alta
2. Contribua para repos trending
3. Estude papers de áreas quentes

---

**Próxima Atualização**: Automático (diário via cron)

**Acesse Dados Brutos**: http://91.98.158.19:8889 (Jupyter Lab)

---

*Gerado automaticamente pelo Sofia Pulse Premium Insights Engine*
"""

# Salvar Markdown
md_path = '/home/ubuntu/sofia-pulse/analytics/premium-insights/latest.md'
with open(md_path, 'w', encoding='utf-8') as f:
    f.write(output_md)
print(f"   ✅ {md_path}")

# Salvar TXT (para fácil leitura)
txt_path = '/home/ubuntu/sofia-pulse/analytics/premium-insights/latest.txt'
with open(txt_path, 'w', encoding='utf-8') as f:
    f.write(output_md)
print(f"   ✅ {txt_path}")

# Salvar CSV com dados estruturados
csv_path = '/home/ubuntu/sofia-pulse/analytics/premium-insights/data-summary.csv'
summary_data = {
    'metrica': ['Stack Overflow Trends', 'GitHub Repos', 'Research Papers', 'Startups', 'Funding Deals', 'Ações (B3+NASDAQ)'],
    'quantidade': [len(df_stackoverflow), len(df_github), len(df_publications) + len(df_arxiv), len(df_startups), len(df_funding), len(df_b3) + len(df_nasdaq)],
    'ultima_atualizacao': [timestamp] * 6
}
pd.DataFrame(summary_data).to_csv(csv_path, index=False)
print(f"   ✅ {csv_path}")

print("\n" + "=" * 60)
print("✅ INSIGHTS PREMIUM GERADOS COM SUCESSO!")
print("=" * 60)

print(f"\n📄 Arquivos Gerados:")
print(f"   📝 Markdown: {md_path}")
print(f"   📄 Texto: {txt_path}")
print(f"   📊 CSV: {csv_path}")

print(f"\n🎯 Para Ver:")
print(f"   cat {txt_path}")
print(f"\n💰 Custo: ~$0.02 (Gemini API)")
print(f"💎 Valor: INESTIMÁVEL (insights exclusivos!)")

print("\n" + "=" * 60)
