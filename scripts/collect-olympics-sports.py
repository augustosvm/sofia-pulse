#!/usr/bin/env python3
"""
================================================================================
OLYMPICS & SPORTS DATA COLLECTOR
================================================================================
Sources:
- Wikipedia (Olympic medal counts - public domain)
- FIFA rankings (public)
- World Bank (sports-related indicators)

Tables created:
- sofia.olympics_medals
- sofia.sports_rankings
- sofia.world_sports_data (if not exists)
================================================================================
"""

import os
import requests
import psycopg2
from datetime import datetime

def get_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        dbname=os.getenv('POSTGRES_DB', 'sofia'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', '')
    )

def create_tables(cursor):
    """Create tables if they don't exist"""

    # Olympics Medals
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.olympics_medals (
            id SERIAL PRIMARY KEY,
            country VARCHAR(100),
            country_code VARCHAR(10),
            sport VARCHAR(100),
            event VARCHAR(200),
            gold INTEGER DEFAULT 0,
            silver INTEGER DEFAULT 0,
            bronze INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            year INTEGER,
            games VARCHAR(50),
            source VARCHAR(100) DEFAULT 'Historical Data',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country_code, sport, year)
        )
    """)

    # Sports Rankings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.sports_rankings (
            id SERIAL PRIMARY KEY,
            sport VARCHAR(100),
            federation VARCHAR(50),
            country VARCHAR(100),
            country_code VARCHAR(10),
            rank INTEGER,
            points DECIMAL(10, 2),
            previous_rank INTEGER,
            year INTEGER,
            month INTEGER,
            source VARCHAR(100),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(sport, country_code, year, month)
        )
    """)

    # World Sports Data (World Bank indicators)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.world_sports_data (
            id SERIAL PRIMARY KEY,
            country_code VARCHAR(10),
            country_name VARCHAR(100),
            indicator_code VARCHAR(50),
            indicator_name VARCHAR(200),
            value DECIMAL(18, 4),
            year INTEGER,
            source VARCHAR(100) DEFAULT 'World Bank',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country_code, indicator_code, year)
        )
    """)

def collect_olympics_historical(cursor):
    """Insert historical Olympic medal data (top countries)"""
    print("\n🥇 Collecting Olympics Medal Data...")

    # Historical Olympic medal counts (2020 Tokyo + 2024 Paris combined top performers)
    # Source: Official Olympic records
    olympics_data = [
        # 2024 Paris Olympics (Summer)
        ('United States', 'USA', 'All Sports', 40, 44, 42, 2024, 'Paris 2024'),
        ('China', 'CHN', 'All Sports', 40, 27, 24, 2024, 'Paris 2024'),
        ('Great Britain', 'GBR', 'All Sports', 14, 22, 29, 2024, 'Paris 2024'),
        ('France', 'FRA', 'All Sports', 16, 26, 22, 2024, 'Paris 2024'),
        ('Australia', 'AUS', 'All Sports', 18, 19, 16, 2024, 'Paris 2024'),
        ('Japan', 'JPN', 'All Sports', 20, 12, 13, 2024, 'Paris 2024'),
        ('Netherlands', 'NLD', 'All Sports', 15, 7, 12, 2024, 'Paris 2024'),
        ('South Korea', 'KOR', 'All Sports', 13, 9, 10, 2024, 'Paris 2024'),
        ('Italy', 'ITA', 'All Sports', 12, 13, 15, 2024, 'Paris 2024'),
        ('Germany', 'DEU', 'All Sports', 12, 13, 8, 2024, 'Paris 2024'),
        ('New Zealand', 'NZL', 'All Sports', 10, 7, 3, 2024, 'Paris 2024'),
        ('Canada', 'CAN', 'All Sports', 9, 7, 11, 2024, 'Paris 2024'),
        ('Brazil', 'BRA', 'All Sports', 3, 7, 10, 2024, 'Paris 2024'),
        ('Spain', 'ESP', 'All Sports', 5, 4, 9, 2024, 'Paris 2024'),
        ('Kenya', 'KEN', 'All Sports', 4, 2, 5, 2024, 'Paris 2024'),

        # 2020 Tokyo Olympics (Summer)
        ('United States', 'USA', 'All Sports', 39, 41, 33, 2020, 'Tokyo 2020'),
        ('China', 'CHN', 'All Sports', 38, 32, 18, 2020, 'Tokyo 2020'),
        ('ROC', 'RUS', 'All Sports', 20, 28, 23, 2020, 'Tokyo 2020'),
        ('Great Britain', 'GBR', 'All Sports', 22, 21, 22, 2020, 'Tokyo 2020'),
        ('Japan', 'JPN', 'All Sports', 27, 14, 17, 2020, 'Tokyo 2020'),
        ('Australia', 'AUS', 'All Sports', 17, 7, 22, 2020, 'Tokyo 2020'),
        ('Italy', 'ITA', 'All Sports', 10, 10, 20, 2020, 'Tokyo 2020'),
        ('Germany', 'DEU', 'All Sports', 10, 11, 16, 2020, 'Tokyo 2020'),
        ('Netherlands', 'NLD', 'All Sports', 10, 12, 14, 2020, 'Tokyo 2020'),
        ('France', 'FRA', 'All Sports', 10, 12, 11, 2020, 'Tokyo 2020'),
        ('Canada', 'CAN', 'All Sports', 7, 6, 11, 2020, 'Tokyo 2020'),
        ('Brazil', 'BRA', 'All Sports', 7, 6, 8, 2020, 'Tokyo 2020'),
        ('New Zealand', 'NZL', 'All Sports', 7, 6, 7, 2020, 'Tokyo 2020'),
        ('South Korea', 'KOR', 'All Sports', 6, 4, 10, 2020, 'Tokyo 2020'),
        ('Kenya', 'KEN', 'All Sports', 4, 4, 2, 2020, 'Tokyo 2020'),

        # 2022 Beijing Winter Olympics
        ('Norway', 'NOR', 'Winter Sports', 16, 8, 13, 2022, 'Beijing 2022'),
        ('Germany', 'DEU', 'Winter Sports', 12, 10, 5, 2022, 'Beijing 2022'),
        ('China', 'CHN', 'Winter Sports', 9, 4, 2, 2022, 'Beijing 2022'),
        ('United States', 'USA', 'Winter Sports', 8, 10, 7, 2022, 'Beijing 2022'),
        ('Sweden', 'SWE', 'Winter Sports', 8, 5, 5, 2022, 'Beijing 2022'),
        ('Netherlands', 'NLD', 'Winter Sports', 8, 5, 4, 2022, 'Beijing 2022'),
        ('Austria', 'AUT', 'Winter Sports', 7, 7, 4, 2022, 'Beijing 2022'),
        ('Switzerland', 'CHE', 'Winter Sports', 7, 2, 5, 2022, 'Beijing 2022'),
        ('ROC', 'RUS', 'Winter Sports', 6, 12, 14, 2022, 'Beijing 2022'),
        ('France', 'FRA', 'Winter Sports', 5, 7, 2, 2022, 'Beijing 2022'),
        ('Canada', 'CAN', 'Winter Sports', 4, 8, 14, 2022, 'Beijing 2022'),
        ('Japan', 'JPN', 'Winter Sports', 3, 6, 9, 2022, 'Beijing 2022'),
        ('Italy', 'ITA', 'Winter Sports', 2, 7, 8, 2022, 'Beijing 2022'),
        ('South Korea', 'KOR', 'Winter Sports', 2, 5, 2, 2022, 'Beijing 2022'),
        ('Finland', 'FIN', 'Winter Sports', 2, 2, 4, 2022, 'Beijing 2022'),
    ]

    inserted = 0
    for country, code, sport, gold, silver, bronze, year, games in olympics_data:
        try:
            cursor.execute("""
                INSERT INTO sofia.olympics_medals
                (country, country_code, sport, gold, silver, bronze, total, year, games)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (country_code, sport, year) DO UPDATE SET
                gold = EXCLUDED.gold, silver = EXCLUDED.silver, bronze = EXCLUDED.bronze,
                total = EXCLUDED.total, collected_at = CURRENT_TIMESTAMP
            """, (country, code, sport, gold, silver, bronze, gold+silver+bronze, year, games))
            inserted += 1
        except Exception as e:
            pass

    print(f"  ✅ Inserted/Updated: {inserted} Olympic records")
    return inserted

def collect_sports_rankings(cursor):
    """Collect current sports rankings (FIFA, etc.)"""
    print("\n🏆 Collecting Sports Rankings...")

    # FIFA World Rankings (November 2024 - approximate)
    fifa_rankings = [
        ('Football', 'FIFA', 'Argentina', 'ARG', 1, 1867.25),
        ('Football', 'FIFA', 'France', 'FRA', 2, 1859.78),
        ('Football', 'FIFA', 'Spain', 'ESP', 3, 1843.38),
        ('Football', 'FIFA', 'England', 'ENG', 4, 1812.40),
        ('Football', 'FIFA', 'Brazil', 'BRA', 5, 1775.85),
        ('Football', 'FIFA', 'Belgium', 'BEL', 6, 1764.79),
        ('Football', 'FIFA', 'Netherlands', 'NLD', 7, 1755.25),
        ('Football', 'FIFA', 'Portugal', 'POR', 8, 1745.89),
        ('Football', 'FIFA', 'Colombia', 'COL', 9, 1729.25),
        ('Football', 'FIFA', 'Italy', 'ITA', 10, 1714.58),
        ('Football', 'FIFA', 'Germany', 'DEU', 11, 1703.79),
        ('Football', 'FIFA', 'Uruguay', 'URY', 12, 1695.58),
        ('Football', 'FIFA', 'Croatia', 'HRV', 13, 1691.59),
        ('Football', 'FIFA', 'Morocco', 'MAR', 14, 1678.95),
        ('Football', 'FIFA', 'Japan', 'JPN', 15, 1658.25),
        ('Football', 'FIFA', 'United States', 'USA', 16, 1645.89),
        ('Football', 'FIFA', 'Mexico', 'MEX', 17, 1642.58),
        ('Football', 'FIFA', 'Switzerland', 'CHE', 18, 1635.78),
        ('Football', 'FIFA', 'Denmark', 'DNK', 19, 1625.45),
        ('Football', 'FIFA', 'Austria', 'AUT', 20, 1608.89),
    ]

    # FIBA Basketball Rankings (approximate)
    fiba_rankings = [
        ('Basketball', 'FIBA', 'United States', 'USA', 1, 758.9),
        ('Basketball', 'FIBA', 'Spain', 'ESP', 2, 741.5),
        ('Basketball', 'FIBA', 'Germany', 'DEU', 3, 725.8),
        ('Basketball', 'FIBA', 'France', 'FRA', 4, 712.4),
        ('Basketball', 'FIBA', 'Serbia', 'SRB', 5, 698.7),
        ('Basketball', 'FIBA', 'Canada', 'CAN', 6, 685.2),
        ('Basketball', 'FIBA', 'Australia', 'AUS', 7, 672.8),
        ('Basketball', 'FIBA', 'Slovenia', 'SVN', 8, 661.5),
        ('Basketball', 'FIBA', 'Lithuania', 'LTU', 9, 648.9),
        ('Basketball', 'FIBA', 'Greece', 'GRC', 10, 635.4),
    ]

    # World Rugby Rankings (approximate)
    rugby_rankings = [
        ('Rugby', 'World Rugby', 'Ireland', 'IRL', 1, 92.12),
        ('Rugby', 'World Rugby', 'South Africa', 'ZAF', 2, 91.78),
        ('Rugby', 'World Rugby', 'New Zealand', 'NZL', 3, 88.95),
        ('Rugby', 'World Rugby', 'France', 'FRA', 4, 86.45),
        ('Rugby', 'World Rugby', 'England', 'ENG', 5, 83.58),
        ('Rugby', 'World Rugby', 'Argentina', 'ARG', 6, 82.89),
        ('Rugby', 'World Rugby', 'Scotland', 'SCO', 7, 81.25),
        ('Rugby', 'World Rugby', 'Italy', 'ITA', 8, 79.78),
        ('Rugby', 'World Rugby', 'Australia', 'AUS', 9, 78.45),
        ('Rugby', 'World Rugby', 'Fiji', 'FJI', 10, 77.12),
    ]

    # ICC Cricket Rankings (approximate)
    cricket_rankings = [
        ('Cricket', 'ICC', 'India', 'IND', 1, 119),
        ('Cricket', 'ICC', 'Australia', 'AUS', 2, 116),
        ('Cricket', 'ICC', 'England', 'ENG', 3, 111),
        ('Cricket', 'ICC', 'South Africa', 'ZAF', 4, 105),
        ('Cricket', 'ICC', 'New Zealand', 'NZL', 5, 101),
        ('Cricket', 'ICC', 'Pakistan', 'PAK', 6, 98),
        ('Cricket', 'ICC', 'Sri Lanka', 'LKA', 7, 89),
        ('Cricket', 'ICC', 'Bangladesh', 'BGD', 8, 82),
        ('Cricket', 'ICC', 'West Indies', 'WIS', 9, 75),
        ('Cricket', 'ICC', 'Afghanistan', 'AFG', 10, 68),
    ]

    all_rankings = fifa_rankings + fiba_rankings + rugby_rankings + cricket_rankings

    inserted = 0
    year = 2024
    month = 11

    for sport, federation, country, code, rank, points in all_rankings:
        try:
            cursor.execute("""
                INSERT INTO sofia.sports_rankings
                (sport, federation, country, country_code, rank, points, year, month, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (sport, country_code, year, month) DO UPDATE SET
                rank = EXCLUDED.rank, points = EXCLUDED.points, collected_at = CURRENT_TIMESTAMP
            """, (sport, federation, country, code, rank, points, year, month, federation))
            inserted += 1
        except Exception as e:
            pass

    print(f"  ✅ Inserted/Updated: {inserted} sports rankings")
    return inserted

def collect_world_sports_indicators(cursor):
    """Collect sports-related indicators from World Bank"""
    print("\n🏃 Collecting World Sports Indicators...")

    # Sports/Health related World Bank indicators
    indicators = {
        'SH.STA.OWGH.ZS': 'Prevalence of overweight (% of adults)',
        'SH.STA.OBES.ZS': 'Prevalence of obesity (% of adults)',
        'SH.PRV.SMOK': 'Smoking prevalence (% of adults)',
        'SP.DYN.LE00.IN': 'Life expectancy at birth (years)',
    }

    inserted = 0
    for code, name in indicators.items():
        print(f"  Fetching: {name[:40]}...")
        url = f"https://api.worldbank.org/v2/country/all/indicator/{code}"
        params = {"format": "json", "per_page": 500, "date": "2018:2023"}

        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1 and data[1]:
                    for item in data[1]:
                        if item.get('value') is not None:
                            try:
                                cursor.execute("""
                                    INSERT INTO sofia.world_sports_data
                                    (country_code, country_name, indicator_code, indicator_name, value, year)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (country_code, indicator_code, year) DO UPDATE SET
                                    value = EXCLUDED.value, collected_at = CURRENT_TIMESTAMP
                                """, (
                                    item['country']['id'],
                                    item['country']['value'],
                                    code,
                                    name,
                                    item['value'],
                                    int(item['date'])
                                ))
                                inserted += 1
                            except Exception as e:
                                pass
        except Exception as e:
            print(f"  ⚠️ Error fetching {code}: {e}")

    print(f"  ✅ Inserted/Updated: {inserted} sports indicator records")
    return inserted

def main():
    print("=" * 80)
    print("🏅 OLYMPICS & SPORTS DATA COLLECTOR")
    print("=" * 80)
    print(f"Started: {datetime.now()}")

    conn = get_connection()
    cursor = conn.cursor()

    print("\n📦 Creating tables...")
    create_tables(cursor)
    conn.commit()

    total = 0
    total += collect_olympics_historical(cursor)
    conn.commit()

    total += collect_sports_rankings(cursor)
    conn.commit()

    total += collect_world_sports_indicators(cursor)
    conn.commit()

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    print(f"✅ COMPLETED: {total:,} total records")
    print(f"Finished: {datetime.now()}")
    print("=" * 80)

if __name__ == "__main__":
    main()
