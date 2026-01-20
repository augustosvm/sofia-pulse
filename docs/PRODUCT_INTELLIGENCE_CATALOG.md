# Sofia Pulse - Product Intelligence Catalog

## Executive Summary
This catalog documents the intelligence features available in Sofia Pulse, what data sources power them, and how they appear on maps.

---

## TIER 1: CORE INTELLIGENCE (LIVE)

### 1. Capital Flow Intelligence
**What it measures**: Investment velocity, deal concentration, and market maturity by country.

| Metric | Formula | Source |
|--------|---------|--------|
| Volume 12m | `SUM(amount_usd)` | funding_rounds |
| Momentum | `(vol_6m - vol_prev_6m) / vol_prev_6m` | funding_rounds |
| Stage Proxy | `CASE avg_ticket > 50M THEN late...` | funding_rounds |
| Sector Concentration | `1 - top_sector_share` | funding_rounds |

**Map Appearance**: Choropleth green→orange by flow_type tier
**Confidence**: Based on deal count + recency + data completeness

---

### 2. Talent Gap Intelligence
**What it measures**: Skill demand (jobs) vs supply (research papers) by country.

| Metric | Formula | Source |
|--------|---------|--------|
| Demand % | `job_mentions / total_jobs * 100` | jobs |
| Supply % | `paper_mentions / total_papers * 100` | research_papers |
| Gap Score | `demand_pct - supply_pct` | derived |
| Gap Type | market_hungry / academia_ahead / aligned | derived |

**Map Appearance**: Choropleth red (hungry) → blue (academia ahead) → green (aligned)
**Confidence**: Based on job volume + paper volume

---

### 3. Security Risk Intelligence
**What it measures**: Geopolitical instability, conflict severity, and stress trends.

| Metric | Formula | Source |
|--------|---------|--------|
| Acute Risk | `severity_weighted_events_30d` | security_observations (ACLED) |
| Structural Risk | governance index (if available) | external (placeholder) |
| Stress Index | `events_30d / (events_180d/6)` | security_observations |
| Spillover Risk | `0.7*own + 0.3*neighbor_avg` | derived (scaffold) |

**Map Appearance**: Choropleth red intensity by risk level
**Confidence**: Based on source diversity + recency

---

### 4. Opportunity Composite Index
**What it measures**: Overall country attractiveness combining Capital + Talent - Security.

| Metric | Formula | Source |
|--------|---------|--------|
| Opportunity Score | `0.4*capital + 0.35*talent + 0.25*(100-security)` | composite MVs |
| Tier | prime / emerging / watch / avoid | derived |

**Map Appearance**: Gradient from blue (prime) to gray (avoid)
**Confidence**: Minimum of component confidences

---

## TIER 2: ADVANCED INTELLIGENCE (LIVE)

### 5. Brain Drain Index
**What it measures**: Net talent export/import by comparing research production vs job absorption.

| Metric | Formula | Source |
|--------|---------|--------|
| Papers Produced | `COUNT(papers) by author_country` | research_papers |
| Jobs Available | `COUNT(jobs) by country` | jobs |
| Brain Drain Index | `(papers - jobs) / papers * 100` | derived |
| Tier | talent_exporter / talent_importer / balanced | derived |

**Map Appearance**: Purple (exporter) → Green (importer)
**Confidence**: Based on paper + job volume

---

### 6. AI Capability Density
**What it measures**: Country's positioning in AI research and hiring.

| Metric | Formula | Source |
|--------|---------|--------|
| AI Papers | `COUNT(papers) WHERE topic LIKE '%AI%'` | research_papers |
| AI Jobs | `COUNT(jobs) WHERE title LIKE '%AI%'` | jobs |
| AI Density Score | `(papers*2 + jobs)` normalized | derived |
| Tier | ai_leader / ai_active / ai_emerging / ai_nascent | derived |

**Map Appearance**: Cyan gradient by density
**Confidence**: Based on AI paper + job counts

---

## TIER 3: EXPANSION CANDIDATES (PROPOSED)

### 7. Conference Gravity Index
**Status**: 🔄 Needs Implementation
**Collector**: `tech-conferences-collector.ts`
**Base Table**: `sofia.tech_conferences`

| Metric | Formula | Source |
|--------|---------|--------|
| Conference Count | `COUNT(conferences) by country` | tech_conferences |
| Tier Distribution | Major (attendees>5k) vs Minor | tech_conferences |
| Seasonality Score | variance across months | tech_conferences |

**Map Appearance**: Nodes sized by conference count
**Why Enterprises Care**: Indicates innovation ecosystem density

---

### 8. Developer Tool Demand Index
**Status**: 🔄 Needs Implementation
**Collectors**: `developer-tools-collector.ts` + `jobs-collector.ts`
**Base Tables**: `developer_tools` + `jobs`

| Metric | Formula | Source |
|--------|---------|--------|
| Tool Mentions in Jobs | `COUNT(jobs) WHERE description LIKE '%toolname%'` | jobs |
| Rising Tools | momentum by tool | derived |
| Stack Concentration | HHI of tool mentions | derived |

**Map Appearance**: Choropleth by tech stack modernity
**Why Enterprises Care**: Hiring friction prediction

---

### 9. Research Velocity Index
**Status**: 🔄 Needs Implementation
**Collector**: `research-papers-collector.ts`
**Base Table**: `sofia.research_papers`

| Metric | Formula | Source |
|--------|---------|--------|
| Papers 12m | `COUNT(papers)` | research_papers |
| Momentum | `papers_6m / papers_prev_6m` | research_papers |
| Frontier Score | % papers in emerging topics | research_papers |

**Map Appearance**: Blue gradient by velocity
**Why Enterprises Care**: Predicts future innovation capacity

---

### 10. Open Source Execution Capacity
**Status**: 🔄 Needs Implementation  
**Collector**: `developer-tools-collector.ts` (GitHub data)
**Base Table**: `developer_tools`

| Metric | Formula | Source |
|--------|---------|--------|
| Contributors by Country | proxy from commit locations | github_activity |
| Stars Received | aggregated by country | developer_tools |
| OSS Activity Score | normalized composite | derived |

**Map Appearance**: Green gradient
**Why Enterprises Care**: Engineering talent execution proof

---

### 11. Industry Signals Heat
**Status**: 🔄 Needs Implementation
**Collector**: `industry-signals-collector.ts`
**Base Table**: `sofia.industry_signals`

| Metric | Formula | Source |
|--------|---------|--------|
| Signals by Sector | COUNT by sector + country | industry_signals |
| Volatility | variance of signal types | industry_signals |
| Momentum | trend direction | industry_signals |

**Map Appearance**: Sector-filterable heatmap
**Why Enterprises Care**: Early warning for sector disruptions

---

### 12. Cyber Leak Pressure Index
**Status**: ⚠️ Needs New Collector
**Proposed Source**: HaveIBeenPwned / GitGuardian public data

| Metric | Formula | Source |
|--------|---------|--------|
| Leaks by Domain | COUNT by TLD → country | external |
| Severity Score | weighted by breach size | external |

**Map Appearance**: Red gradient
**Why Enterprises Care**: Security posture assessment

---

## Implementation Priority

| Feature | Data Ready | Description |
|---------|------------|-------------|
| Conference Gravity | ✅ | Medium |
| Research Velocity | ✅ | High |
| Developer Tool Demand | ✅ | High |
| Industry Signals Heat | ✅ Live | Emerging business activity clusters |
| Cyber Risk Density | ✅ Live | Cyber threat concentration map |
| Clinical Trials Activity | ✅ Live | Pharma R&D hubs and innovation |

## Recommended Next Sprint
1. **Research Velocity Index** - Easy win, high value
2. **Conference Gravity Index** - Differentiator for PE/VC
3. **Developer Tool Demand** - Unique cross-domain insight

---

*Document Version: 1.0*
*Generated: 2026-01-18*
