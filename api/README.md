# Security Hybrid Model API

FastAPI implementation of the Security Hybrid Model v2.1

## Endpoints

### 1. GET /api/security/map
Get security points for map display

**Query Parameters:**
- `zoom` (optional): Zoom level 1-20
- `country` (optional): Country code (e.g., BR)
- `bbox` (optional): Bounding box (w,s,e,n)
- `sources` (optional): Comma-separated sources (default: "acled,local")

**Returns:** GeoJSON FeatureCollection

**Example:**
```bash
curl "http://localhost:8000/api/security/map?zoom=10&country=BR"
```

---

### 2. GET /api/security/countries
Get security scores by country (hybrid model)

**Query Parameters:**
- `sort` (optional): Sort by total_risk|acute_risk|structural_risk (default: total_risk)
- `min_coverage` (optional): Minimum coverage score 0-100
- `risk_level` (optional): Filter by Critical|High|Elevated|Moderate|Low

**Returns:** Array of country scores

**Example:**
```bash
curl "http://localhost:8000/api/security/countries?sort=total_risk&min_coverage=50"
```

---

### 3. GET /api/security/countries/{country_code}/local
Get local detail for a specific country

**Path Parameters:**
- `country_code`: Country code (e.g., BR)

**Returns:** Local risk breakdown

**Example:**
```bash
curl "http://localhost:8000/api/security/countries/BR/local"
```

---

## Installation

```bash
pip install fastapi uvicorn psycopg2-binary
```

## Running

```bash
python api/security-api.py
```

Or with uvicorn:
```bash
uvicorn api.security-api:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment

Requires `.env` file with:
```
POSTGRES_HOST=...
POSTGRES_PORT=...
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_DB=...
```

## Architecture

### /api/security/map
- **Sources:** ACLED + Brasil local (conditional)
- **Conditional:** Brasil local only if zoom >= 8 OR country=BR
- **Never returns:** World Bank, GDELT as points

### /api/security/countries
- **Sources:** ACLED + GDELT + World Bank
- **Never uses:** Brasil local data in global score

### /api/security/countries/{code}/local
- **Sources:** BRASIL_* only
- **Warning:** "Dados não comparáveis globalmente"

## Response Examples

### /api/security/map
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-46.63, -23.55]
      },
      "properties": {
        "source": "ACLED",
        "severity_norm": 75.5,
        "country_code": "BR",
        "coverage_score_global": 50,
        "warning": null
      }
    }
  ],
  "metadata": {
    "total_points": 1234,
    "sources_used": ["acled"],
    "zoom_level": 10
  }
}
```

### /api/security/countries
```json
{
  "countries": [
    {
      "country_code": "UA",
      "country_name": "Ukraine",
      "acute_risk": 85.2,
      "structural_risk": 45.0,
      "total_risk": 71.1,
      "risk_level": "High",
      "coverage_score_global": 70,
      "sources_used": ["ACLED", "GDELT", "WORLD_BANK"],
      "warning": null
    }
  ],
  "metadata": {
    "total_countries": 195,
    "avg_coverage": 55.3
  }
}
```

### /api/security/countries/BR/local
```json
{
  "country_code": "BR",
  "country_name": "Brazil",
  "local_risk_score": 65.0,
  "coverage_score_local": 90,
  "sources_used": ["BRASIL_CRIME", "BRASIL_VIOLENCE_WOMEN"],
  "warning": "Cobertura local detalhada. Dados não comparáveis globalmente.",
  "breakdown": {
    "brasil-crime": {
      "severity_norm": 45.0,
      "last_update": "2026-01-10"
    }
  }
}
```

## Version

2.1 - Official Implementation
