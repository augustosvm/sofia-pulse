#!/usr/bin/env python3
"""
SOFIA PULSE - EXPANSION LOCATION ANALYZER (DATABASE-DRIVEN)
Recomenda melhores cidades para abrir filiais baseado em DADOS REAIS do banco
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

def extract_cities_from_funding(conn):
    """Extrai cidades com funding rounds"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT
        COALESCE(city, 'Unknown') as city,
        country,
        COUNT(*) as deals_count,
        SUM(amount_usd) as total_funding,
        AVG(amount_usd) as avg_funding,
        ARRAY_AGG(DISTINCT sector) FILTER (WHERE sector IS NOT NULL) as sectors
    FROM sofia.funding_rounds
    WHERE announced_date >= CURRENT_DATE - INTERVAL '365 days'
        AND country IS NOT NULL
    GROUP BY city, country
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

    # OpenAlex papers têm institutions_display_name que pode conter cidades
    query = """
    SELECT
        title,
        primary_topic,
        keywords,
        institutions_display_name,
        countries,
        publication_date
    FROM sofia.openalex_papers
    WHERE publication_date >= CURRENT_DATE - INTERVAL '365 days'
        AND (institutions_display_name IS NOT NULL OR countries IS NOT NULL)
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

    return list(set(industries))

def analyze_papers_by_country(papers_openalex, papers_arxiv):
    """Analisa papers por país e identifica especialidades"""
    country_papers = defaultdict(lambda: {'count': 0, 'keywords': [], 'topics': []})

    # OpenAlex papers
    for paper in papers_openalex:
        if not paper.get('countries'):
            continue

        countries = paper['countries'] if isinstance(paper['countries'], list) else [paper['countries']]
        keywords = paper.get('keywords', []) or []
        topic = paper.get('primary_topic')

        for country in countries:
            if not country:
                continue
            country_papers[country]['count'] += 1
            if keywords:
                country_papers[country]['keywords'].extend(keywords)
            if topic:
                country_papers[country]['topics'].append(topic)

    # ArXiv papers - distribuir globalmente (sem país específico)
    # Mas podemos inferir alguns países por universidades conhecidas
    for paper in papers_arxiv:
        keywords = paper.get('keywords', []) or []
        # Adicionar ao pool global
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

def estimate_cost_level(country, city):
    """Estima custo de vida baseado em país/cidade"""
    # High-cost countries
    high_cost_countries = ['USA', 'Switzerland', 'Norway', 'Denmark', 'Sweden',
                          'United Kingdom', 'Singapore', 'Hong Kong', 'Japan',
                          'Australia', 'Canada', 'Germany', 'France', 'Netherlands',
                          'Ireland', 'United Arab Emirates', 'Israel']

    # High-cost cities in medium-cost countries
    high_cost_cities = ['São Paulo', 'Rio de Janeiro', 'Brasília', 'Seoul',
                       'Taipei', 'Dubai', 'Tel Aviv']

    # Low-cost countries
    low_cost_countries = ['India', 'Indonesia', 'Vietnam', 'Philippines', 'Thailand',
                         'Pakistan', 'Bangladesh', 'Nigeria', 'Kenya', 'Egypt',
                         'Poland', 'Czech Republic', 'Hungary', 'Romania', 'Bulgaria',
                         'Colombia', 'Peru', 'Argentina', 'Ukraine', 'Malaysia']

    if country in high_cost_countries or any(c in str(city) for c in high_cost_cities):
        return 'High'
    elif country in low_cost_countries:
        return 'Low'
    else:
        return 'Medium'

def is_recognized_tech_hub(city, country):
    """Verifica se é um tech hub reconhecido"""
    tech_hubs = {
        # USA
        'San Francisco', 'San Jose', 'Palo Alto', 'Mountain View', 'New York',
        'Austin', 'Seattle', 'Boston', 'Cambridge', 'Boulder', 'Denver',
        'San Diego', 'Los Angeles', 'Chicago', 'Miami', 'Atlanta', 'Raleigh',

        # Brazil
        'São Paulo', 'Florianópolis', 'Belo Horizonte', 'Campinas', 'Rio de Janeiro',
        'Curitiba', 'Porto Alegre', 'Recife',

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

def analyze_locations(conn, country_papers):
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

        # 1. Funding activity (0-30 points)
        if deals_count >= 20:
            score += 30
            advantages.append(f"Very strong startup ecosystem: {deals_count} funding deals")
        elif deals_count >= 10:
            score += 25
            advantages.append(f"Strong startup ecosystem: {deals_count} funding deals")
        elif deals_count >= 5:
            score += 15
            advantages.append(f"Moderate startup activity: {deals_count} deals")
        elif deals_count >= 2:
            score += 8
            disadvantages.append(f"Limited startup ecosystem: only {deals_count} deals")
        else:
            score += 3
            disadvantages.append(f"Very limited funding activity: {deals_count} deal(s)")

        # 2. Total funding amount (0-25 points)
        funding_billions = total_funding / 1e9
        if funding_billions >= 1.0:
            score += 25
            advantages.append(f"Major capital hub: ${funding_billions:.1f}B total funding")
        elif funding_billions >= 0.1:
            score += 20
            advantages.append(f"Significant funding: ${funding_billions:.2f}B")
        elif funding_billions >= 0.01:
            score += 10
            advantages.append(f"Emerging funding: ${funding_billions:.2f}B")
        else:
            score += 5
            disadvantages.append(f"Limited capital: ${total_funding/1e6:.1f}M only")

        # 3. Cost of living (0-20 points)
        cost_level = estimate_cost_level(country, city)
        if cost_level == 'Low':
            score += 20
            advantages.append("Low cost of living (salary advantage)")
        elif cost_level == 'Medium':
            score += 12
            advantages.append("Medium cost of living (balanced)")
        else:
            score += 5
            disadvantages.append("High cost of living (expensive salaries)")

        # 4. Tech hub status (0-15 points)
        if is_recognized_tech_hub(city, country):
            score += 15
            advantages.append("Recognized tech hub (established ecosystem)")
        else:
            disadvantages.append("Not a primary tech hub")

        # 5. Research specialization (0-10 points) - NOVO!
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
            'recommended_industries': recommended_industries or global_industries if 'global_industries' in locals() else [],
        })

    # Sort by score
    city_scores.sort(key=lambda x: x['score'], reverse=True)

    print(f"✅ Scored {len(city_scores)} cities")

    # Ensure we have Brazilian cities - add top Brazilian cities with less data if needed
    brazilian_cities = [c for c in city_scores if c['country'] == 'Brazil']
    print(f"✅ Found {len(brazilian_cities)} Brazilian cities")

    return city_scores

def generate_report(locations, country_papers):
    """Gera relatório formatado agrupado por país"""
    report = []
    report.append("=" * 80)
    report.append("🌍 EXPANSION LOCATION ANALYZER - Sofia Pulse Intelligence")
    report.append("=" * 80)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("🎯 DATABASE-DRIVEN ANALYSIS")
    report.append("Recommends best cities based on REAL DATA:")
    report.append("  • Funding activity (actual deals)")
    report.append("  • Research specialization (paper topics)")
    report.append("  • Startup sectors (funding sectors)")
    report.append("  • Cost of living estimates")
    report.append("  • Tech ecosystem strength")
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
        report.append(f"   Best Score: {best_score}/100")
        report.append(f"   Total Deals: {total_deals} | Total Funding: ${total_funding/1e9:.2f}B")
        report.append("█" * 80)
        report.append("")

        for loc in cities:
            report.append(f"#{global_rank} - {loc['city']}")
            report.append(f"   Expansion Score: {loc['score']}/100")
            report.append(f"   Cost Level: {loc['cost']}")
            report.append(f"   Funding: {loc['deals_count']} deals, ${loc['total_funding']/1e6:.1f}M total")

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
            if loc['score'] >= 75:
                recommendation = "🟢 EXCELLENT CHOICE - Strong ecosystem + Good cost"
            elif loc['score'] >= 60:
                recommendation = "🟡 GOOD OPTION - Solid fundamentals"
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
    report.append("🎯 DATA-DRIVEN APPROACH:")
    report.append("  1. Extract cities from sofia.funding_rounds (365 days)")
    report.append("  2. Analyze paper topics by country (OpenAlex + ArXiv)")
    report.append("  3. Match paper keywords to industries")
    report.append("  4. Recommend company types based on local research strength")
    report.append("")
    report.append("Scoring Factors (0-100 points):")
    report.append("  • Funding Activity: 0-30 points (deal count)")
    report.append("  • Capital Volume: 0-25 points (total funding)")
    report.append("  • Cost of Living: 0-20 points (Low/Med/High)")
    report.append("  • Tech Hub Status: 0-15 points (recognized ecosystem)")
    report.append("  • Research Match: 0-10 points (paper specialization)")
    report.append("")
    report.append("Industry Recommendations:")
    report.append("  • Based on local paper topics (keywords analysis)")
    report.append("  • AI/ML: neural, transformer, llm, deep learning")
    report.append("  • Energy/Battery: lithium, solar, ev, storage")
    report.append("  • Biotech: genome, drug, protein, medical")
    report.append("  • Robotics: autonomous, drone, manipulation")
    report.append("  • Quantum: qubit, entanglement, quantum")
    report.append("  • Cybersecurity: encryption, privacy, blockchain")
    report.append("  • + Fintech, Space, Climate, Semiconductors")
    report.append("")
    report.append("Cost Levels:")
    report.append("  • Low: R$80-120k (Brazil) / $50-80k (International)")
    report.append("  • Medium: R$120-180k (Brazil) / $80-120k (International)")
    report.append("  • High: R$180k+ (Brazil) / $120k+ (International)")
    report.append("")
    report.append("=" * 80)

    return "\n".join(report)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("=" * 80)
        print("🌍 EXPANSION LOCATION ANALYZER - DATABASE-DRIVEN")
        print("=" * 80)
        print()

        print("📊 Step 1: Extracting papers by location...")
        papers_openalex = extract_papers_by_location(conn)
        papers_arxiv = extract_arxiv_papers(conn)

        print()
        print("📊 Step 2: Analyzing paper topics by country...")
        country_papers = analyze_papers_by_country(papers_openalex, papers_arxiv)

        print()
        print("📊 Step 3: Analyzing cities from funding data...")
        locations = analyze_locations(conn, country_papers)

        print()
        print("📊 Step 4: Generating report...")
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
