# 🔍 AUDITORIA COMPLETA - Collectors vs Cron

**Data**: 2025-11-18 23:45 UTC
**Branch**: `claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE`

---

## 📊 COLLECTORS QUE EXISTEM

### ✅ Principal (package.json)

| Collector | Script | Status | Cron? |
|-----------|--------|--------|-------|
| `collect:cardboard` | `scripts/collect-cardboard-production.ts` | ✅ Existe | ❓ |
| `collect:wipo-china` | `scripts/collect-wipo-china-patents.ts` | ✅ Existe | ❓ |
| `collect:hkex` | `scripts/collect-hkex-ipos.ts` | ✅ Existe | ❓ |
| `collect:epo` | `scripts/collect-epo-patents.ts` | ✅ Existe | ❓ |
| `collect:asia-universities` | `scripts/collect-asia-universities.ts` | ✅ Existe | ❓ |
| `collect:arxiv-ai` | `scripts/collect-arxiv-ai.ts` | ✅ Existe | ❓ |
| `collect:ai-companies` | `scripts/collect-ai-companies.ts` | ✅ Existe | ❓ |
| `collect:openalex` | `scripts/collect-openalex.ts` | ✅ Existe | ❓ |
| `collect:nih-grants` | `scripts/collect-nih-grants.ts` | ✅ Existe | ❓ |

### ✅ Finance (finance/package.json)

| Collector | Script | Status | Cron? |
|-----------|--------|--------|-------|
| `collect:brazil` | `finance/scripts/collect-brazil-stocks.ts` | ✅ Existe | ✅ SIM (21:00) |
| `collect:nasdaq` | `finance/scripts/collect-nasdaq-momentum.ts` | ✅ Existe | ✅ SIM (21:00) |
| `collect:funding` | `finance/scripts/collect-funding-rounds.ts` | ✅ Existe | ✅ SIM (21:00) |

### ✅ Collectors Avulsos (sem npm script)

| Collector | Script | Status | Cron? |
|-----------|--------|--------|-------|
| IPO Calendar | `collectors/ipo-calendar.ts` | ✅ Existe | ❌ NÃO |
| Jobs Collector | `collectors/jobs-collector.ts` | ✅ Existe | ❌ NÃO |

---

## ❌ COLLECTORS NO CRON MAS NÃO EXISTEM

Esses estão no crontab mas **NÃO TÊM** scripts:

| Linha Cron | Comando | Status |
|------------|---------|--------|
| `0 2 * * *` | `npm run collect:yc` | ❌ **NÃO EXISTE** |
| `0 3 * * *` | `npm run collect:sec` | ❌ **NÃO EXISTE** (mas IPO Calendar coleta SEC/EDGAR) |
| `0 4 * * *` | `npm run collect:hackernews` | ❌ **NÃO EXISTE** |

---

## 🎯 CRON ATUAL (completo)

```bash
# Auto-recovery (a cada 1 minuto)
*/1 * * * * /home/ubuntu/infraestrutura/scripts/auto-recovery.sh

# Backups
0 3 * * * /home/ubuntu/infraestrutura/scripts/comprehensive-backup.sh
0 2 * * * /home/ubuntu/infraestrutura/scripts/backup-dashboards.sh
0 2 * * 3 /home/ubuntu/infraestrutura/scripts/full-backup.sh

# Sofia Pulse - Main
0 */6 * * * /home/ubuntu/sofia-pulse/collect-cron.sh         # ❓ Precisa verificar
0 6 * * * /home/ubuntu/sofia-pulse/cron-daily.sh             # ❓ Precisa verificar
0 7 * * 1 /home/ubuntu/sofia-pulse/cron-weekly.sh            # ❓ Precisa verificar
0 8 1 * * /home/ubuntu/sofia-pulse/cron-monthly.sh           # ❓ Precisa verificar

# Sofia Finance - INEXISTENTES
0 2 * * * cd /home/ubuntu/sofia-pulse/finance && npm run collect:yc        # ❌ NÃO EXISTE
0 3 * * * cd /home/ubuntu/sofia-pulse/finance && npm run collect:sec       # ❌ NÃO EXISTE
0 4 * * * cd /home/ubuntu/sofia-pulse/finance && npm run collect:hackernews # ❌ NÃO EXISTE

# Sofia Finance - B3, NASDAQ, Funding (EXISTEM!)
0 21 * * 1-5 /home/ubuntu/sofia-pulse/collect-finance.sh     # ❓ Precisa verificar

# Insights Generation
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && ./generate-insights.sh
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && ./generate-insights.sh  # DUPLICADO!
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && ./generate-insights.sh  # DUPLICADO!

# Backup
0 4 * * * /home/ubuntu/sofia-pulse/scripts/backup-complete.sh # ❓ Precisa verificar
```

---

## 🚨 PROBLEMAS IDENTIFICADOS

### 1. **Scripts no Cron que NÃO existem**
- ❌ `collect:yc` (Y Combinator)
- ❌ `collect:sec` (SEC filings)
- ❌ `collect:hackernews` (Hacker News)

### 2. **Collectors que EXISTEM mas NÃO estão no Cron**
- ❌ `collect:cardboard` (Leading indicator)
- ❌ `collect:wipo-china` (Patentes China)
- ❌ `collect:hkex` (IPOs Hong Kong)
- ❌ `collect:epo` (Patentes Europa)
- ❌ `collect:asia-universities` (Universidades Ásia)
- ❌ `collect:arxiv-ai` (Papers AI/ML)
- ❌ `collect:ai-companies` (Empresas AI)
- ❌ `collect:openalex` (Research papers)
- ❌ `collect:nih-grants` (NIH grants biomedicina)
- ❌ IPO Calendar (NASDAQ, B3, SEC/EDGAR)
- ❌ Jobs Collector (Indeed, LinkedIn)

### 3. **Linhas DUPLICADAS no Cron**
- 3x `./generate-insights.sh` às 22:00 (seg-sex)

### 4. **Scripts de Orquestração não verificados**
- `collect-cron.sh`
- `cron-daily.sh`
- `cron-weekly.sh`
- `cron-monthly.sh`
- `collect-finance.sh`
- `generate-insights.sh`
- `scripts/backup-complete.sh`

---

## ✅ PLANO DE AÇÃO

### Fase 1: AUDITORIA (AGORA)
1. ✅ Listar collectors existentes
2. ✅ Comparar com cron
3. ⏳ Verificar scripts de orquestração existem
4. ⏳ Propor novo cron limpo

### Fase 2: LIMPEZA (próximo)
1. Remover linhas duplicadas do cron
2. Remover referências a scripts inexistentes (yc, sec, hackernews)
3. Adicionar collectors existentes mas não rodando

### Fase 3: IMPLEMENTAÇÃO (depois)
1. Implementar collectors faltantes para tech intelligence:
   - GitHub (trending, stars)
   - npm/PyPI (downloads)
   - Stack Overflow (tags)
   - Hacker News (se quiser)
   - Reddit (r/programming)

---

## 📋 PRÓXIMO PASSO

Verificar se os scripts de orquestração existem:

```bash
ls -la /home/ubuntu/sofia-pulse/collect-cron.sh
ls -la /home/ubuntu/sofia-pulse/cron-daily.sh
ls -la /home/ubuntu/sofia-pulse/cron-weekly.sh
ls -la /home/ubuntu/sofia-pulse/cron-monthly.sh
ls -la /home/ubuntu/sofia-pulse/collect-finance.sh
ls -la /home/ubuntu/sofia-pulse/generate-insights.sh
ls -la /home/ubuntu/sofia-pulse/scripts/backup-complete.sh
```

---

**Status**: Auditoria em andamento. Aguardando verificação dos scripts de orquestração.
