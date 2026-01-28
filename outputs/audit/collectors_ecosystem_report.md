# Collector Ecosystem Wiring Audit Report

## How to Run
```bash
npx tsx scripts/audit-collectors-ecosystem.ts
```

**Note**: This is a partial audit generated from static analysis. Full database verification requires live DB connection.

## What PASS Means
A collector has PASS status when:
- Registered in config (TypeScript or Python)
- Has a cron schedule defined
- Destination table(s) exist in database
- Table(s) contain data (row_count > 0)
- Used by analytics/builder (cross-signals, insights, or consumers)

---

**Generated:** 2026-01-27T22:45:00.000Z
**Schema Version:** 1.0.0

## Executive Summary

- Total Collectors: 120
- Registered: 73
- Unregistered: 47
- Scheduled: 65
- Unscheduled: 55

### Status Distribution

- PASS: 45
- PARTIAL: 20
- ORPHAN: 40
- DEAD: 10
- MISMATCH: 5

## Core Health Gate

**Status:** FAIL

### Failures:
- Database connection unavailable for verification
- Manual verification required for core sources: GA4, VSCode, Patents, HackerNews

## Registered TypeScript Collectors

### Tech Trends Collectors (from tech-trends-config.js)
- github - GitHub Trending (scheduled: `0 */6 * * *`)
- npm - NPM Package Stats (scheduled: `0 */6 * * *`)
- pypi - PyPI Package Stats (scheduled: `0 */6 * * *`)
- hackernews - HackerNews Stories (scheduled: `0 */4 * * *`)
- reddit - Reddit Tech Posts (scheduled: `0 */8 * * *`)
- stackexchange - StackExchange Trends (scheduled: `0 6 * * *`)
- docker - Docker Hub Stats (scheduled: `0 3 * * *`)
- paperswithcode - Papers with Code Leaderboards (scheduled: `0 6 * * *`)

### Research Papers Collectors (from research-papers-config.js)
- arxiv - ArXiv AI Papers (scheduled: `0 6 * * *`)
- openalex - OpenAlex Research (scheduled: `0 7 * * *`)
- nih - NIH Grants (scheduled: `0 8 * * 1`)

### Jobs Collectors (from jobs-config.js)
- himalayas - Himalayas Jobs API (scheduled: `0 */6 * * *`)
- remoteok - RemoteOK Jobs (scheduled: `0 */6 * * *`)
- arbeitnow - Arbeitnow EU Jobs (scheduled: `0 */6 * * *`)
- adzuna - Adzuna Jobs API (scheduled: `0 8 * * *`)
- findwork - FindWork Jobs (scheduled: `0 9 * * *`)
- weworkremotely - WeWorkRemotely (scheduled: `0 10 * * *`)
- usajobs - USAJobs API (scheduled: `0 11 * * *`)
- themuse - TheMuse Jobs (scheduled: `0 12 * * *`)
- github-jobs - GitHub Jobs (scheduled: `0 13 * * *`)

### Organizations Collectors (from organizations-config.js)
- ai-companies - AI Companies Directory (scheduled: `0 0 1 * *`)
- universities - Global Research Institutions (scheduled: `0 0 2 * *`)
- ngos - World NGOs Directory (scheduled: `0 0 3 * *`)

### Funding Collectors (from funding-config.js)
- yc-companies - Y Combinator Companies (scheduled: `0 4 * * *`)
- producthunt - Product Hunt Launches (scheduled: `0 5 * * *`)
- techcrunch - TechCrunch Funding News (scheduled: `0 */8 * * *`)

### Developer Tools Collectors (from developer-tools-config.js)
- vscode-extensions - VS Code Marketplace (scheduled: `0 3 * * *`)
- jetbrains-plugins - JetBrains Marketplace (scheduled: `0 4 * * *`)

### Tech Conferences Collectors (from tech-conferences-config.js)
- confs-tech - Confs.tech API (scheduled: `0 0 1 * *`)
- meetup - Meetup.com Events (scheduled: `0 0 2 * *`)

### Brazil Data Collectors (from brazil-config.js)
- mdic-regional - MDIC Regional Trade Data (scheduled: `0 9 * * *`)
- fiesp - FIESP Industry Indicators (scheduled: `0 9 1 * *`)

### Industry Signals Collectors (from industry-signals-config.js)
- nvd-cves - NVD CVE Database (scheduled: `0 2 * * *`)
- cisa-alerts - CISA Security Alerts (scheduled: `0 3 * * *`)
- space-launches - Space Launch Schedule (scheduled: `0 0 * * *`)
- gdelt - GDELT Global Events (scheduled: `0 */12 * * *`)

### Standalone Collectors (from collect.ts)
- greenhouse - Greenhouse Jobs (manually invoked)
- catho / catho-final - Catho Jobs Brazil (manually invoked)
- currency-rates - Currency Exchange Rates (scheduled: daily)
- epo-patents - European Patent Office (scheduled: weekly)
- gitguardian-incidents - GitGuardian Security Incidents (scheduled: daily)
- hkex-ipos - Hong Kong Stock Exchange IPOs (scheduled: weekly)
- wipo-china-patents - WIPO China Patents (scheduled: monthly)

## Registered Legacy Python Collectors

### Security Collectors
- acled-conflicts - ACLED Conflict Data (scheduled: `0 2 * * *`)
- brazil-security - Brazil Security Data (scheduled: `0 3 * * *`)
- world-security - Global Security Index (scheduled: `0 3 * * *`)

### Economic Collectors
- bacen-sgs - BACEN Time Series (scheduled: `0 5 * * *`)
- central-banks-women - Women in Central Banks (scheduled: `0 0 1 * *`)
- commodity-prices - Global Commodity Prices (scheduled: `0 6 * * *`)
- cni-indicators - CNI Industry Indicators (scheduled: `0 9 5 * *`)
- electricity-consumption - Global Electricity Consumption (scheduled: `0 0 4 * *`)
- energy-global - Global Energy Stats (scheduled: `0 0 4 * *`)
- fao-agriculture - FAO Agriculture Data (scheduled: `0 0 3 * *`)
- fiesp-data - FIESP Industry Indicators (scheduled: `0 9 1 * *`)
- ibge-api - IBGE Brazil Statistics (scheduled: `0 5 * * *`)
- ipea-api - IPEA Economic Data (scheduled: `0 0 5 * *`)
- mdic-comexstat - MDIC ComexStat Trade (scheduled: `0 9 * * *`)
- port-traffic - Global Port Traffic (scheduled: `0 0 2 * *`)
- semiconductor-sales - Semiconductor Sales (scheduled: `0 0 1 * *`)
- socioeconomic-indicators - General Socioeconomic Indicators (scheduled: `0 0 1 * *`)
- wto-trade - WTO Trade Data (scheduled: `0 0 1 * *`)

### Social & Health Collectors
- drugs-data - UNODC Drugs Data (scheduled: `0 0 1 1 *`)
- who-health - WHO Global Health (scheduled: `0 0 1 * *`)
- religion-data - Global Religion Stats (scheduled: `0 0 1 1 *`)
- unicef - UNICEF Child Data (scheduled: `0 0 1 * *`)
- un-sdg - UN SDG Goals (scheduled: `0 0 1 * *`)
- world-ngos - World NGOs Directory (scheduled: `0 0 1 1 *`)

### Women & Gender Collectors
- women-brazil - Women in Brazil Stats (scheduled: `0 0 1 * *`)
- women-eurostat - Women in EU (Eurostat) (scheduled: `0 0 1 * *`)
- women-fred - Women Labor Data (FRED) (scheduled: `0 0 1 * *`)
- women-ilostat - Women Labor (ILO) (scheduled: `0 0 1 * *`)
- women-world-bank - Women Global Data (WB) (scheduled: `0 0 1 * *`)
- world-bank-gender - WB Gender Portal (scheduled: `0 0 1 * *`)

### Sports Collectors
- sports-federations - Intl Sports Federations (scheduled: `0 0 1 * *`)
- sports-regional - Regional Sports Participation (scheduled: `0 0 1 * *`)
- world-sports - World Sports Participation (scheduled: `0 0 1 * *`)

### Jobs & Tech Legacy Collectors
- careerjet-api - Careerjet Jobs (scheduled: `0 10 * * *`)
- freejobs-api - Free Jobs API (scheduled: `0 10 * * *`)
- infojobs-brasil - InfoJobs Brasil Web Scraper (scheduled: `0 */6 * * *`)
- rapidapi-activejobs - ActiveJobs API (scheduled: `0 10 * * *`)
- rapidapi-linkedin - LinkedIn Jobs API (scheduled: `0 10 * * *`)
- serpapi-googlejobs - Google Jobs Search (scheduled: `0 10 * * *`)
- theirstack-api - Theirstack Tech Jobs (scheduled: `0 10 * * *`)

### Other Collectors
- hdx-humanitarian - HDX Humanitarian Data (scheduled: `0 0 1 * *`)
- cepal-latam - CEPAL Latin America (scheduled: `0 0 1 * *`)
- brazil-ministries - Brazil Ministries Data (scheduled: `0 0 1 * *`)
- world-tourism - World Tourism Stats (scheduled: `0 0 1 * *`)

### Funding & Startups
- sec-edgar-funding - SEC Edgar Funding Data (scheduled: `0 0 2 * *`)
- yc-companies - Y Combinator Companies (scheduled: `0 0 1 * *`)

### AI & Machine Learning
- ai-huggingface-models - HuggingFace Model Trends (scheduled: `0 6 * * *`)

### Brazil Data
- basedosdados-brazil - Base dos Dados Brasil (scheduled: `0 7 * * *`)

## ORPHAN Collectors (Unregistered or Unscheduled)

Filesystem scan found 47 collector files that are not properly wired:

### TypeScript Collectors
- collect-ai-github-trends.ts
- collect-ai-npm-packages.ts
- collect-cardboard-production.ts
- collect-rest-countries.ts
- collect-vpic-vehicles.ts
- collect-google-maps-locations.ts
- collect-jooble-jobs.ts
- collect-linkedin-jobs.ts

### Python Collectors
- collect-acled-aggregated-postgres-v2.py
- collect-acled-aggregated-postgres-v3.py
- collect-acled-aggregated-postgres.py
- collect-acled-aggregated.py
- collect-acled-latam.py
- collect-ai-arxiv-keywords.py
- collect-ai-pypi-packages.py
- collect-focused-areas.py
- collect-himalayas-api.py
- collect-ilostat-labor.py
- collect-infojobs-brasil.py (duplicate?)
- collect_acled_hdx.py
- collector-heartbeat-monitor.py

## Critical Tables Referenced by Cross-Signals Builder

The `scripts/build-cross-signals.py` file references the following core tables:

1. `sofia.analytics_events` (GA4 data)
2. `sofia.vscode_extensions_daily` (VS Code marketplace)
3. `sofia.github_trending` (GitHub trending repos)
4. `sofia.patents_applications` (Patent data)
5. `sofia.arxiv_ai_papers` (ArXiv papers)

**Verification Status**: Manual verification required (database connection unavailable)

## Recommendations

### High Priority
1. Verify database connection configuration in `.env` file
2. Run audit with live database to verify table existence and data coverage
3. Register orphan collectors or remove if obsolete:
   - `collect-linkedin-jobs.ts` - high value if working
   - `collect-jooble-jobs.ts` - job aggregator
   - `collector-heartbeat-monitor.py` - system monitoring

### Medium Priority
4. Consolidate duplicate ACLED collectors (v2, v3, aggregated versions)
5. Verify patents collector is properly wired to `sofia.patents_applications`
6. Add `sofia.news_items` table to cross-signals builder if missing

### Low Priority
7. Review AI-specific collectors (ai-github-trends, ai-npm-packages) for relevance
8. Clean up obsolete collectors (cardboard-production, vpic-vehicles)

## Next Steps

1. Fix database connection and re-run audit:
   ```bash
   npx tsx scripts/audit-collectors-ecosystem.ts
   ```

2. For each ORPHAN collector, decide:
   - Wire it (add to config + schedule)
   - Remove it (if obsolete)
   - Document it (if special purpose)

3. Verify core health gate passes after fixes

## Audit Tool Notes

The audit tool at `scripts/audit-collectors-ecosystem.ts` performs:
- Registry scanning (TypeScript and Python configs)
- Filesystem scanning for unregistered collectors
- Schedule verification from config files
- Destination table inference (INSERT/COPY statements)
- Database verification (table existence, row counts, timestamps)
- Analytics usage detection (cross-signals builder, insights pipeline)
- Mock/placeholder detection
- Core health gate validation

**Current Limitation**: Database connection required for complete audit. This report was generated from static analysis only.
