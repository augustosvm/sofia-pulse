# 📊 Collector Coverage Analysis

## Total Collectors: **55**

### ✅ Currently Covered in Cron: **22 collectors** (40%)

#### Fast APIs Script (12 collectors):
1. ✅ collect-electricity-consumption.py
2. ✅ collect-port-traffic.py
3. ✅ collect-commodity-prices.py
4. ✅ collect-semiconductor-sales.py
5. ✅ collect-socioeconomic-indicators.py
6. ✅ collect-energy-global.py
7. ✅ collect-hackernews.ts
8. ✅ collect-npm-stats.ts
9. ✅ collect-pypi-stats.ts
10. ✅ collect-arxiv-ai.ts
11. ✅ collect-space-industry.ts
12. ✅ collect-cybersecurity.ts

#### Limited APIs Script (10 collectors):
13. ✅ collect-github-trending.ts
14. ✅ collect-github-niches.ts
15. ✅ collect-reddit-tech.ts
16. ✅ collect-openalex.ts
17. ✅ collect-nih-grants.ts
18. ✅ collect-asia-universities.ts
19. ✅ collect-gdelt.ts
20. ✅ collect-ai-regulation.ts
21. ✅ collect-epo-patents.ts
22. ✅ collect-wipo-china-patents.ts

---

## ❌ MISSING: **33 collectors** (60%) NOT IN CRON!

### International Organizations (8 collectors):
23. ❌ collect-who-health.py - WHO health data
24. ❌ collect-unicef.py - UNICEF child welfare
25. ❌ collect-ilostat.py - ILO labor statistics
26. ❌ collect-un-sdg.py - UN Sustainable Development Goals
27. ❌ collect-hdx-humanitarian.py - Humanitarian Data Exchange
28. ❌ collect-wto-trade.py - World Trade Organization
29. ❌ collect-fao-agriculture.py - Food and Agriculture Org
30. ❌ collect-cepal-latam.py - CEPAL/ECLAC Latin America

### Women & Gender Data (6 collectors):
31. ❌ collect-women-world-bank.py - World Bank gender
32. ❌ collect-women-eurostat.py - EU gender data
33. ❌ collect-women-fred.py - US Fed gender data
34. ❌ collect-women-ilostat.py - ILO gender labor
35. ❌ collect-women-brazil.py - Brazil gender data
36. ❌ collect-central-banks-women.py - Women in central banks

### Brazil Data (6 collectors):
37. ❌ collect-bacen-sgs.py - Brazil Central Bank (Selic, IPCA)
38. ❌ collect-ibge-api.py - IBGE official data
39. ❌ collect-ipea-api.py - IPEA economic data
40. ❌ collect-mdic-comexstat.py - Import/export data
41. ❌ collect-brazil-ministries.py - Ministry budgets
42. ❌ collect-brazil-security.py - Crime data 27 states

### Social & Demographics (5 collectors):
43. ❌ collect-religion-data.py - World religion data
44. ❌ collect-world-ngos.py - Top 200 NGOs
45. ❌ collect-drugs-data.py - UNODC drug data
46. ❌ collect-world-security.py - Security by region
47. ❌ collect-world-tourism.py - Tourism 90+ countries

### Sports (3 collectors):
48. ❌ collect-sports-federations.py - FIFA, IOC rankings
49. ❌ collect-sports-regional.py - 17 regional sports
50. ❌ collect-world-sports.py - Olympics, WHO activity

### Other (5 collectors):
51. ❌ collect-world-bank-gender.py - WB gender focus
52. ❌ collect-basedosdados.py - Brazil open datasets
53. ❌ collect-ai-companies.ts - AI companies data
54. ❌ collect-hkex-ipos.ts - Hong Kong IPOs
55. ❌ collect-cardboard-production.ts - Cardboard production

---

## 🎯 Impact of Missing Collectors

### Critical Missing (High Priority):

**Brazil Data** (6 collectors) - ESSENTIAL for Brazilian analysis:
- BACEN (Selic, inflation) - Used in economic correlation
- IBGE (official demographics) - Population, GDP regional
- IPEA (historical series) - Long-term trends
- ComexStat (trade) - Export/import by product
- Ministries (budget) - Government spending
- Security (crime) - 27 states crime data

**International Orgs** (8 collectors) - 92K+ records:
- WHO, UNICEF, ILO, UN SDG, HDX, WTO, FAO, CEPAL
- Used in: socioeconomic reports, correlations, quality of life

**Women & Gender** (6 collectors) - Gender gap analysis:
- World Bank, Eurostat, FRED, ILO, Brazil, Central Banks
- Used in: Women Global Analysis report

**Social** (5 collectors) - 200+ NGOs, religion, drugs:
- Used in: Social Intelligence report

**Sports** (3 collectors) - FIFA, Olympics, IOC:
- Used in: Olympics & Sports Intelligence report

---

## 🚨 Problems with Current Setup

### 1. No Error Details in WhatsApp
Current alert only shows:
```
❌ Failed: 2
• GitHub Trending
• Reddit Tech
```

**Missing**:
- WHY it failed (SQL error? API key? Network?)
- Error message details
- Which table/operation failed
- Timestamp of failure

### 2. No Logs Captured
Errors go to `/var/log/sofia-*.log` but:
- No structured logging
- No error parsing
- No SQL error detection
- No API key error detection

### 3. Missing Collectors = Missing Data
33 collectors NEVER run = 0 data from:
- Brazil official sources
- International organizations
- Gender data
- Social/sports data

---

## ✅ SOLUTION NEEDED

### 1. Complete Collector Coverage Script
Create `collect-all-apis.sh` with ALL 55 collectors, grouped by:
- Fast APIs (no rate limit)
- Limited APIs (with rate limit + delay)
- Python collectors (international orgs)
- Brazil collectors (official data)

### 2. Enhanced Error Logging
Each collector should log to:
```
/var/log/sofia/collectors/COLLECTOR_NAME-YYYY-MM-DD.log
```

With structured errors:
```json
{
  "collector": "bacen-sgs",
  "timestamp": "2025-12-03T16:00:00Z",
  "error_type": "sql_error",
  "error_message": "duplicate key value violates unique constraint",
  "table": "bacen_series",
  "stack_trace": "..."
}
```

### 3. Smart WhatsApp Alerts
Instead of just "Failed: 2", send:
```
❌ Collector Failures

1. bacen-sgs
   Error: SQL duplicate key
   Table: bacen_series
   Time: 16:00:15 UTC

2. reddit-tech
   Error: HTTP 403 Forbidden
   API: reddit.com
   Time: 16:02:30 UTC

📝 See logs:
tail -f /var/log/sofia/collectors/bacen-sgs-2025-12-03.log
```

### 4. Error Type Detection
Parse errors and categorize:
- ✅ **SQL Errors** - Constraint violations, type mismatches
- ✅ **API Key Errors** - 401, 403, "missing key"
- ✅ **Network Errors** - Timeout, connection refused
- ✅ **Data Errors** - Parsing failures, unexpected format
- ✅ **Rate Limit** - 429, "rate limit exceeded"

---

## 📋 Next Steps

1. **Create complete collector script** with all 55 collectors
2. **Add structured error logging** with JSON format
3. **Enhance WhatsApp alerts** with error details
4. **Add error parser** to detect SQL/API key/network errors
5. **Update cron** to use new comprehensive script

---

**Created**: 03 Dec 2025
**Total Collectors**: 55
**Currently Running**: 22 (40%)
**Missing**: 33 (60%)
**Priority**: HIGH - Missing critical Brazil + International data
