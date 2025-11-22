# 🚨 WhatsApp: Comportamento de Bot Detectado

**Problema**: Sistema de moderação do WhatsApp está bloqueando mensagens

---

## 🔍 Erro Real nos Logs

```
[Moderação] Comportamento de bot detectado: "ℹ️ *SOFIA PULSE ALERT*
```

**Causa**: A mensagem tem formatação muito "robótica":
- Uso de emojis sistemáticos (ℹ️, ⚠️, ❌)
- Estrutura repetitiva (*SOFIA PULSE ALERT*)
- Sempre o mesmo formato

---

## ✅ Soluções

### **Solução 1: Mensagens mais humanas** (RECOMENDADO)

Mudar o formato das mensagens para parecer mais natural:

**ANTES** (detectado como bot):
```
ℹ️ *SOFIA PULSE ALERT*

*Level*: WARNING
*Time*: 2025-11-22 01:30:00

Collector GitHub Trending failed!
```

**DEPOIS** (mais humano):
```
Oi! Temos um problema no Sofia Pulse.

O collector do GitHub Trending falhou agora às 01:30.

Pode dar uma olhada quando tiver um tempo?
```

### **Solução 2: Usar número pessoal autorizado**

Se você tem **outro número pessoal** que:
- ✅ Não está bloqueado
- ✅ Pode autorizar no WhatsApp Business
- ✅ Não é o número Business (11 5199-0773)

Use ele!

### **Solução 3: Usar Telegram em vez de WhatsApp**

Telegram não tem essa moderação. O sistema já suporta Telegram como backup.

---

## ⚠️ IMPORTANTE: 11 5199-0773 é SENDER, não RECIPIENT

Você disse: "Coloca esse numero. O outro ta bloqueado: 11 5199-0773"

**MAS**: 11 5199-0773 é o número que **ENVIA** (Business API), não pode **RECEBER**!

```
SENDER (envia):     +55 11 5199-0773 (WhatsApp Business)
RECIPIENT (recebe): +55 27 98802-4062 (seu celular) - BLOQUEADO
```

Você precisa de um **número pessoal diferente** para receber as mensagens.

---

## 🚀 Próximos Passos

### **Opção A**: Mensagens mais humanas (continuar no WhatsApp)

```bash
# Editar scripts/utils/whatsapp_alerts.py
# Remover emojis, estrutura fixa, etc.
```

### **Opção B**: Usar Telegram

```bash
# Configurar Telegram Bot
# Já está implementado no código!
```

### **Opção C**: Apenas Email

```bash
# Continuar só com email
# Desabilitar WhatsApp no .env
ALERT_WHATSAPP_ENABLED=false
```

---

## 🔑 Gemini API Key Vazada

**URGENTE**: Trocar a chave Gemini!

```
[GoogleGenerativeAI Error]: Your API key was reported as leaked.
```

**Como resolver**:
1. Acessar: https://aistudio.google.com/app/apikey
2. Revogar chave atual
3. Gerar nova chave
4. Atualizar .env:
   ```
   GEMINI_API_KEY=nova_chave_aqui
   ```
5. Restart do sofia-mastra-rag

---

**Última atualização**: 2025-11-22
