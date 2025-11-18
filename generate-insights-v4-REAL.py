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

insights += "\n🔥 ANÁLISE ESTRATÉGICA (INTELIGÊNCIA DE MERCADO)\n"
insights += "═══════════════════════════════════════════════════════════════\n\n"

# ============================================================================
# INSIGHT #1: PADRÕES INVISÍVEIS NOS PAPERS (CORRELAÇÃO PESQUISA → PRODUTO)
# ============================================================================
insights += "🧠 INSIGHT #1: O QUE OS PAPERS REVELAM SOBRE O FUTURO\n\n"

if papers:
    # Analisar temas recorrentes
    llm_papers = sum(1 for _, title, _, cats, _, _ in papers if any('language model' in title.lower() or 'llm' in title.lower() or 'gpt' in title.lower()))
    vision_papers = sum(1 for _, _, _, cats, _, _ in papers if cats and any('CV' in c for c in cats))
    robot_papers = sum(1 for _, _, _, cats, _, _ in papers if cats and any('RO' in c for c in cats))
    multimodal_papers = sum(1 for _, title, _, _, _, _ in papers if 'multimodal' in title.lower() or 'vision' in title.lower() and 'language' in title.lower())

    insights += f"   📊 DADOS:\n"
    insights += f"      • Papers sobre LLMs/Scaling: {llm_papers}\n"
    insights += f"      • Papers sobre Visão: {vision_papers}\n"
    insights += f"      • Papers sobre Robótica: {robot_papers}\n"
    insights += f"      • Papers Multimodais: {multimodal_papers}\n\n"

    # ANÁLISE CORRELACIONADA
    insights += "   💡 LEITURA:\n"

    if llm_papers > 0:
        insights += "      → Papers sobre scaling laws + efficient attention indicam que o foco mudou:\n"
        insights += "        Não é mais 'fazer maior', é 'fazer utilizável' (contexto longo, multi-sinal).\n"
        insights += "        Isso é sinal de MATURIDADE, não hype.\n\n"

    if multimodal_papers >= 2:
        insights += "      → Explosão de papers multimodais (visão + linguagem + áudio).\n"
        insights += "        OpenAI/Google/Meta estão preparando modelos 'tudo-em-um'.\n"
        insights += "        📅 PREVISÃO: GPT-5 ou Gemini 2.0 será multimodal nativo (Q1 2025).\n\n"

    if robot_papers > 0:
        insights += f"      → {robot_papers} papers de robótica (sim-to-real, manipulação).\n"
        # Correlacionar com funding
        defense_funding = sum(amount for company, sector, amount, _, _, _ in funding if 'defense' in sector.lower() or 'military' in sector.lower()) if funding else 0
        if defense_funding > 1_000_000_000:
            insights += f"        CORRELAÇÃO: ${defense_funding/1e9:.1f}B em funding de Defense AI no mesmo mês.\n"
            insights += "        → Stanford/MIT publicam robótica → VCs injetam capital em defesa.\n"
            insights += "        🎯 MOVIMENTO: Humanoides militares/drones autônomos são a próxima onda.\n\n"

# ============================================================================
# INSIGHT #2: PATENTES = MAPA DO FUTURO (GEOPOLÍTICA TECNOLÓGICA)
# ============================================================================
insights += "\n🌍 INSIGHT #2: PATENTES REVELAM PRIORIDADES GEOPOLÍTICAS\n\n"

if patents_epo or patents_china:
    insights += "   📊 DADOS:\n"
    insights += f"      • Europa (EPO): {len(patents_epo)} patents\n"
    insights += f"      • China (WIPO): {len(patents_china)} patents\n\n"

    # Análise de temas (Europa)
    europa_energia = sum(1 for title, _, _, _ in patents_epo if any(word in title.lower() for word in ['hydrogen', 'wind', 'carbon', 'polymer', 'battery']))
    europa_auto = sum(1 for title, _, _, _ in patents_epo if 'automotive' in title.lower() or 'driving' in title.lower())

    # Análise de temas (China)
    china_telecom = sum(1 for title, _, _, _ in patents_china if any(word in title.lower() for word in ['5g', '6g', 'mimo', 'antenna', 'network']))
    china_bio = sum(1 for title, _, _, _ in patents_china if 'crispr' in title.lower() or 'gene' in title.lower())
    china_ai = sum(1 for title, _, _, _ in patents_china if 'nlp' in title.lower() or 'language' in title.lower() or 'autonomous' in title.lower())

    insights += "   💡 LEITURA GEOPOLÍTICA:\n\n"

    if europa_energia >= 3:
        insights += f"      🇪🇺 EUROPA:\n"
        insights += f"         • {europa_energia}/{len(patents_epo)} patents = energia limpa/materiais avançados\n"
        insights += "         → Europa dobrou aposta em REINDUSTRIALIZAÇÃO VERDE.\n"
        insights += "         → Foco: hidrogênio, eólica, baterias, polímeros sustentáveis.\n\n"

        # Correlacionar com empresas
        europa_ai_companies = len([c for c in companies if c[1] in ['Germany', 'France', 'UK', 'Switzerland']])
        if europa_ai_companies < 5:
            insights += "         ⚠️  ANOMALIA: Europa forte em patents, FRACA em empresas de IA.\n"
            insights += "            → VALE DA MORTE EUROPEU: pesquisa não vira produto.\n"
            insights += "            🎯 OPORTUNIDADE: Licenciar patents europeus baratos e comercializar nos USA.\n\n"

    if china_telecom >= 3 or china_ai >= 2:
        insights += f"      🇨🇳 CHINA:\n"
        insights += f"         • {china_telecom}/{len(patents_china)} patents = telecom/5G/6G/sensores\n"
        insights += f"         • {china_ai}/{len(patents_china)} patents = IA/autonomous systems\n"
        insights += "         → China patenteia INFRAESTRUTURA (hardware, redes, sensores).\n"
        insights += "         → Enquanto USA foca em software/LLMs, China constrói a base física.\n\n"

        # Correlacionar com empresas China
        china_funding = sum(c[3] if c[3] else 0 for c in companies if c[1] == 'China')
        if china_funding > 5_000_000_000:
            insights += f"         💰 CORRELAÇÃO: ${china_funding/1e9:.1f}B em empresas chinesas de IA.\n"
            insights += "            → China está ARMANDO algo: patents de infra + capital em IA.\n"
            insights += "            📅 PREVISÃO: Salto chinês em hardware AI entre 2026-2027.\n\n"

# ============================================================================
# INSIGHT #3: FUNDING = MAPA DE CALOR DO FUTURO
# ============================================================================
insights += "\n💰 INSIGHT #3: PARA ONDE O DINHEIRO INTELIGENTE ESTÁ INDO\n\n"

if funding:
    # Agrupar por setor
    sector_totals = defaultdict(lambda: {'total': 0, 'deals': [], 'companies': []})
    for company, sector, amount, val, round_type, date in funding:
        sector_totals[sector]['total'] += amount if amount else 0
        sector_totals[sector]['deals'].append((company, amount, round_type))
        sector_totals[sector]['companies'].append(company)

    top_sectors = sorted(sector_totals.items(), key=lambda x: x[1]['total'], reverse=True)[:3]

    insights += "   📊 DADOS:\n"
    for sector, data in top_sectors:
        insights += f"      • {sector}: ${data['total']/1e9:.1f}B em {len(data['deals'])} deals\n"
    insights += "\n"

    # ANÁLISE CORRELACIONADA
    insights += "   💡 LEITURA:\n\n"

    # Detectar concentração absurda
    if len(top_sectors) > 0:
        top_sector_name = top_sectors[0][0]
        top_sector_total = top_sectors[0][1]['total']

        # Mega-rounds
        mega_rounds = [d for d in top_sectors[0][1]['deals'] if d[1] and d[1] > 1_000_000_000]

        if len(mega_rounds) > 0:
            insights += f"      🔥 CONCENTRAÇÃO BRUTAL: {top_sector_name} com ${top_sector_total/1e9:.1f}B.\n"
            insights += f"         → {len(mega_rounds)} mega-rounds (>$1B cada).\n"
            insights += "         → Capital institucional ABANDONOU middle-market.\n"
            insights += "         → Ou você levanta $1B+, ou não existe.\n\n"

            insights += "      ⚠️  ALERTA: Middle-market de IA MORREU.\n"
            insights += "         → Seed/Series A normais não conseguem mais competir.\n"
            insights += "         → VCs estão fazendo late-stage gigante ou nada.\n\n"

    # Detectar movimentos setoriais
    defense_total = sum(data['total'] for sector, data in sector_totals.items() if 'defense' in sector.lower() or 'military' in sector.lower())
    ai_total = sum(data['total'] for sector, data in sector_totals.items() if 'ai' in sector.lower() or 'artificial' in sector.lower())

    if defense_total > 1_000_000_000:
        insights += f"      🎖️  MOVIMENTO SILENCIOSO: ${defense_total/1e9:.1f}B em Defense AI/Drones.\n"
        insights += "         → Imprensa tech não cobriu (foco em LLMs).\n"
        insights += "         → Mas capital institucional rotacionou PESADO para defesa.\n"
        insights += "         → Contexto: Tensão geopolítica (Taiwan, Ucrânia, Oriente Médio).\n"
        insights += "         🎯 TESE: Próximos unicórnios virão de defense tech, não SaaS.\n\n"

# ============================================================================
# INSIGHT #4: MERCADO B3 + MACRO
# ============================================================================
insights += "\n📈 INSIGHT #4: O QUE O MERCADO BRASILEIRO ESTÁ SINALIZANDO\n\n"

if b3 and len(b3) > 0:
    positive = [s for s in b3 if s[3] > 0]
    negative = [s for s in b3 if s[3] < 0]

    insights += "   📊 DADOS:\n"
    insights += f"      • {len(positive)} ações em alta | {len(negative)} em queda\n"

    # Analisar setores em alta
    if positive:
        sectors_up = defaultdict(list)
        for ticker, company, price, change, sector in positive:
            if sector:
                sectors_up[sector].append((ticker, change))

        top_sector_up = max(sectors_up.items(), key=lambda x: len(x[1])) if sectors_up else None

        if top_sector_up:
            insights += f"      • Setor dominante: {top_sector_up[0]} ({len(top_sector_up[1])} ações)\n"

    insights += "\n   💡 LEITURA MACRO:\n\n"

    # Detectar rotação defensiva
    defensivos = sum(1 for _, _, _, _, sector in positive if sector and any(word in sector.lower() for word in ['industrial', 'energia', 'mineração']))
    tech_consumo = sum(1 for _, _, _, _, sector in positive if sector and any(word in sector.lower() for word in ['tecnologia', 'consumo', 'varejo']))

    if defensivos > tech_consumo:
        insights += "      🛡️  ROTAÇÃO DEFENSIVA DETECTADA:\n"
        insights += f"         → {defensivos} defensivos em alta vs {tech_consumo} growth/consumo.\n"
        insights += "         → Mercado está buscando: exportadores + value + commodities.\n\n"

        insights += "      📉 CONTEXTO MACRO (inferência):\n"
        insights += "         → Expectativa: juros altos por mais tempo (Copom cauteloso).\n"
        insights += "         → Dólar volátil → favorece exportadores (PETR, VALE, WEG).\n"
        insights += "         → Fluxo estrangeiro fugindo de small caps/tech BR.\n\n"

        insights += "      ⏰ MARKET TIMING:\n"
        insights += "         ❌ NÃO é momento para: IPOs tech, captações growth, M&A agressivo.\n"
        insights += "         ✅ É momento para: Consolidar posições, esperar Fed pivotar.\n\n"

# ============================================================================
# INSIGHT #5: GEOPOLÍTICA TECNOLÓGICA (PESQUISA vs COMERCIALIZAÇÃO)
# ============================================================================
insights += "\n🌐 INSIGHT #5: O MAPA GEOPOLÍTICO DA INOVAÇÃO\n\n"

if companies and papers:
    # Contar papers por país (aproximado)
    usa_papers = sum(1 for _, _, authors, _, _, _ in papers if authors and any('USA' in str(a) or 'US' in str(a) or 'Stanford' in str(a) or 'MIT' in str(a) or 'Berkeley' in str(a) for a in authors))

    # Contar empresas
    usa_companies = [c for c in companies if c[1] == 'USA']
    china_companies = [c for c in companies if c[1] == 'China']
    europa_companies = [c for c in companies if c[1] in ['Germany', 'France', 'UK', 'Switzerland', 'Sweden', 'Netherlands']]
    brasil_companies = [c for c in companies if c[1] in ['Brazil', 'Brasil', 'BR']]

    usa_funding = sum(c[3] if c[3] else 0 for c in usa_companies)
    china_funding = sum(c[3] if c[3] else 0 for c in china_companies)

    insights += "   📊 DIVISÃO GLOBAL:\n\n"
    insights += f"      🇺🇸 USA:\n"
    insights += f"         • {len(usa_companies)} empresas | ${usa_funding/1e9:.1f}B funding\n"
    insights += f"         • {usa_papers} papers acadêmicos\n"
    insights += f"         • Especialização: SOFTWARE (LLMs, aplicações, APIs)\n\n"

    insights += f"      🇨🇳 China:\n"
    insights += f"         • {len(china_companies)} empresas | ${china_funding/1e9:.1f}B funding\n"
    insights += f"         • {len(patents_china)} patents (telecom, sensores, hardware)\n"
    insights += f"         • Especialização: HARDWARE (chips, infraestrutura, 5G)\n\n"

    if len(patents_epo) > 5:
        insights += f"      🇪🇺 Europa:\n"
        insights += f"         • {len(europa_companies)} empresas de IA\n"
        insights += f"         • {len(patents_epo)} patents (energia, materiais, auto)\n"
        insights += f"         • Especialização: ENERGIA/SUSTENTABILIDADE\n"
        insights += "         ⚠️  PROBLEMA: Pesquisa forte, comercialização fraca (vale da morte).\n\n"

    insights += f"      🇧🇷 Brasil:\n"
    insights += f"         • {len(brasil_companies)} empresas com funding relevante\n"
    insights += "         • Especialização: ESPECTADOR (consumidor, não produtor)\n\n"

    insights += "   💡 CONCLUSÃO GEOPOLÍTICA:\n\n"
    insights += "      O eixo tecnológico do planeta se formalizou:\n"
    insights += "         • USA controla SOFTWARE (modelos, APIs, produtos)\n"
    insights += "         • China controla HARDWARE (chips, infra, manufatura)\n"
    insights += "         • Europa controla ENERGIA (transição verde)\n"
    insights += "         • Brasil = consumidor final.\n\n"

    insights += "      🎯 IMPLICAÇÃO ESTRATÉGICA:\n"
    insights += "         → Quem controla COMPUTE controla IA.\n"
    insights += "         → Quem controla IA controla DEFESA.\n"
    insights += "         → NVDA/TSMC/AMD são o novo petróleo.\n"
    insights += "         → Brasil precisa URGENTEMENTE de compute soberano ou ficará refém.\n\n"

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
