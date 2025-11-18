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

# Mapeamento de categorias ArXiv para nomes legíveis
ARXIV_CATEGORIES = {
    'cs.AI': 'Inteligência Artificial',
    'cs.LG': 'Machine Learning',
    'cs.CV': 'Visão Computacional',
    'cs.CL': 'Processamento de Linguagem Natural (NLP)',
    'cs.RO': 'Robótica',
    'cs.NE': 'Computação Neural e Evolutiva',
    'cs.MA': 'Sistemas Multi-Agente',
    'cs.HC': 'Interação Humano-Computador',
    'cs.IR': 'Recuperação de Informação',
    'cs.CR': 'Criptografia e Segurança',
    'stat.ML': 'Machine Learning (Estatística)',
    'math.OC': 'Otimização e Controle',
    'q-bio': 'Biologia Quantitativa',
    'eess.IV': 'Processamento de Imagens',
    'eess.AS': 'Processamento de Áudio',
}

def translate_category(cat):
    """Traduz categoria ArXiv para português"""
    return ARXIV_CATEGORIES.get(cat, cat)

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
    SELECT title, applicant, filing_date, ipc_classification
    FROM epo_patents
    ORDER BY filing_date DESC
    LIMIT 50
""")
patents_epo = cur.fetchall()
print(f"   📜 EPO Patents: {len(patents_epo)}")

# 5. WIPO CHINA PATENTS
cur.execute("""
    SELECT title, applicant, filing_date, ipc_classification
    FROM wipo_china_patents
    ORDER BY filing_date DESC
    LIMIT 50
""")
patents_china = cur.fetchall()
print(f"   🇨🇳 WIPO China Patents: {len(patents_china)}")

# 6. OPENALEX PAPERS
cur.execute("""
    SELECT title, authors, publication_date, cited_by_count
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
    # Traduzir categorias
    cats_translated = [translate_category(c) for c in cats[:3]] if cats else ['N/A']
    cats_str = ', '.join(cats_translated)
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
        cat_translated = translate_category(cat)
        insights += f"   {cat_translated:45s} | {count:3d} papers\n"

insights += "\n\n🚀 AI COMPANIES GLOBAIS\n"
insights += "-------------------------------------------------------------------\n\n"

if companies:
    # Por país
    from collections import defaultdict
    by_country = defaultdict(list)
    for name, country, category, comp_funding, employees, year in companies:
        by_country[country or 'Unknown'].append((name, category, comp_funding))

    insights += "🌍 EMPRESAS DE IA POR PAÍS:\n\n"
    for country, comps in sorted(by_country.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        insights += f"   {country}: {len(comps)} empresas\n"
        for name, cat, comp_funding in comps[:3]:
            funding_m = comp_funding / 1_000_000 if comp_funding else 0
            insights += f"      • {name} ({cat}) - ${funding_m:.1f}M funding\n"
        insights += "\n"

insights += "\n📜 PATENTS (Europa + China)\n"
insights += "-------------------------------------------------------------------\n\n"

insights += f"🇪🇺 EPO (Europa): {len(patents_epo)} patents recentes\n"
insights += f"🇨🇳 WIPO China: {len(patents_china)} patents recentes\n\n"

if patents_epo:
    insights += "🔥 TOP PATENTS EPO:\n\n"
    for title, applicant, date, ipc_class in patents_epo[:5]:
        appl_str = applicant if applicant else 'N/A'
        insights += f"   • {title}\n"
        insights += f"     Empresa: {appl_str}\n"
        insights += f"     Data: {date}\n\n"

if patents_china:
    insights += "🔥 TOP PATENTS CHINA:\n\n"
    for title, applicant, date, ipc_class in patents_china[:5]:
        appl_str = applicant if applicant else 'N/A'
        insights += f"   • {title}\n"
        insights += f"     Empresa: {appl_str}\n"
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

    for name, country, category, comp_funding, employees, year in companies:
        if country:
            continent = get_continent(country)
            companies_by_continent[continent].append((name, country, comp_funding))
            companies_by_country[country].append((name, category, comp_funding))

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

insights += "\n🔥 INSIGHTS ACIONÁVEIS (ANÁLISE PROFUNDA)\n"
insights += "═══════════════════════════════════════════════════════════════\n\n"

# 1. ANÁLISE DE CONCENTRAÇÃO DE CAPITAL
if companies:
    usa_companies = [c for c in companies if c[1] == 'USA']
    china_companies = [c for c in companies if c[1] == 'China']
    brasil_companies = [c for c in companies if c[1] in ['Brazil', 'Brasil', 'BR']]

    usa_funding = sum(c[3] if c[3] else 0 for c in usa_companies)
    china_funding = sum(c[3] if c[3] else 0 for c in china_companies)

    insights += "💰 INSIGHT #1: CONCENTRAÇÃO DE CAPITAL EM IA\n\n"

    if len(usa_companies) > 0:
        avg_usa = usa_funding / len(usa_companies) / 1_000_000
        insights += f"   📊 USA: {len(usa_companies)} empresas com ${usa_funding/1e9:.1f}B total\n"
        insights += f"      → Média: ${avg_usa:.0f}M por empresa\n"

    if len(china_companies) > 0:
        avg_china = china_funding / len(china_companies) / 1_000_000
        insights += f"   📊 China: {len(china_companies)} empresas com ${china_funding/1e9:.1f}B total\n"
        insights += f"      → Média: ${avg_china:.0f}M por empresa\n\n"

    if len(usa_companies) > 0 and len(china_companies) > 0:
        if avg_usa > avg_china * 1.5:
            insights += "   💡 CONCLUSÃO: USA aposta em unicórnios gigantes (mega-rounds).\n"
            insights += "      China pulveriza capital em mais empresas (menor risco).\n\n"
            insights += "   🎯 OPORTUNIDADE: Investidores conservadores → China (diversificação)\n"
            insights += "      Investidores agressivos → USA (home runs)\n\n"

    insights += f"   ⚠️  ALERTA BRASIL: {len(brasil_companies)} empresas de IA com funding significativo.\n"
    insights += "      Mercado brasileiro está SUBPENETRADO em IA.\n"
    insights += "      → OPORTUNIDADE: Blue Ocean para founders brasileiros em IA B2B.\n\n"

# 2. ANÁLISE DE TENDÊNCIAS EM FUNDING
if funding:
    insights += "\n🎯 INSIGHT #2: PARA ONDE ESTÁ INDO O DINHEIRO?\n\n"

    # Agrupar por setor
    sector_funding = defaultdict(lambda: {'count': 0, 'total': 0, 'companies': []})
    for company, sector, amount, val, round_type, date in funding:
        sector_funding[sector]['count'] += 1
        sector_funding[sector]['total'] += amount if amount else 0
        sector_funding[sector]['companies'].append((company, amount))

    # Top 3 setores
    top_sectors = sorted(sector_funding.items(), key=lambda x: x[1]['total'], reverse=True)[:3]

    for sector, data in top_sectors:
        total_b = data['total'] / 1_000_000_000
        insights += f"   🔥 {sector}: ${total_b:.1f}B em {data['count']} deals\n"
        # Pegar maior deal
        if data['companies']:
            top_company, top_amount = max(data['companies'], key=lambda x: x[1] if x[1] else 0)
            insights += f"      → Maior: {top_company} (${top_amount/1e9:.1f}B)\n"

    insights += "\n   💡 CONCLUSÃO: "
    if len(top_sectors) > 0:
        top_sector_name = top_sectors[0][0]
        top_sector_total = top_sectors[0][1]['total'] / 1e9
        insights += f"{top_sector_name} domina com ${top_sector_total:.1f}B.\n"
        insights += f"   🎯 OPORTUNIDADE: Startups em {top_sector_name} têm vento a favor.\n"
        insights += f"      Investidores estão ATIVAMENTE procurando deals nesse setor.\n\n"

# 3. ANÁLISE GEOPOLÍTICA (PESQUISA vs COMERCIALIZAÇÃO)
insights += "\n🌍 INSIGHT #3: QUEM PESQUISA vs QUEM COMERCIALIZA\n\n"

usa_papers = sum(1 for _, _, authors, _, _, _ in papers if authors and any('USA' in str(a) or 'US' in str(a) for a in authors))
china_papers = sum(1 for _, _, authors, _, _, _ in papers if authors and any('China' in str(a) for a in authors))
brasil_papers = sum(1 for _, _, authors, _, _, _ in papers if authors and any('Brazil' in str(a) or 'Brasil' in str(a) for a in authors))

if companies:
    insights += f"   📚 PESQUISA: USA={usa_papers} papers | China={china_papers} | Brasil={brasil_papers}\n"
    insights += f"   💰 COMERCIALIZAÇÃO: USA={len(usa_companies)} empresas | China={len(china_companies)} | Brasil={len(brasil_companies)}\n\n"

    if len(patents_epo) > 5 and len([c for c in companies if c[1] in ['Germany', 'France', 'UK']]) < 3:
        insights += "   ⚠️  ALERTA EUROPA: {len(patents_epo)} patents mas poucas empresas de IA.\n"
        insights += "      → Europa pesquisa mas NÃO comercializa (vale da morte).\n"
        insights += "      🎯 OPORTUNIDADE: Licenciar patents europeus baratos e comercializar nos USA.\n\n"

    if brasil_papers > 0 and len(brasil_companies) == 0:
        insights += f"   ⚠️  ALERTA BRASIL: {brasil_papers} papers mas 0 empresas com funding significativo.\n"
        insights += "      → Universidades brasileiras produzem pesquisa, mas não viram startups.\n"
        insights += "      🎯 OPORTUNIDADE: Spin-offs de USP/Unicamp/UFMG em Agro-tech AI.\n"
        insights += "         Founders técnicos precisam de: capital semente + mentoria go-to-market.\n\n"

# 4. ANÁLISE DE MARKET TIMING (B3)
if b3 and len(b3) > 0:
    insights += "\n📈 INSIGHT #4: SINAIS DO MERCADO BRASILEIRO\n\n"

    positive = [s for s in b3 if s[3] > 0]
    negative = [s for s in b3 if s[3] < 0]

    insights += f"   📊 Balanço: {len(positive)} em alta vs {len(negative)} em queda\n"

    if len(positive) > len(negative) * 2:
        insights += "   ✅ CONCLUSÃO: Mercado brasileiro em modo RISK-ON.\n"
        insights += "      → Momento favorável para IPOs e captações.\n\n"
    elif len(negative) > len(positive) * 2:
        insights += "   ⚠️  CONCLUSÃO: Mercado brasileiro em modo RISK-OFF.\n"
        insights += "      → Momento para consolidar posições, não para levantar capital.\n\n"

    # Setores em alta
    if positive:
        sectors_up = defaultdict(int)
        for ticker, company, price, change, sector in positive[:5]:
            if sector:
                sectors_up[sector] += 1

        if sectors_up:
            top_sector_up = max(sectors_up.items(), key=lambda x: x[1])
            insights += f"   🔥 Setor em ALTA: {top_sector_up[0]} ({top_sector_up[1]} ações subindo)\n"
            insights += f"      → Investidores estão rotacionando capital para {top_sector_up[0]}.\n\n"

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
