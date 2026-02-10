# notify.whatsapp

Envia notificações via WhatsApp usando API Baileys nativa do projeto.

## Resumo

- **Categoria:** notification
- **LLM:** Não
- **Custo:** 0 (usa API própria)
- **Retryable:** Sim (erros HTTP)

## Uso

```python
from lib.skill_runner import run

result = run("notify.whatsapp", {
    "to": "admin",  # ou número direto: "5527988024062"
    "severity": "critical",  # info | warning | critical
    "title": "Daily Pipeline UNHEALTHY",
    "message": "3 collectors falharam...",
    "summary": {
        "Failed": 3,
        "Missing": 1
    }
})
```

## Input Schema

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `to` | string | Não | Destinatário: "admin" (usa WHATSAPP_ADMIN_NUMBER) ou número com DDD |
| `severity` | enum | Não | Severidade: "info" \| "warning" \| "critical" (default: "info") |
| `title` | string | Sim | Título da notificação (max 100 chars) |
| `message` | string | Sim | Corpo da mensagem (max 4000 chars) |
| `summary` | object | Não | Dados estruturados para adicionar ao final |

## Output Schema

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `sent` | boolean | True se mensagem foi enviada com sucesso |
| `to` | string | Número de destino usado |
| `api_status` | integer | HTTP status code da API WhatsApp (se enviado) |
| `message_preview` | string | Preview dos primeiros 100 caracteres |

## Variáveis de Ambiente

| Variável | Obrigatória | Default | Descrição |
|----------|-------------|---------|-----------|
| `WHATSAPP_API_URL` | Sim | `http://localhost:3001/send` | URL da API WhatsApp (Baileys) |
| `WHATSAPP_ADMIN_NUMBER` | Sim | `5527988024062` | Número do admin (fallback: WHATSAPP_NUMBER) |
| `WHATSAPP_ENABLED` | Não | `true` | Se false, skill retorna ok mas não envia |

## Formato da Mensagem

A skill formata automaticamente a mensagem usando WhatsApp markdown:

```
🚨 *Título da Notificação*

Corpo da mensagem aqui...

*Summary:*
• Campo1: Valor1
• Campo2: Valor2
```

### Emojis por Severidade

- `info` → ℹ️
- `warning` → ⚠️
- `critical` → 🚨

## Exemplos

### 1. Alerta Crítico (Admin)

```python
run("notify.whatsapp", {
    "to": "admin",
    "severity": "critical",
    "title": "Production Database Down",
    "message": "PostgreSQL não está respondendo há 5 minutos.\n\nCheck urgente necessário!"
})
```

### 2. Info Simples

```python
run("notify.whatsapp", {
    "severity": "info",
    "title": "Backup Completo",
    "message": "Backup diário concluído com sucesso.",
    "summary": {
        "Size": "2.3 GB",
        "Duration": "18 min"
    }
})
```

### 3. Warning com Número Direto

```python
run("notify.whatsapp", {
    "to": "5511987654321",
    "severity": "warning",
    "title": "High CPU Usage",
    "message": "CPU acima de 80% por 10 minutos."
})
```

## Error Codes

| Código | Retryable | Quando |
|--------|-----------|--------|
| `INVALID_INPUT` | false | title ou message ausentes |
| `HTTP_REQUEST_FAILED` | true | API WhatsApp retornou erro |
| `TIMEOUT` | true | API não respondeu em 10s |
| `UNKNOWN_ERROR` | false | Erro inesperado |

## Integração com API WhatsApp

A skill NÃO fala direto com Baileys. Ela faz POST para uma API HTTP intermediária:

```http
POST {WHATSAPP_API_URL}
Content-Type: application/json

{
  "to": "5527988024062",
  "message": "🚨 *Título*\n\nMensagem..."
}
```

**Importante:** A API WhatsApp deve estar rodando separadamente (geralmente em Docker na porta 3001).

## Dry Run

```python
result = run("notify.whatsapp", {
    "title": "Teste",
    "message": "Mensagem de teste"
}, dry_run=True)

# Output:
# {
#   "ok": true,
#   "data": {
#     "sent": false,
#     "to": "5527988024062",
#     "message_preview": "ℹ️ *Teste*\n\nMensagem de teste",
#     "dry_run": true
#   }
# }
```

## Logs

A skill NÃO loga automaticamente. Use `logger.event` separadamente se necessário:

```python
result = run("notify.whatsapp", {...})

if result["ok"]:
    run("logger.event", {
        "level": "info",
        "event": "whatsapp.notification_sent",
        "skill": "my_script",
        "to": result["data"]["to"]
    })
```

## Arquitetura

```
scripts/notify_unhealthy.py
    ↓ (usa runner)
skills/notify_whatsapp/
    ↓ (HTTP POST)
WhatsApp API (Baileys)
    ↓ (protocolo WhatsApp)
Destinatário (celular)
```

**Separação de responsabilidades:**
- `notify.whatsapp` = skill genérica reutilizável
- `notify_unhealthy.py` = caso de uso específico (daily pipeline)
- WhatsApp API = infraestrutura (Baileys)

## Troubleshooting

### "HTTP_REQUEST_FAILED"
- Verificar se WhatsApp API está rodando: `curl http://localhost:3001/health`
- Verificar WHATSAPP_API_URL no .env

### "TIMEOUT"
- API WhatsApp pode estar sobrecarregada ou Baileys travado
- Restart: `docker restart whatsapp-api`

### Mensagem não chega
- Verificar se número está correto (com DDD e código país)
- Verificar se WhatsApp API está conectado (QR Code escaneado)
- Checar logs da API WhatsApp

## Ver Também

- `scripts/notify_unhealthy.py` - Exemplo de uso
- `scripts/utils/whatsapp_notifier.py` - Integração legada (deprecated)
- `docs/crontab-example.txt` - Setup de notificações diárias
