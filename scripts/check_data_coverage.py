#!/usr/bin/env python3
"""
Sofia Pulse - Data Health Check
Purpose: Verify data coverage and quality across intelligence domains
Usage: python scripts/check_data_coverage.py
"""

import psycopg2
import psycopg2.extras
import os
from pathlib import Path
from datetime import datetime

def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v

def get_db():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("POSTGRES_DB", "sofia_db")
    )

def check_materialized_view(cur, view_name, key_column="country_code"):
    """Check a single materialized view"""
    try:
        # Check if exists
        cur.execute(f"""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'sofia' AND table_name = %s
        """, (view_name,))
        exists = cur.fetchone()[0] > 0
        
        if not exists:
            return {"exists": False, "count": 0, "status": "NOT_FOUND"}
        
        # Get count
        cur.execute(f"SELECT COUNT(*) FROM sofia.{view_name}")
        count = cur.fetchone()[0]
        
        # Get confidence distribution if column exists
        cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'sofia' 
              AND table_name = %s 
              AND column_name IN ('confidence', 'confidence_score')
        """, (view_name,))
        conf_col = cur.fetchone()
        
        confidence_dist = None
        if conf_col:
            col_name = conf_col[0]
            cur.execute(f"""
                SELECT 
                    COUNT(*) FILTER (WHERE {col_name} >= 0.8) as high,
                    COUNT(*) FILTER (WHERE {col_name} >= 0.5 AND {col_name} < 0.8) as medium,
                    COUNT(*) FILTER (WHERE {col_name} < 0.5) as low
                FROM sofia.{view_name}
            """)
            row = cur.fetchone()
            confidence_dist = {"high": row[0], "medium": row[1], "low": row[2]}
        
        # Get last update if column exists
        cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'sofia' 
              AND table_name = %s 
              AND column_name IN ('updated_at', 'calculated_at', 'as_of_date')
        """, (view_name,))
        date_col = cur.fetchone()
        
        last_update = None
        if date_col:
            cur.execute(f"SELECT MAX({date_col[0]}) FROM sofia.{view_name}")
            last_update = cur.fetchone()[0]
        
        return {
            "exists": True,
            "count": count,
            "status": "OK" if count > 0 else "EMPTY",
            "confidence_dist": confidence_dist,
            "last_update": last_update
        }
        
    except Exception as e:
        return {"exists": False, "count": 0, "status": f"ERROR: {e}"}

def main():
    load_env()
    conn = get_db()
    cur = conn.cursor()
    
    print("=" * 70)
    print("SOFIA PULSE - DATA HEALTH REPORT")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 70)
    
    views_to_check = [
        ("mv_capital_analytics", "Capital Intelligence"),
        ("mv_skill_gap_country_summary", "Talent Intelligence"),
        ("mv_security_country_combined", "Security Intelligence"),
        ("mv_opportunity_by_country", "Opportunity Index"),
        ("mv_brain_drain_by_country", "Brain Drain Index"),
        ("mv_ai_capability_density_by_country", "AI Capability Density"),
        ("mv_innovation_velocity_by_country", "Innovation Velocity"),
        ("mv_research_velocity_by_country", "Research Velocity"),
        ("mv_tool_demand_by_country", "Tool Demand"),
        ("mv_industry_signals_heat_by_country", "Industry Signals Heat"),
        ("mv_cyber_risk_by_country", "Cyber Risk"),
        ("mv_clinical_trials_by_country", "Clinical Trials"),
        ("mv_women_intelligence_by_country", "Women/Violence Risk Proxy"),
        ("mv_ngo_coverage_by_country", "NGO Coverage"),
        ("mv_regulatory_pressure_by_country", "Regulatory Pressure"),
        ("mv_infrastructure_stress_by_country", "Infrastructure Stress"),
    ]

    
    for view_name, display_name in views_to_check:
        result = check_materialized_view(cur, view_name)
        status_icon = "✅" if result["status"] == "OK" else "⚠️" if result["status"] == "EMPTY" else "❌"
        
        print(f"\n{status_icon} {display_name}")
        print(f"   View: sofia.{view_name}")
        print(f"   Status: {result['status']}")
        print(f"   Countries: {result['count']}")
        
        if result.get("confidence_dist"):
            cd = result["confidence_dist"]
            print(f"   Confidence: High={cd['high']}, Medium={cd['medium']}, Low={cd['low']}")
        
        if result.get("last_update"):
            print(f"   Last Update: {result['last_update']}")
    
    print("\n" + "=" * 70)
    print("REFRESH COMMANDS (run in order):")
    print("=" * 70)
    print("""
-- Base views first
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_skill_demand_by_country;
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_skill_supply_by_country;

-- Domain views
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_capital_analytics;
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_skill_gap_by_country;
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_skill_gap_country_summary;
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_security_country_combined;
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_brain_drain_by_country;
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_ai_capability_density_by_country;

-- Phase 2 views
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_industry_signals_heat_by_country;
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_cyber_risk_by_country;
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_clinical_trials_by_country;

-- Phase 3 views (Women + NGO)
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_women_intelligence_by_country;
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_ngo_coverage_by_country;

-- Composite views last
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_opportunity_by_country;
""")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
