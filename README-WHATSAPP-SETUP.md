# 📱 Sofia Pulse - WhatsApp Setup Guide

**IMPORTANTE**: Entenda como funciona o sistema de WhatsApp

---

## 🔑 Conceitos Importantes

### Números Envolvidos

**1. Número Business (SENDER)** - Quem ENVIA as mensagens:
- **+55 11 5199-0773**
- É o número do WhatsApp Business da sofia-mastra-rag
- Configurado no backend sofia-mastra-rag
- É quem "assina" as mensagens

**2. Número Pessoal (RECIPIENT)** - Quem RECEBE as mensagens:
- **+55 27 98802-4062** (Augusto)
- É o seu número pessoal
- Aparece nas mensagens como destinatário
- Precisa estar autorizado no WhatsApp Business API

---

## ⚠️ Problema Comum

**"As mensagens não chegam"**

**Causa provável**: O número pessoal (+55 27 98802-4062) precisa estar **pré-autorizado** no WhatsApp Business API.

**Como funciona o WhatsApp Business API:**
1. Você cria uma conta Business com o número +55 11 5199-0773
2. Você REGISTRA quais números podem RECEBER mensagens
3. Só números registrados recebem mensagens da API

**Solução:**
- Verificar no painel do WhatsApp Business se +55 27 98802-4062 está autorizado
- Ou usar um número que já está autorizado para testes

---

## 🧪 Testar Integração

### 1. Atualizar Configuração

```bash
# Atualiza .env com números corretos
bash update-whatsapp-config.sh
```

Isso configura:
```env
WHATSAPP_NUMBER=5527988024062       # Recipient (seu número)
WHATSAPP_SENDER=551151990773        # Sender (WhatsApp Business)
SOFIA_API_ENDPOINT=http://localhost:8001/api/v2/chat
ALERT_WHATSAPP_ENABLED=true
```

### 2. Testar API Endpoint

```bash
# Testa conectividade e formatos de payload
python3 scripts/test-whatsapp-api.py
```

**O que esse script faz:**
- ✅ Verifica se sofia-mastra-rag está acessível
- ✅ Testa 3 formatos diferentes de payload
- ✅ Mostra exatamente qual resposta a API retorna
- ✅ Indica qual formato funcionou

### 3. Verificar Logs

```bash
# Se sofia-mastra-rag está em Docker
docker logs sofia-mastra-api

# Se está em PM2
pm2 logs sofia-mastra-api

# Procurar por:
# - WhatsApp send errors
# - Unauthorized number
# - API key errors
```

---

## 🔧 Troubleshooting

### Erro: "Unauthorized number"

**Problema**: Número +55 27 98802-4062 não está registrado no WhatsApp Business

**Solução**:
1. Acessar painel do WhatsApp Business API
2. Adicionar +55 27 98802-4062 à lista de números autorizados
3. Aguardar aprovação (pode levar alguns minutos)

### Erro: "Connection refused"

**Problema**: sofia-mastra-rag não está rodando

**Solução**:
```bash
# Verificar se está rodando
curl http://localhost:8001/health

# Se não estiver, iniciar
docker start sofia-mastra-api
# ou
pm2 start sofia-mastra-api
```

### Erro: "Invalid payload"

**Problema**: Formato do payload não está correto

**Solução**:
```bash
# Rodar script de teste para ver qual formato funciona
python3 scripts/test-whatsapp-api.py
```

O script testa 3 formatos:
1. **Format 1** (Current): `{query, user_id, channel, phone}`
2. **Format 2** (Direct): `{to, message, channel}`
3. **Format 3** (Simplified): `{message, phone}`

### Mensagem enviada mas não chegou

**Problema**: Mensagem foi aceita pela API mas não chegou no WhatsApp

**Possíveis causas**:
1. Número não autorizado no WhatsApp Business
2. WhatsApp Business não tem créditos
3. Número bloqueou o Business
4. Mensagem foi para spam

**Solução**:
1. Verificar logs do sofia-mastra-rag
2. Verificar painel do WhatsApp Business
3. Tentar com outro número autorizado

---

## 📋 Checklist de Setup

- [ ] sofia-mastra-rag está rodando (`curl localhost:8001/health`)
- [ ] WhatsApp Business configurado (+55 11 5199-0773)
- [ ] Número pessoal autorizado (+55 27 98802-4062)
- [ ] .env atualizado (`bash update-whatsapp-config.sh`)
- [ ] Teste de API executado (`python3 scripts/test-whatsapp-api.py`)
- [ ] Logs verificados (sem erros)
- [ ] Mensagem de teste recebida

---

## 🎯 Fluxo Correto

```
Sofia Pulse
    ↓
scripts/utils/whatsapp_alerts.py
    ↓
POST http://localhost:8001/api/v2/chat
    payload: {
        query: "mensagem",
        phone: "5527988024062"  ← Seu número (RECIPIENT)
    }
    ↓
sofia-mastra-rag processa
    ↓
WhatsApp Business API
    from: +55 11 5199-0773  ← Business (SENDER)
    to: +55 27 98802-4062   ← Você (RECIPIENT)
    ↓
Mensagem chega no seu WhatsApp ✅
```

---

## 🚀 Próximos Passos

### Se o teste funcionou:
```bash
# Teste completo de alertas
python3 scripts/test-alerts.py

# Rodar pipeline completo
bash run-all-with-monitoring.sh
```

### Se o teste falhou:
1. Verificar logs do sofia-mastra-rag
2. Verificar painel do WhatsApp Business
3. Confirmar número está autorizado
4. Testar com número alternativo (se tiver)

---

## 📞 Contatos

**Recipient (Você)**: +55 27 98802-4062
**Sender (Business)**: +55 11 5199-0773
**Email**: augustosvm@gmail.com

---

**Última atualização**: 2025-11-22
**Branch**: `claude/fix-github-rate-limits-012Xm4nfg6i34xKQHSDbWfq3`
