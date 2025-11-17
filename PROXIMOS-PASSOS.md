# 🚀 Próximos Passos - Resolver Discrepância do Banco

**Situação**: Scripts TypeScript encontram 29 tabelas, mas `psql \dn` mostra 0 schemas.

---

## 1️⃣ No Servidor (onde Docker está rodando)

### Passo 1: Puxar novos scripts
```bash
cd ~/sofia-pulse
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE
```

### Passo 2: Executar verificação rápida
```bash
bash scripts/quick-db-check.sh
```

**O que vai mostrar**:
- ✅ Se mostra tabelas: Descobriremos em qual schema elas estão
- ❌ Se mostra 0 tabelas: Há problema mais profundo

---

### Passo 3A: Se quick-check mostrar tabelas

Ótimo! Significa que os dados existem, só precisamos saber onde.

```bash
# Execute a investigação completa:
docker exec -i sofia-postgres psql -U sofia -d sofia_db < scripts/investigate.sql

# Vai gerar output completo mostrando:
# - Em qual schema as 29 tabelas estão
# - Quantos registros cada uma tem
# - Se tem dados de sábado até hoje
```

**Depois cole o output completo para eu analisar.**

---

### Passo 3B: Se quick-check mostrar 0 tabelas

Então o problema é que TypeScript e psql estão vendo bancos diferentes.

```bash
# 1. Liste TODAS as databases:
docker exec -it sofia-postgres psql -U postgres -c "\l"

# 2. Veja se existe database sofia_db:
docker exec -it sofia-postgres psql -U postgres -c "SELECT datname FROM pg_database WHERE datname = 'sofia_db';"

# 3. Se não existir, crie:
docker exec -it sofia-postgres psql -U postgres -c "CREATE DATABASE sofia_db OWNER sofia;"

# 4. Rode collectors para popular:
npm run collect:cardboard
npm run collect:arxiv-ai
npm run collect:ai-companies
```

---

## 2️⃣ Investigando Dados de Sábado

Depois de descobrir onde as tabelas estão, precisamos verificar:

```bash
# Execute no psql:
docker exec -it sofia-postgres psql -U sofia -d sofia_db

# Dentro do psql, rode:
SELECT
  'cardboard_production' as tabela,
  MIN(collected_at) as primeira_coleta,
  MAX(collected_at) as ultima_coleta,
  COUNT(*) as total_registros
FROM cardboard_production;

-- Repita para outras tabelas:
-- arxiv_ai_papers, ai_companies, wipo_china_patents, etc.
```

**O que procurar**:
- `primeira_coleta`: Deve ser sábado (2025-11-15) ou antes
- `ultima_coleta`: Deve ser hoje (2025-11-17)
- `total_registros`: Deve ser > 0

---

## 3️⃣ Verificando Cron Jobs

Se dados existem mas não estão atualizados:

```bash
# Ver se cron jobs rodaram:
sudo tail -100 /var/log/sofia-daily.log
sudo tail -100 /var/log/sofia-weekly.log

# Ver próxima execução:
crontab -l

# Testar manualmente:
npm run collect:cardboard
# Deveria atualizar com dados de HOJE
```

---

## 4️⃣ Cenários Possíveis

### ✅ Cenário 1: Tabelas em schema diferente (MELHOR CASO)
**Sintoma**: quick-check mostra tabelas em `schema_name.tabela`
**Solução**: Atualizar audit script para usar schema correto
**Tempo**: 5 minutos

### 🟡 Cenário 2: Database diferente
**Sintoma**: sofia_db não existe ou está vazio
**Solução**: Criar database e rodar collectors
**Tempo**: 20 minutos

### 🟠 Cenário 3: Dados foram coletados mas sumidos
**Sintoma**: Tabelas existem mas vazias
**Causa**: Erro nos collectors ou banco foi resetado
**Solução**: Rodar collectors novamente
**Tempo**: 30 minutos

### 🔴 Cenário 4: PostgreSQL corrompido
**Sintoma**: Erros ao conectar ou queries falhando
**Solução**: Restart do container ou restore de backup
**Tempo**: 1-2 horas

---

## 5️⃣ Se Tudo Falhar: Restart Completo

```bash
# 1. Backup de precaução (se houver dados):
docker exec sofia-postgres pg_dump -U sofia sofia_db > backup-$(date +%Y%m%d).sql

# 2. Restart do container:
docker restart sofia-postgres

# 3. Aguardar 10 segundos:
sleep 10

# 4. Verificar se subiu:
docker ps | grep sofia-postgres

# 5. Testar conexão:
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "SELECT version();"

# 6. Rodar collectors:
npm run collect:cardboard
npm run collect:arxiv-ai
npm run collect:ai-companies

# 7. Auditar:
npm run audit
```

---

## 📊 Output Esperado (quando funcionar)

```
🔍 SOFIA PULSE - DATABASE AUDIT
================================

📊 Encontradas 13 tabelas no banco

📋 Analisando: cardboard_production
────────────────────────────────────────────────────────
   Registros: 50
   Coluna de data: collected_at
   Período: 2025-11-15 → 2025-11-17
   ✅ HOJE - Dados coletados hoje!

📋 Analisando: arxiv_ai_papers
────────────────────────────────────────────────────────
   Registros: 100
   Coluna de data: collected_at
   Período: 2025-11-15 → 2025-11-17
   ✅ HOJE - Dados coletados hoje!

...

✅ Tabelas com dados: 13/13
❌ Tabelas vazias: 0/13
📈 Total de registros: 786
```

---

## 🆘 Se Precisar de Ajuda

**Cole aqui os outputs de**:
1. `bash scripts/quick-db-check.sh`
2. `docker exec -i sofia-postgres psql -U sofia -d sofia_db < scripts/investigate.sql`
3. `docker logs sofia-postgres --tail 50`

Com esses 3 outputs eu consigo diagnosticar EXATAMENTE o problema.

---

**Criado**: 2025-11-17
**Branch**: claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE
