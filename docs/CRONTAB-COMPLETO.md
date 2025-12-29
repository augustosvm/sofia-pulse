# 📅 Sofia Pulse - Crontab Completo

**Status Atual**: ❌ Crontab VAZIO (verificado em 2025-11-18)

**Este arquivo contém o crontab completo recomendado para Sofia Pulse**

---

## 📋 Crontab Completo Recomendado

```bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Sofia Pulse - Automações Completas
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# VARIÁVEIS DE AMBIENTE
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAILTO=""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. FINANCE COLLECTORS (Segunda a Sexta)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# B3 (Brasil) - 21:00 UTC (18:00 BRT = Após fechamento mercado)
0 21 * * 1-5 cd /home/ubuntu/sofia-pulse && npm run collect:brazil >> /var/log/sofia-finance-b3.log 2>&1

# NASDAQ (USA) - 21:05 UTC (Após fechamento US 16:00 ET)
5 21 * * 1-5 cd /home/ubuntu/sofia-pulse && npm run collect:nasdaq >> /var/log/sofia-finance-nasdaq.log 2>&1

# Funding Rounds - 21:10 UTC (Todos os dias)
10 21 * * * cd /home/ubuntu/sofia-pulse && npm run collect:funding >> /var/log/sofia-finance-funding.log 2>&1

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. PREMIUM INSIGHTS (Segunda a Sexta, após Finance)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Gerar insights premium - 22:00 UTC (após todos os collectors)
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && ./generate-premium-insights.sh >> /var/log/sofia-insights.log 2>&1

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. BACKUP COMPLETO (Diário)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Backup completo - 04:00 UTC (01:00 BRT)
0 4 * * * /home/ubuntu/sofia-pulse/scripts/backup-complete.sh >> /var/log/sofia-backup.log 2>&1

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. LIMPEZA DE LOGS (Semanal)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Limpar logs antigos - Domingo 05:00 UTC
0 5 * * 0 find /var/log/sofia-*.log -mtime +30 -delete

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 📊 Cronograma Visual

| Horário UTC | Horário BRT | Tarefa | Frequência |
|-------------|-------------|--------|------------|
| **04:00** | 01:00 | 🔄 Backup Completo | Diário |
| **05:00** | 02:00 | 🗑️ Limpeza Logs | Domingo |
| **21:00** | 18:00 | 📊 Finance B3 | Seg-Sex |
| **21:05** | 18:05 | 📊 Finance NASDAQ | Seg-Sex |
| **21:10** | 18:10 | 💰 Finance Funding | Diário |
| **22:00** | 19:00 | 💎 Premium Insights | Seg-Sex |

---

## 🚀 Como Instalar

### Método 1: Copiar/Colar (Recomendado)

```bash
# No servidor (91.98.158.19):

# 1. Editar crontab
crontab -e

# 2. Copiar TODO o conteúdo entre as linhas ━━━━ acima

# 3. Colar no editor

# 4. Salvar e sair (Ctrl+X, Y, Enter no nano)
```

### Método 2: Instalar via Arquivo

```bash
# No servidor:

# 1. Criar arquivo temporário
cat > /tmp/sofia-crontab << 'EOF'
# [copiar conteúdo do crontab acima]
EOF

# 2. Instalar
crontab /tmp/sofia-crontab

# 3. Verificar
crontab -l
```

---

## ✅ Verificar Instalação

```bash
# Ver crontab instalado
crontab -l

# Verificar com script
bash /home/ubuntu/sofia-pulse/check-crontab.sh

# Ver logs em tempo real
tail -f /var/log/sofia-finance-b3.log
tail -f /var/log/sofia-insights.log
tail -f /var/log/sofia-backup.log
```

---

## 📝 Logs Esperados

### Localização:
```
/var/log/sofia-finance-b3.log       # B3 collector
/var/log/sofia-finance-nasdaq.log   # NASDAQ collector
/var/log/sofia-finance-funding.log  # Funding collector
/var/log/sofia-insights.log         # Premium insights
/var/log/sofia-backup.log           # Backup completo
```

### Ver todos os logs:
```bash
ls -lh /var/log/sofia-*.log
```

---

## 🔧 Ajustes Opcionais

### Mudar Horários:

Se quiser rodar em horários diferentes, edite os números:

```bash
# Formato: MIN HORA DIA MÊS DIASEMANA
#          0   21   *   *   1-5

# Exemplos:
0 21 * * 1-5    # 21:00 UTC, Seg-Sex
30 14 * * *     # 14:30 UTC, Todos os dias
0 */6 * * *     # A cada 6 horas
```

### Adicionar Email de Notificação:

```bash
# No topo do crontab, adicionar:
MAILTO="seu-email@example.com"
```

---

## ⚠️ IMPORTANTE

### Antes de Instalar:

1. ✅ Verificar se scripts existem:
   ```bash
   ls -la /home/ubuntu/sofia-pulse/generate-premium-insights.sh
   ls -la /home/ubuntu/sofia-pulse/scripts/backup-complete.sh
   ```

2. ✅ Testar scripts manualmente:
   ```bash
   cd /home/ubuntu/sofia-pulse
   ./generate-premium-insights.sh
   npm run collect:brazil
   ```

3. ✅ Configurar GEMINI_API_KEY:
   ```bash
   echo 'GEMINI_API_KEY=your-key' >> /home/ubuntu/sofia-pulse/.env
   ```

---

## 🎯 Resultado Esperado

Após 1 semana rodando:

### Banco de Dados:
```
market_data_brazil:  ~200-300 registros (5 dias * 1x/dia)
market_data_nasdaq:  ~100-150 registros (5 dias * 1x/dia)
funding_rounds:      ~50-60 registros (7 dias * 1x/dia)
```

### Insights:
```
analytics/premium-insights/
├── latest.md          (atualizado diariamente)
├── latest.txt         (atualizado diariamente)
└── data-summary.csv   (atualizado diariamente)
```

### Backups:
```
/home/ubuntu/backups/
├── sofia-pulse-YYYY-MM-DD.tar.gz
├── postgres-YYYY-MM-DD.sql.gz
└── mastra-rag-YYYY-MM-DD.tar.gz
```

---

## 🆘 Troubleshooting

### Cron não roda:

```bash
# Verificar se cron está ativo
systemctl status cron

# Ver logs do cron
grep CRON /var/log/syslog | tail -20

# Testar manualmente
cd /home/ubuntu/sofia-pulse && npm run collect:brazil
```

### Logs vazios:

```bash
# Verificar permissões
ls -la /var/log/sofia-*.log

# Criar logs manualmente se necessário
touch /var/log/sofia-finance-b3.log
chmod 666 /var/log/sofia-finance-b3.log
```

---

**Criado**: 2025-11-18
**Última Atualização**: 2025-11-18
**Versão**: 1.0
