# SPORTS-REGIONAL + WOMEN-BRAZIL VERIFICATION PROTOCOL

**Date:** 2025-12-12 15:00 UTC
**Status:** ✅ FASE 2 COMPLETA - Correções aplicadas
**Commit:** f7f210b
**Collectors Fixed:** 2 (sports-regional, women-brazil)

---

## ✅ FASE 1 - AUTOPSIA (COMPLETA)

### **Causa Raiz (Ambos Collectors):**

**"Estes collectors falharam por erro nosso."**

### **Padrão de Bugs (Idêntico em Ambos):**

#### **Bug #1: Tuple Wrapping**
```python
# ANTES:
location = (normalize_location(conn, {"country": country_code}),)  # ❌ TUPLA

# DEPOIS:
location = normalize_location(conn, {"country": country_code})  # ✅ DICT
```

**Impacto:** `location["country_id"]` causa `TypeError: tuple indices must be integers`

---

#### **Bug #2: SQL Malformado**
```python
# ANTES:
cursor.execute(
    """,  # ❌ Vírgula antes de INSERT
    INSERT INTO ...
    ON CONFLICT (...),  # ❌ Vírgula extra
    DO UPDATE ...                        """,  # ❌ Espaços estranhos
)

# DEPOIS:
cursor.execute(
    """
    INSERT INTO ...
    ON CONFLICT (...)
    DO UPDATE SET ..., country_id = EXCLUDED.country_id
    """,
)
```

---

#### **Bug #3: country_id Fora de Escopo**

**sports-regional.py:**
- Definido apenas na linha 772 (bloco regional_federations)
- Usado nas linhas 806, 834, 860 (blocos diferentes: regional_data, rankings, disciplines)

**women-brazil.py:**
- Usado na linha 327 (função save_ipea) mas nunca definido
- Usado na linha 461 (bloco DataSUS) mas nunca definido

---

#### **Bug #4: Silent Exceptions**
```python
# ANTES:
except:
    continue  # ❌ SILENT

# DEPOIS:
except Exception as e:
    errors += 1
    if errors <= 3:
        print(f"      ERROR: {str(e)[:100]}")
    continue  # ✅ LOGGED
```

---

## ✅ FASE 2 - CORREÇÃO (COMPLETA)

### **1. collect-sports-regional.py**

**Blocos Corrigidos:** 4

#### **Bloco 1: regional_federations (linhas 768-784)**
- ✅ Removido tuple wrapping
- ✅ Fixado SQL malformado
- ✅ Adicionado error logging

#### **Bloco 2: regional_data (linhas 789-817)**
- ✅ Adicionado normalização de country_code
- ✅ Definido country_id dentro do loop
- ✅ Fixado SQL + error logging

#### **Bloco 3: rankings (linhas 818-853)**
- ✅ Adicionado normalização de country_code
- ✅ Definido country_id dentro do loop
- ✅ Fixado SQL + error logging

#### **Bloco 4: disciplines (linhas 844-865)**
- ✅ Adicionado normalização de country_code
- ✅ Definido country_id dentro do loop
- ✅ Fixado SQL + error logging

**Mudanças Totais:**
- +1 linha: `errors = 0` (contador)
- +4 blocos: normalização de country_id
- +4 blocos: error logging
- ~16 linhas alteradas: SQL fixado

---

### **2. collect-women-brazil.py**

**Blocos Corrigidos:** 3

#### **Bloco 1: save_ibge_to_database (linhas 221-253)**
- ✅ Removido tuple wrapping
- ✅ Fixado SQL malformado
- ✅ Adicionado error logging
- ✅ Mudado `.get()` para evitar KeyError

#### **Bloco 2: save_ipea_to_database (linhas 294-332)**
- ✅ Adicionado normalização de Brazil no início da função
- ✅ Definido country_id antes do loop
- ✅ Fixado SQL + error logging

#### **Bloco 3: main() - DataSUS (linhas 433-466)**
- ✅ Adicionado normalização de Brazil antes do loop
- ✅ Definido country_id
- ✅ Fixado SQL + error logging

**Mudanças Totais:**
- +3 linhas: `errors = 0` (contadores)
- +2 blocos: normalização de Brazil
- +3 blocos: error logging
- ~12 linhas alteradas: SQL fixado

---

## ⏳ FASE 3 — PROVA DE VIDA (EXECUTAR NO SERVIDOR)

### **1. SSH para o servidor**
```bash
ssh ubuntu@91.98.158.19
cd ~/sofia-pulse
```

### **2. Pull das correções**
```bash
git fetch
git pull origin master
```

### **3. Executar collectors com timeout**

#### **sports-regional:**
```bash
timeout 180 python3 scripts/collect-sports-regional.py 2>&1 | tee /tmp/sports-regional-verification.log
echo "Exit code: $?"
```

**EXPECTED OUTPUT:**
```
================================================================================
REGIONAL SPORTS DATA COLLECTOR
================================================================================

Time: 2025-12-12 12:XX:XX

Sports covered:
  • Football (Soccer)
  • Basketball
  • Volleyball
  ...

Total records saved: XXX
```

---

#### **women-brazil:**
```bash
timeout 180 python3 scripts/collect-women-brazil.py 2>&1 | tee /tmp/women-brazil-verification.log
echo "Exit code: $?"
```

**EXPECTED OUTPUT:**
```
================================================================================
BRAZILIAN WOMEN'S DATA - IBGE, IPEA, DATASUS
================================================================================

Time: 2025-12-12 12:XX:XX
Sources:
  - IBGE SIDRA: https://sidra.ibge.gov.br/
  - IPEA: http://www.ipeadata.gov.br/
  - DataSUS: http://datasus.saude.gov.br/

IBGE Tables: X
IPEA Series: X

--- IBGE SIDRA ---
  Table 1234: Mulheres no mercado de trabalho...
    Fetched: XX records
    Saved: XX records

--- IPEA ---
  Series ABC: Taxa de participacao feminina...
    Fetched: XX records
    Saved: XX records

--- VIOLENCE DATA ---
  Maternal mortality (World Bank)...
    Fetched: XX records

Total records: XXX
```

---

### **4. Verificar logs**
```bash
# sports-regional
tail -50 /tmp/sports-regional-verification.log
grep -E "Fetched:|Saved:|ERROR" /tmp/sports-regional-verification.log

# women-brazil
tail -50 /tmp/women-brazil-verification.log
grep -E "Fetched:|Saved:|ERROR" /tmp/women-brazil-verification.log
```

**CRITÉRIOS DE SUCESSO:**
- ✅ Exit code = 0
- ✅ `Saved >= 1` para pelo menos 1 fonte
- ✅ Nenhum `TypeError` ou `KeyError` nos logs
- ✅ Se `ERROR:` aparecer, deve mostrar mensagem descritiva (não mais silencioso)

---

## ⏳ FASE 3 — PROVA SQL (EXECUTAR NO SERVIDOR)

### **5. Conectar ao PostgreSQL**
```bash
psql postgresql://sofia:sofia123strong@91.98.158.19:5432/sofia_db
```

### **6. Verificar sports-regional**

```sql
-- Query 1: Total de records
SELECT
  COUNT(*) as total_records,
  COUNT(DISTINCT sport) as sports,
  COUNT(DISTINCT country_code) as countries,
  COUNT(CASE WHEN country_id IS NOT NULL THEN 1 END) as with_country_fk,
  MAX(collected_at AT TIME ZONE 'America/Sao_Paulo') as latest_insert_brt
FROM sofia.sports_regional;
```

**EXPECTED RESULT:**
```
 total_records | sports | countries | with_country_fk |      latest_insert_brt
---------------+--------+-----------+-----------------+-----------------------------
          XXXX |     17 |       100 |            XXXX | 2025-12-12 12:XX:XX.XXXXXX
```

**CRITÉRIO:** `total_records >= 1` (antes era 0)

---

```sql
-- Query 2: Breakdown por esporte
SELECT
  sport,
  COUNT(*) as countries_count,
  COUNT(CASE WHEN country_id IS NOT NULL THEN 1 END) as with_fk
FROM sofia.sports_regional
GROUP BY sport
ORDER BY countries_count DESC
LIMIT 10;
```

**EXPECTED RESULT:**
```
    sport     | countries_count | with_fk
--------------+-----------------+---------
 Football     |              50 |      50
 Basketball   |              40 |      40
 Cricket      |              35 |      35
 ...
```

---

### **7. Verificar women-brazil**

```sql
-- Query 1: Total de records
SELECT
  COUNT(*) as total_records,
  COUNT(DISTINCT source) as sources,
  COUNT(DISTINCT indicator_code) as indicators,
  COUNT(CASE WHEN country_id IS NOT NULL THEN 1 END) as with_country_fk,
  MAX(collected_at AT TIME ZONE 'America/Sao_Paulo') as latest_insert_brt
FROM sofia.women_brazil_data;
```

**EXPECTED RESULT:**
```
 total_records | sources | indicators | with_country_fk |      latest_insert_brt
---------------+---------+------------+-----------------+-----------------------------
          XXXX |       3 |         XX |            XXXX | 2025-12-12 12:XX:XX.XXXXXX
```

**CRITÉRIO:** `total_records >= 1` (antes era 0)

---

```sql
-- Query 2: Breakdown por fonte
SELECT
  source,
  COUNT(*) as records,
  COUNT(DISTINCT indicator_code) as indicators,
  COUNT(CASE WHEN country_id IS NOT NULL THEN 1 END) as with_fk,
  MIN(period) as oldest_period,
  MAX(period) as latest_period
FROM sofia.women_brazil_data
GROUP BY source
ORDER BY records DESC;
```

**EXPECTED RESULT:**
```
   source    | records | indicators | with_fk | oldest_period | latest_period
-------------+---------+------------+---------+---------------+---------------
 IBGE        |    XXXX |         XX |    XXXX | 2000          | 2024
 IPEA        |    XXXX |         XX |    XXXX | 2000          | 2024
 World Bank  |      XX |          1 |      XX | 2000          | 2024
```

**CRITÉRIOS:**
- ✅ Cada fonte tem `records >= 1`
- ✅ `with_fk > 0` (foreign keys funcionando)

---

### **8. Verificar collector_runs**

```sql
-- sports-regional
SELECT
  id,
  started_at AT TIME ZONE 'America/Sao_Paulo' as started_brt,
  completed_at AT TIME ZONE 'America/Sao_Paulo' as completed_brt,
  status,
  records_inserted,
  error_message
FROM sofia.collector_runs
WHERE collector_name = 'sports-regional'
ORDER BY started_at DESC
LIMIT 3;
```

```sql
-- women-brazil
SELECT
  id,
  started_at AT TIME ZONE 'America/Sao_Paulo' as started_brt,
  completed_at AT TIME ZONE 'America/Sao_Paulo' as completed_brt,
  status,
  records_inserted,
  error_message
FROM sofia.collector_runs
WHERE collector_name = 'women-brazil'
ORDER BY started_at DESC
LIMIT 3;
```

**EXPECTED RESULT (ambos):**
```
  id  |       started_brt        |      completed_brt       | status  | records_inserted | error_message
------+--------------------------+--------------------------+---------+------------------+---------------
 XXXX | 2025-12-12 12:XX:XX.XXX  | 2025-12-12 12:XX:XX.XXX  | success |            XXXX  |
```

**CRITÉRIOS DE ACEITAÇÃO FINAL:**
- ✅ `status = 'success'`
- ✅ `records_inserted >= 1` (antes era 0)
- ✅ `error_message IS NULL`
- ✅ Timestamps em BRT

---

## 📊 RESULTADO ESPERADO FINAL

| Collector | Antes (com bugs) | Esperado Após Fix |
|-----------|------------------|-------------------|
| **sports-regional** | | |
| Fetched | Unknown | ~500+ (17 sports × 30+ countries) |
| Saved | **0** ❌ | **>= 100** ✅ |
| Status | failed | **success** ✅ |
| **women-brazil** | | |
| Fetched | Unknown | ~200+ (IBGE + IPEA + DataSUS) |
| Saved | **0** ❌ | **>= 100** ✅ |
| Status | failed | **success** ✅ |

---

## 📝 COMANDOS RÁPIDOS (COPIAR/COLAR NO SERVIDOR)

```bash
# 1. Pull + Run sports-regional
cd ~/sofia-pulse
git pull
timeout 180 python3 scripts/collect-sports-regional.py 2>&1 | tee /tmp/sports-regional-verification.log
echo "Exit code: $?"

# 2. Run women-brazil
timeout 180 python3 scripts/collect-women-brazil.py 2>&1 | tee /tmp/women-brazil-verification.log
echo "Exit code: $?"

# 3. SQL Verification - sports-regional
psql postgresql://sofia:sofia123strong@localhost:5432/sofia_db -c "
SELECT COUNT(*) as total, MAX(collected_at AT TIME ZONE 'America/Sao_Paulo') as latest_brt
FROM sofia.sports_regional
WHERE collected_at >= CURRENT_TIMESTAMP - INTERVAL '10 minutes';"

# 4. SQL Verification - women-brazil
psql postgresql://sofia:sofia123strong@localhost:5432/sofia_db -c "
SELECT COUNT(*) as total, MAX(collected_at AT TIME ZONE 'America/Sao_Paulo') as latest_brt
FROM sofia.women_brazil_data
WHERE collected_at >= CURRENT_TIMESTAMP - INTERVAL '10 minutes';"
```

---

**Status Atual:**
- ✅ **FASE 1 (Autopsia):** Complete - 4 tipos de bugs identificados em cada collector
- ✅ **FASE 2 (Correction):** Complete - All bugs fixed in commit f7f210b
- ⏳ **FASE 3 (Proof of Life):** Aguardando execução no servidor

**Documentação:** `SPORTS-WOMEN-VERIFICATION.md` (this file)
**Commit:** f7f210b - fix: sports-regional + women-brazil collectors
