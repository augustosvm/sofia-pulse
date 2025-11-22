# 📱 Sofia + WhatsApp Integration Guide

**Integração completa entre Sofia API (análise técnica) e WhatsApp Business (alertas)**

---

## 🎯 O Que Foi Criado

Sistema de alertas inteligentes que:
1. **Detecta** erros/anomalias nos collectors
2. **Consulta** a Sofia API para análise técnica
3. **Envia** alerta com solução para WhatsApp

**Antes (alerta simples):**
```
❌ Erro na API XYZ
Status: 500
```

**Agora (com análise da Sofia):**
```
❌ Erro na API XYZ
Status: 500

--- Análise da Sofia ---
Causa provável: Rate limit excedido
Solução: Implementar exponential backoff
Impacto: Coleta pausada temporariamente
Ação: Aguardar reset em 15 minutos
```

---

## 📁 Arquivos Criados

```
scripts/utils/
├── sofia_whatsapp_integration.py  ← Módulo principal (integração)
└── whatsapp_alerts.py             ← Módulo básico (apenas envio)

scripts/
└── example-alert-with-sofia.py    ← Exemplos de uso

test-sofia-whatsapp.sh              ← Script de teste
SOFIA-WHATSAPP-INTEGRATION.md       ← Esta documentação
```

---

## 🚀 Quick Start (3 passos)

### 1. Configure .env

```bash
nano .env
```

Adicione (use seus números reais):

```bash
# WhatsApp Configuration
WHATSAPP_NUMBER=5527988024062           # Seu número (recebe mensagens)
WHATSAPP_SENDER=551151990773            # Business number (envia mensagens)
SOFIA_API_URL=http://localhost:8001/api/v2/chat
WHATSAPP_ENABLED=true
```

### 2. Teste a Integração

```bash
chmod +x test-sofia-whatsapp.sh
bash test-sofia-whatsapp.sh
```

**Output esperado:**
```
✅ Sofia API is running
✅ Sofia API responding correctly
✅ Integration module working!
✅ ALL TESTS PASSED
```

### 3. Execute Exemplos

```bash
python3 scripts/example-alert-with-sofia.py
```

Menu interativo com 6 exemplos prontos!

---

## 💻 Como Usar (Código)

### Exemplo 1: Erro em API Externa

```python
from scripts.utils.sofia_whatsapp_integration import alert_api_error

# Detectou erro em API? Envia alerta com análise da Sofia
alert_api_error(
    api_name="Bressan API",
    status_code=500,
    error_message="Internal Server Error",
    endpoint="/api/v1/transactions"
)
```

**Resultado no WhatsApp:**
```
🚨 Erro na Bressan API

Detalhes:
- API: Bressan API
- Status: 500
- Erro: Internal Server Error
- Endpoint: /api/v1/transactions
- Timestamp: 2025-11-22 10:30:00

---
Análise da Sofia:
[Análise técnica completa aqui]

---
Sofia Pulse - 2025-11-22 10:30:00
```

### Exemplo 2: Collector Falhou

```python
from scripts.utils.sofia_whatsapp_integration import alert_collector_failed

alert_collector_failed(
    collector_name="collect-github-trending",
    error="HTTP 403 - Rate limit exceeded"
)
```

### Exemplo 3: Anomalia nos Dados

```python
from scripts.utils.sofia_whatsapp_integration import alert_data_anomaly

alert_data_anomaly(
    table_name="funding_rounds",
    anomaly_type="Queda abrupta de registros",
    details="Esperado 50, recebido 3"
)
```

### Exemplo 4: Alerta Customizado

```python
from scripts.utils.sofia_whatsapp_integration import SofiaWhatsAppIntegration

integration = SofiaWhatsAppIntegration()

integration.alert_with_analysis(
    title="Disk Full - Backup Failed",
    error_details={
        'Sistema': 'PostgreSQL Backup',
        'Espaço': '0 MB disponível',
        'Necessário': '2.5 GB',
        'Criticidade': 'ALTA'
    },
    ask_sofia=True  # Pede análise da Sofia
)
```

### Exemplo 5: Apenas Consultar Sofia (sem WhatsApp)

```python
from scripts.utils.sofia_whatsapp_integration import ask_sofia

# Apenas perguntar à Sofia (não envia WhatsApp)
response = ask_sofia("""
Meu servidor tem:
- Disco 95% cheio
- CPU 80% constante
- RAM 90% usada

Qual a ordem de prioridade?
""")

print(response)  # Imprime resposta da Sofia
```

---

## 🔧 Integração com Collectors Existentes

### Antes (collector sem análise):

```python
# collect-github-trending.ts
try {
    response = await fetch(GITHUB_API)
    if (!response.ok) {
        console.error('GitHub API failed')
    }
} catch (error) {
    console.error('Error:', error)
}
```

### Depois (com Sofia + WhatsApp):

```python
# collect-github-trending.py (adaptado)
import sys
sys.path.append('scripts/utils')
from sofia_whatsapp_integration import alert_api_error

try:
    response = requests.get(GITHUB_API)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    # Alerta automático com análise da Sofia
    alert_api_error(
        api_name="GitHub API",
        status_code=e.response.status_code,
        error_message=str(e),
        endpoint=GITHUB_API
    )
    raise
```

---

## 📊 API da Sofia

### Endpoint

```
POST http://localhost:8001/api/v2/chat
```

**IMPORTANTE:** Só funciona em `localhost` (não aceita IP externo por segurança)

### Request

```json
{
  "query": "Sua pergunta ou contexto do erro",
  "user_id": "sistema-alertas",
  "channel": "whatsapp"
}
```

### Response

```json
{
  "response": "Análise técnica completa...",
  "context_sources": [...],
  "session_id": "...",
  "timestamp": "2025-11-22T10:30:00Z"
}
```

**Usar apenas:** `response.response`

---

## 🧪 Testes

### Teste Completo

```bash
bash test-sofia-whatsapp.sh
```

Verifica:
1. ✅ Sofia API rodando
2. ✅ Endpoint `/api/v2/chat` funcional
3. ✅ Módulo Python integrado

### Teste Manual (cURL)

```bash
# Teste direto na API
curl -X POST http://localhost:8001/api/v2/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Como resolver erro HTTP 500?",
    "user_id": "teste",
    "channel": "whatsapp"
  }'
```

### Teste Python

```python
python3 scripts/utils/sofia_whatsapp_integration.py
```

Executa teste completo com envio real para WhatsApp!

---

## ⚙️ Configuração Avançada

### Variáveis de Ambiente (.env)

```bash
# WhatsApp
WHATSAPP_NUMBER=5527988024062           # REQUIRED: Seu número
WHATSAPP_SENDER=551151990773            # REQUIRED: Business number
WHATSAPP_ENABLED=true                   # true/false

# Sofia API
SOFIA_API_URL=http://localhost:8001/api/v2/chat  # API endpoint
```

### Desabilitar WhatsApp Temporariamente

```bash
export WHATSAPP_ENABLED=false
```

Agora os alertas **não serão enviados**, mas Sofia ainda será consultada.

### Timeout da Sofia

Por padrão: **30 segundos** (permite processamento de AI)

Para alterar:

```python
integration = SofiaWhatsAppIntegration()
# Modificar timeout no código do módulo (linha ~37)
```

---

## 🔍 Troubleshooting

### ❌ "Cannot connect to Sofia API"

**Causa:** Sofia API não está rodando

**Solução:**
```bash
docker ps | grep sofia
# Se não aparecer:
docker restart sofia-mastra-api
```

### ❌ "WhatsApp failed: HTTP 400"

**Causa:** Número de WhatsApp inválido ou não autorizado

**Solução:**
1. Verificar formato do número: `5527988024062` (sem +, sem espaços)
2. Verificar se número está autorizado no WhatsApp Business API
3. Checar `.env`: `WHATSAPP_NUMBER` configurado?

### ❌ "Sofia API timeout"

**Causa:** Sofia está processando (AI leva tempo)

**Solução:**
- Normal em primeira consulta (carregando modelo)
- Se persistir: verificar logs do Docker
```bash
docker logs sofia-mastra-api --tail 100
```

### ❌ "Module not found: sofia_whatsapp_integration"

**Causa:** Python não encontra o módulo

**Solução:**
```python
import sys
sys.path.insert(0, 'scripts/utils')
from sofia_whatsapp_integration import ...
```

---

## 📈 Monitoramento Automático

Exemplo de script que monitora APIs e envia alertas automáticos:

```python
# monitor-apis.py
from scripts.utils.sofia_whatsapp_integration import alert_api_error
import requests
import time

APIS = [
    'https://api.github.com/rate_limit',
    'https://api.example.com/health',
    # Suas APIs aqui
]

while True:
    for api_url in APIS:
        try:
            r = requests.get(api_url, timeout=10)
            if r.status_code != 200:
                alert_api_error(
                    api_name=api_url.split('/')[2],  # Domain name
                    status_code=r.status_code,
                    error_message=r.text[:100],
                    endpoint=api_url
                )
        except Exception as e:
            alert_api_error(
                api_name=api_url.split('/')[2],
                status_code=0,
                error_message=str(e),
                endpoint=api_url
            )

    time.sleep(300)  # Check every 5 minutes
```

Execute em background:
```bash
nohup python3 monitor-apis.py > monitor.log 2>&1 &
```

---

## 🔐 Segurança

### ✅ Práticas Seguras Implementadas

1. **Números mascarados no código** (usam variáveis de ambiente)
2. **`.env` no `.gitignore`** (nunca commitado)
3. **Sofia API apenas localhost** (não exposta externamente)
4. **Timeout configurado** (previne DoS)
5. **Error handling completo** (não vaza informações sensíveis)

### ⚠️ Importante

- **NUNCA** commite arquivos `.env`
- **SEMPRE** use `YOUR_WHATSAPP_NUMBER` em docs/exemplos
- **ROTACIONE** tokens se repositório foi público
- **VERIFIQUE** `.gitignore` está configurado

---

## 📚 Referências

### Arquivos do Projeto

- **Módulo principal:** `scripts/utils/sofia_whatsapp_integration.py`
- **Exemplos:** `scripts/example-alert-with-sofia.py`
- **Testes:** `test-sofia-whatsapp.sh`
- **Config:** `.env` (criar a partir de `.env.example`)

### APIs

- **Sofia API:** `http://localhost:8001/api/v2/chat`
- **Health check:** `http://localhost:8001/health`
- **WhatsApp:** Via Sofia API (abstrato)

### Documentos Relacionados

- `README-WHATSAPP-SETUP.md` - Setup inicial WhatsApp
- `README-ALERTS.md` - Sistema de alertas
- `SECURITY-FIX-WHATSAPP.md` - Correções de segurança

---

## ✅ Checklist de Integração

- [ ] `.env` configurado com números reais
- [ ] Sofia API rodando (`docker ps | grep sofia`)
- [ ] Teste passou (`bash test-sofia-whatsapp.sh`)
- [ ] Exemplo executado (`python3 scripts/example-alert-with-sofia.py`)
- [ ] Mensagem recebida no WhatsApp
- [ ] Integrado com pelo menos 1 collector
- [ ] Monitoramento automático configurado (opcional)

---

## 📞 Suporte

**Em caso de problemas:**

1. **Verificar logs:**
   ```bash
   docker logs sofia-mastra-api --tail 100
   ```

2. **Testar API manualmente:**
   ```bash
   bash test-sofia-whatsapp.sh
   ```

3. **Verificar configuração:**
   ```bash
   cat .env | grep WHATSAPP
   ```

4. **Executar exemplo simples:**
   ```python
   python3 scripts/example-alert-with-sofia.py
   # Escolher opção 5 (apenas Sofia, sem WhatsApp)
   ```

---

**Status:** ✅ Sistema completo e testado
**Última atualização:** 2025-11-22
**Versão:** 1.0
