#!/usr/bin/env python3
"""
Apply Enterprise Intelligence Migrations
Usage: python scripts/apply_enterprise_migrations.py
"""

import psycopg2
import os
from pathlib import Path

def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v

def main():
    load_env()
    
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("POSTGRES_DB", "sofia_db")
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    migrations_dir = Path(__file__).parent.parent / "sql" / "migrations"
    
    migrations = [
        "009_talent_enterprise.sql",
        "010_security_enterprise.sql", 
        "011_opportunity_index.sql",
        "012_new_domains_scaffold.sql",
        "013_intelligence_expansion.sql",
        "014_intelligence_expansion_phase2.sql",
        "015_normalization_layer.sql",
        "016_optimized_intelligence_mvs.sql",
        "017_women_ngo_intelligence.sql"
    ]
    
    for mig in migrations:
        mig_path = migrations_dir / mig
        if not mig_path.exists():
            print(f"❌ Migration not found: {mig}")
            continue
            
        print(f"📦 Applying {mig}...")
        try:
            sql = mig_path.read_text(encoding='utf-8')
            cur.execute(sql)
            print(f"   ✅ Success")
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
            # Continue with other migrations
    
    print("\n📊 Refreshing materialized views...")
    refresh_order = [
        "sofia.mv_capital_analytics",
        "sofia.mv_security_country_combined",
        "sofia.mv_brain_drain_by_country",
        "sofia.mv_ai_capability_density_by_country",
    ]
    
    for mv in refresh_order:
        try:
            print(f"   Refreshing {mv}...")
            cur.execute(f"REFRESH MATERIALIZED VIEW {mv}")
            print(f"   ✅ Done")
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
    
    cur.close()
    conn.close()
    print("\n✅ Migration complete!")

if __name__ == "__main__":
    main()
