# Segurança e Custos no BigQuery

> [!WARNING]
> **LEIA ANTES DE USAR BIGQUERY**
> Consultas mal formuladas em datasets públicos podem gerar custos de milhares de dólares em segundos.

## Regra de Ouro: DOWNLOAD ONLY
> [!CRITICAL]
> **É ESTRITAMENTE PROIBIDO realizar consultas analíticas ("queries") em datasets públicos do BigQuery.**
>
> O BigQuery cobra por dados processados (scanned). Uma única query analítica em tabelas de patentes públicas pode escanear TBs de dados e custar centenas de dólares.
>
> **Permitido:** Baixar dados brutos (dump/export) de fontes externas gratuitas (ETL) e processar localmente ou no Postgres.
> **Proibido:** Usar o BigQuery como engine de análise para dados públicos (`patents-public-data`, etc).

## Scripts Removidos (Risco Alto)
Os seguintes scripts foram removidos do repositório em 03/02/2026 pois violavam esta regra:

- `test-brazil-patents.py`
- `scripts/test-bigquery-simple.py`

**NUNCA RESTAURE ESSES ARQUIVOS SEM APROVAÇÃO EXPLÍCITA.**

## Coletores Seguros (Mock Data)
Atualmente, os coletores de patentes abaixo operam em modo de segurança, utilizando dados simulados ("mock") e **NÃO** conectam ao BigQuery, garantindo custo zero:

- `scripts/collectors/epo-patents-collector.ts` (ou `collect-epo-patents.ts`)
- `scripts/collectors/wipo-china-patents-collector.ts` (ou `collect-wipo-china-patents.ts`)

## Google Analytics 4 (GA4)
O script `scripts/collect_ga4_bigquery.py` é o **único** autorizado a usar BigQuery.
- **Segurança**: Ele consulta apenas o dataset `analytics_*` do próprio projeto.
- **Custo**: Gera custos normais de armazenamento e consulta dos seus próprios dados.

## Boas Práticas
1. **Sempre use filtros de partição**: `WHERE _TABLE_SUFFIX BETWEEN ...` ou `WHERE partition_date = ...`.
2. **Limite de Bytes**: Ao testar queries no console, verifique a estimativa de bytes processados.
3. **Dry Run**: Use a flag `--dry-run` em scripts sempre que possível antes da execução real.
