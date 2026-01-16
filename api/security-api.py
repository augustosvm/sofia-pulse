#!/usr/bin/env python3
"""
Security Hybrid Model - API Endpoints v2.1
FastAPI implementation - 100% spec compliant
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import psycopg2
import psycopg2.extras
import os
from pathlib import Path
from datetime import datetime

app = FastAPI(title="Sofia Security Hybrid Model API", version="2.1")

# CORS - Fixed: wildcard + credentials is invalid
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False with wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db():
    # Try current dir first, then parent dir
    env_file = Path(".env")
    if not env_file.exists():
        env_file = Path("../.env")
    
    if env_file.exists():
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k] = v.strip()
    
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB")
    )


@app.get("/api/security/map")
async def get_security_map(
    zoom: Optional[int] = Query(None, ge=1, le=20),
    country: Optional[str] = Query(None, max_length=3),
    bbox: Optional[str] = Query(None),
    sources: Optional[str] = Query("acled,local")
):
    """
    Get security points for map display
    
    Sources:
    - ACLED (always)
    - Brasil local (only if zoom >= 8 OR country=BR)
    
    Returns: GeoJSON FeatureCollection
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Parse sources
    source_list = sources.split(',') if sources else ['acled']
    
    # Build source conditions (FIXED: proper precedence)
    source_conditions = []
    params = []
    
    # ACLED always (accept both ACLED and ACLED_AGGREGATED temporarily)
    if 'acled' in source_list:
        source_conditions.append("(source IN ('ACLED', 'ACLED_AGGREGATED') AND coverage_scope = 'global_comparable')")
    
    # Brasil local only if zoom >= 8 OR country=BR
    if 'local' in source_list:
        if (zoom and zoom >= 8) or (country and country.upper() == 'BR'):
            source_conditions.append("(source LIKE 'BRASIL_%' AND coverage_scope = 'local_only')")
    
    if not source_conditions:
        return {"type": "FeatureCollection", "features": [], "metadata": {"total_points": 0}}
    
    # FIXED: Proper WHERE precedence: ((sources OR...) AND filters)
    where_parts = [f"({' OR '.join(source_conditions)})"]
    
    # Add bbox filter with PARAMETERIZED query (FIXED: SQL injection)
    if bbox:
        try:
            w, s, e, n = map(float, bbox.split(','))
            where_parts.append("latitude BETWEEN %s AND %s")
            where_parts.append("longitude BETWEEN %s AND %s")
            params.extend([s, n, w, e])
        except:
            raise HTTPException(status_code=400, detail="Invalid bbox format. Use: w,s,e,n")
    
    # Add country filter with PARAMETERIZED query (FIXED: SQL injection)
    if country:
        where_parts.append("country_code = %s")
        params.append(country.upper())
    
    where_clause = " AND ".join(where_parts)
    
    # FIXED: Pagination by zoom level
    limit = 10000 if zoom and zoom >= 10 else 5000 if zoom and zoom >= 6 else 1000
    
    query = f"""
        SELECT 
            latitude,
            longitude,
            source,
            severity_norm,
            country_code,
            country_name,
            event_count,
            fatalities,
            coverage_score_global,
            coverage_score_local,
            coverage_scope,
            event_time_start,
            admin1,
            city
        FROM sofia.security_observations
        WHERE {where_clause}
          AND latitude IS NOT NULL
          AND longitude IS NOT NULL
        ORDER BY severity_norm DESC
        LIMIT %s
    """
    
    params.append(limit)
    cur.execute(query, params)
    
    features = []
    for row in cur.fetchall():
        # FIXED: Coverage chosen by coverage_scope, not source
        coverage = row['coverage_score_global'] if row['coverage_scope'] == 'global_comparable' else row['coverage_score_local']
        
        # Warning if coverage < 50
        warning = "Baixa cobertura — risco pode estar subestimado" if coverage < 50 else None
        
        # Brasil local always has warning
        if row['coverage_scope'] == 'local_only':
            warning = "Cobertura local detalhada. Dados não comparáveis globalmente."
        
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row['longitude']), float(row['latitude'])]
            },
            "properties": {
                "source": row['source'],
                "severity_norm": float(row['severity_norm']) if row['severity_norm'] else 0,
                "country_code": row['country_code'],
                "country_name": row['country_name'],
                "event_count": row['event_count'],
                "fatalities": row['fatalities'] or 0,
                "coverage_score": float(coverage) if coverage else 0,
                "coverage_scope": row['coverage_scope'],
                "event_date": row['event_time_start'].isoformat() if row['event_time_start'] else None,
                "admin1": row['admin1'],
                "city": row['city'],
                "warning": warning
            }
        })
    
    cur.close()
    conn.close()
    
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "total_points": len(features),
            "sources_used": source_list,
            "zoom_level": zoom,
            "limit_applied": limit
        }
    }


@app.get("/api/security/countries")
async def get_security_countries(
    sort: Optional[str] = Query("total_risk", regex="^(total_risk|acute_risk|structural_risk)$"),
    min_coverage: Optional[int] = Query(None, ge=0, le=100),
    risk_level: Optional[str] = Query(None, regex="^(Critical|High|Elevated|Moderate|Low)$")
):
    """
    Get security scores by country (hybrid model)
    
    Uses: ACLED + GDELT + World Bank
    Does NOT use: Brasil local data
    
    Returns: Country scores with breakdown
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Build WHERE conditions with PARAMETERIZED queries
    where_conditions = []
    params = []
    
    if min_coverage:
        # FIXED: Need to join with observations to get coverage
        pass  # Will handle in main query
    
    if risk_level:
        where_conditions.append("c.risk_level = %s")
        params.append(risk_level)
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    
    # FIXED: Column names are *_risk_score in view
    sort_column_map = {
        'total_risk': 'total_risk_score',
        'acute_risk': 'acute_risk_score',
        'structural_risk': 'structural_risk_score'
    }
    sort_column = sort_column_map.get(sort, 'total_risk_score')
    
    # FIXED: Single query to eliminate N+1, aggregate sources and coverage
    query = f"""
        WITH country_coverage AS (
            SELECT 
                country_code,
                MAX(coverage_score_global) as coverage_score_global,
                ARRAY_AGG(DISTINCT source ORDER BY source) as sources_used
            FROM sofia.security_observations
            WHERE coverage_scope = 'global_comparable'
              AND country_code IS NOT NULL
            GROUP BY country_code
        )
        SELECT 
            c.country_code,
            c.country_name,
            c.acute_risk_score,
            c.structural_risk_score,
            c.total_risk_score,
            c.risk_level,
            c.total_incidents,
            c.fatalities,
            c.indicators_count,
            c.as_of_date,
            COALESCE(cc.coverage_score_global, 0) as coverage_score_global,
            COALESCE(cc.sources_used, ARRAY[]::text[]) as sources_used
        FROM sofia.mv_security_country_combined c
        LEFT JOIN country_coverage cc ON c.country_code = cc.country_code
        WHERE {where_clause}
        ORDER BY c.{sort_column} DESC NULLS LAST
    """
    
    cur.execute(query, params)
    
    countries = []
    for row in cur.fetchall():
        coverage = float(row['coverage_score_global']) if row['coverage_score_global'] else 0
        
        # Apply min_coverage filter if specified
        if min_coverage and coverage < min_coverage:
            continue
        
        # Warning
        warning = "Baixa cobertura — risco pode estar subestimado" if coverage < 50 else None
        
        countries.append({
            "country_code": row['country_code'],
            "country_name": row['country_name'],
            "acute_risk": float(row['acute_risk_score']) if row['acute_risk_score'] else 0,
            "structural_risk": float(row['structural_risk_score']) if row['structural_risk_score'] else 0,
            "total_risk": float(row['total_risk_score']) if row['total_risk_score'] else 0,
            "risk_level": row['risk_level'],
            "coverage_score_global": coverage,
            "sources_used": list(row['sources_used']) if row['sources_used'] else [],
            "last_update": row['as_of_date'].isoformat() if row['as_of_date'] else None,
            "warning": warning,
            "breakdown": {
                "total_incidents": row['total_incidents'] or 0,
                "fatalities": row['fatalities'] or 0,
                "indicators_count": row['indicators_count'] or 0
            }
        })
    
    cur.close()
    conn.close()
    
    # Calculate avg coverage
    avg_coverage = sum(c["coverage_score_global"] for c in countries) / len(countries) if countries else 0
    
    return {
        "countries": countries,
        "metadata": {
            "total_countries": len(countries),
            "avg_coverage": round(avg_coverage, 1)
        }
    }


@app.get("/api/security/countries/{country_code}/local")
async def get_country_local_detail(country_code: str):
    """
    Get local detail for a specific country (Brasil)
    
    Uses: BRASIL_* sources only
    Warning: "Dados não comparáveis globalmente"
    
    Returns: Local risk breakdown
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    country_code = country_code.upper()
    
    # PARAMETERIZED query to prevent SQL injection
    # Check if country has local data
    cur.execute("""
        SELECT COUNT(*)
        FROM sofia.security_observations
        WHERE country_code = %s AND coverage_scope = 'local_only'
    """, (country_code,))
    
    if cur.fetchone()['count'] == 0:
        raise HTTPException(status_code=404, detail=f"No local data for country {country_code}")
    
    # Get country name
    cur.execute("""
        SELECT DISTINCT country_name
        FROM sofia.security_observations
        WHERE country_code = %s
        LIMIT 1
    """, (country_code,))
    
    result = cur.fetchone()
    country_name = result['country_name'] if result else country_code
    
    # Get local risk score (average of all local sources)
    cur.execute("""
        SELECT AVG(severity_norm) as avg_severity
        FROM sofia.security_observations
        WHERE country_code = %s AND coverage_scope = 'local_only'
    """, (country_code,))
    
    local_risk = float(cur.fetchone()['avg_severity'] or 0)
    
    # Get coverage score local
    cur.execute("""
        SELECT MAX(coverage_score_local) as max_coverage
        FROM sofia.security_observations
        WHERE country_code = %s AND coverage_scope = 'local_only'
    """, (country_code,))
    
    coverage_local = float(cur.fetchone()['max_coverage'] or 0)
    
    # Get breakdown by source (single query)
    cur.execute("""
        SELECT 
            source,
            AVG(severity_norm) as avg_severity,
            MAX(event_time_start) as last_update,
            COUNT(*) as record_count
        FROM sofia.security_observations
        WHERE country_code = %s AND coverage_scope = 'local_only'
        GROUP BY source
        ORDER BY avg_severity DESC
    """, (country_code,))
    
    breakdown = {}
    sources_used = []
    for row in cur.fetchall():
        sources_used.append(row['source'])
        breakdown[row['source'].lower().replace('_', '-')] = {
            "severity_norm": float(row['avg_severity']) if row['avg_severity'] else 0,
            "source": row['source'],
            "last_update": row['last_update'].isoformat() if row['last_update'] else None,
            "record_count": row['record_count']
        }
    
    # Get states breakdown (if admin1 exists)
    cur.execute("""
        SELECT 
            admin1,
            AVG(severity_norm) as avg_severity
        FROM sofia.security_observations
        WHERE country_code = %s 
          AND coverage_scope = 'local_only'
          AND admin1 IS NOT NULL
        GROUP BY admin1
        ORDER BY avg_severity DESC
        LIMIT 10
    """, (country_code,))
    
    states = []
    for row in cur.fetchall():
        states.append({
            "state_code": row['admin1'],
            "state_name": row['admin1'],
            "local_risk": float(row['avg_severity']) if row['avg_severity'] else 0
        })
    
    cur.close()
    conn.close()
    
    return {
        "country_code": country_code,
        "country_name": country_name,
        "local_risk_score": round(local_risk, 1),
        "coverage_score_local": coverage_local,
        "sources_used": sources_used,
        "warning": "Cobertura local detalhada. Dados não comparáveis globalmente.",
        "breakdown": breakdown,
        "states": states
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "2.1", "spec": "compliant"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
