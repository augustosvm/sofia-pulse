# ⚡ Quick Start - Sofia + WhatsApp (3 minutos)

## 📥 1. No Servidor, Puxe as Mudanças

```bash
cd ~/sofia-pulse
git pull origin claude/fix-github-rate-limits-018sBR9un3QV4u2qhdW2tKNH
```

---

## ⚙️ 2. Configure .env

```bash
nano .env
```

**Adicione estas linhas** (com seus números reais):

```bash
# WhatsApp Configuration
WHATSAPP_NUMBER=5527988024062           # Seu número
WHATSAPP_SENDER=551151990773            # Business number
SOFIA_API_URL=http://localhost:8001/api/v2/chat
WHATSAPP_ENABLED=true
```

**Salve:** `Ctrl+O` → Enter → `Ctrl+X`

---

## 🧪 3. Teste a Integração

```bash
bash test-sofia-whatsapp.sh
```

**Esperado:**
```
✅ Sofia API is running
✅ Sofia API responding correctly
✅ Integration module working!
✅ ALL TESTS PASSED
```

Se der erro:
```bash
# Verificar se Sofia API está rodando
docker ps | grep sofia

# Se não estiver, reiniciar
docker restart sofia-mastra-api
```

---

## 📱 4. Envie Alerta de Teste

```bash
cd ~/sofia-pulse
source venv-analytics/bin/activate  # Ativa venv Python
python3 scripts/example-alert-with-sofia.py
```

**Menu interativo:**
```
1. Erro em API Externa (Bressan API)
2. Collector Falhou (GitHub)
3. Anomalia nos Dados (funding_rounds)
4. Alerta Customizado (Backup)
5. Apenas Consultar Sofia (sem WhatsApp)
6. Monitoramento de APIs (auto-detect)

Opção: _
```

**Escolha opção 1** para testar alerta completo

**Verifique seu WhatsApp!** Você deve receber:
```
🚨 Erro na Bressan API

Detalhes:
- API: Bressan API
- Status: 500
- Erro: Internal Server Error
...

--- Análise da Sofia ---
[Análise técnica aqui]
```

---

## 🚀 5. Use em Seus Collectors

**Exemplo simples:**

```python
# No seu collector Python
import sys
sys.path.append('/home/ubuntu/sofia-pulse/scripts/utils')
from sofia_whatsapp_integration import alert_api_error

try:
    response = requests.get('https://api.example.com')
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    # Alerta automático com análise da Sofia!
    alert_api_error(
        api_name="Example API",
        status_code=e.response.status_code,
        error_message=str(e),
        endpoint='https://api.example.com'
    )
```

---

## 📊 6. Exemplos Prontos

```python
# Erro em API
from sofia_whatsapp_integration import alert_api_error
alert_api_error("GitHub API", 403, "Rate limit")

# Collector falhou
from sofia_whatsapp_integration import alert_collector_failed
alert_collector_failed("collect-github", "HTTP 403")

# Anomalia nos dados
from sofia_whatsapp_integration import alert_data_anomaly
alert_data_anomaly("funding_rounds", "Queda", "Esperado 50, got 3")

# Apenas perguntar à Sofia (sem WhatsApp)
from sofia_whatsapp_integration import ask_sofia
response = ask_sofia("Como resolver erro 500 em API?")
print(response)
```

---

## 🔍 Troubleshooting

### ❌ "Cannot connect to Sofia API"

```bash
docker ps | grep sofia
# Se vazio:
docker restart sofia-mastra-api
```

### ❌ "WhatsApp failed"

```bash
# Verificar .env
cat .env | grep WHATSAPP
# Deve mostrar:
# WHATSAPP_NUMBER=5527988024062
# WHATSAPP_ENABLED=true
```

### ❌ "Module not found"

```bash
# Ativar venv
cd ~/sofia-pulse
source venv-analytics/bin/activate
```

---

## ✅ Checklist

- [ ] Git pull executado
- [ ] `.env` configurado com números reais
- [ ] `test-sofia-whatsapp.sh` passou ✅
- [ ] Exemplo executado (opção 1)
- [ ] Mensagem recebida no WhatsApp
- [ ] Pronto para integrar com collectors!

---

## 📚 Documentação Completa

**Leia:** `SOFIA-WHATSAPP-INTEGRATION.md`

**Contém:**
- Todos os exemplos de uso
- Integração com collectors
- Troubleshooting avançado
- Monitoramento automático
- API reference

---

**Tempo total:** ~3 minutos ⚡
**Próximo passo:** Integre com seus collectors!
