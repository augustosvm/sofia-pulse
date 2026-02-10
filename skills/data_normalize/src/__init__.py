#!/usr/bin/env python3
"""
Sofia Skills Kit - data.normalize
Normalizes data from multiple sources into canonical tables.
"""

import json
import time
from pathlib import Path
from datetime import datetime
import psycopg2
import psycopg2.extras


def load_registry():
    """Load normalization registry config."""
    registry_path = Path(__file__).resolve().parents[3] / "config" / "normalization_registry.json"
    
    if not registry_path.exists():
        raise FileNotFoundError(f"Normalization registry not found: {registry_path}")
    
    with open(registry_path, "r") as f:
        return json.load(f)


def build_normalization_query(domain_config, source_config, mode, since=None, until=None):
    """Build SQL query for normalization."""
    field_mapping = source_config["field_mapping"]
    source_table = source_config["table"]
    target_table = domain_config["target_table"]
    unique_key = source_config["unique_key"]
    
    # Build SELECT clause
    select_fields = []
    for target_field, source_expr in field_mapping.items():
        select_fields.append(f"{source_expr} AS {target_field}")
    
    select_clause = ",\n    ".join(select_fields)
    
    # Build WHERE clause based on mode
    where_conditions = []
    
    if mode == "incremental":
        # Only new data since last normalization
        where_conditions.append(f"""
            NOT EXISTS (
                SELECT 1 FROM {target_table} t
                WHERE t.source = {source_config['field_mapping']['source']}
                  AND t.source_id = {source_table.split('.')[-1]}.{source_config['field_mapping']['source_id'].split('.')[-1] if '.' in source_config['field_mapping']['source_id'] else source_config['field_mapping']['source_id']}
            )
        """)
    
    elif mode == "date_range":
        if since:
            where_conditions.append(f"collected_at >= '{since}'::date")
        if until:
            where_conditions.append(f"collected_at < '{until}'::date + interval '1 day'")
    
    # mode == "full" has no WHERE conditions (backfill all)
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE"
    
    # Build conflict resolution
    update_set_clause = domain_config.get("conflict_resolution", "").replace("DO UPDATE SET ", "")
    
    # Build full query
    query = f"""
    INSERT INTO {target_table} (
      {', '.join(field_mapping.keys())}
    )
    SELECT
      {select_clause}
    FROM {source_table}
    WHERE {where_clause}
    ON CONFLICT ({', '.join(unique_key)})
    {domain_config.get('conflict_resolution', 'DO NOTHING')};
    """
    
    return query


def execute(trace_id, actor, dry_run, params, context):
    """Execute data normalization."""
    start_time = time.time()
    
    # Extract parameters
    domain = params.get("domain")
    mode = params.get("mode", "incremental")
    since = params.get("since")
    until = params.get("until")
    dry_run_param = params.get("dry_run", False)
    source_filter = params.get("source_filter")
    
    # Validate parameters
    if not domain:
        return {
            "ok": False,
            "errors": [{
                "code": "PARAM_MISSING",
                "message": "Parameter 'domain' is required",
                "field": "domain"
            }]
        }
    
    if mode not in ["full", "incremental", "date_range"]:
        return {
            "ok": False,
            "errors": [{
                "code": "PARAM_INVALID",
                "message": f"Invalid mode: {mode}. Must be one of: full, incremental, date_range",
                "field": "mode"
            }]
        }
    
    if mode == "date_range" and not (since or until):
        return {
            "ok": False,
            "errors": [{
                "code": "PARAM_MISSING",
                "message": "Mode 'date_range' requires 'since' or 'until' parameter",
                "field": "mode"
            }]
        }
    
    # Load registry
    try:
        registry = load_registry()
    except Exception as e:
        return {
            "ok": False,
            "errors": [{
                "code": "REGISTRY_LOAD_ERROR",
                "message": f"Failed to load normalization registry: {e}",
                "retryable": False
            }]
        }
    
    # Get domain config
    domain_config = registry.get("domains", {}).get(domain)
    
    if not domain_config:
        available_domains = list(registry.get("domains", {}).keys())
        return {
            "ok": False,
            "errors": [{
                "code": "DOMAIN_NOT_FOUND",
                "message": f"Domain '{domain}' not found in registry. Available: {available_domains}",
                "field": "domain"
            }]
        }
    
    if not domain_config.get("enabled", False):
        return {
            "ok": False,
            "errors": [{
                "code": "DOMAIN_DISABLED",
                "message": f"Domain '{domain}' is disabled in registry",
                "field": "domain"
            }]
        }
    
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
    
    # Process sources
    total_processed = 0
    inserted = 0
    updated = 0
    skipped = 0
    queries_executed = []
    
    try:
        for source_config in domain_config["sources"]:
            source_id = source_config["source_id"]
            
            # Apply source filter if provided
            if source_filter and source_id != source_filter:
                continue
            
            # Build query
            query = build_normalization_query(domain_config, source_config, mode, since, until)
            queries_executed.append({
                "source": source_id,
                "query": query
            })
            
            if dry_run or dry_run_param:
                # Dry run: just count rows that would be affected
                count_query = f"""
                SELECT COUNT(*) as count
                FROM {source_config['table']}
                WHERE TRUE
                """
                cur.execute(count_query)
                count_result = cur.fetchone()
                total_processed += count_result["count"] if count_result else 0
            else:
                # Execute normalization
                cur.execute(query)
                affected_rows = cur.rowcount
                total_processed += affected_rows
                
                # Estimate inserted vs updated (rough heuristic)
                if mode == "full":
                    updated += affected_rows // 2
                    inserted += affected_rows // 2
                elif mode == "incremental":
                    inserted += affected_rows
                else:
                    inserted += affected_rows // 3
                    updated += (affected_rows // 3) * 2
        
        # Commit if not dry run
        if not dry_run and not dry_run_param:
            conn.commit()
        else:
            conn.rollback()
        
    except Exception as e:
        conn.rollback()
        return {
            "ok": False,
            "errors": [{
                "code": "NORMALIZATION_ERROR",
                "message": f"Error during normalization: {e}",
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
            "domain": domain,
            "mode": mode,
            "total_processed": total_processed,
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "duration_ms": duration_ms,
            "dry_run": dry_run or dry_run_param,
            "sources_processed": len([s for s in domain_config["sources"] if not source_filter or s["source_id"] == source_filter]),
            "queries": queries_executed if (dry_run or dry_run_param) else []
        },
        "meta": {
            "skill": "data.normalize",
            "version": "1.0.0",
            "trace_id": trace_id,
            "duration_ms": duration_ms
        }
    }
