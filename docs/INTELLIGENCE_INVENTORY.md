# Sofia Pulse - Intelligence Inventory
> Automated audit of collectors, migrations, endpoints, and data coverage.
> Generated: 2026-01-18

---

## 1. Collectors Inventory

### Active Collectors (scripts/)

| Collector | Destination Table | Geo Field | Refresh | Status |
|-----------|-------------------|-----------|---------|--------|
| `jobs-collector.ts` | `sofia.jobs` | `country` / `country_id` | Daily | ✅ Active |
| `gdelt_events_collector.py` | `sofia.gdelt_events` | `country_code` | Daily | ✅ Active |
| `bndes_desembolsos_collector.py` | `sofia.bndes_*` | BR only | Weekly | ✅ Active |
| `cvm_ofertas_collector.py` | `sofia.cvm_*` | BR only | Weekly | ✅ Active |
| `sec_form_d_collector.py` | `sofia.sec_*` | US only | Daily | ✅ Active |

### Inferred from Logs (logs/*-collector.log)

| Collector | Likely Table | Notes |
|-----------|--------------|-------|
| `hackernews-collector` | `hackernews_stories` | Global |
| `github-collector` | `github_trending`, `github_niches` | Global |
| `techcrunch-collector` | `industry_signals` | Global |
| `nvd_cve-collector` | `cybersecurity_events` | Global |
| `cisa_kev-collector` | `cybersecurity_events` | Global |
| `space_launches-collector` | `space_launches` (if exists) | Global |

---

## 2. SQL Migrations Applied

| Migration | Purpose | Key MVs Created |
|-----------|---------|-----------------|
| 001 | ACLED metadata versioning | - |
| 002 | ACLED v3 full | - |
| 005 | Security map views | `mv_security_*` |
| 006 | Skill gap views | `mv_skill_gap_*` |
| 007 | Capital map views | `mv_capital_*` |
| 008 | Capital analytics | `mv_capital_analytics` |
| 009 | Talent enterprise | Talent MVs upgraded |
| 010 | Security enterprise | `mv_security_country_combined` |
| 011 | Opportunity index | `mv_opportunity_by_country` |
| 012 | New domains scaffold | Brain Drain, AI Density scaffolds |
| 013 | Intelligence expansion | Research Velocity, Tool Demand |
| 014 | Phase 2 expansion | Industry Signals, Cyber Risk, Clinical Trials |

---

## 3. API Endpoints (FastAPI)

| Endpoint | MV Source | Status |
|----------|-----------|--------|
| `/api/capital/by-country` | `mv_capital_analytics` | ✅ Live |
| `/api/security/countries` | `mv_security_country_combined` | ✅ Live |
| `/api/opportunity/by-country` | `mv_opportunity_by_country` | ✅ Live |
| `/api/brain-drain/by-country` | `mv_brain_drain_by_country` | ✅ Live |
| `/api/ai-density/by-country` | `mv_ai_capability_density_by_country` | ✅ Live |
| `/api/research-velocity/by-country` | `mv_research_velocity_by_country` | ⚠️ Low Data |
| `/api/tool-demand/by-country` | `mv_tool_demand_by_country` | ⚠️ Low Data |
| `/api/industry-signals/by-country` | `mv_industry_signals_heat_by_country` | ⚠️ Performance Issue |
| `/api/cyber-risk/by-country` | `mv_cyber_risk_by_country` | ⚠️ Performance Issue |
| `/api/clinical-trials/by-country` | `mv_clinical_trials_by_country` | ⚠️ Performance Issue |

---

## 4. Next.js Route Adapters

| Route | FastAPI Target | Status |
|-------|----------------|--------|
| `/api/map/capital/flow` | `/api/capital/by-country` | ✅ Live |
| `/api/map/security` | `/api/security/countries` | ✅ Live |
| `/api/map/talent/skill-gap` | `/api/map/talent/skill-gap` | ✅ Live |
| `/api/map/industry-signals` | `/api/industry-signals/by-country` | ✅ Created |

---

## 5. Data Coverage Summary

| Domain | Source Table | Rows | Countries | Issue |
|--------|--------------|------|-----------|-------|
| Capital | `funding_rounds` | 10,233 | ~7 | Low coverage |
| Security | `acled_aggregated` | 197,932 | 115 | ✅ Good |
| Talent | `jobs` + `research_papers` | 15k + 1k | ~50 | Medium |
| Industry Signals | `industry_signals` | 28,633 | ? | No direct geo column |
| Cyber Risk | `cybersecurity_events` | 1,904 | 0 | ❌ No geo column |
| Clinical Trials | `clinical_trials` | 1,390 | 0 | ❌ No geo column |

---

## 6. Critical Gap: Normalization Layer

**Problem**: Migration 014 uses `ILIKE '%' || country_name || '%'` inside MVs.
This causes:
- O(n*m) complexity per refresh (events × countries).
- Slow refresh times (minutes instead of seconds).
- Non-deterministic results (ambiguous matches).

**Solution**: Create normalization tables with indexed mappings:
1. `sofia.country_aliases` - All known country name variants.
2. `sofia.cyber_event_country_map` - Pre-computed event → country mapping.
3. `sofia.trial_country_map` - Pre-computed trial → country mapping.
4. `sofia.industry_signal_country_map` - Pre-computed signal → country mapping.

These are populated by one-time backfill scripts + ingestion-time updates.

---

## 7. Recommended Actions

1. **Create Migration 015** with normalization tables + indexes.
2. **Create backfill scripts** for each domain.
3. **Rewrite Migration 014** to use mapping tables instead of text joins.
4. **Update collectors** to populate country_code at ingestion time.
5. **Add coverage health checks** for new domains.
