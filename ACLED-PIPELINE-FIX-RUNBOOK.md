# ACLED Pipeline Fix - Runbook de Execução

## Problema Identificado
1. **Gargalo ETL**: Dados LATAM em `acled_aggregated.regional` não chegavam em `sofia.security_events`
2. **Gargalo ISO2**: Mapeamento de `country_code` por nome exato falhava massivamente (261 registros sem ISO2)

## Solução Implementada

### 1. Tabela de Aliases de Países
Criada `sofia.dim_country_alias` com mapeamentos robustos para ACLED, incluindo:
- Nomes oficiais em inglês
- Variações conhecidas (Myanmar/Burma, DR Congo, etc.)
- Todos os países da América Latina

### 2. ETL Regional → Events
Script `import-acled-regional-to-security-events.py` que:
- Lê de `acled_aggregated.regional`
- Transforma para formato `sofia.security_events`
- Preserva metadados regionais

### 3. Normalizer v3 Robusto
Script `normalize-acled-to-observations-v3.py` que:
- Mapeia `country_code` via `dim_country_alias` (fallback para `dim_country`)
- Normalização P95 mantida
- Insere diretamente com ISO2 (não UPDATE posterior)

## Ordem de Execução

```bash
# 1. Limpar códigos ISO com espaços (JÁ EXECUTADO)
python -c "import psycopg2, os; from dotenv import load_dotenv; load_dotenv(); c=psycopg2.connect(host=os.getenv('POSTGRES_HOST'),user=os.getenv('POSTGRES_USER'),password=os.getenv('POSTGRES_PASSWORD'),dbname=os.getenv('POSTGRES_DB')); c.autocommit=True; cur=c.cursor(); cur.execute('UPDATE sofia.dim_country SET country_code_iso2 = TRIM(country_code_iso2), country_code_iso3 = TRIM(country_code_iso3)'); print(f'✅ Limpados {cur.rowcount} códigos ISO')"

# 2. Criar tabela de aliases
python -c "import psycopg2, os; from dotenv import load_dotenv; load_dotenv(); c=psycopg2.connect(host=os.getenv('POSTGRES_HOST'),user=os.getenv('POSTGRES_USER'),password=os.getenv('POSTGRES_PASSWORD'),dbname=os.getenv('POSTGRES_DB')); c.autocommit=True; cur=c.cursor(); cur.execute(open('migrations/001_create_country_alias.sql', encoding='utf-8').read()); print('✅ Tabela dim_country_alias criada e populada')"

# 3. Coletar dados LATAM
python scripts/collect-acled-latam.py

# 4. ETL: Regional → Events
python scripts/import-acled-regional-to-security-events.py

# 5. Normalizar: Events → Observations (com ISO2 robusto)
python scripts/normalize-acled-to-observations-v3.py

# 6. Refresh materialized views
python scripts/refresh_view.py

# 7. Verificar resultado
python scripts/verify_api_data.py
```

## Verificações SQL

### Antes da Execução
```sql
-- LATAM em regional?
SELECT COUNT(*) FROM acled_aggregated.regional
WHERE region ILIKE '%Latin America%';

-- LATAM em security_events?
SELECT COUNT(*) FROM sofia.security_events
WHERE source='ACLED_AGGREGATED'
  AND LOWER(country_name) IN ('brazil','argentina','chile','colombia','peru','venezuela');

-- Quantos sem country_code?
SELECT COUNT(*) AS null_cc
FROM sofia.security_observations
WHERE source='ACLED' AND country_code IS NULL;
```

### Depois da Execução
```sql
-- Total por país em observations
SELECT country_code, country_name, COUNT(*) as cnt
FROM sofia.security_observations
WHERE source='ACLED'
GROUP BY country_code, country_name
ORDER BY cnt DESC
LIMIT 20;

-- LATAM específico
SELECT country_code, country_name, COUNT(*) as cnt
FROM sofia.security_observations
WHERE source='ACLED' 
  AND country_code IN ('BR','AR','CL','CO','PE','VE','BO','EC','PY','UY','MX')
GROUP BY country_code, country_name
ORDER BY cnt DESC;

-- Taxa de sucesso ISO2
SELECT 
    COUNT(*) as total,
    COUNT(country_code) as with_iso2,
    ROUND(COUNT(country_code)::numeric / COUNT(*) * 100, 1) as success_rate
FROM sofia.security_observations
WHERE source='ACLED';

-- Países na view final
SELECT COUNT(*) FROM sofia.mv_security_country_combined;
```

## Arquivos Criados
- `migrations/001_create_country_alias.sql` - Schema da tabela de aliases
- `scripts/collect-acled-latam.py` - Coletor LATAM (corrigido com autocommit)
- `scripts/import-acled-regional-to-security-events.py` - ETL regional→events
- `scripts/normalize-acled-to-observations-v3.py` - Normalizer robusto
- `scripts/diagnose_acled_pipeline.py` - Diagnóstico dos gargalos

## Resultado Esperado
- ✅ 165k+ registros LATAM em `acled_aggregated.regional`
- ✅ 165k+ registros LATAM em `sofia.security_events`
- ✅ 165k+ registros LATAM em `sofia.security_observations` com `country_code` preenchido
- ✅ Taxa de sucesso ISO2 >= 95%
- ✅ Países LATAM visíveis em `/api/security/countries`
- ✅ Choropleth com variação de cores (não mais "tudo igual")
