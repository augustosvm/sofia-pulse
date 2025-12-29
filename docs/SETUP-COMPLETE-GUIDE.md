# 🚀 GUIA COMPLETO DE SETUP - Sofia Pulse

## ✅ API Key do Alpha Vantage

**Sua chave**: `JFVYRODTWGO1W5M6`

Esta chave permite:
- 🔥 **25 requests/dia** (GRÁTIS)
- 📈 Commodity prices em tempo real
- 💰 Financial data (stocks, forex)
- 🌍 Global economic indicators

---

## 📋 Setup Passo a Passo

### 1️⃣ Adicionar Alpha Vantage API Key

```bash
cd /home/ubuntu/sofia-pulse
./setup-alpha-vantage.sh
```

**O que faz:**
- ✅ Adiciona `ALPHA_VANTAGE_API_KEY=JFVYRODTWGO1W5M6` ao `.env`
- ✅ Remove chaves antigas se existirem
- ✅ Cria backup do `.env`
- ✅ Valida configuração

**Resultado esperado:**
```
✅ SUCCESS! Alpha Vantage Configured

📝 Your .env now has 3 API keys:
   ✅ EIA_API_KEY (electricity data)
   ✅ API_NINJAS_KEY (platinum price)
   ✅ ALPHA_VANTAGE_API_KEY (commodities - NOVO!)
```

---

### 2️⃣ Verificar Setup Completo

```bash
./verify-setup-complete.sh
```

**O que verifica:**
- 🔑 API Keys (EIA, API Ninjas, Alpha Vantage)
- 🐍 Python environment (venv-analytics)
- 📜 Scripts executáveis
- 🐍 Python collectors
- ⏰ Crontab configurado
- 🗄️ Database tables

**Resultado esperado:**
```
✅ ALL SYSTEMS GO!

🎯 Next execution:
   Python Collectors: 13:00 UTC (10:00 BRT)
   Analytics + Email: 22:00 UTC (19:00 BRT)
```

---

### 3️⃣ Atualizar Crontab

```bash
./update-crontab-complete.sh
```

**O que faz:**
- 📋 Mostra crontab atual
- 🔧 Cria novo crontab com Python collectors
- ⏰ Agenda execuções diárias
- 💾 Faz backup do crontab anterior

**Novidades no crontab:**
```cron
# Python Collectors - Diariamente às 13:00 UTC (10:00 BRT)
0 13 * * * cd /home/ubuntu/sofia-pulse && ./run-all-with-venv.sh >> /var/log/sofia-python-collectors.log 2>&1

# Analytics + Email - Seg-Sex às 22:00 UTC (19:00 BRT)
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-all-now.sh >> /var/log/sofia-pulse-complete.log 2>&1
```

**Total de jobs**: 26
- 19 Node.js collectors
- 1 Python batch (4 collectors)
- 1 Analytics + Email
- 5 Backups

---

## 🔄 Execução Única (Tudo de uma vez)

```bash
cd /home/ubuntu/sofia-pulse

# 1. Setup Alpha Vantage
./setup-alpha-vantage.sh

# 2. Verificar tudo
./verify-setup-complete.sh

# 3. Atualizar crontab
./update-crontab-complete.sh
# (digite 'y' quando perguntar)

# 4. Testar execução manual
./run-all-with-venv.sh
```

---

## 📊 O Que Cada Script Faz

### `setup-alpha-vantage.sh`
- ✅ Adiciona Alpha Vantage API key ao `.env`
- ✅ Remove duplicatas
- ✅ Valida configuração

### `verify-setup-complete.sh`
- 🔍 Verifica API keys
- 🔍 Verifica Python environment
- 🔍 Verifica scripts
- 🔍 Verifica database
- 🔍 Verifica crontab
- 📊 Mostra summary

### `update-crontab-complete.sh`
- 📋 Mostra crontab atual
- 🔧 Cria novo crontab
- ⏰ Agenda Python collectors (13:00 UTC)
- ⏰ Agenda Analytics (22:00 UTC)
- 💾 Faz backup

### `run-all-with-venv.sh`
- ⚡ Executa Electricity Consumption
- 🚢 Executa Port Traffic
- 📈 Executa Commodity Prices
- 💾 Executa Semiconductor Sales

---

## 🎯 Cronograma Diário

| Hora (UTC) | Hora (BRT) | Ação |
|------------|------------|------|
| 08:00 | 05:00 | GitHub Trending |
| 08:30 | 05:30 | HackerNews |
| 09:00 | 06:00 | NPM Stats |
| 09:30 | 06:30 | PyPI Stats |
| 10:00 | 07:00 | Reddit Tech |
| 11:00 | 08:00 | Cybersecurity |
| 11:30 | 08:30 | Space Industry |
| 12:00 | 09:00 | AI Regulation |
| 12:30 | 09:30 | GDELT Events |
| **13:00** | **10:00** | **🔥 Python Collectors (NOVO!)** |
| 20:00 | 17:00 | ArXiv AI |
| 20:05 | 17:05 | OpenAlex |
| 20:10 | 17:10 | AI Companies |
| 21:00 | 18:00 | Finance (Seg-Sex) |
| **22:00** | **19:00** | **📧 Analytics + Email** |

---

## 📝 Logs

### Ver logs em tempo real:

```bash
# Python collectors
tail -f /var/log/sofia-python-collectors.log

# Analytics + Email
tail -f /var/log/sofia-pulse-complete.log

# Todos os logs
tail -f /var/log/sofia-*.log
```

### Ver últimas execuções:

```bash
# Python collectors (últimas 100 linhas)
tail -100 /var/log/sofia-python-collectors.log

# Analytics (últimas 100 linhas)
tail -100 /var/log/sofia-pulse-complete.log
```

---

## 🧪 Testar Agora

### Testar Python collectors:

```bash
cd /home/ubuntu/sofia-pulse
./run-all-with-venv.sh
```

**Resultado esperado:**
```
✅ Electricity Consumption: 239 records
✅ Port Traffic: 2,462 records
✅ Commodity Prices: 5 commodities
✅ Semiconductor Sales: 4 records

TOTAL: 2,710 records
```

### Testar crontab:

```bash
# Ver crontab instalado
crontab -l

# Ver próxima execução
crontab -l | grep run-all-with-venv.sh
```

---

## 🔧 Troubleshooting

### Problema: API key não encontrada

```bash
# Verificar .env
cat .env | grep ALPHA_VANTAGE

# Se não aparecer, rodar novamente:
./setup-alpha-vantage.sh
```

### Problema: Python packages não instalados

```bash
# Verificar venv
ls -la venv-analytics/

# Se não existir, criar:
./install-python-deps.sh
```

### Problema: Crontab não executando

```bash
# Verificar se cron está rodando
sudo service cron status

# Ver logs do cron
grep CRON /var/log/syslog | tail -20

# Testar manualmente
./run-all-with-venv.sh
```

---

## 📊 Verificar Dados no Banco

```bash
psql -U sofia -d sofia_db -c "
SELECT
    'electricity_consumption' as table, COUNT(*) as records
    FROM sofia.electricity_consumption
UNION ALL
SELECT 'port_traffic', COUNT(*) FROM sofia.port_traffic
UNION ALL
SELECT 'commodity_prices', COUNT(*) FROM sofia.commodity_prices
UNION ALL
SELECT 'semiconductor_sales', COUNT(*) FROM sofia.semiconductor_sales;
"
```

**Resultado esperado:**
```
        table            | records
------------------------+---------
 electricity_consumption|     239
 port_traffic           |    2462
 commodity_prices       |       5
 semiconductor_sales    |       4
```

---

## ✅ Checklist Final

- [ ] Alpha Vantage API key adicionada (`./setup-alpha-vantage.sh`)
- [ ] Setup verificado (`./verify-setup-complete.sh`)
- [ ] Crontab atualizado (`./update-crontab-complete.sh`)
- [ ] Teste manual executado (`./run-all-with-venv.sh`)
- [ ] Dados no banco verificados (query SQL acima)
- [ ] Logs configurados (`tail -f /var/log/sofia-python-collectors.log`)

---

## 🎉 Conclusão

Depois de completar todos os passos:

✅ **3 API keys** configuradas (EIA, API Ninjas, Alpha Vantage)
✅ **4 Python collectors** rodando (electricity, port, commodity, semiconductor)
✅ **26 cron jobs** agendados (19 Node + 1 Python batch + 1 analytics + 5 backups)
✅ **2,710+ registros** coletados diariamente
✅ **Automação completa** (10:00 BRT collectors, 19:00 BRT email)

**Sistema 100% operacional! 🚀**

---

**Última atualização**: 2025-11-19
**Branch**: `claude/fix-sql-syntax-error-015w5Ss8ZiqFEJziiWrN7Rs1`
