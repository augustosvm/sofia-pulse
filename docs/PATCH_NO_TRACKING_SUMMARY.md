# PATCH NO_TRACKING - Resumo Executivo

**Data:** 2026-02-19
**Objetivo:** Eliminar tracking duplicado em collector_runs
**Status:** ✅ CONCLUÍDO COM SUCESSO

---

## 📊 RESULTADOS

### Antes do Patch
- **Problema:** Cada execução de collector criava 2 registros em `sofia.collector_runs`
  1. tracked_runner.py → status='completed', ok=true/false, saved=int ✅ CORRETO
  2. TypeScript legacy → status='success', ok=NULL, saved=NULL ❌ DUPLICADO

### Depois do Patch
- **Solução:** Apenas 1 registro por execução
  - tracked_runner.py → status='completed', ok=true/false, saved=int ✅ ÚNICO

### Evidência
```sql
-- Duplicatas nos últimos 10 minutos
SELECT collector_name, COUNT(*)
FROM sofia.collector_runs
WHERE started_at >= NOW() - INTERVAL '10 minutes'
GROUP BY collector_name, date_trunc('minute', started_at)
HAVING COUNT(*) > 1;

-- RESULTADO: 0 rows ✅
```

---

## 🔧 ARQUIVOS MODIFICADOS

### 1. Collectors TypeScript (7 arquivos)

**Diretório:** `/home/ubuntu/sofia-pulse/scripts/collectors/`

Arquivos patchados:
- developer-tools-collector.ts
- funding-collector.ts
- jobs-collector.ts
- organizations-collector.ts
- research-papers-collector.ts
- tech-conferences-collector.ts
- tech-trends-collector.ts

**Modificações aplicadas:**
1. Adicionado `const SKIP_TRACKING = process.env.NO_TRACKING === '1';` após `dotenv.config();`
2. Wrapped `sofia.start_collector_run()` em `if (!SKIP_TRACKING) { ... }`
3. Modificado guards de `sofia.finish_collector_run()` para `if (!SKIP_TRACKING && runId) { ... }`

**Exemplo:**
```typescript
// Antes
const result = await this.pool.query(
  'SELECT sofia.start_collector_run($1, $2) as run_id',
  [config.name, hostname]
);
runId = result.rows[0]?.run_id;

// Depois
if (!SKIP_TRACKING) {
const result = await this.pool.query(
  'SELECT sofia.start_collector_run($1, $2) as run_id',
  [config.name, hostname]
);
runId = result.rows[0]?.run_id;
}
```

### 2. collect-with-notification.sh

**Arquivo:** `/home/ubuntu/sofia-pulse/scripts/collect-with-notification.sh`

**Modificação:**
```bash
# Antes
OUTPUT=$(npx tsx scripts/collect.ts "$COLLECTOR_NAME" 2>&1)

# Depois
OUTPUT=$(export NO_TRACKING=1
npx tsx scripts/collect.ts "$COLLECTOR_NAME" 2>&1)
```

---

## 💾 BACKUPS CRIADOS

**Timestamp:** 20260219-003835

**Localização:**
```bash
# Collectors TypeScript
/home/ubuntu/sofia-pulse/scripts/collectors/*.bak-20260219-003835

# collect-with-notification.sh
/home/ubuntu/sofia-pulse/scripts/collect-with-notification.sh.bak-20260219-003835
```

**Listar backups:**
```bash
ls -lh /home/ubuntu/sofia-pulse/scripts/collectors/*.bak-*
ls -lh /home/ubuntu/sofia-pulse/scripts/*.bak-*
```

---

## 🔄 ROLLBACK (Se Necessário)

### Restaurar Collectors TypeScript
```bash
cd /home/ubuntu/sofia-pulse/scripts/collectors

# Restaurar todos de uma vez
for f in *.bak-20260219-003835; do
  cp "$f" "${f%.bak-*}"
done

# OU restaurar individual
cp jobs-collector.ts.bak-20260219-003835 jobs-collector.ts
```

### Restaurar collect-with-notification.sh
```bash
cd /home/ubuntu/sofia-pulse/scripts
cp collect-with-notification.sh.bak-20260219-003835 collect-with-notification.sh
```

---

## ✅ VALIDAÇÃO

### 1. Verificação Estática
```bash
bash /tmp/verify_no_tracking.sh
```

**Resultado esperado:**
- ✅ Todos os collectors têm `SKIP_TRACKING`
- ✅ Todos `start_collector_run` wrapped
- ✅ Todos `finish_collector_run` guarded
- ✅ `export NO_TRACKING=1` presente

### 2. Verificação no Banco
```bash
# Executar um collector
cd /home/ubuntu/sofia-pulse
bash cron-wrapper.sh python3 scripts/tracked_runner.py jobs-adzuna \
  'bash scripts/collect-with-notification.sh jobs-adzuna'

# Verificar duplicatas
PGPASSWORD='SofiaPulse2025Secure@DB' psql -h localhost -U sofia -d sofia_db -c "
SELECT
  collector_name,
  COUNT(*) as records
FROM sofia.collector_runs
WHERE started_at >= NOW() - INTERVAL '5 minutes'
GROUP BY collector_name, date_trunc('minute', started_at)
HAVING COUNT(*) > 1;
"
```

**Resultado esperado:** 0 rows (nenhuma duplicata)

---

## 🐛 ISSUES IDENTIFICADOS (Não relacionados ao patch)

### 1. Error Code Truncation
**Sintoma:** `psycopg2.errors.StringDataRightTruncation: value too long for type character varying(80)`

**Causa:** Coluna `error_code VARCHAR(80)` muito pequena para mensagens de erro longas

**Solução futura:**
```sql
ALTER TABLE sofia.collector_runs
ALTER COLUMN error_code TYPE VARCHAR(500);
```

### 2. WhatsApp API Timeout
**Sintoma:** `Connection to 91.98.158.19:3001 timed out`

**Causa:** Serviço Baileys API não está respondendo

**Solução:** Verificar se serviço está rodando ou aumentar timeout

---

## 📝 PRÓXIMOS PASSOS

1. ✅ **CONCLUÍDO:** Patch NO_TRACKING aplicado
2. ✅ **CONCLUÍDO:** Verificação de zero duplicatas
3. ⏳ **PENDENTE:** Corrigir error_code VARCHAR(80) → VARCHAR(500)
4. ⏳ **PENDENTE:** Investigar WhatsApp API timeout
5. ⏳ **PENDENTE:** Monitorar execuções via cron por 24h

---

## 🎯 CONCLUSÃO

**Tracking duplicado eliminado com sucesso.**

- Patch cirúrgico aplicado em 8 arquivos (7 collectors + 1 wrapper)
- Zero sobrescrita de arquivos completos (apenas linhas específicas modificadas)
- Backups criados para rollback seguro
- Validação confirma: 1 registro por execução (não mais 2)
- Sistema legado preservado (funciona sem NO_TRACKING=1)

**Próxima execução via cron:** Verificar logs para confirmar estabilidade.

---

**Gerado:** 2026-02-19 00:40 UTC
**Por:** apply_patch_no_tracking.py (cirúrgico + validado)
