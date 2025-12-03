#!/usr/bin/env python3
"""
SOFIA PULSE - REMOTE WORK QUALITY INDEX
Melhores cidades para trabalho remoto

Considera:
- Internet quality (speed, reliability)
- Cost of living (salary goes further)
- Safety & Healthcare
- Infrastructure (electricity, connectivity)
- Quality of life (environment, safety)
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

def calculate_remote_work_score(country, socio_data):
    """
    Calculate Remote Work Quality Score (0-100)

    Factors:
    1. Internet Quality (35 pts) - Speed, reliability, broadband
    2. Cost of Living (25 pts) - Salary purchasing power
    3. Safety & Healthcare (20 pts) - Safe, good healthcare
    4. Infrastructure (10 pts) - Electricity, basic services
    5. Environment (10 pts) - Air quality, quality of life
    """

    data = socio_data.get(country, {})
    score = 0
    details = {}

    # 1. INTERNET QUALITY (0-35 points)
    internet = data.get('internet_users', 0) or 0
    broadband = data.get('broadband_subscriptions', 0) or 0

    internet_score = 0
    internet_score += min(internet / 100 * 25, 25)  # 25 pts for high internet penetration
    internet_score += min(broadband / 40 * 10, 10)  # 10 pts for broadband (40 per 100 = 100%)

    score += internet_score
    details['internet'] = round(internet_score, 1)

    # 2. COST OF LIVING (0-25 points)
    gdp_per_capita = data.get('gdp_per_capita', 0) or 0

    cost_score = 0
    # Lower cost = higher score (remote salary goes further)
    if gdp_per_capita < 10000:
        cost_score = 25
    elif gdp_per_capita < 20000:
        cost_score = 20
    elif gdp_per_capita < 35000:
        cost_score = 12
    elif gdp_per_capita < 50000:
        cost_score = 5
    else:
        cost_score = 2

    score += cost_score
    details['cost_advantage'] = cost_score

    # 3. SAFETY & HEALTHCARE (0-20 points)
    life_exp = data.get('life_expectancy', 0) or 0
    physicians = data.get('physicians_per_1000', 0) or 0
    suicide = data.get('suicide_rate', 0) or 0
    injuries = data.get('injuries_deaths', 0) or 0

    safety_health = 0

    # Healthcare (10 pts)
    if life_exp >= 75:
        safety_health += 5
    elif life_exp >= 70:
        safety_health += 3
    elif life_exp < 65:
        safety_health -= 2

    safety_health += min(physicians / 4 * 5, 5)  # 5 pts max (4 per 1000 = 100%)

    # Safety (10 pts)
    safety_health += 10  # Start at max
    if suicide > 15:
        safety_health -= min((suicide - 15) / 15 * 5, 5)
    if injuries > 10:
        safety_health -= min(injuries / 15 * 5, 5)

    safety_health = max(min(safety_health, 20), 0)
    score += safety_health
    details['safety_health'] = round(safety_health, 1)

    # 4. INFRASTRUCTURE (0-10 points)
    electricity = data.get('electricity_access', 0) or 0

    infra_score = min(electricity / 100 * 10, 10)
    score += infra_score
    details['infrastructure'] = round(infra_score, 1)

    # 5. ENVIRONMENT (0-10 points)
    pm25 = data.get('air_pollution_pm25', 0) or 0
    forest = data.get('forest_area', 0) or 0

    env_score = 10  # Start at max

    # Air quality penalty
    if pm25 > 0:
        env_score -= min(pm25 / 50 * 5, 5)

    # Forest bonus
    if forest > 30:
        env_score += min((forest - 30) / 70 * 5, 5)

    env_score = max(min(env_score, 10), 0)
    score += env_score
    details['environment'] = round(env_score, 1)

    return round(score, 1), details

def analyze_countries_remote_work(socio_data):
    """Analyze countries for remote work"""

    country_scores = []

    for country in socio_data.keys():
        score, details = calculate_remote_work_score(country, socio_data)

        # Skip countries with very incomplete data
        if score < 10:
            continue

        country_scores.append({
            'country': country,
            'score': score,
            'details': details,
        })

    country_scores.sort(key=lambda x: x['score'], reverse=True)

    print(f"✅ Scored {len(country_scores)} countries")
    return country_scores

def generate_report(locations):
    """Generate report"""
    report = []
    report.append("=" * 80)
    report.append("🌐 REMOTE WORK QUALITY INDEX - Sofia Pulse Intelligence")
    report.append("=" * 80)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("🎯 BEST COUNTRIES FOR REMOTE WORK")
    report.append("Based on:")
    report.append("  • Internet Quality (speed, reliability, broadband)")
    report.append("  • Cost of Living (salary purchasing power)")
    report.append("  • Safety & Healthcare")
    report.append("  • Infrastructure (electricity, services)")
    report.append("  • Environment (air quality, nature)")
    report.append("")
    report.append("=" * 80)
    report.append("")

    if not locations:
        report.append("⚠️  No data available")
        return "\n".join(report)

    report.append(f"🏆 TOP {min(len(locations), 50)} COUNTRIES FOR REMOTE WORK")
    report.append("")
    report.append("=" * 80)
    report.append("")

    for i, loc in enumerate(locations[:50], 1):
        report.append(f"#{i} - {loc['country']}")
        report.append(f"   Remote Work Score: {loc['score']:.1f}/100")

        # Score breakdown
        details = loc['details']
        report.append(f"   Score Breakdown:")
        report.append(f"      Internet Quality: {details.get('internet', 0):.0f}/35")
        report.append(f"      Cost Advantage: {details.get('cost_advantage', 0):.0f}/25")
        report.append(f"      Safety & Healthcare: {details.get('safety_health', 0):.0f}/20")
        report.append(f"      Infrastructure: {details.get('infrastructure', 0):.0f}/10")
        report.append(f"      Environment: {details.get('environment', 0):.0f}/10")

        # Rating
        if loc['score'] >= 75:
            rating = "🟢 EXCELLENT - Top choice for remote work"
        elif loc['score'] >= 60:
            rating = "🟡 GOOD - Great remote work location"
        elif loc['score'] >= 45:
            rating = "🟠 MODERATE - Acceptable for remote work"
        else:
            rating = "🔴 CHALLENGING - Limited remote work suitability"

        report.append(f"   📊 RATING: {rating}")
        report.append("")
        report.append("   " + "-" * 70)
        report.append("")

    report.append("=" * 80)
    report.append("📚 METHODOLOGY")
    report.append("=" * 80)
    report.append("")
    report.append("Scoring System (0-100 points):")
    report.append("  1. Internet Quality (0-35 pts) - Users %, broadband availability")
    report.append("  2. Cost Advantage (0-25 pts) - Low cost = higher score")
    report.append("  3. Safety & Healthcare (0-20 pts) - Life expectancy, physicians, crime")
    report.append("  4. Infrastructure (0-10 pts) - Electricity access")
    report.append("  5. Environment (0-10 pts) - Air quality, forest coverage")
    report.append("")
    report.append("Data Source:")
    report.append("  • sofia.socioeconomic_indicators - World Bank (56 indicators)")
    report.append("")
    report.append("=" * 80)

    return "\n".join(report)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("=" * 80)
        print("🌐 REMOTE WORK QUALITY INDEX")
        print("=" * 80)
        print()

        print("📊 Step 1: Extracting socioeconomic data...")
        socio_data = extract_socioeconomic_data(conn)

        print()
        print("📊 Step 2: Analyzing countries...")
        locations = analyze_countries_remote_work(socio_data)

        print()
        print("📊 Step 3: Generating report...")
        report = generate_report(locations)

        output_file = 'analytics/remote-work-quality-latest.txt'
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
