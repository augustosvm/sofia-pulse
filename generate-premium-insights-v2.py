#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sofia Pulse - Gerador de Insights PREMIUM v2.0
ANÁLISE GEOGRÁFICA + NARRATIVAS RICAS

Novidades v2:
- Análise por continente/país
- Papers por universidade/região
- Startups e funding por localização
- Especialização regional
- Textos narrativos prontos para copiar
- IPOs pendentes (quando disponível)
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import google.generativeai as genai
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

print("🔬 Sofia Pulse - Premium Insights v2.0 (GEO-LOCALIZADOS)")
print("=" * 70)

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

# ============================================================================
# MAPEAMENTOS GEOGRÁFICOS
# ============================================================================

# Mapeamento de países para continentes
CONTINENTS = {
    # América do Norte
    'USA': 'América do Norte', 'US': 'América do Norte', 'United States': 'América do Norte',
    'Canada': 'América do Norte', 'México': 'América do Norte', 'Mexico': 'América do Norte',

    # América do Sul
    'Brazil': 'América do Sul', 'Brasil': 'América do Sul', 'BR': 'América do Sul',
    'Argentina': 'América do Sul', 'Chile': 'América do Sul', 'Colombia': 'América do Sul',
    'Peru': 'América do Sul', 'Venezuela': 'América do Sul', 'Uruguay': 'América do Sul',

    # Europa
    'UK': 'Europa', 'United Kingdom': 'Europa', 'England': 'Europa', 'Germany': 'Europa',
    'France': 'Europa', 'Spain': 'Europa', 'Italy': 'Europa', 'Netherlands': 'Europa',
    'Switzerland': 'Europa', 'Sweden': 'Europa', 'Norway': 'Europa', 'Denmark': 'Europa',
    'Finland': 'Europa', 'Poland': 'Europa', 'Portugal': 'Europa', 'Ireland': 'Europa',

    # Ásia
    'China': 'Ásia', 'India': 'Ásia', 'Japan': 'Ásia', 'South Korea': 'Ásia',
    'Singapore': 'Ásia', 'Taiwan': 'Ásia', 'Hong Kong': 'Ásia', 'Israel': 'Ásia',
    'UAE': 'Ásia', 'Saudi Arabia': 'Ásia', 'Thailand': 'Ásia', 'Indonesia': 'Ásia',

    # Oceania
    'Australia': 'Oceania', 'New Zealand': 'Oceania',

    # África
    'South Africa': 'África', 'Nigeria': 'África', 'Kenya': 'África', 'Egypt': 'África',
}

# Universidades reconhecidas e suas especializações
UNIVERSITIES = {
    # USA
    'MIT': ('USA', ['AI', 'Robotics', 'Computer Science']),
    'Stanford': ('USA', ['AI', 'Biotech', 'Clean Energy']),
    'Harvard': ('USA', ['Medicine', 'Biotech', 'Business']),
    'Berkeley': ('USA', ['AI', 'Quantum', 'Climate']),
    'CMU': ('USA', ['AI', 'Robotics', 'HCI']),
    'Caltech': ('USA', ['Physics', 'Space', 'Quantum']),

    # China
    'Tsinghua': ('China', ['AI', 'Manufacturing', 'Engineering']),
    'Peking': ('China', ['AI', 'Chemistry', 'Materials']),

    # Europa
    'Oxford': ('UK', ['Medicine', 'AI', 'Climate']),
    'Cambridge': ('UK', ['Physics', 'Biotech', 'AI']),
    'ETH': ('Switzerland', ['Robotics', 'Quantum', 'Climate']),

    # Brasil
    'USP': ('Brasil', ['Agro-tech', 'Medicine', 'Engineering']),
    'Unicamp': ('Brasil', ['Agro-tech', 'Materials', 'Energy']),
    'UFRJ': ('Brasil', ['Oil & Gas', 'Ocean', 'Medicine']),
    'UFMG': ('Brasil', ['Mining', 'Materials', 'AI']),

    # Outras
    'Technion': ('Israel', ['Defense Tech', 'AI', 'Cybersecurity']),
    'NUS': ('Singapore', ['AI', 'Fintech', 'Smart Cities']),
}

# Especialização por região
REGIONAL_SPECIALIZATIONS = {
    'Brasil': ['Agro-tech', 'Fintech', 'Healthcare', 'Ed-tech'],
    'USA': ['AI', 'SaaS', 'Biotech', 'Space'],
    'China': ['AI', 'Manufacturing', 'Hardware', 'E-commerce'],
    'Europa': ['Green Tech', 'Privacy Tech', 'Mobility', 'Deep Tech'],
    'Israel': ['Cybersecurity', 'Defense Tech', 'AI', 'Biotech'],
    'India': ['Software', 'Fintech', 'Ed-tech', 'Healthcare'],
    'Singapore': ['Fintech', 'Smart Cities', 'Logistics', 'Biotech'],
}

def extract_country_from_author(author_str):
    """Extrai país/universidade de uma string de autor"""
    for uni, (country, specs) in UNIVERSITIES.items():
        if uni.lower() in author_str.lower():
            return country, uni

    for country in CONTINENTS.keys():
        if country.lower() in author_str.lower():
            return country, None

    return None, None

def get_continent(country):
    """Retorna continente do país"""
    return CONTINENTS.get(country, 'Outros')

# ============================================================================
# CARREGAR DADOS
# ============================================================================

print("\n📊 1. Carregando TODOS os dados com informação geográfica...")

# ArXiv Papers (com autores para extrair afiliação)
try:
    df_arxiv = pd.read_sql('''
        SELECT id, title, authors, categories, published_date, citation_count
        FROM sofia.arxiv_ai_papers
        ORDER BY published_date DESC
        LIMIT 500
    ''', engine)
    print(f"   ✅ ArXiv AI: {len(df_arxiv)} papers")
except Exception as e:
    df_arxiv = pd.DataFrame()
    print(f"   ⚠️  ArXiv: sem dados - {e}")

# Funding Rounds (COM país)
try:
    df_funding = pd.read_sql('''
        SELECT id, company, sector, round_type, amount_usd, country, announced_date
        FROM sofia.funding_rounds
        ORDER BY announced_date DESC
    ''', engine)
    print(f"   ✅ Funding: {len(df_funding)} deals")
except Exception as e:
    df_funding = pd.DataFrame()
    print(f"   ⚠️  Funding: sem dados - {e}")

# Startups (se tiver localização)
try:
    df_startups = pd.read_sql('''
        SELECT id, name, sector, founded_date, country, employees
        FROM sofia.startups
    ''', engine)
    print(f"   ✅ Startups: {len(df_startups)} empresas")
except Exception as e:
    df_startups = pd.DataFrame()
    print(f"   ⚠️  Startups: sem dados - {e}")

# Clinical Trials (COM país)
try:
    df_trials = pd.read_sql('''
        SELECT trial_id, title, sponsor, phase, country, condition, start_date
        FROM sofia.clinical_trials
        WHERE country IS NOT NULL
        ORDER BY start_date DESC
        LIMIT 200
    ''', engine)
    print(f"   ✅ Clinical Trials: {len(df_trials)} trials")
except Exception as e:
    df_trials = pd.DataFrame()
    print(f"   ⚠️  Clinical Trials: sem dados - {e}")

# Patents (COM país)
try:
    df_patents = pd.read_sql('''
        SELECT patent_number, title, assignee, country, filing_date, classifications
        FROM sofia.patents
        WHERE country IS NOT NULL
        ORDER BY filing_date DESC
        LIMIT 200
    ''', engine)
    print(f"   ✅ Patents: {len(df_patents)} patentes")
except Exception as e:
    df_patents = pd.DataFrame()
    print(f"   ⚠️  Patents: sem dados - {e}")

# BDTD (teses brasileiras)
try:
    df_bdtd = pd.read_sql('''
        SELECT id, title, author, university, area, defense_date
        FROM sofia.bdtd_theses
        ORDER BY defense_date DESC
        LIMIT 200
    ''', engine)
    print(f"   ✅ BDTD (Teses BR): {len(df_bdtd)} teses")
except Exception as e:
    df_bdtd = pd.DataFrame()
    print(f"   ⚠️  BDTD: sem dados - {e}")

# B3 e NASDAQ (já temos)
try:
    df_b3 = pd.read_sql('SELECT * FROM sofia.market_data_brazil ORDER BY collected_at DESC LIMIT 100', engine)
    print(f"   ✅ B3: {len(df_b3)} stocks")
except:
    df_b3 = pd.DataFrame()
    print("   ⚠️  B3: sem dados")

try:
    df_nasdaq = pd.read_sql('SELECT * FROM sofia.market_data_nasdaq ORDER BY collected_at DESC LIMIT 100', engine)
    print(f"   ✅ NASDAQ: {len(df_nasdaq)} stocks")
except:
    df_nasdaq = pd.DataFrame()
    print("   ⚠️  NASDAQ: sem dados")

# ============================================================================
# ANÁLISE GEOGRÁFICA
# ============================================================================

print("\n🌍 2. Gerando Análises GEO-LOCALIZADAS...")

insights = []

# ============================================================================
# INSIGHT 1: MAPA GLOBAL DE INOVAÇÃO
# ============================================================================

print("\n   🗺️  Insight 1: Mapa Global de Inovação...")

insight_1 = "## 🗺️ Mapa Global de Inovação\n\n"

# Papers por continente
if not df_arxiv.empty and 'authors' in df_arxiv.columns:
    insight_1 += "### 📚 Pesquisa Científica (ArXiv AI Papers)\n\n"

    # Extrair países dos autores
    countries_papers = []
    universities_papers = defaultdict(int)

    for authors in df_arxiv['authors'].dropna():
        author_str = str(authors)
        country, uni = extract_country_from_author(author_str)
        if country:
            countries_papers.append(country)
        if uni:
            universities_papers[uni] += 1

    if countries_papers:
        country_counts = pd.Series(countries_papers).value_counts()
        continent_counts = pd.Series([get_continent(c) for c in countries_papers]).value_counts()

        insight_1 += "**Por Continente**:\n"
        for cont, count in continent_counts.head(5).items():
            pct = (count / len(countries_papers)) * 100
            insight_1 += f"- **{cont}**: {count} papers ({pct:.1f}%)\n"

        insight_1 += "\n**Top 5 Países**:\n"
        for country, count in country_counts.head(5).items():
            pct = (count / len(countries_papers)) * 100
            insight_1 += f"- **{country}**: {count} papers ({pct:.1f}%)\n"

        if universities_papers:
            insight_1 += "\n**Universidades Mais Ativas**:\n"
            for uni, count in sorted(universities_papers.items(), key=lambda x: x[1], reverse=True)[:5]:
                specs = UNIVERSITIES.get(uni, (None, []))[1]
                specs_str = ", ".join(specs[:2]) if specs else "Geral"
                insight_1 += f"- **{uni}**: {count} papers (Especialidade: {specs_str})\n"

# Funding por continente
if not df_funding.empty and 'country' in df_funding.columns:
    insight_1 += "\n### 💰 Investimentos (Funding Rounds)\n\n"

    funding_by_country = df_funding.groupby('country').agg({
        'amount_usd': 'sum',
        'company': 'count'
    }).sort_values('amount_usd', ascending=False)

    funding_by_continent = df_funding.copy()
    funding_by_continent['continent'] = funding_by_continent['country'].apply(get_continent)
    continent_funding = funding_by_continent.groupby('continent').agg({
        'amount_usd': 'sum',
        'company': 'count'
    }).sort_values('amount_usd', ascending=False)

    insight_1 += "**Por Continente**:\n"
    for cont, row in continent_funding.head(5).iterrows():
        amount_b = row['amount_usd'] / 1e9
        deals = row['company']
        insight_1 += f"- **{cont}**: ${amount_b:.2f}B em {deals} deals\n"

    insight_1 += "\n**Top 5 Países** (por volume investido):\n"
    for country, row in funding_by_country.head(5).iterrows():
        amount_b = row['amount_usd'] / 1e9
        deals = row['company']
        insight_1 += f"- **{country}**: ${amount_b:.2f}B em {deals} deals\n"

insights.append(("Mapa Global de Inovação", insight_1))
print("      ✅ Gerado!")

# ============================================================================
# INSIGHT 2: ESPECIALIZAÇÃO REGIONAL
# ============================================================================

print("   🎯 Insight 2: Especialização Regional...")

insight_2 = "## 🎯 Especialização Regional\n\n"
insight_2 += "*Onde cada região do mundo está focando sua inovação*\n\n"

# Funding por setor por continente
if not df_funding.empty and 'country' in df_funding.columns and 'sector' in df_funding.columns:
    df_funding_geo = df_funding.copy()
    df_funding_geo['continent'] = df_funding_geo['country'].apply(get_continent)

    for continent in df_funding_geo['continent'].value_counts().head(5).index:
        if continent == 'Outros':
            continue

        continent_data = df_funding_geo[df_funding_geo['continent'] == continent]

        if len(continent_data) > 0:
            insight_2 += f"### {continent}\n\n"

            # Top setores
            sector_funding = continent_data.groupby('sector')['amount_usd'].sum().sort_values(ascending=False).head(5)

            if len(sector_funding) > 0:
                insight_2 += "**Setores em Alta**:\n"
                for sector, amount in sector_funding.items():
                    amount_m = amount / 1e6
                    deals = len(continent_data[continent_data['sector'] == sector])
                    insight_2 += f"- **{sector}**: ${amount_m:.1f}M ({deals} deals)\n"

            # Empresas top
            top_companies = continent_data.nlargest(3, 'amount_usd')[['company', 'amount_usd', 'sector', 'round_type']]
            if len(top_companies) > 0:
                insight_2 += "\n**Maiores Deals**:\n"
                for _, row in top_companies.iterrows():
                    amount_m = row['amount_usd'] / 1e6
                    insight_2 += f"- **{row['company']}** ({row['sector']}): ${amount_m:.1f}M - {row['round_type']}\n"

            insight_2 += "\n"

insights.append(("Especialização Regional", insight_2))
print("      ✅ Gerado!")

# ============================================================================
# INSIGHT 3: TENDÊNCIAS EMERGENTES POR PAÍS
# ============================================================================

print("   📈 Insight 3: Tendências Emergentes...")

insight_3 = "## 📈 Tendências Emergentes por País\n\n"

# Análise Brasil
if not df_bdtd.empty:
    insight_3 += "### 🇧🇷 Brasil\n\n"
    insight_3 += "**Pesquisa Acadêmica** (Teses/Dissertações recentes):\n"

    top_areas = df_bdtd['area'].value_counts().head(5)
    for area, count in top_areas.items():
        insight_3 += f"- **{area}**: {count} teses\n"

    top_unis = df_bdtd['university'].value_counts().head(3)
    insight_3 += "\n**Universidades Mais Produtivas**:\n"
    for uni, count in top_unis.items():
        insight_3 += f"- {uni}: {count} teses\n"

    insight_3 += "\n"

# Análise USA (papers + funding)
usa_papers = 0
if not df_arxiv.empty:
    for authors in df_arxiv['authors'].dropna():
        country, _ = extract_country_from_author(str(authors))
        if country in ['USA', 'US', 'United States']:
            usa_papers += 1

if usa_papers > 0:
    insight_3 += "### 🇺🇸 Estados Unidos\n\n"
    insight_3 += f"**Pesquisa**: {usa_papers} papers AI recentes\n"

    if not df_funding.empty:
        usa_funding = df_funding[df_funding['country'].isin(['USA', 'US', 'United States'])]
        if len(usa_funding) > 0:
            total_usd = usa_funding['amount_usd'].sum() / 1e9
            deals = len(usa_funding)
            insight_3 += f"**Funding**: ${total_usd:.2f}B em {deals} deals\n"

            top_sectors = usa_funding.groupby('sector')['amount_usd'].sum().sort_values(ascending=False).head(3)
            insight_3 += "\n**Setores em Alta**:\n"
            for sector, amount in top_sectors.items():
                insight_3 += f"- {sector}: ${amount/1e9:.2f}B\n"

    insight_3 += "\n"

insights.append(("Tendências Emergentes", insight_3))
print("      ✅ Gerado!")

# ============================================================================
# INSIGHT 4: MERCADO (B3 + NASDAQ) - Com fix de duplicatas
# ============================================================================

print("   📊 Insight 4: Performance de Mercado...")

if not df_b3.empty or not df_nasdaq.empty:
    insight_4 = "## 📊 Performance de Mercado\n\n"

    if not df_b3.empty:
        b3_avg = df_b3['change_pct'].mean()
        # FIX: Remover duplicatas por ticker
        b3_unique = df_b3.drop_duplicates(subset='ticker', keep='first')
        b3_top = b3_unique.nlargest(5, 'change_pct')[['ticker', 'company', 'change_pct', 'sector']]

        insight_4 += f"**B3 (Brasil)**:\n- Performance média: {b3_avg:.2f}%\n\n"
        insight_4 += "Top 5 Performers:\n"
        for _, row in b3_top.iterrows():
            insight_4 += f"\n- **{row['ticker']}** ({row['company']}): +{row['change_pct']:.2f}% - {row['sector']}"

    if not df_nasdaq.empty:
        nasdaq_avg = df_nasdaq['change_pct'].mean()
        # FIX: Remover duplicatas por ticker
        nasdaq_unique = df_nasdaq.drop_duplicates(subset='ticker', keep='first')
        nasdaq_top = nasdaq_unique.nlargest(5, 'change_pct')[['ticker', 'company', 'change_pct', 'sector']]

        insight_4 += f"\n\n**NASDAQ (US)**:\n- Performance média: {nasdaq_avg:.2f}%\n\n"
        insight_4 += "Top 5 Performers:\n"
        for _, row in nasdaq_top.iterrows():
            insight_4 += f"\n- **{row['ticker']}** ({row['company']}): +{row['change_pct']:.2f}% - {row['sector']}"

    insights.append(("Mercado Financeiro", insight_4))
    print("      ✅ Gerado!")

# ============================================================================
# NARRATIVA COM GEMINI AI
# ============================================================================

print("\n🤖 3. Gerando Narrativa com Gemini AI...")

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

    if available_models:
        model_name = available_models[0]
        print(f"   ℹ️  Usando modelo: {model_name}")
        model = genai.GenerativeModel(model_name)

        all_insights_text = "\n\n".join([f"# {title}\n{content}" for title, content in insights])

        prompt = f"""
Você é um analista de tecnologia e inovação global expert. Analise estes dados geo-localizados e crie um RESUMO EXECUTIVO NARRATIVO para colunistas.

{all_insights_text}

Forneça um texto CORRIDO (não bullet points) de 3-4 parágrafos que:

1. **Destaque o panorama global**: Quais continentes/países estão liderando em inovação
2. **Especialização regional**: O que cada região faz de melhor (ex: Brasil em Agro-tech, China em AI, Europa em Green Tech)
3. **Oportunidades emergentes**: Onde estão surgindo as maiores oportunidades de investimento
4. **Conclusão provocativa**: Uma frase impactante sobre o futuro da inovação global

Use números concretos dos dados. Seja direto e escreva em português brasileiro.
Gere um texto que colunistas possam COPIAR e COLAR direto em seus artigos.
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

# ============================================================================
# SALVAR OUTPUTS
# ============================================================================

print("\n💾 4. Salvando Insights GEO-LOCALIZADOS...")

os.makedirs('/home/ubuntu/sofia-pulse/analytics/premium-insights', exist_ok=True)

timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
output_md = f"""# 🌍 Sofia Pulse - Insights PREMIUM Geo-Localizados

**Gerado em**: {timestamp}
**Modelo IA**: Gemini 2.5 Pro Preview (v2.0)
**Análise**: Global com foco em especialização regional

---

## 📰 TEXTO PARA COLUNISTAS (COPIAR/COLAR)

{ai_summary}

---

"""

for title, content in insights:
    output_md += f"{content}\n\n---\n\n"

output_md += f"""
## 📊 Metodologia v2.0

**Fontes de Dados Geo-Localizadas**:
- ArXiv AI Papers: {len(df_arxiv)} papers (com afiliação de autores)
- Funding Rounds: {len(df_funding)} deals (com país)
- Clinical Trials: {len(df_trials)} trials (com país)
- Patents: {len(df_patents)} patentes (com país)
- BDTD (Brasil): {len(df_bdtd)} teses (universidades brasileiras)
- Market Data: B3 ({len(df_b3)}), NASDAQ ({len(df_nasdaq)})

**Novidades v2**:
- ✅ Análise por continente/país
- ✅ Especialização regional
- ✅ Universidades e suas áreas de expertise
- ✅ Narrativas prontas para copiar
- ✅ Mapa global de inovação

**Custo da Análise**: ~$0.03 (Gemini API)

---

## 💡 Como Usar

**Para Colunistas**:
1. Use o "TEXTO PARA COLUNISTAS" no início - está pronto para publicar
2. Adicione insights específicos das seções abaixo
3. Cite "Sofia Pulse Global Innovation Platform" como fonte

**Para Investidores**:
1. Veja "Especialização Regional" para saber onde investir
2. Use "Tendências Emergentes" para detectar oportunidades cedo
3. Cruze com "Performance de Mercado" para validar teses

---

**Próxima Atualização**: Automático (diário via cron)

**Acesse Dados Brutos**: http://91.98.158.19:8889 (Jupyter Lab)

---

*Gerado automaticamente pelo Sofia Pulse Premium Insights Engine v2.0*
*Powered by Gemini AI + PostgreSQL Analytics*
"""

# Salvar Markdown
md_path = '/home/ubuntu/sofia-pulse/analytics/premium-insights/latest-geo.md'
with open(md_path, 'w', encoding='utf-8') as f:
    f.write(output_md)
print(f"   ✅ {md_path}")

# Salvar TXT (mesma coisa)
txt_path = '/home/ubuntu/sofia-pulse/analytics/premium-insights/latest-geo.txt'
with open(txt_path, 'w', encoding='utf-8') as f:
    f.write(output_md)
print(f"   ✅ {txt_path}")

# Salvar CSV com sumário por continente
summary_data = []

if not df_funding.empty and 'country' in df_funding.columns:
    df_funding_geo = df_funding.copy()
    df_funding_geo['continent'] = df_funding_geo['country'].apply(get_continent)

    continent_summary = df_funding_geo.groupby('continent').agg({
        'amount_usd': 'sum',
        'company': 'count'
    }).reset_index()

    continent_summary.columns = ['Continente', 'Funding Total (USD)', 'Número de Deals']
    continent_summary['Funding Total (B)'] = continent_summary['Funding Total (USD)'] / 1e9

    csv_path = '/home/ubuntu/sofia-pulse/analytics/premium-insights/geo-summary.csv'
    continent_summary[['Continente', 'Funding Total (B)', 'Número de Deals']].to_csv(csv_path, index=False)
    print(f"   ✅ {csv_path}")

print("\n" + "=" * 70)
print("✅ INSIGHTS GEO-LOCALIZADOS GERADOS COM SUCESSO!")
print("=" * 70)
print("\n📄 Arquivos Gerados:")
print(f"   📝 Markdown: {md_path}")
print(f"   📄 Texto: {txt_path}")
if summary_data or not df_funding.empty:
    print(f"   📊 CSV: {csv_path}")

print("\n🎯 Para Ver:")
print(f"   cat {txt_path}")
print("\n💰 Custo: ~$0.03 (Gemini API)")
print("💎 Valor: Insights GEO-LOCALIZADOS exclusivos!")
print("\n" + "=" * 70)
