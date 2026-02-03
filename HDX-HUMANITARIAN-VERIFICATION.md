# HDX-HUMANITARIAN COLLECTOR - VERIFICATION PROTOCOL

**Date:** 2025-12-12 13:00 UTC
**Status:** ✅ FASE 2 COMPLETA - Correções aplicadas
**Commit:** 1759f8d
**Situation:** 61 datasets found, 0 saved → Fixed

---

## ✅ FASE 1 - AUTOPSIA (COMPLETA)

### **Causa Raiz:**

**"Este collector falhou por erro nosso."**

### **Bugs Identificados:**

#### **BUG #1: Invalid Python Syntax - Linha 153**
```python
# ANTES:
dataset.get("id", "", country_id=EXCLUDED.country_id)  # ❌ SyntaxError

# DEPOIS:
dataset.get("id", "")  # ✅ CORRETO
```

**Impacto:** Python parser rejeita esta linha imediatamente

---

#### **BUG #2: Missing 15th Parameter - Linhas 143-167**
```python
# ANTES:
INSERT INTO sofia.hdx_humanitarian_data (..., country_id)  # 15 colunas
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)  # ❌ 14 valores

# DEPOIS:
INSERT INTO sofia.hdx_humanitarian_data (..., country_id)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)  # ✅ 15 valores

# Adicionado:
country_id = None  # HDX datasets são multi-país
(..., country_id)  # 15º parâmetro
```

---

#### **BUG #3: Silent Errors - Linha 170**
```python
# ANTES:
except Exception:
    continue  # ❌ Erro silencioso

# DEPOIS:
except Exception as e:
    errors += 1
    if errors <= 3:  # Log primeiros 3 erros
        print(f"❌ ERROR inserting dataset {dataset.get('id', 'unknown')[:20]}: {str(e)[:100]}")
    continue  # ✅ Com logging
```

---

### **Fluxo do Bug:**
1. HDX API retorna 61 datasets ✅
2. Loop entra em `save_to_database()` ✅
3. Linha 153: `SyntaxError` em dict.get() ❌
4. Exception capturada silenciosamente ❌
5. Loop continua, `inserted` permanece 0 ❌
6. Retorna 0, usuário vê "61 found, 0 saved" ❌

---

## ✅ FASE 2 - CORREÇÃO (COMPLETA)

### **Correções Aplicadas:**

1. ✅ **Removido invalid syntax** (linha 153)
   - `dataset.get("id", "", country_id=...)` → `dataset.get("id", "")`

2. ✅ **Adicionado 15º parâmetro** (linhas 139-167)
   - `country_id = None` (HDX datasets são multi-país, não faz sentido foreign key único)
   - Adicionado `country_id` na tupla VALUES (posição 15)

3. ✅ **Error logging** (linha 170)
   - `except Exception:` → `except Exception as e:`
   - Log dos primeiros 3 erros com mensagem descritiva

4. ✅ **ON CONFLICT atualizado** (linha 155)
   - Adicionado `country_id = EXCLUDED.country_id`

### **Nota sobre country_id:**

HDX datasets são **multi-país** (ex: "Global Food Security Report" cobre 50+ países). O campo `country_codes` (array) já armazena todos os países. Usar `country_id` (foreign key único) não faria sentido semântico.

**Decisão:** `country_id = None` para todos os datasets HDX.

Se futuramente necessário normalizar por país principal:
```python
# Opção 1: Primeiro país do array
if countries:
    location = normalize_location(conn, {"country": countries[0]})
    country_id = location.get("country_id")

# Opção 2: País da organização (ex: UNHCR → Switzerland)
# Requer mapeamento manual org → HQ country
```

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

### **3. Executar collector com timeout**
```bash
# Executar com timeout de 3 minutos
timeout 180 python3 scripts/collect-hdx-humanitarian.py 2>&1 | tee /tmp/hdx-humanitarian-verification.log

# Capturar exit code
echo "Exit code: $?"
```

### **4. Verificar logs**
```bash
# Ver últimas 50 linhas
tail -50 /tmp/hdx-humanitarian-verification.log

# Buscar por métricas chave
grep -E "Found:|Saved:|ERROR" /tmp/hdx-humanitarian-verification.log
```

**EXPECTED OUTPUT:**
```
================================================================================
📊 HDX - Humanitarian Data Exchange
================================================================================

⏰ Time: 2025-12-12 10:XX:XX
📡 Source: https://data.humdata.org/

✅ Database connected

📊 Fetching humanitarian datasets...

🏢 By Organization:
   📈 UNHCR...
      ✅ Found: 30 datasets
      💾 Saved: 30 datasets
   📈 OCHA...
      ✅ Found: 30 datasets
      💾 Saved: 30 datasets
   ...

🏷️  By Tag:
   📈 refugees...
      ✅ Found: 20 datasets
      💾 Saved: XX datasets (some duplicates)
   ...

================================================================================
✅ HDX HUMANITARIAN COLLECTION COMPLETE
================================================================================
💾 Total dataset records: XX
```

**CRITÉRIOS DE SUCESSO:**
- ✅ `Saved >= 1` para pelo menos 1 organização ou tag
- ✅ Exit code = 0
- ✅ Nenhum `SyntaxError` ou `IndexError` nos logs
- ✅ Se `ERROR:` aparecer, deve mostrar mensagem descritiva

---

## ⏳ FASE 3 — PROVA SQL (EXECUTAR NO SERVIDOR)

### **5. Conectar ao PostgreSQL**
```bash
psql postgresql://sofia:sofia123strong@91.98.158.19:5432/sofia_db
```

### **6. Verificar dados inseridos**

#### **Query 1: Total de datasets**
```sql
SELECT
  COUNT(*) as total_datasets,
  COUNT(DISTINCT organization) as organizations,
  COUNT(DISTINCT source) as sources,
  MAX(collected_at AT TIME ZONE 'America/Sao_Paulo') as latest_insert_brt,
  MIN(date_created) as oldest_dataset,
  MAX(date_modified) as newest_dataset
FROM sofia.hdx_humanitarian_data;
```

**EXPECTED RESULT:**
```
 total_datasets | organizations | sources |      latest_insert_brt       |   oldest_dataset    |   newest_dataset
----------------+---------------+---------+------------------------------+---------------------+---------------------
             XX |             7 |      14 | 2025-12-12 10:XX:XX.XXXXXX  | 2015-XX-XX XX:XX:XX | 2025-XX-XX XX:XX:XX
```

**CRITÉRIO:** `total_datasets >= 1` (antes era 0)

---

#### **Query 2: Breakdown por organização**
```sql
SELECT
  organization,
  COUNT(*) as datasets,
  SUM(num_resources) as total_resources,
  SUM(total_downloads) as total_downloads,
  COUNT(DISTINCT dataset_id) as unique_datasets
FROM sofia.hdx_humanitarian_data
GROUP BY organization
ORDER BY datasets DESC;
```

**EXPECTED RESULT:**
```
 organization | datasets | total_resources | total_downloads | unique_datasets
--------------+----------+-----------------+-----------------+-----------------
 UNHCR        |       XX |             XXX |          XXXXX  |              XX
 OCHA         |       XX |             XXX |          XXXXX  |              XX
 WFP          |       XX |             XXX |          XXXXX  |              XX
 MSF          |       XX |             XXX |          XXXXX  |              XX
 ...
```

**CRITÉRIO:** Pelo menos 1 organização com `datasets >= 1`

---

#### **Query 3: Sample de datasets reais**
```sql
SELECT
  dataset_id,
  title,
  organization,
  ARRAY_LENGTH(tags, 1) as num_tags,
  ARRAY_LENGTH(country_codes, 1) as num_countries,
  num_resources,
  total_downloads,
  date_modified
FROM sofia.hdx_humanitarian_data
WHERE collected_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
ORDER BY total_downloads DESC NULLS LAST
LIMIT 10;
```

**EXPECTED RESULT:** 10 linhas com dados reais de datasets humanitários

**Exemplo:**
```
dataset_id              | title                                          | organization | num_tags | num_countries | num_resources | total_downloads
------------------------+------------------------------------------------+--------------+----------+---------------+---------------+----------------
d4c6b...               | UNHCR Refugee Data Finder                      | UNHCR        |        5 |           150 |            25 |          15000
a2f8e...               | Syria Humanitarian Needs Overview 2024         | OCHA         |        8 |             1 |            12 |           8500
...
```

---

#### **Query 4: Tags mais comuns**
```sql
SELECT
  UNNEST(tags) as tag,
  COUNT(*) as datasets_count
FROM sofia.hdx_humanitarian_data
GROUP BY tag
ORDER BY datasets_count DESC
LIMIT 15;
```

**EXPECTED TAGS:**
- refugees
- internally displaced persons-idp
- humanitarian needs overview-hno
- food security
- conflict-violence
- migration
- health
- education
- wash
- protection

---

#### **Query 5: Verificar collector_runs**
```sql
SELECT
  id,
  started_at AT TIME ZONE 'America/Sao_Paulo' as started_brt,
  completed_at AT TIME ZONE 'America/Sao_Paulo' as completed_brt,
  status,
  records_inserted,
  records_updated,
  error_message,
  EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_sec
FROM sofia.collector_runs
WHERE collector_name = 'hdx-humanitarian'
ORDER BY started_at DESC
LIMIT 5;
```

**EXPECTED RESULT:**
```
  id  |       started_brt        |      completed_brt       | status  | records_inserted | records_updated | error_message | duration_sec
------+--------------------------+--------------------------+---------+------------------+-----------------+---------------+--------------
 XXXX | 2025-12-12 10:XX:XX.XXX  | 2025-12-12 10:XX:XX.XXX  | success |              XX  |               0 |               |     XX.XXX
```

**CRITÉRIOS DE ACEITAÇÃO FINAL:**
- ✅ `status = 'success'`
- ✅ `records_inserted >= 1` (antes era 0)
- ✅ `error_message IS NULL`
- ✅ Timestamps em BRT (America/Sao_Paulo)
- ✅ `duration_sec < 180` (dentro do timeout)

---

## 🔧 TROUBLESHOOTING

### **Se ainda salvar 0 records:**

#### **1. Verificar erros nos logs:**
```bash
grep "ERROR inserting" /tmp/hdx-humanitarian-verification.log
```

Se houver erros, investigar:
- Schema mismatch (coluna faltando?)
- Constraint violation (UNIQUE dataset_id?)
- Data type mismatch (array vs string?)

---

#### **2. Testar manualmente uma inserção:**
```sql
-- Inserir dataset de teste
INSERT INTO sofia.hdx_humanitarian_data (
    dataset_id, dataset_name, title, organization, source,
    tags, country_codes, num_resources, total_downloads, country_id
) VALUES (
    'test-12345',
    'test-dataset',
    'Test Humanitarian Dataset',
    'TEST',
    'TEST',
    ARRAY['test', 'humanitarian'],
    ARRAY['BRA', 'USA'],
    5,
    1000,
    NULL
);

-- Verificar
SELECT * FROM sofia.hdx_humanitarian_data WHERE dataset_id = 'test-12345';

-- Limpar
DELETE FROM sofia.hdx_humanitarian_data WHERE dataset_id = 'test-12345';
```

---

#### **3. Verificar HDX API diretamente:**
```bash
# Test UNHCR endpoint
curl -s "https://data.humdata.org/api/3/action/package_search?fq=organization:unhcr&rows=5" | jq '.result.count, .result.results[0].title'

# Expected output:
# 800+ (total datasets)
# "Title of first UNHCR dataset"
```

Se API retornar vazio: **BLOCKED EXTERNAL** (HDX API down ou rate limited)

---

#### **4. Verificar se datasets já existem (duplicates):**
```sql
-- Se já houver 200 datasets no banco, ON CONFLICT vai UPDATE ao invés de INSERT
-- Isso é CORRETO (idempotência), mas records_inserted será 0

SELECT COUNT(*) as existing_datasets
FROM sofia.hdx_humanitarian_data;

-- Se existing_datasets > 0, rodar collector novamente deve UPDATE ao invés de INSERT
-- Para forçar INSERT, deletar registros antigos:
-- TRUNCATE TABLE sofia.hdx_humanitarian_data;  -- ⚠️ CUIDADO: apaga tudo
```

---

## 📊 COMANDOS RÁPIDOS (COPIAR/COLAR NO SERVIDOR)

```bash
# 1. Pull + Run
cd ~/sofia-pulse
git pull
timeout 180 python3 scripts/collect-hdx-humanitarian.py 2>&1 | tee /tmp/hdx-humanitarian-verification.log
echo "Exit code: $?"

# 2. Ver métricas
tail -40 /tmp/hdx-humanitarian-verification.log | grep -E "Found:|Saved:|Total|Exit"

# 3. SQL Verification - Total datasets
psql postgresql://sofia:sofia123strong@localhost:5432/sofia_db -c "
SELECT
  COUNT(*) as total,
  MAX(collected_at AT TIME ZONE 'America/Sao_Paulo') as latest_brt
FROM sofia.hdx_humanitarian_data
WHERE collected_at >= CURRENT_TIMESTAMP - INTERVAL '10 minutes';
"

# 4. SQL Verification - By organization
psql postgresql://sofia:sofia123strong@localhost:5432/sofia_db -c "
SELECT organization, COUNT(*) as datasets
FROM sofia.hdx_humanitarian_data
GROUP BY organization
ORDER BY datasets DESC;
"

# 5. Collector runs
psql postgresql://sofia:sofia123strong@localhost:5432/sofia_db -c "
SELECT status, records_inserted, error_message
FROM sofia.collector_runs
WHERE collector_name = 'hdx-humanitarian'
ORDER BY started_at DESC LIMIT 1;
"
```

---

## 📋 RESULTADO ESPERADO FINAL

| Métrica | Antes (com bugs) | Esperado Após Fix |
|---------|------------------|-------------------|
| Datasets Found | 61 | 61 (unchanged) |
| Datasets Saved | **0** ❌ | **>= 1** ✅ |
| Status | failed | **success** ✅ |
| Exit code | != 0 | **0** ✅ |
| Errors | Silent | **Logged** ✅ |
| collector_runs | status=failed | **status=success** ✅ |

---

## 📚 ESPECIFICAÇÕES TÉCNICAS

### **API Endpoints:**
- **Base:** `https://data.humdata.org/api/3/action/package_search`
- **By organization:** `?fq=organization:{org}&rows=30&sort=metadata_modified desc`
- **By tag:** `?fq=tags:{tag}&rows=20&sort=metadata_modified desc`

### **Organizações Coletadas:**
1. UNHCR (UN Refugee Agency) - Refugees, asylum seekers
2. OCHA (Humanitarian Affairs) - Humanitarian needs, crises
3. WFP (World Food Programme) - Food security, hunger
4. MSF (Médecins Sans Frontières) - Medical emergencies
5. UNICEF - Children, education, health
6. ICRC (Red Cross) - Conflict zones, protection
7. IOM (Migration) - Migrants, displaced persons

### **Tags Coletadas:**
- refugees
- internally-displaced-persons (IDPs)
- humanitarian-needs-overview (HNO)
- food-security
- conflict
- migration
- health

### **Campos Armazenados:**
- **dataset_id** (UNIQUE key)
- **title, dataset_name** (metadata)
- **organization, source** (attribution)
- **tags** (TEXT[] array)
- **country_codes** (TEXT[] array, ISO 3-letter)
- **date_created, date_modified** (timestamps)
- **num_resources** (count of files/APIs)
- **total_downloads** (popularity metric)
- **methodology, notes** (documentation)
- **url** (link to HDX platform)

---

**Status Atual:**
- ✅ **FASE 1 (Autopsia):** Complete - 3 bugs identificados
- ✅ **FASE 2 (Correction):** Complete - All bugs fixed in commit 1759f8d
- ⏳ **FASE 3 (Proof of Life):** Aguardando execução no servidor

**Arquivo de Verificação:** `HDX-HUMANITARIAN-VERIFICATION.md` (this file)
**Commit:** 1759f8d - fix: hdx-humanitarian collector
