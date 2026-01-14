#!/usr/bin/env python3
"""
Brazil Economy Intelligence Report
===================================
Comprehensive Brazilian economic data from multiple official sources:
- BACEN (Central Bank) - Selic, IPCA, exchange rates
- IBGE - GDP, inflation, employment
- IPEA - Economic research series
- CNI - Industrial indicators
- FIESP - Sao Paulo industrial activity
- ComexStat - Trade data (imports/exports)
- B3 - Stock market data

Actionable insights for:
- Investment decisions in Brazil
- Market entry/expansion strategy
- Economic trend analysis
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
        "BRAZIL ECONOMY INTELLIGENCE REPORT",
        "=" * 80,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "Sources: BACEN, IBGE, IPEA, CNI, FIESP, ComexStat, B3",
        ""
    ]

    # =========================================================================
    # 1. BACEN - Central Bank Key Indicators
    # =========================================================================
    r.extend(["=" * 80, "1. BACEN - CENTRAL BANK KEY INDICATORS", "=" * 80, ""])

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.bacen_sgs_series")
        count = cur.fetchone()[0]
        r.append(f"Total BACEN series records: {count:,}")
        r.append("")

        if count > 0:
            # Key rates by category
            cur.execute("""
                SELECT DISTINCT ON (series_name)
                    series_name, value, date, unit
                FROM sofia.bacen_sgs_series
                WHERE value IS NOT NULL
                ORDER BY series_name, date DESC
                LIMIT 15
            """)
            rows = cur.fetchall()

            if rows:
                r.append("LATEST KEY INDICATORS:")
                r.append("-" * 70)

                for name, value, date, unit in rows:
                    name_short = name[:45] if name else "N/A"
                    unit_str = f" {unit}" if unit else ""
                    r.append(f"  {name_short}: {float(value):,.2f}{unit_str} ({date})")

                r.append("")

            # Selic history (if available)
            cur.execute("""
                SELECT date, value
                FROM sofia.bacen_sgs_series
                WHERE series_name ILIKE '%selic%' AND value IS NOT NULL
                ORDER BY date DESC
                LIMIT 6
            """)
            rows = cur.fetchall()

            if rows:
                r.append("SELIC RATE TREND:")
                r.append("-" * 40)
                for date, value in rows:
                    r.append(f"  {date}: {float(value):.2f}%")
                r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 2. IPEA - Economic Research Series
    # =========================================================================
    r.extend(["=" * 80, "2. IPEA - ECONOMIC RESEARCH DATA", "=" * 80, ""])

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.ipea_series")
        count = cur.fetchone()[0]
        r.append(f"Total IPEA series records: {count:,}")
        r.append("")

        if count > 0:
            # Categories available
            cur.execute("""
                SELECT category, COUNT(*) as cnt
                FROM sofia.ipea_series
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY cnt DESC
                LIMIT 10
            """)
            rows = cur.fetchall()

            if rows:
                r.append("CATEGORIES TRACKED:")
                r.append("-" * 40)
                for cat, cnt in rows:
                    r.append(f"  {cat}: {cnt} records")
                r.append("")

            # Latest values by series
            cur.execute("""
                SELECT DISTINCT ON (series_name)
                    series_name, value, date, category
                FROM sofia.ipea_series
                WHERE value IS NOT NULL
                ORDER BY series_name, date DESC
                LIMIT 10
            """)
            rows = cur.fetchall()

            if rows:
                r.append("LATEST IPEA INDICATORS:")
                r.append("-" * 70)
                for name, value, date, cat in rows:
                    name_short = name[:40] if name else "N/A"
                    cat_str = f" [{cat[:15]}]" if cat else ""
                    r.append(f"  {name_short}: {float(value):,.2f}{cat_str} ({date})")
                r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 3. FIESP - Sao Paulo Industrial Activity
    # =========================================================================
    r.extend(["=" * 80, "3. FIESP - SAO PAULO INDUSTRIAL ACTIVITY", "=" * 80, ""])

    try:
        # INA - Industrial Activity Index
        cur.execute("SELECT COUNT(*) FROM sofia.fiesp_ina")
        count_ina = cur.fetchone()[0]

        # Sensor - Business Sentiment
        cur.execute("SELECT COUNT(*) FROM sofia.fiesp_sensor")
        count_sensor = cur.fetchone()[0]

        r.append(f"INA (Activity Index) records: {count_ina:,}")
        r.append(f"Sensor (Sentiment) records: {count_sensor:,}")
        r.append("")

        if count_ina > 0:
            cur.execute("""
                SELECT period, general_activity_index, real_sales,
                       capacity_utilization, hours_worked
                FROM sofia.fiesp_ina
                ORDER BY period DESC
                LIMIT 6
            """)
            rows = cur.fetchall()

            if rows:
                r.append("INDUSTRIAL ACTIVITY INDEX (INA) - LATEST:")
                r.append("-" * 70)
                r.append(f"{'Period':<10} {'Activity':>10} {'Sales':>10} {'Capacity':>10} {'Hours':>10}")
                r.append("-" * 70)

                for period, activity, sales, capacity, hours in rows:
                    act = f"{float(activity):.1f}" if activity else "N/A"
                    sal = f"{float(sales):.1f}" if sales else "N/A"
                    cap = f"{float(capacity):.1f}%" if capacity else "N/A"
                    hrs = f"{float(hours):.1f}" if hours else "N/A"
                    r.append(f"{str(period):<10} {act:>10} {sal:>10} {cap:>10} {hrs:>10}")

                r.append("")

        if count_sensor > 0:
            cur.execute("""
                SELECT period, market_conditions, sales_expectations,
                       inventory_levels, investment_intention
                FROM sofia.fiesp_sensor
                ORDER BY period DESC
                LIMIT 6
            """)
            rows = cur.fetchall()

            if rows:
                r.append("BUSINESS SENTIMENT (SENSOR) - LATEST:")
                r.append("-" * 70)
                r.append(f"{'Period':<10} {'Market':>12} {'Sales Exp':>12} {'Inventory':>12} {'Investment':>12}")
                r.append("-" * 70)

                for period, market, sales, inv, invest in rows:
                    mkt = f"{float(market):.1f}" if market else "N/A"
                    sal = f"{float(sales):.1f}" if sales else "N/A"
                    inventory = f"{float(inv):.1f}" if inv else "N/A"
                    inv_int = f"{float(invest):.1f}" if invest else "N/A"
                    r.append(f"{str(period):<10} {mkt:>12} {sal:>12} {inventory:>12} {inv_int:>12}")

                r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 4. CNI - Industrial Indicators
    # =========================================================================
    r.extend(["=" * 80, "4. CNI - INDUSTRIAL INDICATORS", "=" * 80, ""])

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.cni_industrial_indicators")
        count = cur.fetchone()[0]
        r.append(f"CNI indicators: {count:,}")
        r.append("")

        if count > 0:
            cur.execute("""
                SELECT indicator_title, value_numeric, period_description
                FROM sofia.cni_industrial_indicators
                WHERE value_numeric IS NOT NULL
                ORDER BY collected_at DESC
                LIMIT 12
            """)
            rows = cur.fetchall()

            if rows:
                r.append("LATEST CNI INDICATORS:")
                r.append("-" * 70)
                for title, value, period in rows:
                    title_short = title[:45] if title else "N/A"
                    period_str = f" ({period})" if period else ""
                    r.append(f"  {title_short}: {float(value):.2f}{period_str}")
                r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 5. COMEXSTAT - Trade Data
    # =========================================================================
    r.extend(["=" * 80, "5. COMEXSTAT - BRAZIL TRADE DATA", "=" * 80, ""])

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.comexstat_trade")
        count = cur.fetchone()[0]
        r.append(f"Trade records: {count:,}")
        r.append("")

        if count > 0:
            # Top trading partners
            cur.execute("""
                SELECT country_name, flow, COUNT(*) as transactions,
                       SUM(COALESCE(value_usd, 0)) as total_value
                FROM sofia.comexstat_trade
                WHERE country_name IS NOT NULL
                GROUP BY country_name, flow
                ORDER BY total_value DESC
                LIMIT 15
            """)
            rows = cur.fetchall()

            if rows:
                r.append("TOP TRADING PARTNERS:")
                r.append("-" * 60)
                for country, flow, trans, value in rows:
                    flow_str = "EXP" if flow and 'exp' in flow.lower() else "IMP"
                    value_str = f"${float(value):,.0f}" if value else "N/A"
                    r.append(f"  {country[:25]:<25} [{flow_str}]: {trans:>5} trans, {value_str}")
                r.append("")

            # Top products
            cur.execute("""
                SELECT ncm_description, flow, COUNT(*) as cnt
                FROM sofia.comexstat_trade
                WHERE ncm_description IS NOT NULL
                GROUP BY ncm_description, flow
                ORDER BY cnt DESC
                LIMIT 10
            """)
            rows = cur.fetchall()

            if rows:
                r.append("TOP TRADED PRODUCTS:")
                r.append("-" * 70)
                for product, flow, cnt in rows:
                    product_short = product[:50] if product else "N/A"
                    flow_str = "EXP" if flow and 'exp' in flow.lower() else "IMP"
                    r.append(f"  [{flow_str}] {product_short}: {cnt} records")
                r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 6. B3 - Stock Market
    # =========================================================================
    r.extend(["=" * 80, "6. B3 - BRAZILIAN STOCK MARKET", "=" * 80, ""])

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.market_data_brazil")
        count = cur.fetchone()[0]
        r.append(f"Stocks tracked: {count:,}")
        r.append("")

        if count > 0:
            # Top gainers (deduplicated by ticker)
            cur.execute("""
                SELECT ticker, company, sector, price, change_pct, volume
                FROM (
                    SELECT DISTINCT ON (ticker)
                        ticker, company, sector, price, change_pct, volume
                    FROM sofia.market_data_brazil
                    WHERE change_pct IS NOT NULL
                    ORDER BY ticker, collected_at DESC NULLS LAST
                ) latest
                ORDER BY change_pct DESC
                LIMIT 10
            """)
            rows = cur.fetchall()

            if rows:
                r.append("TOP GAINERS:")
                r.append("-" * 70)
                for ticker, company, sector, price, change, volume in rows:
                    company_short = company[:25] if company else "N/A"
                    price_str = f"R${float(price):.2f}" if price else "N/A"
                    change_str = f"+{float(change):.1f}%" if change else "N/A"
                    r.append(f"  {ticker:<8} {company_short:<25} {price_str:>12} {change_str:>8}")
                r.append("")

            # Top losers (deduplicated by ticker)
            cur.execute("""
                SELECT ticker, company, sector, price, change_pct
                FROM (
                    SELECT DISTINCT ON (ticker)
                        ticker, company, sector, price, change_pct
                    FROM sofia.market_data_brazil
                    WHERE change_pct IS NOT NULL
                    ORDER BY ticker, collected_at DESC NULLS LAST
                ) latest
                ORDER BY change_pct ASC
                LIMIT 5
            """)
            rows = cur.fetchall()

            if rows:
                r.append("TOP LOSERS:")
                r.append("-" * 70)
                for ticker, company, sector, price, change in rows:
                    company_short = company[:25] if company else "N/A"
                    price_str = f"R${float(price):.2f}" if price else "N/A"
                    change_str = f"{float(change):.1f}%" if change else "N/A"
                    r.append(f"  {ticker:<8} {company_short:<25} {price_str:>12} {change_str:>8}")
                r.append("")

            # By sector (using deduplicated data)
            cur.execute("""
                SELECT sector, COUNT(*) as stocks, AVG(change_pct) as avg_change
                FROM (
                    SELECT DISTINCT ON (ticker)
                        ticker, sector, change_pct
                    FROM sofia.market_data_brazil
                    WHERE sector IS NOT NULL AND change_pct IS NOT NULL
                    ORDER BY ticker, collected_at DESC NULLS LAST
                ) latest
                GROUP BY sector
                ORDER BY avg_change DESC
                LIMIT 10
            """)
            rows = cur.fetchall()

            if rows:
                r.append("PERFORMANCE BY SECTOR:")
                r.append("-" * 50)
                for sector, stocks, avg_change in rows:
                    sector_short = sector[:30] if sector else "N/A"
                    change_str = f"{float(avg_change):+.1f}%" if avg_change else "N/A"
                    r.append(f"  {sector_short:<30} ({stocks} stocks): {change_str}")
                r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 7. Security Data
    # =========================================================================
    r.extend(["=" * 80, "7. BRAZIL SECURITY DATA", "=" * 80, ""])

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.brazil_security_data")
        count = cur.fetchone()[0]
        r.append(f"Security records: {count:,}")
        r.append("")

        if count > 0:
            cur.execute("""
                SELECT indicator, region_name, year, value
                FROM sofia.brazil_security_data
                WHERE value IS NOT NULL AND region_type = 'state'
                ORDER BY year DESC, value DESC
                LIMIT 15
            """)
            rows = cur.fetchall()

            if rows:
                r.append("SECURITY INDICATORS BY STATE:")
                r.append("-" * 60)
                current_indicator = None
                for indicator, region, year, value in rows:
                    if indicator != current_indicator:
                        r.append(f"\n  {indicator}:")
                        current_indicator = indicator
                    r.append(f"    {region}: {float(value):,.1f} ({year})")
                r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 8. STRATEGIC INSIGHTS
    # =========================================================================
    r.extend(["=" * 80, "8. STRATEGIC INSIGHTS FOR BRAZIL", "=" * 80, ""])

    r.append("")
    r.append("INVESTMENT CLIMATE:")
    r.append("-" * 50)
    r.append("  - Monitor SELIC rate for borrowing cost trends")
    r.append("  - IPCA inflation affects consumer purchasing power")
    r.append("  - Industrial activity (FIESP INA) signals manufacturing health")
    r.append("  - Business sentiment (FIESP Sensor) predicts near-term outlook")
    r.append("")

    r.append("MARKET ENTRY CONSIDERATIONS:")
    r.append("-" * 50)
    r.append("  - Sao Paulo: Largest industrial base, track FIESP data")
    r.append("  - Trade partners: Use ComexStat for supply chain analysis")
    r.append("  - Security: Consider regional security data for operations")
    r.append("  - B3 sectors: Identify growing industries for investment")
    r.append("")

    r.append("KEY DATA SOURCES:")
    r.append("-" * 50)
    r.append("  - BACEN SGS: api.bcb.gov.br (official central bank)")
    r.append("  - IBGE: servicodados.ibge.gov.br (official statistics)")
    r.append("  - IPEA: ipeadata.gov.br (economic research)")
    r.append("  - FIESP: fiesp.com.br (Sao Paulo industry)")
    r.append("  - CNI: portaldaindustria.com.br (national industry)")
    r.append("  - ComexStat: comexstat.mdic.gov.br (trade)")
    r.append("")

    # Save report
    cur.close()
    conn.close()

    text = "\n".join(r)
    print(text)

    output_path = "analytics/basedosdados-intelligence.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"\n{'=' * 80}")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    main()
