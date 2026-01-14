#!/usr/bin/env python3
"""
================================================================================
BRAZIL ECONOMY INTELLIGENCE - Executive Dashboard
================================================================================
Clear, actionable insights on Brazil's economy for:
- Investment decisions
- Market entry strategy
- Currency/trade planning
- Tech sector opportunities

Sources: BACEN, IBGE, IPEA, ComexStat, Ministries
================================================================================
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

def format_trend(current, previous):
    """Return trend arrow and percentage change"""
    if not current or not previous or previous == 0:
        return ""
    change = ((current - previous) / abs(previous)) * 100
    if change > 0.5:
        return f" [+{change:.1f}%]"
    elif change < -0.5:
        return f" [{change:.1f}%]"
    return " [stable]"

def main():
    conn = get_connection()
    cur = conn.cursor()

    r = []
    r.append("=" * 80)
    r.append("BRAZIL ECONOMY INTELLIGENCE - EXECUTIVE DASHBOARD")
    r.append("=" * 80)
    r.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    r.append("Sources: BACEN, IBGE, IPEA, ComexStat, Ministries")
    r.append("")

    # Store key metrics for insights
    metrics = {}

    # =========================================================================
    # 1. ECONOMIC SNAPSHOT - Key Indicators at a Glance
    # =========================================================================
    r.append("=" * 80)
    r.append("1. ECONOMIC SNAPSHOT - KEY INDICATORS")
    r.append("=" * 80)
    r.append("")

    try:
        # Get latest SELIC
        cur.execute("""
            SELECT value, date FROM sofia.bacen_sgs_series
            WHERE series_name ILIKE '%selic%' AND value IS NOT NULL
            ORDER BY date DESC LIMIT 1
        """)
        row = cur.fetchone()
        selic = row[0] if row else None
        selic_date = row[1] if row else None
        metrics['selic'] = selic

        # Get previous SELIC (30 days ago)
        cur.execute("""
            SELECT value FROM sofia.bacen_sgs_series
            WHERE series_name ILIKE '%selic%' AND value IS NOT NULL
            ORDER BY date DESC OFFSET 30 LIMIT 1
        """)
        row = cur.fetchone()
        selic_prev = row[0] if row else None

        # Get latest USD/BRL
        cur.execute("""
            SELECT value, date FROM sofia.bacen_sgs_series
            WHERE series_name ILIKE '%dolar%' OR series_name ILIKE '%cambio%'
            ORDER BY date DESC LIMIT 1
        """)
        row = cur.fetchone()
        usd_brl = row[0] if row else None
        usd_date = row[1] if row else None
        metrics['usd_brl'] = usd_brl

        # Get previous USD/BRL
        cur.execute("""
            SELECT value FROM sofia.bacen_sgs_series
            WHERE series_name ILIKE '%dolar%' OR series_name ILIKE '%cambio%'
            ORDER BY date DESC OFFSET 30 LIMIT 1
        """)
        row = cur.fetchone()
        usd_prev = row[0] if row else None

        # Get latest IPCA (inflation)
        cur.execute("""
            SELECT value, date FROM sofia.bacen_sgs_series
            WHERE series_name ILIKE '%ipca%' AND value IS NOT NULL
            ORDER BY date DESC LIMIT 1
        """)
        row = cur.fetchone()
        ipca = row[0] if row else None
        ipca_date = row[1] if row else None
        metrics['ipca'] = ipca

        # Get unemployment from IPEA
        cur.execute("""
            SELECT value, date FROM sofia.ipea_series
            WHERE series_name ILIKE '%desocupa%' OR series_name ILIKE '%desemprego%'
            ORDER BY date DESC LIMIT 1
        """)
        row = cur.fetchone()
        unemployment = row[0] if row else None
        unemp_date = row[1] if row else None
        metrics['unemployment'] = unemployment

        # Display Economic Snapshot
        r.append("MONETARY POLICY:")
        r.append("-" * 40)
        if selic:
            trend = format_trend(selic, selic_prev)
            r.append(f"  SELIC (Interest Rate):    {selic:.2f}%{trend}")
            r.append(f"                            As of {selic_date}")

        if usd_brl:
            trend = format_trend(usd_brl, usd_prev)
            r.append(f"  USD/BRL (Exchange Rate):  R$ {usd_brl:.4f}{trend}")
            r.append(f"                            As of {usd_date}")
        r.append("")

        r.append("INFLATION & EMPLOYMENT:")
        r.append("-" * 40)
        if ipca:
            r.append(f"  IPCA (Monthly Inflation): {ipca:.2f}%")
            r.append(f"                            As of {ipca_date}")

        if unemployment:
            r.append(f"  Unemployment Rate:        {unemployment:.1f}%")
            r.append(f"                            As of {unemp_date}")
        r.append("")

        # Interpretation
        r.append("INTERPRETATION:")
        r.append("-" * 40)

        if selic and selic >= 13:
            r.append("  * HIGH SELIC: Restrictive monetary policy")
            r.append("    - Borrowing costs elevated for businesses")
            r.append("    - Fixed income investments more attractive")
            r.append("    - Startup funding environment challenging")
        elif selic and selic < 10:
            r.append("  * LOW SELIC: Expansionary monetary policy")
            r.append("    - Favorable borrowing conditions")
            r.append("    - Equity investments more attractive")

        if usd_brl and usd_brl > 5.0:
            r.append("  * WEAK BRL: Currency depreciated vs USD")
            r.append("    - Good for exporters and USD earners")
            r.append("    - Import costs elevated")
            r.append("    - Tech workers earning in USD benefit")

        r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error loading snapshot: {e}")
        r.append("")

    # =========================================================================
    # 2. SELIC RATE HISTORY - Trend Analysis
    # =========================================================================
    r.append("=" * 80)
    r.append("2. SELIC RATE HISTORY (Last 6 Months)")
    r.append("=" * 80)
    r.append("")

    try:
        cur.execute("""
            SELECT DISTINCT ON (DATE_TRUNC('month', date))
                DATE_TRUNC('month', date) as month, value
            FROM sofia.bacen_sgs_series
            WHERE series_name ILIKE '%selic%' AND value IS NOT NULL
            ORDER BY DATE_TRUNC('month', date) DESC
            LIMIT 6
        """)
        rows = cur.fetchall()

        if rows:
            r.append(f"{'Month':<15} {'Rate':>10}   Visualization")
            r.append("-" * 60)

            max_val = max(r[1] for r in rows) if rows else 15
            for month, value in rows:
                month_str = month.strftime('%Y-%m') if month else "N/A"
                bar_len = int((value / max_val) * 30) if max_val > 0 else 0
                bar = "#" * bar_len
                r.append(f"{month_str:<15} {value:>10.2f}%  {bar}")

            r.append("")

            # Trend analysis
            if len(rows) >= 2:
                latest = float(rows[0][1]) if rows[0][1] else 0
                oldest = float(rows[-1][1]) if rows[-1][1] else 0
                if latest > oldest + 0.5:
                    r.append("TREND: RISING - Central Bank tightening policy")
                elif latest < oldest - 0.5:
                    r.append("TREND: FALLING - Central Bank easing policy")
                else:
                    r.append("TREND: STABLE - Policy rate maintained")
            r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 3. INFLATION TRACKER
    # =========================================================================
    r.append("=" * 80)
    r.append("3. INFLATION TRACKER (IPCA)")
    r.append("=" * 80)
    r.append("")

    try:
        # Monthly IPCA from BACEN or IPEA
        cur.execute("""
            SELECT DISTINCT ON (DATE_TRUNC('month', date))
                DATE_TRUNC('month', date) as month, value
            FROM sofia.ipea_series
            WHERE series_name ILIKE '%ipc%' AND category = 'inflation'
            ORDER BY DATE_TRUNC('month', date) DESC
            LIMIT 12
        """)
        rows = cur.fetchall()

        if rows:
            r.append("MONTHLY INFLATION (%):")
            r.append("-" * 60)
            r.append(f"{'Month':<12} {'Rate':>8}   Bar")
            r.append("-" * 60)

            for month, value in rows[:6]:
                month_str = month.strftime('%Y-%m') if month else "N/A"
                # Visual bar (scaled for small percentages)
                bar_len = int(abs(value) * 20) if value else 0
                bar = "+" * bar_len if value > 0 else "-" * bar_len
                sign = "+" if value > 0 else ""
                r.append(f"{month_str:<12} {sign}{value:>7.2f}%  {bar}")

            r.append("")

            # Calculate 12-month accumulated
            if len(rows) >= 12:
                accumulated = sum(r[1] for r in rows if r[1])
                r.append(f"12-MONTH ACCUMULATED INFLATION: {accumulated:.2f}%")

                if accumulated > 6:
                    r.append("  * Above target ceiling (6.5%) - Pressure on Central Bank")
                elif accumulated < 3:
                    r.append("  * Below target floor (3%) - Deflationary concerns")
                else:
                    r.append("  * Within target range (3-6.5%) - Inflation controlled")
            r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 4. LABOR MARKET
    # =========================================================================
    r.append("=" * 80)
    r.append("4. LABOR MARKET INDICATORS")
    r.append("=" * 80)
    r.append("")

    try:
        # Unemployment trend
        cur.execute("""
            SELECT DISTINCT ON (DATE_TRUNC('month', date))
                DATE_TRUNC('month', date) as month, value
            FROM sofia.ipea_series
            WHERE (series_name ILIKE '%desocupa%' OR series_name ILIKE '%desemprego%')
              AND category = 'employment'
            ORDER BY DATE_TRUNC('month', date) DESC
            LIMIT 6
        """)
        unemployment_rows = cur.fetchall()

        # Income trend
        cur.execute("""
            SELECT DISTINCT ON (DATE_TRUNC('month', date))
                DATE_TRUNC('month', date) as month, value
            FROM sofia.ipea_series
            WHERE series_name ILIKE '%rendimento%' AND category = 'income'
            ORDER BY DATE_TRUNC('month', date) DESC
            LIMIT 6
        """)
        income_rows = cur.fetchall()

        if unemployment_rows:
            r.append("UNEMPLOYMENT RATE TREND:")
            r.append("-" * 40)
            for month, value in unemployment_rows:
                month_str = month.strftime('%Y-%m') if month else "N/A"
                bar_len = int(value * 3) if value else 0
                bar = "#" * bar_len
                r.append(f"  {month_str}: {value:>5.1f}% {bar}")

            # Analysis
            if len(unemployment_rows) >= 2:
                latest = unemployment_rows[0][1]
                prev = unemployment_rows[1][1]
                if latest < prev:
                    r.append("")
                    r.append("  TREND: Improving - unemployment falling")
                elif latest > prev:
                    r.append("")
                    r.append("  TREND: Weakening - unemployment rising")
            r.append("")

        if income_rows:
            r.append("AVERAGE REAL INCOME (R$):")
            r.append("-" * 40)
            for month, value in income_rows:
                month_str = month.strftime('%Y-%m') if month else "N/A"
                r.append(f"  {month_str}: R$ {value:,.0f}")
            r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 5. FOREIGN TRADE OVERVIEW
    # =========================================================================
    r.append("=" * 80)
    r.append("5. FOREIGN TRADE - TOP PARTNERS & PRODUCTS")
    r.append("=" * 80)
    r.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.comexstat_trade")
        count = cur.fetchone()[0]

        if count > 0:
            # Top export destinations
            cur.execute("""
                SELECT country_name, SUM(value_usd) as total, COUNT(*) as transactions
                FROM sofia.comexstat_trade
                WHERE LOWER(flow) LIKE '%exp%' AND country_name IS NOT NULL
                GROUP BY country_name
                ORDER BY total DESC
                LIMIT 8
            """)
            export_countries = cur.fetchall()

            # Top import origins
            cur.execute("""
                SELECT country_name, SUM(value_usd) as total, COUNT(*) as transactions
                FROM sofia.comexstat_trade
                WHERE LOWER(flow) LIKE '%imp%' AND country_name IS NOT NULL
                GROUP BY country_name
                ORDER BY total DESC
                LIMIT 8
            """)
            import_countries = cur.fetchall()

            if export_countries:
                r.append("TOP EXPORT DESTINATIONS:")
                r.append("-" * 50)
                for country, total, trans in export_countries:
                    total_f = float(total) if total else 0
                    if total_f >= 1e9:
                        val_str = f"${total_f/1e9:.1f}B"
                    elif total_f >= 1e6:
                        val_str = f"${total_f/1e6:.1f}M"
                    else:
                        val_str = f"${total_f:,.0f}"
                    r.append(f"  {country:<25} {val_str:>12} ({trans} trans)")
                r.append("")

            if import_countries:
                r.append("TOP IMPORT ORIGINS:")
                r.append("-" * 50)
                for country, total, trans in import_countries:
                    total_f = float(total) if total else 0
                    if total_f >= 1e9:
                        val_str = f"${total_f/1e9:.1f}B"
                    elif total_f >= 1e6:
                        val_str = f"${total_f/1e6:.1f}M"
                    else:
                        val_str = f"${total_f:,.0f}"
                    r.append(f"  {country:<25} {val_str:>12} ({trans} trans)")
                r.append("")

            # Top products traded
            cur.execute("""
                SELECT ncm_description, flow, SUM(value_usd) as total
                FROM sofia.comexstat_trade
                WHERE ncm_description IS NOT NULL
                GROUP BY ncm_description, flow
                ORDER BY total DESC
                LIMIT 10
            """)
            products = cur.fetchall()

            if products:
                r.append("TOP TRADED PRODUCTS (Tech focus):")
                r.append("-" * 60)
                for product, flow, total in products:
                    flow_str = "EXP" if 'exp' in flow.lower() else "IMP"
                    product_short = product[:40] if product else "N/A"
                    total_f = float(total) if total else 0
                    if total_f >= 1e6:
                        val_str = f"${total_f/1e6:.1f}M"
                    else:
                        val_str = f"${total_f:,.0f}"
                    r.append(f"  [{flow_str}] {product_short:<40} {val_str:>10}")
                r.append("")

            # Trade balance insight
            cur.execute("""
                SELECT
                    SUM(CASE WHEN LOWER(flow) LIKE '%exp%' THEN value_usd ELSE 0 END) as exports,
                    SUM(CASE WHEN LOWER(flow) LIKE '%imp%' THEN value_usd ELSE 0 END) as imports
                FROM sofia.comexstat_trade
            """)
            row = cur.fetchone()
            if row and row[0] and row[1]:
                exports = float(row[0])
                imports = float(row[1])
                balance = exports - imports
                r.append("TRADE BALANCE (in dataset):")
                r.append("-" * 40)
                r.append(f"  Exports: ${exports/1e6:.1f}M")
                r.append(f"  Imports: ${imports/1e6:.1f}M")
                r.append(f"  Balance: ${balance/1e6:.1f}M {'(SURPLUS)' if balance > 0 else '(DEFICIT)'}")
                r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 6. AGRICULTURE & PRODUCTION
    # =========================================================================
    r.append("=" * 80)
    r.append("6. AGRICULTURE & PRODUCTION (Ministry Data)")
    r.append("=" * 80)
    r.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.brazil_ministries_data")
        count = cur.fetchone()[0]

        if count > 0:
            # Agriculture production value
            cur.execute("""
                SELECT period, value
                FROM sofia.brazil_ministries_data
                WHERE ministry = 'agricultura'
                  AND indicator ILIKE '%valor da produ%'
                  AND indicator NOT LIKE '%percent%'
                ORDER BY period DESC
                LIMIT 5
            """)
            production = cur.fetchall()

            if production:
                r.append("AGRICULTURAL PRODUCTION VALUE (R$ billions):")
                r.append("-" * 40)
                for period, value in production:
                    val_f = float(value) if value else 0
                    val_billions = val_f / 1e9
                    bar_len = int(val_billions / 30) if val_billions else 0
                    bar = "#" * bar_len
                    r.append(f"  {period}: R$ {val_billions:>6.1f}B {bar}")
                r.append("")

            # Planted area
            cur.execute("""
                SELECT period, value
                FROM sofia.brazil_ministries_data
                WHERE ministry = 'agricultura'
                  AND indicator ILIKE '%area plantada%'
                  AND indicator NOT LIKE '%percent%'
                ORDER BY period DESC
                LIMIT 5
            """)
            area = cur.fetchall()

            if area:
                r.append("PLANTED AREA (million hectares):")
                r.append("-" * 40)
                for period, value in area:
                    val_f = float(value) if value else 0
                    val_millions = val_f / 1e6
                    r.append(f"  {period}: {val_millions:>6.1f}M ha")
                r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 7. STRATEGIC INSIGHTS & RECOMMENDATIONS
    # =========================================================================
    r.append("=" * 80)
    r.append("7. STRATEGIC INSIGHTS & RECOMMENDATIONS")
    r.append("=" * 80)
    r.append("")

    r.append("FOR INVESTORS:")
    r.append("-" * 50)

    selic = metrics.get('selic')
    usd_brl = metrics.get('usd_brl')
    unemployment = metrics.get('unemployment')

    if selic:
        if selic >= 13:
            r.append("  * Fixed income attractive at current SELIC levels")
            r.append("  * VC/PE returns need to exceed ~15% to compete")
            r.append("  * Local debt financing expensive")
        else:
            r.append("  * Equity investments more competitive vs fixed income")
            r.append("  * Favorable environment for leveraged deals")

    if usd_brl:
        if usd_brl > 5.5:
            r.append("  * BRL significantly depreciated - consider hedging")
            r.append("  * USD-denominated revenue streams valuable")
        elif usd_brl < 4.5:
            r.append("  * BRL relatively strong - good for imports")
    r.append("")

    r.append("FOR TECH COMPANIES:")
    r.append("-" * 50)
    r.append("  * Remote workers earning USD benefit from weak BRL")
    r.append("  * Export tech services to maximize USD earnings")
    r.append("  * Import tech equipment costs elevated")
    r.append("  * Monitor FIESP/CNI for industrial demand signals")
    r.append("")

    r.append("FOR EXPORTERS:")
    r.append("-" * 50)
    r.append("  * China remains dominant trade partner (imports)")
    r.append("  * US/Chile key export markets")
    r.append("  * Tech products (IoT, monitors, servers) dominate imports")
    r.append("  * Diversify export destinations beyond traditional partners")
    r.append("")

    r.append("KEY MONITORING POINTS:")
    r.append("-" * 50)
    r.append("  * COPOM meetings (every 45 days) - SELIC decisions")
    r.append("  * IBGE releases - GDP, employment, inflation")
    r.append("  * Trade balance - monthly ComexStat updates")
    r.append("  * FX intervention - BACEN swap operations")
    r.append("")

    # Save report
    cur.close()
    conn.close()

    text = "\n".join(r)
    print(text)

    output_path = "analytics/brazil-economy-intelligence.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"\n{'=' * 80}")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    main()
