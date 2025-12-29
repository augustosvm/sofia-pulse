# 📊 RELATÓRIOS BRUTOS COMPLETOS - ANÁLISE DE CÓDIGO SOFIA PULSE

**Data**: 2025-12-29 11:08 BRT  
**Ferramentas**: Pylint 3.3.0, Radon 6.0.1, Flake8 7.3.0

---

## 📋 ÍNDICE

1. [Radon - Complexidade Ciclomática (JSON)](#radon-cc)
2. [Radon - Índice de Manutenibilidade (JSON)](#radon-mi)
3. [Radon - Métricas Brutas (LOC, SLOC, Comments)](#radon-raw)
4. [Pylint - Relatório Completo](#pylint)
5. [Flake8 - Violações PEP 8](#flake8)

---

## 1. RADON - COMPLEXIDADE CICLOMÁTICA (JSON) {#radon-cc}

```json
{
  "scripts\\collect-mdic-comexstat.py": [
    {
      "type": "function",
      "rank": "D",
      "complexity": 22,
      "name": "save_to_database",
      "lineno": 172,
      "endline": 260,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "C",
      "complexity": 19,
      "name": "fetch_comexstat_data",
      "lineno": 46,
      "endline": 141,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "B",
      "complexity": 9,
      "name": "main",
      "lineno": 291,
      "endline": 370,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "A",
      "complexity": 3,
      "name": "log_run_finish",
      "lineno": 275,
      "endline": 289,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "A",
      "complexity": 2,
      "name": "log_run_start",
      "lineno": 262,
      "endline": 273,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "A",
      "complexity": 1,
      "name": "init_db",
      "lineno": 143,
      "endline": 170,
      "col_offset": 0,
      "closures": []
    }
  ],
  "scripts\\collect-fiesp-data.py": [
    {
      "type": "function",
      "rank": "D",
      "complexity": 24,
      "name": "download_and_parse_sensor",
      "lineno": 136,
      "endline": 258,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "D",
      "complexity": 22,
      "name": "download_and_parse_ina",
      "lineno": 281,
      "endline": 393,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "C",
      "complexity": 14,
      "name": "get_excel_links",
      "lineno": 72,
      "endline": 123,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "B",
      "complexity": 9,
      "name": "main",
      "lineno": 395,
      "endline": 455,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "A",
      "complexity": 5,
      "name": "parse_pt_date",
      "lineno": 260,
      "endline": 279,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "A",
      "complexity": 4,
      "name": "clean_num",
      "lineno": 126,
      "endline": 134,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "A",
      "complexity": 1,
      "name": "init_db",
      "lineno": 34,
      "endline": 70,
      "col_offset": 0,
      "closures": []
    }
  ],
  "scripts\\collect-infojobs-web-scraper.py": [
    {
      "type": "function",
      "rank": "D",
      "complexity": 26,
      "name": "scrape_infojobs",
      "lineno": 38,
      "endline": 141,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "B",
      "complexity": 6,
      "name": "insert_jobs",
      "lineno": 143,
      "endline": 227,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "A",
      "complexity": 3,
      "name": "main",
      "lineno": 229,
      "endline": 252,
      "col_offset": 0,
      "closures": []
    }
  ],
  "scripts\\shared\\geo_helpers.py": [
    {
      "type": "function",
      "rank": "C",
      "complexity": 16,
      "name": "normalize_city_name",
      "lineno": 412,
      "endline": 481,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "B",
      "complexity": 9,
      "name": "apply_intelligent_fallbacks",
      "lineno": 483,
      "endline": 519,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "B",
      "complexity": 6,
      "name": "get_or_create_city",
      "lineno": 564,
      "endline": 589,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "A",
      "complexity": 5,
      "name": "get_or_create_country",
      "lineno": 521,
      "endline": 541,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "A",
      "complexity": 5,
      "name": "get_or_create_state",
      "lineno": 543,
      "endline": 562,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "A",
      "complexity": 1,
      "name": "normalize_location",
      "lineno": 591,
      "endline": 600,
      "col_offset": 0,
      "closures": []
    }
  ],
  "scripts\\shared\\org_helpers.py": [
    {
      "type": "function",
      "rank": "B",
      "complexity": 8,
      "name": "batch_link_jobs_to_organizations",
      "lineno": 81,
      "endline": 181,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "A",
      "complexity": 4,
      "name": "get_organization_by_name",
      "lineno": 48,
      "endline": 79,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "A",
      "complexity": 3,
      "name": "get_or_create_organization",
      "lineno": 7,
      "endline": 46,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "A",
      "complexity": 1,
      "name": "get_top_hiring_companies",
      "lineno": 183,
      "endline": 210,
      "col_offset": 0,
      "closures": []
    },
    {
      "type": "function",
      "rank": "A",
      "complexity": 1,
      "name": "get_company_job_history",
      "lineno": 212,
      "endline": 234,
      "col_offset": 0,
      "closures": []
    }
  ]
}
```

---

## 2. RADON - ÍNDICE DE MANUTENIBILIDADE (JSON) {#radon-mi}

```json
{
  "scripts\\collect-mdic-comexstat.py": {
    "mi": 42.012123494208495,
    "rank": "A"
  },
  "scripts\\collect-fiesp-data.py": {
    "mi": 31.93,
    "rank": "A"
  },
  "scripts\\collect-infojobs-web-scraper.py": {
    "mi": 53.57,
    "rank": "A"
  },
  "scripts\\shared\\geo_helpers.py": {
    "mi": 57.82,
    "rank": "A"
  },
  "scripts\\shared\\org_helpers.py": {
    "mi": 72.23126557525735,
    "rank": "A"
  }
}
```

**Escala de Manutenibilidade**:
- **A (20-100)**: Muito manutenível
- **B (10-19)**: Moderadamente manutenível
- **C (0-9)**: Difícil de manter

---

## 3. RADON - MÉTRICAS BRUTAS (LOC, SLOC, Comments) {#radon-raw}

### scripts\collect-mdic-comexstat.py
```
LOC: 372                    # Total de linhas
LLOC: 202                   # Linhas lógicas de código
SLOC: 284                   # Linhas de código fonte (sem brancos)
Comments: 34                # Linhas de comentário
Single comments: 28         # Comentários de linha única
Multi: 3                    # Blocos de comentário multi-linha
Blank: 57                   # Linhas em branco

Comment Stats:
  (C % L): 9%              # Comentários / Total de linhas
  (C % S): 12%             # Comentários / Linhas de código
  (C + M % L): 10%         # (Comentários + Multi) / Total
```

### scripts\collect-fiesp-data.py
```
LOC: 457
LLOC: 307
SLOC: 340
Comments: 39
Single comments: 44
Multi: 0
Blank: 73

Comment Stats:
  (C % L): 9%
  (C % S): 11%
  (C + M % L): 9%
```

### scripts\collect-infojobs-web-scraper.py
```
LOC: 254
LLOC: 122
SLOC: 179
Comments: 24
Single comments: 24
Multi: 5
Blank: 46

Comment Stats:
  (C % L): 9%
  (C % S): 13%
  (C + M % L): 11%
```

### ** TOTAL (3 arquivos) **
```
LOC: 1083                   # Total de linhas
LLOC: 631                   # Linhas lógicas de código
SLOC: 803                   # Linhas de código fonte
Comments: 97                # Linhas de comentário
Single comments: 96
Multi: 8
Blank: 176                  # Linhas em branco

Comment Stats:
  (C % L): 9%              # Taxa de comentários: 9%
  (C % S): 12%
  (C + M % L): 10%
```

**Análise**:
- Taxa de comentários de **9%** está abaixo do ideal (15-20%)
- 16% de linhas em branco (176/1083) é aceitável
- LLOC/LOC ratio de 58% indica código razoavelmente denso

---

## 4. PYLINT - RELATÓRIO COMPLETO {#pylint}

### Score Geral: 6.63/10

### Estatísticas Detalhadas por Tipo de Mensagem

| Message ID | Ocorrências | Categoria | Descrição |
|:---|---:|:---|:---|
| trailing-whitespace | 57 | Convention | Espaços em branco no final da linha |
| line-too-long | 47 | Convention | Linha excede 100 caracteres |
| broad-exception-caught | 26 | Warning | Captura Exception genérico |
| multiple-statements | 23 | Convention | Múltiplas statements em uma linha |
| wrong-import-order | 13 | Convention | Imports fora de ordem PEP 8 |
| redefined-outer-name | 8 | Warning | Variável redefine nome externo |
| unused-variable | 7 | Warning | Variável declarada mas não usada |
| unused-import | 7 | Warning | Import não utilizado |
| bad-indentation | 7 | Convention | Indentação incorreta |
| bare-except | 5 | Warning | except: sem tipo de exceção |
| too-many-locals | 4 | Refactor | Função com muitas variáveis locais |
| too-many-branches | 4 | Refactor | Função com muitos if/else |
| invalid-name | 4 | Convention | Nome de variável não segue padrão |
| too-many-return-statements | 3 | Refactor | Função com muitos returns |
| missing-function-docstring | 3 | Convention | Função sem docstring |
| wrong-import-position | 2 | Convention | Import em posição incorreta |
| too-many-statements | 2 | Refactor | Função muito longa |
| too-many-positional-arguments | 2 | Refactor | Função com muitos args posicionais |
| too-many-arguments | 2 | Refactor | Função com muitos argumentos |
| missing-module-docstring | 2 | Convention | Módulo sem docstring |
| import-error | 2 | Error | Módulo não encontrado |
| f-string-without-interpolation | 2 | Warning | f-string sem variáveis |
| anomalous-backslash-in-string | 2 | Warning | Backslash inválido em string |
| unused-argument | 1 | Warning | Argumento não utilizado |
| unnecessary-pass | 1 | Convention | pass desnecessário |
| possibly-used-before-assignment | 1 | Warning | Variável usada antes de atribuição |
| no-else-return | 1 | Refactor | else desnecessário após return |
| no-else-continue | 1 | Refactor | else desnecessário após continue |
| import-outside-toplevel | 1 | Convention | Import dentro de função |
| duplicate-key | 1 | Error | Chave duplicada em dicionário |
| consider-using-in | 1 | Convention | Usar 'in' ao invés de comparações |
| cell-var-from-loop | 1 | Warning | Variável de loop em closure |

**TOTAL**: 243 issues

### Distribuição por Categoria

- **Convention (C)**: 162 issues (66.7%)
- **Warning (W)**: 59 issues (24.3%)
- **Refactor (R)**: 18 issues (7.4%)
- **Error (E)**: 4 issues (1.6%)

### Dependências Externas

```
dotenv (collect-fiesp-data, collect-infojobs-web-scraper, collect-mdic-comexstat)
psycopg2 (collect-fiesp-data, collect-infojobs-web-scraper, collect-mdic-comexstat)
requests (collect-fiesp-data, collect-infojobs-web-scraper, collect-mdic-comexstat)
beautifulsoup4 (collect-fiesp-data, collect-infojobs-web-scraper)
pandas (collect-fiesp-data)
openpyxl (collect-fiesp-data)
urllib3 (collect-mdic-comexstat)
shared.geo_helpers (collect-fiesp-data, collect-infojobs-web-scraper, collect-mdic-comexstat)
shared.org_helpers (collect-infojobs-web-scraper)
utils.whatsapp_alerts (collect-fiesp-data, collect-mdic-comexstat)
```

---

## 5. FLAKE8 - VIOLAÇÕES PEP 8 {#flake8}

### Total de Violações: 158

### Estatísticas por Código de Erro

| Código | Ocorrências | Descrição |
|:---|---:|:---|
| W293 | 48 | Blank line contains whitespace |
| E501 | 12 | Line too long (>120 characters) |
| W291 | 9 | Trailing whitespace |
| F401 | 7 | Module imported but unused |
| F841 | 6 | Local variable assigned but never used |
| E701 | 23 | Multiple statements on one line (colon) |
| E722 | 5 | Do not use bare 'except' |
| E402 | 2 | Module level import not at top of file |
| F541 | 2 | f-string is missing placeholders |
| W605 | 2 | Invalid escape sequence '\s' |

### Detalhamento Completo

#### W293 - Blank line contains whitespace (48 ocorrências)
Linhas em branco contendo espaços ou tabs. Devem ser completamente vazias.

**Solução**:
```bash
# Remover automaticamente
sed -i 's/^[[:space:]]*$//' scripts/*.py
```

#### E501 - Line too long (12 ocorrências)
Linhas com mais de 120 caracteres.

**Exemplos**:
```python
# scripts/collect-mdic-comexstat.py
print(f"   ⚠️  Rate limit (429) hit. Waiting {backoff}s... (Attempt {attempt+1}/{max_retries})")  # 112 chars
```

#### W291 - Trailing whitespace (9 ocorrências)
Espaços no final das linhas.

#### F401 - Module imported but unused (7 ocorrências)
```python
# collect-fiesp-data.py
import re  # ❌ Não usado
from io import BytesIO  # ❌ Não usado

# collect-mdic-comexstat.py
import json  # ❌ Não usado
from datetime import timedelta  # ❌ Não usado
```

#### F841 - Local variable assigned but never used (6 ocorrências)
```python
# Variáveis declaradas mas não utilizadas
text = element.get_text()  # ❌ Não usado depois
e = Exception("error")  # ❌ Não usado
```

#### E701 - Multiple statements on one line (23 ocorrências)
```python
# ❌ ERRADO
try: val = float(val)
except: val = 0

# ✅ CORRETO
try:
    val = float(val)
except (ValueError, TypeError):
    val = 0
```

#### E722 - Do not use bare 'except' (5 ocorrências)
```python
# ❌ NUNCA faça isso
try:
    risky_operation()
except:  # Captura TUDO, até KeyboardInterrupt!
    pass

# ✅ SEMPRE especifique
try:
    risky_operation()
except (ValueError, TypeError) as e:
    logger.error(f"Error: {e}")
```

#### E402 - Module level import not at top of file (2 ocorrências)
Imports devem estar no topo do arquivo, após docstrings.

#### F541 - f-string is missing placeholders (2 ocorrências)
```python
# ❌ ERRADO
message = f"Error occurred"  # Sem variáveis, use string normal

# ✅ CORRETO
message = "Error occurred"
# OU
message = f"Error occurred: {error_msg}"
```

#### W605 - Invalid escape sequence '\s' (2 ocorrências)
```python
# ❌ ERRADO
pattern = "\s+"  # \s não é reconhecido em string normal

# ✅ CORRETO
pattern = r"\s+"  # Use raw string
# OU
pattern = "\\s+"  # Escape duplo
```

**Localização**: `scripts/shared/geo_helpers.py` linha 68

---

## 🎯 RESUMO EXECUTIVO

### Métricas Consolidadas

| Métrica | Valor |
|:---|---:|
| **Total de Linhas (LOC)** | 1,083 |
| **Linhas de Código (SLOC)** | 803 |
| **Linhas Lógicas (LLOC)** | 631 |
| **Comentários** | 97 (9%) |
| **Linhas em Branco** | 176 (16%) |
| **Total de Funções** | 27 |
| **Complexidade Média** | B (8.48) |
| **Manutenibilidade Média** | A (51.5) |
| **Pylint Score** | 6.63/10 |
| **Flake8 Violations** | 158 |

### Distribuição de Complexidade

- **A (1-5)**: 14 funções (51.9%) ✅
- **B (6-10)**: 6 funções (22.2%) ✅
- **C (11-20)**: 3 funções (11.1%) ⚠️
- **D (21-50)**: 4 funções (14.8%) 🔴
- **E (51+)**: 0 funções (0%) ✅

### Top 4 Funções Mais Complexas (Críticas)

1. `scrape_infojobs()` - **D (26)** - 104 linhas
2. `download_and_parse_sensor()` - **D (24)** - 123 linhas
3. `download_and_parse_ina()` - **D (22)** - 113 linhas
4. `save_to_database()` - **D (22)** - 89 linhas

### Problemas Mais Frequentes

1. **Trailing/Blank Whitespace**: 105 ocorrências (W291, W293)
2. **Linhas Longas**: 47 ocorrências (E501, line-too-long)
3. **Exceções Genéricas**: 31 ocorrências (broad-exception-caught, bare-except)
4. **Múltiplas Statements**: 23 ocorrências (E701, multiple-statements)
5. **Imports Incorretos**: 22 ocorrências (wrong-import-order, unused-import)

---

## 📝 WARNINGS E ERROS

### SyntaxWarning
```
<unknown>:68: SyntaxWarning: invalid escape sequence '\s'
```
**Arquivo**: `scripts/shared/geo_helpers.py` linha 68  
**Fix**: Usar raw string `r"\s+"` ao invés de `"\s+"`

### Import Errors (2)
Módulos locais não encontrados durante análise estática (provavelmente falso positivo).

---

*Relatório gerado em: 2025-12-29 11:08 BRT*
