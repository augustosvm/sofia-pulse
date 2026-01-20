# Sofia Pulse - Intelligence Maps Implementation Guide
> Technical reference for implemented Materialized Views and APIs.

## 1. Architecture Overview
- **Source of Truth**: PostgreSQL Materialized Views (MVs).
- **Update Frequency**: Daily/Weekly updates via crontab specific to domain.
- **Anti-Mock Policy**: All maps must handle missing data gracefully (gray fill, no_data class) without faking values.
- **Universal Schema**: All APIs return `{ iso, metrics, narrative, confidence, class }`.

---

## 2. Core Domains (Phase 1)

### 2.1 Capital Flow
- **MV**: `sofia.mv_capital_analytics`
- **Metric**: `total_vol_12m` (Total Funding Volume).
- **Confidence**: Based on deal count and recency.
- **Visuals**: Purple/Indigo scale.

### 2.2 Talent Gap
- **MV**: `sofia.mv_skill_gap_country_summary`
- **Metric**: `gap_score` (Demand minus Supply normalized).
- **Confidence**: Based on job count (demand) and paper count (supply).
- **Visuals**: Red (Deficit) to Green (Surplus) diverging scale.

### 2.3 Security Risk
- **MV**: `sofia.mv_security_country_combined`
- **Metric**: `stress_index` (Composite of fatalities + events).
- **Confidence**: High for ACLED covered regions.
- **Visuals**: Orange/Red scale.

---

## 3. Composite Indexes

### 3.1 Opportunity Index
- **MV**: `sofia.mv_opportunity_by_country`
- **Logic**: Weighted average of Capital (40%), Talent (30%), Security (30%).
- **Visuals**: Gold/Yellow scale.

---

## 4. Phase 2 Expansion (v2.4)

### 4.1 Industry Signals Heat
- **Goal**: Identify emerging business activity sectors.
- **MV**: `sofia.mv_industry_signals_heat_by_country`
- **Source**: `sofia.industry_signals` (28k rows) + Metadata Jurisdiction.
- **Metrics**: 30d/90d volume, momentum, sector diversity.
- **Confidence**: Based on volume (>500 = high) and diversity.
- **Visuals**: Green scale (Heat).

### 4.2 Cyber Risk Density
- **Goal**: Visualize cyber threat concentration.
- **MV**: `sofia.mv_cyber_risk_by_country`
- **Source**: `sofia.cybersecurity_events` (Text match on Title/Desc).
- **Metrics**: Event count, severity avg, critical events.
- **Confidence**: Low baseline (0.8 cap) due to text matching.
- **Visuals**: Red/Orange scale (Risk).

### 4.3 Clinical Trials Activity
- **Goal**: Track pharma R&D hubs.
- **MV**: `sofia.mv_clinical_trials_by_country`
- **Source**: `sofia.clinical_trials` (Sponsor Text Match).
- **Metrics**: Active trials, Phase 3 count, diversity.
- **Confidence**: Medium.
- **Visuals**: Blue scale (Science).
