# 🧪 How to Run WhatsApp Integration Tests

**IMPORTANT**: These tests must be run on your **actual server** (91.98.158.19 or wherever Sofia containers are running), not from a remote environment.

---

## ⚠️ Why 403 "Access Denied" Happens

The WhatsApp Baileys API at `http://91.98.158.19:3001/send` is configured to only accept requests from:
- Localhost on the server where containers run
- Authorized IP addresses
- Internal network

**You will get HTTP 403 if you run tests from**:
- ❌ Different machine
- ❌ Remote environment
- ❌ Claude Code sandbox
- ❌ External IP addresses

**Tests will work when run from**:
- ✅ The actual server (SSH into it)
- ✅ Localhost on that server
- ✅ Same network as the containers

---

## 🚀 Running Tests (Step-by-Step)

### Step 1: SSH into Your Server

```bash
# SSH into the server where Sofia containers are running
ssh ubuntu@91.98.158.19
# OR wherever your server is located
```

### Step 2: Navigate to Sofia Pulse Directory

```bash
cd /home/ubuntu/sofia-pulse
# OR wherever your sofia-pulse directory is
```

### Step 3: Verify Containers Are Running

```bash
docker ps | grep sofia
```

**Expected output**:
```
sofia-mastra-api   Up X hours   0.0.0.0:8001->8001/tcp
sofia-wpp          Up X hours   0.0.0.0:3001->3001/tcp
```

If containers are NOT running:
```bash
docker restart sofia-mastra-api sofia-wpp
```

### Step 4: Checkout Correct Branch

```bash
git fetch origin
git checkout claude/fix-github-rate-limits-018sBR9un3QV4u2qhdW2tKNH
git pull origin claude/fix-github-rate-limits-018sBR9un3QV4u2qhdW2tKNH
```

---

## 🧪 Test 1: Quick Test (No Sofia, Just WhatsApp)

This test bypasses Sofia API and sends directly to WhatsApp Baileys.

```bash
python3 test-whatsapp-quick.py
```

**Expected output**:
```
🧪 WhatsApp Integration Test
============================================================

TEST 1: Simple message
✅ Message sent successfully!

TEST 2: Formatted alert
✅ Message sent successfully!

✅ Tests complete!
```

**You should receive 2 WhatsApp messages** 📱

**If you see HTTP 403**:
- You're running from wrong location (not on the server)
- Containers might not be running
- WhatsApp API changed configuration

---

## 🧪 Test 2: Full Integration (Sofia + WhatsApp)

This test queries Sofia API for AI analysis, then sends to WhatsApp.

### 2a. Install Dependencies (First Time Only)

```bash
bash install-whatsapp-deps.sh
```

### 2b. Configure Environment (First Time Only)

```bash
bash setup-whatsapp-config.sh
```

**Enter when prompted**:
- WhatsApp number: `5527988024062`
- Business number: `[press ENTER to use same]`

### 2c. Run Full Integration Test

```bash
source venv-analytics/bin/activate
python3 scripts/debug-whatsapp.py
```

**Expected output**:
```
🔍 DEBUG WHATSAPP INTEGRATION - VERBOSE MODE
============================================================

📋 CONFIGURATION:
  • WHATSAPP_NUMBER: 5527988024062
  • SOFIA_API_URL: http://localhost:8001/api/v2/chat
  • WHATSAPP_ENABLED: true

TEST 1: Ask Sofia (consulta simples)
✅ Sofia respondeu: [Analysis here]

TEST 2: Send WhatsApp (envio direto)
✅ WhatsApp enviado com sucesso!

TEST 3: Alert with Analysis (fluxo completo)
✅ Alerta completo enviado!

🏁 DEBUG COMPLETE
```

**You should receive 2-3 WhatsApp messages** 📱

---

## 🧪 Test 3: Interactive Examples

```bash
source venv-analytics/bin/activate
python3 scripts/example-alert-with-sofia.py
```

**Choose an option**:
```
🎯 Sofia + WhatsApp Integration - Interactive Examples
============================================================
1. API Error Alert (exemplo completo)
2. Collector Failed Alert
3. Data Anomaly Alert
4. Custom Alert
5. Ask Sofia Only (sem WhatsApp)
6. Exit

Escolha (1-6): 1
```

**Each example will**:
1. Show you what it's doing
2. Ask Sofia for AI analysis
3. Send formatted alert to WhatsApp
4. Display result

---

## 🧪 Test 4: Curl Test (Direct API)

Most basic test - if this fails, API is not accessible.

```bash
curl -X POST http://localhost:3001/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "5527988024062",
    "message": "🎉 Curl test successful!"
  }'
```

**Expected response**:
```json
{"success":true,"to":"5527988024062@s.whatsapp.net"}
```

**If you get "Access denied"**:
- You're running from wrong machine
- Use `http://localhost:3001/send` not `http://91.98.158.19:3001/send`
- Check firewall rules

---

## 🧪 Test 5: Verify Sofia API Works

```bash
curl -X POST http://localhost:8001/api/v2/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Test query",
    "user_id": "test",
    "channel": "whatsapp"
  }'
```

**Expected response**:
```json
{"response":"[Sofia's AI analysis here]"}
```

---

## 🐛 Troubleshooting

### Problem: HTTP 403 "Access Denied"

**Cause**: Running from wrong location

**Solution**:
```bash
# Make sure you're ON the actual server:
ssh ubuntu@91.98.158.19

# Use localhost URLs:
# ✅ http://localhost:3001/send
# ❌ http://91.98.158.19:3001/send
```

### Problem: "Connection refused"

**Cause**: Containers not running

**Solution**:
```bash
docker ps | grep sofia
docker restart sofia-mastra-api sofia-wpp
docker logs sofia-wpp --tail 50
```

### Problem: File Not Found (debug-whatsapp.py)

**Cause**: Wrong git branch

**Solution**:
```bash
git checkout claude/fix-github-rate-limits-018sBR9un3QV4u2qhdW2tKNH
git pull
```

### Problem: "WHATSAPP_NUMBER: YOUR_WHATSAPP_NUMBER"

**Cause**: .env not configured

**Solution**:
```bash
bash setup-whatsapp-config.sh
# OR manually edit .env
nano .env
```

### Problem: Sofia API not responding

**Cause**: Container down or crashed

**Solution**:
```bash
docker restart sofia-mastra-api
docker logs sofia-mastra-api --tail 100
```

### Problem: WhatsApp not receiving messages

**Cause**: sofia-wpp container issue

**Solution**:
```bash
docker logs sofia-wpp --tail 100 | grep -i error
docker restart sofia-wpp
# Wait 30 seconds for reconnection
curl http://localhost:3001/health
```

---

## ✅ Success Checklist

After running tests, you should have:

- [ ] Received 2 messages from `test-whatsapp-quick.py`
- [ ] Received 2-3 messages from `debug-whatsapp.py`
- [ ] Curl test returned `{"success":true}`
- [ ] Sofia API returned JSON response
- [ ] Messages contain "Análise da Sofia" section
- [ ] Messages formatted correctly with emojis

---

## 📊 Expected Message Format

**Simple Test**:
```
🎉 Sofia Pulse - Sistema funcionando!
```

**Formatted Alert**:
```
🚨 ALERTA DE TESTE

API: Test API
Status: 200
Timestamp: 2025-11-22 12:00:00

---
Este é um teste do sistema Sofia Pulse.
Se você está vendo isto, o WhatsApp está 100% funcional!

---
Sofia Pulse Intelligence System
```

**Alert with Sofia Analysis**:
```
🚨 Erro na Bressan API

Detalhes:
- API: Bressan API
- Status: 500
- Erro: Internal Server Error
- Timestamp: 2025-11-22 12:00:00

---
Análise da Sofia:
[Detailed AI analysis from Sofia API here]
---

Sofia Pulse - 2025-11-22 12:00:00
```

---

## 🔐 Security Notes

**NEVER commit .env file**:
```bash
cat .gitignore | grep .env
# Should show: .env
```

**Use environment variables in production**:
- Don't hardcode WhatsApp numbers in scripts
- Use .env for all sensitive configuration
- Keep repository private if it contains any sensitive data

---

## 🚀 Next Steps After Tests Pass

Once all tests work:

1. **Integrate into collectors**:
   ```python
   from scripts.utils.sofia_whatsapp_integration import SofiaWhatsAppIntegration

   integration = SofiaWhatsAppIntegration()

   try:
       response = requests.get('https://api.example.com')
       response.raise_for_status()
   except requests.HTTPError as e:
       integration.alert_api_error(
           api_name="Example API",
           status_code=e.response.status_code,
           error_message=str(e)
       )
   ```

2. **Monitor logs**:
   ```bash
   # Terminal 1: Sofia API logs
   docker logs -f sofia-mastra-api

   # Terminal 2: WhatsApp logs
   docker logs -f sofia-wpp
   ```

3. **Set up automated monitoring**:
   - Add to collectors for error detection
   - Create cron jobs for health checks
   - Monitor for anomalies in data collection

---

**Document Version**: 1.0
**Last Updated**: 2025-11-22
**Status**: Ready for testing on actual server
