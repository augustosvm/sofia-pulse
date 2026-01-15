# ACLED Aggregated Data Pipeline - PostgreSQL

Pipeline de ingestão de **dados agregados oficiais** do ACLED para PostgreSQL.

## ⚠️ IMPORTANTE: Por que NÃO derivar agregados de eventos?

### Justificativa Legal e Metodológica

**1. Rastreabilidade Legal**
- Os agregados oficiais do ACLED são publicados com metodologia documentada
- Recriar agregados via `GROUP BY` não garante conformidade com a metodologia oficial
- Em auditorias ou citações, é necessário provar que os números vêm da fonte primária

**2. Consistência Metodológica**
- O ACLED aplica filtros, ajustes e normalizações específicas nos agregados
- Eventos podem conter duplicatas ou registros preliminares que são corrigidos nos agregados
- A granularidade temporal pode ser diferente (semana epidemiológica vs semana calendar

ária)

**3. Auditabilidade**
- Ter os agregados oficiais permite comparar com qualquer reconstrução interna
- Facilita detectar divergências causadas por bugs ou transformações incorretas
- Garante compliance em relatórios governamentais ou acadêmicos

**4. Completude**
- Alguns agregados regionais incluem países sem dados event-level públicos
- Datasets históricos agregados podem ter cobertura maior que eventos individuais

### Conclusão
**Sempre ingira os agregados oficiais diretamente.**  
Só crie agregados derivados SE e SOMENTE SE você:
1. Documentar claramente que NÃO são dados oficiais
2. Manter ambos (oficial + derivado) para comparação
3. Never substituir os oficiais pelos derivados

---

## Instalação

```bash
cd c:\Users\augusto.moreira\Documents\sofia-pulse

# Install dependencies
pip install requests beautifulsoup4 pandas psycopg2-binary openpyxl

# Create database schemas
psql -h 91.98.158.19 -U sofia -d sofia_db -f sql/create-acled-aggregated-schema.sql
```

## Configuração

### Credenciais ACLED

Defina as variáveis de ambiente ou edite o script:

```bash
export ACLED_EMAIL="your_email@example.com"
export ACLED_PASSWORD="your_password"
```

### PostgreSQL

O script usa automaticamente as mesmas configurações do `.env`:

```
POSTGRES_HOST=91.98.158.19
POSTGRES_PORT=5432
POSTGRES_USER=sofia
POSTGRES_PASSWORD=SofiaPulse2025Secure@DB
POSTGRES_DB=sofia_db
```

## Uso

### Executar Coletor

```bash
python scripts/collect-acled-aggregated-postgres.py
```

### O que o coletor faz:

1. **Autentica** no ACLED com credenciais fornecidas
2. **Scrapa** cada página de agregado
3. **Baixa** os arquivos XLSX/CSV oficiais
4. **Detecta automaticamente** o nível de agregação:
   - `country-year`
   - `country-month-year`
   - `regional` (admin1-week, etc)
5. **Calcula hash SHA256** para versionamento
6. **Insere no PostgreSQL** na tabela apropriada
7. **Registra metadata** completa

### Agendar Execução Semanal

**Windows Task Scheduler:**
```
Trigger: Weekly, Monday 3 AM
Action: python scripts\collect-acled-aggregated-postgres.py
Start in: c:\Users\augusto.moreira\Documents\sofia-pulse
```

**Linux/Mac Cron:**
```cron
0 3 * * 1 cd /path/to/sofia-pulse && python scripts/collect-acled-aggregated-postgres.py
```

---

## Estrutura do Banco de Dados

### Schemas

- `acled_metadata`: Rastreamento de coletas
- `acled_aggregated`: Dados agregados oficiais

### Tabelas

```sql
-- Metadata
acled_metadata.datasets

-- Aggregated Data
acled_aggregated.country_year           -- Agregados país-ano
acled_aggregated.country_month_year     -- Agregados país-mês-ano
acled_aggregated.regional               -- Agregados regionais flexíveis
```

### Exemplo de  Query

```sql
-- Ver últimas coletas
SELECT * FROM acled_metadata.latest_datasets;

-- Eventos de violência política por país em 2025
SELECT country, year, events 
FROM acled_aggregated.country_year
WHERE year = 2025 AND dataset_slug = 'political-violence-country-year'
ORDER BY events DESC;

-- Resumo por nível de agregação
SELECT * FROM acled_metadata.aggregation_summary;
```

---

## Detecção Automática

O pipeline detecta automaticamente se um dataset é agregado usando heurísticas:

**Classificado como AGREGADO se:**
- ✅ Existe coluna `events` ou `fatalities` (contadores)
- ✅ Existe coluna temporal (`year`, `month`, `week`)
- ✅ Existe coluna geográfica (`country`, `admin1`)
- ❌ NÃO existe `event_date`, `actor1`, `latitude` (indicadores de event-level)

**Granularidade Detectada:**
- `country-year`: Se tem `country` + `year`
- `country-month-year`: Se tem `country` + `year` + `month`
- `regional`: Se tem `admin1`, `week`, ou outros níveis sub-nacionais

---

## Validação

### Verificar se dados foram inseridos

```bash
psql -h 91.98.158.19 -U sofia -d sofia_db
```

```sql
-- Contar registros por dataset
SELECT dataset_slug, COUNT(*) as records
FROM acled_aggregated.country_year
GROUP BY dataset_slug;

-- Ver metadata da última coleta
SELECT dataset_slug, file_name, collected_at, file_hash
FROM acled_metadata.datasets
ORDER BY collected_at DESC
LIMIT 10;
```

### Logs

Verifique `acled_aggregated_postgres.log` para:
- Autenticação bem-sucedida
- Downloads completados
- Inserções no PostgreSQL
- Erros

---

## Adicionar Novos Datasets

Edite `DATASETS` em `collect-acled-aggregated-postgres.py`:

```python
{
    "slug": "new-dataset-slug",
    "url": "https://acleddata.com/aggregated/...",
    "aggregation_level": "country-week",
    "region": "Global"
}
```

---

## Troubleshooting

### Erro de Autenticação
- Verifique `ACLED_EMAIL` e `ACLED_PASSWORD`
- Teste o login manualmente em https://acleddata.com/user/login

### Nenhum Link de Download Encontrado
- O ACLED pode ter mudado a estrutura da página
- Verifique logs em `acled_aggregated_postgres.log`
- Acesse a URL manualmente e veja se o link está presente

### Erro de Conexão PostgreSQL
- Verifique `DB_CONFIG` no script
- Teste: `psql -h 91.98.158.19 -U sofia -d sofia_db`

### Hash Sempre Diferente
- Normal se o ACLED atualiza dados frequentemente
- O coletor salva cada versão com timestamp
- Use `ON CONFLICT` para evitar duplicatas

---

## Datasets Cobertos

| Slug | Agregação | Região |
|------|-----------|--------|
| `political-violence-country-year` | country-year | Global |
| `political-violence-country-month-year` | country-month-year | Global |
| `demonstrations-country-year` | country-year | Global |
| `civilian-targeting-country-year` | country-year | Global |
| `fatalities-country-year` | country-year | Global |
| `civilian-fatalities-country-year` | country-year | Global |
| `aggregated-europe-central-asia` | regional | Europa/Ásia Central |
| `aggregated-us-canada` | regional | EUA/Canadá |
| `aggregated-latin-america-caribbean` | regional | América Latina |
| `aggregated-middle-east` | regional | Oriente Médio |
| `aggregated-asia-pacific` | regional | Ásia-Pacífico |
| `aggregated-africa` | regional | África |

---

## Arquitetura

```
┌─────────────────────────────────────────────────┐
│ ACLED Website (Dados Oficiais Agregados)       │
└─────────────────┬───────────────────────────────┘
                  │ scraping + login
                  ▼
┌─────────────────────────────────────────────────┐
│ Collector Python                                │
│ - Detecção automática de agregação             │
│ - Hash SHA256 para versionamento                │
│ - Retry com backoff                             │
└─────────────────┬───────────────────────────────┘
                  │ insert
                  ▼
┌─────────────────────────────────────────────────┐
│ PostgreSQL                                      │
│ ├─ acled_metadata.datasets                     │
│ ├─ acled_aggregated.country_year               │
│ ├─ acled_aggregated.country_month_year         │
│ └─ acled_aggregated.regional                   │
└─────────────────────────────────────────────────┘
```

---

## Licença

Parte do projeto Sofia Pulse.  
Dados ACLED são propriedade do Armed Conflict Location & Event Data Project.
