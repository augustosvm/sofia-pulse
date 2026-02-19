# FIX ERROR_CODE VARCHAR(80) - Resumo Executivo

**Data:** 2026-02-19
**Problema:** Registros ficando presos em status='running' por truncamento de error_code
**Status:** ✅ RESOLVIDO

---

## 📊 PROBLEMA IDENTIFICADO

### Sintoma
```
psycopg2.errors.StringDataRightTruncation: value too long for type character varying(80)
```

### Root Cause
- Coluna `error_code VARCHAR(80)` muito pequena para mensagens de erro longas
- Quando tracked_runner.py tentava fazer UPDATE final, falhava por truncamento
- Registro ficava preso em status='running' permanentemente

### Exemplo de Erro Longo
```
requests.exceptions.ConnectTimeout: HTTPConnectionPool(host='91.98.158.19', port=3001):
Max retries exceeded with url: /send (Caused by ConnectTimeoutError(...))
```
**Comprimento:** 120+ caracteres (excede VARCHAR(80))

---

## 🔧 CORREÇÃO APLICADA

### 1. Aumentar error_code de VARCHAR(80) → VARCHAR(500)

```sql
BEGIN;

ALTER TABLE sofia.collector_runs
  ALTER COLUMN error_code TYPE VARCHAR(500);

COMMIT;
```

**Resultado:**
```
✅ error_code: VARCHAR(80) → VARCHAR(500)
✅ error_message: TEXT (já estava correto)
```

---

## 🧪 VALIDAÇÃO

### Teste Prático - Execução de Collector

**Antes do fix:**
```
id=1049 | status='running' | ok=NULL | saved=NULL | completed_at=NULL
```
❌ Ficou preso em 'running' (UPDATE falhou por truncamento)

**Depois do fix:**
```
id=1050 | status='failed' | ok=false | saved=0 | completed_at='00:50:58' | duration_ms=11040
```
✅ Finalizou corretamente (UPDATE funcionou, error_code com 120 chars coube no VARCHAR(500))

---

## 🧹 LIMPEZA DE ZUMBIS

### Registros Antigos Presos em 'running'

**Comando executado:**
```sql
UPDATE sofia.collector_runs
SET
  status = 'failed',
  ok = FALSE,
  saved = COALESCE(saved, 0),
  duration_ms = COALESCE(duration_ms, 86400000),  -- 24h em ms
  completed_at = COALESCE(completed_at, NOW()),
  error_code = COALESCE(error_code, 'tracking_finalize_failed')
WHERE status = 'running'
  AND started_at < NOW() - INTERVAL '30 minutes';
```

**Resultado:**
- ✅ **50 registros zumbis curados**
- ✅ **0 zumbis restantes** (running > 30 min)
- ✅ Todos marcados como 'failed' com error_code='tracking_finalize_failed'

---

## 📈 ANTES vs DEPOIS

| Métrica | ANTES | DEPOIS |
|---------|-------|--------|
| error_code max length | VARCHAR(80) | VARCHAR(500) ✅ |
| Registros presos em 'running' | 50+ | 0 ✅ |
| Falha ao finalizar tracking | Sim ❌ | Não ✅ |
| Collector finalizando corretamente | Não ❌ | Sim ✅ |

---

## 🎯 RESULTADO FINAL

### Schema Atualizado
```
error_code    | VARCHAR(500) ✅
error_message | TEXT         ✅
```

### Status do Sistema (últimas 24h)
```
status='success'   : 20 (57.1%) - registros ANTES do patch NO_TRACKING (legacy)
status='failed'    :  9 (25.7%) - inclui zumbis curados + falhas reais
status='completed' :  5 (14.3%) - registros APÓS patch NO_TRACKING
status='running'   :  1 ( 2.9%) - execução atual (< 30 min) ✅ NORMAL
```

### Últimas Execuções
```
id=1050 | jobs-adzuna | status='failed' | ok=false | saved=0 | duration_ms=11040
   ✅ Finalizou corretamente mesmo com erro
   ✅ error_code completo salvo (120 chars)
   ✅ Todos campos preenchidos (ok, saved, duration_ms, completed_at)
```

---

## 🔍 MONITORAMENTO CONTÍNUO

### Query de Verificação
```sql
-- Verificar se registros estão finalizando corretamente
SELECT
  id,
  collector_name,
  status,
  ok,
  saved,
  length(coalesce(error_code,'')) as error_code_len,
  duration_ms,
  started_at,
  completed_at
FROM sofia.collector_runs
WHERE started_at >= NOW() - INTERVAL '1 hour'
ORDER BY started_at DESC;
```

### Alertas Sugeridos
```sql
-- Detectar novos zumbis (executar a cada hora)
SELECT COUNT(*) as zombie_alert
FROM sofia.collector_runs
WHERE status = 'running'
  AND started_at < NOW() - INTERVAL '30 minutes';
```

**Resultado esperado:** 0 rows (nenhum zumbi)

---

## 📝 PRÓXIMOS PASSOS

1. ✅ **CONCLUÍDO** - error_code aumentado para VARCHAR(500)
2. ✅ **CONCLUÍDO** - 50 zumbis curados
3. ✅ **CONCLUÍDO** - Validado com execução real
4. ⏳ **MONITORAR** - Próximas 24h para confirmar estabilidade
5. ⏳ **OPCIONAL** - Investigar WhatsApp API timeout (91.98.158.19:3001)

---

## 🎯 CONCLUSÃO

**Problema resolvido com sucesso.**

- Schema de error_code expandido de VARCHAR(80) → VARCHAR(500)
- Registros agora finalizam corretamente mesmo com mensagens de erro longas
- 50 registros zumbis antigos foram curados
- Sistema estável e funcionando conforme esperado

**Combinado com patch NO_TRACKING anterior:**
- ✅ Tracking único (sem duplicatas)
- ✅ Finalização correta (sem zumbis)
- ✅ Dados completos (ok, saved, duration_ms preenchidos)

---

**Gerado:** 2026-02-19 00:52 UTC
**Por:** Claude Code (SRE/DevOps Engineer)
