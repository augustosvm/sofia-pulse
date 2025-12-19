#!/usr/bin/env python3
"""
SOFIA PULSE - BEST CITIES FOR TECH TALENT
Recomenda melhores cidades para procurar emprego em tech

Considera:
- Job opportunities (funding deals como proxy)
- Education quality (universities, literacy)
- Infrastructure (internet, connectivity)
- Safety & Quality of Life
- Cost of living (salary purchasing power)
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv

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

    query = """
    WITH latest_data AS (
        SELECT
            country_name,
            indicator_name,
            value,
            ROW_NUMBER() OVER (PARTITION BY country_name, indicator_name ORDER BY year DESC) as rn
        FROM sofia.socioeconomic_indicators
        WHERE year >= 2018
    )
    SELECT country_name, indicator_name, value
    FROM latest_data
    WHERE rn = 1
    """

    cur.execute(query)
    results = cur.fetchall()

    country_data = defaultdict(dict)
    for row in results:
        country = row['country_name']
        indicator = row['indicator_name']
        value = float(row['value']) if row['value'] else None
        country_data[country][indicator] = value

    print(f"✅ Found socioeconomic data for {len(country_data)} countries")
    return country_data

def extract_cities_with_jobs(conn):
    """Extrai cidades com oportunidades de emprego (funding como proxy)"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT
        COALESCE(cities.name, fr.city, countries.name, 'Unknown') as city,
        COALESCE(countries.name, fr.country, 'Unknown') as country,
        COUNT(*) as deals_count,
        SUM(fr.amount_usd) as total_funding,
        ARRAY_AGG(DISTINCT fr.sector) FILTER (WHERE fr.sector IS NOT NULL) as sectors
    FROM sofia.funding_rounds fr
    LEFT JOIN sofia.countries ON fr.country_id = countries.id
    LEFT JOIN sofia.cities ON fr.city_id = cities.id
    WHERE fr.announced_date >= CURRENT_DATE - INTERVAL '365 days'
        AND (fr.country_id IS NOT NULL OR fr.country IS NOT NULL)
    GROUP BY cities.name, fr.city, countries.name, fr.country
    HAVING COUNT(*) >= 1
    ORDER BY deals_count DESC, total_funding DESC
    LIMIT 100
    """

    cur.execute(query)
    results = cur.fetchall()
    print(f"✅ Found {len(results)} cities with job opportunities")
    return results

def calculate_tech_talent_score(city, country, deals, funding, socio_data):
    """
    Calculate Tech Talent Score (0-100)

    Factors:
    1. Job Opportunities (30 pts) - Funding deals as proxy for hiring
    2. Education Quality (25 pts) - Universities, literacy
    3. Infrastructure (20 pts) - Internet, connectivity
    4. Safety & QoL (15 pts) - Safety, healthcare
    5. Cost of Living (10 pts) - Salary purchasing power
    """

    data = socio_data.get(country, {})
    score = 0
    details = {}

    # 1. JOB OPPORTUNITIES (0-30 points)
    job_score = 0
    if deals >= 20:
        job_score = 30
    elif deals >= 10:
        job_score = 25
    elif deals >= 5:
        job_score = 20
    elif deals >= 2:
        job_score = 12
    else:
        job_score = 5

    score += job_score
    details['job_opportunities'] = job_score

    # 2. EDUCATION QUALITY (0-25 points)
    literacy = data.get('literacy_rate', 0) or 0
    tertiary = data.get('school_enrollment_tertiary', 0) or 0

    education_score = 0
    education_score += min(literacy / 100 * 15, 15)  # 15 pts max
    education_score += min(tertiary / 100 * 10, 10)  # 10 pts max

    score += education_score
    details['education'] = round(education_score, 1)

    # 3. INFRASTRUCTURE (0-20 points)
    internet = data.get('internet_users', 0) or 0
    broadband = data.get('broadband_subscriptions', 0) or 0

    infra_score = 0
    infra_score += min(internet / 100 * 15, 15)  # 15 pts max
    infra_score += min(broadband / 40 * 5, 5)    # 5 pts max (40 per 100 = 100%)

    score += infra_score
    details['infrastructure'] = round(infra_score, 1)

    # 4. SAFETY & QOL (0-15 points)
    life_exp = data.get('life_expectancy', 0) or 0
    suicide = data.get('suicide_rate', 0) or 0
    injuries = data.get('injuries_deaths', 0) or 0

    safety_score = 15  # Start at max

    # Life expectancy bonus
    if life_exp >= 75:
        safety_score += 5
    elif life_exp < 65:
        safety_score -= 5

    # Safety penalties
    if suicide > 15:  # High suicide rate
        safety_score -= min((suicide - 15) / 15 * 5, 5)
    if injuries > 10:  # High injury deaths
        safety_score -= min(injuries / 15 * 5, 5)

    safety_score = max(min(safety_score, 15), 0)
    score += safety_score
    details['safety_qol'] = round(safety_score, 1)

    # 5. COST OF LIVING (0-10 points)
    gdp_per_capita = data.get('gdp_per_capita', 0) or 0

    cost_score = 0
    # Low cost = more points (salary goes further)
    if gdp_per_capita < 15000:  # Very low cost
        cost_score = 10
    elif gdp_per_capita < 30000:  # Low-medium cost
        cost_score = 7
    elif gdp_per_capita < 50000:  # Medium cost
        cost_score = 5
    else:  # High cost
        cost_score = 2

    score += cost_score
    details['cost_advantage'] = cost_score

    return round(score, 1), details

def analyze_cities_for_talent(conn, socio_data):
    """Analyze cities for tech talent"""

    cities = extract_cities_with_jobs(conn)

    city_scores = []

    for city_data in cities:
        city = city_data['city']
        country = city_data['country']
        deals = city_data['deals_count'] or 0
        funding = float(city_data['total_funding'] or 0)
        sectors = city_data['sectors'] or []

        if city == 'Unknown':
            continue

        score, details = calculate_tech_talent_score(city, country, deals, funding, socio_data)

        city_scores.append({
            'city': city,
            'country': country,
            'score': score,
            'deals': deals,
            'funding': funding,
            'sectors': sectors[:3],  # Top 3 sectors
            'details': details,
        })

    city_scores.sort(key=lambda x: x['score'], reverse=True)

    print(f"✅ Scored {len(city_scores)} cities")
    return city_scores

def generate_report(locations, socio_data):
    """Generate report"""
    report = []
    report.append("=" * 80)
    report.append("💼 BEST CITIES FOR TECH TALENT - Sofia Pulse Intelligence")
    report.append("=" * 80)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("🎯 BEST CITIES TO FIND TECH JOBS")
    report.append("Based on:")
    report.append("  • Job Opportunities (funding deals as hiring proxy)")
    report.append("  • Education Quality (universities, literacy)")
    report.append("  • Infrastructure (internet, connectivity)")
    report.append("  • Safety & Quality of Life")
    report.append("  • Cost of Living (salary purchasing power)")
    report.append("")
    report.append("=" * 80)
    report.append("")

    if not locations:
        report.append("⚠️  No data available")
        return "\n".join(report)

    # Group by country
    by_country = defaultdict(list)
    for loc in locations:
        by_country[loc['country']].append(loc)

    country_order = sorted(by_country.keys(),
                          key=lambda c: max(loc['score'] for loc in by_country[c]),
                          reverse=True)

    report.append(f"🏆 TOP {len(locations)} CITIES FOR TECH JOBS")
    report.append("")
    report.append("=" * 80)
    report.append("")

    global_rank = 1

    for country in country_order:
        cities = by_country[country]
        cities.sort(key=lambda x: x['score'], reverse=True)

        best_score = cities[0]['score']
        total_deals = sum(c['deals'] for c in cities)

        report.append("")
        report.append("█" * 80)
        report.append(f"📍 {country.upper()} ({len(cities)} cities)")
        report.append(f"   Best Score: {best_score:.1f}/100")
        report.append(f"   Total Job Opportunities: {total_deals} companies hiring")
        report.append("█" * 80)
        report.append("")

        for loc in cities[:5]:  # Top 5 per country
            report.append(f"#{global_rank} - {loc['city']}")
            report.append(f"   Tech Talent Score: {loc['score']:.1f}/100")
            report.append(f"   Job Opportunities: {loc['deals']} hiring companies")

            # Score breakdown
            details = loc['details']
            report.append(f"   Score Breakdown:")
            report.append(f"      Job Opportunities: {details.get('job_opportunities', 0):.0f}/30")
            report.append(f"      Education Quality: {details.get('education', 0):.0f}/25")
            report.append(f"      Infrastructure: {details.get('infrastructure', 0):.0f}/20")
            report.append(f"      Safety & QoL: {details.get('safety_qol', 0):.0f}/15")
            report.append(f"      Cost Advantage: {details.get('cost_advantage', 0):.0f}/10")

            # Sectors
            if loc['sectors']:
                sectors_str = ', '.join(loc['sectors'])
                report.append(f"   Active Sectors: {sectors_str}")

            # Rating
            if loc['score'] >= 75:
                rating = "🟢 EXCELLENT - Top tier tech job market"
            elif loc['score'] >= 60:
                rating = "🟡 GOOD - Strong opportunities"
            elif loc['score'] >= 45:
                rating = "🟠 MODERATE - Consider tradeoffs"
            else:
                rating = "🔴 LIMITED - Few opportunities"

            report.append(f"   📊 RATING: {rating}")
            report.append("")
            report.append("   " + "-" * 70)
            report.append("")

            global_rank += 1

    report.append("=" * 80)
    report.append("📚 METHODOLOGY")
    report.append("=" * 80)
    report.append("")
    report.append("Scoring System (0-100 points):")
    report.append("  1. Job Opportunities (0-30 pts) - Companies hiring (funding deals)")
    report.append("  2. Education Quality (0-25 pts) - Literacy + University enrollment")
    report.append("  3. Infrastructure (0-20 pts) - Internet + Broadband access")
    report.append("  4. Safety & QoL (0-15 pts) - Life expectancy, low crime")
    report.append("  5. Cost Advantage (0-10 pts) - Salary purchasing power")
    report.append("")
    report.append("Data Sources:")
    report.append("  • sofia.funding_rounds - Hiring proxies (365 days)")
    report.append("  • sofia.socioeconomic_indicators - World Bank")
    report.append("")
    report.append("=" * 80)

    return "\n".join(report)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("=" * 80)
        print("💼 BEST CITIES FOR TECH TALENT")
        print("=" * 80)
        print()

        print("📊 Step 1: Extracting socioeconomic data...")
        socio_data = extract_socioeconomic_data(conn)

        print()
        print("📊 Step 2: Analyzing cities...")
        locations = analyze_cities_for_talent(conn, socio_data)

        print()
        print("📊 Step 3: Generating report...")
        report = generate_report(locations, socio_data)

        output_file = 'analytics/best-cities-tech-talent-latest.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ Report saved: {output_file}")
        print()
        print("=" * 80)
        print("✅ ANALYSIS COMPLETE")
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
