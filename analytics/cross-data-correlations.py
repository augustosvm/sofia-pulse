#!/usr/bin/env python3
"""
================================================================================
CROSS-DATA CORRELATIONS ANALYSIS
================================================================================
Statistical analysis of correlations between socioeconomic indicators.
Uses Pearson correlation coefficient to identify real relationships.

Key Correlations Analyzed:
1. GDP vs Life Expectancy (Health-Wealth connection)
2. Education vs R&D Investment (Innovation pipeline)
3. Female Labor vs GDP (Gender equality indicator)
4. Internet Access vs GDP (Digital divide)
5. Security vs Foreign Investment (Risk assessment)

Output: Statistical correlations with actionable insights
================================================================================
"""
import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import math

load_dotenv()

# Regions and aggregates to exclude (not countries)
EXCLUDE_ENTITIES = [
    'World', 'North America', 'South Asia', 'Europe & Central Asia',
    'East Asia & Pacific', 'Latin America & Caribbean', 'Middle East & North Africa',
    'Sub-Saharan Africa', 'European Union', 'OECD members', 'High income',
    'Low income', 'Middle income', 'Upper middle income', 'Lower middle income',
    'Post-demographic dividend', 'Pre-demographic dividend', 'Late-demographic dividend',
    'Early-demographic dividend', 'IDA & IBRD total', 'IDA total', 'IBRD only',
    'Heavily indebted poor countries (HIPC)', 'Least developed countries: UN classification',
    'Fragile and conflict affected situations', 'Small states', 'Pacific island small states',
    'Caribbean small states', 'Other small states', 'Arab World', 'Central Europe and the Baltics',
    'Euro area', 'Africa Eastern and Southern', 'Africa Western and Central'
]

def get_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', os.getenv('POSTGRES_HOST', 'localhost')),
        port=os.getenv('DB_PORT', os.getenv('POSTGRES_PORT', '5432')),
        dbname=os.getenv('DB_NAME', os.getenv('POSTGRES_DB', 'sofia')),
        user=os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'postgres')),
        password=os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', ''))
    )

def pearson_correlation(x_values, y_values):
    """Calculate Pearson correlation coefficient"""
    n = len(x_values)
    if n < 3:
        return None, None

    sum_x = sum(x_values)
    sum_y = sum(y_values)
    sum_xy = sum(x * y for x, y in zip(x_values, y_values))
    sum_x2 = sum(x * x for x in x_values)
    sum_y2 = sum(y * y for y in y_values)

    numerator = n * sum_xy - sum_x * sum_y
    denominator = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))

    if denominator == 0:
        return None, None

    r = numerator / denominator

    # Strength classification
    abs_r = abs(r)
    if abs_r >= 0.8:
        strength = "VERY STRONG"
    elif abs_r >= 0.6:
        strength = "STRONG"
    elif abs_r >= 0.4:
        strength = "MODERATE"
    elif abs_r >= 0.2:
        strength = "WEAK"
    else:
        strength = "NEGLIGIBLE"

    direction = "POSITIVE" if r > 0 else "NEGATIVE"

    return r, f"{strength} {direction}"

def format_correlation_bar(r):
    """Create visual bar for correlation strength"""
    if r is None:
        return ""
    abs_r = abs(r)
    bar_len = int(abs_r * 20)
    char = "+" if r > 0 else "-"
    return char * bar_len

def main():
    conn = get_connection()
    cur = conn.cursor()

    r = []
    r.append("=" * 80)
    r.append("CROSS-DATA CORRELATIONS ANALYSIS")
    r.append("=" * 80)
    r.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    r.append("Method: Pearson Correlation Coefficient (r)")
    r.append("Interpretation: |r| > 0.8 = Very Strong, > 0.6 = Strong, > 0.4 = Moderate")
    r.append("")

    # Build exclude clause
    exclude_clause = "AND country_name NOT IN (" + ",".join(f"'{e}'" for e in EXCLUDE_ENTITIES) + ")"

    correlations_summary = []

    # =========================================================================
    # 1. GDP vs LIFE EXPECTANCY (Health-Wealth Nexus)
    # =========================================================================
    r.append("=" * 80)
    r.append("1. GDP vs LIFE EXPECTANCY (Health-Wealth Connection)")
    r.append("=" * 80)
    r.append("")

    try:
        cur.execute(f"""
            WITH latest_data AS (
                SELECT country_name,
                       MAX(CASE WHEN indicator_code = 'NY.GDP.PCAP.CD' THEN value END) as gdp,
                       MAX(CASE WHEN indicator_code = 'SP.DYN.LE00.IN' THEN value END) as life_exp
                FROM sofia.socioeconomic_indicators
                WHERE value IS NOT NULL
                  AND year >= 2018
                  {exclude_clause}
                GROUP BY country_name
                HAVING MAX(CASE WHEN indicator_code = 'NY.GDP.PCAP.CD' THEN value END) IS NOT NULL
                   AND MAX(CASE WHEN indicator_code = 'SP.DYN.LE00.IN' THEN value END) IS NOT NULL
            )
            SELECT country_name, gdp, life_exp
            FROM latest_data
            WHERE gdp > 0 AND life_exp > 0
            ORDER BY gdp DESC
        """)
        rows = cur.fetchall()

        if rows:
            gdp_values = [float(row[1]) for row in rows]
            life_values = [float(row[2]) for row in rows]

            corr, strength = pearson_correlation(gdp_values, life_values)

            r.append(f"Sample Size: {len(rows)} countries")
            r.append(f"Correlation (r): {corr:.4f}" if corr else "Correlation: N/A")
            r.append(f"Strength: {strength}" if strength else "")
            r.append(f"Visual: {format_correlation_bar(corr)}")
            r.append("")

            correlations_summary.append(("GDP vs Life Expectancy", corr, strength))

            # Show top/bottom examples
            r.append("HIGH GDP + HIGH LIFE EXPECTANCY (Top 8):")
            r.append("-" * 60)
            r.append(f"{'Country':<25} {'GDP/capita':>15} {'Life Exp':>12}")
            r.append("-" * 60)
            for country, gdp, life in rows[:8]:
                r.append(f"{country:<25} ${float(gdp):>14,.0f} {float(life):>10.1f} yrs")
            r.append("")

            # Show outliers (high life exp, lower GDP)
            outliers = [(c, g, l) for c, g, l in rows if float(l) > 80 and float(g) < 30000]
            if outliers:
                r.append("OUTLIERS: High Life Expectancy Despite Lower GDP:")
                r.append("-" * 60)
                for country, gdp, life in sorted(outliers, key=lambda x: -float(x[2]))[:5]:
                    r.append(f"  {country}: Life {float(life):.1f} yrs, GDP ${float(gdp):,.0f}")
                r.append("  -> These countries achieve health outcomes above economic level")
                r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 2. EDUCATION vs R&D SPENDING (Innovation Pipeline)
    # =========================================================================
    r.append("=" * 80)
    r.append("2. TERTIARY EDUCATION vs R&D SPENDING (Innovation Pipeline)")
    r.append("=" * 80)
    r.append("")

    try:
        cur.execute(f"""
            WITH latest_data AS (
                SELECT country_name,
                       MAX(CASE WHEN indicator_code = 'SE.TER.ENRR' THEN value END) as education,
                       MAX(CASE WHEN indicator_code = 'GB.XPD.RSDV.GD.ZS' THEN value END) as rd_spend
                FROM sofia.socioeconomic_indicators
                WHERE value IS NOT NULL
                  AND year >= 2015
                  {exclude_clause}
                GROUP BY country_name
                HAVING MAX(CASE WHEN indicator_code = 'SE.TER.ENRR' THEN value END) IS NOT NULL
                   AND MAX(CASE WHEN indicator_code = 'GB.XPD.RSDV.GD.ZS' THEN value END) IS NOT NULL
            )
            SELECT country_name, education, rd_spend
            FROM latest_data
            WHERE education > 0 AND rd_spend > 0
            ORDER BY rd_spend DESC
        """)
        rows = cur.fetchall()

        if rows:
            edu_values = [float(row[1]) for row in rows]
            rd_values = [float(row[2]) for row in rows]

            corr, strength = pearson_correlation(edu_values, rd_values)

            r.append(f"Sample Size: {len(rows)} countries")
            r.append(f"Correlation (r): {corr:.4f}" if corr else "Correlation: N/A")
            r.append(f"Strength: {strength}" if strength else "")
            r.append(f"Visual: {format_correlation_bar(corr)}")
            r.append("")

            correlations_summary.append(("Education vs R&D", corr, strength))

            r.append("TOP R&D INVESTORS:")
            r.append("-" * 60)
            r.append(f"{'Country':<25} {'Tertiary Enroll':>15} {'R&D % GDP':>12}")
            r.append("-" * 60)
            for country, edu, rd in rows[:10]:
                r.append(f"{country:<25} {float(edu):>14.1f}% {float(rd):>11.2f}%")
            r.append("")

            # Identify potential
            potential = [(c, e, rd) for c, e, rd in rows if float(e) > 60 and float(rd) < 1.5]
            if potential:
                r.append("UNTAPPED POTENTIAL: High Education, Low R&D:")
                r.append("-" * 60)
                for country, edu, rd in sorted(potential, key=lambda x: -float(x[1]))[:5]:
                    r.append(f"  {country}: {float(edu):.1f}% tertiary, only {float(rd):.2f}% R&D")
                r.append("  -> Educated workforce, room for R&D investment growth")
                r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 3. FEMALE LABOR PARTICIPATION vs GDP
    # =========================================================================
    r.append("=" * 80)
    r.append("3. FEMALE LABOR PARTICIPATION vs GDP (Gender-Development Link)")
    r.append("=" * 80)
    r.append("")

    try:
        cur.execute(f"""
            WITH latest_data AS (
                SELECT country_name,
                       MAX(CASE WHEN indicator_code = 'SL.TLF.CACT.FE.ZS' THEN value END) as female_labor,
                       MAX(CASE WHEN indicator_code = 'NY.GDP.PCAP.CD' THEN value END) as gdp
                FROM sofia.socioeconomic_indicators
                WHERE value IS NOT NULL
                  AND year >= 2018
                  {exclude_clause}
                GROUP BY country_name
                HAVING MAX(CASE WHEN indicator_code = 'SL.TLF.CACT.FE.ZS' THEN value END) IS NOT NULL
                   AND MAX(CASE WHEN indicator_code = 'NY.GDP.PCAP.CD' THEN value END) IS NOT NULL
            )
            SELECT country_name, female_labor, gdp
            FROM latest_data
            WHERE female_labor > 0 AND gdp > 0
            ORDER BY gdp DESC
        """)
        rows = cur.fetchall()

        if rows:
            female_values = [float(row[1]) for row in rows]
            gdp_values = [float(row[2]) for row in rows]

            corr, strength = pearson_correlation(female_values, gdp_values)

            r.append(f"Sample Size: {len(rows)} countries")
            r.append(f"Correlation (r): {corr:.4f}" if corr else "Correlation: N/A")
            r.append(f"Strength: {strength}" if strength else "")
            r.append(f"Visual: {format_correlation_bar(corr)}")
            r.append("")

            correlations_summary.append(("Female Labor vs GDP", corr, strength))

            # Group by development level
            high_gdp = [(c, f, g) for c, f, g in rows if float(g) > 40000]
            low_gdp = [(c, f, g) for c, f, g in rows if float(g) < 5000]

            if high_gdp:
                avg_female_high = sum(float(x[1]) for x in high_gdp) / len(high_gdp)
                r.append(f"HIGH-INCOME COUNTRIES (GDP > $40k):")
                r.append(f"  Average Female Labor Participation: {avg_female_high:.1f}%")
                r.append(f"  Sample: {len(high_gdp)} countries")
                r.append("")

            if low_gdp:
                avg_female_low = sum(float(x[1]) for x in low_gdp) / len(low_gdp)
                r.append(f"LOW-INCOME COUNTRIES (GDP < $5k):")
                r.append(f"  Average Female Labor Participation: {avg_female_low:.1f}%")
                r.append(f"  Sample: {len(low_gdp)} countries")
                r.append("")

            # Top performers
            r.append("HIGHEST FEMALE PARTICIPATION:")
            r.append("-" * 50)
            top_female = sorted(rows, key=lambda x: -float(x[1]))[:8]
            for country, fem, gdp in top_female:
                r.append(f"  {country:<25} {float(fem):.1f}% (GDP: ${float(gdp):,.0f})")
            r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 4. INTERNET ACCESS vs GDP (Digital Divide)
    # =========================================================================
    r.append("=" * 80)
    r.append("4. INTERNET ACCESS vs GDP (Digital Divide Analysis)")
    r.append("=" * 80)
    r.append("")

    try:
        cur.execute(f"""
            WITH latest_data AS (
                SELECT country_name,
                       MAX(CASE WHEN indicator_code = 'IT.NET.USER.ZS' THEN value END) as internet,
                       MAX(CASE WHEN indicator_code = 'NY.GDP.PCAP.CD' THEN value END) as gdp
                FROM sofia.socioeconomic_indicators
                WHERE value IS NOT NULL
                  AND year >= 2018
                  {exclude_clause}
                GROUP BY country_name
                HAVING MAX(CASE WHEN indicator_code = 'IT.NET.USER.ZS' THEN value END) IS NOT NULL
                   AND MAX(CASE WHEN indicator_code = 'NY.GDP.PCAP.CD' THEN value END) IS NOT NULL
            )
            SELECT country_name, internet, gdp
            FROM latest_data
            WHERE internet > 0 AND gdp > 0
            ORDER BY internet DESC
        """)
        rows = cur.fetchall()

        if rows:
            internet_values = [float(row[1]) for row in rows]
            gdp_values = [float(row[2]) for row in rows]

            corr, strength = pearson_correlation(internet_values, gdp_values)

            r.append(f"Sample Size: {len(rows)} countries")
            r.append(f"Correlation (r): {corr:.4f}" if corr else "Correlation: N/A")
            r.append(f"Strength: {strength}" if strength else "")
            r.append(f"Visual: {format_correlation_bar(corr)}")
            r.append("")

            correlations_summary.append(("Internet vs GDP", corr, strength))

            # Digital leaders
            r.append("DIGITAL LEADERS (>95% Internet Access):")
            r.append("-" * 50)
            leaders = [(c, i, g) for c, i, g in rows if float(i) > 95]
            for country, internet, gdp in leaders[:8]:
                r.append(f"  {country:<25} {float(internet):.1f}% (GDP: ${float(gdp):,.0f})")
            r.append("")

            # Digital divide
            low_internet = [(c, i, g) for c, i, g in rows if float(i) < 30]
            if low_internet:
                r.append("DIGITAL DIVIDE (<30% Internet Access):")
                r.append("-" * 50)
                for country, internet, gdp in sorted(low_internet, key=lambda x: float(x[1]))[:5]:
                    r.append(f"  {country:<25} {float(internet):.1f}% (GDP: ${float(gdp):,.0f})")
                r.append("  -> Opportunity for digital infrastructure investment")
                r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # 5. UNEMPLOYMENT vs GDP GROWTH
    # =========================================================================
    r.append("=" * 80)
    r.append("5. UNEMPLOYMENT vs GDP per CAPITA")
    r.append("=" * 80)
    r.append("")

    try:
        cur.execute(f"""
            WITH latest_data AS (
                SELECT country_name,
                       MAX(CASE WHEN indicator_code = 'SL.UEM.TOTL.ZS' THEN value END) as unemployment,
                       MAX(CASE WHEN indicator_code = 'NY.GDP.PCAP.CD' THEN value END) as gdp
                FROM sofia.socioeconomic_indicators
                WHERE value IS NOT NULL
                  AND year >= 2018
                  {exclude_clause}
                GROUP BY country_name
                HAVING MAX(CASE WHEN indicator_code = 'SL.UEM.TOTL.ZS' THEN value END) IS NOT NULL
                   AND MAX(CASE WHEN indicator_code = 'NY.GDP.PCAP.CD' THEN value END) IS NOT NULL
            )
            SELECT country_name, unemployment, gdp
            FROM latest_data
            WHERE unemployment >= 0 AND gdp > 0
            ORDER BY unemployment ASC
        """)
        rows = cur.fetchall()

        if rows:
            unemp_values = [float(row[1]) for row in rows]
            gdp_values = [float(row[2]) for row in rows]

            corr, strength = pearson_correlation(unemp_values, gdp_values)

            r.append(f"Sample Size: {len(rows)} countries")
            r.append(f"Correlation (r): {corr:.4f}" if corr else "Correlation: N/A")
            r.append(f"Strength: {strength}" if strength else "")
            r.append(f"Visual: {format_correlation_bar(corr)}")
            r.append("")

            correlations_summary.append(("Unemployment vs GDP", corr, strength))

            # Low unemployment high GDP
            r.append("LOW UNEMPLOYMENT + HIGH GDP (Best Labor Markets):")
            r.append("-" * 60)
            best_labor = [(c, u, g) for c, u, g in rows if float(u) < 5 and float(g) > 30000]
            for country, unemp, gdp in sorted(best_labor, key=lambda x: float(x[1]))[:8]:
                r.append(f"  {country:<25} {float(unemp):.1f}% unemp (GDP: ${float(gdp):,.0f})")
            r.append("")

            # High unemployment
            r.append("LABOR MARKET CHALLENGES (>15% Unemployment):")
            r.append("-" * 50)
            high_unemp = [(c, u, g) for c, u, g in rows if float(u) > 15]
            for country, unemp, gdp in sorted(high_unemp, key=lambda x: -float(x[1]))[:5]:
                r.append(f"  {country:<25} {float(unemp):.1f}% (GDP: ${float(gdp):,.0f})")
            r.append("")

    except Exception as e:
        conn.rollback()
        r.append(f"Error: {e}")
        r.append("")

    # =========================================================================
    # CORRELATION SUMMARY & RANKINGS
    # =========================================================================
    r.append("=" * 80)
    r.append("CORRELATION SUMMARY & RANKINGS")
    r.append("=" * 80)
    r.append("")

    r.append("CORRELATION STRENGTH RANKING:")
    r.append("-" * 70)
    r.append(f"{'Relationship':<35} {'r-value':>10} {'Strength':>20}")
    r.append("-" * 70)

    # Sort by absolute correlation value
    valid_corrs = [(name, c, s) for name, c, s in correlations_summary if c is not None]
    sorted_corrs = sorted(valid_corrs, key=lambda x: abs(x[1]), reverse=True)

    for name, corr, strength in sorted_corrs:
        bar = format_correlation_bar(corr)
        r.append(f"{name:<35} {corr:>10.4f} {strength:>20}")
        r.append(f"{'':35} {bar}")
        r.append("")

    # =========================================================================
    # STRATEGIC INSIGHTS
    # =========================================================================
    r.append("=" * 80)
    r.append("STRATEGIC INSIGHTS")
    r.append("=" * 80)
    r.append("")

    r.append("FOR MARKET EXPANSION:")
    r.append("-" * 50)
    r.append("  * GDP-Life Expectancy correlation suggests:")
    r.append("    - High GDP markets have healthier, longer-living consumers")
    r.append("    - Healthcare/wellness products viable in wealthy markets")
    r.append("")
    r.append("  * Internet-GDP correlation indicates:")
    r.append("    - Digital services scale with economic development")
    r.append("    - Low-internet countries = infrastructure opportunity")
    r.append("")

    r.append("FOR TALENT ACQUISITION:")
    r.append("-" * 50)
    r.append("  * Education-R&D correlation shows:")
    r.append("    - Countries with high tertiary enrollment = tech talent pools")
    r.append("    - R&D hubs attract and retain educated workers")
    r.append("")
    r.append("  * Low unemployment + high GDP countries:")
    r.append("    - Tight labor markets, higher salary expectations")
    r.append("    - Consider remote hiring from other regions")
    r.append("")

    r.append("FOR ESG/IMPACT INVESTING:")
    r.append("-" * 50)
    r.append("  * Female labor participation patterns:")
    r.append("    - Gender equality correlates with development")
    r.append("    - Markets with low female participation = growth potential")
    r.append("")

    r.append("METHODOLOGY NOTES:")
    r.append("-" * 50)
    r.append("  * Pearson r ranges from -1 to +1")
    r.append("  * |r| > 0.8: Very Strong correlation")
    r.append("  * |r| > 0.6: Strong correlation")
    r.append("  * |r| > 0.4: Moderate correlation")
    r.append("  * Correlation does not imply causation")
    r.append("  * Data filtered to countries only (regions excluded)")
    r.append("")

    # Save report
    cur.close()
    conn.close()

    text = "\n".join(r)
    print(text)

    output_path = "analytics/cross-data-correlations.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"\n{'=' * 80}")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    main()
