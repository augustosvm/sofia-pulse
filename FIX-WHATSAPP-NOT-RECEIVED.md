# 🔧 FIX: WhatsApp Messages Not Received

## ❌ **Problema Identificado**

Você viu:
```
✅ WhatsApp sent to YOUR_WHATSAPP_NUMBER
```

Ao invés de:
```
✅ WhatsApp sent to 5527988024062
```

**Causa:** O arquivo `.env` não existe ou não está sendo carregado pelo Python.

---

## ✅ **Solução (3 passos - 2 minutos)**

### **Passo 1: Pull das correções**

```bash
cd ~/sofia-pulse
git pull origin claude/fix-github-rate-limits-018sBR9un3QV4u2qhdW2tKNH
```

**Arquivos novos:**
- `install-whatsapp-deps.sh` - Instala dependências
- `setup-whatsapp-config.sh` - Configura .env interativo
- `scripts/utils/sofia_whatsapp_integration.py` - Atualizado com dotenv

---

### **Passo 2: Instalar dependências**

```bash
bash install-whatsapp-deps.sh
```

**Output esperado:**
```
✅ Virtual environment activated
✅ Dependencies installed
✅ python-dotenv: x.x.x
✅ requests: x.x.x
```

---

### **Passo 3: Configurar .env**

```bash
bash setup-whatsapp-config.sh
```

**Será perguntado:**
```
Seu número WhatsApp (ex: 5527988024062): 5527988024062
Número Business (enter para usar mesmo número): [ENTER]
```

**Output esperado:**
```
✅ .env file updated
✅ Sofia API is running
✅ Python can load WHATSAPP_NUMBER: 5527988024062
✅ SETUP COMPLETE
```

---

### **Passo 4: Testar novamente**

```bash
source venv-analytics/bin/activate
python3 scripts/example-alert-with-sofia.py
```

**Escolha opção 1**

**AGORA DEVE MOSTRAR:**
```
✅ WhatsApp sent to 5527988024062  ← SEU NÚMERO REAL!
```

**E você DEVE RECEBER a mensagem no WhatsApp!** 📱

---

## 🔍 **O Que Foi Mudado**

### **Antes (não funcionava):**

```python
# Tentava ler .env, mas .env não existia
WHATSAPP_NUMBER = os.getenv('WHATSAPP_NUMBER', 'YOUR_WHATSAPP_NUMBER')
```

**Resultado:** Usava o fallback `YOUR_WHATSAPP_NUMBER`

### **Depois (funciona):**

```python
# Agora carrega .env automaticamente com python-dotenv
from dotenv import load_dotenv
load_dotenv()  # Carrega /home/ubuntu/sofia-pulse/.env
WHATSAPP_NUMBER = os.getenv('WHATSAPP_NUMBER', 'YOUR_WHATSAPP_NUMBER')
```

**Resultado:** Lê o número real do arquivo `.env`

---

## 🧪 **Verificação Rápida**

### **Verificar que .env existe:**

```bash
cat .env | grep WHATSAPP
```

**Esperado:**
```
WHATSAPP_NUMBER=5527988024062
WHATSAPP_SENDER=5527988024062
SOFIA_API_URL=http://localhost:8001/api/v2/chat
WHATSAPP_ENABLED=true
```

### **Verificar que Python lê o .env:**

```bash
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('WHATSAPP_NUMBER:', os.getenv('WHATSAPP_NUMBER'))
"
```

**Esperado:**
```
WHATSAPP_NUMBER: 5527988024062
```

Se mostrar `None` ou `YOUR_WHATSAPP_NUMBER`, o .env não foi carregado.

---

## 📱 **Teste Completo (1 comando)**

```bash
bash test-sofia-whatsapp.sh
```

**Deve mostrar:**
```
✅ Sofia API is running
✅ Sofia API responding correctly
✅ WhatsApp sent to 5527988024062  ← Número real
✅ ALL TESTS PASSED
```

**E você deve receber mensagem no WhatsApp!**

---

## 🚨 **Se Ainda Não Funcionar**

### **1. Verificar Sofia API está rodando:**

```bash
docker ps | grep sofia
```

**Esperado:**
```
sofia-mastra-api   Up X hours   0.0.0.0:8001->8001/tcp
```

Se não estiver:
```bash
docker restart sofia-mastra-api
docker logs sofia-mastra-api --tail 50
```

### **2. Verificar número WhatsApp está correto:**

```bash
cat .env | grep WHATSAPP_NUMBER
```

**Deve ser:** `WHATSAPP_NUMBER=5527988024062` (sem espaços, sem +)

### **3. Testar Sofia API manualmente:**

```bash
curl -X POST http://localhost:8001/api/v2/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Teste manual",
    "user_id": "teste",
    "channel": "whatsapp",
    "phone": "5527988024062"
  }'
```

**Esperado:** Receber resposta JSON com campo `response`

### **4. Verificar logs do Docker:**

```bash
docker logs sofia-mastra-api --tail 100 | grep -i whatsapp
```

Procure por:
- ✅ "WhatsApp message sent"
- ❌ "WhatsApp error"
- ⚠️  "Invalid phone number"

---

## 📋 **Checklist Completo**

Execute em ordem:

```bash
# 1. Pull correções
cd ~/sofia-pulse
git pull origin claude/fix-github-rate-limits-018sBR9un3QV4u2qhdW2tKNH

# 2. Instalar dependências
bash install-whatsapp-deps.sh

# 3. Configurar .env
bash setup-whatsapp-config.sh

# 4. Testar
bash test-sofia-whatsapp.sh

# 5. Enviar alerta de exemplo
source venv-analytics/bin/activate
python3 scripts/example-alert-with-sofia.py
# Escolha opção 1

# 6. Verificar WhatsApp!
```

---

## ✅ **Confirmação de Sucesso**

Você saberá que está funcionando quando:

1. ✅ O script mostra: `✅ WhatsApp sent to 5527988024062` (número real)
2. ✅ Você recebe mensagem no WhatsApp
3. ✅ Mensagem contém "Análise da Sofia"

**Exemplo de mensagem que você vai receber:**

```
🚨 Erro na Bressan API

Detalhes:
- API: Bressan API
- Status: 500
- Erro: Internal Server Error
- Endpoint: /api/v1/transactions
- Timestamp: 2025-11-22 12:00:00

---
Análise da Sofia:
[Análise técnica detalhada aqui]
---

Sofia Pulse - 2025-11-22 12:00:00
```

---

## 🔐 **Segurança do .env**

**IMPORTANTE:**

```bash
# Verificar que .env NÃO está no git
cat .gitignore | grep .env
```

**Deve conter:**
```
.env
.env.local
.env.*.local
```

**NUNCA commite o .env!** Ele contém seus números de WhatsApp.

---

## 📞 **Suporte**

Se após seguir todos os passos ainda não funcionar:

1. **Envie os outputs de:**
   ```bash
   cat .env | grep WHATSAPP
   python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('WHATSAPP_NUMBER'))"
   docker ps | grep sofia
   ```

2. **Teste direto no Sofia API:**
   ```bash
   curl -X POST http://localhost:8001/api/v2/chat \
     -H "Content-Type: application/json" \
     -d '{"query": "teste", "user_id": "teste", "channel": "whatsapp", "phone": "5527988024062"}'
   ```

3. **Verifique se o número WhatsApp está autorizado** no WhatsApp Business API

---

**Arquivo:** `FIX-WHATSAPP-NOT-RECEIVED.md`
**Última atualização:** 2025-11-22
**Commit:** 7e510cc - Fix: WhatsApp .env loading + setup scripts
