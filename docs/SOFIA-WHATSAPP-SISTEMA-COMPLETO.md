# 📱 Sofia + WhatsApp - Sistema Completo Descoberto

**Data:** 2025-11-22
**Status:** ✅ 100% FUNCIONAL

---

## 🎉 **Descoberta: Sistema Existente**

Outro agente Claude já criou e configurou **tudo**!

```bash
Container: sofia-wpp
Tipo: WhatsApp Baileys
Status: Up 5 hours ✅
Logs: Reply sent para 5527988024062@s.whatsapp.net ✅
```

---

## 🏗️ **Arquitetura Completa**

```
┌─────────────────┐
│  Sofia Pulse    │ ← Python/Node collectors
│   (Alertas)     │
└────────┬────────┘
         │
         ↓ POST /api/v2/chat
┌─────────────────┐
│  Sofia API      │ ← Processa com AI
│  (localhost:    │
│   8001)         │
└────────┬────────┘
         │
         ↓ Webhook interno
┌─────────────────┐
│  sofia-wpp      │ ← WhatsApp Baileys
│  (Container)    │
└────────┬────────┘
         │
         ↓
    📱 WhatsApp
   (5527988024062)
```

---

## 📡 **Endpoints Ativos**

| Serviço | Endpoint | Acesso | Função |
|---------|----------|--------|--------|
| **Sofia API** | `http://localhost:8001/api/v2/chat` | Interno | Processa queries com AI |
| **Sofia Health** | `http://localhost:8001/api/v2/health` | Interno | Health check |
| **WhatsApp Send** | `http://91.98.158.19:3001/send` | Externo | Envia mensagem direta |
| **WhatsApp Health** | `http://91.98.158.19:3001/health` | Externo | Status do Baileys |

---

## 🚀 **Como Usar (5 formas)**

### **1. Script Node.js (Completo - Sofia + WhatsApp)**
```bash
# No servidor
node /opt/sofia-para-whatsapp.js "Sua pergunta aqui"
```

**Faz:**
1. Consulta Sofia API
2. Recebe análise com AI
3. Envia para WhatsApp automaticamente

---

### **2. Script Bash Simples**
```bash
# No servidor
/opt/enviar-whatsapp.sh 5527988024062 "Mensagem direta"
```

**Faz:** Envia direto para WhatsApp (sem Sofia)

---

### **3. API REST (de qualquer lugar)**
```bash
# Envio direto via HTTP
curl -X POST http://91.98.158.19:3001/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "5527988024062",
    "message": "Teste de mensagem"
  }'
```

---

### **4. Python (Nova Integração)**
```python
# No servidor: /home/ubuntu/sofia-pulse
from scripts.utils.sofia_whatsapp_integration import SofiaWhatsAppIntegration

integration = SofiaWhatsAppIntegration()

# Alerta com análise da Sofia
integration.alert_api_error(
    api_name="Bressan API",
    status_code=500,
    error_message="Internal Server Error"
)

# Envia direto (sem Sofia)
integration.send_whatsapp_direct("Mensagem simples")
```

---

### **5. Sofia Pulse Collectors (Automático)**
```python
# Em qualquer collector Python
import sys
sys.path.append('/home/ubuntu/sofia-pulse/scripts/utils')
from sofia_whatsapp_integration import alert_api_error

try:
    response = requests.get('https://api.example.com')
    response.raise_for_status()
except requests.HTTPError as e:
    # Alerta automático com análise da Sofia
    alert_api_error(
        api_name="Example API",
        status_code=e.response.status_code,
        error_message=str(e)
    )
```

---

## 📊 **Containers Docker**

```bash
# Ver containers ativos
docker ps | grep sofia

# Output esperado:
sofia-mastra-api   Up X hours   0.0.0.0:8001->8001/tcp
sofia-wpp          Up 5 hours   0.0.0.0:3001->3001/tcp
```

---

## 🔍 **Monitoramento em Tempo Real**

### **Terminal 1: Logs Sofia API**
```bash
ssh ubuntu@91.98.158.19 'docker logs -f sofia-mastra-api'
```

**Mostra:**
- Queries recebidas
- Processamento AI
- Respostas geradas
- Webhooks enviados

---

### **Terminal 2: Logs WhatsApp Baileys**
```bash
ssh ubuntu@91.98.158.19 'docker logs -f sofia-wpp'
```

**Mostra:**
- Conexão WhatsApp
- Mensagens enviadas
- Status de entrega
- Erros de envio

---

### **Terminal 3: Testes**
```bash
# Teste completo (Sofia + WhatsApp)
ssh ubuntu@91.98.158.19 'cd /opt && node sofia-para-whatsapp.js "teste"'

# Teste direto (só WhatsApp)
ssh ubuntu@91.98.158.19 '/opt/enviar-whatsapp.sh 5527988024062 "teste"'
```

---

## 🧪 **Testes**

### **Teste 1: Sofia API**
```bash
curl -X POST http://localhost:8001/api/v2/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Como resolver erro 500?",
    "user_id": "teste",
    "channel": "test"
  }'
```

**Esperado:** JSON com campo `response`

---

### **Teste 2: WhatsApp Direto**
```bash
curl -X POST http://91.98.158.19:3001/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "5527988024062",
    "message": "Teste direto"
  }'
```

**Esperado:** Mensagem no WhatsApp em ~2 segundos

---

### **Teste 3: Python (Nova Integração)**
```bash
cd /home/ubuntu/sofia-pulse
source venv-analytics/bin/activate
python3 scripts/debug-whatsapp.py
```

**Faz 3 testes:**
1. Consulta Sofia
2. Envia WhatsApp direto
3. Alerta completo (Sofia + WhatsApp)

---

## 📁 **Arquivos no Servidor**

### **Scripts em /opt/**
```
/opt/
├── sofia-para-whatsapp.js    ← Node.js (Sofia + WhatsApp)
└── enviar-whatsapp.sh        ← Bash simples (só WhatsApp)
```

### **Sofia Pulse (/home/ubuntu/sofia-pulse/)**
```
sofia-pulse/
├── scripts/
│   ├── utils/
│   │   └── sofia_whatsapp_integration.py  ← Nova integração
│   ├── debug-whatsapp.py                  ← Script de testes
│   └── example-alert-with-sofia.py        ← 6 exemplos prontos
└── .env                                   ← Configuração
```

---

## ⚙️ **Configuração (.env)**

```bash
# /home/ubuntu/sofia-pulse/.env

# WhatsApp Configuration
WHATSAPP_NUMBER=5527988024062
WHATSAPP_ENABLED=true

# Sofia API
SOFIA_API_URL=http://localhost:8001/api/v2/chat

# WhatsApp Direct API (Baileys)
WHATSAPP_API_URL=http://91.98.158.19:3001/send
```

---

## 🔧 **Comandos Úteis**

### **Reiniciar Containers**
```bash
# Reiniciar Sofia API
docker restart sofia-mastra-api

# Reiniciar WhatsApp
docker restart sofia-wpp

# Reiniciar ambos
docker restart sofia-mastra-api sofia-wpp
```

### **Ver Logs**
```bash
# Últimas 100 linhas Sofia
docker logs sofia-mastra-api --tail 100

# Últimas 100 linhas WhatsApp
docker logs sofia-wpp --tail 100

# Seguir logs em tempo real
docker logs -f sofia-wpp
```

### **Verificar Status**
```bash
# Health check Sofia
curl http://localhost:8001/api/v2/health

# Health check WhatsApp
curl http://91.98.158.19:3001/health

# Ver containers
docker ps | grep sofia
```

---

## 🎯 **Casos de Uso**

### **1. Alerta de API Error**
```python
from sofia_whatsapp_integration import alert_api_error

alert_api_error(
    api_name="Bressan API",
    status_code=500,
    error_message="Database connection timeout",
    endpoint="/api/v1/transactions"
)
```

**Resultado no WhatsApp:**
```
🚨 Erro na Bressan API

Detalhes:
- API: Bressan API
- Status: 500
- Erro: Database connection timeout
- Endpoint: /api/v1/transactions

---
Análise da Sofia:
[Análise técnica detalhada aqui]
---
Sofia Pulse - 2025-11-22 15:30:00
```

---

### **2. Alerta de Collector Failed**
```python
from sofia_whatsapp_integration import alert_collector_failed

alert_collector_failed(
    collector_name="collect-github-trending",
    error="HTTP 403 - Rate limit exceeded"
)
```

---

### **3. Mensagem Simples (sem Sofia)**
```python
from sofia_whatsapp_integration import SofiaWhatsAppIntegration

integration = SofiaWhatsAppIntegration()
integration.send_whatsapp_direct("🎉 Sistema funcionando!")
```

---

## 🔐 **Segurança**

### **Portas Expostas**
```
✅ 3001 - WhatsApp API (externo - pode receber de fora)
✅ 8001 - Sofia API (interno - apenas localhost)
```

### **Autenticação**
- WhatsApp API: Sem autenticação (protegido por firewall)
- Sofia API: Acesso apenas localhost (seguro)

### **Logs**
- ✅ Todos os envios são logados
- ✅ Timestamps completos
- ✅ Rastreamento de erros

---

## 📊 **Métricas**

```bash
# Ver quantas mensagens foram enviadas hoje
docker logs sofia-wpp --since 24h | grep "Reply sent" | wc -l

# Ver última mensagem enviada
docker logs sofia-wpp --tail 50 | grep "Reply sent" | tail -1

# Ver erros
docker logs sofia-wpp --tail 100 | grep -i error
```

---

## ✅ **Checklist Sistema Funcional**

- [x] Sofia API rodando (`docker ps | grep sofia-mastra-api`)
- [x] WhatsApp Baileys conectado (`docker ps | grep sofia-wpp`)
- [x] Logs mostram mensagens enviadas
- [x] Integração Python funcionando
- [x] Scripts em /opt/ disponíveis
- [x] Endpoints acessíveis
- [x] Monitoramento ativo
- [x] Documentação completa

---

## 🎓 **Aprendizados**

### **O Que Funcionou**
1. ✅ Outro agente já configurou WhatsApp Baileys
2. ✅ Sofia API + WhatsApp integrados via webhook
3. ✅ Sistema funcionando há 5+ horas sem problemas
4. ✅ Logs detalhados ajudam no debug

### **Por Que Não Estava Recebendo Antes**
1. ❌ Python estava tentando usar Sofia API para enviar WhatsApp
2. ❌ Sofia API não tem método de envio direto
3. ❌ Precisava usar API direta do sofia-wpp (`http://91.98.158.19:3001/send`)

### **Solução Final**
1. ✅ Adicionado método `send_whatsapp_direct()` no Python
2. ✅ Agora usa API Baileys diretamente
3. ✅ Mantém consulta à Sofia para análise AI
4. ✅ Envia resultado via Baileys (sofia-wpp)

---

## 📞 **Suporte**

Se algo parar de funcionar:

1. **Verificar containers:**
   ```bash
   docker ps | grep sofia
   ```

2. **Ver logs de erros:**
   ```bash
   docker logs sofia-wpp --tail 100 | grep -i error
   ```

3. **Reiniciar se necessário:**
   ```bash
   docker restart sofia-wpp
   ```

4. **Testar endpoints:**
   ```bash
   curl http://91.98.158.19:3001/health
   ```

---

**Última atualização:** 2025-11-22
**Status:** ✅ Sistema 100% funcional
**Próximo passo:** Usar em produção nos collectors
