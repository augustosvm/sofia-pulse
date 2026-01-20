#!/usr/bin/env python3
"""Aplica a migration 006 - Skill Gap Views"""
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

import psycopg2

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "sofia"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "database": os.getenv("POSTGRES_DB", "sofia_db"),
}

def apply_migration():
    print("=" * 60)
    print("APLICANDO MIGRATION 006 - SKILL GAP VIEWS")
    print("=" * 60)
    
    migration_path = Path(__file__).parent.parent / 'sql' / 'migrations' / '006_skill_gap_views.sql'
    
    if not migration_path.exists():
        print(f"❌ Migration não encontrada: {migration_path}")
        return False
    
    sql = migration_path.read_text(encoding='utf-8')
    
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    
    try:
        # Executar cada statement separadamente
        statements = sql.split(';')
        for i, stmt in enumerate(statements):
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                print(f"   Executando statement {i+1}...")
                try:
                    cur.execute(stmt)
                    print(f"   ✅ OK")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"   ⚠️ Já existe, pulando...")
                    else:
                        print(f"   ❌ Erro: {e}")
        
        print("\n✅ Migration aplicada!")
        
        # Verificar views criadas
        print("\n📊 Verificando views criadas:")
        cur.execute("""
            SELECT matviewname FROM pg_matviews 
            WHERE schemaname = 'sofia' AND matviewname LIKE 'mv_skill%'
        """)
        for row in cur.fetchall():
            print(f"   ✅ {row[0]}")
        
        # Contagem
        print("\n📈 Contagem de registros:")
        views = [
            'sofia.mv_skill_demand_by_country',
            'sofia.mv_skill_supply_by_country', 
            'sofia.mv_skill_gap_by_country',
            'sofia.mv_skill_gap_country_summary'
        ]
        for view in views:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {view}")
                count = cur.fetchone()[0]
                print(f"   {view}: {count} rows")
            except Exception as e:
                print(f"   {view}: ❌ {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    apply_migration()
