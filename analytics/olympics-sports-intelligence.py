#!/usr/bin/env python3
"""
Olympics & Sports Intelligence Report
======================================
Comprehensive sports analytics with actionable insights for:
- Sports marketing opportunities
- Regional market strategies
- Health/fitness industry targeting
- Event sponsorship decisions
"""
import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', os.getenv('POSTGRES_HOST', 'localhost')),
        port=os.getenv('DB_PORT', os.getenv('POSTGRES_PORT', '5432')),
        dbname=os.getenv('DB_NAME', os.getenv('POSTGRES_DB', 'sofia')),
        user=os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'postgres')),
        password=os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', ''))
    )

def main():
    conn = get_connection()
    cur = conn.cursor()

    r = [
        "=" * 80,
        "OLYMPICS & SPORTS INTELLIGENCE REPORT",
        "=" * 80,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]

    # =========================================================================
    # 1. OLYMPIC MEDALS - Historical Performance
    # =========================================================================
    r.extend(["=" * 80, "1. OLYMPIC MEDALS - COUNTRY DOMINANCE", "=" * 80, ""])

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.olympics_medals")
        count = cur.fetchone()[0]

        if count > 0:
            # Top medal winners by total medals
            cur.execute("""
                SELECT
                    country_name,
                    SUM(gold) as total_gold,
                    SUM(silver) as total_silver,
                    SUM(bronze) as total_bronze,
                    SUM(gold + silver + bronze) as total_medals,
                    COUNT(DISTINCT olympics_year) as editions
                FROM sofia.olympics_medals
                GROUP BY country_name
                ORDER BY total_gold DESC, total_medals DESC
                LIMIT 15
            """)
            rows = cur.fetchall()

            r.append("TOP 15 OLYMPIC NATIONS (All-time in database):")
            r.append("-" * 70)
            r.append(f"{'Country':<20} {'Gold':>6} {'Silver':>6} {'Bronze':>6} {'Total':>6} {'Events':>6}")
            r.append("-" * 70)

            for country, gold, silver, bronze, total, editions in rows:
                r.append(f"{country:<20} {gold:>6} {silver:>6} {bronze:>6} {total:>6} {editions:>6}")

            r.append("")

            # Recent Olympics breakdown
            cur.execute("""
                SELECT olympics_name, olympics_year, country_name, gold, silver, bronze
                FROM sofia.olympics_medals
                WHERE olympics_year >= 2020
                ORDER BY olympics_year DESC, gold DESC
            """)
            rows = cur.fetchall()

            if rows:
                r.append("RECENT OLYMPICS RESULTS:")
                r.append("-" * 70)
                current_event = None
                for event, year, country, g, s, b in rows:
                    if event != current_event:
                        r.append(f"\n  {event} ({year}):")
                        current_event = event
                    r.append(f"    {country}: {g}G {s}S {b}B = {g+s+b} total")
                r.append("")
        else:
            r.append("No Olympic medal data available.")
            r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 2. FIFA WORLD RANKINGS
    # =========================================================================
    r.extend(["=" * 80, "2. FIFA WORLD RANKINGS - FOOTBALL DOMINANCE", "=" * 80, ""])

    try:
        cur.execute("""
            SELECT COUNT(*), MAX(year)
            FROM sofia.sports_rankings
            WHERE federation = 'FIFA'
        """)
        count, latest_year = cur.fetchone()

        if count > 0:
            # Get unique rankings (deduplicated)
            cur.execute("""
                SELECT DISTINCT ON (rank)
                    country_name, rank, year
                FROM sofia.sports_rankings
                WHERE federation = 'FIFA'
                ORDER BY rank, year DESC
                LIMIT 20
            """)
            rows = cur.fetchall()

            r.append(f"FIFA World Rankings (Latest: {latest_year}):")
            r.append("-" * 50)

            for country, rank, year in rows:
                r.append(f"  #{rank:>2}. {country}")

            r.append("")
            r.append("INSIGHT: Top 10 countries are prime markets for:")
            r.append("  - Football/soccer apps and games")
            r.append("  - Sports betting platforms")
            r.append("  - Sports apparel and equipment")
            r.append("  - Broadcasting and streaming rights")
            r.append("")
        else:
            r.append("No FIFA ranking data available.")
            r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 3. SPORTS POPULARITY BY REGION
    # =========================================================================
    r.extend(["=" * 80, "3. SPORTS POPULARITY BY REGION - MARKET OPPORTUNITIES", "=" * 80, ""])

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.sports_regional")
        count = cur.fetchone()[0]

        if count > 0:
            # Sports by global reach
            cur.execute("""
                SELECT sport, COUNT(DISTINCT country_name) as countries,
                       STRING_AGG(DISTINCT region, ', ' ORDER BY region) as regions
                FROM sofia.sports_regional
                WHERE country_name IS NOT NULL
                GROUP BY sport
                ORDER BY countries DESC
                LIMIT 15
            """)
            rows = cur.fetchall()

            r.append("SPORTS BY GLOBAL REACH:")
            r.append("-" * 70)
            r.append(f"{'Sport':<35} {'Countries':>10}   Regions")
            r.append("-" * 70)

            for sport, countries, regions in rows:
                r.append(f"{sport:<35} {countries:>10}   {regions[:30]}")

            r.append("")

            # Top markets by sport
            r.append("TOP MARKETS BY SPORT (Very High Popularity):")
            r.append("-" * 70)

            for sport_name in ['Football/Soccer', 'Cricket', 'Basketball', 'Tennis', 'Rugby']:
                cur.execute("""
                    SELECT country_name, region
                    FROM sofia.sports_regional
                    WHERE sport = %s AND popularity_level IN ('Very High', 'Extremely High', 'High')
                    ORDER BY
                        CASE popularity_level
                            WHEN 'Extremely High' THEN 1
                            WHEN 'Very High' THEN 2
                            ELSE 3
                        END,
                        country_name
                    LIMIT 8
                """, (sport_name,))
                rows = cur.fetchall()

                if rows:
                    countries = [f"{c} ({r[:2]})" for c, r in rows]
                    r.append(f"  {sport_name}:")
                    r.append(f"    {', '.join(countries)}")

            r.append("")

            # Regional breakdown
            r.append("REGIONAL SPORTS BREAKDOWN:")
            r.append("-" * 70)

            cur.execute("""
                SELECT region,
                       COUNT(DISTINCT sport) as sports,
                       COUNT(DISTINCT country_name) as countries
                FROM sofia.sports_regional
                GROUP BY region
                ORDER BY countries DESC
            """)
            rows = cur.fetchall()

            for region, sports, countries in rows:
                cur.execute("""
                    SELECT sport, COUNT(*) as cnt
                    FROM sofia.sports_regional
                    WHERE region = %s AND popularity_level IN ('Very High', 'High')
                    GROUP BY sport
                    ORDER BY cnt DESC
                    LIMIT 3
                """, (region,))
                top_sports = [s[0] for s in cur.fetchall()]

                r.append(f"  {region}: {countries} countries, {sports} sports tracked")
                if top_sports:
                    r.append(f"    Top: {', '.join(top_sports)}")

            r.append("")
        else:
            r.append("No regional sports data available.")
            r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 4. PHYSICAL FITNESS & HEALTH RANKINGS
    # =========================================================================
    r.extend(["=" * 80, "4. PHYSICAL FITNESS & HEALTH - WELLNESS MARKET INSIGHTS", "=" * 80, ""])

    try:
        # Physical inactivity by country (health risk = business opportunity)
        # Use DISTINCT ON to get only the most recent year per country
        cur.execute("""
            SELECT country_code, value, year
            FROM (
                SELECT DISTINCT ON (country_code)
                    country_code, value, year
                FROM sofia.world_sports_data
                WHERE indicator_name ILIKE '%insufficiently physically active%'
                  AND value IS NOT NULL
                ORDER BY country_code, year DESC
            ) latest
            ORDER BY value DESC
            LIMIT 15
        """)
        rows = cur.fetchall()

        if rows:
            r.append("MOST PHYSICALLY INACTIVE POPULATIONS (% adolescents):")
            r.append("-" * 50)
            r.append("(Higher = more sedentary = fitness app opportunity)")
            r.append("")

            for country, value, year in rows:
                bar = "#" * int(float(value) / 5)
                r.append(f"  {country}: {float(value):.1f}% {bar}")

            r.append("")
            r.append("INSIGHT: High inactivity markets need:")
            r.append("  - Fitness apps and wearables")
            r.append("  - Gym/wellness center expansion")
            r.append("  - Corporate wellness programs")
            r.append("")

        # Overweight prevalence (health market)
        # Use DISTINCT ON to get only the most recent year per country
        cur.execute("""
            SELECT country_code, value, year
            FROM (
                SELECT DISTINCT ON (country_code)
                    country_code, value, year
                FROM sofia.world_sports_data
                WHERE indicator_name ILIKE '%overweight%adult%'
                  AND indicator_name NOT LIKE '%male%'
                  AND indicator_name NOT LIKE '%female%'
                  AND value IS NOT NULL
                ORDER BY country_code, year DESC
            ) latest
            ORDER BY value DESC
            LIMIT 15
        """)
        rows = cur.fetchall()

        if rows:
            r.append("OVERWEIGHT PREVALENCE (% of adults):")
            r.append("-" * 50)
            r.append("(Higher = larger health/wellness market)")
            r.append("")

            for country, value, year in rows:
                bar = "#" * int(float(value) / 5)
                r.append(f"  {country}: {float(value):.1f}% {bar}")

            r.append("")
            r.append("INSIGHT: High overweight markets = opportunities for:")
            r.append("  - Weight loss apps and programs")
            r.append("  - Healthy food delivery")
            r.append("  - Medical fitness solutions")
            r.append("")

        # Most active countries
        # Use DISTINCT ON to get only the most recent year per country
        cur.execute("""
            SELECT country_code, value, year
            FROM (
                SELECT DISTINCT ON (country_code)
                    country_code, value, year
                FROM sofia.world_sports_data
                WHERE indicator_name ILIKE '%insufficiently physically active%'
                  AND value IS NOT NULL
                ORDER BY country_code, year DESC
            ) latest
            ORDER BY value ASC
            LIMIT 10
        """)
        rows = cur.fetchall()

        if rows:
            r.append("MOST PHYSICALLY ACTIVE POPULATIONS:")
            r.append("-" * 50)
            r.append("(Lower inactivity = more active = sports equipment market)")
            r.append("")

            for country, value, year in rows:
                r.append(f"  {country}: Only {float(value):.1f}% inactive")

            r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 5. STRATEGIC INSIGHTS & RECOMMENDATIONS
    # =========================================================================
    r.extend(["=" * 80, "5. STRATEGIC INSIGHTS & RECOMMENDATIONS", "=" * 80, ""])

    r.append("SPORTS MARKETING OPPORTUNITIES:")
    r.append("-" * 50)
    r.append("")
    r.append("  FOOTBALL/SOCCER (Global reach: 55+ countries):")
    r.append("    - Prime markets: Brazil, Argentina, Germany, UK, Spain")
    r.append("    - Emerging: USA (growing rapidly), China, India")
    r.append("    - Products: Apps, streaming, betting, merchandise")
    r.append("")
    r.append("  CRICKET (Strong regional: 28 countries):")
    r.append("    - Dominant: India, Pakistan, Australia, UK, Caribbean")
    r.append("    - Massive market in South Asia (1.5B+ potential users)")
    r.append("    - Products: Fantasy leagues, streaming, equipment")
    r.append("")
    r.append("  BASKETBALL (Americas + Growing global):")
    r.append("    - Core: USA, China, Spain, Lithuania, Philippines")
    r.append("    - NBA influence drives global adoption")
    r.append("    - Products: Training apps, shoes, streetwear")
    r.append("")
    r.append("  ESPORTS (Not tracked but correlates with):")
    r.append("    - High inactivity markets = esports opportunity")
    r.append("    - Cross-promote: fitness gaming (Ring Fit, VR sports)")
    r.append("")

    r.append("FITNESS TECH OPPORTUNITIES:")
    r.append("-" * 50)
    r.append("")
    r.append("  HIGH PRIORITY MARKETS (sedentary + overweight):")
    r.append("    - USA, UK, Australia, Gulf states")
    r.append("    - Products: Peloton-style, weight loss apps, wearables")
    r.append("")
    r.append("  EMERGING FITNESS MARKETS:")
    r.append("    - Latin America: Brazil, Mexico, Argentina")
    r.append("    - Asia: China, Japan, South Korea")
    r.append("    - Products: Affordable fitness tech, gym franchises")
    r.append("")

    # Save report
    cur.close()
    conn.close()

    text = "\n".join(r)
    print(text)

    output_path = "analytics/olympics-sports-intelligence.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"\n{'=' * 80}")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    main()
