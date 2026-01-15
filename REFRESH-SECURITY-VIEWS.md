# 🔄 Refresh Security Views - URGENTE

## Problema

Os dados ACLED foram coletados de TODOS os continentes (US, Europe, Asia, Latin America, Middle East, Africa) mas as **materialized views** ainda mostram apenas África.

## Solução

Execute este comando SQL no banco de dados:

```sql
SELECT sofia.refresh_security_views();
```

### Opção 1: Via psql

```bash
psql -h 91.98.158.19 -U dbs_sofia -d sofia -c "SELECT sofia.refresh_security_views();"
```

### Opção 2: Via DBeaver/pgAdmin

1. Conecte no banco `sofia` no host `91.98.158.19`
2. Execute a query:
```sql
SELECT sofia.refresh_security_views();
```

### Opção 3: Via Python

```bash
cd sofia-pulse
python3 scripts/refresh-security-views.py
```

(Precisa DATABASE_URL correto no .env)

## Verificar Resultado

Após refresh, execute:

```sql
-- Ver quantos pontos geo existem
SELECT COUNT(*) FROM sofia.mv_security_geo_points;

-- Ver países por severidade
SELECT country_code, country_name, incidents, severity_norm, risk_level
FROM sofia.mv_security_country_summary
ORDER BY severity_norm DESC
LIMIT 30;

-- Ver range geográfico
SELECT
  MIN(latitude) as min_lat,
  MAX(latitude) as max_lat,
  MIN(longitude) as min_lng,
  MAX(longitude) as max_lng
FROM sofia.mv_security_geo_points;
```

Se min_lng/max_lng cobrir range maior (-180 a 180), significa que tem dados globais.

## Depois

1. Recarregue o mapa: http://172.27.140.239:3001/map
2. Clique em Security
3. Deve aparecer pontos em TODOS os continentes

## Dados Coletados

Hoje (2026-01-15) foram coletados:
- ✅ US-Canada: 21,488 rows
- ✅ Latin America-Caribbean: 165,443 rows
- ✅ Middle East: 141,487 rows
- ✅ Asia-Pacific: 202,705 rows
- ✅ Africa: 262,143 rows

**TOTAL: ~800K+ eventos** mas views precisam ser refreshed!
