# 📅 Adicionar Finance Collectors ao Crontab

**Status Atual**: Finance collectors (B3, NASDAQ, Funding) NÃO estão no cron!

**Descoberta**: Crontab tem outros collectors finance (YC, SEC, HackerNews) mas NÃO tem os 3 principais que acabamos de corrigir.

---

## 📋 O Que Está no Cron Atualmente

### Sofia Pulse Principal:
```bash
0 */6 * * * /home/ubuntu/sofia-pulse/collect-cron.sh          # A cada 6h
0 6 * * *   /home/ubuntu/sofia-pulse/cron-daily.sh           # 06:00 diário
0 7 * * 1   /home/ubuntu/sofia-pulse/cron-weekly.sh          # 07:00 segundas
0 8 1 * *   /home/ubuntu/sofia-pulse/cron-monthly.sh         # 08:00 dia 1
```

### Finance (Parcial):
```bash
0 2 * * * cd /home/ubuntu/sofia-pulse/finance && DB_HOST=localhost npm run collect:yc
0 3 * * * cd /home/ubuntu/sofia-pulse/finance && DB_HOST=localhost npm run collect:sec
0 4 * * * cd /home/ubuntu/sofia-pulse/finance && DB_HOST=localhost npm run collect:hackernews
```

### ❌ FALTANDO (acabamos de corrigir!):
- `collect:brazil` (B3 stocks) - 56 registros hoje
- `collect:nasdaq` (NASDAQ momentum) - 19 registros hoje
- `collect:funding` (Funding rounds) - 6 registros hoje

---

## ✅ OPÇÃO 1: Adicionar Finance ao Crontab (Recomendado)

### Adicionar ao Crontab do Usuário:

```bash
# No servidor, editar crontab:
crontab -e

# Adicionar estas linhas no final:

# Sofia Pulse - Finance Collectors (B3, NASDAQ, Funding)
# B3: Roda 2x por dia (abertura e fechamento mercado brasileiro)
0 12 * * 1-5 cd /home/ubuntu/sofia-pulse && npm run collect:brazil >> /var/log/sofia-finance-b3.log 2>&1
0 21 * * 1-5 cd /home/ubuntu/sofia-pulse && npm run collect:brazil >> /var/log/sofia-finance-b3.log 2>&1

# NASDAQ: Roda 1x por dia após fechamento mercado US (21:00 UTC = 16:00 ET)
5 21 * * 1-5 cd /home/ubuntu/sofia-pulse && npm run collect:nasdaq >> /var/log/sofia-finance-nasdaq.log 2>&1

# Funding Rounds: Roda 1x por dia (dados menos voláteis)
10 21 * * * cd /home/ubuntu/sofia-pulse && npm run collect:funding >> /var/log/sofia-finance-funding.log 2>&1

# Salvar e sair (Ctrl+X, Y, Enter no nano)
```

### Horários Escolhidos (UTC):

| Collector | Horário UTC | Horário BRT | Frequência | Motivo |
|-----------|-------------|-------------|------------|--------|
| **B3** | 12:00 | 09:00 | 2x/dia seg-sex | Abertura B3 |
| **B3** | 21:00 | 18:00 | 2x/dia seg-sex | Fechamento B3 |
| **NASDAQ** | 21:05 | 18:05 | 1x/dia seg-sex | Após fechamento US |
| **Funding** | 21:10 | 18:10 | 1x/dia todos | Dados estáticos |

**Por que 21:00 UTC?**
- 21:00 UTC = 18:00 BRT = 16:00 ET (fechamento mercados)
- Garante dados do dia completo
- Evita rate limits (espaçamento de 5min entre cada)

---

## ✅ OPÇÃO 2: Adicionar ao Script Existente

Se `collect-cron.sh` ou `cron-daily.sh` já existem, adicione lá:

### Verificar conteúdo do script:
```bash
cat /home/ubuntu/sofia-pulse/cron-daily.sh
```

### Se quiser adicionar ao cron-daily.sh:
```bash
# Editar o script:
nano /home/ubuntu/sofia-pulse/cron-daily.sh

# Adicionar no final:
echo "🔹 Coletando Finance..."
cd /home/ubuntu/sofia-pulse

# B3
echo "  📊 B3 Stocks..."
npm run collect:brazil >> /var/log/sofia-finance-b3.log 2>&1

# NASDAQ (com delay para rate limit)
echo "  📊 NASDAQ..."
sleep 60
npm run collect:nasdaq >> /var/log/sofia-finance-nasdaq.log 2>&1

# Funding Rounds
echo "  💰 Funding Rounds..."
npm run collect:funding >> /var/log/sofia-finance-funding.log 2>&1

echo "✅ Finance coletado!"
```

---

## ✅ OPÇÃO 3: Criar Script Finance Dedicado

### Criar novo script:

```bash
# No servidor:
nano /home/ubuntu/sofia-pulse/collect-finance.sh

# Conteúdo:
#!/bin/bash

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔹 Sofia Pulse - Finance Collectors"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd /home/ubuntu/sofia-pulse

# B3 Stocks
echo "📊 [1/3] Coletando B3 (Brasil)..."
npm run collect:brazil >> /var/log/sofia-finance-b3.log 2>&1
if [ $? -eq 0 ]; then
  echo "   ✅ B3: Sucesso"
else
  echo "   ❌ B3: Falhou"
fi

# NASDAQ (com delay para rate limit)
echo ""
echo "📊 [2/3] Coletando NASDAQ (aguardando rate limit 60s)..."
sleep 60
npm run collect:nasdaq >> /var/log/sofia-finance-nasdaq.log 2>&1
if [ $? -eq 0 ]; then
  echo "   ✅ NASDAQ: Sucesso"
else
  echo "   ❌ NASDAQ: Falhou"
fi

# Funding Rounds
echo ""
echo "💰 [3/3] Coletando Funding Rounds..."
npm run collect:funding >> /var/log/sofia-finance-funding.log 2>&1
if [ $? -eq 0 ]; then
  echo "   ✅ Funding: Sucesso"
else
  echo "   ❌ Funding: Falhou"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Finance Collectors - Concluído!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

### Dar permissão de execução:
```bash
chmod +x /home/ubuntu/sofia-pulse/collect-finance.sh
```

### Adicionar ao crontab:
```bash
crontab -e

# Adicionar:
# Sofia Pulse - Finance Collectors (Completo)
0 21 * * 1-5 /home/ubuntu/sofia-pulse/collect-finance.sh >> /var/log/sofia-finance-complete.log 2>&1
```

---

## 📊 Resultado Esperado Após Adicionar

### Logs Diários:

```bash
# Ver logs finance:
tail -f /var/log/sofia-finance-b3.log
tail -f /var/log/sofia-finance-nasdaq.log
tail -f /var/log/sofia-finance-funding.log

# Ou log completo:
tail -f /var/log/sofia-finance-complete.log
```

### Banco de Dados:

Após 1 semana no cron:
```
market_data_brazil:  ~200-300 registros (2x/dia * 5 dias)
market_data_nasdaq:  ~100-150 registros (1x/dia * 7 dias)
funding_rounds:      ~50-60 registros (1x/dia * 7 dias)
```

---

## ⚠️ IMPORTANTE: Rate Limits

### Alpha Vantage (NASDAQ):
- **Limite**: 25 requests/dia (free tier)
- **Nosso uso**: ~5-10 requests/coleta
- **Solução**: Rodar apenas 1x por dia (21:05 UTC)

### B3 (Scraping):
- **Limite**: Nenhum oficial, mas seja educado
- **Solução**: Max 2x por dia, só dias úteis

### Funding (Mock Data):
- **Limite**: Nenhum (dados mock locais)
- **Solução**: 1x por dia é suficiente

---

## 🧪 Testar Antes de Adicionar ao Cron

```bash
# No servidor:
cd /home/ubuntu/sofia-pulse

# Testar manualmente:
npm run collect:brazil
sleep 60
npm run collect:nasdaq
npm run collect:funding

# Verificar resultado:
npm run audit | grep -E "market_data|funding_rounds"
```

**Output esperado**:
```
✅ market_data_brazil: XX registros (HOJE!)
✅ market_data_nasdaq: XX registros (HOJE!)
✅ funding_rounds: XX registros (HOJE!)
```

---

## 📅 Crontab Final Recomendado

```bash
# INFRAESTRUTURA (já existente)
*/1 * * * * /home/ubuntu/infraestrutura/scripts/auto-recovery.sh
0 3 * * * /home/ubuntu/infraestrutura/scripts/comprehensive-backup.sh >> /var/log/backup.log 2>&1
0 2 * * * /home/ubuntu/infraestrutura/scripts/backup-dashboards.sh
0 2 * * 3 /home/ubuntu/infraestrutura/scripts/full-backup.sh >> /home/ubuntu/backups/full-backup.log 2>&1

# SOFIA PULSE PRINCIPAL (já existente)
0 */6 * * * /home/ubuntu/sofia-pulse/collect-cron.sh >> /home/ubuntu/sofia-pulse/logs/cron.log 2>&1
0 6 * * * /home/ubuntu/sofia-pulse/cron-daily.sh
0 7 * * 1 /home/ubuntu/sofia-pulse/cron-weekly.sh
0 8 1 * * /home/ubuntu/sofia-pulse/cron-monthly.sh

# FINANCE - OUTROS (já existente)
0 2 * * * cd /home/ubuntu/sofia-pulse/finance && DB_HOST=localhost npm run collect:yc >> /var/log/sofia-finance-yc.log 2>&1
0 3 * * * cd /home/ubuntu/sofia-pulse/finance && DB_HOST=localhost npm run collect:sec >> /var/log/sofia-finance-sec.log 2>&1
0 4 * * * cd /home/ubuntu/sofia-pulse/finance && DB_HOST=localhost npm run collect:hackernews >> /var/log/sofia-finance-hn.log 2>&1

# FINANCE - PRINCIPAIS (ADICIONAR!) ← NOVO!
0 21 * * 1-5 /home/ubuntu/sofia-pulse/collect-finance.sh >> /var/log/sofia-finance-complete.log 2>&1
```

---

## 💡 Alternativa: Tudo em Um Comando

Se preferir simplicidade, adicione apenas:

```bash
# Finance completo (1x por dia, 21:00 UTC)
0 21 * * * cd /home/ubuntu/sofia-pulse && npm run collect:finance-all >> /var/log/sofia-finance-all.log 2>&1
```

**Prós**:
- ✅ Simples (1 linha)
- ✅ Usa o script npm existente

**Contras**:
- ❌ Não tem delay entre collectors (pode bater rate limit)
- ❌ Se um falhar, os outros continuam (mas sem log detalhado)

---

## ✅ Recomendação Final

**Opção 3** (Script dedicado) é a melhor:
1. Criar `/home/ubuntu/sofia-pulse/collect-finance.sh`
2. Adicionar ao cron: `0 21 * * 1-5 /home/ubuntu/sofia-pulse/collect-finance.sh`
3. Monitorar logs: `tail -f /var/log/sofia-finance-complete.log`

**Motivos**:
- ✅ Delay entre collectors (evita rate limit)
- ✅ Logs detalhados por collector
- ✅ Fácil de debugar
- ✅ Fácil de rodar manualmente para testar

---

**Execute no servidor**:
```bash
# 1. Criar script:
nano /home/ubuntu/sofia-pulse/collect-finance.sh
# (copiar conteúdo da Opção 3)

# 2. Dar permissão:
chmod +x /home/ubuntu/sofia-pulse/collect-finance.sh

# 3. Testar:
/home/ubuntu/sofia-pulse/collect-finance.sh

# 4. Adicionar ao cron:
crontab -e
# (adicionar linha: 0 21 * * 1-5 /home/ubuntu/sofia-pulse/collect-finance.sh >> /var/log/sofia-finance-complete.log 2>&1)
```

🚀 **Pronto! Finance collectors no cron automatizado!**
