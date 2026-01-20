# 🔧 ACLED V3 ETL - Instruções URGENTES

## Problema Identificado

✅ **Collector V3 rodou** e baixou dados de TODOS os continentes (800K+ eventos):
- US-Canada: 21,488 rows
- Latin America: 165,443 rows
- Middle East: 141,487 rows
- Asia-Pacific: 202,705 rows
- Africa: 262,143 rows

❌ **MAS os dados foram inseridos em**:
- `acled_aggregated.regional` (schema separado)
- `acled_aggregated.country_year`
- `acled_aggregated.country_month_year`

✅ **O mapa lê de**:
- `sofia.security_events` (está vazio ou só tem dados antigos da África!)

## Solução: Rodar ETL/Normalizer V3

O script `collectors/security/acled_normalizer_v3.py` foi criado para:
1. Ler de `acled_aggregated.regional` (onde está TODO o mundo)
2. Transformar para `sofia.security_events` (onde o mapa lê)
3. Refresh das materialized views
4. Resultado: Mapa mostra TODOS os continentes!

## Como Executar

**Simples**: O script lê do `.env` automaticamente!

```bash
cd /mnt/c/Users/augusto.moreira/Documents/sofia-pulse

# Run normalizer (lê senha do .env)
python3 collectors/security/acled_normalizer_v3.py
```

Se precisar sobrescrever (opcional):
```bash
export POSTGRES_PASSWORD="senha_manual"
python3 collectors/security/acled_normalizer_v3.py
```

## O que o Script Faz

1. ✅ Conecta em `acled_aggregated.regional`
2. ✅ Conta total de registros (~800K)
3. ✅ **Limpa dados antigos** de `sofia.security_events` (fonte ACLED)
4. ✅ **Insere TODOS os dados** em `sofia.security_events`:
   - country_name
   - latitude, longitude (centroids)
   - event_date, event_type
   - fatalities, severity
5. ✅ **Refresh views**:
   - mv_security_country_summary
   - mv_security_geo_points
   - mv_security_momentum
   - mv_security_country_acled (hybrid model)

## Verificação

Após rodar, o script vai mostrar:

```
✅ Security Events Summary (ACLED):
  Total records: 800000+
  With geo: 800000+
  Countries: 150+
  Date range: 2020-01-01 to 2026-01-03

📊 Top 20 countries by events:
  Ukraine: XXXX events
  Nigeria: XXXX events
  Ethiopia: XXXX events
  Myanmar: XXXX events
  United States: XXXX events  ← DEVE APARECER AQUI!
  Brazil: XXXX events         ← DEVE APARECER AQUI!
  ...
```

## Depois do ETL

1. Refresh o mapa: http://172.27.140.239:3001/map
2. Clique em "Security"
3. **Ctrl+Shift+R** (hard reload)
4. Deve aparecer pontos em:
   - ✅ África (já estava)
   - ✅ Ucrânia/Europa (agora vai aparecer!)
   - ✅ Américas (US, Brasil, México, etc.)
   - ✅ Oriente Médio (Síria, Iêmen, etc.)
   - ✅ Ásia (Myanmar, Filipinas, etc.)

## Troubleshooting

### Erro: "No data in acled_aggregated.regional"

Rode o collector V3 primeiro:
```bash
python3 scripts/collect-acled-aggregated-postgres-v3.py
```

### Erro: "connection to server failed: no password supplied"

Verifique se o `.env` tem a senha configurada:
```bash
grep POSTGRES_PASSWORD .env
# ou
grep DB_PASSWORD .env
```

Se não tiver, adicione no `.env`:
```env
POSTGRES_PASSWORD=sua_senha_aqui
```

### Mapa ainda mostra só África após ETL

1. Verifique os logs do normalizer (deve mostrar 800K+ records)
2. Force refresh das views:
```bash
psql -h 91.98.158.19 -U dbs_sofia -d sofia -c "SELECT sofia.refresh_security_hybrid_views();"
```
3. Hard reload no browser (Ctrl+Shift+F5)

## Próximos Passos

Depois que o ETL rodar:

1. ✅ Aplicar migration 052 (hybrid model)
```bash
psql -h 91.98.158.19 -U dbs_sofia -d sofia -f migrations/052_security_hybrid_model.sql
```

2. ✅ Popular dim_country
```bash
python3 scripts/populate-dim-country.py
```

3. ✅ Refresh hybrid views
```bash
psql -h 91.98.158.19 -U dbs_sofia -d sofia -c "SELECT sofia.refresh_security_hybrid_views();"
```

## CRÍTICO

**RODE O NORMALIZER V3 AGORA!**

Todos os dados já estão coletados, só falta mover de:
`acled_aggregated.regional` → `sofia.security_events`

Isso vai fazer a Ucrânia, Américas, Ásia aparecerem no mapa!
