# WORLD SPORTS COLLECTOR - VERIFICATION PROTOCOL

**Date:** 2025-12-12 12:30 UTC
**Status:** ✅ FASE 2 COMPLETA - Correções aplicadas
**Commit:** eaabbbb

---

## BUGS CORRIGIDOS (FASE 2)

### 1. **save_who_data() - Undefined Variable**
**Linha 308:** `country_code` não definido
```python
# ANTES:
location = normalize_location(conn, {"country": country_code})  # ❌ NameError

# DEPOIS:
location = normalize_location(conn, {"country": country})  # ✅ CORRETO
```

### 2. **save_worldbank_data() - Invalid Syntax**
**Linha 369:** Syntax inválido em dict.get()
```python
# ANTES:
indicator_info.get("name", "", country_id=EXCLUDED.country_id)  # ❌ SyntaxError

# DEPOIS:
indicator_info.get("name", "")  # ✅ CORRETO
```

### 3. **save_worldbank_data() - Missing country_id**
**Linhas 361-375:** INSERT espera 9 valores mas recebia 8
```python
# ANTES:
INSERT INTO sofia.world_sports_data (..., country_id)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)  # ❌ Faltando 9º parâmetro

# DEPOIS:
# Normalização de country
country_code = record.get("countryiso3code", ...)
location = normalize_location(conn, {"country": country_code})
country_id = location.get("country_id")

# INSERT com 9 parâmetros
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)  # ✅ CORRETO
(..., country_id)  # 9º parâmetro
```

### 4. **Eurostat Section - Same Issues**
**Linhas 441-452:** Mesmo padrão de erros
```python
# ANTES:
r.get("dataset", "", country_id=EXCLUDED.country_id)  # ❌ SyntaxError
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)  # ❌ Faltando country_id

# DEPOIS:
r.get("dataset", "")  # ✅ CORRETO
location = normalize_location(conn, {"country": "EU"})
country_id = location.get("country_id")
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)  # ✅ 9 parâmetros
```

### 5. **Silent Errors - All Sections**
**Linhas 331, 378, 455:** Try/except sem logging
```python
# ANTES:
except:
    continue  # ❌ Erro silencioso

# DEPOIS:
except Exception as e:
    errors += 1
    if errors <= 3:  # Log primeiros 3 erros
        print(f"      ERROR saving record: {str(e)[:100]}")
    continue  # ✅ Com logging
```

---

## FASE 3 — PROVA DE VIDA (EXECUTAR NO SERVIDOR)

### **1. SSH para o servidor**
```bash
ssh ubuntu@91.98.158.19
cd ~/sofia-pulse
```

### **2. Pull das correções**
```bash
git fetch
git pull origin master  # ou branch específica
```

### **3. Executar collector com timeout**
```bash
# Executar com timeout de 3 minutos
timeout 180 python3 scripts/collect-world-sports.py 2>&1 | tee /tmp/world-sports-verification.log

# Capturar exit code
echo "Exit code: $?"
```

### **4. Verificar logs**
```bash
# Ver últimas 50 linhas
tail -50 /tmp/world-sports-verification.log

# Buscar por métricas chave
grep -E "Fetched:|Saved:|ERROR" /tmp/world-sports-verification.log
```

**EXPECTED OUTPUT:**
```
=== WHO PHYSICAL ACTIVITY ===
  Adolescents insufficiently physically active (%)...
    Fetched: XXXX records
    Saved: XXXX records

=== EUROSTAT SPORTS PARTICIPATION (EU) ===
  Fetching EU sports participation surveys...
    Fetched: XX records
    Saved: XX records

=== SOCIOECONOMIC INDICATORS ===
  Prevalence of overweight (% of adults)...
    Fetched: XXXX records
    Saved: XXXX records

WORLD SPORTS DATA COLLECTION COMPLETE
Total records: XXXX
```

**CRITÉRIOS DE SUCESSO:**
- ✅ `saved >= 1` para pelo menos 1 fonte (WHO, Eurostat, ou World Bank)
- ✅ Exit code = 0
- ✅ Nenhum `SyntaxError` ou `NameError` nos logs
- ✅ Se `ERROR:` aparecer, deve mostrar mensagem descritiva (não mais silencioso)

---

## FASE 3 — PROVA SQL (EXECUTAR NO SERVIDOR)

### **5. Conectar ao PostgreSQL**
```bash
psql postgresql://sofia:sofia123strong@91.98.158.19:5432/sofia_db
```

### **6. Verificar dados inseridos**
```sql
-- Query 1: Total de records
SELECT
  COUNT(*) as total_records,
  COUNT(DISTINCT source) as sources,
  COUNT(DISTINCT country_code) as countries,
  MAX(collected_at AT TIME ZONE 'America/Sao_Paulo') as latest_insert_brt
FROM sofia.world_sports_data;
```

**EXPECTED RESULT:**
```
 total_records | sources | countries |      latest_insert_brt
---------------+---------+-----------+-----------------------------
          XXXX |       3 |        XX | 2025-12-12 09:XX:XX.XXXXXX  (BRT)
```

**CRITÉRIO:** `total_records >= 1` (antes era 0)

---

```sql
-- Query 2: Breakdown por fonte
SELECT
  source,
  COUNT(*) as records,
  COUNT(DISTINCT country_code) as countries,
  COUNT(CASE WHEN country_id IS NOT NULL THEN 1 END) as with_country_fk,
  MIN(year) as min_year,
  MAX(year) as max_year
FROM sofia.world_sports_data
GROUP BY source
ORDER BY records DESC;
```

**EXPECTED RESULT:**
```
    source    | records | countries | with_country_fk | min_year | max_year
--------------+---------+-----------+-----------------+----------+----------
 World Bank   |   XXXX  |        XX |           XXXX  |     2010 |     2024
 WHO          |   XXXX  |        XX |           XXXX  |     2010 |     2022
 Eurostat     |     XX  |         1 |             XX  |     2022 |     2022
```

**CRITÉRIOS:**
- ✅ Cada fonte tem `records >= 1`
- ✅ `with_country_fk > 0` (foreign keys funcionando)

---

```sql
-- Query 3: Sample de dados reais
SELECT
  source,
  indicator_name,
  country_code,
  (SELECT common_name FROM sofia.countries WHERE id = wsd.country_id) as country_name,
  year,
  value
FROM sofia.world_sports_data wsd
WHERE collected_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
ORDER BY RANDOM()
LIMIT 10;
```

**EXPECTED RESULT:** 10 linhas com dados reais e country_name preenchido

---

```sql
-- Query 4: Verificar collector_runs
SELECT
  id,
  started_at AT TIME ZONE 'America/Sao_Paulo' as started_brt,
  completed_at AT TIME ZONE 'America/Sao_Paulo' as completed_brt,
  status,
  records_inserted,
  error_message,
  EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_sec
FROM sofia.collector_runs
WHERE collector_name = 'world-sports'
ORDER BY started_at DESC
LIMIT 5;
```

**EXPECTED RESULT:**
```
  id  |       started_brt        |      completed_brt       | status  | records_inserted | error_message | duration_sec
------+--------------------------+--------------------------+---------+------------------+---------------+--------------
 XXXX | 2025-12-12 09:XX:XX.XXX  | 2025-12-12 09:XX:XX.XXX  | success |           XXXX   |               |     XX.XXX
```

**CRITÉRIOS DE ACEITAÇÃO FINAL:**
- ✅ `status = 'success'`
- ✅ `records_inserted >= 1` (antes era 0)
- ✅ `error_message IS NULL`
- ✅ Timestamps em BRT (America/Sao_Paulo)
- ✅ `duration_sec < 180` (dentro do timeout)

---

## TROUBLESHOOTING

### Se ainda salvar 0 records:

**1. Verificar erros nos logs:**
```bash
grep "ERROR saving" /tmp/world-sports-verification.log
```

**2. Verificar se normalize_location() funciona:**
```python
# No servidor Python
from shared.geo_helpers import normalize_location
import psycopg2

conn = psycopg2.connect(...)
location = normalize_location(conn, {"country": "BRA"})
print(location)  # Deve retornar {'country_id': XX, 'city_id': None, ...}
```

**3. Verificar UNIQUE constraint:**
```sql
-- Se já tiver dados antigos, INSERT pode estar sendo bloqueado por UNIQUE
SELECT source, indicator_code, country_code, sex, year, COUNT(*)
FROM sofia.world_sports_data
GROUP BY source, indicator_code, country_code, sex, year
HAVING COUNT(*) > 1;
```

**4. Verificar transação:**
```python
# No código Python, confirmar que tem:
conn.commit()  # Linha 338, 381, 457
```

---

## RESULTADO ESPERADO FINAL

**ANTES (com bugs):**
- Fetched: ~189,000 records
- Saved: 0 records
- Status: failed (ou success indevido)
- Errors: silenciosos

**DEPOIS (com correções):**
- Fetched: ~189,000 records
- Saved: >= 1 record (idealmente milhares)
- Status: success
- Errors: logged (primeiros 3 de cada seção)
- collector_runs: status=success, records_inserted >= 1
- Foreign keys: country_id preenchido para registros válidos

---

## COMANDOS RÁPIDOS (COPIAR/COLAR NO SERVIDOR)

```bash
# 1. Pull + Run
cd ~/sofia-pulse
git pull
timeout 180 python3 scripts/collect-world-sports.py 2>&1 | tee /tmp/world-sports-verification.log
echo "Exit code: $?"

# 2. Ver métricas
tail -30 /tmp/world-sports-verification.log | grep -E "Fetched:|Saved:|Total|Exit"

# 3. SQL Verification
psql postgresql://sofia:sofia123strong@localhost:5432/sofia_db -c "
SELECT
  COUNT(*) as total,
  MAX(collected_at AT TIME ZONE 'America/Sao_Paulo') as latest_brt
FROM sofia.world_sports_data
WHERE collected_at >= CURRENT_TIMESTAMP - INTERVAL '10 minutes';
"

# 4. Collector runs
psql postgresql://sofia:sofia123strong@localhost:5432/sofia_db -c "
SELECT status, records_inserted, error_message
FROM sofia.collector_runs
WHERE collector_name = 'world-sports'
ORDER BY started_at DESC LIMIT 1;
"
```

---

**Status:** ✅ CÓDIGO CORRIGIDO - Aguardando execução no servidor para FASE 3
**Próximo:** Executar comandos acima no servidor de produção
