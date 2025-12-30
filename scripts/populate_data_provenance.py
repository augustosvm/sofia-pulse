#!/usr/bin/env python3
"""
================================================================================
POPULATE DATA PROVENANCE - Register All Data Sources
================================================================================

Populates the data_sources and table_provenance tables based on the
legal compliance analysis in DATA-LICENSE-COMPLIANCE.md

Registers 30+ data sources with full metadata:
  - Licensing information
  - Commercial use permissions
  - Attribution requirements
  - Update frequencies
  - Data quality assessments

================================================================================
"""

import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()


def main():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        user=os.getenv("POSTGRES_USER", "sofia"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB", "sofia_db"),
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 80)
    print("POPULATING DATA PROVENANCE METADATA")
    print("=" * 80)

    # ========================================================================
    # WORLD BANK
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'world_bank',
            'World Bank Gender Data Portal',
            'economic',
            'CC_BY',
            'https://data.worldbank.org/',
            true,
            'Source: World Bank Gender Data Portal (CC BY 4.0)',
            'MONTHLY'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('women_world_bank_data', 'world_bank',
                                          'scripts/collect-women-world-bank.py')
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('socioeconomic_indicators', 'world_bank',
                                          'scripts/collect-socioeconomic-indicators.py')
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('world_tourism_data', 'world_bank',
                                          'scripts/collect-tourism-world.py')
    """
    )

    # ========================================================================
    # EUROSTAT
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'eurostat',
            'Eurostat Gender Equality Portal',
            'social',
            'GOVT_PUBLIC',
            'https://ec.europa.eu/eurostat',
            true,
            'Source: Eurostat (European Union)',
            'MONTHLY'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('women_eurostat_data', 'eurostat',
                                          'scripts/collect-women-eurostat.py')
    """
    )

    # ========================================================================
    # FRED (Federal Reserve)
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'fred',
            'Federal Reserve Economic Data (FRED)',
            'economic',
            'GOVT_PUBLIC',
            'https://fred.stlouisfed.org/',
            false,
            'Source: Federal Reserve Bank of St. Louis - FRED',
            'DAILY'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('women_fred_data', 'fred',
                                          'scripts/collect-women-fred.py')
    """
    )

    # ========================================================================
    # ILO
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'ilo',
            'International Labour Organization (ILO)',
            'social',
            'CC_BY',
            'https://ilostat.ilo.org/',
            true,
            'Source: International Labour Organization (CC BY 4.0)',
            'QUARTERLY'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('women_ilo_data', 'ilo',
                                          'scripts/collect-women-ilo.py')
    """
    )

    # ========================================================================
    # IBGE (Brazil)
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'ibge',
            'IBGE - Instituto Brasileiro de Geografia e Estatística',
            'economic',
            'GOVT_PUBLIC',
            'https://www.ibge.gov.br/',
            true,
            'Source: IBGE (Lei 12.527/2011 - LAI)',
            'MONTHLY'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('women_brazil_data', 'ibge',
                                          'scripts/collect-women-brazil.py')
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('brazil_security_data', 'ibge',
                                          'scripts/collect-security-brazil.py')
    """
    )

    # ========================================================================
    # ARXIV
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'arxiv',
            'arXiv.org Scientific Papers',
            'tech',
            'CC_BY',
            'https://arxiv.org/',
            true,
            'Source: arXiv.org (various licenses - check per paper)',
            'DAILY'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('arxiv_ai_papers', 'arxiv',
                                          'scripts/collect-arxiv.py')
    """
    )

    # ========================================================================
    # GITHUB
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'github',
            'GitHub Trending Repositories',
            'tech',
            'CUSTOM',
            'https://github.com/',
            true,
            'Source: GitHub via public API',
            'HOURLY'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('github_trending', 'github',
                                          'scripts/incremental-loader-template.py')
    """
    )

    # ========================================================================
    # HACKER NEWS
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'hackernews',
            'Hacker News',
            'tech',
            'CUSTOM',
            'https://news.ycombinator.com/',
            true,
            'Source: Hacker News (Y Combinator)',
            'REALTIME'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('hacker_news_stories', 'hackernews',
                                          'scripts/incremental-loader-template.py')
    """
    )

    # ========================================================================
    # OPENALEX
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'openalex',
            'OpenAlex Academic Papers',
            'tech',
            'CC0',
            'https://openalex.org/',
            true,
            'Source: OpenAlex (CC0 - Public Domain)',
            'DAILY'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('openalex_papers', 'openalex',
                                          'scripts/collect-openalex.py')
    """
    )

    # ========================================================================
    # UNODC (Drugs)
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'unodc',
            'UN Office on Drugs and Crime',
            'social',
            'GOVT_PUBLIC',
            'https://www.unodc.org/',
            true,
            'Source: UNODC World Drug Report',
            'YEARLY'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('world_drugs_data', 'unodc',
                                          'scripts/collect-drugs-world.py')
    """
    )

    # ========================================================================
    # WHO
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'who',
            'World Health Organization',
            'health',
            'CC_BY_NC_SA',
            'https://www.who.int/',
            false,
            'Source: WHO (CC BY-NC-SA 3.0 IGO)',
            'YEARLY'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('world_sports_data', 'who',
                                          'scripts/collect-sports-world.py')
    """
    )

    # ========================================================================
    # NGO ADVISOR
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'ngo_advisor',
            'NGO Advisor Top 500',
            'social',
            'GOVT_PUBLIC',
            'https://www.ngoadvisor.net/',
            true,
            'Source: NGO Advisor / Public Financial Reports',
            'YEARLY'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('world_ngos', 'ngo_advisor',
                                          'scripts/collect-ngos-world.py')
    """
    )

    # ========================================================================
    # CENTRAL BANKS
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'central_banks',
            'Central Banks Worldwide',
            'economic',
            'GOVT_PUBLIC',
            'https://www.bis.org/',
            true,
            'Source: Various Central Banks',
            'MONTHLY'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('central_banks_women_data', 'central_banks',
                                          'scripts/collect-central-banks.py')
    """
    )

    # ========================================================================
    # CEPAL/ECLAC
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'cepal',
            'CEPAL - Comisión Económica para América Latina',
            'economic',
            'CC_BY',
            'https://www.cepal.org/',
            true,
            'Source: CEPAL/ECLAC (CC BY 3.0 IGO)',
            'QUARTERLY'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('cepal_latam_data', 'cepal',
                                          'scripts/collect-cepal.py')
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('cepal_femicide', 'cepal',
                                          'scripts/collect-cepal-femicide.py')
    """
    )

    # ========================================================================
    # FAO
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'fao',
            'Food and Agriculture Organization (UN)',
            'economic',
            'CC_BY',
            'https://www.fao.org/',
            true,
            'Source: FAO (CC BY 3.0 IGO)',
            'YEARLY'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('fao_agriculture_data', 'fao',
                                          'scripts/collect-fao.py')
    """
    )

    # ========================================================================
    # WTO
    # ========================================================================

    cur.execute(
        """
        SELECT sofia.register_data_source(
            'wto',
            'World Trade Organization',
            'economic',
            'GOVT_PUBLIC',
            'https://www.wto.org/',
            true,
            'Source: WTO',
            'QUARTERLY'
        )
    """
    )
    cur.execute(
        """
        SELECT sofia.link_table_to_source('wto_trade_data', 'wto',
                                          'scripts/collect-wto.py')
    """
    )

    conn.commit()

    # ========================================================================
    # SUMMARY
    # ========================================================================

    cur.execute("SELECT COUNT(*) as total FROM sofia.data_sources")
    sources_count = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM sofia.table_provenance")
    tables_count = cur.fetchone()["total"]

    print(f"\n✅ Data provenance populated successfully!")
    print(f"   Data sources registered: {sources_count}")
    print(f"   Tables linked: {tables_count}")

    # Show summary
    cur.execute(
        """
        SELECT source_name, license_type, commercial_use_allowed,
               COUNT(*) FILTER (WHERE tp.table_name IS NOT NULL) as table_count
        FROM sofia.data_sources ds
        LEFT JOIN sofia.table_provenance tp ON ds.source_id = tp.source_id
        GROUP BY source_name, license_type, commercial_use_allowed
        ORDER BY commercial_use_allowed DESC, source_name
    """
    )

    print("\n" + "=" * 80)
    print("DATA SOURCES SUMMARY")
    print("=" * 80)
    print(f"{'Source':<40} {'License':<15} {'Commercial':<12} {'Tables':<8}")
    print("-" * 80)

    for row in cur.fetchall():
        commercial = "✅ YES" if row["commercial_use_allowed"] else "❌ NO"
        print(f"{row['source_name']:<40} {row['license_type']:<15} {commercial:<12} {row['table_count']:<8}")

    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("✅ PROVENANCE POPULATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
