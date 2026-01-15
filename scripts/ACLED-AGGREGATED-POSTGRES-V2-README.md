# ACLED Aggregated Data Pipeline - Production Grade

**Version 2.0** - Security Hardened & Robustness Enhanced

Pipeline seguro e robusto para ingestão de dados agregados oficiais do ACLED em PostgreSQL.

---

## ⚠️ CRITICAL: Por que NÃO derivar agregados de eventos?

### Justificativa Legal e Metodológica

**1. Rastreabilidade Legal**
- Agregados oficiais do ACLED têm metodologia documentada e auditável
- Recriar via `GROUP BY` não garante conformidade com metodologia oficial
- Necessário para citações, auditorias e compliance regulatório

**2. Consistência Metodológica**
- ACLED aplica filtros, ajustes e normalizações específicas
- Eventos podem conter duplicatas ou registros preliminares
- Granularidade temporal pode diferir (semana epidemiológica vs calendário)

**3. Auditabilidade**
- Permite comparar agregados oficiais vs reconstruções internas
- Facilita detectar divergências de bugs ou transformações
- Garante compliance em relatórios governamentais/acadêmicos

**4. Completude**
- Alguns agregados regionais incluem países sem event-level público
- Datasets históricos podem ter cobertura maior que eventos

### Conclusão

✅ **Sempre ingira os agregados oficiais diretamente**  
❌ **Nunca substitua oficiais por derivados**

---

## 🔒 Segurança

### Configuração de Credenciais

**NUNCA commit credenciais no Git.**

#### 1. Criar arquivo `.env`

```bash
cp .env.example .env
```

#### 2. Preencher `.env`

```env
# ACLED Credentials (REQUIRED)
ACLED_EMAIL=your_email@example.com
ACLED_PASSWORD=your_secure_password

# PostgreSQL (REQUIRED)
POSTGRES_HOST=your_database_host
POSTGRES_PORT=5432
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=your_database_name
```

#### 3. Carregar variáveis

**Linux/Mac:**
```bash
export $(grep -v '^#' .env | xargs)
python scripts/collect-acled-aggregated-postgres-v2.py
```

**Windows PowerShell:**
```powershell
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.+)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}
python scripts/collect-acled-aggregated-postgres-v2.py
```

### Proteção de Logs

O coletor **automaticamente sanitiza logs** removendo:
- Passwords
- Session cookies (SSESS)
- Bearer tokens

### Recomendações de Segurança

1. ✅ **Rotacione senhas regularmente** (a cada 90 dias)
2. ✅ **Use `.gitignore` para `.env`**
3. ✅ **Nunca commit logs** com dados sensíveis
4. ✅ **Use variáveis de ambiente** em produção (não arquivos)
5. ✅ **Limite permissões de acesso** ao PostgreSQL

---

## Instalação

### 1. Dependências

```bash
pip install requests beautifulsoup4 pandas psycopg2-binary openpyxl
```

### 2. Criar Schemas PostgreSQL

```bash
# Run initial schema creation
python -c "import psycopg2; conn = psycopg2.connect(...); cur = conn.cursor(); cur.execute(open('sql/create-acled-aggregated-schema.sql').read()); conn.commit()"

# Run migration for versioning support
python -c "import psycopg2; conn = psycopg2.connect(...); cur = conn.cursor(); cur.execute(open('sql/migrations/001-acled-metadata-versioning.sql').read()); conn.commit()"
```

### 3. Configurar `.env`

Ver seção **Segurança** acima.

---

## Uso

### Executar Coletor

```bash
# Set environment variables (see Security section)
export $(grep -v '^#' .env | xargs)

# Run collector
python scripts/collect-acled-aggregated-postgres-v2.py
```

### O Que o Coletor Faz

1. **✅ Autentica** no ACLED (sessão Drupal segura)
2. **✅ Multi-Strategy Scraping** para encontrar downloads:
   - Strategy A: Links diretos `.xlsx`/`.csv`
   - Strategy B: Botões "Download"
   - Strategy C: Verificação de `Content-Type`
3. **✅ Valida** que dados são agregados oficiais (não event-level)
4. **✅ Versionamento** por SHA256 hash
5. **✅ Detecção automática** de granularidade (country-year, regional, etc)
6. **✅ Inserção PostgreSQL** com UPSERT
7. **✅ Debug** salva HTML em falhas (sem dados sensíveis)

### Validação de Agregados

O coletor **rejeita** datasets com indicadores de event-level:
- `event_date`, `event_id`
- `actor1`, `actor2`
- `latitude`, `longitude` (de evento)
- `source`, `notes`

Se detectado, o dataset é marcado como `is_aggregated=FALSE` e **não** é inserido em `acled_aggregated`.

---

## Estrutura do Banco de Dados

### Schemas

- **`acled_metadata`**: Rastreamento de coletas
- **`acled_aggregated`**: Dados agregados oficiais

### Tabelas

```sql
-- Metadata (com versionamento)
acled_metadata.datasets
  - UNIQUE(dataset_slug, file_hash)  -- Permite múltiplas versões
  
-- Aggregated Data
acled_aggregated.country_year
acled_aggregated.country_month_year
acled_aggregated.regional
```

### Consultas

```sql
-- Ver últimas versões coletadas
SELECT * FROM acled_metadata.latest_datasets;

-- Histórico de versões
SELECT * FROM acled_metadata.version_history;

-- Dados agregados
SELECT country, year, fatalities 
FROM acled_aggregated.country_year
WHERE year = 2025
ORDER BY fatalities DESC;
```

---

## Debugging

### Quando datasets falham:

1. **Verifique `data/acled/debug/`**
   - HTML salvo automaticamente em falhas
   - Contém status code, URL final, HTML snippet

2. **Verifique logs**
   - `acled_collector.log`
   - Procure por "Strategy A/B/C" para ver qual tentativa falhou

3. **Metadata de falhas**
   - Mesmo em falha, tentativas são registradas em `acled_metadata.datasets`

### Exemplo de Debug

```sql
-- Ver datasets que falharam validação
SELECT dataset_slug, is_aggregated, detected_columns
FROM acled_metadata.datasets
WHERE is_aggregated = FALSE;

-- Ver últimas tentativas
SELECT dataset_slug, collected_at, file_name
FROM acled_metadata.datasets
ORDER BY collected_at DESC
LIMIT 20;
```

---

## Agendar Execução

### Linux/Mac (Cron)

```cron
# Weekly on Monday 3 AM
0 3 * * 1 cd /path/to/sofia-pulse && export $(grep -v '^#' .env | xargs) && python scripts/collect-acled-aggregated-postgres-v2.py
```

### Windows (Task Scheduler)

1. Criar batch script `run-acled-collector.bat`:

```batch
@echo off
cd c:\Users\augusto.moreira\Documents\sofia-pulse
for /f "tokens=1,2 delims==" %%a in (.env) do set %%a=%%b
python scripts\collect-acled-aggregated-postgres-v2.py
```

2. Agendar no Task Scheduler:
   - Trigger: Weekly, Monday 3 AM
   - Action: Run `run-acled-collector.bat`

---

## Datasets Cobertos

| # | Slug | Tipo | Região |
|---|------|------|--------|
| 1 | `political-violence-country-year` | country-year | Global |
| 2 | `political-violence-country-month-year` | country-month-year | Global |
| 3 | `demonstrations-country-year` | country-year | Global |
| 4 | `civilian-targeting-country-year` | country-year | Global |
| 5 | `fatalities-country-year` | country-year | Global |
| 6 | `civilian-fatalities-country-year` | country-year | Global |
| 7 | `aggregated-europe-central-asia` | regional | Europa/Ásia Central |
| 8 | `aggregated-us-canada` | regional | EUA/Canadá |
| 9 | `aggregated-latin-america-caribbean` | regional | América Latina |
| 10 | `aggregated-middle-east` | regional | Oriente Médio |
| 11 | `aggregated-asia-pacific` | regional | Ásia-Pacífico |
| 12 | `aggregated-africa` | regional | África |

---

## Troubleshooting

### Erro: `ACLED_EMAIL and ACLED_PASSWORD environment variables required`

**Solução:** Configure as variáveis de ambiente antes de rodar.

```bash
export ACLED_EMAIL="your_email@example.com"
export ACLED_PASSWORD="your_password"
```

### Erro: `Authentication failed - no session cookie`

**Possíveis causas:**
1. Credenciais incorretas
2. ACLED mudou estrutura de login
3. Senha expirada

**Solução:**
1. Teste login manual em https://acleddata.com/user/login
2. Verifique se credenciais estão corretas
3. Verifique logs para detalhes

### Erro: `VALIDATION FAILED: Event-level columns detected`

**Causa:** O dataset não é um agregado oficial.

**Ação:** O coletor corretamente rejeitou o dataset. Verifique se a URL está correta.

### Nenhum download link encontrado

**Causa:** ACLED pode ter mudado estrutura da página.

**Debug:**
1. Verifique `data/acled/debug/{slug}.html`
2. Procure por links manualmente no HTML salvo
3. Atualize lógica de scraping se necessário

---

## Diferenças da v1.0

### ✅ Segurança

- ❌ v1.0: Credenciais hardcoded
- ✅ v2.0: Environment variables obrigatórias
- ✅ v2.0: Logs sanitizados (sem passwords/cookies)

### ✅ Robustez

- ❌ v1.0: Uma estratégia de scraping
- ✅ v2.0: Três estratégias (A, B, C)
- ✅ v2.0: Debug HTML em falhas

### ✅ Validação

- ❌ v1.0: Assume que arquivo é agregado
- ✅ v2.0: Valida e rejeita event-level

### ✅ Versionamento

- ❌ v1.0: `UNIQUE(dataset_slug)` impede histórico
- ✅ v2.0: `UNIQUE(dataset_slug, file_hash)` permite versões

---

## Arquivos

- [`sql/migrations/001-acled-metadata-versioning.sql`](file:///c:/Users/augusto.moreira/Documents/sofia-pulse/sql/migrations/001-acled-metadata-versioning.sql) - Migration para versionamento
- [`scripts/collect-acled-aggregated-postgres-v2.py`](file:///c:/Users/augusto.moreira/Documents/sofia-pulse/scripts/collect-acled-aggregated-postgres-v2.py) - Coletor v2.0
- [`sql/create-acled-aggregated-schema.sql`](file:///c:/Users/augusto.moreira/Documents/sofia-pulse/sql/create-acled-aggregated-schema.sql) - Schema inicial

---

## Licença

Parte do projeto Sofia Pulse.  
Dados ACLED são propriedade do Armed Conflict Location & Event Data Project.

**NUNCA redistribua dados ACLED sem permissão explícita.**
