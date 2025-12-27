#!/usr/bin/env python3
"""
Regional Sports Data Collector
Coleta dados de muitos esportes regionalizados pelo mundo

Federacoes por regiao:
- CONMEBOL, CONCACAF, UEFA, AFC, CAF, OFC (Futebol)
- ICC (Cricket - Asia, Oceania, UK)
- NBA, EuroLeague, NBL (Basquete regional)
- IPL, BBL, CPL (Cricket T20)
- E muitos outros esportes
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

# ===========================================
# REGIONAL SPORTS DATA
# ===========================================

REGIONAL_SPORTS_DATA = {
    # ===========================================
    # FOOTBALL/SOCCER BY REGION
    # ===========================================
    'football': {
        'sport': 'Football/Soccer',
        'world_federation': 'FIFA',
        'regional_federations': {
            'UEFA': {
                'region': 'Europe',
                'members': 55,
                'top_leagues': ['Premier League (ENG)', 'La Liga (ESP)', 'Bundesliga (DEU)', 'Serie A (ITA)', 'Ligue 1 (FRA)'],
                'top_countries': [('ENG', 'England'), ('ESP', 'Spain'), ('DEU', 'Germany'), ('ITA', 'Italy'), ('FRA', 'France'),
                                  ('NLD', 'Netherlands'), ('PRT', 'Portugal'), ('BEL', 'Belgium'), ('TUR', 'Turkey'), ('RUS', 'Russia')],
            },
            'CONMEBOL': {
                'region': 'South America',
                'members': 10,
                'top_leagues': ['Brasileirao (BRA)', 'Liga Profesional (ARG)', 'Primera Division (URY)'],
                'top_countries': [('ARG', 'Argentina'), ('BRA', 'Brazil'), ('URY', 'Uruguay'), ('COL', 'Colombia'), ('CHL', 'Chile'),
                                  ('ECU', 'Ecuador'), ('PER', 'Peru'), ('PRY', 'Paraguay'), ('VEN', 'Venezuela'), ('BOL', 'Bolivia')],
            },
            'CONCACAF': {
                'region': 'North/Central America & Caribbean',
                'members': 41,
                'top_leagues': ['MLS (USA)', 'Liga MX (MEX)', 'Canadian Premier League'],
                'top_countries': [('MEX', 'Mexico'), ('USA', 'United States'), ('CAN', 'Canada'), ('CRI', 'Costa Rica'), ('JAM', 'Jamaica'),
                                  ('HON', 'Honduras'), ('PAN', 'Panama'), ('SLV', 'El Salvador'), ('GTM', 'Guatemala'), ('HAI', 'Haiti')],
            },
            'AFC': {
                'region': 'Asia',
                'members': 47,
                'top_leagues': ['J-League (JPN)', 'K-League (KOR)', 'Chinese Super League', 'Saudi Pro League'],
                'top_countries': [('JPN', 'Japan'), ('KOR', 'South Korea'), ('AUS', 'Australia'), ('IRN', 'Iran'), ('SAU', 'Saudi Arabia'),
                                  ('QAT', 'Qatar'), ('UAE', 'United Arab Emirates'), ('CHN', 'China'), ('IRQ', 'Iraq'), ('UZB', 'Uzbekistan')],
            },
            'CAF': {
                'region': 'Africa',
                'members': 54,
                'top_leagues': ['Egyptian Premier League', 'NPFL (NGA)', 'Botola Pro (MAR)'],
                'top_countries': [('MAR', 'Morocco'), ('SEN', 'Senegal'), ('EGY', 'Egypt'), ('NGA', 'Nigeria'), ('CMR', 'Cameroon'),
                                  ('ALG', 'Algeria'), ('TUN', 'Tunisia'), ('CIV', 'Cote d Ivoire'), ('GHA', 'Ghana'), ('ZAF', 'South Africa')],
            },
            'OFC': {
                'region': 'Oceania',
                'members': 13,
                'top_leagues': ['A-League (NZL)'],
                'top_countries': [('NZL', 'New Zealand'), ('NCL', 'New Caledonia'), ('TAH', 'Tahiti'), ('FJI', 'Fiji'), ('PNG', 'Papua New Guinea')],
            },
        }
    },

    # ===========================================
    # CRICKET (ICC)
    # ===========================================
    'cricket': {
        'sport': 'Cricket',
        'world_federation': 'ICC',
        'popular_regions': ['Asia', 'Oceania', 'UK/Ireland', 'Caribbean', 'Africa'],
        'regional_data': {
            'South Asia': {
                'countries': [('IND', 'India'), ('PAK', 'Pakistan'), ('BGD', 'Bangladesh'), ('LKA', 'Sri Lanka'), ('NPL', 'Nepal'), ('AFG', 'Afghanistan')],
                'leagues': ['IPL (India)', 'PSL (Pakistan)', 'BPL (Bangladesh)'],
                'popularity': 'Extremely High',
            },
            'Oceania': {
                'countries': [('AUS', 'Australia'), ('NZL', 'New Zealand')],
                'leagues': ['Big Bash League (Australia)', 'Super Smash (NZ)'],
                'popularity': 'High',
            },
            'UK & Ireland': {
                'countries': [('ENG', 'England'), ('IRL', 'Ireland'), ('SCO', 'Scotland')],
                'leagues': ['The Hundred', 'County Championship'],
                'popularity': 'High',
            },
            'Caribbean': {
                'countries': [('WI', 'West Indies'), ('JAM', 'Jamaica'), ('TTO', 'Trinidad'), ('BRB', 'Barbados')],
                'leagues': ['Caribbean Premier League'],
                'popularity': 'High',
            },
            'Africa': {
                'countries': [('ZAF', 'South Africa'), ('ZWE', 'Zimbabwe'), ('KEN', 'Kenya')],
                'leagues': ['SA20 (South Africa)'],
                'popularity': 'Medium',
            },
        },
        'icc_rankings_men': [
            ('IND', 'India', 1), ('AUS', 'Australia', 2), ('ENG', 'England', 3), ('NZL', 'New Zealand', 4),
            ('ZAF', 'South Africa', 5), ('PAK', 'Pakistan', 6), ('BGD', 'Bangladesh', 7), ('LKA', 'Sri Lanka', 8),
            ('AFG', 'Afghanistan', 9), ('WI', 'West Indies', 10),
        ],
        'icc_rankings_women': [
            ('AUS', 'Australia', 1), ('ENG', 'England', 2), ('IND', 'India', 3), ('NZL', 'New Zealand', 4),
            ('ZAF', 'South Africa', 5), ('PAK', 'Pakistan', 6), ('WI', 'West Indies', 7), ('BGD', 'Bangladesh', 8),
        ],
    },

    # ===========================================
    # BASKETBALL BY REGION
    # ===========================================
    'basketball': {
        'sport': 'Basketball',
        'world_federation': 'FIBA',
        'regional_data': {
            'North America': {
                'countries': [('USA', 'United States'), ('CAN', 'Canada')],
                'leagues': ['NBA', 'WNBA', 'G League', 'CEBL (Canada)'],
                'popularity': 'Extremely High',
            },
            'Europe': {
                'countries': [('ESP', 'Spain'), ('TUR', 'Turkey'), ('GRC', 'Greece'), ('SRB', 'Serbia'), ('LTU', 'Lithuania'),
                              ('FRA', 'France'), ('ITA', 'Italy'), ('DEU', 'Germany'), ('RUS', 'Russia'), ('SLO', 'Slovenia')],
                'leagues': ['EuroLeague', 'EuroCup', 'Liga ACB (Spain)', 'VTB League'],
                'popularity': 'High',
            },
            'Asia': {
                'countries': [('CHN', 'China'), ('JPN', 'Japan'), ('PHL', 'Philippines'), ('KOR', 'South Korea'), ('AUS', 'Australia')],
                'leagues': ['CBA (China)', 'B.League (Japan)', 'PBA (Philippines)', 'NBL (Australia)'],
                'popularity': 'Growing',
            },
            'South America': {
                'countries': [('ARG', 'Argentina'), ('BRA', 'Brazil'), ('VEN', 'Venezuela'), ('URY', 'Uruguay')],
                'leagues': ['Liga Nacional (Argentina)', 'NBB (Brazil)'],
                'popularity': 'Medium',
            },
        },
    },

    # ===========================================
    # VOLLEYBALL BY REGION
    # ===========================================
    'volleyball': {
        'sport': 'Volleyball',
        'world_federation': 'FIVB',
        'regional_data': {
            'Europe': {
                'countries': [('POL', 'Poland'), ('ITA', 'Italy'), ('SRB', 'Serbia'), ('TUR', 'Turkey'), ('RUS', 'Russia'),
                              ('FRA', 'France'), ('DEU', 'Germany'), ('NLD', 'Netherlands'), ('BEL', 'Belgium'), ('SLO', 'Slovenia')],
                'leagues': ['SuperLega (Italy)', 'PlusLiga (Poland)', 'Sultanlar Ligi (Turkey)'],
            },
            'South America': {
                'countries': [('BRA', 'Brazil'), ('ARG', 'Argentina'), ('COL', 'Colombia'), ('VEN', 'Venezuela')],
                'leagues': ['Superliga (Brazil)'],
            },
            'Asia': {
                'countries': [('JPN', 'Japan'), ('CHN', 'China'), ('KOR', 'South Korea'), ('IRN', 'Iran'), ('THA', 'Thailand')],
                'leagues': ['V.League (Japan)', 'CVL (China)'],
            },
        },
    },

    # ===========================================
    # RUGBY BY REGION
    # ===========================================
    'rugby': {
        'sport': 'Rugby',
        'world_federation': 'World Rugby',
        'regional_data': {
            'Europe': {
                'countries': [('FRA', 'France'), ('ENG', 'England'), ('IRL', 'Ireland'), ('WAL', 'Wales'), ('SCO', 'Scotland'), ('ITA', 'Italy')],
                'leagues': ['Top 14 (France)', 'Premiership (England)', 'URC'],
            },
            'Southern Hemisphere': {
                'countries': [('NZL', 'New Zealand'), ('ZAF', 'South Africa'), ('AUS', 'Australia'), ('ARG', 'Argentina'), ('FJI', 'Fiji')],
                'leagues': ['Super Rugby'],
            },
            'Pacific Islands': {
                'countries': [('FJI', 'Fiji'), ('SAM', 'Samoa'), ('TON', 'Tonga')],
            },
        },
    },

    # ===========================================
    # SWIMMING (WORLD AQUATICS)
    # ===========================================
    'swimming': {
        'sport': 'Swimming',
        'world_federation': 'World Aquatics (FINA)',
        'top_countries': [('USA', 'United States'), ('AUS', 'Australia'), ('CHN', 'China'), ('GBR', 'Great Britain'),
                          ('FRA', 'France'), ('ITA', 'Italy'), ('JPN', 'Japan'), ('HUN', 'Hungary'), ('BRA', 'Brazil'), ('NLD', 'Netherlands')],
        'regional_strength': {
            'North America': ['USA', 'CAN'],
            'Europe': ['GBR', 'FRA', 'ITA', 'HUN', 'NLD', 'DEU', 'SWE'],
            'Asia Pacific': ['AUS', 'CHN', 'JPN', 'KOR'],
            'South America': ['BRA'],
        },
    },

    # ===========================================
    # TENNIS (ITF)
    # ===========================================
    'tennis': {
        'sport': 'Tennis',
        'world_federation': 'ITF',
        'regional_data': {
            'Europe': {
                'countries': [('ESP', 'Spain'), ('SRB', 'Serbia'), ('DEU', 'Germany'), ('ITA', 'Italy'), ('FRA', 'France'),
                              ('GBR', 'Great Britain'), ('GRC', 'Greece'), ('POL', 'Poland'), ('CHE', 'Switzerland'), ('RUS', 'Russia')],
                'grand_slam': 'French Open, Wimbledon',
            },
            'North America': {
                'countries': [('USA', 'United States'), ('CAN', 'Canada')],
                'grand_slam': 'US Open',
            },
            'Asia Pacific': {
                'countries': [('AUS', 'Australia'), ('JPN', 'Japan'), ('CHN', 'China'), ('KOR', 'South Korea')],
                'grand_slam': 'Australian Open',
            },
            'South America': {
                'countries': [('ARG', 'Argentina'), ('BRA', 'Brazil'), ('CHL', 'Chile')],
            },
        },
    },

    # ===========================================
    # CYCLING (UCI)
    # ===========================================
    'cycling': {
        'sport': 'Cycling',
        'world_federation': 'UCI',
        'regional_data': {
            'Europe': {
                'countries': [('BEL', 'Belgium'), ('NLD', 'Netherlands'), ('FRA', 'France'), ('ESP', 'Spain'), ('ITA', 'Italy'),
                              ('GBR', 'Great Britain'), ('DNK', 'Denmark'), ('SLO', 'Slovenia'), ('DEU', 'Germany'), ('CHE', 'Switzerland')],
                'major_races': ['Tour de France', 'Giro dItalia', 'Vuelta a Espana'],
            },
            'Americas': {
                'countries': [('USA', 'United States'), ('COL', 'Colombia'), ('ECU', 'Ecuador')],
            },
            'Asia Pacific': {
                'countries': [('AUS', 'Australia'), ('NZL', 'New Zealand'), ('JPN', 'Japan')],
            },
        },
    },

    # ===========================================
    # TABLE TENNIS (ITTF)
    # ===========================================
    'table_tennis': {
        'sport': 'Table Tennis',
        'world_federation': 'ITTF',
        'regional_data': {
            'Asia': {
                'countries': [('CHN', 'China'), ('JPN', 'Japan'), ('KOR', 'South Korea'), ('TWN', 'Chinese Taipei'), ('HKG', 'Hong Kong')],
                'dominance': 'Very High',
            },
            'Europe': {
                'countries': [('DEU', 'Germany'), ('SWE', 'Sweden'), ('FRA', 'France'), ('ENG', 'England')],
                'dominance': 'Medium',
            },
        },
    },

    # ===========================================
    # BADMINTON (BWF)
    # ===========================================
    'badminton': {
        'sport': 'Badminton',
        'world_federation': 'BWF',
        'regional_data': {
            'Asia': {
                'countries': [('CHN', 'China'), ('IDN', 'Indonesia'), ('JPN', 'Japan'), ('MYS', 'Malaysia'), ('KOR', 'South Korea'),
                              ('IND', 'India'), ('THA', 'Thailand'), ('TWN', 'Chinese Taipei')],
                'dominance': 'Very High',
            },
            'Europe': {
                'countries': [('DNK', 'Denmark'), ('ESP', 'Spain'), ('DEU', 'Germany'), ('ENG', 'England')],
                'dominance': 'Medium',
            },
        },
    },

    # ===========================================
    # HANDBALL (IHF)
    # ===========================================
    'handball': {
        'sport': 'Handball',
        'world_federation': 'IHF',
        'regional_data': {
            'Europe': {
                'countries': [('DNK', 'Denmark'), ('FRA', 'France'), ('ESP', 'Spain'), ('DEU', 'Germany'), ('NOR', 'Norway'),
                              ('SWE', 'Sweden'), ('CRO', 'Croatia'), ('HUN', 'Hungary'), ('SLO', 'Slovenia'), ('POL', 'Poland')],
                'dominance': 'Very High',
            },
            'Africa & Middle East': {
                'countries': [('EGY', 'Egypt'), ('TUN', 'Tunisia'), ('QAT', 'Qatar')],
            },
            'South America': {
                'countries': [('BRA', 'Brazil'), ('ARG', 'Argentina')],
            },
        },
    },

    # ===========================================
    # HOCKEY (FIH)
    # ===========================================
    'hockey': {
        'sport': 'Field Hockey',
        'world_federation': 'FIH',
        'regional_data': {
            'Europe': {
                'countries': [('NLD', 'Netherlands'), ('BEL', 'Belgium'), ('DEU', 'Germany'), ('ENG', 'England'), ('ESP', 'Spain')],
            },
            'Asia': {
                'countries': [('IND', 'India'), ('PAK', 'Pakistan'), ('MYS', 'Malaysia'), ('KOR', 'South Korea'), ('JPN', 'Japan')],
            },
            'Oceania': {
                'countries': [('AUS', 'Australia'), ('NZL', 'New Zealand')],
            },
            'South America': {
                'countries': [('ARG', 'Argentina')],
            },
        },
    },

    # ===========================================
    # WINTER SPORTS (FIS)
    # ===========================================
    'winter_sports': {
        'sport': 'Winter Sports (Skiing, Snowboard)',
        'world_federation': 'FIS',
        'regional_data': {
            'Alpine Europe': {
                'countries': [('CHE', 'Switzerland'), ('AUT', 'Austria'), ('FRA', 'France'), ('ITA', 'Italy'), ('DEU', 'Germany'), ('NOR', 'Norway')],
            },
            'Scandinavia': {
                'countries': [('NOR', 'Norway'), ('SWE', 'Sweden'), ('FIN', 'Finland')],
            },
            'North America': {
                'countries': [('USA', 'United States'), ('CAN', 'Canada')],
            },
            'Asia': {
                'countries': [('JPN', 'Japan'), ('KOR', 'South Korea'), ('CHN', 'China')],
            },
        },
    },

    # ===========================================
    # MARTIAL ARTS
    # ===========================================
    'martial_arts': {
        'sport': 'Martial Arts',
        'disciplines': {
            'Judo': {
                'federation': 'IJF',
                'top_countries': [('JPN', 'Japan'), ('FRA', 'France'), ('KOR', 'South Korea'), ('BRA', 'Brazil'), ('GEO', 'Georgia')],
            },
            'Taekwondo': {
                'federation': 'World Taekwondo',
                'top_countries': [('KOR', 'South Korea'), ('CHN', 'China'), ('IRN', 'Iran'), ('ESP', 'Spain'), ('MEX', 'Mexico')],
            },
            'Wrestling': {
                'federation': 'UWW',
                'top_countries': [('RUS', 'Russia'), ('USA', 'United States'), ('JPN', 'Japan'), ('IRN', 'Iran'), ('TUR', 'Turkey')],
            },
            'Boxing': {
                'federation': 'IBA',
                'top_countries': [('CUB', 'Cuba'), ('USA', 'United States'), ('GBR', 'Great Britain'), ('UZB', 'Uzbekistan'), ('KAZ', 'Kazakhstan')],
            },
            'Karate': {
                'federation': 'WKF',
                'top_countries': [('JPN', 'Japan'), ('ESP', 'Spain'), ('TUR', 'Turkey'), ('FRA', 'France'), ('EGY', 'Egypt')],
            },
        },
    },

    # ===========================================
    # MOTORSPORTS (FIA)
    # ===========================================
    'motorsports': {
        'sport': 'Motorsports',
        'world_federation': 'FIA',
        'regional_data': {
            'Europe': {
                'series': ['Formula 1', 'WRC', 'WEC'],
                'countries': [('GBR', 'Great Britain'), ('DEU', 'Germany'), ('ITA', 'Italy'), ('FRA', 'France'), ('ESP', 'Spain'), ('NLD', 'Netherlands')],
            },
            'Americas': {
                'series': ['IndyCar', 'NASCAR', 'Formula E'],
                'countries': [('USA', 'United States'), ('BRA', 'Brazil'), ('MEX', 'Mexico'), ('ARG', 'Argentina')],
            },
            'Asia Pacific': {
                'series': ['Super GT', 'Super Formula'],
                'countries': [('JPN', 'Japan'), ('AUS', 'Australia')],
            },
        },
    },

    # ===========================================
    # GOLF (IGF)
    # ===========================================
    'golf': {
        'sport': 'Golf',
        'world_federation': 'IGF',
        'regional_data': {
            'North America': {
                'tours': ['PGA Tour', 'LPGA Tour'],
                'countries': [('USA', 'United States'), ('CAN', 'Canada')],
            },
            'Europe': {
                'tours': ['DP World Tour'],
                'countries': [('GBR', 'Great Britain'), ('IRL', 'Ireland'), ('ESP', 'Spain'), ('SWE', 'Sweden'), ('DEU', 'Germany')],
            },
            'Asia': {
                'tours': ['Asian Tour', 'Japan Golf Tour', 'KLPGA'],
                'countries': [('JPN', 'Japan'), ('KOR', 'South Korea'), ('THA', 'Thailand'), ('CHN', 'China')],
            },
            'Oceania': {
                'tours': ['PGA Tour Australasia'],
                'countries': [('AUS', 'Australia'), ('NZL', 'New Zealand')],
            },
        },
    },

    # ===========================================
    # E-SPORTS (EMERGING)
    # ===========================================
    'esports': {
        'sport': 'E-Sports',
        'regional_data': {
            'Asia': {
                'countries': [('KOR', 'South Korea'), ('CHN', 'China'), ('JPN', 'Japan'), ('VNM', 'Vietnam'), ('PHL', 'Philippines')],
                'games': ['League of Legends', 'PUBG', 'Valorant', 'Mobile Legends'],
            },
            'Europe': {
                'countries': [('DNK', 'Denmark'), ('SWE', 'Sweden'), ('FRA', 'France'), ('DEU', 'Germany'), ('POL', 'Poland')],
                'games': ['CS2', 'Dota 2', 'League of Legends'],
            },
            'Americas': {
                'countries': [('USA', 'United States'), ('BRA', 'Brazil'), ('CAN', 'Canada')],
                'games': ['League of Legends', 'Valorant', 'Fortnite'],
            },
        },
    },
}


def save_to_database(conn) -> int:
    """Save all regional sports data to PostgreSQL"""

    cursor = conn.cursor()

    # Create regional sports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.sports_regional (
            country_id INTEGER REFERENCES sofia.countries(id),
            id SERIAL PRIMARY KEY,
            sport VARCHAR(100) NOT NULL,
            world_federation VARCHAR(100),
            regional_federation VARCHAR(100),
            region VARCHAR(100),
            country_code VARCHAR(10),
            country_name VARCHAR(100),
            league_name VARCHAR(200),
            ranking INTEGER,
            popularity_level VARCHAR(50),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(sport, region, country_code)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sports_regional_sport
        ON sofia.sports_regional(sport)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sports_regional_region
        ON sofia.sports_regional(region)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sports_regional_country
        ON sofia.sports_regional(country_code)
    """)

    inserted = 0

    for sport_key, sport_data in REGIONAL_SPORTS_DATA.items():
        sport_name = sport_data.get('sport', sport_key)
        world_fed = sport_data.get('world_federation', '')

        # Handle different data structures
        if 'regional_federations' in sport_data:
            for fed_code, fed_data in sport_data['regional_federations'].items():
                region = fed_data.get('region', '')
                for i, country in enumerate(fed_data.get('top_countries', [])):
                    try:
                        # Normalize country
                        country_code = country[0]
                        location = normalize_location(conn, {'country': country_code}),
                        country_id = location['country_id']

                        cursor.execute(""",
                            INSERT INTO sofia.sports_regional (sport, world_federation, regional_federation, region, country_code, country_name, ranking, country_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (sport, region, country_code),
                            DO UPDATE SET ranking = EXCLUDED.ranking                        """, (
                            sport_name,
                            world_fed,
                            fed_code,
                            region,
                            country[0],
                            country[1],
                            i + 1,
                            country_id
                        ))
                        inserted += 1
                    except:
                        continue

        elif 'regional_data' in sport_data:
            for region, region_data in sport_data['regional_data'].items():
                countries = region_data.get('countries', [])
                for i, country in enumerate(countries):
                    try:
                        cursor.execute(""",
                            INSERT INTO sofia.sports_regional (sport, world_federation, region, country_code, country_name, ranking, popularity_level, country_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (sport, region, country_code)
                            DO UPDATE SET ranking = EXCLUDED.ranking
                        """, (
                            sport_name,
                            world_fed,
                            region,
                            country[0],
                            country[1],
                            i + 1,
                            region_data.get('dominance', region_data.get('popularity', 'Medium')),
                            country_id
                        ))
                        inserted += 1
                    except:
                        continue

        # Handle rankings
        for ranking_key in ['icc_rankings_men', 'icc_rankings_women', 'top_countries']:
            if ranking_key in sport_data:
                rankings = sport_data[ranking_key]
                sex = 'men' if 'men' in ranking_key else ('women' if 'women' in ranking_key else 'mixed')
                for ranking in rankings:
                    try:
                        cursor.execute(""",
                            INSERT INTO sofia.sports_regional (sport, world_federation, region, country_code, country_name, ranking, country_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (sport, region, country_code)
                            DO UPDATE SET ranking = EXCLUDED.ranking
                        """, (
                            sport_name,
                            world_fed,
                            f'World ({sex})',
                            ranking[0],
                            ranking[1],
                            ranking[2] if len(ranking) > 2 else 0,
                country_id
                        ))
                        inserted += 1
                    except:
                        continue

        # Handle martial arts disciplines
        if 'disciplines' in sport_data:
            for discipline, disc_data in sport_data['disciplines'].items():
                for i, country in enumerate(disc_data.get('top_countries', [])):
                    try:
                        cursor.execute(""",
                            INSERT INTO sofia.sports_regional (sport, world_federation, region, country_code, country_name, ranking, country_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (sport, region, country_code)
                            DO UPDATE SET ranking = EXCLUDED.ranking
                        """, (
                            discipline,
                            disc_data.get('federation', ''),
                            'World',
                            country[0],
                            country[1],
                            i + 1,
                country_id
                        ))
                        inserted += 1
                    except:
                        continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("=" * 80)
    print("REGIONAL SPORTS DATA COLLECTOR")
    print("=" * 80)
    print("")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    print("Sports covered:")
    for sport_key in REGIONAL_SPORTS_DATA.keys():
        print(f"  - {REGIONAL_SPORTS_DATA[sport_key].get('sport', sport_key)}")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Database connected")
        print("")
    except Exception as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)

    print("Saving regional sports data...")
    total_records = save_to_database(conn)

    conn.close()

    print("")
    print("=" * 80)
    print("REGIONAL SPORTS DATA COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total records: {total_records}")
    print("")
    print("Sports with regional data:")
    print("  - Football (UEFA, CONMEBOL, CONCACAF, AFC, CAF, OFC)")
    print("  - Cricket (ICC - Asia, UK, Oceania, Caribbean, Africa)")
    print("  - Basketball (FIBA - Europe, Asia, Americas)")
    print("  - Volleyball (FIVB - Europe, Asia, South America)")
    print("  - Rugby (World Rugby - Europe, Southern Hemisphere)")
    print("  - Swimming (World Aquatics)")
    print("  - Tennis (ITF - Grand Slam regions)")
    print("  - Cycling (UCI - European dominance)")
    print("  - Table Tennis (ITTF - Asian dominance)")
    print("  - Badminton (BWF - Asian dominance)")
    print("  - Handball (IHF - European dominance)")
    print("  - Hockey (FIH - Europe, Asia, Oceania)")
    print("  - Winter Sports (FIS - Alpine, Scandinavia)")
    print("  - Martial Arts (Judo, Taekwondo, Wrestling, Boxing, Karate)")
    print("  - Motorsports (FIA - F1, NASCAR, WRC)")
    print("  - Golf (IGF - Regional tours)")
    print("  - E-Sports (Emerging - Asia, Europe, Americas)")
    print("")
    print("Table created: sofia.sports_regional")


if __name__ == '__main__':
    main()
