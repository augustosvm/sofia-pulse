# 📱 Sofia Pulse - WhatsApp Alerts Setup

**Número configurado**: +55 XX XXXXX-XXXX (Augusto)

---

## 🚀 Setup Rápido

```bash
# 1. Configurar alertas WhatsApp
bash configure-alerts.sh

# 2. Testar alertas
python3 scripts/test-alerts.py

# 3. Pronto! Todas as falhas serão enviadas automaticamente
```

---

## ✅ O que está configurado

### Alertas Automáticos (WhatsApp)

**Quando você recebe alertas:**

1. **🚨 Collector Falhou**
   - Quando qualquer coletor falha
   - Mostra o erro e onde ver o log

2. **⚠️ Anomalia nos Dados**
   - Quando detecta 0 linhas (esperava 100+)
   - Quando detecta spike anormal (10x o normal)
   - Quando detecta dados no futuro

3. **ℹ️ API Rate Limit**
   - Quando GitHub/Reddit bloqueia (429)
   - Mostra quando o limite reseta

4. **🚨 Healthcheck Falhou**
   - Quando vários coletores estão falhando
   - Mostra quantos falharam

5. **⚠️ Sanity Check Falhou**
   - Quando validação de dados detecta problemas
   - Lista as 5 principais issues

---

## 📡 Como Funciona

```
Collector falha
     ↓
scripts/utils/logger.py detecta erro
     ↓
scripts/utils/alerts.py → alert_collector_failed()
     ↓
scripts/utils/whatsapp_alerts.py
     ↓
POST http://localhost:8001/api/v2/chat
     ↓
sofia-mastra-rag processa
     ↓
Mensagem WhatsApp enviada para +55 XX XXXXX-XXXX
```

---

## 🧪 Testar Alertas

```bash
# Teste completo (envia 4 mensagens)
python3 scripts/test-alerts.py

# Teste manual
python3 -c "
from scripts.utils.whatsapp_alerts import test_whatsapp_alert
test_whatsapp_alert()
"
```

Você deve receber:
1. ✅ Alerta de teste
2. 🚨 Simulação de falha de coletor
3. ⚠️ Simulação de anomalia
4. ℹ️ Simulação de rate limit

---

## 🔧 Configuração (.env)

```bash
# WhatsApp Configuration (via sofia-mastra-rag)
WHATSAPP_NUMBER=YOUR_WHATSAPP_NUMBER
SOFIA_API_ENDPOINT=http://localhost:8001/api/v2/chat
ALERT_WHATSAPP_ENABLED=true
```

---

## 📊 Monitoramento Automático

### Healthcheck (a cada 30 min)

```bash
# Adicionar ao cron
*/30 * * * * cd /home/ubuntu/sofia-pulse && bash healthcheck-collectors.sh
```

- Se ≥1 coletor falhar → você recebe WhatsApp

### Sanity Check (após cada coleta)

```bash
# Adicionar aos scripts de coleta
python3 scripts/sanity-check.py || echo "Sanity check failed (alert sent)"
```

- Se detectar anomalia → você recebe WhatsApp

---

## 🎯 Tipos de Alertas

### CRITICAL (🚨)
- Collector falhou completamente
- Múltiplos coletores falhando
- Database inacessível

### WARNING (⚠️)
- Anomalia nos dados (volume baixo/alto)
- Dados duplicados
- Dados muito antigos

### INFO (ℹ️)
- API rate limit (normal)
- Retry automático funcionando

---

## 📱 Exemplo de Mensagem WhatsApp

```
🚨 SOFIA PULSE ALERT

Level: CRITICAL
Time: 2025-11-22 10:30:15

Collector Failed

Collector: collect-github-trending.ts
Error: HTTP 403 - Rate limited

Check logs:
/var/log/sofia/collectors/collect-github-trending.ts.log

---
Sofia Pulse Intelligence System
```

---

## 🔍 Troubleshooting

### Não recebeu alerta?

1. **Verificar sofia-mastra-rag está rodando:**
   ```bash
   curl http://localhost:8001/api/v2/chat \
     -H "Content-Type: application/json" \
     -d '{"query":"teste","user_id":"pulse"}'
   ```

2. **Verificar configuração:**
   ```bash
   grep -E "WHATSAPP_|SOFIA_API" .env
   ```

3. **Testar manualmente:**
   ```bash
   python3 scripts/test-alerts.py
   ```

### Sofia API não responde?

```bash
# Ver logs do sofia-mastra-rag
docker logs sofia-mastra-api

# Ou se rodando com PM2
pm2 logs sofia-mastra-api
```

---

## 🚀 Próximos Passos

1. ✅ Configurar alertas (feito!)
2. ✅ Testar alertas
3. ⏳ Rodar coleta completa: `bash run-all-with-monitoring.sh`
4. ⏳ Verificar se recebe alertas em falhas reais
5. ⏳ Agendar healthcheck no cron

---

**Contato**: +55 XX XXXXX-XXXX (Augusto)
**Email**: augustosvm@gmail.com
