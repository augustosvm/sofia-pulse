# 📅 Setup Crontab - Sofia Pulse

## 🎯 O que o crontab faz

**1 execução principal (22:00 UTC / 19:00 BRT):**
- ✅ Aplica migrations no banco
- ✅ Corrige configs de DB
- ✅ Coleta TODOS os dados (Reddit, NPM, PyPI, etc)
- ✅ Gera TODAS as análises (Top 10, Correlações, Dark Horses, etc)
- ✅ Envia EMAIL automático para augustosvm@gmail.com

**9 collectors individuais** (ao longo do dia):
- GitHub Trending, HackerNews, Finance (B3, NASDAQ, Funding), GDELT, Reddit, NPM, PyPI

**5 backups automáticos**:
- Auto-recovery (a cada minuto)
- Backups diários e semanais

---

## 🚀 Como aplicar

### No servidor:

```bash
cd /home/ubuntu/sofia-pulse

# Pull das mudanças
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE

# Aplicar crontab (interativo)
bash apply-crontab.sh

# OU aplicar diretamente
crontab crontab-updated.txt
```

---

## 📊 Verificar

```bash
# Ver jobs instalados
crontab -l | grep sofia

# Ver logs
tail -f /var/log/sofia-pulse-complete.log
tail -f /var/log/sofia-email.log
```

---

## 📧 Email automático

Você vai receber **todo dia às 19:00 BRT** (22:00 UTC):

**6 relatórios TXT:**
- Sofia Complete Report
- Top 10 Tech Trends
- Correlações Papers ↔ Funding
- Dark Horses Report
- Entity Resolution
- NLG Playbooks (Gemini AI)

**CSVs com dados RAW:**
- github_trending.csv
- npm_stats.csv
- pypi_stats.csv
- reddit_stats.csv
- funding_30d.csv

---

## 🔧 Customizar horários

Edite `crontab-updated.txt` e ajuste os horários no formato:

```
MINUTO HORA DIA_MÊS MÊS DIA_SEMANA COMANDO

Exemplos:
0 22 * * 1-5  → Seg-Sex às 22:00 UTC
0 9,21 * * *  → Todo dia às 09:00 e 21:00 UTC
*/30 * * * *  → A cada 30 minutos
```

Depois aplique:
```bash
crontab crontab-updated.txt
```

---

## ⚠️ Importante

- Horários são em **UTC** (BRT = UTC - 3)
- Logs em `/var/log/sofia-*.log`
- Se mudar `.env`, não precisa re-aplicar crontab
- Para desabilitar: `crontab -r` (remove tudo) ou comente linhas no arquivo

---

**Última atualização**: 2025-11-19
**Branch**: claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE
