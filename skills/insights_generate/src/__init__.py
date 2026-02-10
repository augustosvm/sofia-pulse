#!/usr/bin/env python3
"""
Sofia Skills Kit - insights.generate
Generates real insights from normalized and aggregated data.
HOTFIX 8.0a: Watermark persistence, zero logging, domains config
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import psycopg2
import psycopg2.extras


def load_domains_config():
    """Load insights domains configuration."""
    config_path = Path(__file__).resolve().parents[3] / "config" / "insights_domains.json"

    if not config_path.exists():
        # Fallback to default
        return {"enabled_domains": ["research"], "domains": {"research": {"enabled": True, "best_effort": False}}}

    with open(config_path, "r") as f:
        return json.load(f)


def get_watermark(cur, skill_name, domain, detector=None):
    """Get watermark from sofia.skill_state.

    Args:
        skill_name: Name of the skill
        domain: Domain (research, tech, etc)
        detector: Detector name (e.g., 'org_growth_spike') or None for domain-level watermark

    Returns:
        datetime or None
    """
    cur.execute("""
        SELECT last_processed_at
        FROM sofia.skill_state
        WHERE skill_name = %s AND domain = %s AND detector IS NOT DISTINCT FROM %s
    """, (skill_name, domain, detector))

    row = cur.fetchone()
    return row['last_processed_at'] if row else None


def update_watermark(cur, skill_name, domain, watermark, detector=None):
    """Update watermark in sofia.skill_state.

    Args:
        skill_name: Name of the skill
        domain: Domain (research, tech, etc)
        watermark: Timestamp to set as last_processed_at
        detector: Detector name or None for domain-level watermark
    """
    cur.execute("""
        INSERT INTO sofia.skill_state (skill_name, domain, detector, last_processed_at, updated_at)
        VALUES (%s, %s, %s, %s, NOW())
        ON CONFLICT (skill_name, domain, detector)
        DO UPDATE SET last_processed_at = EXCLUDED.last_processed_at, updated_at = NOW()
    """, (skill_name, domain, detector, watermark))


def generate_evidence_hash(evidence):
    """Generate SHA256 hash of evidence for deduplication."""
    evidence_str = json.dumps(evidence, sort_keys=True)
    return hashlib.sha256(evidence_str.encode()).hexdigest()


def generate_status_insight(cur, domain, since=None):
    """
    Generate fallback 'Heartbeat' insight when no anomalies detected.
    Ensures site always has fresh content, deduped by week to avoid spam.
    """
    if domain == "research":
        # Count recent papers
        cur.execute("""
            SELECT
                COUNT(*) as total_papers,
                COUNT(DISTINCT source) as sources,
                MAX(publication_date) as latest_date,
                TO_CHAR(CURRENT_DATE, 'IYYY-IW') as week_key
            FROM sofia.research_papers
            WHERE publication_date >= NOW() - INTERVAL '7 days'
              AND (%(since)s IS NULL OR created_at > %(since)s)
        """, {"since": since})

        row = cur.fetchone()
        if row and row['total_papers'] > 0:
            return {
                "title": f"Research Status: {row['total_papers']} papers esta semana",
                "summary": f"Sofia indexou {row['total_papers']} papers de {row['sources']} fontes nos últimos 7 dias. Última publicação: {row['latest_date']:%Y-%m-%d}. Nenhuma anomalia detectada no período.",
                "severity": "info",
                "evidence": {
                    "total_papers": row['total_papers'],
                    "sources": row['sources'],
                    "latest_date": str(row['latest_date']),
                    "period_days": 7,
                    "week_key": row['week_key']  # Dedupe by week (e.g., "2025-W50")
                },
                "insight_type": "heartbeat"  # Changed from "daily_status" to "heartbeat"
            }

    return None


def detect_research_insights(cur, since=None):
    """
    Detect insights from research domain.
    Returns: [(title, summary, severity, evidence), ...]
    """
    insights = []

    # Insight 1: Sudden growth in publications by organization
    cur.execute("""
        WITH recent_papers AS (
            SELECT
                o.organization_name,
                COUNT(*) as paper_count,
                MAX(p.publication_date) as latest_paper
            FROM sofia.research_papers p
            JOIN sofia.paper_organizations po ON po.paper_id = p.id
            JOIN sofia.organizations o ON o.organization_id = po.organization_id
            WHERE p.publication_date >= NOW() - INTERVAL '30 days'
              AND (%(since)s IS NULL OR p.created_at > %(since)s)
            GROUP BY o.organization_name
            HAVING COUNT(*) >= 2
        ),
        historical_avg AS (
            SELECT
                o.organization_name,
                COUNT(*) / 12.0 as monthly_avg
            FROM sofia.research_papers p
            JOIN sofia.paper_organizations po ON po.paper_id = p.id
            JOIN sofia.organizations o ON o.organization_id = po.organization_id
            WHERE p.publication_date >= NOW() - INTERVAL '12 months'
              AND p.publication_date < NOW() - INTERVAL '30 days'
            GROUP BY o.organization_name
        )
        SELECT
            r.organization_name,
            r.paper_count,
            COALESCE(h.monthly_avg, 0) as historical_avg,
            r.paper_count / NULLIF(COALESCE(h.monthly_avg, 0), 0) as growth_factor
        FROM recent_papers r
        LEFT JOIN historical_avg h ON h.organization_name = r.organization_name
        WHERE r.paper_count > COALESCE(h.monthly_avg, 0) * 2
        ORDER BY growth_factor DESC
        LIMIT 5
    """, {"since": since})

    for row in cur.fetchall():
        insights.append({
            "title": f"Crescimento Anormal: {row['organization_name']}",
            "summary": f"A organização {row['organization_name']} publicou {row['paper_count']} papers nos últimos 30 dias, {row['growth_factor']:.1f}x acima da média histórica ({row['historical_avg']:.1f} papers/mês).",
            "severity": "warning" if row['growth_factor'] > 3 else "info",
            "evidence": {
                "organization": row['organization_name'],
                "recent_papers": row['paper_count'],
                "historical_avg": float(row['historical_avg']),
                "growth_factor": float(row['growth_factor'])
            },
            "insight_type": "growth_spike_organization"
        })

    # Insight 2: Breakthrough papers concentration
    cur.execute("""
        SELECT
            source,
            COUNT(*) as breakthrough_count,
            COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0) as percentage
        FROM sofia.research_papers
        WHERE is_breakthrough = true
          AND publication_date >= NOW() - INTERVAL '90 days'
          AND (%(since)s IS NULL OR created_at > %(since)s)
        GROUP BY source
        HAVING COUNT(*) >= 2
        ORDER BY breakthrough_count DESC
    """, {"since": since})

    for row in cur.fetchall():
        if row['breakthrough_count'] >= 3:
            insights.append({
                "title": f"Concentração de Breakthroughs: {row['source'].upper()}",
                "summary": f"Fonte {row['source'].upper()} concentra {row['breakthrough_count']} papers marcados como breakthrough nos últimos 90 dias ({row['percentage']:.1f}% do total).",
                "severity": "info",
                "evidence": {
                    "source": row['source'],
                    "breakthrough_count": row['breakthrough_count'],
                    "percentage": float(row['percentage'])
                },
                "insight_type": "breakthrough_concentration"
            })

    return insights


def detect_aggregation_insights(cur, since=None):
    """
    Detect insights from aggregated facts tables.
    Returns: [(title, summary, severity, evidence), ...]
    """
    insights = []

    # Insight: Month-over-month growth in research_monthly
    cur.execute("""
        WITH monthly_totals AS (
            SELECT
                source,
                publication_year,
                publication_month,
                total_papers,
                LAG(total_papers) OVER (
                    PARTITION BY source
                    ORDER BY publication_year, publication_month
                ) as prev_month_papers
            FROM sofia.facts_research_monthly
            WHERE (publication_year * 100 + publication_month) >=
                  EXTRACT(YEAR FROM NOW() - INTERVAL '6 months')::int * 100 +
                  EXTRACT(MONTH FROM NOW() - INTERVAL '6 months')::int
        )
        SELECT
            source,
            publication_year,
            publication_month,
            total_papers,
            prev_month_papers,
            (total_papers - prev_month_papers) * 100.0 / NULLIF(prev_month_papers, 0) as growth_pct
        FROM monthly_totals
        WHERE prev_month_papers IS NOT NULL
          AND total_papers > prev_month_papers * 1.5
        ORDER BY growth_pct DESC
        LIMIT 3
    """)

    for row in cur.fetchall():
        insights.append({
            "title": f"Crescimento Mensal: {row['source'].upper()}",
            "summary": f"Fonte {row['source'].upper()} teve crescimento de {row['growth_pct']:.0f}% em {row['publication_year']}-{row['publication_month']:02d} ({row['total_papers']} papers vs {row['prev_month_papers']} no mês anterior).",
            "severity": "warning" if row['growth_pct'] > 100 else "info",
            "evidence": {
                "source": row['source'],
                "year": row['publication_year'],
                "month": row['publication_month'],
                "current_papers": row['total_papers'],
                "previous_papers": row['prev_month_papers'],
                "growth_pct": float(row['growth_pct'])
            },
            "insight_type": "monthly_growth"
        })

    return insights


def execute(trace_id, actor, dry_run, params, context):
    """Execute insights generation."""
    start_time = time.time()

    # Load domains config
    domains_config = load_domains_config()

    # Extract parameters
    domains = params.get("domains", domains_config.get("enabled_domains", ["research"]))
    since = params.get("since")  # Watermark from params (optional, overrides DB)
    dry_run_param = params.get("dry_run", False)

    # Connect to database
    import os
    db_url = os.environ.get("DATABASE_URL")

    if not db_url:
        return {
            "ok": False,
            "errors": [{
                "code": "DB_CONFIG_MISSING",
                "message": "DATABASE_URL environment variable not set",
                "retryable": False
            }]
        }

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    except Exception as e:
        return {
            "ok": False,
            "errors": [{
                "code": "DB_CONNECTION_ERROR",
                "message": f"Failed to connect to database: {e}",
                "retryable": True
            }]
        }

    # Generate insights per domain
    all_insights = []
    by_domain = {}
    by_severity = {"info": 0, "warning": 0, "critical": 0}
    watermarks = {}

    try:
        for domain in domains:
            domain_config = domains_config.get("domains", {}).get(domain, {})
            best_effort = domain_config.get("best_effort", False)

            # Get watermark from DB (if not provided in params)
            since_dt = None
            if since:
                try:
                    since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                except:
                    since_dt = None
            else:
                # Get from DB
                db_watermark = get_watermark(cur, "insights.generate", domain)
                since_dt = db_watermark

            domain_insights = []

            try:
                if domain == "research":
                    # Detect from research_papers
                    domain_insights.extend(detect_research_insights(cur, since_dt))
                    # Detect from facts_research_monthly
                    domain_insights.extend(detect_aggregation_insights(cur, since_dt))

                # Add domain and detector_name to each insight
                for insight in domain_insights:
                    insight["domain"] = domain
                    if "insight_type" not in insight:
                        insight["insight_type"] = "anomaly"
                    # detector_name is the insight_type (e.g., 'growth_spike_organization')
                    insight["detector_name"] = insight["insight_type"]
                    all_insights.append(insight)

                by_domain[domain] = len(domain_insights)

                # Track watermark for this domain (general)
                watermarks[domain] = datetime.utcnow()

            except Exception as e:
                if not best_effort:
                    raise  # Fail if domain is critical
                else:
                    print(f"  [insights.generate] Warning: {domain} failed (best-effort): {e}")
                    by_domain[domain] = 0

        # Log zero insights event
        if not all_insights:
            print(f"  [insights.generate] Zero insights generated")

            # Log structured event
            try:
                from lib.skill_runner import run
                run("logger.event", {
                    "level": "info",
                    "event": "insights.generate.zero",
                    "skill": "insights.generate",
                    "domains": domains,
                    "since": str(since_dt) if since_dt else None,
                    "reason": "no_anomalies_detected"
                }, trace_id=trace_id)
            except:
                pass  # Best-effort logging

            # Generate status fallback insights
            if domains_config.get("global_settings", {}).get("generate_status_fallback", False):
                for domain in domains:
                    status_insight = generate_status_insight(cur, domain, since_dt)
                    if status_insight:
                        status_insight["domain"] = domain
                        all_insights.append(status_insight)
                        by_domain[domain] = by_domain.get(domain, 0) + 1
                        print(f"  [insights.generate] Generated status fallback for {domain}")

        # Save insights to database (if not dry run)
        if not dry_run and not dry_run_param and all_insights:
            for insight in all_insights:
                evidence_hash = generate_evidence_hash(insight["evidence"])

                try:
                    cur.execute("""
                        INSERT INTO sofia.insights (
                            domain, insight_type, title, summary, severity,
                            evidence, trace_id, watermark, evidence_hash
                        )
                        VALUES (
                            %(domain)s, %(insight_type)s, %(title)s, %(summary)s, %(severity)s,
                            %(evidence)s, %(trace_id)s, NOW(), %(evidence_hash)s
                        )
                        ON CONFLICT (evidence_hash) DO NOTHING
                    """, {
                        "domain": insight["domain"],
                        "insight_type": insight["insight_type"],
                        "title": insight["title"],
                        "summary": insight["summary"],
                        "severity": insight["severity"],
                        "evidence": json.dumps(insight["evidence"]),
                        "trace_id": trace_id,
                        "evidence_hash": evidence_hash
                    })

                    if cur.rowcount > 0:
                        by_severity[insight["severity"]] += 1

                except psycopg2.IntegrityError:
                    # Duplicate (evidence_hash already exists)
                    pass

            # Update watermarks (domain-level + detector-level)
            for domain, watermark in watermarks.items():
                # Update domain-level watermark (global for domain)
                update_watermark(cur, "insights.generate", domain, watermark, detector=None)

                # Update detector-level watermarks (specific for each detector)
                domain_detectors = set()
                for insight in all_insights:
                    if insight.get("domain") == domain and "detector_name" in insight:
                        domain_detectors.add(insight["detector_name"])

                for detector in domain_detectors:
                    update_watermark(cur, "insights.generate", domain, watermark, detector=detector)

            conn.commit()

        # Calculate new watermark
        new_watermark = datetime.utcnow().isoformat() + "Z"

    except Exception as e:
        conn.rollback()
        return {
            "ok": False,
            "errors": [{
                "code": "INSIGHTS_GENERATION_ERROR",
                "message": f"Error generating insights: {e}",
                "retryable": True
            }]
        }
    finally:
        cur.close()
        conn.close()

    # Calculate duration
    duration_ms = int((time.time() - start_time) * 1000)

    # Return success
    return {
        "ok": True,
        "data": {
            "insights_generated": len(all_insights),
            "by_domain": by_domain,
            "by_severity": by_severity,
            "watermark": new_watermark,
            "duration_ms": duration_ms,
            "dry_run": dry_run or dry_run_param,
            "insights_preview": all_insights[:3] if (dry_run or dry_run_param) else []
        },
        "meta": {
            "skill": "insights.generate",
            "version": "1.0a",
            "trace_id": trace_id,
            "duration_ms": duration_ms
        }
    }
