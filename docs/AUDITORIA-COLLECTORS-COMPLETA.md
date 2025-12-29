# 🔍 AUDITORIA COMPLETA - Collectors vs Cron

**Data**: 2025-11-18 23:50 UTC  
**Branch**: `claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE`

---

## ✅ RESUMO EXECUTIVO

**Collectors existentes**: 14  
**Collectors no cron**: 3 (apenas finance)  
**Collectors FALTANDO no cron**: 11  
**Scripts no cron que NÃO existem**: 7  
**Linhas duplicadas no cron**: 3  

---

## 📊 COLLECTORS QUE EXISTEM

### ✅ Principal (package.json)

| Collector | Script | Dados | Cron? |
|-----------|--------|-------|-------|
| `collect:cardboard` | `scripts/collect-cardboard-production.ts` | Leading indicator econômico | ❌ |
| `collect:wipo-china` | `scripts/collect-wipo-china-patents.ts` | Patentes China | ❌ |
| `collect:hkex` | `scripts/collect-hkex-ipos.ts` | IPOs Hong Kong | ❌ |
| `collect:epo` | `scripts/collect-epo-patents.ts` | Patentes Europa | ❌ |
| `collect:asia-universities` | `scripts/collect-asia-universities.ts` | Universidades Ásia | ❌ |
| `collect:arxiv-ai` | `scripts/collect-arxiv-ai.ts` | Papers AI/ML | ❌ |
| `collect:ai-companies` | `scripts/collect-ai-companies.ts` | Empresas AI | ❌ |
| `collect:openalex` | `scripts/collect-openalex.ts` | Research papers | ❌ |
| `collect:nih-grants` | `scripts/collect-nih-grants.ts` | NIH grants biomedicina | ❌ |

### ✅ Finance (finance/package.json)

| Collector | Script | Dados | Cron? |
|-----------|--------|-------|-------|
| `collect:brazil` | `finance/scripts/collect-brazil-stocks.ts` | Ações B3 | ✅ 21:00 |
| `collect:nasdaq` | `finance/scripts/collect-nasdaq-momentum.ts` | NASDAQ high-momentum | ✅ 21:00 |
| `collect:funding` | `finance/scripts/collect-funding-rounds.ts` | Funding rounds | ✅ 21:00 |

### ✅ Collectors Avulsos (sem npm script)

| Collector | Script | Dados | Package.json? | Cron? |
|-----------|--------|-------|---------------|-------|
| IPO Calendar | `collectors/ipo-calendar.ts` | IPOs (NASDAQ, B3, SEC/EDGAR) | ❌ | ❌ |
| Jobs Collector | `collectors/jobs-collector.ts` | Vagas tech (Indeed, LinkedIn) | ❌ | ❌ |

---

## ❌ NO CRON MAS NÃO EXISTEM

| Linha Cron | Comando | Status |
|------------|---------|--------|
| `0 */6 * * *` | `/home/ubuntu/sofia-pulse/collect-cron.sh` | ❌ **NÃO EXISTE** |
| `0 6 * * *` | `/home/ubuntu/sofia-pulse/cron-daily.sh` | ❌ **NÃO EXISTE** |
| `0 7 * * 1` | `/home/ubuntu/sofia-pulse/cron-weekly.sh` | ❌ **NÃO EXISTE** |
| `0 8 1 * *` | `/home/ubuntu/sofia-pulse/cron-monthly.sh` | ❌ **NÃO EXISTE** |
| `0 2 * * *` | `npm run collect:yc` | ❌ **NÃO EXISTE** |
| `0 3 * * *` | `npm run collect:sec` | ❌ **NÃO EXISTE** (mas IPO tem SEC) |
| `0 4 * * *` | `npm run collect:hackernews` | ❌ **NÃO EXISTE** |

---

## 🚨 PROBLEMAS NO CRON ATUAL

### 1. Linhas DUPLICADAS
```bash
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && ./generate-insights.sh  # 1x
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && ./generate-insights.sh  # 2x DUPLICADO
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && ./generate-insights.sh  # 3x DUPLICADO
```

### 2. Referências a scripts inexistentes (7 linhas)
- `collect-cron.sh`
- `cron-daily.sh`
- `cron-weekly.sh`
- `cron-monthly.sh`
- `collect:yc`
- `collect:sec`
- `collect:hackernews`

### 3. Collectors existentes mas NÃO no cron (11)
- ArXiv AI, OpenAlex, AI Companies
- Patentes (China, Europa)
- HKEX IPOs
- NIH Grants
- Universidades Ásia
- Cardboard Production
- IPO Calendar
- Jobs Collector

---

## 📊 SCRIPTS DE INSIGHTS (CONFUSÃO!)

Tem **9 scripts diferentes** de geração de insights:

| Script | Versão | Usado pelo cron? |
|--------|--------|------------------|
| `generate-insights.py` | v1.0 | ✅ SIM (`generate-insights.sh`) |
| `generate-insights-v2.0.sh` | v2.0 ⭐ | ❌ NÃO |
| `generate-premium-insights-v2.0.py` | v2.0 ⭐ | ❌ NÃO |
| `generate-insights-v4-REAL.py` | v4.0 | ❌ NÃO |
| `generate-premium-insights-v2.py` | v2.0 antiga | ❌ NÃO |
| `generate-premium-insights-v3-REAL.py` | v3.0 | ❌ NÃO |
| `generate-premium-insights-v3.py` | v3.0 | ❌ NÃO |
| `generate-premium-insights.py` | v1.0 | ❌ NÃO |
| `generate-insights-simple.py` | Simple | ❌ NÃO |

**Problema**: Cron roda v1.0 (antigo), mas v2.0 é o novo com análise temporal!

---

## ✅ CRON LIMPO PROPOSTO

```bash
#============================================================================
# SOFIA PULSE - Cron Jobs (Limpo e Organizado)
#============================================================================

# 1. COLLECTORS - Dados Reais
#============================================================================

# Finance (B3, NASDAQ, Funding) - Seg-Sex às 21:00 UTC (18:00 BRT)
0 21 * * 1-5 cd /home/ubuntu/sofia-pulse && ./collect-finance.sh >> /var/log/sofia-finance.log 2>&1

# ArXiv AI Papers - Diário às 20:00 UTC
0 20 * * * cd /home/ubuntu/sofia-pulse && npm run collect:arxiv-ai >> /var/log/sofia-arxiv.log 2>&1

# OpenAlex Papers - Diário às 20:05 UTC
5 20 * * * cd /home/ubuntu/sofia-pulse && npm run collect:openalex >> /var/log/sofia-openalex.log 2>&1

# AI Companies - Diário às 20:10 UTC
10 20 * * * cd /home/ubuntu/sofia-pulse && npm run collect:ai-companies >> /var/log/sofia-ai-companies.log 2>&1

# Patentes (WIPO China, EPO) - Diário às 01:00 UTC
0 1 * * * cd /home/ubuntu/sofia-pulse && npm run collect:patents-all >> /var/log/sofia-patents.log 2>&1

# IPOs Hong Kong - Seg-Sex às 02:00 UTC
0 2 * * 1-5 cd /home/ubuntu/sofia-pulse && npm run collect:hkex >> /var/log/sofia-hkex.log 2>&1

# NIH Grants (Biotech) - Semanal (segunda às 03:00 UTC)
0 3 * * 1 cd /home/ubuntu/sofia-pulse && npm run collect:nih-grants >> /var/log/sofia-nih.log 2>&1

# Universidades Ásia - Mensal (dia 1 às 04:00 UTC)
0 4 1 * * cd /home/ubuntu/sofia-pulse && npm run collect:asia-universities >> /var/log/sofia-unis.log 2>&1

# Cardboard Production (Leading Indicator) - Semanal (segunda às 05:00 UTC)
0 5 * * 1 cd /home/ubuntu/sofia-pulse && npm run collect:cardboard >> /var/log/sofia-cardboard.log 2>&1

#============================================================================
# 2. INSIGHTS GENERATION (v2.0 - Com Análise Temporal!)
#============================================================================

# Premium Insights v2.0 - Seg-Sex às 22:00 UTC (19:00 BRT)
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && ./generate-insights-v2.0.sh >> /var/log/sofia-insights-v2.log 2>&1

#============================================================================
# 3. EMAIL & REPORTING
#============================================================================

# Email com Insights - Seg-Sex às 23:00 UTC (20:00 BRT)
0 23 * * 1-5 cd /home/ubuntu/sofia-pulse && ./send-insights-email.sh >> /var/log/sofia-email.log 2>&1

#============================================================================
# TOTAL: 11 jobs (sem duplicatas, sem scripts inexistentes)
#============================================================================
```

---

## 🎯 DECISÕES NECESSÁRIAS

### 1. **Qual script de insights usar?**
   - ⭐ `generate-insights-v2.0.sh` (RECOMENDO - tem análise temporal, correlações, forecasts)
   - `generate-insights-v4-REAL.py` (tem geo-localização)
   - Outro?

### 2. **Adicionar collectors avulsos ao package.json?**
   - IPO Calendar (`collectors/ipo-calendar.ts`)
   - Jobs Collector (`collectors/jobs-collector.ts`)

### 3. **Implementar collectors tech intelligence?**
   - GitHub (trending, stars, linguagens)
   - npm/PyPI (downloads)
   - Stack Overflow (tags)
   - Hacker News (real)
   - Reddit (r/programming)

---

## 📋 AÇÕES IMEDIATAS

### No servidor:
```bash
# 1. Backup do cron atual
crontab -l > ~/crontab-backup-$(date +%Y%m%d).txt

# 2. Editar cron
crontab -e

# 3. REMOVER linhas:
#    - Duplicatas de generate-insights.sh
#    - Refs a collect-cron.sh, cron-daily.sh, etc
#    - Refs a collect:yc, collect:sec, collect:hackernews

# 4. ADICIONAR collectors existentes (copiar do CRON LIMPO acima)

# 5. Verificar logs:
tail -f /var/log/sofia-*.log
```

---

## ✅ SOLUÇÃO IMPLEMENTADA

### Arquivos Criados:

1. **`install-clean-crontab.sh`** - Script automático de instalação
   - Faz backup do cron atual
   - Remove linhas duplicadas e inexistentes
   - Adiciona 11 collectors faltantes
   - Atualiza de v1.0 para v2.0
   - Cria diretórios de log

2. **`GUIA-INSTALACAO-CRON-LIMPO.md`** - Guia completo de instalação
   - Passo-a-passo detalhado
   - Troubleshooting
   - Verificação pós-instalação

3. **`package.json`** - Atualizado com collectors avulsos
   - ✅ Adicionado: `collect:ipo-calendar`
   - ✅ Adicionado: `collect:jobs`

### Para Instalar no Servidor:

```bash
cd /home/ubuntu/sofia-pulse
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE
bash install-clean-crontab.sh
```

---

**Status**: ✅ Solução pronta! Execute `bash install-clean-crontab.sh` no servidor.
