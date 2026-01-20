-- ============================================================================
-- Refresh Materialized Views (Dependencies in Order)
-- Run after migrations and backfill scripts
-- ============================================================================

-- Core domains (no dependencies)
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_capital_analytics;
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_security_country_combined;

-- Talent (depends on jobs + papers)
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_skill_gap_country_summary;

-- Composite indexes (depend on core)
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_opportunity_by_country;
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_brain_drain_by_country;
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_ai_capability_density_by_country;

-- Phase 2: Intelligence Expansion (depend on mapping tables)
-- IMPORTANT: Run backfill scripts FIRST before refreshing these
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_industry_signals_heat_by_country;
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_cyber_risk_by_country;
REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_clinical_trials_by_country;

-- Scaffolds (if they exist)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_research_velocity_by_country;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_tool_demand_by_country;
