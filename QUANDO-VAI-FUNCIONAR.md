# ⏰ QUANDO O CRON VAI FUNCIONAR?

## 🔴 STATUS ATUAL: **CRON NÃO ESTÁ INSTALADO**

```bash
$ crontab -l
no crontab for augusto  # ❌ Ainda não configurado
```

**Por quê?**
Você está no **Windows/WSL** (`/mnt/c/Users/...`), não no **servidor Ubuntu**.

---

## ✅ PARA FAZER FUNCIONAR

### Passo 1: SSH no Servidor Ubuntu

```bash
ssh ubuntu@SEU_SERVIDOR_IP
# OU
ssh ubuntu@sofia-pulse.seu-dominio.com
```

### Passo 2: Navegar para o Projeto

```bash
cd /home/ubuntu/sofia-pulse
```

### Passo 3: Pull das Últimas Mudanças

```bash
git pull origin claude/fix-deployment-script-errors-01DFTu3TQVACwYj4RZzJJNPH
```

### Passo 4: Instalar o Crontab

```bash
bash install-crontab-with-daily-report.sh
```

**O script vai mostrar**:
```
✅ Crontab installed with daily WhatsApp reports!

📅 SCHEDULE:
   08:00, 11:00, 14:00, 17:00, 20:00 UTC - Hourly collectors (7)
   10:00 UTC - Daily collectors (34)
   13:00 UTC Mon - Weekly collectors (10)
   14:00 UTC 1st Mon - Monthly collectors (6)
   22:00 UTC - Analytics (33 reports)
   22:30 UTC - Email report
   23:00 UTC - Daily WhatsApp summary 📱
```

### Passo 5: Verificar que Instalou

```bash
crontab -l
```

Deve mostrar algo como:
```cron
0 8,11,14,17,20 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-collectors-with-logging.sh
0 10 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-collectors-with-logging.sh
...
```

---

## 📅 QUANDO VOCÊ VAI SABER QUE ESTÁ FUNCIONANDO?

### 🕐 Horários UTC (Brasil = UTC -3)

| Horário UTC | Horário Brasil | O Que Acontece | WhatsApp Que Você Receberá |
|-------------|----------------|----------------|----------------------------|
| **08:00 UTC** | **05:00 BRT** | Collectors hourly (1ª rodada) | 🚨 Alertas de erros críticos (se houver) |
| **10:00 UTC** | **07:00 BRT** | Collectors daily (34 collectors) | 🚨 Alertas de erros críticos (se houver) |
| **11:00 UTC** | **08:00 BRT** | Collectors hourly (2ª rodada) | 🚨 Alertas de erros críticos (se houver) |
| **13:00 UTC** | **10:00 BRT** | Collectors weekly (só Segunda) | 🚨 Alertas de erros críticos (se houver) |
| **14:00 UTC** | **11:00 BRT** | Collectors hourly (3ª rodada) | 🚨 Alertas de erros críticos (se houver) |
| **17:00 UTC** | **14:00 BRT** | Collectors hourly (4ª rodada) | 🚨 Alertas de erros críticos (se houver) |
| **20:00 UTC** | **17:00 BRT** | Collectors hourly (5ª rodada) | 🚨 Alertas de erros críticos (se houver) |
| **22:00 UTC** | **19:00 BRT** | Analytics (33 reports) | ⚠️ Resumo analytics (quantos reports OK) |
| **22:30 UTC** | **19:30 BRT** | Email enviado | ✅ "Email enviado: 33 reports, 15 CSVs" |
| **23:00 UTC** | **20:00 BRT** | **📊 RELATÓRIO DIÁRIO** | **✅ RESUMO COMPLETO DO DIA** |

---

## 📱 PRIMEIRO SINAL DE QUE FUNCIONOU

### Se Instalar HOJE (03 Dez 2025):

**Dia**: Quarta-feira
**Hora Atual**: ~10:30 BRT (13:30 UTC)

#### ⏰ Próximas Execuções HOJE:

1. **14:00 UTC (11:00 BRT)** - Daqui a ~30 minutos
   - Collectors hourly (3ª rodada)
   - 7 collectors: HackerNews, Reddit, NPM, PyPI, GitHub x2, GDELT
   - WhatsApp: 🚨 Somente se houver erro crítico

2. **17:00 UTC (14:00 BRT)** - Daqui a ~3h30
   - Collectors hourly (4ª rodada)
   - Mesmos 7 collectors
   - WhatsApp: 🚨 Somente se houver erro crítico

3. **20:00 UTC (17:00 BRT)** - Daqui a ~6h30
   - Collectors hourly (5ª rodada)
   - Mesmos 7 collectors
   - WhatsApp: 🚨 Somente se houver erro crítico

4. **22:00 UTC (19:00 BRT)** - Daqui a ~8h30
   - Analytics (33 reports)
   - WhatsApp: ⚠️ "Analytics Complete: 33/33 reports ✅"

5. **22:30 UTC (19:30 BRT)** - Daqui a ~9h
   - Email enviado
   - WhatsApp: ✅ "Sofia Pulse Report Sent: 33 reports, 15 CSVs"

6. **23:00 UTC (20:00 BRT)** - Daqui a ~9h30 🎯 **PRINCIPAL**
   - **RELATÓRIO DIÁRIO COMPLETO**
   - WhatsApp: 📊 "Total: 42 collectors | ✅ 39 (92.9%) | ❌ 3"

---

## 🎯 GARANTIA DE QUE FUNCIONOU

### Amanhã de Manhã (04 Dez 2025):

**10:00 UTC (07:00 BRT)** - Quinta-feira de manhã
- **34 collectors daily** rodam
- Inclui: BACEN, IBGE, IPEA, ComexStat, WHO, UNICEF, ILO, etc.
- WhatsApp: 🚨 Alertas imediatos se algo crítico falhar

**23:00 UTC (20:00 BRT)** - Quinta à noite
- **RELATÓRIO DIÁRIO COMPLETO**
- Vai mostrar TODOS os collectors que rodaram hoje
- Você verá algo como:

```
✅ Sofia Pulse - Relatório Diário
Data: 04/12/2025 20:00

📊 RESUMO GERAL
━━━━━━━━━━━━━━━━
Total: 49 collectors
✅ Sucesso: 46 (93.9%)
❌ Falhas: 3

🔴 FALHAS POR CATEGORIA
━━━━━━━━━━━━━━━━
...
```

---

## 🧪 TESTAR AGORA (Sem Esperar)

Se quiser testar AGORA sem esperar o cron:

```bash
# No servidor
ssh ubuntu@SERVER
cd /home/ubuntu/sofia-pulse

# Testar relatório diário
source venv-analytics/bin/activate
python3 scripts/utils/daily_report_generator.py /var/log/sofia

# Testar collectors hourly
bash run-collectors-with-logging.sh

# Testar analytics
bash run-mega-analytics-with-alerts.sh

# Testar email
bash send-email-mega.sh
```

---

## ⚠️ SE NÃO RECEBER NADA NO WHATSAPP

### Checklist:

1. **Cron instalado?**
   ```bash
   crontab -l | grep -c "collect"
   # Deve mostrar número > 0
   ```

2. **Cron service rodando?**
   ```bash
   systemctl status cron
   # Deve mostrar: Active: active (running)
   ```

3. **WhatsApp API configurada?**
   ```bash
   cat .env | grep WHATSAPP
   # Deve mostrar: WHATSAPP_NUMBER, WHATSAPP_API_URL
   ```

4. **Verificar logs do cron:**
   ```bash
   tail -f /var/log/sofia/hourly.log
   tail -f /var/log/sofia/daily.log
   tail -f /var/log/sofia/daily-report.log
   ```

5. **Testar WhatsApp manualmente:**
   ```bash
   source venv-analytics/bin/activate
   python3 -c "
   import sys
   sys.path.insert(0, 'scripts/utils')
   from whatsapp_notifier import WhatsAppNotifier
   w = WhatsAppNotifier()
   w.send('🧪 Test message from Sofia Pulse')
   "
   ```

---

## 📊 RESUMO VISUAL

```
HOJE (Se instalar agora ~10:30 BRT):
├─ 11:00 BRT ⏰ Hourly collectors (7)
├─ 14:00 BRT ⏰ Hourly collectors (7)
├─ 17:00 BRT ⏰ Hourly collectors (7)
├─ 19:00 BRT 📈 Analytics (33 reports)
├─ 19:30 BRT 📧 Email sent
└─ 20:00 BRT 📊 RELATÓRIO DIÁRIO ✅ ← AQUI VOCÊ SABE COM CERTEZA

AMANHÃ (Quinta 04/12):
├─ 05:00 BRT ⏰ Hourly collectors (7)
├─ 07:00 BRT 📅 Daily collectors (34) ← PRINCIPAL
├─ 08:00 BRT ⏰ Hourly collectors (7)
├─ 11:00 BRT ⏰ Hourly collectors (7)
├─ 14:00 BRT ⏰ Hourly collectors (7)
├─ 17:00 BRT ⏰ Hourly collectors (7)
├─ 19:00 BRT 📈 Analytics (33 reports)
├─ 19:30 BRT 📧 Email sent
└─ 20:00 BRT 📊 RELATÓRIO DIÁRIO ✅ ← CONFIRMAÇÃO TOTAL
```

---

## 🎯 RESPOSTA DIRETA

**QUANDO VOU SABER?**

### Opção 1: Teste Manual (Agora)
```bash
ssh ubuntu@SERVER
cd /home/ubuntu/sofia-pulse
bash install-crontab-with-daily-report.sh
python3 scripts/utils/daily_report_generator.py /var/log/sofia
```
→ **Em 2 minutos você recebe o 1º WhatsApp**

### Opção 2: Primeira Execução Automática (Hoje)
```
20:00 BRT (23:00 UTC) - Daqui a ~9h30
```
→ **Relatório diário completo no WhatsApp**

### Opção 3: Confirmação Total (Amanhã)
```
07:00 BRT (10:00 UTC) - Quinta de manhã
```
→ **34 collectors rodam + alertas imediatos**

```
20:00 BRT (23:00 UTC) - Quinta à noite
```
→ **Relatório mostra TUDO que rodou no dia**

---

**IMPORTANTE**: O cron só funciona no **servidor Ubuntu**, não no Windows/WSL!

**Status Atual**: ❌ Não instalado
**Depois de instalar**: ✅ Funcionando automaticamente
**Primeira confirmação**: 🕐 Hoje 20:00 BRT (se instalar nas próximas horas)

---

**Criado**: 03 Dec 2025
**Hora**: ~10:30 BRT (13:30 UTC)
**Próxima execução**: 11:00 BRT se instalar agora
