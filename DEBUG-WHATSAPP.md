# 🔍 DEBUG - WhatsApp Não Chegou

**Status**: Email ✅ | WhatsApp ❌

**Sintoma**: API retorna HTTP 200 mas mensagem não chega no celular

---

## 🔍 Diagnóstico

### ✅ O que ESTÁ funcionando:
1. sofia-mastra-rag API acessível (localhost:8001)
2. API retorna HTTP 200 (request aceito)
3. Payload correto identificado:
   ```json
   {
     "query": "mensagem",
     "user_id": "sofia-pulse",
     "channel": "whatsapp",
     "phone": "YOUR_WHATSAPP_NUMBER"
   }
   ```

### ❌ O que NÃO está funcionando:
- Mensagem não chega no WhatsApp do usuário (+55 XX XXXXX-XXXX)

---

## 🔎 Possíveis Causas

### 1. Número não autorizado no WhatsApp Business API ⚠️ **MAIS PROVÁVEL**

**Problema**: O número +55 XX XXXXX-XXXX não está na lista de números autorizados.

**Como funciona WhatsApp Business API:**
- Você cria uma conta Business com +55 XX XXXXX-XXXX (Business)
- Você REGISTRA quais números podem RECEBER mensagens
- Só números registrados recebem mensagens
- API aceita request (200) mas descarta silenciosamente

**Solução**:
1. Acessar painel do WhatsApp Business API
2. Ir em "Phone Numbers" ou "Números Autorizados"
3. Adicionar +55 XX XXXXX-XXXX à lista
4. Aguardar aprovação (pode levar minutos)

**Como verificar**:
```bash
# Verificar logs do sofia-mastra-rag
docker logs sofia-mastra-api | grep -i "whatsapp\|unauthorized\|forbidden"

# OU se PM2:
pm2 logs sofia-mastra-api | grep -i "whatsapp\|unauthorized"
```

Procurar por:
- "Unauthorized number"
- "Number not registered"
- "403 Forbidden"

---

### 2. WhatsApp Business sem créditos

**Problema**: Conta do WhatsApp Business sem saldo

**Solução**:
- Verificar saldo no painel do WhatsApp Business
- Adicionar créditos se necessário

---

### 3. sofia-mastra-rag não configurado corretamente

**Problema**: Backend não tem WhatsApp API key configurada

**Como verificar**:
```bash
# Acessar servidor do sofia-mastra-rag
ssh usuario@servidor-sofia-mastra-rag

# Verificar .env tem WhatsApp credentials
grep -E "WHATSAPP_|TWILIO_|META_" .env
```

Deve ter algo como:
```env
WHATSAPP_API_KEY=...
WHATSAPP_PHONE_ID=...
META_ACCESS_TOKEN=...
```

---

### 4. Número bloqueou o Business

**Problema**: Usuário bloqueou +55 XX XXXXX-XXXX (Business) no WhatsApp

**Solução**:
1. Abrir WhatsApp
2. Procurar conversas com +55 XX XXXXX-XXXX (Business)
3. Se estiver bloqueado, desbloquear

---

### 5. Mensagem foi para SPAM

**Problema**: WhatsApp classificou como spam

**Solução**:
1. Verificar pasta de spam no WhatsApp
2. Marcar como "Não é spam"

---

## 🚀 Próximos Passos

### PASSO 1: Verificar logs do sofia-mastra-rag

```bash
# Se Docker:
docker logs sofia-mastra-api --tail 100 | grep -i whatsapp

# Se PM2:
pm2 logs sofia-mastra-api --lines 100 | grep -i whatsapp
```

**Procurar por**:
- ✅ "WhatsApp message sent successfully"
- ❌ "Unauthorized number"
- ❌ "Insufficient credits"
- ❌ "Number not registered"

---

### PASSO 2: Verificar se número está autorizado

**Onde verificar**:
- Meta Business Suite (business.facebook.com)
- WhatsApp Business API Manager
- Painel do provedor (Twilio, MessageBird, etc.)

**O que fazer**:
1. Login no painel
2. Ir em "Phone Numbers" ou "Recipient Numbers"
3. Verificar se +55 XX XXXXX-XXXX está na lista
4. Se não estiver, adicionar e aguardar aprovação

---

### PASSO 3: Testar com número alternativo

Se tiver outro número autorizado, testar com ele:

```bash
# Editar .env temporariamente
WHATSAPP_NUMBER=5511999999999  # Número já autorizado

# Rodar teste
python3 scripts/test-whatsapp-api.py
```

Se funcionar = confirma que problema é autorização do número original

---

## 📞 Informações de Contato

**Recipient (você)**: +55 XX XXXXX-XXXX (precisa estar autorizado)
**Sender (Business)**: +55 XX XXXXX-XXXX (Business) (envia as mensagens)

---

## ✅ Checklist de Debug

- [ ] Logs do sofia-mastra-rag verificados
- [ ] Número +55 XX XXXXX-XXXX está autorizado no painel
- [ ] WhatsApp Business tem créditos
- [ ] Número +55 XX XXXXX-XXXX (Business) não está bloqueado
- [ ] Verificar pasta de spam no WhatsApp
- [ ] Testar com número alternativo (se tiver)

---

**Última atualização**: 2025-11-22
**Status**: Aguardando verificação de logs e autorização de número
