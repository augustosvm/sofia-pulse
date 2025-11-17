# 🚀 Como Usar o Sofia Pulse - Guia Rápido

**Atualizado**: 2025-11-17 22:25 UTC

---

## ⚡ Comandos Mais Usados

### Verificar Status do Banco:
```bash
npm run audit
```

**O que faz**: Mostra todas as tabelas, quantos registros, última coleta, status.

**Output esperado**:
```
📊 Encontradas 29 tabelas
✅ Tabelas com dados: 19/29
📈 Total de registros: 941
```

---

### Verificação Rápida (30 segundos):
```bash
bash scripts/quick-db-check.sh
```

**O que faz**: Mostra schemas, tabelas, contagens aproximadas.

---

### Contagem Exata de Tudo:
```bash
docker exec -i sofia-postgres psql -U sofia -d sofia_db < scripts/count-all-data.sql
```

**O que faz**: Contagem exata + datas de primeira e última coleta.

---

## 📊 Rodar Collectors

### Sofia Pulse (9 collectors principais):

```bash
# Rodar TODOS de uma vez:
npm run collect:cardboard && \
npm run collect:wipo-china && \
npm run collect:hkex && \
npm run collect:epo && \
npm run collect:asia-universities && \
npm run collect:arxiv-ai && \
npm run collect:ai-companies && \
npm run collect:openalex && \
npm run collect:nih-grants

# Ou por grupos:
npm run collect:ai-all          # ArXiv + AI Companies
npm run collect:patents-all     # WIPO + EPO
npm run collect:biotech-all     # NIH Grants
npm run collect:research-all    # OpenAlex + ArXiv
npm run collect:china-all       # WIPO + HKEX
```

---

### Finance Collectors (Novos!):

```bash
# Rodar todos:
npm run collect:finance-all

# Ou individualmente:
npm run collect:brazil    # B3 stocks
npm run collect:nasdaq    # NASDAQ stocks
npm run collect:funding   # Funding rounds (vai popular tabela vazia!)
```

---

### Demo Mode (Sem Salvar no Banco):

```bash
# Ver como funciona sem salvar:
npm run demo:all

# Ou individualmente:
npm run collect:cardboard:demo
npm run collect:arxiv-ai:demo
```

---

## 📁 Documentação Criada

### Para Entender o Sistema:

| Arquivo | Quando Usar |
|---------|-------------|
| **RESUMO-FINAL.md** | Ler PRIMEIRO - Resumo executivo completo |
| **PROBLEMA-RESOLVIDO.md** | Entender o bug do audit e como foi resolvido |
| **STATUS-REAL-17NOV.md** | Status detalhado do banco (375 linhas) |
| **ANALISE-TABELAS.md** | Ver origem de cada tabela (Sofia Pulse vs. outras) |
| **COMO-USAR.md** | Este arquivo - Guia rápido de comandos |

### Para Debugging:

| Arquivo | Quando Usar |
|---------|-------------|
| **INVESTIGACAO-DISCREPANCIA.md** | Se audit mostrar resultados estranhos |
| **PROXIMOS-PASSOS.md** | Deploy em produção ou setup inicial |
| **scripts/investigate.sql** | SQL avançado para investigação |
| **scripts/quick-db-check.sh** | Verificação rápida do banco |

---

## 🔍 Troubleshooting

### Audit mostra 0 tabelas:

```bash
# 1. Verificar conexão:
docker ps | grep sofia-postgres

# 2. Testar PostgreSQL:
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "SELECT version();"

# 3. Verificar schemas:
bash scripts/quick-db-check.sh

# 4. Se nada aparecer, rodar investigação completa:
docker exec -i sofia-postgres psql -U sofia -d sofia_db < scripts/investigate.sql
```

---

### Collector falha:

```bash
# Ver output completo:
npm run collect:cardboard 2>&1 | tee collector.log

# Verificar variáveis de ambiente:
cat .env | grep DB_

# Testar conexão com banco:
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "SELECT COUNT(*) FROM sofia.cardboard_production;"
```

---

### Tabela vazia mas collector roda:

```bash
# 1. Verificar se salvou no banco:
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "
SELECT COUNT(*) FROM sofia.cardboard_production;
"

# 2. Ver última coleta:
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "
SELECT MAX(collected_at) FROM sofia.cardboard_production;
"

# 3. Se vazia, verificar se rodou com --dry-run:
npm run collect:cardboard:demo  # Este NÃO salva (demo mode)
npm run collect:cardboard       # Este SALVA no banco
```

---

## 🕐 Cron Jobs (No Servidor)

### Ver cron jobs configurados:
```bash
crontab -l
```

### Ver logs de execução:
```bash
# Logs diários:
tail -f /var/log/sofia-daily.log

# Logs semanais:
tail -f /var/log/sofia-weekly.log

# Ou via journalctl:
journalctl -u cron --since "1 day ago"
```

### Adicionar novo cron job:
```bash
# Editar crontab:
crontab -e

# Exemplo: Rodar às 21:40 todos os dias:
40 21 * * * cd /home/ubuntu/sofia-pulse && npm run collect:cardboard >> /var/log/sofia-daily.log 2>&1
```

---

## 📊 Queries SQL Úteis

### Ver todas as tabelas com dados:
```sql
SELECT
  schemaname,
  tablename,
  n_live_tup as registros
FROM pg_stat_user_tables
WHERE n_live_tup > 0
ORDER BY n_live_tup DESC;
```

### Ver última coleta de todas as tabelas:
```sql
-- Cardboard:
SELECT MAX(collected_at) FROM sofia.cardboard_production;

-- ArXiv AI:
SELECT MAX(collected_at) FROM sofia.arxiv_ai_papers;

-- AI Companies:
SELECT MAX(collected_at) FROM sofia.ai_companies;

-- Patents:
SELECT MAX(collected_at) FROM sofia.wipo_china_patents;
SELECT MAX(collected_at) FROM sofia.epo_patents;
```

### Contagem por schema:
```sql
SELECT
  schemaname,
  COUNT(*) as num_tabelas,
  SUM(n_live_tup) as total_registros
FROM pg_stat_user_tables
GROUP BY schemaname
ORDER BY total_registros DESC;
```

---

## 🎯 Workflows Comuns

### 1. Atualizar Todos os Dados (Manualmente):

```bash
# Sofia Pulse collectors:
npm run collect:cardboard
npm run collect:wipo-china
npm run collect:hkex
npm run collect:epo
npm run collect:asia-universities
npm run collect:arxiv-ai
npm run collect:ai-companies
npm run collect:openalex
npm run collect:nih-grants

# Finance collectors:
npm run collect:finance-all

# Depois auditar:
npm run audit
```

---

### 2. Setup em Novo Servidor:

```bash
# 1. Clonar repo:
git clone https://github.com/augustosvm/sofia-pulse.git
cd sofia-pulse

# 2. Instalar dependências:
npm install

# 3. Configurar .env:
cp .env.example .env
nano .env  # Editar com suas credenciais

# 4. Subir PostgreSQL:
docker run -d \
  --name sofia-postgres \
  --network sofia-network \
  -e POSTGRES_USER=sofia \
  -e POSTGRES_PASSWORD=sofia123strong \
  -e POSTGRES_DB=sofia_db \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  --restart unless-stopped \
  postgres:15-alpine

# 5. Testar conexão:
npm run audit

# 6. Rodar primeira coleta:
npm run demo:all  # Primeiro testar sem salvar
npm run collect:cardboard  # Depois salvar de verdade

# 7. Configurar cron:
crontab -e
# Adicionar: 40 21 * * * cd ~/sofia-pulse && npm run collect:cardboard >> /var/log/sofia-daily.log 2>&1
```

---

### 3. Debugging de Problema:

```bash
# 1. Verificação rápida:
bash scripts/quick-db-check.sh

# 2. Se algo estranho, investigação completa:
docker exec -i sofia-postgres psql -U sofia -d sofia_db < scripts/investigate.sql

# 3. Ver logs de PostgreSQL:
docker logs sofia-postgres --tail 100

# 4. Testar collector individual:
npm run collect:cardboard 2>&1 | tee debug.log

# 5. Auditar resultado:
npm run audit
```

---

### 4. Monitoramento Diário:

```bash
# Manhã: Ver o que foi coletado ontem
npm run audit | grep "HOJE"

# Verificar erros:
grep -i "error" /var/log/sofia-daily.log

# Ver próxima execução cron:
crontab -l

# Contagem rápida:
bash scripts/quick-db-check.sh | grep "Total"
```

---

## 🔗 Links Úteis

### Documentação:
- [RESUMO-FINAL.md](./RESUMO-FINAL.md) - Resumo executivo
- [STATUS-REAL-17NOV.md](./STATUS-REAL-17NOV.md) - Status detalhado
- [ANALISE-TABELAS.md](./ANALISE-TABELAS.md) - Origem das tabelas

### Scripts:
- [scripts/audit-database.ts](./scripts/audit-database.ts) - Audit completo
- [scripts/quick-db-check.sh](./scripts/quick-db-check.sh) - Verificação rápida
- [scripts/count-all-data.sql](./scripts/count-all-data.sql) - Contagem exata

### Collectors:
- [scripts/collect-cardboard-production.ts](./scripts/collect-cardboard-production.ts)
- [scripts/collect-arxiv-ai.ts](./scripts/collect-arxiv-ai.ts)
- [finance/scripts/](./finance/scripts/) - Finance collectors

---

## 💡 Dicas Pro

### Rodar múltiplos collectors em paralelo:
```bash
# Bash (background):
npm run collect:cardboard &
npm run collect:arxiv-ai &
npm run collect:ai-companies &
wait

# Ou sequencial (se der erro em um, para):
npm run collect:cardboard && \
npm run collect:arxiv-ai && \
npm run collect:ai-companies
```

### Ver apenas tabelas atualizadas hoje:
```bash
npm run audit | grep -A 5 "HOJE"
```

### Backup do banco:
```bash
# Schema only:
docker exec sofia-postgres pg_dump -U sofia -d sofia_db --schema-only > schema-backup.sql

# Dados + schema:
docker exec sofia-postgres pg_dump -U sofia -d sofia_db > full-backup.sql

# Apenas dados de uma tabela:
docker exec sofia-postgres pg_dump -U sofia -d sofia_db -t sofia.cardboard_production --data-only > cardboard-data.sql
```

### Restaurar backup:
```bash
# Restaurar schema:
docker exec -i sofia-postgres psql -U sofia -d sofia_db < schema-backup.sql

# Restaurar tudo:
docker exec -i sofia-postgres psql -U sofia -d sofia_db < full-backup.sql
```

---

## ❓ FAQ

### Por que audit mostrava 0 tabelas?

**R**: Bug corrigido! Estava procurando apenas no schema `public` (vazio). Dados sempre existiram nos schemas `sofia` e `sofia_sofia`.

---

### Quantos collectors o Sofia Pulse tem?

**R**: 9 collectors principais + 3 de finance = 12 total.

**Sofia Pulse (9)**:
- cardboard, wipo-china, hkex, epo
- asia-universities, arxiv-ai, ai-companies
- openalex, nih-grants

**Finance (3)**:
- brazil (B3), nasdaq, funding

---

### De onde vêm as outras tabelas (startups, publications, etc.)?

**R**: Provavelmente de outro sistema (Sofia IA principal). São 8 tabelas (763 registros, 81% do total) que não são coletadas pelo Sofia Pulse.

---

### Como saber se cron jobs estão rodando?

**R**: Verificar última coleta via audit:
```bash
npm run audit | grep "HOJE"
```

Se mostrar "HOJE", cron está funcionando!

---

### Qual a diferença entre demo e collect normal?

**R**:
- `npm run demo:all` → **NÃO salva** no banco (apenas mostra output)
- `npm run collect:cardboard` → **SALVA** no banco

---

## 🎉 Quick Start (30 segundos)

```bash
# No servidor:
cd ~/sofia-pulse
git pull
npm run audit

# Esperado:
# ✅ ~941 registros
# ✅ 19 tabelas com dados
# ✅ 14 tabelas atualizadas hoje
```

Se ver isso, **TUDO está funcionando!** 🚀

---

**Criado**: 2025-11-17 22:25 UTC
**Última atualização**: 2025-11-17 22:25 UTC
**Branch**: claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE
