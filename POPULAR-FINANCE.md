# 🚀 Popular Finance com Dados REAIS

**Execute NO SERVIDOR** (onde PostgreSQL está rodando)

---

## ⚡ Quick Start (4 comandos)

```bash
cd ~/sofia-pulse

# 1. Puxar últimas atualizações:
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE

# 2. IMPORTANTE - Copiar .env para finance/:
cp .env finance/.env

# 3. Popular finance com dados REAIS:
npm run collect:finance-all

# 4. Verificar resultado:
npm run audit | grep -E "market_data|funding_rounds"
```

**⚠️ IMPORTANTE**: O passo 2 é NECESSÁRIO! Scripts finance precisam do `.env` no diretório `finance/`.

Se você esquecer, verá erro: `password authentication failed for user "postgres"`
→ **Solução**: Ver `FIX-FINANCE-ENV.md`

---

## 📊 Rodar Finance COMPLETO

### Opção 1: Popular TUDO (Recomendado)

```bash
cd ~/sofia-pulse

# Rodar todos os 3 collectors finance:
npm run collect:finance-all

# Tempo estimado:
# - Brazil (B3): ~30s
# - NASDAQ: ~30s
# - Funding: ~45s
# Total: ~2 minutos

# Depois verificar:
npm run audit
```

**O que vai acontecer**:
- ✅ market_data_brazil: Vai ATUALIZAR (já tem 32, vai adicionar mais)
- ✅ market_data_nasdaq: Vai ATUALIZAR (já tem 14, vai adicionar mais)
- ✅ funding_rounds: Vai POPULAR pela primeira vez! (0 → ~10-20 registros)

---

### Opção 2: Só Popular Funding Rounds (tabela vazia)

```bash
cd ~/sofia-pulse

# Só o que está vazio:
npm run collect:funding

# Verificar:
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "
SELECT COUNT(*) as total FROM sofia.funding_rounds;
"
```

---

### Opção 3: Finance Full Investment Mode

```bash
cd ~/sofia-pulse/finance

# Coleta tudo + gera sinais de investimento:
npm run invest:full

# Vai fazer:
# 1. Coletar B3, NASDAQ, Funding
# 2. Gerar sinais de investimento (score 0-100)
# 3. Salvar em output/sofia-signals-*.json

# Ver sinais gerados:
cat output/sofia-signals-*.json | jq '.signals | length'
cat output/sofia-signals-*.json | jq '.signals[] | select(.score > 85)'
```

---

## 🔍 Verificar Depois da Coleta

### Ver todas as tabelas finance:

```bash
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "
SELECT
  'market_data_brazil' as tabela,
  COUNT(*) as registros,
  MAX(collected_at) as ultima_coleta
FROM sofia.market_data_brazil
UNION ALL
SELECT
  'market_data_nasdaq',
  COUNT(*),
  MAX(collected_at)
FROM sofia.market_data_nasdaq
UNION ALL
SELECT
  'funding_rounds',
  COUNT(*),
  MAX(collected_at)
FROM sofia.funding_rounds;
"
```

**Output esperado**:
```
tabela               | registros | ultima_coleta
---------------------|-----------|----------------------------
market_data_brazil   | 60-80     | 2025-11-17 22:XX:XX (HOJE!)
market_data_nasdaq   | 25-35     | 2025-11-17 22:XX:XX (HOJE!)
funding_rounds       | 10-20     | 2025-11-17 22:XX:XX (HOJE!)
```

---

### Audit completo:

```bash
npm run audit | grep -E "market_data|funding_rounds"
```

**Output esperado**:
```
📋 Analisando: sofia.market_data_brazil
   Registros: 64
   ✅ HOJE - Dados coletados hoje!

📋 Analisando: sofia.market_data_nasdaq
   Registros: 28
   ✅ HOJE - Dados coletados hoje!

📋 Analisando: sofia.funding_rounds
   Registros: 15
   ✅ HOJE - Dados coletados hoje!
```

---

## 📈 Ver Dados Coletados

### B3 (Brasil):

```bash
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "
SELECT
  ticker,
  company,
  sector,
  price,
  collected_at
FROM sofia.market_data_brazil
ORDER BY collected_at DESC
LIMIT 10;
"
```

---

### NASDAQ:

```bash
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "
SELECT
  ticker,
  company,
  sector,
  price,
  momentum,
  collected_at
FROM sofia.market_data_nasdaq
ORDER BY momentum DESC
LIMIT 10;
"
```

---

### Funding Rounds (novo!):

```bash
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "
SELECT
  company_name,
  round_type,
  amount_usd,
  investors,
  collected_at
FROM sofia.funding_rounds
ORDER BY amount_usd DESC
LIMIT 10;
"
```

---

## 🎯 Exemplo de Dados Esperados

### Funding Rounds:

```
company_name    | round_type | amount_usd  | investors
----------------|------------|-------------|------------------
Anduril         | Series E   | 1500000000  | Founders Fund, a16z
Nubank          | Series G   | 750000000   | Sequoia, Tiger Global
Shield AI       | Series D   | 500000000   | Fidelity, T. Rowe Price
OpenAI          | Series C   | 300000000   | Microsoft, Khosla
Anthropic       | Series B   | 450000000   | Google, Spark Capital
```

---

## 💡 Troubleshooting

### "Error: connect ECONNREFUSED"

**Problema**: PostgreSQL não está acessível

```bash
# Verificar se está rodando:
docker ps | grep sofia-postgres

# Se não estiver:
docker start sofia-postgres

# Testar conexão:
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "SELECT 1;"
```

---

### "API key missing"

**Problema**: NASDAQ collector precisa de API key

**Solução 1 - Usar chave existente**:
```bash
# Verificar .env:
cat ~/sofia-pulse/.env | grep ALPHA_VANTAGE

# Deveria ter:
# ALPHA_VANTAGE_API_KEY=TM3DVH1A35DUPPZ9
```

**Solução 2 - Pular NASDAQ, só B3 + Funding**:
```bash
npm run collect:brazil
npm run collect:funding
```

---

### "Timeout" ou "Network error"

**Problema**: Sites podem estar lentos

```bash
# Tentar novamente:
npm run collect:funding

# Ou aumentar timeout (editar script)
```

---

## 📋 Comandos Úteis

### Ver logs em tempo real:

```bash
# Brazil:
npm run collect:brazil 2>&1 | tee collect-brazil.log

# NASDAQ:
npm run collect:nasdaq 2>&1 | tee collect-nasdaq.log

# Funding:
npm run collect:funding 2>&1 | tee collect-funding.log
```

---

### Limpar dados antigos (se quiser recomeçar):

```bash
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "
TRUNCATE TABLE sofia.market_data_brazil;
TRUNCATE TABLE sofia.market_data_nasdaq;
TRUNCATE TABLE sofia.funding_rounds;
"

# Depois popular novamente:
npm run collect:finance-all
```

---

### Backup antes de popular:

```bash
# Backup das tabelas finance:
docker exec sofia-postgres pg_dump -U sofia -d sofia_db \
  -t sofia.market_data_brazil \
  -t sofia.market_data_nasdaq \
  -t sofia.funding_rounds \
  > backup-finance-$(date +%Y%m%d).sql
```

---

## 🎉 Resultado Final Esperado

Depois de rodar `npm run collect:finance-all`:

```
✅ market_data_brazil: 60-80 registros (atualizado hoje)
✅ market_data_nasdaq: 25-35 registros (atualizado hoje)
✅ funding_rounds: 10-20 registros (populado hoje!)

Total Finance: ~100-135 registros
Percentual do banco total: ~10-12%
```

---

## 🚀 Próximo Passo

Depois de popular:

1. **Gerar sinais de investimento**:
   ```bash
   cd finance
   npm run signals
   cat output/sofia-signals-*.json | jq
   ```

2. **Auditar banco completo**:
   ```bash
   npm run audit
   ```

3. **Ver métricas atualizadas**:
   ```bash
   docker exec -i sofia-postgres psql -U sofia -d sofia_db < scripts/count-all-data.sql
   ```

---

**Execute NO SERVIDOR**: `npm run collect:finance-all`
**Tempo estimado**: 2-3 minutos
**Resultado**: 3 tabelas finance populadas com dados reais! 🚀
