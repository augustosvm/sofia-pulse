#!/usr/bin/env python3
"""
SOFIA PULSE - INTELLIGENCE REPORTS SUITE
Gera múltiplos relatórios complementares baseados em dados socioeconômicos

Relatórios gerados:
1. Innovation Hubs Ranking - Centros de inovação global
2. Best Cities for Startup Founders - Onde fundar sua startup
3. Digital Nomad Index - Para nômades digitais
4. STEM Education Leaders - Melhores países para estudar tech
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

    return country_data

def extract_research_activity(conn):
    """Extrai atividade de pesquisa por país"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT
        unnest(COALESCE(countries, ARRAY['Global']::TEXT[])) as country,
        COUNT(*) as paper_count,
        AVG(cited_by_count) as avg_citations
    FROM sofia.openalex_papers
    WHERE publication_date >= CURRENT_DATE - INTERVAL '365 days'
    GROUP BY country
    """

    cur.execute(query)
    results = cur.fetchall()

    research_data = {}
    for row in results:
        country = row['country']
        if country:  # Skip empty countries
            research_data[country] = {
                'papers': row['paper_count'] or 0,
                'avg_citations': row['avg_citations'] or 0
            }

    return research_data

def extract_funding_activity(conn):
    """Extrai atividade de funding por país"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Top funding countries
    cur.execute("""
        SELECT
            COALESCE(co.name, fr.country, 'Unknown') as country,
            COUNT(*) as deals,
            SUM(fr.amount_usd) as total_funding
        FROM sofia.funding_rounds fr
        LEFT JOIN sofia.countries co ON fr.country_id = co.id
        WHERE fr.announced_date >= CURRENT_DATE - INTERVAL '90 days'
            AND (fr.country_id IS NOT NULL OR fr.country IS NOT NULL)
        GROUP BY co.name, fr.country
        ORDER BY total_funding DESC NULLS LAST
        LIMIT 10
    """)
    results = cur.fetchall()

    funding_data = {}
    for row in results:
        country = row['country']
        funding_data[country] = {
            'deals': row['deals_count'] or 0,
            'total_funding': float(row['total_funding'] or 0),
            'avg_funding': float(row['avg_funding'] or 0)
        }

    return funding_data

# ==================== REPORT 1: INNOVATION HUBS ====================

def generate_innovation_hubs_report(socio_data, research_data, funding_data):
    """Generate Innovation Hubs Ranking Report"""

    country_scores = []

    for country in socio_data.keys():
        data = socio_data[country]
        research = research_data.get(country, {'papers': 0, 'avg_citations': 0})
        funding = funding_data.get(country, {'deals': 0, 'total_funding': 0})

        score = 0

        # R&D spending (0-40 pts)
        rd_gdp = data.get('research_development_gdp', 0) or 0
        score += min(rd_gdp / 4 * 40, 40)

        # Research output (0-30 pts)
        papers = research['papers']
        score += min(papers / 50 * 30, 30)

        # Funding activity (0-20 pts)
        deals = funding['deals']
        score += min(deals / 10 * 20, 20)

        # Education (0-10 pts)
        tertiary = data.get('school_enrollment_tertiary', 0) or 0
        score += min(tertiary / 100 * 10, 10)

        if score >= 10:  # Skip countries with very low scores
            country_scores.append({
                'country': country,
                'score': round(score, 1),
                'rd_gdp': round(rd_gdp, 2),
                'papers': papers,
                'deals': deals,
                'tertiary': round(tertiary, 1)
            })

    country_scores.sort(key=lambda x: x['score'], reverse=True)

    # Generate report
    report = []
    report.append("=" * 80)
    report.append("🔬 INNOVATION HUBS RANKING - Sofia Pulse Intelligence")
    report.append("=" * 80)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("Factors: R&D Spending + Research Output + Funding + Education")
    report.append("")
    report.append("=" * 80)
    report.append("")

    report.append(f"🏆 TOP {min(len(country_scores), 30)} INNOVATION HUBS")
    report.append("")

    for i, loc in enumerate(country_scores[:30], 1):
        report.append(f"#{i} - {loc['country']}")
        report.append(f"   Innovation Score: {loc['score']:.1f}/100")
        report.append(f"   R&D Spending: {loc['rd_gdp']}% of GDP")
        report.append(f"   Research Papers: {loc['papers']} (last 12 months)")
        report.append(f"   Funding Deals: {loc['deals']}")
        report.append(f"   University Enrollment: {loc['tertiary']:.0f}%")

        if loc['score'] >= 70:
            rating = "🟢 WORLD-CLASS - Leading innovation center"
        elif loc['score'] >= 50:
            rating = "🟡 STRONG - Major innovation hub"
        else:
            rating = "🟠 EMERGING - Growing innovation ecosystem"

        report.append(f"   📊 RATING: {rating}")
        report.append("")

    report.append("=" * 80)
    report.append("📚 Scoring: R&D (40pts) + Research (30pts) + Funding (20pts) + Education (10pts)")
    report.append("=" * 80)

    return "\n".join(report)

# ==================== REPORT 2: STARTUP FOUNDERS ====================

def generate_startup_founders_report(socio_data, funding_data):
    """Generate Best Cities for Startup Founders Report"""

    country_scores = []

    for country in socio_data.keys():
        data = socio_data[country]
        funding = funding_data.get(country, {'deals': 0, 'total_funding': 0})

        score = 0

        # Funding ecosystem (0-35 pts)
        deals = funding['deals']
        score += min(deals / 15 * 35, 35)

        # Cost of living (0-25 pts) - Lower is better
        gdp_per_capita = data.get('gdp_per_capita', 0) or 0
        if gdp_per_capita < 15000:
            score += 25
        elif gdp_per_capita < 30000:
            score += 15
        elif gdp_per_capita < 50000:
            score += 8
        else:
            score += 3

        # Talent pool (0-20 pts)
        tertiary = data.get('school_enrollment_tertiary', 0) or 0
        literacy = data.get('literacy_rate', 0) or 0
        score += min(tertiary / 100 * 10, 10)
        score += min(literacy / 100 * 10, 10)

        # Infrastructure (0-20 pts)
        internet = data.get('internet_users', 0) or 0
        electricity = data.get('electricity_access', 0) or 0
        score += min(internet / 100 * 10, 10)
        score += min(electricity / 100 * 10, 10)

        if score >= 10:
            country_scores.append({
                'country': country,
                'score': round(score, 1),
                'deals': deals,
                'cost_level': 'Low' if gdp_per_capita < 20000 else 'Medium' if gdp_per_capita < 50000 else 'High',
                'internet': round(internet, 1)
            })

    country_scores.sort(key=lambda x: x['score'], reverse=True)

    # Generate report
    report = []
    report.append("=" * 80)
    report.append("🚀 BEST COUNTRIES FOR STARTUP FOUNDERS - Sofia Pulse Intelligence")
    report.append("=" * 80)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("Factors: Funding Ecosystem + Low Cost + Talent Pool + Infrastructure")
    report.append("")
    report.append("=" * 80)
    report.append("")

    report.append(f"🏆 TOP {min(len(country_scores), 30)} COUNTRIES FOR FOUNDERS")
    report.append("")

    for i, loc in enumerate(country_scores[:30], 1):
        report.append(f"#{i} - {loc['country']}")
        report.append(f"   Founder Score: {loc['score']:.1f}/100")
        report.append(f"   Funding Ecosystem: {loc['deals']} active deals")
        report.append(f"   Cost Level: {loc['cost_level']}")
        report.append(f"   Internet Penetration: {loc['internet']:.0f}%")

        if loc['score'] >= 65:
            rating = "🟢 EXCELLENT - Top choice for founders"
        elif loc['score'] >= 45:
            rating = "🟡 GOOD - Strong startup ecosystem"
        else:
            rating = "🟠 EMERGING - Growing ecosystem"

        report.append(f"   📊 RATING: {rating}")
        report.append("")

    report.append("=" * 80)
    report.append("📚 Scoring: Funding (35pts) + Cost (25pts) + Talent (20pts) + Infra (20pts)")
    report.append("=" * 80)

    return "\n".join(report)

# ==================== REPORT 3: DIGITAL NOMAD ====================

def generate_digital_nomad_report(socio_data):
    """Generate Digital Nomad Index Report"""

    country_scores = []

    for country in socio_data.keys():
        data = socio_data[country]

        score = 0

        # Internet (0-30 pts)
        internet = data.get('internet_users', 0) or 0
        broadband = data.get('broadband_subscriptions', 0) or 0
        score += min(internet / 100 * 20, 20)
        score += min(broadband / 40 * 10, 10)

        # Cost (0-30 pts) - Lower is better
        gdp_per_capita = data.get('gdp_per_capita', 0) or 0
        if gdp_per_capita < 8000:
            score += 30
        elif gdp_per_capita < 15000:
            score += 25
        elif gdp_per_capita < 25000:
            score += 15
        elif gdp_per_capita < 40000:
            score += 8
        else:
            score += 3

        # Safety (0-20 pts)
        life_exp = data.get('life_expectancy', 0) or 0
        suicide = data.get('suicide_rate', 0) or 0
        injuries = data.get('injuries_deaths', 0) or 0

        safety = 20
        if life_exp < 65:
            safety -= 5
        if suicide > 15:
            safety -= min((suicide - 15) / 15 * 5, 5)
        if injuries > 10:
            safety -= min(injuries / 15 * 5, 5)
        score += max(safety, 0)

        # Healthcare (0-10 pts)
        physicians = data.get('physicians_per_1000', 0) or 0
        score += min(physicians / 4 * 10, 10)

        # Environment (0-10 pts)
        pm25 = data.get('air_pollution_pm25', 0) or 0
        env = 10
        if pm25 > 0:
            env -= min(pm25 / 50 * 10, 10)
        score += max(env, 0)

        if score >= 20:
            country_scores.append({
                'country': country,
                'score': round(score, 1),
                'internet': round(internet, 1),
                'cost_level': 'Low' if gdp_per_capita < 15000 else 'Medium' if gdp_per_capita < 35000 else 'High'
            })

    country_scores.sort(key=lambda x: x['score'], reverse=True)

    # Generate report
    report = []
    report.append("=" * 80)
    report.append("✈️ DIGITAL NOMAD INDEX - Sofia Pulse Intelligence")
    report.append("=" * 80)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("Factors: Internet + Low Cost + Safety + Healthcare + Environment")
    report.append("")
    report.append("=" * 80)
    report.append("")

    report.append(f"🏆 TOP {min(len(country_scores), 30)} DIGITAL NOMAD DESTINATIONS")
    report.append("")

    for i, loc in enumerate(country_scores[:30], 1):
        report.append(f"#{i} - {loc['country']}")
        report.append(f"   Nomad Score: {loc['score']:.1f}/100")
        report.append(f"   Internet: {loc['internet']:.0f}%")
        report.append(f"   Cost Level: {loc['cost_level']}")

        if loc['score'] >= 70:
            rating = "🟢 EXCELLENT - Perfect for digital nomads"
        elif loc['score'] >= 55:
            rating = "🟡 GOOD - Great nomad destination"
        else:
            rating = "🟠 DECENT - Acceptable for nomads"

        report.append(f"   📊 RATING: {rating}")
        report.append("")

    report.append("=" * 80)
    report.append("📚 Scoring: Internet (30pts) + Cost (30pts) + Safety (20pts) + Health (10pts) + Env (10pts)")
    report.append("=" * 80)

    return "\n".join(report)

# ==================== REPORT 4: STEM EDUCATION ====================

def extract_universities_data(conn):
    """Extract top universities with cities"""
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT name, city, country, qs_rank, research_output_papers_year,
                   student_count, strong_fields
            FROM asia_universities
            WHERE qs_rank IS NOT NULL
            ORDER BY qs_rank ASC
            LIMIT 50
        """)
        universities = []
        for row in cur.fetchall():
            universities.append({
                'name': row[0],
                'city': row[1] or 'N/A',
                'country': row[2],
                'qs_rank': row[3],
                'papers': row[4] or 0,
                'students': row[5] or 0,
                'fields': row[6] or []
            })
        return universities
    except Exception as e:
        print(f"⚠️  Universities data not available: {e}")
        return []

def generate_stem_education_report(socio_data, research_data, universities_data):
    """Generate STEM Education Leaders Report"""

    country_scores = []

    for country in socio_data.keys():
        data = socio_data[country]
        research = research_data.get(country, {'papers': 0, 'avg_citations': 0})

        score = 0

        # University enrollment (0-30 pts)
        tertiary = data.get('school_enrollment_tertiary', 0) or 0
        score += min(tertiary / 100 * 30, 30)

        # R&D spending (0-30 pts)
        rd_gdp = data.get('research_development_gdp', 0) or 0
        score += min(rd_gdp / 4 * 30, 30)

        # Research output (0-25 pts)
        papers = research['papers']
        score += min(papers / 50 * 25, 25)

        # Literacy (0-15 pts)
        literacy = data.get('literacy_rate', 0) or 0
        score += min(literacy / 100 * 15, 15)

        # Find top universities in this country
        country_unis = [u for u in universities_data if u['country'] == country]
        top_uni = country_unis[0] if country_unis else None

        if score >= 15:
            country_scores.append({
                'country': country,
                'score': round(score, 1),
                'tertiary': round(tertiary, 1),
                'rd_gdp': round(rd_gdp, 2),
                'papers': papers,
                'top_university': top_uni
            })

    country_scores.sort(key=lambda x: x['score'], reverse=True)

    # Generate report
    report = []
    report.append("=" * 80)
    report.append("🎓 STEM EDUCATION LEADERS - Sofia Pulse Intelligence")
    report.append("=" * 80)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("Factors: University Enrollment + R&D Spending + Research Output + Literacy")
    report.append("")
    report.append("=" * 80)
    report.append("")

    report.append(f"🏆 TOP {min(len(country_scores), 30)} STEM EDUCATION LEADERS")
    report.append("")

    for i, loc in enumerate(country_scores[:30], 1):
        report.append(f"#{i} - {loc['country']}")

        # Show top university if available
        if loc['top_university']:
            uni = loc['top_university']
            report.append(f"   🏛️  Top University: {uni['name']} ({uni['city']})")
            report.append(f"   📊 QS Rank: #{uni['qs_rank']} | Papers/year: {uni['papers']:,}")

        report.append(f"   STEM Education Score: {loc['score']:.1f}/100")
        report.append(f"   University Enrollment: {loc['tertiary']:.0f}%")
        report.append(f"   R&D Spending: {loc['rd_gdp']}% of GDP")
        report.append(f"   Research Papers: {loc['papers']}")

        if loc['score'] >= 70:
            rating = "🟢 WORLD-CLASS - Top STEM education"
        elif loc['score'] >= 50:
            rating = "🟡 STRONG - Excellent STEM programs"
        else:
            rating = "🟠 GOOD - Solid STEM education"

        report.append(f"   ⭐ RATING: {rating}")
        report.append("")

    report.append("=" * 80)
    report.append("📚 Scoring: Enrollment (30pts) + R&D (30pts) + Research (25pts) + Literacy (15pts)")
    report.append("=" * 80)

    return "\n".join(report)

# ==================== MAIN ====================

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("=" * 80)
        print("📊 INTELLIGENCE REPORTS SUITE")
        print("=" * 80)
        print()

        print("📊 Extracting data...")
        socio_data = extract_socioeconomic_data(conn)
        print(f"   ✅ {len(socio_data)} countries")

        research_data = extract_research_activity(conn)
        print(f"   ✅ Research data for {len(research_data)} countries")

        funding_data = extract_funding_activity(conn)
        print(f"   ✅ Funding data for {len(funding_data)} countries")

        universities_data = extract_universities_data(conn)
        print(f"   ✅ Universities data: {len(universities_data)} top universities")

        print()

        # Generate Report 1: Innovation Hubs
        print("📊 Generating Innovation Hubs Report...")
        report1 = generate_innovation_hubs_report(socio_data, research_data, funding_data)
        with open('analytics/innovation-hubs-latest.txt', 'w', encoding='utf-8') as f:
            f.write(report1)
        print("   ✅ Saved: analytics/innovation-hubs-latest.txt")

        # Generate Report 2: Startup Founders
        print("📊 Generating Startup Founders Report...")
        report2 = generate_startup_founders_report(socio_data, funding_data)
        with open('analytics/startup-founders-latest.txt', 'w', encoding='utf-8') as f:
            f.write(report2)
        print("   ✅ Saved: analytics/startup-founders-latest.txt")

        # Generate Report 3: Digital Nomad
        print("📊 Generating Digital Nomad Report...")
        report3 = generate_digital_nomad_report(socio_data)
        with open('analytics/digital-nomad-latest.txt', 'w', encoding='utf-8') as f:
            f.write(report3)
        print("   ✅ Saved: analytics/digital-nomad-latest.txt")

        # Generate Report 4: STEM Education
        print("📊 Generating STEM Education Report...")
        report4 = generate_stem_education_report(socio_data, research_data, universities_data)
        with open('analytics/stem-education-latest.txt', 'w', encoding='utf-8') as f:
            f.write(report4)
        print("   ✅ Saved: analytics/stem-education-latest.txt")

        print()
        print("=" * 80)
        print("✅ ALL REPORTS GENERATED SUCCESSFULLY")
        print("=" * 80)
        print()
        print("Generated Reports:")
        print("  1. Innovation Hubs Ranking")
        print("  2. Best Countries for Startup Founders")
        print("  3. Digital Nomad Index")
        print("  4. STEM Education Leaders")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
