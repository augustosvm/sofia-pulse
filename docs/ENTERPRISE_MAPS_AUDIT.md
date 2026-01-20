# Sofia Pulse Enterprise Maps Audit

## Truth Table - Current State

### Domains Implemented

| Domain | MV Name | API Endpoint | Status |
|--------|---------|--------------|--------|
| Capital | `mv_capital_analytics` | `/api/capital/by-country` | ✅ Live |
| Talent | `mv_skill_gap_country_summary` | `/api/map/talent/skill-gap` | ✅ Live |
| Innovation Velocity | `mv_research_velocity_by_country` | `/api/research-velocity/...` | ⚠️ Low Data |
| Conference Gravity | - | `/api/conference-gravity/...` | ❌ No Table |
| Tool Demand | `mv_tool_demand_by_country` | `/api/tool-demand/...` | ⚠️ Low Data |
| Industry Signals | `mv_industry_signals_heat_by_country` | `/api/industry-signals/...` | ✅ Live |
| Cyber Risk | `mv_cyber_risk_by_country` | `/api/cyber-risk/...` | ✅ Live |
| Clinical Trials | `mv_clinical_trials_by_country` | `/api/clinical-trials/...` | ✅ Live |
| Security | `mv_security_country_combined` | `/api/security/countries` | ✅ Live |
| Opportunity | `mv_opportunity_by_country` | `/api/opportunity/by-country` | ✅ Live |
| Brain Drain | `mv_brain_drain_by_country` | `/api/brain-drain/by-country` | ✅ Live |
| AI Density | `mv_ai_capability_density_by_country` | `/api/ai-density/by-country` | ✅ Live |
| Innovation | `mv_innovation_velocity_by_country` | `/api/innovation/by-country` | ⚠️ Scaffold |
| Regulatory | `mv_regulatory_pressure_by_country` | `/api/regulatory/by-country` | ⚠️ Scaffold |
| Infrastructure | `mv_infrastructure_stress_by_country` | `/api/infrastructure/by-country` | ⚠️ Scaffold |

### Collectors → Base Tables Mapping

| Collector | Base Table | Key Fields | Geo Field |
|-----------|------------|------------|-----------|
| `funding-collector.ts` | `sofia.funding_rounds` | amount_usd, sector, announced_date | country_id → countries.iso_alpha2 |
| `jobs-collector.ts` | `sofia.jobs` | title, description, skills, posted_date | country, country_id |
| `research-papers-collector.ts` | `sofia.research_papers` | title, keywords, authors, publication_date | author_countries (array) |
| `tech-conferences-collector.ts` | `sofia.tech_conferences` | name, location, date | country |
| `developer-tools-collector.ts` | `sofia.developer_tools` | name, category, stars | global (no geo) |
| `organizations-collector.ts` | `sofia.organizations` | name, type | country_id |
| `brazil-collector.ts` | `sofia.security_observations` | events, fatalities | country_code=BR only |
| `industry-signals-collector.ts` | `sofia.industry_signals` | sector, signal_type | global |
| `tech-trends-collector.ts` | `sofia.tech_trends` | topic, momentum | global |

### Country Coverage (Last Check)

| Domain | Countries with Data | Conf > 0.8 | Conf 0.5-0.8 | Conf < 0.5 |
|--------|--------------------:|----------:|-------------:|----------:|
| Capital | 7 | 1 (US) | 0 | 6 |
| Security | 115 | 50+ | 50+ | ~10 |
| Talent | TBD | TBD | TBD | TBD |
| Opportunity | 7 (composite) | 1 | 0 | 6 |

### Mock Status

| Location | Status | Notes |
|----------|--------|-------|
| `sofia-web/src/app/api/map/capital/flow/route.ts` | ✅ No Mocks | Proxies to FastAPI |
| `sofia-web/src/app/api/map/talent/skill-gap/route.ts` | ✅ No Mocks | Direct DB query |
| `sofia-web/src/app/api/map/security/points/route.ts` | ✅ No Mocks | Direct DB query |
| `sofia-pulse/api/security-api.py` | ✅ No Mocks | v2.2-enterprise |

### Migrations Applied

| File | Content | Applied |
|------|---------|---------|
| `001-acled-metadata-versioning.sql` | ACLED schema | ✅ |
| `002-acled-v3-full.sql` | Security observations | ✅ |
| `005_security_map_views.sql` | Security MVs | ✅ |
| `006_skill_gap_views.sql` | Talent MVs | ✅ |
| `007_capital_map_views.sql` | Capital view (old) | ✅ |
| `008_capital_analytics.sql` | Capital MV | ✅ |
| `009_talent_enterprise.sql` | Talent Enterprise | ✅ |
| `010_security_enterprise.sql` | Security Enterprise | ✅ |
| `011_opportunity_index.sql` | Opportunity Composite | ✅ |
| `012_new_domains_scaffold.sql` | 5 New Domains | ✅ |

## Recommendations

1. **Populate Conference Gravity**: Use `tech_conferences` table to create conference density by country
2. **Tool Demand Map**: Combine `developer_tools` signals with `jobs` skill mentions
3. **Research Velocity**: Use `openalex_papers` growth rates by country
4. **Industry Signals**: Create sector-level map using `industry_signals` data

## Generated At
2026-01-18T16:50:00Z
