# 🧹 Guia de Instalação - Cron LIMPO

**Data**: 2025-11-19
**Branch**: `claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE`

---

## 🎯 O QUE ESTE GUIA FAZ

Baseado na **AUDITORIA COMPLETA** que identificou:
- ❌ **7 scripts inexistentes** no cron (collect-cron.sh, cron-daily.sh, etc)
- ❌ **3 linhas duplicadas** (generate-insights.sh rodando 3x)
- ❌ **11 collectors existentes** mas NÃO rodando no cron
- ❌ **Cron rodando v1.0** (antigo) em vez de v2.0 (novo com análise temporal)

**Solução**: Script automático que faz backup, limpa, e instala cron correto.

---

## 🚀 INSTALAÇÃO NO SERVIDOR (1 COMANDO!)

```bash
# 1. Ir para o diretório do Sofia Pulse
cd /home/ubuntu/sofia-pulse

# 2. Atualizar código (pull da branch)
git stash  # Se houver mudanças locais
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE

# 3. Executar instalador automático
bash install-clean-crontab.sh
```

**Pronto!** O script vai:
1. ✅ Fazer backup do cron atual
2. ✅ Mostrar o diff (o que vai mudar)
3. ✅ Pedir confirmação
4. ✅ Instalar cron limpo
5. ✅ Criar diretórios de log
6. ✅ Mostrar resumo

---

## 📊 O QUE VAI MUDAR

### ✅ ADICIONADOS (11 collectors que existiam mas não rodavam)

| Collector | Horário | Dados |
|-----------|---------|-------|
| `collect:arxiv-ai` | 20:00 UTC diário | Papers AI/ML |
| `collect:openalex` | 20:05 UTC diário | Research papers |
| `collect:ai-companies` | 20:10 UTC diário | Empresas AI |
| `collect:patents-all` | 01:00 UTC diário | Patentes (China + Europa) |
| `collect:hkex` | 02:00 UTC seg-sex | IPOs Hong Kong |
| `collect:nih-grants` | 03:00 UTC segunda | NIH grants biomedicina |
| `collect:asia-universities` | 04:00 UTC dia 1 | Universidades Ásia |
| `collect:cardboard` | 05:00 UTC segunda | Cardboard production |
| `collect:ipo-calendar` | 06:00 UTC diário | IPOs (NASDAQ, B3, SEC) |
| `collect:jobs` | 07:00 UTC diário | Vagas (Indeed, LinkedIn) |

### ❌ REMOVIDOS (não existem)

- `collect-cron.sh`
- `cron-daily.sh`
- `cron-weekly.sh`
- `cron-monthly.sh`
- `npm run collect:yc`
- `npm run collect:sec`
- `npm run collect:hackernews`
- 3x duplicatas de `generate-insights.sh`

### 🔄 ATUALIZADOS

- **Antes**: `generate-insights.sh` (v1.0 - básico)
- **Depois**: `generate-insights-v2.0.sh` (v2.0 - com análise temporal, anomalias, correlações, forecasts)

---

## 📅 NOVO CRONOGRAMA (Todos os Horários em UTC)

### Diário
```
20:00 - ArXiv AI Papers
20:05 - OpenAlex Papers
20:10 - AI Companies
01:00 - Patentes (China + Europa)
06:00 - IPO Calendar
07:00 - Jobs (Indeed, LinkedIn)
```

### Segunda a Sexta (dias úteis)
```
21:00 - Finance (B3, NASDAQ, Funding)
22:00 - Premium Insights v2.0
23:00 - Email com Insights + CSVs
02:00 - IPOs Hong Kong
```

### Semanal (Segundas)
```
03:00 - NIH Grants
05:00 - Cardboard Production
```

### Mensal (Dia 1)
```
04:00 - Universidades Ásia
```

---

## 🔍 VERIFICAÇÃO PÓS-INSTALAÇÃO

### 1. Ver cron instalado
```bash
crontab -l
```

### 2. Verificar collectors no package.json
```bash
npm run | grep collect:
```

Deve mostrar:
```
collect:arxiv-ai
collect:openalex
collect:ai-companies
collect:patents-all
collect:hkex
collect:nih-grants
collect:asia-universities
collect:cardboard
collect:ipo-calendar  # ← NOVO!
collect:jobs          # ← NOVO!
collect:brazil
collect:nasdaq
collect:funding
```

### 3. Testar um collector manualmente
```bash
npm run collect:arxiv-ai
```

### 4. Testar insights v2.0
```bash
./generate-insights-v2.0.sh
```

### 5. Ver logs
```bash
# Ver últimas 50 linhas de todos os logs
tail -50 /var/log/sofia-*.log

# Seguir em tempo real (esperar próximo job rodar)
tail -f /var/log/sofia-*.log
```

---

## 🐛 TROUBLESHOOTING

### Erro: "crontab: command not found"
```bash
sudo apt update
sudo apt install cron
```

### Erro: "npm: command not found"
```bash
# Instalar Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### Erro: "tsx: command not found"
```bash
cd /home/ubuntu/sofia-pulse
npm install
```

### Erro: "venv-analytics not found"
```bash
bash setup-data-mining.sh
```

### Erro: "Permission denied" nos logs
```bash
sudo chown ubuntu:ubuntu /var/log/sofia-*.log
```

### Erro: Collector falha com "database connection failed"
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar credenciais no .env
cat .env | grep -E "(DB_HOST|DB_USER|DB_PASS)"
```

---

## 📊 ESTATÍSTICAS DO NOVO CRON

| Tipo | Quantidade |
|------|------------|
| Collectors de dados | 11 |
| Insights + Email | 2 |
| Backups | 5 |
| **TOTAL** | **18 jobs** |

### Antes (cron antigo):
- ❌ 7 scripts inexistentes
- ❌ 3 duplicatas
- ❌ 11 collectors não rodando
- ❌ Insights v1.0 (básico)

### Depois (cron limpo):
- ✅ 0 scripts inexistentes
- ✅ 0 duplicatas
- ✅ Todos os 11 collectors rodando
- ✅ Insights v2.0 (avançado)

---

## 🎯 PRÓXIMOS PASSOS (APÓS INSTALAÇÃO)

### 1. Aguardar primeira rodada de coleta
Esperar 24-48h para os collectors popularem o banco com dados.

### 2. Verificar dados coletados
```bash
# Entrar no banco
psql -U sofia -d sofia_db

# Ver quantidade de dados por tabela
SELECT 'arxiv_ai_papers' as table_name, COUNT(*) FROM sofia.arxiv_ai_papers
UNION ALL
SELECT 'openalex_papers', COUNT(*) FROM sofia.openalex_papers
UNION ALL
SELECT 'ai_companies', COUNT(*) FROM sofia.ai_companies
UNION ALL
SELECT 'funding_rounds', COUNT(*) FROM sofia.funding_rounds
UNION ALL
SELECT 'jobs', COUNT(*) FROM sofia.jobs
ORDER BY table_name;
```

### 3. Verificar insights gerados
```bash
# Ver último insight gerado
cat analytics/premium-insights/latest-geo.txt

# Ver quando foi gerado
ls -lh analytics/premium-insights/latest-geo.txt
```

### 4. Verificar email enviado
Checar inbox: **augustosvm@gmail.com**

Deve ter:
- 📄 Insights em texto (latest-geo.txt)
- 📊 CSVs de dados RAW anexados

---

## 🔒 BACKUP E ROLLBACK

### Se algo der errado, você pode voltar ao cron antigo:

```bash
# 1. Ver backups disponíveis
ls -lh ~/crontab-backup-*.txt

# 2. Restaurar backup (trocar pela data correta)
crontab ~/crontab-backup-20251119-120000.txt

# 3. Verificar
crontab -l
```

---

## 📋 CHECKLIST COMPLETO

```bash
# No servidor (/home/ubuntu/sofia-pulse)

# ✅ 1. Atualizar código
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE

# ✅ 2. Instalar cron limpo
bash install-clean-crontab.sh

# ✅ 3. Verificar instalação
crontab -l | grep -E "^[^#]" | wc -l
# Deve mostrar ~18 linhas (jobs ativos)

# ✅ 4. Testar collector
npm run collect:arxiv-ai

# ✅ 5. Testar insights v2.0
./generate-insights-v2.0.sh

# ✅ 6. Aguardar próxima rodada automática (20:00 UTC)
tail -f /var/log/sofia-*.log
```

---

## 📞 SUPORTE

### Se encontrar problemas:

1. **Verificar logs**:
   ```bash
   tail -100 /var/log/sofia-*.log
   ```

2. **Verificar status do cron**:
   ```bash
   sudo systemctl status cron
   ```

3. **Verificar último erro de um collector**:
   ```bash
   grep -i error /var/log/sofia-arxiv.log | tail -20
   ```

4. **Executar manualmente para debug**:
   ```bash
   cd /home/ubuntu/sofia-pulse
   npm run collect:arxiv-ai
   # Ver erro completo no terminal
   ```

---

## 🎉 RESUMO EXECUTIVO

**O que foi feito**:
- ✅ Auditoria completa de collectors vs cron
- ✅ Script automático de limpeza e instalação
- ✅ Adicionados 11 collectors que faltavam
- ✅ Removidos 7 scripts inexistentes
- ✅ Removidas 3 duplicatas
- ✅ Atualizado de v1.0 para v2.0 (análise temporal)

**O que você precisa fazer**:
```bash
cd /home/ubuntu/sofia-pulse
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE
bash install-clean-crontab.sh
```

**Resultado esperado**:
- 🤖 11 collectors rodando automaticamente
- 📊 Insights v2.0 com análise temporal, anomalias, correlações, forecasts
- 📧 Email diário (seg-sex) com insights + CSVs
- 📁 Dados RAW exportados para análise externa

---

**Última Atualização**: 2025-11-19
**Branch**: `claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE`
**Status**: ✅ Pronto para instalação
