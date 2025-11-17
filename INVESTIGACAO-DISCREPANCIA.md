# 🔍 Investigação: Discrepância de Tabelas

**Data**: 2025-11-17
**Status**: 🔴 INVESTIGANDO

---

## 🚨 O Problema

### Achados Contraditórios:

1. **Script TypeScript** (`npm run investigate`):
   - ✅ Conectou no banco com sucesso
   - ✅ Encontrou **29 tabelas**
   - ✅ Listou todas: ai_companies, arxiv_ai_papers, cardboard_production, etc.

2. **Conexão direta psql**:
   - ✅ Conectou no banco com sucesso
   - ❌ Comando `\dn` mostrou **0 schemas**
   - ❌ Aparentemente banco vazio

### Por que isso é estranho?

Se há 29 tabelas, DEVE existir pelo menos 1 schema (geralmente `public`).

---

## 🤔 Hipóteses Possíveis

### Hipótese 1: Schemas Diferentes ✅ MAIS PROVÁVEL
As tabelas podem estar em um schema que não é o `public` padrão.

**Como verificar**:
```sql
SELECT schemaname, COUNT(*)
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
GROUP BY schemaname;
```

**Por que acontece**:
- Collectors podem ter criado schema próprio
- Migrations podem ter usado schema customizado
- Variável `search_path` pode estar configurada diferente

---

### Hipótese 2: Bancos de Dados Diferentes ❌ IMPROVÁVEL
Scripts TypeScript podem estar conectando em database diferente do psql.

**Como verificar**:
```sql
-- No psql, rode:
SELECT current_database();

-- Depois liste todas as databases:
\l
```

**Por que é improvável**:
- O .env aponta para `sofia_db`
- Os scripts usam as mesmas variáveis de ambiente
- Mas vale verificar

---

### Hipótese 3: Problema de Permissões ❌ IMPROVÁVEL
O usuário `sofia` pode não ter permissão para ver certos schemas.

**Como verificar**:
```sql
SELECT * FROM information_schema.schemata;
```

**Por que é improvável**:
- Scripts TypeScript conseguem ver as tabelas
- Ambos usam mesmo usuário (`sofia`)

---

### Hipótese 4: Cache ou Timing Issue ❌ MUITO IMPROVÁVEL
Conexões diferentes podem estar vendo estados diferentes.

**Como verificar**:
Rodar ambos os comandos simultaneamente e comparar.

---

## 🔧 Como Investigar

### Opção 1: Executar SQL completo (RECOMENDADO)

```bash
# Execute a investigação completa:
docker exec -i sofia-postgres psql -U sofia -d sofia_db < scripts/investigate.sql

# Vai mostrar:
# - Todos os schemas
# - Todas as tabelas (com schema)
# - Contagem de registros
# - Search path
# - Databases disponíveis
```

---

### Opção 2: Verificação rápida

```bash
# Execute o quick check:
bash scripts/quick-db-check.sh

# Vai mostrar resumo de:
# - Schemas existentes
# - Tabelas por schema
# - Contagem aproximada de registros
```

---

### Opção 3: Comandos individuais no psql

Se você está DENTRO do psql (`sofia_db=#`), rode:

```sql
-- 1. Ver qual database você está:
SELECT current_database();

-- 2. Ver search_path:
SHOW search_path;

-- 3. Ver TODOS os schemas:
SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg_%' AND nspname != 'information_schema';

-- 4. Ver tabelas com nome completo (schema.tabela):
SELECT schemaname, tablename FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema');

-- 5. Contar registros aproximados:
SELECT schemaname, tablename, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC;
```

---

## 📊 O Que Esperamos Encontrar

### Se Hipótese 1 estiver correta (schema diferente):

```
schemaname     | tablename              | n_live_tup
---------------|------------------------|------------
sofia_schema   | ai_companies           | 20
sofia_schema   | arxiv_ai_papers        | 100
sofia_schema   | cardboard_production   | 50
...
```

**Solução**: Ajustar `search_path` ou sempre usar `schema.tabela` nas queries.

---

### Se Hipótese 2 estiver correta (database diferente):

```
current_database
-----------------
postgres  ← ERRADO! Deveria ser sofia_db
```

**Solução**: Conectar no database correto ou ajustar .env.

---

## 🚀 Próximos Passos

1. **URGENTE**: Rodar `bash scripts/quick-db-check.sh` para diagnóstico rápido

2. **Se quick-check mostrar 0 tabelas**:
   - Listar todas as databases (`\l` no psql)
   - Verificar se tabelas estão em outro database

3. **Se quick-check mostrar tabelas em schema diferente**:
   - Atualizar audit script para buscar em todos os schemas
   - Ou: Migrar tabelas para schema `public`
   - Ou: Configurar `search_path` padrão

4. **Depois de resolver**:
   - Rodar `npm run audit` (atualizado)
   - Verificar se dados de sábado existem
   - Confirmar se cron jobs estão funcionando

---

## 💡 Comandos Úteis de Referência

```bash
# Ver logs do PostgreSQL:
docker logs sofia-postgres --tail 100

# Ver status do container:
docker ps -a | grep sofia

# Verificar variáveis de ambiente dentro do container:
docker exec sofia-postgres env | grep POSTGRES

# Backup do schema atual (precaução):
docker exec sofia-postgres pg_dump -U sofia -d sofia_db --schema-only > backup-schema.sql

# Conectar como superuser (para ver tudo):
docker exec -it sofia-postgres psql -U postgres
```

---

## 📝 Resultados da Investigação

### Execute os scripts e cole os resultados aqui:

```bash
# 1. Quick check
bash scripts/quick-db-check.sh

# Resultados:
# [Cole aqui]


# 2. Investigação completa
docker exec -i sofia-postgres psql -U sofia -d sofia_db < scripts/investigate.sql

# Resultados:
# [Cole aqui]
```

---

**Atualizado**: 2025-11-17
**Próximo passo**: Executar quick-db-check.sh
