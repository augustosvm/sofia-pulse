#!/usr/bin/env python3
"""
Sofia Pulse - Premium Insights v4.0 FINAL
USA OS DADOS REAIS coletados pelos collectors
+ GEO-LOCALIZAÇÃO (continentes, países, universidades)
"""

import psycopg2
from datetime import datetime
import os
from collections import defaultdict, Counter

# Config
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'sofia_db'),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', 'sofia123strong')
}

# ============================================================================
# MAPEAMENTOS GEOGRÁFICOS (da v2.0)
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
    'ITA': ('Brasil', ['Aerospace', 'Defense Tech', 'Engineering']),
    'UFRGS': ('Brasil', ['AI', 'Agro-tech', 'Materials']),

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

def extract_country_from_text(text):
    """Extrai país/universidade de um texto (autores, empresa, etc)"""
    if not text:
        return None, None

    text_lower = str(text).lower()

    # Primeiro procura universidades
    for uni, (country, specs) in UNIVERSITIES.items():
        if uni.lower() in text_lower:
            return country, uni

    # Depois procura países
    for country in CONTINENTS.keys():
        if country.lower() in text_lower:
            return country, None

    return None, None

def get_continent(country):
    """Retorna continente do país"""
    return CONTINENTS.get(country, 'Outros')

# ============================================================================

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

os.makedirs('analytics/premium-insights', exist_ok=True)

print("📊 Coletando TODOS os dados...")

# 1. ARXIV PAPERS
cur.execute("""
    SELECT arxiv_id, title, authors, categories, published_date, abstract
    FROM arxiv_ai_papers
    ORDER BY published_date DESC
    LIMIT 50
""")
papers = cur.fetchall()
print(f"   📚 ArXiv Papers: {len(papers)}")

# 2. FUNDING ROUNDS
cur.execute("""
    SELECT company_name, sector, amount_usd, valuation_usd, round_type, announced_date
    FROM sofia.funding_rounds
    ORDER BY announced_date DESC
    LIMIT 50
""")
funding = cur.fetchall()
print(f"   💰 Funding Rounds: {len(funding)}")

# 3. AI COMPANIES
cur.execute("""
    SELECT name, country, category, total_funding_usd, employee_count, founded_year
    FROM ai_companies
    ORDER BY total_funding_usd DESC NULLS LAST
    LIMIT 50
""")
companies = cur.fetchall()
print(f"   🚀 AI Companies: {len(companies)}")

# 4. EPO PATENTS
cur.execute("""
    SELECT title, applicants, publication_date, classifications
    FROM epo_patents
    ORDER BY publication_date DESC
    LIMIT 50
""")
patents_epo = cur.fetchall()
print(f"   📜 EPO Patents: {len(patents_epo)}")

# 5. WIPO CHINA PATENTS
cur.execute("""
    SELECT title, applicants, publication_date, ipc_codes
    FROM wipo_china_patents
    ORDER BY publication_date DESC
    LIMIT 50
""")
patents_china = cur.fetchall()
print(f"   🇨🇳 WIPO China Patents: {len(patents_china)}")

# 6. OPENALEX PAPERS
cur.execute("""
    SELECT title, authors_raw, publication_date, cited_by_count
    FROM openalex_papers
    ORDER BY cited_by_count DESC NULLS LAST
    LIMIT 50
""")
openalex = cur.fetchall()
print(f"   📖 OpenAlex Papers: {len(openalex)}")

# 7. B3
cur.execute("""
    WITH latest AS (
        SELECT ticker, company, price, change_pct, sector,
               ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY collected_at DESC) as rn
        FROM market_data_brazil
    )
    SELECT ticker, company, price, change_pct, sector
    FROM latest WHERE rn = 1
    ORDER BY change_pct DESC
""")
b3 = cur.fetchall()
print(f"   📈 B3: {len(b3)}")

print("\n💎 Gerando insights...\n")

# GERAR INSIGHTS
insights = f"""
════════════════════════════════════════════════════════════════
   🌍 SOFIA PULSE - PREMIUM INSIGHTS v4.0
   Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}
════════════════════════════════════════════════════════════════

📊 DADOS COLETADOS:
- {len(papers)} papers ArXiv (AI/ML)
- {len(openalex)} papers OpenAlex (global)
- {len(patents_epo)} patents EPO (Europa)
- {len(patents_china)} patents WIPO China
- {len(funding)} funding rounds
- {len(companies)} AI companies
- {len(b3)} ações B3


🔬 PAPERS ACADÊMICOS (ArXiv AI/ML)
-------------------------------------------------------------------

🔥 TOP PAPERS RECENTES:

"""

for arxiv_id, title, authors, cats, pub_date, abstract in papers[:10]:
    authors_str = ', '.join(authors[:3]) if authors else 'N/A'
    cats_str = ', '.join(cats[:3]) if cats else 'N/A'
    insights += f"   📄 {title}\n"
    insights += f"      Autores: {authors_str}\n"
    insights += f"      Categorias: {cats_str}\n"
    insights += f"      Data: {pub_date}\n\n"

# Análise por categoria
if papers:
    from collections import Counter
    all_cats = []
    for _, _, _, cats, _, _ in papers:
        if cats:
            all_cats.extend(cats)

    top_cats = Counter(all_cats).most_common(10)
    insights += "\n📊 TOP CATEGORIAS DE PESQUISA:\n\n"
    for cat, count in top_cats:
        insights += f"   {cat:20s} | {count:3d} papers\n"

insights += "\n\n🚀 AI COMPANIES GLOBAIS\n"
insights += "-------------------------------------------------------------------\n\n"

if companies:
    # Por país
    from collections import defaultdict
    by_country = defaultdict(list)
    for name, country, category, funding, employees, year in companies:
        by_country[country or 'Unknown'].append((name, category, funding))

    insights += "🌍 EMPRESAS DE IA POR PAÍS:\n\n"
    for country, comps in sorted(by_country.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        insights += f"   {country}: {len(comps)} empresas\n"
        for name, cat, funding in comps[:3]:
            funding_m = funding / 1_000_000 if funding else 0
            insights += f"      • {name} ({cat}) - ${funding_m:.1f}M funding\n"
        insights += "\n"

insights += "\n📜 PATENTS (Europa + China)\n"
insights += "-------------------------------------------------------------------\n\n"

insights += f"🇪🇺 EPO (Europa): {len(patents_epo)} patents recentes\n"
insights += f"🇨🇳 WIPO China: {len(patents_china)} patents recentes\n\n"

if patents_epo:
    insights += "🔥 TOP PATENTS EPO:\n\n"
    for title, applicants, date, classes in patents_epo[:5]:
        appl_str = ', '.join(applicants[:2]) if applicants else 'N/A'
        insights += f"   • {title}\n"
        insights += f"     Empresas: {appl_str}\n"
        insights += f"     Data: {date}\n\n"

if patents_china:
    insights += "🔥 TOP PATENTS CHINA:\n\n"
    for title, applicants, date, ipc in patents_china[:5]:
        appl_str = ', '.join(applicants[:2]) if applicants else 'N/A'
        insights += f"   • {title}\n"
        insights += f"     Empresas: {appl_str}\n"
        insights += f"     Data: {date}\n\n"

insights += "\n💰 FUNDING ROUNDS\n"
insights += "-------------------------------------------------------------------\n\n"

if funding:
    insights += "🔥 TOP RODADAS:\n\n"
    for company, sector, amount, val, round_type, date in funding[:10]:
        amount_b = amount / 1_000_000_000 if amount else 0
        val_b = val / 1_000_000_000 if val else 0
        insights += f"   • {company} ({sector})\n"
        insights += f"     {round_type} - ${amount_b:.1f}B"
        if val:
            insights += f" | Valuation: ${val_b:.1f}B"
        insights += f"\n     Data: {date}\n\n"

insights += "\n📈 MERCADO B3 (Brasil)\n"
insights += "-------------------------------------------------------------------\n\n"

if b3:
    insights += "🔥 TOP AÇÕES:\n\n"
    for ticker, company, price, change, sector in b3[:10]:
        symbol = "📈" if change > 0 else "📉"
        sector_str = sector or 'N/A'
        insights += f"   {symbol} {ticker:8s} | {company:25s} | {change:+6.2f}% | {sector_str}\n"

insights += "\n\n🌍 ANÁLISE GEO-LOCALIZADA\n"
insights += "-------------------------------------------------------------------\n\n"

# Análise de Papers por Continente/País/Universidade
if papers:
    insights += "📚 PESQUISA ACADÊMICA POR REGIÃO:\n\n"

    countries_found = []
    universities_found = defaultdict(int)
    continents_found = []

    for arxiv_id, title, authors, cats, pub_date, abstract in papers:
        authors_str = ', '.join(authors) if authors else ''
        country, uni = extract_country_from_text(authors_str)

        if country:
            countries_found.append(country)
            continents_found.append(get_continent(country))

        if uni:
            universities_found[uni] += 1

    if continents_found:
        continent_counts = Counter(continents_found)
        insights += "   🗺️  Papers por Continente:\n"
        for cont, count in continent_counts.most_common(5):
            pct = (count / len(papers)) * 100
            insights += f"      {cont}: {count} papers ({pct:.1f}%)\n"
        insights += "\n"

    if countries_found:
        country_counts = Counter(countries_found)
        insights += "   🌐 Top Países em Pesquisa:\n"
        for country, count in country_counts.most_common(5):
            insights += f"      {country}: {count} papers\n"
        insights += "\n"

    if universities_found:
        insights += "   🎓 Universidades Mais Ativas:\n"
        for uni, count in sorted(universities_found.items(), key=lambda x: x[1], reverse=True)[:5]:
            specs = UNIVERSITIES.get(uni, (None, []))[1]
            specs_str = ", ".join(specs[:2]) if specs else "Geral"
            insights += f"      • {uni}: {count} papers (Especialidade: {specs_str})\n"
        insights += "\n"

# Análise de Empresas de IA por Continente/País
if companies:
    insights += "🚀 EMPRESAS DE IA POR REGIÃO:\n\n"

    companies_by_continent = defaultdict(list)
    companies_by_country = defaultdict(list)

    for name, country, category, funding, employees, year in companies:
        if country:
            continent = get_continent(country)
            companies_by_continent[continent].append((name, country, funding))
            companies_by_country[country].append((name, category, funding))

    if companies_by_continent:
        insights += "   🗺️  Por Continente:\n"
        for cont, comps in sorted(companies_by_continent.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            total_funding = sum(c[2] if c[2] else 0 for c in comps)
            total_funding_b = total_funding / 1_000_000_000
            insights += f"      {cont}: {len(comps)} empresas (${total_funding_b:.1f}B funding total)\n"
        insights += "\n"

    if companies_by_country:
        insights += "   🌐 Top 5 Países:\n"
        for country, comps in sorted(companies_by_country.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            total_funding = sum(c[2] if c[2] else 0 for c in comps)
            total_funding_b = total_funding / 1_000_000_000
            insights += f"      • {country}: {len(comps)} empresas (${total_funding_b:.1f}B)\n"

            # Mostrar especialização regional
            if country in REGIONAL_SPECIALIZATIONS:
                specs = REGIONAL_SPECIALIZATIONS[country]
                insights += f"        Especialização: {', '.join(specs)}\n"
        insights += "\n"

# Análise de Funding por Região
if funding:
    insights += "💰 INVESTIMENTOS POR REGIÃO:\n\n"

    # Agrupar funding por país (extrair do nome da empresa ou setor)
    funding_by_continent = defaultdict(lambda: {'deals': 0, 'total': 0})

    for company, sector, amount, val, round_type, date in funding:
        # Tentar extrair país do nome da empresa
        country, _ = extract_country_from_text(company)

        if country:
            continent = get_continent(country)
            funding_by_continent[continent]['deals'] += 1
            funding_by_continent[continent]['total'] += amount if amount else 0

    if funding_by_continent:
        insights += "   🗺️  Por Continente:\n"
        for cont, data in sorted(funding_by_continent.items(), key=lambda x: x[1]['total'], reverse=True):
            amount_b = data['total'] / 1_000_000_000
            deals = data['deals']
            insights += f"      {cont}: ${amount_b:.2f}B em {deals} deals\n"
        insights += "\n"

insights += "\n💡 ANÁLISE INTELIGENTE\n"
insights += "-------------------------------------------------------------------\n\n"

# Detectar tendências
ai_papers_count = sum(1 for _, _, _, cats, _, _ in papers if cats and any('AI' in c or 'LG' in c for c in cats))
cv_papers_count = sum(1 for _, _, _, cats, _, _ in papers if cats and any('CV' in c for c in cats))
nlp_papers_count = sum(1 for _, _, _, cats, _, _ in papers if cats and any('CL' in c for c in cats))

insights += f"🎯 TENDÊNCIAS EM PESQUISA:\n\n"
insights += f"   • AI/ML: {ai_papers_count} papers (últimos 30 dias)\n"
insights += f"   • Computer Vision: {cv_papers_count} papers\n"
insights += f"   • NLP: {nlp_papers_count} papers\n\n"

if companies:
    usa_companies = [c for c in companies if c[1] == 'USA']
    china_companies = [c for c in companies if c[1] == 'China']
    brasil_companies = [c for c in companies if c[1] in ['Brazil', 'Brasil', 'BR']]

    insights += f"🌍 CONCENTRAÇÃO GEOGRÁFICA DE IA:\n\n"
    insights += f"   • USA: {len(usa_companies)} empresas\n"
    insights += f"   • China: {len(china_companies)} empresas\n"
    insights += f"   • Brasil: {len(brasil_companies)} empresas\n"
    insights += f"   • Europa: {len(patents_epo)} patents recentes\n\n"

insights += """

═══════════════════════════════════════════════════════════════
Gerado por Sofia Pulse v4.0 - Dados reais dos collectors
═══════════════════════════════════════════════════════════════
"""

# Salvar
with open('analytics/premium-insights/latest-v4.txt', 'w', encoding='utf-8') as f:
    f.write(insights)

with open('analytics/premium-insights/latest-v4.md', 'w', encoding='utf-8') as f:
    f.write(insights)

# Também como latest-geo para compatibilidade com email
with open('analytics/premium-insights/latest-geo.txt', 'w', encoding='utf-8') as f:
    f.write(insights)

with open('analytics/premium-insights/latest-geo.md', 'w', encoding='utf-8') as f:
    f.write(insights)

print("✅ Insights v4.0 gerados!")
print(f"📄 analytics/premium-insights/latest-v4.txt")
print(f"\nPreview:\n{insights[:800]}...\n")

# Export CSVs
print("📤 Exportando CSVs...")

# Papers CSV
cur.execute("""
    SELECT arxiv_id, title, authors, categories, published_date
    FROM arxiv_ai_papers
    ORDER BY published_date DESC
    LIMIT 100
""")
with open('analytics/premium-insights/arxiv_papers.csv', 'w', encoding='utf-8') as f:
    f.write("arxiv_id,title,authors,categories,published_date\n")
    for row in cur.fetchall():
        # Simplificar arrays para CSV
        arxiv_id, title, authors, cats, date = row
        authors_str = ';'.join(authors) if authors else ''
        cats_str = ';'.join(cats) if cats else ''
        f.write(f'"{arxiv_id}","{title}","{authors_str}","{cats_str}","{date}"\n')

# Companies CSV
cur.execute("""
    SELECT name, country, category, total_funding_usd, employee_count, founded_year
    FROM ai_companies
    ORDER BY total_funding_usd DESC NULLS LAST
""")
with open('analytics/premium-insights/ai_companies.csv', 'w', encoding='utf-8') as f:
    f.write("name,country,category,total_funding_usd,employee_count,founded_year\n")
    for row in cur.fetchall():
        f.write(','.join(str(x) if x is not None else '' for x in row) + '\n')

print("✅ CSVs exportados!")
print("   - arxiv_papers.csv")
print("   - ai_companies.csv")

conn.close()

print("\n🎉 CONCLUÍDO! Agora COM papers, patents, startups e tudo mais!")
