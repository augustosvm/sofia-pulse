# ACLED Aggregated Data Pipeline v3 - Production Complete

Pipeline completo para ingestão de dados agregados oficiais do ACLED com rastreamento de falhas e auditoria.

---

## ⚠️ Por que NÃO Derivar Agregados de Eventos?

**Regra Crítica:** Sempre ingira agregados oficiais diretamente.

**Razões:**
1. **Legal**: Rastreabilidade auditável
2. **Metodológica**: ACLED aplica filtros/ajustes próprios
3. **Compliance**: Necessário para citações governamentais/acadêmicas
4. **Completude**: Alguns agregados têm cobertura maior

---

## 🔒 Segurança

### Setup de Credenciais

1. **Criar `.env`** (NUNCA commit!)
```bash
cp .env.example .env
```

2. **Preencher `.env`**
```env
ACLED_EMAIL=your_email@example.com
ACLED_PASSWORD=your_password
POSTGRES_HOST=your_host
POSTGRES_PORT=5432
POSTGRES_USER=sofia
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=sofia_db
```

3. **Carregar variáveis**

**PowerShell (Windows):**
```powershell
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.+)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}
```

**Bash (Linux/Mac):**
```bash
export $(grep -v '^#' .env | xargs)
```

### Proteção Automática
- Logs sanitizados (sem passwords/cookies)
- Environment variables obrigatórias
- Nenhum segredo hardcoded

---

## 📦 Instalação

### 1. Dependências
```bash
pip install requests beautifulsoup4 pandas psycopg2-binary openpyxl
```

### 2. Database Schema
```bash
# Executar migration
python -c "import psycopg2; conn = psycopg2.connect(host='...', user='...', password='...', database='...'); cur = conn.cursor(); cur.execute(open('sql/migrations/002-acled-v3-full.sql').read()); conn.commit(); print('✅ Schema created')"
```

---

## 🚀 Uso

### Executar Coletor

```bash
# Carregar env vars (veja seção Segurança)
python scripts/collect-acled-aggregated-postgres-v3.py
```

### O Que Faz

1. ✅ **Autentica** (Drupal session)
2. ✅ **4 Estratégias de Scraping**:
   - A: Links diretos `.xlsx`/`.csv`
   - B: Botões "Download"
   - C: Content-Type check
   - D: WordPress pattern matching
3. ✅ **Valida** agregados (flexible detection)
4. ✅ **Salva RAW** em `data/acled/raw/{slug}/{date}/`
5. ✅ **Debug** em `data/acled/debug/` (HTML + links.json)
6. ✅ **Registra TUDO** (success/failed/invalid)
7. ✅ **Versionamento** por SHA256

---

## 📊 Estrutura Database

### Schemas
- `acled_metadata`: Rastreamento completo
- `acled_aggregated`: Dados oficiais

### Tabelas

```sql
-- Metadata (com status tracking)
acled_metadata.datasets
  - UNIQUE(dataset_slug, file_hash, collected_at)
  - status: 'success'|'failed'|'invalid'
  - error_message, http_status, strategy_used

-- Aggregated Data
acled_aggregated.country_year
acled_aggregated.country_month_year
acled_aggregated.regional
```

### Queries Úteis

```sql
-- Ver últimas coletas bem-sucedidas
SELECT * FROM acled_metadata.latest_datasets;

-- Histórico de versões e falhas
SELECT * FROM acled_metadata.version_history;

-- Resumo diário
SELECT * FROM acled_metadata.collection_summary;

-- Ver falhas recentes
SELECT dataset_slug, error_message, http_status, strategy_used
FROM acled_metadata.datasets
WHERE status = 'failed'
ORDER BY collected_at DESC
LIMIT 20;

-- Dados agregados
SELECT country, year, fatalities 
FROM acled_aggregated.country_year
WHERE year = 2025
ORDER BY fatalities DESC;
```

---

## 🔍 Debugging

### Quando falhar:

1. **Verificar `data/acled/debug/`**
   - HTML salvo com status/URL
   - `links.json` com candidate links

2. **Verificar logs**
   - `acled_collector_v3.log`
   - Procurar por "Strategy A/B/C/D"

3. **Verificar metadata**
```sql
SELECT dataset_slug, status, error_message, strategy_used
FROM acled_metadata.datasets
WHERE dataset_slug = 'seu-dataset'
ORDER BY collected_at DESC;
```

---

## ⏰ Agendar Execução

### Windows (Task Scheduler)

**Criar:** `run-acled-v3.bat`
```batch
@echo off
cd c:\Users\augusto.moreira\Documents\sofia-pulse
for /f "tokens=1,2 delims==" %%a in (.env) do set %%a=%%b
python scripts\collect-acled-aggregated-postgres-v3.py
```

**Agendar:** Weekly, Monday 3 AM

### Linux/Mac (Cron)

```cron
0 3 * * 1 cd /path/to/sofia-pulse && export $(grep -v '^#' .env | xargs) && python scripts/collect-acled-aggregated-postgres-v3.py
```

---

## 📋 Datasets Cobertos

| # | Slug | Tipo | Região |
|---|------|------|--------|
| 1 | `political-violence-country-year` | country-year | Global |
| 2 | `political-violence-country-month-year` | country-month-year | Global |
| 3 | `demonstrations-country-year` | country-year | Global |
| 4 | `civilian-targeting-country-year` | country-year | Global |
| 5 | `fatalities-country-year` | country-year | Global |
| 6 | `civilian-fatalities-country-year` | country-year | Global |
| 7 | `aggregated-europe-central-asia` | regional | Europa/Ásia |
| 8 | `aggregated-us-canada` | regional | EUA/Canadá |
| 9 | `aggregated-latin-america-caribbean` | regional | América Latina |
| 10 | `aggregated-middle-east` | regional | Oriente Médio |
| 11 | `aggregated-asia-pacific` | regional | Ásia-Pacífico |
| 12 | `aggregated-africa` | regional | África |

---

## 🆕 Novidades v3

### vs v2.0

| Funcionalidade | v2.0 | v3.0 |
|----------------|------|------|
| **Failure Tracking** | ❌ | ✅ Status tracking |
| **Debug Output** | Básico | ✅ HTML + links.json |
| **Strategies** | 3 | ✅ 4 estratégias |
| **Validation** | Rígida | ✅ Flexível |
| **Granularity** | Buggy | ✅ Fixed (admin1→regional) |
| **RAW Files** | ❌ | ✅ Saved to disk |
| **Audit Trail** | Parcial | ✅ Completa |

---

## ❓ Troubleshooting

### Erro: Environment variables required
```bash
export ACLED_EMAIL="your@email.com"
export ACLED_PASSWORD="your_password"
```

### Erro: Authentication failed
1. Verifique credenciais
2. Teste login manual
3. Verifique logs

### Erro: VALIDATION FAILED
**Causa:** Dataset não é agregado oficial  
**Ação:** Verificar metadata, debug HTML

### Nenhum link encontrado
**Debug:**
1. Ver `data/acled/debug/{slug}-links.json`
2. Procurar manualmente no HTML
3. Atualizar estratégias se necessário

---

## 🔐 Recomendações de Segurança

1. ✅ Rotacionar senhas a cada 90 dias
2. ✅ `.gitignore` deve incluir `.env`
3. ✅ Nunca commit logs
4. ✅ Usar env vars em produção
5. ✅ Limitar permissões PostgreSQL

---

## 📄 Arquivos

- [`sql/migrations/002-acled-v3-full.sql`](file:///c:/Users/augusto.moreira/Documents/sofia-pulse/sql/migrations/002-acled-v3-full.sql) - Schema completo
- [`scripts/collect-acled-aggregated-postgres-v3.py`](file:///c:/Users/augusto.moreira/Documents/sofia-pulse/scripts/collect-acled-aggregated-postgres-v3.py) - Coletor v3
- `.env.example` - Template de credenciais
- `.gitignore` - Proteção de segredos

---

## 📜 Licença

Parte do projeto Sofia Pulse.  
Dados ACLED © Armed Conflict Location & Event Data Project.

**NUNCA redistribua dados ACLED sem permissão explícita.**
