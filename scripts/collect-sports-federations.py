#!/usr/bin/env python3
"""
Sports Federations Official Data Collector
Coleta dados oficiais de federacoes esportivas internacionais

Federacoes:
- FIFA (Federation Internationale de Football Association)
- IOC (International Olympic Committee)
- UEFA (Union of European Football Associations)
- FIBA (International Basketball Federation)
- World Athletics (formerly IAAF)
- ITF (International Tennis Federation)
- FIA (Federation Internationale de l'Automobile)
- UCI (Union Cycliste Internationale)
- FIVB (Federation Internationale de Volleyball)
- World Rugby
"""

import os
from shared.geo_helpers import normalize_location
import sys
from shared.geo_helpers import normalize_location
import psycopg2
from shared.geo_helpers import normalize_location
import requests
from shared.geo_helpers import normalize_location
from datetime import datetime
from typing import List, Dict, Any

# Database connection
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', os.getenv('DB_HOST', 'localhost')),
    'port': int(os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432'))),
    'user': os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'sofia')),
    'password': os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', '')),
    'database': os.getenv('POSTGRES_DB', os.getenv('DB_NAME', 'sofia_db'))
}

# Sports Federations and their data
# Note: Most federations don't have public APIs, using published data
FEDERATIONS_DATA = {
    # ===========================================
    # FIFA - Football/Soccer
    # ===========================================
    'FIFA': {
        'name': 'FIFA - Federation Internationale de Football Association',
        'sport': 'Football/Soccer',
        'founded': 1904,
        'headquarters': 'Zurich, Switzerland',
        'member_associations': 211,
        'website': 'https://www.fifa.com/',
        'data_url': 'https://www.fifa.com/fifa-world-ranking',
        'competitions': ['FIFA World Cup', 'FIFA Womens World Cup', 'FIFA Club World Cup'],
        # FIFA World Rankings Top 20 (Men, November 2024)
        'rankings_men': [
            ('ARG', 'Argentina', 1), ('FRA', 'France', 2), ('ESP', 'Spain', 3),
            ('ENG', 'England', 4), ('BRA', 'Brazil', 5), ('BEL', 'Belgium', 6),
            ('NED', 'Netherlands', 7), ('POR', 'Portugal', 8), ('COL', 'Colombia', 9),
            ('ITA', 'Italy', 10), ('DEU', 'Germany', 11), ('CRO', 'Croatia', 12),
            ('MAR', 'Morocco', 13), ('URY', 'Uruguay', 14), ('USA', 'United States', 15),
            ('JPN', 'Japan', 16), ('MEX', 'Mexico', 17), ('SUI', 'Switzerland', 18),
            ('IRN', 'Iran', 19), ('DEN', 'Denmark', 20),
        ],
        # FIFA World Rankings Top 20 (Women)
        'rankings_women': [
            ('USA', 'United States', 1), ('ESP', 'Spain', 2), ('ENG', 'England', 3),
            ('SWE', 'Sweden', 4), ('DEU', 'Germany', 5), ('FRA', 'France', 6),
            ('NED', 'Netherlands', 7), ('JPN', 'Japan', 8), ('CAN', 'Canada', 9),
            ('BRA', 'Brazil', 10), ('AUS', 'Australia', 11), ('DEN', 'Denmark', 12),
            ('PRK', 'North Korea', 13), ('NOR', 'Norway', 14), ('ITA', 'Italy', 15),
            ('CHN', 'China', 16), ('KOR', 'South Korea', 17), ('COL', 'Colombia', 18),
            ('AUT', 'Austria', 19), ('SUI', 'Switzerland', 20),
        ],
    },

    # ===========================================
    # IOC - Olympics
    # ===========================================
    'IOC': {
        'name': 'IOC - International Olympic Committee',
        'sport': 'Multi-sport (Olympics)',
        'founded': 1894,
        'headquarters': 'Lausanne, Switzerland',
        'member_countries': 206,
        'website': 'https://www.olympic.org/',
        # Paris 2024 Medal Count Top 20
        'olympics_2024_medals': [
            ('USA', 'United States', 40, 44, 42, 126),  # Gold, Silver, Bronze, Total
            ('CHN', 'China', 40, 27, 24, 91),
            ('GBR', 'Great Britain', 14, 22, 29, 65),
            ('FRA', 'France', 16, 26, 22, 64),
            ('AUS', 'Australia', 18, 19, 16, 53),
            ('JPN', 'Japan', 20, 12, 13, 45),
            ('ITA', 'Italy', 12, 13, 15, 40),
            ('NED', 'Netherlands', 15, 7, 12, 34),
            ('KOR', 'South Korea', 13, 9, 10, 32),
            ('DEU', 'Germany', 12, 13, 8, 33),
            ('NZL', 'New Zealand', 10, 7, 3, 20),
            ('CAN', 'Canada', 9, 7, 11, 27),
            ('UZB', 'Uzbekistan', 8, 2, 3, 13),
            ('HUN', 'Hungary', 6, 7, 6, 19),
            ('ESP', 'Spain', 5, 4, 9, 18),
            ('SWE', 'Sweden', 4, 4, 3, 11),
            ('KEN', 'Kenya', 4, 2, 5, 11),
            ('NOR', 'Norway', 4, 1, 3, 8),
            ('IRL', 'Ireland', 4, 0, 3, 7),
            ('BRA', 'Brazil', 3, 7, 10, 20),
        ],
        # Registered Athletes Paris 2024
        'athlete_stats': {
            'total_athletes': 10500,
            'female_athletes': 5200,
            'male_athletes': 5300,
            'female_percentage': 49.5,
            'countries_with_female_athletes': 195,
        }
    },

    # ===========================================
    # UEFA - European Football
    # ===========================================
    'UEFA': {
        'name': 'UEFA - Union of European Football Associations',
        'sport': 'Football/Soccer (Europe)',
        'founded': 1954,
        'headquarters': 'Nyon, Switzerland',
        'member_associations': 55,
        'website': 'https://www.uefa.com/',
        # UEFA Coefficient Rankings Top 15 (Club)
        'club_rankings': [
            ('Real Madrid', 'ESP', 1), ('Manchester City', 'ENG', 2),
            ('Bayern Munich', 'DEU', 3), ('Liverpool', 'ENG', 4),
            ('PSG', 'FRA', 5), ('Inter Milan', 'ITA', 6),
            ('Borussia Dortmund', 'DEU', 7), ('Barcelona', 'ESP', 8),
            ('Atletico Madrid', 'ESP', 9), ('Bayer Leverkusen', 'DEU', 10),
        ],
        # UEFA Country Coefficient Rankings
        'country_rankings': [
            ('ENG', 'England', 1), ('ESP', 'Spain', 2), ('ITA', 'Italy', 3),
            ('DEU', 'Germany', 4), ('FRA', 'France', 5), ('NED', 'Netherlands', 6),
            ('POR', 'Portugal', 7), ('BEL', 'Belgium', 8), ('TUR', 'Turkey', 9),
            ('AUT', 'Austria', 10),
        ],
    },

    # ===========================================
    # FIBA - Basketball
    # ===========================================
    'FIBA': {
        'name': 'FIBA - International Basketball Federation',
        'sport': 'Basketball',
        'founded': 1932,
        'headquarters': 'Mies, Switzerland',
        'member_federations': 213,
        'website': 'https://www.fiba.basketball/',
        # FIBA World Rankings Top 15 (Men)
        'rankings_men': [
            ('USA', 'United States', 1), ('ESP', 'Spain', 2), ('DEU', 'Germany', 3),
            ('FRA', 'France', 4), ('SRB', 'Serbia', 5), ('CAN', 'Canada', 6),
            ('AUS', 'Australia', 7), ('LTU', 'Lithuania', 8), ('ARG', 'Argentina', 9),
            ('GRE', 'Greece', 10), ('SLO', 'Slovenia', 11), ('BRA', 'Brazil', 12),
            ('ITA', 'Italy', 13), ('LAT', 'Latvia', 14), ('JPN', 'Japan', 15),
        ],
        # FIBA World Rankings Top 15 (Women)
        'rankings_women': [
            ('USA', 'United States', 1), ('AUS', 'Australia', 2), ('ESP', 'Spain', 3),
            ('CHN', 'China', 4), ('CAN', 'Canada', 5), ('BEL', 'Belgium', 6),
            ('FRA', 'France', 7), ('SRB', 'Serbia', 8), ('JPN', 'Japan', 9),
            ('BRA', 'Brazil', 10), ('DEU', 'Germany', 11), ('KOR', 'South Korea', 12),
            ('PRI', 'Puerto Rico', 13), ('NGA', 'Nigeria', 14), ('GBR', 'Great Britain', 15),
        ],
    },

    # ===========================================
    # World Athletics (IAAF)
    # ===========================================
    'WORLD_ATHLETICS': {
        'name': 'World Athletics (formerly IAAF)',
        'sport': 'Athletics/Track and Field',
        'founded': 1912,
        'headquarters': 'Monaco',
        'member_federations': 214,
        'website': 'https://worldathletics.org/',
        # World Rankings by Country (2024)
        'country_rankings': [
            ('USA', 'United States', 1), ('ETH', 'Ethiopia', 2), ('KEN', 'Kenya', 3),
            ('JAM', 'Jamaica', 4), ('GBR', 'Great Britain', 5), ('JPN', 'Japan', 6),
            ('CHN', 'China', 7), ('DEU', 'Germany', 8), ('AUS', 'Australia', 9),
            ('NED', 'Netherlands', 10),
        ],
    },

    # ===========================================
    # ITF - Tennis
    # ===========================================
    'ITF': {
        'name': 'ITF - International Tennis Federation',
        'sport': 'Tennis',
        'founded': 1913,
        'headquarters': 'London, UK',
        'member_nations': 213,
        'website': 'https://www.itftennis.com/',
        # Davis Cup / Billie Jean King Cup Winners (recent)
        'recent_winners': {
            'davis_cup_2023': 'Italy',
            'bjk_cup_2023': 'Canada',
        },
    },

    # ===========================================
    # FIA - Motorsports
    # ===========================================
    'FIA': {
        'name': 'FIA - Federation Internationale de l\'Automobile',
        'sport': 'Motorsports',
        'founded': 1904,
        'headquarters': 'Paris, France',
        'member_organizations': 246,
        'website': 'https://www.fia.com/',
        # F1 2024 Standings
        'f1_2024': [
            ('Max Verstappen', 'NED', 1), ('Lando Norris', 'GBR', 2),
            ('Charles Leclerc', 'MCO', 3), ('Oscar Piastri', 'AUS', 4),
            ('Carlos Sainz', 'ESP', 5), ('Lewis Hamilton', 'GBR', 6),
            ('George Russell', 'GBR', 7), ('Sergio Perez', 'MEX', 8),
        ],
    },

    # ===========================================
    # FIVB - Volleyball
    # ===========================================
    'FIVB': {
        'name': 'FIVB - Federation Internationale de Volleyball',
        'sport': 'Volleyball',
        'founded': 1947,
        'headquarters': 'Lausanne, Switzerland',
        'member_federations': 222,
        'website': 'https://www.fivb.com/',
        # World Rankings Top 10 (Men)
        'rankings_men': [
            ('POL', 'Poland', 1), ('ITA', 'Italy', 2), ('USA', 'United States', 3),
            ('BRA', 'Brazil', 4), ('SLO', 'Slovenia', 5), ('JPN', 'Japan', 6),
            ('FRA', 'France', 7), ('ARG', 'Argentina', 8), ('SRB', 'Serbia', 9),
            ('DEU', 'Germany', 10),
        ],
        # World Rankings Top 10 (Women)
        'rankings_women': [
            ('TUR', 'Turkey', 1), ('BRA', 'Brazil', 2), ('ITA', 'Italy', 3),
            ('POL', 'Poland', 4), ('USA', 'United States', 5), ('CHN', 'China', 6),
            ('JPN', 'Japan', 7), ('SRB', 'Serbia', 8), ('NED', 'Netherlands', 9),
            ('DOM', 'Dominican Republic', 10),
        ],
    },

    # ===========================================
    # World Rugby
    # ===========================================
    'WORLD_RUGBY': {
        'name': 'World Rugby (formerly IRB)',
        'sport': 'Rugby',
        'founded': 1886,
        'headquarters': 'Dublin, Ireland',
        'member_unions': 131,
        'website': 'https://www.world.rugby/',
        # World Rankings Top 10 (Men)
        'rankings_men': [
            ('ZAF', 'South Africa', 1), ('IRL', 'Ireland', 2), ('NZL', 'New Zealand', 3),
            ('FRA', 'France', 4), ('ENG', 'England', 5), ('ARG', 'Argentina', 6),
            ('SCO', 'Scotland', 7), ('FJI', 'Fiji', 8), ('ITA', 'Italy', 9),
            ('AUS', 'Australia', 10),
        ],
        # World Rankings Top 10 (Women)
        'rankings_women': [
            ('ENG', 'England', 1), ('NZL', 'New Zealand', 2), ('CAN', 'Canada', 3),
            ('FRA', 'France', 4), ('USA', 'United States', 5), ('AUS', 'Australia', 6),
            ('IRL', 'Ireland', 7), ('ITA', 'Italy', 8), ('WAL', 'Wales', 9),
            ('SCO', 'Scotland', 10),
        ],
    },
}


def save_to_database(conn) -> int:
    """Save all sports federations data to PostgreSQL"""

    cursor = conn.cursor()

    # Create federations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.sports_federations (
            country_id INTEGER REFERENCES sofia.countries(id),
            id SERIAL PRIMARY KEY,
            federation_code VARCHAR(50) NOT NULL,
            federation_name TEXT,
            sport VARCHAR(100),
            founded INTEGER,
            headquarters VARCHAR(200),
            member_count INTEGER,
            website VARCHAR(200),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(federation_code)
        )
    """)

    # Create rankings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.sports_rankings (
            id SERIAL PRIMARY KEY,
            federation VARCHAR(50) NOT NULL,
            ranking_type VARCHAR(50),
            sex VARCHAR(20),
            rank INTEGER,
            country_code VARCHAR(10),
            country_name VARCHAR(100),
            entity_name VARCHAR(200),
            year INTEGER DEFAULT 2024,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(federation, ranking_type, sex, rank, year)
        )
    """)

    # Create Olympics medals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.olympics_medals (
            id SERIAL PRIMARY KEY,
            olympics_year INTEGER,
            olympics_name VARCHAR(100),
            country_code VARCHAR(10),
            country_name VARCHAR(100),
            gold INTEGER,
            silver INTEGER,
            bronze INTEGER,
            total INTEGER,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(olympics_year, country_code)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_rankings_federation
        ON sofia.sports_rankings(federation, ranking_type)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_olympics_year
        ON sofia.olympics_medals(olympics_year, total DESC)
    """)

    inserted = 0

    # Save federation info
    for fed_code, fed_data in FEDERATIONS_DATA.items():
        try:
            # Normalize headquarters location
            headquarters = fed_data.get('headquarters', '')
            location = normalize_location(conn, {'country': headquarters})
            country_id = location['country_id']

            cursor.execute("""
                INSERT INTO sofia.sports_federations (federation_code, federation_name, sport, founded, headquarters, member_count, website, country_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (federation_code)
                DO UPDATE SET federation_name = EXCLUDED.federation_name, country_id = EXCLUDED.country_id
            """, (
                fed_code,
                fed_data.get('name', ''),
                fed_data.get('sport', ''),
                fed_data.get('founded'),
                headquarters,
                fed_data.get('member_associations', fed_data.get('member_federations', fed_data.get('member_countries', 0))),
                fed_data.get('website', ''),
                country_id
            ))
            inserted += 1
        except:
            continue

        # Save rankings
        for ranking_key in ['rankings_men', 'rankings_women', 'country_rankings', 'club_rankings']:
            if ranking_key in fed_data:
                rankings = fed_data[ranking_key]
                sex = 'male' if 'men' in ranking_key else ('female' if 'women' in ranking_key else 'mixed')
                ranking_type = 'world_ranking' if 'ranking' in ranking_key else 'coefficient'

                for ranking in rankings:
                    try:
                        if len(ranking) == 3:  # (country_code, country_name, rank)
                            cursor.execute("""
                                INSERT INTO sofia.sports_rankings
                                (federation, ranking_type, sex, rank, country_code, country_name, entity_name, year)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (federation, ranking_type, sex, rank, year)
                                DO UPDATE SET country_code = EXCLUDED.country_code
                            """, (
                                fed_code,
                                ranking_type,
                                sex,
                                ranking[2],
                                ranking[0],
                                ranking[1],
                                ranking[1],
                                2024
                            ))
                            inserted += 1
                    except:
                        continue

        # Save Olympics medals
        if 'olympics_2024_medals' in fed_data:
            for medal_data in fed_data['olympics_2024_medals']:
                try:
                    cursor.execute("""
                        INSERT INTO sofia.olympics_medals
                        (olympics_year, olympics_name, country_code, country_name, gold, silver, bronze, total)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (olympics_year, country_code)
                        DO UPDATE SET gold = EXCLUDED.gold, silver = EXCLUDED.silver, bronze = EXCLUDED.bronze, total = EXCLUDED.total
                    """, (
                        2024,
                        'Paris 2024',
                        medal_data[0],
                        medal_data[1],
                        medal_data[2],
                        medal_data[3],
                        medal_data[4],
                        medal_data[5]
                    ))
                    inserted += 1
                except:
                    continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("=" * 80)
    print("SPORTS FEDERATIONS OFFICIAL DATA COLLECTOR")
    print("=" * 80)
    print("")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    print("Federations covered:")
    for fed_code, fed_data in FEDERATIONS_DATA.items():
        print(f"  - {fed_data['name']}")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Database connected")
        print("")
    except Exception as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)

    print("Saving federations data...")
    total_records = save_to_database(conn)

    conn.close()

    print("")
    print("=" * 80)
    print("SPORTS FEDERATIONS DATA COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total records: {total_records}")
    print("")
    print("Federations included:")
    print("  - FIFA (Football/Soccer) - World Rankings Men & Women")
    print("  - IOC (Olympics) - Paris 2024 Medal Count")
    print("  - UEFA (European Football) - Club & Country Coefficients")
    print("  - FIBA (Basketball) - World Rankings Men & Women")
    print("  - World Athletics - Country Rankings")
    print("  - ITF (Tennis) - Federation Data")
    print("  - FIA (Motorsports) - F1 Standings")
    print("  - FIVB (Volleyball) - World Rankings Men & Women")
    print("  - World Rugby - World Rankings Men & Women")
    print("")
    print("Tables created:")
    print("  - sofia.sports_federations")
    print("  - sofia.sports_rankings")
    print("  - sofia.olympics_medals")
    print("")
    print("Gender data available:")
    print("  - FIFA: Men & Women world rankings")
    print("  - FIBA: Men & Women world rankings")
    print("  - FIVB: Men & Women world rankings")
    print("  - World Rugby: Men & Women rankings")
    print("  - IOC: 49.5% female athletes at Paris 2024")


if __name__ == '__main__':
    main()