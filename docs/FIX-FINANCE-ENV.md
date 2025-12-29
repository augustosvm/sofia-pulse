# 🔧 FIX: Finance Authentication Error

**Erro Encontrado**:
```
❌ password authentication failed for user "postgres"
```

**Causa REAL**: Nomes de variáveis ERRADOS no `.env`!

Scripts esperam: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
Mas o .env tinha: `DB_USER`, `DB_PASSWORD`, `DB_NAME`

**Solução**: Criar `finance/.env` com nomes CORRETOS de variáveis

---

## ⚡ FIX DEFINITIVO (Execute NO SERVIDOR):

```bash
cd ~/sofia-pulse

# 1. Criar finance/.env com variáveis CORRETAS:
cat > finance/.env << 'EOF'
# PostgreSQL - NOMES CORRETOS (POSTGRES_* não DB_*)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=sofia
POSTGRES_PASSWORD=sofia123strong
POSTGRES_DB=sofia_db

# Connection string alternativa
DATABASE_URL=postgresql://sofia:sofia123strong@localhost:5432/sofia_db

# API Keys
ALPHA_VANTAGE_API_KEY=TM3DVH1A35DUPPZ9
EOF

# 2. Verificar se criou corretamente:
cat finance/.env | grep -E "POSTGRES_USER|POSTGRES_PASSWORD"

# Deve mostrar:
# POSTGRES_USER=sofia
# POSTGRES_PASSWORD=sofia123strong

# 3. Testar coleta:
npm run collect:brazil
```

---

## ✅ Se Funcionar, Rodar TUDO:

```bash
cd ~/sofia-pulse/finance

# Coleta completa + sinais:
npm run invest:full

# OU da raiz:
cd ~/sofia-pulse
npm run collect:finance-all
```

---

## 🔍 Por Que Aconteceu?

### Estrutura de Arquivos:
```
sofia-pulse/
├── .env                    ← .env da raiz
└── finance/
    ├── .env                ← .env do finance (FALTAVA!)
    └── scripts/
        └── collect-brazil-stocks.ts
```

### O Problema:
1. Scripts rodando em `finance/scripts/`
2. `dotenv.config()` procura `.env` no diretório atual
3. Não achava `.env` → usava fallback `'postgres'`

### A Solução:
```bash
cp .env finance/.env  # ← Copia credenciais corretas
```

---

## 📊 Teste de Conexão

```bash
# Testar PostgreSQL diretamente:
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "SELECT version();"

# Se funcionar → Banco OK!
# Agora testar collector:
cd ~/sofia-pulse/finance
npm run collect:brazil
```

**Output esperado**:
```
✅ Conectado ao PostgreSQL
📊 Coletando dados da B3...
💾 Salvando 32 stocks no banco...
✅ Coleta concluída! 32 registros inseridos
```

---

## 🚀 Depois de Corrigir

```bash
# Popular TUDO:
cd ~/sofia-pulse
npm run collect:finance-all

# Verificar:
npm run audit | grep -E "market_data|funding_rounds"

# Ver dados coletados:
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "
SELECT COUNT(*) FROM sofia.market_data_brazil;
SELECT COUNT(*) FROM sofia.market_data_nasdaq;
SELECT COUNT(*) FROM sofia.funding_rounds;
"
```

---

## 💡 Prevenção Futura

Para evitar esse problema novamente, mantenha `.env` sincronizado:

```bash
# Sempre que atualizar .env da raiz:
cp ~/sofia-pulse/.env ~/sofia-pulse/finance/.env
```

Ou adicione ao `.gitignore` e documente:
```bash
echo "# Finance usa .env da raiz (copiar manualmente)" >> finance/README.md
```

---

**EXECUTE AGORA**:
```bash
cp ~/sofia-pulse/.env ~/sofia-pulse/finance/.env && cd ~/sofia-pulse/finance && npm run invest:full
```
