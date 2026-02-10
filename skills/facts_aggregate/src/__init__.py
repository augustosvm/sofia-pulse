#!/usr/bin/env python3
"""
Sofia Skills Kit - facts.aggregate
Aggregates normalized data into fact tables for analytics.
"""

import json
import time
from pathlib import Path
from datetime import datetime
import psycopg2
import psycopg2.extras


def load_registry():
    """Load normalization registry config (includes aggregations)."""
    registry_path = Path(__file__).resolve().parents[3] / "config" / "normalization_registry.json"
    
    if not registry_path.exists():
        raise FileNotFoundError(f"Normalization registry not found: {registry_path}")
    
    with open(registry_path, "r") as f:
        return json.load(f)


def build_aggregation_query(agg_config, mode, since=None, until=None):
    """Build SQL query for aggregation."""
    source_table = agg_config["source_table"]
    target_table = agg_config["target_table"]
    grain = agg_config["grain"]
    metrics = agg_config["metrics"]
    filters = agg_config.get("filters", "TRUE")
    update_strategy = agg_config.get("update_strategy", "replace")

    # Handle grain as dict (with expressions) or list (column names)
    if isinstance(grain, dict):
        grain_names = list(grain.keys())
        grain_expressions = [f"{expr} AS {name}" for name, expr in grain.items()]
        grain_select_clause = ", ".join(grain_expressions)
        grain_group_by_clause = ", ".join([grain[name] for name in grain_names])
        grain_insert_clause = ", ".join(grain_names)
    else:
        # Legacy: grain is a list of column names
        grain_names = grain
        grain_select_clause = ", ".join(grain)
        grain_group_by_clause = ", ".join(grain)
        grain_insert_clause = ", ".join(grain)

    metrics_clause = ",\n    ".join([f"{expr} AS {name}" for name, expr in metrics.items()])
    
    # Build WHERE clause based on mode
    where_conditions = [filters]

    if mode == "incremental":
        # Only aggregate new data
        grain_conditions = ' AND '.join([f't.{g} = {source_table}.{g}' if isinstance(grain, list) else f't.{g} = {grain[g]}' for g in grain_names])
        where_conditions.append(f"""
            NOT EXISTS (
                SELECT 1 FROM {target_table} t
                WHERE {grain_conditions}
            )
        """)

    elif mode == "date_range":
        date_grain_names = [g for g in grain_names if 'date' in g.lower() or 'year' in g.lower() or 'month' in g.lower()]
        if since and date_grain_names:
            where_conditions.append(f"{date_grain_names[0]} >= '{since}'::date")
        if until and date_grain_names:
            where_conditions.append(f"{date_grain_names[0]} < '{until}'::date + interval '1 day'")

    where_clause = " AND ".join([f"({c})" for c in where_conditions if c and c != "TRUE"])

    # Build final query based on update strategy
    if update_strategy == "replace":
        # Delete existing records for the grain period, then insert new
        delete_query = None
        if mode == "date_range" and since and until:
            date_grain_names = [g for g in grain_names if 'date' in g.lower() or 'year' in g.lower() or 'month' in g.lower()]
            if date_grain_names:
                delete_query = f"""
                DELETE FROM {target_table}
                WHERE {date_grain_names[0]} >= '{since}'::date
                  AND {date_grain_names[0]} < '{until}'::date + interval '1 day';
                """
        elif mode == "full":
            delete_query = f"TRUNCATE TABLE {target_table};"

        insert_query = f"""
        INSERT INTO {target_table} (
          {grain_insert_clause},
          {', '.join(metrics.keys())},
          created_at
        )
        SELECT
          {grain_select_clause},
          {metrics_clause},
          NOW() as created_at
        FROM {source_table}
        WHERE {where_clause or 'TRUE'}
        GROUP BY {grain_group_by_clause};
        """

        return (delete_query, insert_query) if delete_query else (None, insert_query)

    else:  # upsert or append
        # Use INSERT ... ON CONFLICT for upsert
        insert_query = f"""
        INSERT INTO {target_table} (
          {grain_insert_clause},
          {', '.join(metrics.keys())},
          created_at,
          updated_at
        )
        SELECT
          {grain_select_clause},
          {metrics_clause},
          NOW() as created_at,
          NOW() as updated_at
        FROM {source_table}
        WHERE {where_clause or 'TRUE'}
        GROUP BY {grain_group_by_clause}
        ON CONFLICT ({grain_insert_clause})
        DO UPDATE SET
          {', '.join([f'{name} = EXCLUDED.{name}' for name in metrics.keys()])},
          updated_at = NOW();
        """

        return (None, insert_query)


def execute(trace_id, actor, dry_run, params, context):
    """Execute facts aggregation."""
    start_time = time.time()
    
    # Extract parameters
    aggregation = params.get("aggregation")
    mode = params.get("mode", "incremental")
    since = params.get("since")
    until = params.get("until")
    dry_run_param = params.get("dry_run", False)
    
    # Validate parameters
    if not aggregation:
        return {
            "ok": False,
            "errors": [{
                "code": "PARAM_MISSING",
                "message": "Parameter 'aggregation' is required",
                "field": "aggregation"
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
    
    # Get aggregation config
    agg_config = registry.get("aggregations", {}).get(aggregation)
    
    if not agg_config:
        available_aggs = list(registry.get("aggregations", {}).keys())
        return {
            "ok": False,
            "errors": [{
                "code": "AGGREGATION_NOT_FOUND",
                "message": f"Aggregation '{aggregation}' not found in registry. Available: {available_aggs}",
                "field": "aggregation"
            }]
        }
    
    if not agg_config.get("enabled", False):
        return {
            "ok": False,
            "errors": [{
                "code": "AGGREGATION_DISABLED",
                "message": f"Aggregation '{aggregation}' is disabled in registry",
                "field": "aggregation"
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
    
    # Build and execute aggregation
    queries_executed = []
    total_records = 0
    grain_count = 0
    
    try:
        delete_query, insert_query = build_aggregation_query(agg_config, mode, since, until)
        
        if dry_run or dry_run_param:
            # Dry run: just show queries
            if delete_query:
                queries_executed.append({"type": "delete", "query": delete_query})
            queries_executed.append({"type": "insert", "query": insert_query})
        else:
            # Execute delete if exists
            if delete_query:
                cur.execute(delete_query)
                queries_executed.append({"type": "delete", "rows_affected": cur.rowcount})
            
            # Execute insert/upsert
            cur.execute(insert_query)
            total_records = cur.rowcount
            queries_executed.append({"type": "insert", "rows_affected": total_records})
            
            # Count unique grain combinations
            grain_config = agg_config["grain"]
            if isinstance(grain_config, dict):
                grain_names = list(grain_config.keys())
            else:
                grain_names = grain_config
            grain_columns = ", ".join(grain_names)
            count_query = f"SELECT COUNT(*) AS count FROM {agg_config['target_table']}"
            cur.execute(count_query)
            grain_result = cur.fetchone()
            grain_count = grain_result["count"] if grain_result else 0
            
            # Commit
            conn.commit()
        
    except Exception as e:
        conn.rollback()
        return {
            "ok": False,
            "errors": [{
                "code": "AGGREGATION_ERROR",
                "message": f"Error during aggregation: {e}",
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
            "aggregation": aggregation,
            "mode": mode,
            "total_records": total_records,
            "grain_count": grain_count,
            "duration_ms": duration_ms,
            "dry_run": dry_run or dry_run_param,
            "queries": queries_executed if (dry_run or dry_run_param) else []
        },
        "meta": {
            "skill": "facts.aggregate",
            "version": "1.0.0",
            "trace_id": trace_id,
            "duration_ms": duration_ms
        }
    }
