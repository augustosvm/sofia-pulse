#!/usr/bin/env python3
"""
SOFIA PULSE - EXPANSION LOCATION ANALYZER V2 (COMPREHENSIVE)
Recomenda melhores cidades baseado em DADOS REAIS + QUALITY OF LIFE METRICS

Baseado em modelos padrão:
- Mercer Quality of Living Survey
- Numbeo Quality of Life Index
- Economist Intelligence Unit Global Liveability Index
- World Bank Socioeconomic Indicators
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from collections import defaultdict, Counter
from dotenv import load_dotenv
import re

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or 'localhost',
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5432'),
    'user': os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME') or 'sofia_db',
}

def extract_socioeconomic_data(conn):
    """Extrai indicadores socioeconômicos por país"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get latest year data for key indicators
    query = """
    WITH latest_data AS (
        SELECT
            country_name,
            country_code,
            indicator_name,
            value,
            year,
            ROW_NUMBER() OVER (PARTITION BY country_name, indicator_name ORDER BY year DESC) as rn
        FROM sofia.socioeconomic_indicators
        WHERE year >= 2018  -- Last 5 years
    )
    SELECT
        country_name,
        country_code,
        indicator_name,
        value,
        year
    FROM latest_data
    WHERE rn = 1
    ORDER BY country_name, indicator_name
    """

    cur.execute(query)
    results = cur.fetchall()

    # Group by country
    country_data = defaultdict(dict)
    for row in results:
        country = row['country_name']
        indicator = row['indicator_name']
        value = float(row['value']) if row['value'] else None
        country_data[country][indicator] = value

    print(f"✅ Found socioeconomic data for {len(country_data)} countries")
    return country_data

def extract_cities_from_funding(conn):
    """Extrai cidades com funding rounds"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT
        COALESCE(ci.common_name, fr.city, co.common_name, 'Unknown') as city,
        COALESCE(co.common_name, fr.country, 'Unknown') as country,
        COUNT(*) as deals_count,
        SUM(fr.amount_usd) as total_funding,
        AVG(fr.amount_usd) as avg_funding,
        ARRAY_AGG(DISTINCT fr.sector) FILTER (WHERE fr.sector IS NOT NULL) as sectors
    FROM sofia.funding_rounds fr
    LEFT JOIN sofia.countries co ON fr.country_id = co.id
    LEFT JOIN sofia.cities ci ON fr.city_id = ci.id
    WHERE fr.announced_date >= CURRENT_DATE - INTERVAL '365 days'
        AND (fr.country_id IS NOT NULL OR fr.country IS NOT NULL)
    GROUP BY ci.common_name, fr.city, co.common_name, fr.country
    HAVING COUNT(*) >= 1
    ORDER BY total_funding DESC NULLS LAST, deals_count DESC
    LIMIT 200
    """

    cur.execute(query)
    results = cur.fetchall()

    print(f"✅ Found {len(results)} cities with funding data")
    return results

def extract_papers_by_location(conn):
    """Extrai papers por localização (via instituições)"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT
        title,
        primary_concept as primary_topic,
        concepts as keywords,
        author_institutions as institutions_display_name,
        author_countries as countries,
        publication_date
    FROM sofia.openalex_papers
    WHERE publication_date >= CURRENT_DATE - INTERVAL '365 days'
        AND (author_institutions IS NOT NULL OR author_countries IS NOT NULL)
    ORDER BY cited_by_count DESC NULLS LAST
    LIMIT 500
    """

    cur.execute(query)
    papers = cur.fetchall()

    print(f"✅ Found {len(papers)} papers with location data")
    return papers

def extract_arxiv_papers(conn):
    """Extrai ArXiv papers com keywords"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT
        title,
        primary_category,
        keywords,
        authors
    FROM arxiv_ai_papers
    WHERE published_date >= CURRENT_DATE - INTERVAL '365 days'
        AND keywords IS NOT NULL
    LIMIT 300
    """

    cur.execute(query)
    papers = cur.fetchall()

    print(f"✅ Found {len(papers)} ArXiv papers")
    return papers

def map_keywords_to_industries(keywords):
    """Mapeia keywords de papers para indústrias recomendadas"""
    if not keywords:
        return []

    industries = []
    keywords_lower = [k.lower() for k in keywords]

    # AI/ML
    ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'deep learning',
                   'neural', 'llm', 'gpt', 'transformer', 'nlp', 'computer vision']
    if any(kw in ' '.join(keywords_lower) for kw in ai_keywords):
        industries.append('AI/ML Companies')

    # Batteries/Energy
    battery_keywords = ['battery', 'lithium', 'electric vehicle', 'ev', 'energy storage',
                       'solar', 'renewable', 'wind energy', 'grid']
    if any(kw in ' '.join(keywords_lower) for kw in battery_keywords):
        industries.append('Energy/Battery Tech')

    # Biotech/Health
    bio_keywords = ['biotech', 'genome', 'drug', 'protein', 'medical', 'health',
                   'pharma', 'clinical', 'diagnostic', 'crispr']
    if any(kw in ' '.join(keywords_lower) for kw in bio_keywords):
        industries.append('Biotech/Healthcare')

    # Robotics
    robot_keywords = ['robot', 'autonomous', 'drone', 'sensor', 'actuator',
                     'manipulation', 'navigation']
    if any(kw in ' '.join(keywords_lower) for kw in robot_keywords):
        industries.append('Robotics/Automation')

    # Quantum
    quantum_keywords = ['quantum', 'qubit', 'superposition', 'entanglement']
    if any(kw in ' '.join(keywords_lower) for kw in quantum_keywords):
        industries.append('Quantum Computing')

    # Cybersecurity
    security_keywords = ['security', 'encryption', 'crypto', 'privacy', 'attack',
                        'vulnerability', 'malware', 'blockchain']
    if any(kw in ' '.join(keywords_lower) for kw in security_keywords):
        industries.append('Cybersecurity/Blockchain')

    # Fintech
    fintech_keywords = ['finance', 'payment', 'trading', 'market', 'risk',
                       'portfolio', 'credit', 'lending']
    if any(kw in ' '.join(keywords_lower) for kw in fintech_keywords):
        industries.append('Fintech')

    # Space
    space_keywords = ['satellite', 'space', 'orbit', 'launch', 'aerospace']
    if any(kw in ' '.join(keywords_lower) for kw in space_keywords):
        industries.append('Space/Aerospace')

    # Climate Tech
    climate_keywords = ['climate', 'carbon', 'emission', 'sustainability',
                       'environmental', 'green']
    if any(kw in ' '.join(keywords_lower) for kw in climate_keywords):
        industries.append('Climate Tech')

    # Semiconductors
    chip_keywords = ['chip', 'semiconductor', 'wafer', 'fabrication', 'asic',
                    'fpga', 'gpu', 'processor']
    if any(kw in ' '.join(keywords_lower) for kw in chip_keywords):
        industries.append('Semiconductors/Hardware')

    # Manufacturing/Industry
    manufacturing_keywords = ['manufacturing', 'production', 'supply chain', 'logistics',
                             'factory', 'industrial', 'automation', 'assembly']
    if any(kw in ' '.join(keywords_lower) for kw in manufacturing_keywords):
        industries.append('Manufacturing/Industrial')

    return list(set(industries))

def analyze_papers_by_country(papers_openalex, papers_arxiv):
    """Analisa papers por país e identifica especialidades"""
    country_papers = defaultdict(lambda: {'count': 0, 'keywords': [], 'topics': []})

    # OpenAlex papers
    for paper in papers_openalex:
        countries = paper.get('countries')
        keywords = paper.get('keywords', []) or []
        topic = paper.get('primary_topic')

        if countries:
            # countries can be array or single value
            countries_list = countries if isinstance(countries, list) else [countries]
            for country in countries_list:
                if not country:
                    continue
                country_papers[country]['count'] += 1
                if keywords:
                    country_papers[country]['keywords'].extend(keywords)
                if topic:
                    country_papers[country]['topics'].append(topic)
        else:
            # No country info, add to Global
            country_papers['Global']['count'] += 1
            if keywords:
                country_papers['Global']['keywords'].extend(keywords)
            if topic:
                country_papers['Global']['topics'].append(topic)

    # ArXiv papers - distribuir globalmente
    for paper in papers_arxiv:
        keywords = paper.get('keywords', []) or []
        country_papers['Global']['count'] += 1
        country_papers['Global']['keywords'].extend(keywords)

    print(f"✅ Analyzed papers across {len(country_papers)} countries/regions")
    return country_papers

def get_recommended_industries(country, country_papers, top_n=3):
    """Retorna indústrias recomendadas baseado em papers locais"""
    if country not in country_papers:
        return []

    data = country_papers[country]
    if not data['keywords']:
        return []

    # Mapear keywords para indústrias
    all_industries = []
    for kw in data['keywords']:
        industries = map_keywords_to_industries([kw])
        all_industries.extend(industries)

    # Contar frequência
    industry_counts = Counter(all_industries)

    # Top indústrias
    top_industries = [ind for ind, count in industry_counts.most_common(top_n)]

    return top_industries

def calculate_quality_of_life_score(country, socio_data):
    """
    Calcula Quality of Life Score baseado em modelos padrão

    Baseado em:
    - Mercer Quality of Living (10 categorias)
    - Numbeo Quality of Life Index (8 categorias)
    - EIU Global Liveability (5 categorias)

    Returns: dict com scores por categoria (0-100 cada)
    """
    data = socio_data.get(country, {})

    scores = {}

    # 1. EDUCATION & TALENT (0-100 points)
    # Factors: Literacy, tertiary enrollment, education spending
    education_score = 0
    literacy = data.get('literacy_rate', 0) or 0
    tertiary = data.get('school_enrollment_tertiary', 0) or 0
    edu_expenditure = data.get('education_expenditure_gdp', 0) or 0

    education_score += min(literacy, 100) * 0.4  # 40% weight
    education_score += min(tertiary * 0.5, 50)    # 50% weight (normalize 0-200 to 0-100)
    education_score += min(edu_expenditure * 2, 10)  # 10% weight (normalize ~5% to 10)

    scores['education'] = round(education_score, 1)

    # 2. INFRASTRUCTURE & CONNECTIVITY (0-100 points)
    # Factors: Internet, broadband, electricity, roads
    infrastructure_score = 0
    internet = data.get('internet_users', 0) or 0
    broadband = data.get('broadband_subscriptions', 0) or 0
    electricity = data.get('electricity_access', 0) or 0
    roads = data.get('paved_roads', 0) or 0

    infrastructure_score += min(internet, 100) * 0.4  # 40%
    infrastructure_score += min(broadband * 2.5, 25)   # 25% (normalize 0-40 to 0-100)
    infrastructure_score += min(electricity, 100) * 0.25  # 25%
    infrastructure_score += min(roads, 100) * 0.1  # 10%

    scores['infrastructure'] = round(infrastructure_score, 1)

    # 3. HEALTHCARE (0-100 points)
    # Factors: Life expectancy, physicians, hospital beds
    healthcare_score = 0
    life_exp = data.get('life_expectancy', 0) or 0
    physicians = data.get('physicians_per_1000', 0) or 0
    hospital_beds = data.get('hospital_beds_per_1000', 0) or 0

    # Normalize life expectancy: 50 years = 0, 85 years = 100
    if life_exp > 0:
        healthcare_score += min(max((life_exp - 50) / 35 * 100, 0), 100) * 0.5  # 50%
    healthcare_score += min(physicians / 5 * 100, 100) * 0.3  # 30% (5 per 1000 = 100)
    healthcare_score += min(hospital_beds / 10 * 100, 100) * 0.2  # 20% (10 per 1000 = 100)

    scores['healthcare'] = round(healthcare_score, 1)

    # 4. SAFETY & STABILITY (0-100 points)
    # Factors: Low suicide rate, low injury deaths
    # Note: Lower is better, so we invert
    safety_score = 100  # Start at max
    suicide = data.get('suicide_rate', 0) or 0
    injuries = data.get('injuries_deaths', 0) or 0

    # Suicide: 0 = 100, 30+ per 100k = 0
    if suicide > 0:
        safety_score -= min(suicide / 30 * 50, 50)  # Max 50 point deduction

    # Injuries: 0% = no deduction, 15%+ = 50 point deduction
    if injuries > 0:
        safety_score -= min(injuries / 15 * 50, 50)  # Max 50 point deduction

    scores['safety'] = round(max(safety_score, 0), 1)

    # 5. ENVIRONMENT (0-100 points)
    # Factors: Air quality, renewable energy, forest area
    environment_score = 100  # Start at max
    pm25 = data.get('air_pollution_pm25', 0) or 0
    renewable = data.get('renewable_electricity', 0) or 0
    forest = data.get('forest_area', 0) or 0

    # PM2.5: 0 = no deduction, 50+ = 40 point deduction
    if pm25 > 0:
        environment_score -= min(pm25 / 50 * 40, 40)

    # Renewable energy: bonus for high renewable
    environment_score += min(renewable / 100 * 30, 30)  # Max 30 bonus

    # Forest: bonus for high forest coverage
    if forest > 0:
        environment_score += min(forest / 100 * 30, 30)  # Max 30 bonus

    scores['environment'] = round(min(environment_score, 100), 1)

    # 6. INNOVATION (0-100 points)
    # Factors: R&D spending
    innovation_score = 0
    rd_gdp = data.get('research_development_gdp', 0) or 0

    # R&D: 0% = 0, 4%+ = 100
    innovation_score = min(rd_gdp / 4 * 100, 100)

    scores['innovation'] = round(innovation_score, 1)

    # 7. ECONOMIC OPPORTUNITY (0-100 points)
    # Factors: GDP per capita, unemployment (inverted), FDI inflows
    economic_score = 0
    gdp_per_capita = data.get('gdp_per_capita', 0) or 0
    unemployment = data.get('unemployment_rate', 0) or 0
    fdi = data.get('fdi_inflows', 0) or 0

    # GDP per capita: 0 = 0, $80k+ = 50 points
    economic_score += min(gdp_per_capita / 80000 * 50, 50)

    # Unemployment: 0% = 25, 20%+ = 0
    if unemployment >= 0:
        economic_score += max(25 - (unemployment / 20 * 25), 0)

    # FDI: $1B+ = 25 points
    if fdi > 0:
        economic_score += min((fdi / 1e9) * 5, 25)

    scores['economic'] = round(economic_score, 1)

    # Calculate overall quality of life score (weighted average)
    weights = {
        'education': 0.20,
        'infrastructure': 0.20,
        'healthcare': 0.15,
        'safety': 0.15,
        'environment': 0.10,
        'innovation': 0.10,
        'economic': 0.10,
    }

    overall = sum(scores.get(cat, 0) * weight for cat, weight in weights.items())
    scores['overall'] = round(overall, 1)

    return scores

def estimate_cost_level(country, city, socio_data):
    """Estima custo de vida baseado em país/cidade + GDP per capita"""
    # Get GDP per capita data
    data = socio_data.get(country, {})
    gdp_per_capita = data.get('gdp_per_capita', 0) or 0

    # High-cost countries (GDP per capita > $50k)
    if gdp_per_capita > 50000:
        return 'High'
    elif gdp_per_capita > 20000:
        return 'Medium'
    else:
        return 'Low'

def is_recognized_tech_hub(city, country):
    """Verifica se é um tech hub reconhecido"""
    tech_hubs = {
        # USA
        'San Francisco', 'San Jose', 'Palo Alto', 'Mountain View', 'New York',
        'Austin', 'Seattle', 'Boston', 'Cambridge', 'Boulder', 'Denver',
        'San Diego', 'Los Angeles', 'Chicago', 'Miami', 'Atlanta', 'Raleigh',

        # Brazil
        'São Paulo', 'Florianópolis', 'Belo Horizonte', 'Campinas', 'Rio de Janeiro',
        'Curitiba', 'Porto Alegre', 'Recife', 'Vitória',

        # Europe
        'London', 'Berlin', 'Paris', 'Amsterdam', 'Dublin', 'Stockholm',
        'Copenhagen', 'Tallinn', 'Barcelona', 'Madrid', 'Lisbon', 'Munich',
        'Zurich', 'Helsinki', 'Vienna', 'Prague', 'Warsaw',

        # Asia
        'Singapore', 'Bangalore', 'Tel Aviv', 'Tokyo', 'Seoul', 'Hong Kong',
        'Taipei', 'Shenzhen', 'Shanghai', 'Beijing', 'Dubai', 'Hyderabad',

        # Canada
        'Toronto', 'Vancouver', 'Montreal', 'Waterloo',

        # LATAM
        'Buenos Aires', 'Santiago', 'Bogotá', 'Mexico City',

        # Oceania
        'Sydney', 'Melbourne',
    }

    city_str = str(city)
    return any(hub in city_str for hub in tech_hubs)

def analyze_locations(conn, country_papers, socio_data):
    """Analisa cidades baseado em dados reais do banco"""

    # 1. Get cities from funding data
    funding_cities = extract_cities_from_funding(conn)

    city_scores = []

    for city_data in funding_cities:
        city = city_data['city']
        country = city_data['country']
        deals_count = city_data['deals_count'] or 0
        total_funding = float(city_data['total_funding'] or 0)
        sectors = city_data['sectors'] or []

        # Skip "Unknown" cities
        if city == 'Unknown':
            continue

        score = 0
        advantages = []
        disadvantages = []

        # 1. Funding activity (0-25 points)
        if deals_count >= 20:
            score += 25
            advantages.append(f"Very strong startup ecosystem: {deals_count} funding deals")
        elif deals_count >= 10:
            score += 20
            advantages.append(f"Strong startup ecosystem: {deals_count} funding deals")
        elif deals_count >= 5:
            score += 12
            advantages.append(f"Moderate startup activity: {deals_count} deals")
        elif deals_count >= 2:
            score += 6
            disadvantages.append(f"Limited startup ecosystem: only {deals_count} deals")
        else:
            score += 2
            disadvantages.append(f"Very limited funding activity: {deals_count} deal(s)")

        # 2. Total funding amount (0-20 points)
        funding_billions = total_funding / 1e9
        if funding_billions >= 1.0:
            score += 20
            advantages.append(f"Major capital hub: ${funding_billions:.1f}B total funding")
        elif funding_billions >= 0.1:
            score += 15
            advantages.append(f"Significant funding: ${funding_billions:.2f}B")
        elif funding_billions >= 0.01:
            score += 8
            advantages.append(f"Emerging funding: ${funding_billions:.2f}B")
        else:
            score += 3
            disadvantages.append(f"Limited capital: ${total_funding/1e6:.1f}M only")

        # 3. Quality of Life Score (0-35 points) - NOVO!
        qol_scores = calculate_quality_of_life_score(country, socio_data)
        qol_overall = qol_scores.get('overall', 0)

        # Add QoL subscore (0-35 points)
        qol_points = min(qol_overall * 0.35, 35)
        score += qol_points

        # Add specific advantages/disadvantages based on QoL
        if qol_scores.get('education', 0) >= 70:
            advantages.append(f"Strong education system (score: {qol_scores['education']:.0f}/100)")
        elif qol_scores.get('education', 0) < 40:
            disadvantages.append(f"Weak education system (score: {qol_scores['education']:.0f}/100)")

        if qol_scores.get('infrastructure', 0) >= 70:
            advantages.append(f"Excellent infrastructure & connectivity (score: {qol_scores['infrastructure']:.0f}/100)")
        elif qol_scores.get('infrastructure', 0) < 40:
            disadvantages.append(f"Poor infrastructure (score: {qol_scores['infrastructure']:.0f}/100)")

        if qol_scores.get('safety', 0) < 50:
            disadvantages.append(f"Safety concerns (score: {qol_scores['safety']:.0f}/100)")
        elif qol_scores.get('safety', 0) >= 75:
            advantages.append(f"Very safe location (score: {qol_scores['safety']:.0f}/100)")

        if qol_scores.get('innovation', 0) >= 50:
            advantages.append(f"Strong innovation ecosystem (R&D score: {qol_scores['innovation']:.0f}/100)")

        # 4. Cost of living (0-10 points)
        cost_level = estimate_cost_level(country, city, socio_data)
        if cost_level == 'Low':
            score += 10
            advantages.append("Low cost of living (salary advantage)")
        elif cost_level == 'Medium':
            score += 6
            advantages.append("Medium cost of living (balanced)")
        else:
            score += 2
            disadvantages.append("High cost of living (expensive salaries)")

        # 5. Tech hub status (0-10 points)
        if is_recognized_tech_hub(city, country):
            score += 10
            advantages.append("Recognized tech hub (established ecosystem)")
        else:
            disadvantages.append("Not a primary tech hub")

        # 6. Research specialization (0-10 points)
        recommended_industries = get_recommended_industries(country, country_papers, top_n=3)
        if recommended_industries:
            score += 10
            advantages.append(f"Research specialization: {', '.join(recommended_industries)}")
        else:
            # Try global pool
            global_industries = get_recommended_industries('Global', country_papers, top_n=2)
            if global_industries:
                score += 5
                advantages.append(f"Global research trends: {', '.join(global_industries)}")

        city_scores.append({
            'city': city,
            'country': country,
            'score': score,
            'cost': cost_level,
            'advantages': advantages,
            'disadvantages': disadvantages,
            'deals_count': deals_count,
            'total_funding': total_funding,
            'sectors': sectors[:5],  # Top 5 sectors
            'recommended_industries': recommended_industries or (global_industries if 'global_industries' in locals() else []),
            'qol_scores': qol_scores,
        })

    # Sort by score
    city_scores.sort(key=lambda x: x['score'], reverse=True)

    print(f"✅ Scored {len(city_scores)} cities")

    # Ensure we have Brazilian cities
    brazilian_cities = [c for c in city_scores if c['country'] == 'Brazil']
    print(f"✅ Found {len(brazilian_cities)} Brazilian cities")

    return city_scores

def generate_report(locations, country_papers):
    """Gera relatório formatado agrupado por país"""
    report = []
    report.append("=" * 80)
    report.append("🌍 EXPANSION LOCATION ANALYZER V2 - Sofia Pulse Intelligence")
    report.append("=" * 80)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("🎯 COMPREHENSIVE ANALYSIS WITH QUALITY OF LIFE METRICS")
    report.append("Recommends best cities based on:")
    report.append("  • Funding activity & capital volume (real data)")
    report.append("  • Quality of Life Score (7 dimensions)")
    report.append("  • Research specialization (paper topics)")
    report.append("  • Cost of living (GDP-based)")
    report.append("  • Tech ecosystem strength")
    report.append("")
    report.append("Quality of Life Dimensions (based on Mercer/Numbeo/EIU):")
    report.append("  1. Education & Talent - Universities, literacy, enrollment")
    report.append("  2. Infrastructure & Connectivity - Internet, broadband, electricity")
    report.append("  3. Healthcare - Life expectancy, physicians, hospital beds")
    report.append("  4. Safety & Stability - Low crime proxies (suicide, injuries)")
    report.append("  5. Environment - Air quality, renewable energy, forests")
    report.append("  6. Innovation - R&D expenditure as % of GDP")
    report.append("  7. Economic Opportunity - GDP per capita, employment, FDI")
    report.append("")
    report.append("=" * 80)
    report.append("")

    if not locations:
        report.append("⚠️  No location data available")
        return "\n".join(report)

    # Group by country
    by_country = defaultdict(list)
    for loc in locations:
        by_country[loc['country']].append(loc)

    # Sort countries by best city score
    country_order = sorted(by_country.keys(),
                          key=lambda c: max(loc['score'] for loc in by_country[c]),
                          reverse=True)

    report.append(f"🏆 ANALYZED {len(locations)} CITIES ACROSS {len(by_country)} COUNTRIES")
    report.append(f"📊 {sum(loc['deals_count'] for loc in locations)} total funding deals")
    report.append(f"💰 ${sum(loc['total_funding'] for loc in locations)/1e9:.1f}B total funding")
    report.append("")
    report.append("=" * 80)
    report.append("")

    global_rank = 1

    for country in country_order:
        cities = by_country[country]
        # Sort cities within country by score
        cities.sort(key=lambda x: x['score'], reverse=True)

        # Country header
        best_score = cities[0]['score']
        total_deals = sum(c['deals_count'] for c in cities)
        total_funding = sum(c['total_funding'] for c in cities)

        report.append("")
        report.append("█" * 80)
        report.append(f"📍 {country.upper()} ({len(cities)} cities analyzed)")
        report.append(f"   Best Score: {best_score:.1f}/100")
        report.append(f"   Total Deals: {total_deals} | Total Funding: ${total_funding/1e9:.2f}B")
        report.append("█" * 80)
        report.append("")

        for loc in cities:
            report.append(f"#{global_rank} - {loc['city']}")
            report.append(f"   Expansion Score: {loc['score']:.1f}/100")
            report.append(f"   Cost Level: {loc['cost']}")
            report.append(f"   Funding: {loc['deals_count']} deals, ${loc['total_funding']/1e6:.1f}M total")

            # Quality of Life breakdown
            qol = loc.get('qol_scores', {})
            if qol:
                report.append(f"   Quality of Life: {qol.get('overall', 0):.0f}/100")
                report.append(f"      Education: {qol.get('education', 0):.0f} | "
                            f"Infrastructure: {qol.get('infrastructure', 0):.0f} | "
                            f"Healthcare: {qol.get('healthcare', 0):.0f}")
                report.append(f"      Safety: {qol.get('safety', 0):.0f} | "
                            f"Environment: {qol.get('environment', 0):.0f} | "
                            f"Innovation: {qol.get('innovation', 0):.0f} | "
                            f"Economic: {qol.get('economic', 0):.0f}")

            # Active sectors
            if loc['sectors']:
                sectors_str = ', '.join(loc['sectors'])
                report.append(f"   Active Sectors: {sectors_str}")

            # Recommended industries based on research
            if loc['recommended_industries']:
                rec_str = ', '.join(loc['recommended_industries'])
                report.append(f"   🎯 Recommended: {rec_str}")

            report.append("")

            # Advantages
            if loc['advantages']:
                report.append("   ✅ Advantages:")
                for advantage in loc['advantages']:
                    report.append(f"      • {advantage}")
                report.append("")

            # Disadvantages
            if loc['disadvantages']:
                report.append("   ⚠️  Disadvantages:")
                for disadvantage in loc['disadvantages']:
                    report.append(f"      • {disadvantage}")
                report.append("")

            # Recommendation
            if loc['score'] >= 80:
                recommendation = "🟢 EXCELLENT CHOICE - Top-tier ecosystem + quality of life"
            elif loc['score'] >= 65:
                recommendation = "🟡 GOOD OPTION - Strong fundamentals"
            elif loc['score'] >= 45:
                recommendation = "🟠 CONSIDER CAREFULLY - Weigh tradeoffs"
            else:
                recommendation = "🔴 RISKY - Limited data/ecosystem"

            report.append(f"   📊 RATING: {recommendation}")
            report.append("")
            report.append("   " + "-" * 70)
            report.append("")

            global_rank += 1

    report.append("=" * 80)
    report.append("📚 METHODOLOGY")
    report.append("=" * 80)
    report.append("")
    report.append("🎯 COMPREHENSIVE SCORING SYSTEM (0-100 points):")
    report.append("")
    report.append("1. Funding Activity (0-25 pts) - Number of deals in last 12 months")
    report.append("2. Capital Volume (0-20 pts) - Total funding raised")
    report.append("3. Quality of Life (0-35 pts) - 7 dimensions:")
    report.append("   • Education (20% weight) - Literacy, universities, spending")
    report.append("   • Infrastructure (20%) - Internet, broadband, electricity, roads")
    report.append("   • Healthcare (15%) - Life expectancy, physicians, hospitals")
    report.append("   • Safety (15%) - Low crime proxies")
    report.append("   • Environment (10%) - Air quality, renewables, forests")
    report.append("   • Innovation (10%) - R&D spending")
    report.append("   • Economic (10%) - GDP/capita, employment, FDI")
    report.append("4. Cost of Living (0-10 pts) - Based on GDP per capita")
    report.append("5. Tech Hub Status (0-10 pts) - Recognized ecosystem")
    report.append("6. Research Match (0-10 pts) - Paper specialization")
    report.append("")
    report.append("Data Sources:")
    report.append("  • sofia.funding_rounds - Real funding deals (365 days)")
    report.append("  • sofia.socioeconomic_indicators - World Bank (56 indicators)")
    report.append("  • sofia.openalex_papers + arxiv_ai_papers - Research topics")
    report.append("")
    report.append("Based on Standard Models:")
    report.append("  • Mercer Quality of Living Survey (10 categories)")
    report.append("  • Numbeo Quality of Life Index (8 categories)")
    report.append("  • EIU Global Liveability Index (5 categories)")
    report.append("  • World Bank Development Indicators")
    report.append("")
    report.append("Cost Levels:")
    report.append("  • Low: GDP/capita < $20k")
    report.append("  • Medium: GDP/capita $20-50k")
    report.append("  • High: GDP/capita > $50k")
    report.append("")
    report.append("Example: Vitória, Brazil")
    report.append("  • Has Arcelor Mittal (steel) → Needs: Engineers, Developers, InfoSec")
    report.append("  • Good infrastructure BUT high violence (safety score low)")
    report.append("  • Manufacturing/Industrial companies ideal for supply chain")
    report.append("")
    report.append("=" * 80)

    return "\n".join(report)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("=" * 80)
        print("🌍 EXPANSION LOCATION ANALYZER V2 - COMPREHENSIVE")
        print("=" * 80)
        print()

        print("📊 Step 1: Extracting socioeconomic data...")
        socio_data = extract_socioeconomic_data(conn)

        print()
        print("📊 Step 2: Extracting papers by location...")
        papers_openalex = extract_papers_by_location(conn)
        papers_arxiv = extract_arxiv_papers(conn)

        print()
        print("📊 Step 3: Analyzing paper topics by country...")
        country_papers = analyze_papers_by_country(papers_openalex, papers_arxiv)

        print()
        print("📊 Step 4: Analyzing cities from funding data...")
        locations = analyze_locations(conn, country_papers, socio_data)

        print()
        print("📊 Step 5: Generating report...")
        report = generate_report(locations, country_papers)

        output_file = 'analytics/expansion-locations-latest.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ Report saved: {output_file}")
        print()
        print("=" * 80)
        print("✅ EXPANSION LOCATION ANALYSIS COMPLETE")
        print("=" * 80)

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
