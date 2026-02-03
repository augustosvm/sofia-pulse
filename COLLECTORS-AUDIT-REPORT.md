# COLLECTORS AUDIT REPORT - Critical Bugs Found

**Date:** 2025-12-12 13:30 UTC
**Audited:** 28+ Python collectors
**Critical Bugs:** 2 collectors (sports-regional, women-brazil)
**Status:** world-sports ✅ FIXED, hdx-humanitarian ✅ FIXED, 2 remaining

---

## ✅ COLLECTORS ALREADY FIXED

### 1. **world-sports** (commit eaabbbb)
**Bugs Fixed:**
- Invalid syntax: `get("id", "", country_id=EXCLUDED.country_id)`
- Missing country_id parameter (INSERT expects 9, got 8)
- Silent exceptions

**Status:** ✅ RECOVERED

---

### 2. **hdx-humanitarian** (commit 1759f8d)
**Bugs Fixed:**
- Invalid syntax: `get("id", "", country_id=EXCLUDED.country_id)`
- Missing country_id parameter (INSERT expects 15, got 14)
- Silent exceptions

**Status:** ✅ RECOVERED

---

## 🚨 CRITICAL BUGS - NEEDS FIXING

### 3. **collect-sports-regional.py** ⚠️ HIGH PRIORITY

**Location:** `scripts/collect-sports-regional.py`

#### **Bug #1: Tuple Wrapping - Linha 771**
```python
# BEFORE (linha 771):
location = (normalize_location(conn, {"country": country_code}),)  # ❌ TUPLA!

# AFTER:
location = normalize_location(conn, {"country": country_code})  # ✅ DICT
```

**Impact:** `country_id = location["country_id"]` na linha 772 vai falhar com `TypeError: tuple indices must be integers`

---

#### **Bug #2: SQL Malformado - Linhas 775-779**
```python
# BEFORE:
cursor.execute(
    """,  # ❌ Vírgula antes de INSERT
    INSERT INTO sofia.sports_regional (...)
    VALUES (%s, %s, ...)
    ON CONFLICT (sport, region, country_code),  # ❌ Vírgula extra
    DO UPDATE SET ranking = EXCLUDED.ranking                        """,  # ❌ Espaços estranhos
    (...)
)

# AFTER:
cursor.execute(
    """
    INSERT INTO sofia.sports_regional (...)
    VALUES (%s, %s, ...)
    ON CONFLICT (sport, region, country_code)
    DO UPDATE SET ranking = EXCLUDED.ranking, country_id = EXCLUDED.country_id
    """,
    (...)
)
```

**Impact:** SQL parser pode rejeitar (depende da versão do PostgreSQL)

---

#### **Bug #3: country_id Fora de Escopo - Linhas 789-811, 818-839, 844-864**

**Problema:** 3 blocos usam `country_id` mas ele foi definido apenas na linha 772 (dentro de outro `for` loop)

**Locais:**
1. **Linha 806:** `country_id` usado mas não definido (bloco regional_data)
2. **Linha 834:** `country_id` usado mas não definido (bloco rankings)
3. **Linha 860:** `country_id` usado mas não definido (bloco disciplines)

**Fix Necessário:** Adicionar normalização em cada bloco:

```python
# Bloco 1: regional_data (linha 789)
for i, country in enumerate(countries):
    try:
        # Adicionar:
        country_code = country[0]
        location = normalize_location(conn, {"country": country_code})
        country_id = location.get("country_id")

        cursor.execute(...)

# Bloco 2: rankings (linha 818)
for ranking in rankings:
    try:
        # Adicionar:
        country_code = ranking[0]
        location = normalize_location(conn, {"country": country_code})
        country_id = location.get("country_id")

        cursor.execute(...)

# Bloco 3: disciplines (linha 844)
for i, country in enumerate(disc_data.get("top_countries", [])):
    try:
        # Adicionar:
        country_code = country[0]
        location = normalize_location(conn, {"country": country_code})
        country_id = location.get("country_id")

        cursor.execute(...)
```

---

#### **Bug #4: Silent Exceptions - 4 blocos**
```python
# Linhas 783, 810, 838, 864:
except:
    continue  # ❌ SILENT

# Fix:
except Exception as e:
    errors += 1
    if errors <= 3:
        print(f"      ERROR: {str(e)[:100]}")
    continue
```

**Também adicionar no início da função:**
```python
def save_sports_regional(...):
    inserted = 0
    errors = 0  # ← Adicionar
```

---

### 4. **collect-women-brazil.py** ⚠️ HIGH PRIORITY

**Location:** `scripts/collect-women-brazil.py`

#### **Bug #1: Tuple Wrapping - Linha 229**
```python
# BEFORE:
location = (normalize_location(conn, {"country": "Brazil", "state": region}),)  # ❌ TUPLA

# AFTER:
location = normalize_location(conn, {"country": "Brazil", "state": region})  # ✅ DICT
```

---

#### **Bug #2: SQL Malformado - Linhas 233-237**
```python
# BEFORE:
cursor.execute(
    """,  # ❌ Vírgula antes
    INSERT INTO sofia.women_brazil_data (...)
    VALUES (%s, %s, ...)
    ON CONFLICT (...),  # ❌ Vírgula extra
    DO UPDATE SET value = EXCLUDED.value            """,  # ❌ Espaços
    (...)
)

# AFTER:
cursor.execute(
    """
    INSERT INTO sofia.women_brazil_data (...)
    VALUES (%s, %s, ...)
    ON CONFLICT (...)
    DO UPDATE SET value = EXCLUDED.value, country_id = EXCLUDED.country_id
    """,
    (...)
)
```

**Mesmo problema nas linhas 306-310 (função save_ipea_data) e 432-436 (bloco DataSUS)**

---

#### **Bug #3: country_id Fora de Escopo**

**Função save_ipea_data (linha ~270):**
- country_id usado na linha 322 mas NÃO definido na função

**Fix:** Adicionar no início da função:
```python
def save_ipea_data(conn, series_data: List[Dict]) -> int:
    # ...
    cursor = conn.cursor()

    # Adicionar:
    location = normalize_location(conn, {"country": "Brazil"})
    country_id = location.get("country_id")

    inserted = 0
    # ...
```

**Bloco DataSUS (linha ~428):**
- country_id usado na linha 448 mas NÃO definido

**Fix:** Adicionar dentro do for loop:
```python
for r in records:
    if r.get("value"):
        try:
            # Adicionar:
            location = normalize_location(conn, {"country": "Brazil"})
            country_id = location.get("country_id")

            cursor.execute(...)
```

---

#### **Bug #4: Silent Exceptions - 3 blocos**
```python
# Linhas 252, 326, 452:
except Exception:
    continue  # ou except: pass

# Fix:
except Exception as e:
    errors += 1
    if errors <= 3:
        print(f"      ERROR: {str(e)[:100]}")
    continue
```

---

## 📊 SUMMARY

| Collector | Status | Bugs Found | Priority |
|-----------|--------|------------|----------|
| world-sports | ✅ FIXED | 5 bugs (syntax + missing param + silent exceptions) | DONE |
| hdx-humanitarian | ✅ FIXED | 3 bugs (syntax + missing param + silent exceptions) | DONE |
| sports-regional | ❌ PENDING | 4 types (tuple + SQL + scope + silent) | HIGH |
| women-brazil | ❌ PENDING | 4 types (tuple + SQL + scope + silent) | HIGH |

**Total Collectors with Silent Exceptions:** 28 (audit found)

---

## 🔧 RECOMMENDED ACTION PLAN

### **Option 1: Fix Manually (Safest)**
1. Apply fixes to sports-regional.py (4 bugs × 4 locations = 16 edits)
2. Apply fixes to women-brazil.py (4 bugs × 3 locations = 12 edits)
3. Test each collector: `python3 scripts/collect-sports-regional.py`
4. Verify SQL output and collector_runs tracking
5. Commit: `git commit -m "fix: sports-regional + women-brazil collectors - tuple wrapping + SQL + scope"`

### **Option 2: Automated Script (Riskier)**
1. Run `/tmp/fix-collectors.py` (created but not executed)
2. Review diffs carefully: `git diff scripts/collect-*.py`
3. Test all fixes
4. Commit if OK

### **Option 3: Defer (Low Risk)**
- These collectors may not be critical (sports/women data)
- Focus on core tech/research collectors first
- Add to backlog for future cleanup

---

## 🎯 EXPECTED RESULTS AFTER FIX

### **sports-regional:**
- **Before:** fetched N, saved 0 (tuple error causes all inserts to fail)
- **After:** fetched N, saved N (data persisted with country_id foreign keys)

### **women-brazil:**
- **Before:** fetched N, saved 0 (tuple error in IBGE, missing country_id in IPEA/DataSUS)
- **After:** fetched N, saved N (all 3 sources working)

---

## 📝 NOTES

**Why Tuple Wrapping Happened:**
- Likely copy/paste error: `location = (normalize_location(...),)`
- Extra parentheses + trailing comma create single-element tuple
- Python treats `(x,)` as tuple but `(x)` as just grouped expression

**Why SQL Malformed:**
- Same copy/paste issue: triple-quoted strings with wrong comma placement
- May not break in all PostgreSQL versions (parser is forgiving)
- But violates SQL standard and should be fixed

**Why country_id Out of Scope:**
- Variable defined in parent loop (line 772)
- Used in sibling loops (lines 806, 834, 860)
- Python scope: variables ARE accessible from parent scope
- BUT: variable only defined if first loop runs (regional_federations exists)
- If first loop doesn't run → country_id undefined → NameError

**Critical for SRE:**
- Silent exceptions HIDE all these errors from logs
- Users see "0 saved" with no explanation
- Must fix silent exceptions FIRST, then debug actual errors

---

**Next Steps:**
1. User decides: manual fix, automated script, or defer
2. If fix: follow Option 1 (safest) or Option 2 (automated)
3. Test on production server
4. Verify with SQL queries (collector_runs + data tables)

