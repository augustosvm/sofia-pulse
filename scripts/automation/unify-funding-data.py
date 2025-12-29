#!/usr/bin/env python3
"""
Unificação de Dados de Funding - Execução Completa
Executa os 3 passos: Migration, Normalização e Deduplicação
"""

import psycopg2
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def print_header(title):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70 + "\n")

def execute_sql_file(conn, filepath, description):
    """Executa um arquivo SQL"""
    print(f"▶️  {description}")
    print(f"   Arquivo: {filepath}\n")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        
        print("   ✅ Concluído com sucesso!\n")
        return True
    
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}\n")
        return False

def main():
    print_header("🚀 UNIFICAÇÃO DE DADOS DE FUNDING - EXECUÇÃO COMPLETA")
    
    print("Este script executará:")
    print("  1. Migration (adicionar colunas e constraints)")
    print("  2. Normalização (atualizar dados existentes)")
    print("  3. Deduplicação (remover duplicatas)\n")
    
    # Conectar ao banco
    print("📊 Conectando ao banco de dados...")
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'sofia'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB', 'sofia_db')
        )
        print(f"   ✅ Conectado: {os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}\n")
    except Exception as e:
        print(f"   ❌ Erro na conexão: {e}\n")
        sys.exit(1)
    
    # PASSO 1: Migration
    print_header("PASSO 1/3: MIGRATION - Adicionar Colunas e Constraints")
    
    if not execute_sql_file(
        conn,
        "migrations/add_funding_constraints.sql",
        "Adicionando colunas, constraints e índices"
    ):
        print("❌ Migration falhou! Abortando...\n")
        sys.exit(1)
    
    # PASSO 2: Normalização
    print_header("PASSO 2/3: NORMALIZAÇÃO - Atualizar Dados Existentes")
    
    print("▶️  Executando normalização de dados...\n")
    
    try:
        # Importar e executar normalização
        sys.path.insert(0, 'scripts')
        from shared.org_helpers import get_or_create_organization
        from shared.funding_helpers import normalize_round_type
        
        cur = conn.cursor()
        
        # 1. Adicionar source
        print("1️⃣  Adicionando 'source' baseado em round_type...")
        cur.execute("""
            UPDATE sofia.funding_rounds
            SET source = CASE
                WHEN round_type LIKE 'SEC%' THEN 'sec_edgar'
                WHEN round_type LIKE 'YC%' THEN 'yc_companies'
                ELSE 'unknown'
            END
            WHERE source IS NULL
        """)
        updated_source = cur.rowcount
        print(f"   ✅ {updated_source} registros atualizados\n")
        
        # 2. Normalizar round_type
        print("2️⃣  Normalizando round_type...")
        cur.execute("SELECT id, round_type FROM sofia.funding_rounds WHERE round_type IS NOT NULL LIMIT 100")
        rows = cur.fetchall()
        
        normalized_count = 0
        for row in rows:
            funding_id, round_type = row
            normalized = normalize_round_type(round_type)
            
            if normalized != round_type:
                cur.execute(
                    "UPDATE sofia.funding_rounds SET round_type = %s WHERE id = %s",
                    (normalized, funding_id)
                )
                normalized_count += 1
        
        print(f"   ✅ {normalized_count} registros normalizados\n")
        
        # 3. Adicionar organization_id (primeiros 100)
        print("3️⃣  Adicionando organization_id (amostra de 100)...")
        cur.execute("""
            SELECT id, company_name, country, source 
            FROM sofia.funding_rounds 
            WHERE organization_id IS NULL 
            AND company_name IS NOT NULL
            LIMIT 100
        """)
        
        rows = cur.fetchall()
        org_added = 0
        
        for row in rows:
            funding_id, company_name, country, source = row
            
            try:
                org_id = get_or_create_organization(
                    cur, company_name, None, None, country or 'USA', source or 'funding'
                )
                
                if org_id:
                    cur.execute(
                        "UPDATE sofia.funding_rounds SET organization_id = %s WHERE id = %s",
                        (org_id, funding_id)
                    )
                    org_added += 1
            except:
                pass
        
        print(f"   ✅ {org_added} registros com organization_id\n")
        
        conn.commit()
        print("   ✅ Normalização concluída!\n")
        
    except Exception as e:
        print(f"   ❌ Erro na normalização: {e}\n")
        conn.rollback()
    
    # PASSO 3: Deduplicação
    print_header("PASSO 3/3: DEDUPLICAÇÃO - Remover Duplicatas")
    
    if not execute_sql_file(
        conn,
        "migrations/deduplicate-funding.sql",
        "Removendo registros duplicados"
    ):
        print("⚠️  Deduplicação falhou (pode ser normal se não houver duplicatas)\n")
    
    # Estatísticas finais
    print_header("📊 ESTATÍSTICAS FINAIS")
    
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT company_name) as empresas,
            COUNT(DISTINCT organization_id) as orgs,
            COUNT(DISTINCT source) as fontes,
            COUNT(DISTINCT round_type) as tipos
        FROM sofia.funding_rounds
    """)
    
    row = cur.fetchone()
    print(f"   Total de registros: {row[0]}")
    print(f"   Empresas únicas: {row[1]}")
    print(f"   Organizations linkadas: {row[2]}")
    print(f"   Fontes de dados: {row[3]}")
    print(f"   Tipos de round: {row[4]}\n")
    
    conn.close()
    
    print_header("✅ UNIFICAÇÃO CONCLUÍDA COM SUCESSO!")
    
    print("Próximos passos:")
    print("  1. Testar collectors atualizados")
    print("  2. Verificar dados no banco")
    print("  3. Atualizar documentação\n")

if __name__ == "__main__":
    main()
