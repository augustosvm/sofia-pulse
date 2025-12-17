# 📊 Análise Regional de Papers Científicos

Este documento explica como usar as queries SQL para analisar os assuntos mais citados em papers científicos por região geográfica.

## 📁 Arquivo Principal

**`papers-by-region-analysis.sql`** - Contém 7 queries SQL prontas para uso

## 🌍 Regiões Mapeadas

As queries mapeiam códigos de países (ISO) para as seguintes regiões:

- 🇧🇷 **Brasil**
- 🇺🇸 **América do Norte** (USA, Canadá, México)
- 🇪🇺 **Europa** (todos os países europeus)
- 🌏 **Ásia** (incluindo Oriente Médio e Ásia Central)
- 🇦🇺 **Oceania** (Austrália, Nova Zelândia, ilhas do Pacífico)
- 🌎 **América Latina** (exceto Brasil)
- 🌍 **África**

## 📋 Queries Disponíveis

### 1️⃣ Função de Mapeamento

Cria a função `map_country_to_region()` que converte códigos de países em regiões.

**Execute primeiro!** Esta função é necessária para todas as outras queries.

```sql
-- Copie e execute a seção 1 do arquivo SQL
CREATE OR REPLACE FUNCTION map_country_to_region(country_code TEXT)...
```

### 2️⃣ Análise Completa por Região

Retorna **todos os assuntos** com suas estatísticas por região:
- Quantidade de papers
- Percentual do total da região
- Total de citações
- Média de citações
- Ranking por papers e por citações

**Use quando:** Quiser ver a distribuição completa de todos os assuntos

### 3️⃣ Top 5 Assuntos por Região (RECOMENDADO)

Retorna os **5 assuntos mais citados** em cada região.

**Use quando:** Quiser um resumo executivo dos principais tópicos por região

**Exemplo de resultado:**
```
🌍 Região          | Assunto              | Papers | % do Total | Citações
-------------------|----------------------|--------|------------|----------
🇧🇷 Brasil         | Machine Learning     | 1,234  | 28%        | 45,678
🇧🇷 Brasil         | Deep Learning        | 892    | 20%        | 32,145
...
```

### 4️⃣ Assunto #1 por Região (MAIS SIMPLES)

Retorna **apenas o assunto mais citado** em cada região.

**Use quando:** Quiser validar rapidamente qual é o tópico dominante

**Exemplo de resultado:**
```
Região                  | Assunto #1           | Papers | Percentual
------------------------|----------------------|--------|------------
🇧🇷 Brasil              | Machine Learning     | 1,234  | 28% do total
🇺🇸 América do Norte    | Deep Learning        | 5,678  | 42% do total
```

### 5️⃣ Estatísticas Gerais por Região

Mostra estatísticas agregadas de cada região:
- Total de papers
- Total de citações
- Média de citações por paper
- Percentual do total global

**Use quando:** Quiser entender o volume de produção científica por região

### 6️⃣ Comparação com Dados Fornecidos

Comentários e instruções para comparar os resultados reais com os dados que você forneceu:

**Dados fornecidos:**
- 🇧🇷 Brasil: AI Ethics - 1,234 papers - 28%
- 🇺🇸 América do Norte: LLMs - 5,678 papers - 42%
- 🇪🇺 Europa: Quantum AI - 3,456 papers - 35%
- 🌏 Ásia: Computer Vision - 6,789 papers - 44%
- 🇦🇺 Oceania: Climate AI - 892 papers - 31%

### 7️⃣ Busca por Assuntos Específicos

Busca papers que contenham assuntos específicos (AI Ethics, LLMs, Quantum, Computer Vision, Climate, Multimodal).

**Use quando:** Quiser verificar se os assuntos mencionados realmente existem nos dados

## 🚀 Como Usar

### Passo 1: Conectar ao Banco

```bash
# Via psql
psql -h localhost -U postgres -d sofia_db

# Ou via script Python
python -c "import psycopg2; conn = psycopg2.connect('dbname=sofia_db user=postgres')"
```

### Passo 2: Criar a Função de Mapeamento

```sql
-- Copie e execute a seção 1 do arquivo papers-by-region-analysis.sql
-- Isso cria a função map_country_to_region()
```

### Passo 3: Executar a Query Desejada

**Para validação rápida (recomendado):**
```sql
-- Execute a query #4 (Assunto #1 por Região)
-- Copie e cole a seção 4 do arquivo SQL
```

**Para análise detalhada:**
```sql
-- Execute a query #3 (Top 5 por Região)
-- Copie e cole a seção 3 do arquivo SQL
```

### Passo 4: Exportar Resultados (Opcional)

```sql
-- Exportar para CSV
\copy (SELECT * FROM ...) TO '/tmp/regional_analysis.csv' CSV HEADER;
```

## 📊 Exemplo de Uso Completo

```bash
# 1. Conectar ao banco
psql -h localhost -U postgres -d sofia_db

# 2. Executar o arquivo completo
\i sql/papers-by-region-analysis.sql

# 3. Ou executar queries individuais
# Copie e cole as queries do arquivo conforme necessário
```

## ⚙️ Configurações

### Filtro de Ano

Por padrão, as queries analisam papers de **2020 em diante**. Para alterar:

```sql
-- Altere esta linha nas queries:
AND p.publication_year >= 2020  -- Mude para o ano desejado
```

### Filtro de Quantidade Mínima

Por padrão, a query #2 filtra assuntos com **pelo menos 5 papers**. Para alterar:

```sql
-- Altere esta linha:
WHERE paper_count >= 5  -- Mude para o mínimo desejado
```

## 🔍 Interpretação dos Resultados

### Percentuais

Os percentuais mostram a **proporção dentro de cada região**, não globalmente.

**Exemplo:**
- "Brasil - Machine Learning - 28%" significa que 28% dos papers brasileiros são sobre Machine Learning
- **NÃO** significa que o Brasil tem 28% dos papers globais sobre Machine Learning

### Papers em Múltiplas Regiões

Um paper pode aparecer em múltiplas regiões se tiver **coautoria internacional**.

**Exemplo:**
- Paper com autores do Brasil e EUA aparece em "Brasil" E "América do Norte"

### Conceitos vs Primary Concept

- **`concepts`**: Array com todos os conceitos/assuntos do paper (até 8)
- **`primary_concept`**: O conceito principal/dominante do paper

A query #4 usa `primary_concept` para simplificar. As queries #2 e #3 usam `concepts` para análise completa.

## 🎯 Casos de Uso

### 1. Validar Dados Fornecidos

**Objetivo:** Verificar se os dados que você forneceu fazem sentido

**Queries:** #4 (assunto #1) + #7 (busca específica)

### 2. Identificar Tendências Regionais

**Objetivo:** Descobrir quais assuntos são mais pesquisados em cada região

**Queries:** #3 (top 5) + #5 (estatísticas gerais)

### 3. Análise Competitiva

**Objetivo:** Comparar produção científica entre regiões

**Queries:** #5 (estatísticas) + #2 (análise completa)

### 4. Relatório Executivo

**Objetivo:** Criar um resumo para apresentação

**Queries:** #4 (assunto #1) + #5 (estatísticas)

## ⚠️ Limitações

1. **Dados dependem da coleta**: Se a tabela `openalex_papers` não tiver dados suficientes, os resultados serão limitados
2. **Coautoria internacional**: Papers com múltiplos países aparecem em múltiplas regiões
3. **Mapeamento de países**: Alguns países podem não estar mapeados (aparecem como "Outros")
4. **Conceitos do OpenAlex**: Os conceitos são gerados por IA e podem não ser 100% precisos

## 📚 Referências

- **Fonte de dados**: OpenAlex (250M+ papers)
- **Campo de região**: `author_countries` (array de códigos ISO)
- **Campo de assuntos**: `concepts` (array de conceitos) e `primary_concept`
- **Período padrão**: 2020 em diante

## 🆘 Troubleshooting

### Erro: "function map_country_to_region does not exist"

**Solução:** Execute a seção 1 do arquivo SQL primeiro para criar a função.

### Erro: "relation openalex_papers does not exist"

**Solução:** Verifique se a tabela existe e se você está conectado ao banco correto:
```sql
SELECT COUNT(*) FROM openalex_papers;
```

### Resultados vazios

**Possíveis causas:**
1. Tabela sem dados: `SELECT COUNT(*) FROM openalex_papers;`
2. Sem dados de países: `SELECT COUNT(*) FROM openalex_papers WHERE author_countries IS NOT NULL;`
3. Filtro de ano muito restritivo: Remova ou ajuste `publication_year >= 2020`

### Performance lenta

**Soluções:**
1. Adicione índices:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_openalex_countries 
     ON openalex_papers USING GIN(author_countries);
   CREATE INDEX IF NOT EXISTS idx_openalex_concepts 
     ON openalex_papers USING GIN(concepts);
   ```
2. Reduza o período: `publication_year >= 2023`
3. Limite as regiões: Remova regiões da cláusula `WHERE region IN (...)`

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique se a função `map_country_to_region()` foi criada
2. Confirme que há dados na tabela `openalex_papers`
3. Ajuste os filtros conforme necessário
4. Consulte os comentários no arquivo SQL

---

**Criado para:** Sofia Pulse  
**Última atualização:** 2025-12-16
