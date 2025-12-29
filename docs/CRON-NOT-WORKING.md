# ⚠️ Por Que o Cron Não Está Rodando?

## 🔍 Problema Identificado

Você está tentando rodar o cron no **Windows/WSL**, mas o cron precisa rodar no **servidor Ubuntu** onde o Sofia Pulse está instalado.

**Situação Atual**:
```bash
$ crontab -l
no crontab for augusto  # ❌ Crontab NUNCA foi instalado
```

**Onde você está agora**:
```
/mnt/c/Users/augusto.moreira/Documents/sofia-pulse
```
↑ Isso é o **Windows WSL**, não o servidor!

---

## ✅ Solução: Instalar Crontab no Servidor

### Passo 1: SSH no Servidor Ubuntu

```bash
ssh ubuntu@YOUR_SERVER_IP
# ou
ssh ubuntu@sofia-pulse.example.com
```

### Passo 2: Ir para o Diretório Sofia Pulse

```bash
cd /home/ubuntu/sofia-pulse
```

### Passo 3: Pull das Mudanças Recentes

```bash
git pull origin claude/fix-deployment-script-errors-01DFTu3TQVACwYj4RZzJJNPH
```

### Passo 4: Instalar Crontab

```bash
bash install-crontab-now.sh
```

**Esse script vai**:
- ✅ Criar backup do crontab existente (se houver)
- ✅ Instalar o crontab com 3 schedules (10:00, 16:00, 22:00 UTC)
- ✅ Configurar WhatsApp alerts
- ✅ Não pedir confirmação (aplica automaticamente)

### Passo 5: Verificar que Foi Instalado

```bash
crontab -l
```

Você deve ver:
```cron
# SOFIA PULSE - Distributed Schedule WITH WHATSAPP ALERTS
0 10 * * 1-5 cd /home/ubuntu/sofia-pulse && bash collect-fast-apis.sh ...
0 16 * * 1-5 cd /home/ubuntu/sofia-pulse && bash collect-limited-apis-with-alerts.sh ...
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-mega-analytics-with-alerts.sh ...
```

---

## 🧪 Testar Manualmente (Antes do Cron Rodar)

Ainda no servidor, você pode testar manualmente:

```bash
# Test collectors
bash collect-fast-apis.sh

# Test analytics
bash run-mega-analytics-with-alerts.sh

# Test email
bash send-email-mega.sh
```

---

## 📅 Schedule Completo

Depois de instalar, o cron vai rodar automaticamente:

| Horário UTC | Horário BRT | O Que Roda | Notificação WhatsApp |
|-------------|-------------|------------|---------------------|
| 10:00 | 07:00 | Fast APIs | ❌ Não (muito cedo) |
| 16:00 | 13:00 | Limited APIs | ✅ Sim (summary) |
| 22:00 | 19:00 | Analytics + Email | ✅ Sim (3 mensagens) |

**WhatsApp Notifications**:
1. 16:00 UTC - Após coleta (quantos collectors falharam/sucederam)
2. 22:00 UTC - Após analytics (quais reports foram gerados)
3. 22:05 UTC - Após email (confirmação com count de reports)

---

## 📝 Monitorar Logs

Depois que o cron começar a rodar, você pode ver os logs:

```bash
# Ver logs em tempo real
tail -f /var/log/sofia-limited-apis.log
tail -f /var/log/sofia-analytics.log

# Ver últimas linhas
tail -50 /var/log/sofia-limited-apis.log
tail -50 /var/log/sofia-analytics.log
```

---

## ❓ FAQ

### Por que não funciona no WSL?

O WSL (Windows Subsystem for Linux) é uma emulação do Linux no Windows. O cron do WSL não é confiável e pode não executar tarefas quando o Windows está em suspend/hibernation.

O Sofia Pulse precisa rodar em um **servidor Linux real** (Ubuntu, Debian, etc.) que fique ligado 24/7.

### Como sei se o cron está rodando?

No servidor Ubuntu:
```bash
systemctl status cron
# Deve mostrar: Active: active (running)
```

### Quando será a próxima execução?

Próximos horários (segunda-sexta):
- **16:00 UTC (13:00 BRT)** - Limited APIs
- **22:00 UTC (19:00 BRT)** - Analytics + Email

O cron NÃO roda nos fins de semana (sábado/domingo).

### E se eu quiser rodar agora?

Execute manualmente no servidor:
```bash
bash collect-fast-apis.sh && \
bash collect-limited-apis-with-alerts.sh && \
bash run-mega-analytics-with-alerts.sh && \
bash send-email-mega.sh
```

---

## 🚨 Importante

**NÃO tente configurar o cron no Windows/WSL!**

O cron DEVE ser configurado no servidor Ubuntu onde o Sofia Pulse vai rodar 24/7.

Se você não tem um servidor Ubuntu, considere:
1. **AWS EC2** - t2.micro (grátis por 1 ano)
2. **Google Cloud** - Compute Engine (grátis por 90 dias)
3. **DigitalOcean** - Droplet básico ($6/mês)
4. **Oracle Cloud** - Always Free tier (2 VMs grátis)

---

## ✅ Checklist Final

Após instalar no servidor:

- [ ] SSH no servidor Ubuntu
- [ ] `cd /home/ubuntu/sofia-pulse`
- [ ] `git pull` (pegar últimas mudanças)
- [ ] `bash install-crontab-now.sh`
- [ ] `crontab -l` (verificar instalado)
- [ ] Aguardar próximo horário (16:00 ou 22:00 UTC)
- [ ] Receber WhatsApp notification! 📱

---

**Criado**: 03 Dec 2025
**Autor**: Claude Code
**Branch**: claude/fix-deployment-script-errors-01DFTu3TQVACwYj4RZzJJNPH
