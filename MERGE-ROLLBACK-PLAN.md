# 🔄 Merge Rollback Plan

**Data do Merge**: 2025-12-03 14:46 UTC
**Branch Origem**: `claude/setup-auto-notifications-012c4Fo8viNHgba4oBwMpCjf`
**Branch Destino**: `claude/fix-deployment-script-errors-01DFTu3TQVACwYj4RZzJJNPH`
**Backup Branch**: `backup-prod-20251203-143634`

---

## ✅ O Que Foi Feito

### 1. Merge Executado
- **92 commits** merged
- **173 arquivos** novos/modificados
- **38,464 linhas** adicionadas
- **786 linhas** removidas

### 2. Principais Mudanças

#### Novos Collectors (26+)
- 🌍 **Dados Brasileiros**: IBGE, BACEN, IPEA, Ministérios, Segurança
- 🌎 **Internacional**: CEPAL, FAO, WTO, WHO, UNICEF, UN SDG
- 👩 **Gênero**: Mulheres (World Bank, FRED, ILO, Eurostat, Central Banks)
- ⚽ **Esportes**: Olimpíadas, Federações Regionais
- 🚨 **Segurança Global**: Criminalidade, drogas, religião
- 🌴 **Turismo**: World Tourism
- 🧠 **Intelligence**: Entity Resolution, Data Provenance

#### Novos Analytics (15+)
- Brazil Economy Intelligence
- Women Global Analysis
- Security Intelligence Report
- Tourism Intelligence
- Best Cities Tech Talent
- Dying Sectors Detector
- Remote Work Quality Index
- Cross-data Correlations

#### Infraestrutura
- ✅ WhatsApp Integration (Sofia)
- ✅ Rate Limiting (scripts/utils/rate-limiter.ts)
- ✅ Intelligent Scheduler
- ✅ Alert System (Email + WhatsApp)
- ✅ Database Inventory Scanner
- ✅ Reliability & Monitoring

#### Schemas SQL Novos
- `sql/01-canonical-entities.sql` - Entity Resolution
- `sql/02-changesets.sql` - Audit Trail
- `sql/03-data-provenance.sql` - Data Lineage

### 3. Dependências Instaladas
- ✅ **Node.js**: 70 packages (npm install) - OK
- ⚠️ **Python**: pip3 não disponível no WSL (instalar manualmente se necessário)

---

## 🚨 Rollback: Como Reverter Se Algo Der Errado

### Opção 1: Git Reset Hard (MAIS RÁPIDO)

```bash
# Voltar para o backup
git reset --hard backup-prod-20251203-143634

# Forçar push (CUIDADO: só faça se necessário!)
# git push origin claude/fix-deployment-script-errors-01DFTu3TQVACwYj4RZzJJNPH --force
```

**⚠️ ATENÇÃO**: Isso vai **PERDER TUDO** que foi mergeado! Use apenas se realmente precisar.

### Opção 2: Git Revert (MAIS SEGURO)

```bash
# Reverter o merge commit (mantém histórico)
git revert -m 1 HEAD

# Push normal
git push origin claude/fix-deployment-script-errors-01DFTu3TQVACwYj4RZzJJNPH
```

**Vantagem**: Mantém histórico completo, mais seguro para produção.

### Opção 3: Criar Nova Branch do Backup

```bash
# Criar nova branch clean do backup
git checkout -b fix-rollback-$(date +%Y%m%d) backup-prod-20251203-143634

# Push da nova branch
git push -u origin fix-rollback-$(date +%Y%m%d)
```

**Vantagem**: Não mexe na branch atual, permite comparação lado a lado.

---

## 🔍 Como Validar Se Está Tudo OK

### 1. Testar Collectors Críticos

```bash
# GitHub (collectors essenciais)
npm run collect:github-trending
npm run collect:github-niches

# APIs com rate limits
node scripts/collect-commodity-prices.js
node scripts/collect-energy-global.js

# Novos collectors brasileiros
python3 scripts/collect-ibge-api.py
python3 scripts/collect-bacen-sgs.py
```

### 2. Verificar Banco de Dados

```bash
# Conectar ao DB
psql -h localhost -U sofia -d sofia_db

# Verificar tabelas existentes
\dt sofia.*

# Verificar se novos schemas foram criados (se rodar migrações)
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'sofia'
ORDER BY table_name;
```

### 3. Verificar Analytics

```bash
# Rodar analytics existentes
cd analytics
python3 correlation-papers-funding.py
python3 tech-trend-score-simple.py

# Testar novos analytics
python3 brazil-economy-intelligence.py
python3 women-global-analysis.py
```

### 4. Verificar WhatsApp Integration

```bash
# Testar WhatsApp (se configurado)
python3 scripts/test-whatsapp-api.py
./test-sofia-whatsapp.sh
```

### 5. Verificar Logs

```bash
# Ver logs recentes
tail -100 logs/collectors.log
tail -100 logs/analytics.log

# Verificar erros
grep -i "error\|fail\|exception" logs/*.log | tail -50
```

---

## 📋 Checklist Pós-Merge

### Imediato (Primeiras 24h)
- [ ] Rodar collectors críticos manualmente (GitHub, commodities, energy)
- [ ] Verificar logs de erros
- [ ] Testar 2-3 analytics existentes
- [ ] Verificar se cron jobs rodam (se estiverem configurados)
- [ ] Monitorar uso de memória/CPU

### Curto Prazo (1 semana)
- [ ] Instalar pip3 e dependencies Python (`requirements-collectors.txt`)
- [ ] Rodar migrações SQL se necessário (`sql/01-*.sql`, `02-*.sql`, `03-*.sql`)
- [ ] Testar novos collectors brasileiros (IBGE, BACEN)
- [ ] Configurar WhatsApp integration (se desejado)
- [ ] Configurar alertas (email/WhatsApp)

### Médio Prazo (1 mês)
- [ ] Validar novos analytics (women, security, tourism, sports)
- [ ] Configurar intelligent scheduler
- [ ] Implementar entity resolution (canonical entities)
- [ ] Configurar data provenance tracking

---

## 🐛 Problemas Conhecidos & Soluções

### 1. Pip3 Não Encontrado
```bash
# Instalar pip no WSL
sudo apt update
sudo apt install python3-pip -y
```

### 2. PostgreSQL Client Não Disponível
```bash
# Instalar psql no WSL
sudo apt install postgresql-client -y
```

### 3. Dependências Python Faltando
```bash
# Instalar depois de ter pip3
pip3 install -r requirements-collectors.txt
```

### 4. Conflitos de Merge (Futuros)
Se houver conflitos no CLAUDE.md:
```bash
# Aceitar versão local
git checkout --ours CLAUDE.md
git add CLAUDE.md

# OU aceitar versão remota
git checkout --theirs CLAUDE.md
git add CLAUDE.md
```

### 5. Rate Limits de APIs
Novos collectors respeitam rate limits:
- `scripts/utils/rate-limiter.ts`
- `scripts/utils/retry.py`

Se der erro 429 (Too Many Requests), aguardar 1-5 minutos.

---

## 📞 Contato de Emergência

**Se algo der MUITO errado**:
1. **NÃO ENTRE EM PÂNICO** 🙂
2. Rode: `git status` e `git log --oneline -10`
3. Capture logs: `tail -200 logs/*.log > emergency-logs.txt`
4. Use Opção 1 de Rollback (reset hard) para voltar ao estado anterior
5. Investigue depois com calma

---

## ✅ Conclusão

**Backup criado com sucesso**: `backup-prod-20251203-143634`

**Merge Status**: ✅ Completado sem conflitos

**Next Steps**:
1. Validar collectors críticos (próximas 24h)
2. Instalar dependências Python quando possível
3. Testar novos recursos gradualmente
4. Monitorar logs

**Se precisar reverter**: Use uma das 3 opções acima dependendo da urgência.

---

**Última Atualização**: 2025-12-03 14:46 UTC
**Autor**: Claude Code
