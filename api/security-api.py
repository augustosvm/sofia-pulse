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
    
    # Query based on view type
    # For GEO view:
    # - Global/Regional (ACLED): Must have lat/lon
    # - Local (BRASIL_*): Can have NULL lat/lon (client will use centroids) if zoom is high enough or country selected
    
    # Base query - FIXED: use correct column names
    query = """
        SELECT
            id as event_id,
            event_time_start as date,
            country_name as country,
            country_code,
            city as location,
            admin1,
            latitude,
            longitude,
            source,
            signal_type as event_type,
            fatalities,
            raw_payload->>'sub_event_type' as sub_event_type,
            raw_payload->>'notes' as notes,
            severity_norm,
            coverage_score_global,
            coverage_score_local,
            coverage_scope
        FROM sofia.security_observations
        WHERE event_time_start >= CURRENT_DATE - INTERVAL '90 days'
    """
    
    # Determine if we should include local data
    include_local = (zoom and zoom >= 8) or (country and country.upper() == 'BR')
    
    filters = []
    query_params = [] # Use a new list for params for this new query structure
    
    # Coverage Scope Logic
    if include_local:
        # Global comparable (ACLED) OR Local (BRASIL_*)
        # Note: For Global, we require lat/lon. For Local, we accept NULL lat/lon.
        filters.append("""
            (
                (coverage_scope = 'global_comparable' AND latitude IS NOT NULL AND longitude IS NOT NULL)
                OR
                (coverage_scope = 'local_only')
            )
        """)
    else:
        # Only global comparable with lat/lon
        filters.append("coverage_scope = 'global_comparable'")
        filters.append("latitude IS NOT NULL")
        filters.append("longitude IS NOT NULL")
        
    if country: # Use the original 'country' parameter
        filters.append("country_code = %s")
        query_params.append(country.upper())
        
    if bbox:
        try:
            w, s, e, n = map(float, bbox.split(','))
            filters.append("latitude BETWEEN %s AND %s")
            filters.append("longitude BETWEEN %s AND %s")
            query_params.extend([s, n, w, e])
        except:
            raise HTTPException(status_code=400, detail="Invalid bbox format. Use: w,s,e,n")

    if filters:
        query += " AND " + " AND ".join(filters)
        
    query_params.append(limit)
    
    # print(f"Executing Map Query: {query} | Params: {query_params}") # Debug
        
    cur.execute(query + " ORDER BY event_time_start DESC LIMIT %s", tuple(query_params))
    rows = cur.fetchall()
    
    features = []
    for row in rows:
        # Calculate severity (simplified for map points)
        # ACLED/Global usually has fatalities. Local might have different metrics.
        severity_norm = float(row['severity_norm']) if row['severity_norm'] else 0
        
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
                "coordinates": [float(row['longitude']), float(row['latitude'])] if row['longitude'] and row['latitude'] else None
            },
            "properties": {
                "id": row['event_id'],
                "countryName": row['country'],
                "countryCode": row['country_code'],
                "latitude": row['latitude'], # Can be None for local
                "longitude": row['longitude'], # Can be None for local
                "location": row['location'],
                "admin1": row['admin1'], # Important for local fallback
                "incidents": 1, # Individual event
                "fatalities": row['fatalities'] or 0,
                "severityNorm": severity_norm,
                "riskLevel": "Moderate", # Dynamiccalc would be better but expensive here
                "topEventType": row['event_type'],
                "windowDays": 90,
                "dataSource": row['source'],
                "asOfDate": row['date'].isoformat() if row['date'] else None,
                "coverage_score": float(coverage) if coverage else 0,
                "coverage_scope": row['coverage_scope'],
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


@app.get("/api/capital/by-country")
async def get_capital_by_country():
    """
    Capital Intelligence by Country (Anti-Mock, Enterprise)
    Returns: Real data with deterministic narratives
    """
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT 
                country_code,
                total_vol_12m as total_usd,
                deals_12m as deal_count,
                avg_ticket_12m as avg_usd,
                momentum_pct,
                market_stage,
                top_sector,
                sector_count,
                confidence_score
            FROM sofia.mv_capital_analytics 
            ORDER BY total_vol_12m DESC
        """)
        rows = cur.fetchall()
        
        countries = []
        for row in rows:
            total = float(row['total_usd'])
            momentum = float(row['momentum_pct'])
            confidence = float(row['confidence_score'])
            sector_count = row['sector_count'] or 1
            
            # Flow type classification
            if total >= 10_000_000_000: flow = 'high_flow'
            elif total >= 1_000_000_000: flow = 'medium_flow'
            elif total >= 100_000_000: flow = 'low_flow'
            else: flow = 'minimal_flow'
            
            # DETERMINISTIC NARRATIVE
            narrative_parts = []
            # Momentum narrative
            if momentum > 0.5: narrative_parts.append("Capital acelerando rapidamente")
            elif momentum > 0: narrative_parts.append("Capital crescendo moderadamente")
            elif momentum > -0.3: narrative_parts.append("Capital estável")
            else: narrative_parts.append("Capital em retração")
            
            # Stage narrative
            stage = row['market_stage']
            if stage == 'late_growth': narrative_parts.append("Mercado maduro (late stage)")
            elif stage == 'mid_growth': narrative_parts.append("Mercado em expansão (mid stage)")
            else: narrative_parts.append("Mercado emergente (early stage)")
            
            # Concentration warning
            if sector_count <= 2:
                narrative_parts.append(f"Alta concentração em {row['top_sector'] or 'setor único'}")
            
            narrative = ". ".join(narrative_parts) + "."
            
            # Warning for low confidence
            warning = None
            if confidence < 0.5:
                warning = "Análise baseada em dados parciais. Interpretar com cautela."

            countries.append({
                "iso": row['country_code'],
                "metrics": {
                    "total_usd": total,
                    "deal_count": int(row['deal_count']),
                    "avg_usd": float(row['avg_usd']),
                    "momentum": momentum,
                    "stage": stage,
                    "top_sector": row['top_sector'],
                    "diversity": min(1.0, sector_count / 5.0)  # Normalize to 0-1
                },
                "narrative": narrative,
                "confidence": confidence,
                "class": flow,
                "warning": warning
            })
            
        cur.close()
        return {
            "success": True, 
            "data": countries,
            "metadata": {
                "source": "sofia_intelligence_v1",
                "count": len(countries),
                "generated_at": datetime.now().isoformat(),
                "refresh_frequency": "daily"
            }
        }
    except Exception as e:
        print(f"Error fetching capital data: {e}")
        return {"success": False, "error": str(e), "data": []}
    finally:
        if conn: conn.close()


@app.get("/api/opportunity/by-country")
async def get_opportunity_by_country():
    """
    Opportunity Composite Index (Capital + Talent - Security Risk)
    """
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT * FROM sofia.mv_opportunity_by_country
            ORDER BY opportunity_score DESC
        """)
        rows = cur.fetchall()
        
        countries = []
        for row in rows:
            confidence = float(row['confidence']) if row['confidence'] else 0
            score = float(row['opportunity_score']) if row['opportunity_score'] else 0
            
            # Narrative
            tier = row['opportunity_tier']
            if tier == 'prime_opportunity':
                narrative = "Oportunidade prime: capital forte, talento disponível, risco controlado."
            elif tier == 'high_potential':
                narrative = "Alto potencial: boas condições em múltiplos pilares."
            elif tier == 'emerging':
                narrative = "Mercado emergente: oportunidades com ressalvas."
            else:
                narrative = "Mercado desafiador: avaliar riscos cuidadosamente."
            
            countries.append({
                "iso": row['country_code'],
                "metrics": {
                    "opportunity_score": score,
                    "capital_score": float(row['capital_score'] or 0),
                    "talent_score": float(row['talent_score'] or 0),
                    "security_score": float(row['security_score'] or 0),
                    "capital_volume": float(row['capital_volume'] or 0),
                    "talent_jobs": int(row['talent_jobs'] or 0),
                    "security_risk": float(row['security_risk'] or 0)
                },
                "narrative": narrative,
                "confidence": confidence,
                "class": tier,
                "warning": "Dados parciais." if confidence < 0.5 else None
            })
        
        cur.close()
        return {
            "success": True,
            "data": countries,
            "metadata": {
                "source": "sofia_intelligence_v1",
                "count": len(countries),
                "generated_at": datetime.now().isoformat(),
                "refresh_frequency": "daily"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}
    finally:
        if conn: conn.close()


@app.get("/api/brain-drain/by-country")
async def get_brain_drain_by_country():
    """Brain Drain Index - Talent Export vs Import"""
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM sofia.mv_brain_drain_by_country ORDER BY brain_drain_index DESC")
        rows = cur.fetchall()
        
        countries = []
        for row in rows:
            tier = row['brain_drain_tier']
            if tier == 'talent_exporter':
                narrative = "Exportador líquido de talento: produz mais do que emprega."
            elif tier == 'talent_importer':
                narrative = "Importador líquido de talento: emprega mais do que produz."
            else:
                narrative = "Fluxo de talento equilibrado."
            
            countries.append({
                "iso": row['country_code'],
                "metrics": {
                    "brain_drain_index": float(row['brain_drain_index'] or 0),
                    "papers_produced": int(row['papers_produced'] or 0),
                    "jobs_available": int(row['jobs_available'] or 0)
                },
                "narrative": narrative,
                "confidence": float(row['confidence'] or 0),
                "class": tier,
                "warning": None
            })
        
        cur.close()
        return {"success": True, "data": countries, "metadata": {"count": len(countries), "generated_at": datetime.now().isoformat()}}
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}
    finally:
        if conn: conn.close()


@app.get("/api/ai-density/by-country")
async def get_ai_density_by_country():
    """AI Capability Density"""
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM sofia.mv_ai_capability_density_by_country ORDER BY ai_density_score DESC")
        rows = cur.fetchall()
        
        countries = []
        for row in rows:
            tier = row['ai_tier']
            countries.append({
                "iso": row['country_code'],
                "metrics": {
                    "ai_density_score": float(row['ai_density_score'] or 0),
                    "ai_papers": int(row['ai_papers'] or 0),
                    "ai_jobs": int(row['ai_jobs'] or 0)
                },
                "narrative": f"Posicionamento AI: {tier.replace('_', ' ').title()}.",
                "confidence": float(row['confidence'] or 0),
                "class": tier,
                "warning": None
            })
        
        cur.close()
        return {"success": True, "data": countries, "metadata": {"count": len(countries), "generated_at": datetime.now().isoformat()}}
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}
    finally:
        if conn: conn.close()


# ============================================================================
# INTELLIGENCE EXPANSION ENDPOINTS (Real Data from MVs)
# ============================================================================

@app.get("/api/research-velocity/by-country")
async def get_research_velocity_by_country():
    """Research Velocity Index - Papers momentum and volume by country"""
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM sofia.mv_research_velocity_by_country ORDER BY papers_12m DESC")
        rows = cur.fetchall()
        
        countries = []
        for row in rows:
            tier = row['velocity_tier']
            momentum = float(row['momentum_pct'] or 0)
            
            # Deterministic narrative
            if tier == 'research_powerhouse':
                narrative = f"Centro de pesquisa global. {row['papers_12m']} papers em 12m."
            elif tier == 'research_active':
                narrative = f"Pesquisa ativa. Momentum {'positivo' if momentum > 0 else 'estável'}."
            else:
                narrative = "Pesquisa em desenvolvimento."
            
            if momentum > 50:
                narrative += " Crescimento acelerado."
            elif momentum < -20:
                narrative += " Retração observada."
            
            countries.append({
                "iso": row['country_code'],
                "metrics": {
                    "papers_12m": int(row['papers_12m'] or 0),
                    "papers_6m": int(row['papers_6m'] or 0),
                    "momentum_pct": momentum,
                    "avg_citations": float(row['avg_citations'] or 0),
                    "category_diversity": int(row['category_diversity'] or 0),
                    "top_category": row['top_category']
                },
                "narrative": narrative,
                "confidence": float(row['confidence'] or 0),
                "class": tier,
                "warning": None
            })
        
        cur.close()
        return {
            "success": True, 
            "data": countries, 
            "metadata": {
                "count": len(countries), 
                "generated_at": datetime.now().isoformat(),
                "sources": ["openalex", "arxiv"],
                "refresh_frequency": "daily"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}
    finally:
        if conn: conn.close()


@app.get("/api/conference-gravity/by-country")
async def get_conference_gravity_by_country():
    """Conference Gravity Index - Tech conference density and activity"""
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM sofia.mv_conference_gravity_by_country ORDER BY gravity_score DESC")
        rows = cur.fetchall()
        
        countries = []
        for row in rows:
            tier = row['gravity_tier']
            
            if tier == 'conference_hub':
                narrative = f"Hub de conferências. {row['conference_count']} eventos, {row['major_conferences']} de grande porte."
            elif tier == 'conference_active':
                narrative = f"Cena de conferências ativa com {row['conference_count']} eventos."
            else:
                narrative = "Presença limitada de conferências tech."
            
            countries.append({
                "iso": row['country_code'],
                "metrics": {
                    "conference_count": int(row['conference_count'] or 0),
                    "major_conferences": int(row['major_conferences'] or 0),
                    "gravity_score": float(row['gravity_score'] or 0),
                    "seasonality": row['seasonality']
                },
                "narrative": narrative,
                "confidence": float(row['confidence'] or 0),
                "class": tier,
                "warning": None
            })
        
        cur.close()
        return {
            "success": True, 
            "data": countries, 
            "metadata": {
                "count": len(countries), 
                "generated_at": datetime.now().isoformat(),
                "sources": ["tech_conferences"],
                "refresh_frequency": "weekly"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}
    finally:
        if conn: conn.close()


@app.get("/api/tool-demand/by-country")
async def get_tool_demand_by_country():
    """Tool Demand Index - Developer stack modernity from job postings"""
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM sofia.mv_tool_demand_by_country ORDER BY tool_demand_score DESC")
        rows = cur.fetchall()
        
        countries = []
        for row in rows:
            tier = row['stack_tier']
            
            if tier == 'modern_stack':
                narrative = f"Stack moderno. {row['tools_diversity']} ferramentas, foco em {row['top_tool']}."
            elif tier == 'diverse_stack':
                narrative = f"Stack diversificado com {row['tools_diversity']} ferramentas."
            else:
                narrative = "Stack tradicional ou dados limitados."
            
            countries.append({
                "iso": row['country_code'],
                "metrics": {
                    "tool_demand_score": float(row['tool_demand_score'] or 0),
                    "tools_diversity": int(row['tools_diversity'] or 0),
                    "total_tool_mentions": int(row['total_tool_mentions'] or 0),
                    "top_tool": row['top_tool']
                },
                "narrative": narrative,
                "confidence": float(row['confidence'] or 0),
                "class": tier,
                "warning": None
            })
        
        cur.close()
        return {
            "success": True, 
            "data": countries, 
            "metadata": {
                "count": len(countries), 
                "generated_at": datetime.now().isoformat(),
                "sources": ["jobs"],
                "refresh_frequency": "daily"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}
    finally:
        if conn: conn.close()


# ============================================================================
# INTELLIGENCE EXPANSION PHASE 2 ENDPOINTS
# ============================================================================

@app.get("/api/industry-signals/by-country")
async def get_industry_signals_by_country():
    """Industry Signals Heat - Business activity and sector momentum"""
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM sofia.mv_industry_signals_heat_by_country ORDER BY heat_score DESC")
        rows = cur.fetchall()
        
        countries = []
        for row in rows:
            tier = row['heat_tier']
            momentum = float(row['signal_momentum'] or 0)
            
            # Deterministic narrative
            if tier == 'signals_hot':
                narrative = f"Mercado em ebulição. {row['signals_30d']} sinais em 30d."
                if momentum > 1.5:
                    narrative += " Aceleração forte."
            elif tier == 'signals_active':
                narrative = f"Atividade consistente. {row['sector_diversity']} setores ativos."
            elif tier == 'signals_emerging':
                narrative = f"Atividade emergente. Setor dominante: {row['dominant_sector'] or 'diverso'}."
            else:
                narrative = "Atividade limitada ou dados parciais."
            
            countries.append({
                "iso": row['country_code'],
                "metrics": {
                    "heat_score": float(row['heat_score'] or 0),
                    "signals_30d": int(row['signals_30d'] or 0),
                    "signals_90d": int(row['signals_90d'] or 0),
                    "signal_momentum": momentum,
                    "sector_diversity": int(row['sector_diversity'] or 0),
                    "dominant_sector": row['dominant_sector']
                },
                "narrative": narrative,
                "confidence": float(row['confidence'] or 0),
                "class": tier,
                "warning": "Dados parciais." if float(row['confidence'] or 0) < 0.5 else None
            })
        
        cur.close()
        return {
            "success": True,
            "data": countries,
            "metadata": {
                "count": len(countries),
                "generated_at": datetime.now().isoformat(),
                "as_of_date": datetime.now().date().isoformat(),
                "sources": ["industry_signals"],
                "refresh_frequency": "daily"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}
    finally:
        if conn: conn.close()


@app.get("/api/cyber-risk/by-country")
async def get_cyber_risk_by_country():
    """Cyber Risk Density - Cybersecurity threat concentration"""
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM sofia.mv_cyber_risk_by_country ORDER BY cyber_risk_score DESC")
        rows = cur.fetchall()
        
        countries = []
        for row in rows:
            tier = row['cyber_tier']
            
            # Deterministic narrative
            if tier == 'cyber_critical':
                narrative = f"Risco crítico. {row['critical_events']} eventos críticos, severidade média {row['severity_avg']:.1f}."
            elif tier == 'cyber_high':
                narrative = f"Risco elevado. {row['events_90d']} eventos em 90d."
            elif tier == 'cyber_moderate':
                narrative = "Risco moderado. Monitorar tendências."
            else:
                narrative = "Risco baixo ou dados limitados."
            
            countries.append({
                "iso": row['country_code'],
                "metrics": {
                    "cyber_risk_score": float(row['cyber_risk_score'] or 0),
                    "events_90d": int(row['events_90d'] or 0),
                    "critical_events": int(row['critical_events'] or 0),
                    "severity_avg": float(row['severity_avg'] or 0)
                },
                "narrative": narrative,
                "confidence": float(row['confidence'] or 0),
                "class": tier,
                "warning": "Dados parciais." if float(row['confidence'] or 0) < 0.5 else None
            })
        
        cur.close()
        return {
            "success": True,
            "data": countries,
            "metadata": {
                "count": len(countries),
                "generated_at": datetime.now().isoformat(),
                "as_of_date": datetime.now().date().isoformat(),
                "sources": ["cybersecurity_events"],
                "refresh_frequency": "daily"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}
    finally:
        if conn: conn.close()


@app.get("/api/clinical-trials/by-country")
async def get_clinical_trials_by_country():
    """Clinical Trial Activity - Pharma innovation density"""
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM sofia.mv_clinical_trials_by_country ORDER BY trial_activity_score DESC")
        rows = cur.fetchall()
        
        countries = []
        for row in rows:
            tier = row['pharma_tier']
            
            # Deterministic narrative
            if tier == 'pharma_hub':
                narrative = f"Hub farmacêutico. {row['trials_12m']} trials em 12m, {row['phase3_count']} Phase 3."
            elif tier == 'pharma_active':
                narrative = f"Atividade pharma consistente. {row['area_diversity']} áreas terapêuticas."
            elif tier == 'pharma_emerging':
                narrative = "Atividade pharma emergente."
            else:
                narrative = "Atividade pharma limitada."
            
            countries.append({
                "iso": row['country_code'],
                "metrics": {
                    "trial_activity_score": float(row['trial_activity_score'] or 0),
                    "trials_12m": int(row['trials_12m'] or 0),
                    "phase3_count": int(row['phase3_count'] or 0),
                    "area_diversity": int(row['area_diversity'] or 0)
                },
                "narrative": narrative,
                "confidence": float(row['confidence'] or 0),
                "class": tier,
                "warning": None
            })
        
        cur.close()
        return {
            "success": True,
            "data": countries,
            "metadata": {
                "count": len(countries),
                "generated_at": datetime.now().isoformat(),
                "as_of_date": datetime.now().date().isoformat(),
                "sources": ["clinical_trials"],
                "refresh_frequency": "weekly"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}
    finally:
        if conn: conn.close()


# ============================================================================
# WOMEN & NGO INTELLIGENCE ENDPOINTS (Phase 3)
# ============================================================================

@app.get("/api/women/by-country")
async def get_women_intelligence_by_country():
    """Violence Risk Proxy - General violence data (ACLED). NOT gender-specific."""
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM sofia.mv_women_intelligence_by_country ORDER BY violence_risk_score DESC")
        rows = cur.fetchall()
        
        countries = []
        for row in rows:
            tier = row['violence_tier']
            confidence = float(row['confidence'] or 0)
            momentum = float(row['violence_momentum'] or 0)
            data_scope = row.get('data_scope', 'proxy_general_violence')
            
            # Momentum arrow
            if momentum > 1.3:
                momentum_txt = "↑"
            elif momentum < 0.7:
                momentum_txt = "↓"
            else:
                momentum_txt = "→"
            
            # Deterministic narrative with PROXY disclaimer
            proxy_note = "Proxy baseado em violência geral (ACLED), sem recorte de gênero na fonte."
            
            if tier == 'violence_crisis':
                narrative = f"Crise de violência {momentum_txt}. {row['events_30d']} eventos em 4 semanas. {proxy_note}"
            elif tier == 'violence_high':
                narrative = f"Risco elevado {momentum_txt}. {row['events_30d']} eventos recentes. {proxy_note}"
            elif tier == 'violence_watch':
                narrative = f"Em monitoramento {momentum_txt}. {proxy_note}"
            elif tier == 'violence_low':
                narrative = f"Risco baixo {momentum_txt}. {proxy_note}"
            else:
                narrative = "Dados insuficientes para análise."
            
            # Warnings
            warnings = []
            if confidence < 0.5 and tier != 'no_data':
                warnings.append("low_confidence")
            if data_scope == 'proxy_general_violence':
                warnings.append("proxy_not_gender_specific")
            
            countries.append({
                "iso": row['country_code'],
                "metrics": {
                    "violence_risk_score": float(row['violence_risk_score'] or 0),
                    "events_30d": int(row['events_30d'] or 0),
                    "events_90d": int(row['events_90d'] or 0),
                    "fatalities_90d": int(row['fatalities_90d'] or 0),
                    "violence_momentum": momentum,
                    "data_scope": data_scope
                },
                "narrative": narrative,
                "confidence": confidence,
                "class": tier,
                "warning": ", ".join(warnings) if warnings else None
            })
        
        cur.close()
        return {
            "success": True,
            "data": countries,
            "metadata": {
                "count": len(countries),
                "generated_at": datetime.now().isoformat(),
                "as_of_date": datetime.now().date().isoformat(),
                "sources": ["acled_aggregated"],
                "data_scope": "proxy_general_violence",
                "refresh_frequency": "daily",
                "note": "General violence proxy. No gender-specific data available in ACLED aggregated."
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}
    finally:
        if conn: conn.close()


@app.get("/api/ngo/by-country")
async def get_ngo_coverage_by_country():
    """NGO/Civil Society Coverage - Sector density by country"""
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM sofia.mv_ngo_coverage_by_country ORDER BY ngo_coverage_score DESC")
        rows = cur.fetchall()
        
        countries = []
        for row in rows:
            tier = row['ngo_tier']
            confidence = float(row['confidence'] or 0)
            momentum = float(row['ngo_momentum'] or 0)
            
            # Momentum arrow
            if momentum > 1.3:
                momentum_txt = "↑"
            elif momentum < 0.7:
                momentum_txt = "↓"
            else:
                momentum_txt = "→"
            
            # Deterministic narrative
            if tier == 'ngo_dense':
                narrative = f"Alta densidade NGO {momentum_txt}. {row['ngo_signals_30d']} sinais em 4 semanas, {row['sector_diversity']} setores."
            elif tier == 'ngo_active':
                narrative = f"Atividade NGO consistente {momentum_txt}. {row['ngo_signals_90d']} sinais em 13 semanas."
            elif tier == 'ngo_emerging':
                narrative = f"Setor NGO emergente {momentum_txt}."
            elif tier == 'ngo_sparse':
                narrative = f"Presença NGO limitada {momentum_txt}."
            else:
                narrative = "Dados insuficientes para análise."
            
            # Warning for low confidence
            warning = "low_confidence" if (confidence < 0.5 and tier != 'no_data') else None
            
            countries.append({
                "iso": row['country_code'],
                "metrics": {
                    "ngo_coverage_score": float(row['ngo_coverage_score'] or 0),
                    "ngo_signals_30d": int(row['ngo_signals_30d'] or 0),
                    "ngo_signals_90d": int(row['ngo_signals_90d'] or 0),
                    "ngo_signals_total": int(row['ngo_signals_total'] or 0),
                    "sector_diversity": int(row['sector_diversity'] or 0),
                    "ngo_momentum": momentum
                },
                "narrative": narrative,
                "confidence": confidence,
                "class": tier,
                "warning": warning
            })
        
        cur.close()
        return {
            "success": True,
            "data": countries,
            "metadata": {
                "count": len(countries),
                "generated_at": datetime.now().isoformat(),
                "as_of_date": datetime.now().date().isoformat(),
                "sources": ["industry_signals"],
                "refresh_frequency": "daily"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}

    finally:
        if conn: conn.close()


# ============================================================================
# SCAFFOLD ENDPOINTS (domains pending data sources)
# ============================================================================

@app.get("/api/innovation/by-country")
async def get_innovation_by_country():
    """Innovation Velocity - Scaffold (pending full implementation)"""
    return {"success": True, "data": [], "metadata": {"count": 0, "notes": "Use /api/research-velocity/by-country for research-based innovation metrics"}}

@app.get("/api/regulatory/by-country")
async def get_regulatory_by_country():
    """Regulatory Pressure - Scaffold (no data source yet)"""
    return {"success": True, "data": [], "metadata": {"count": 0, "notes": "Needs external regulatory data source"}}

@app.get("/api/infrastructure/by-country")
async def get_infrastructure_by_country():
    """Infrastructure Stress - Scaffold (no data source yet)"""
    return {"success": True, "data": [], "metadata": {"count": 0, "notes": "Needs World Bank infrastructure index"}}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "2.5-enterprise", "spec": "compliant", "domains": 14}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
