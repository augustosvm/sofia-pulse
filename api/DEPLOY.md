# Security API - Deploy Guide

## Local Development

```bash
cd sofia-pulse/api
pip install -r requirements.txt
uvicorn security-api:app --reload --port 8000
```

## Server Deployment (Docker)

### 1. Build and Run
```bash
cd sofia-pulse

# Build image
docker build -f api/Dockerfile -t sofia-security-api:latest .

# Run with docker-compose
docker-compose -f docker-compose.security-api.yml up -d
```

### 2. Verify
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok","version":"2.1","spec":"compliant"}

curl http://localhost:8000/api/security/countries | jq '.metadata'
# Should show total_countries
```

### 3. Logs
```bash
docker logs sofia-security-api -f
```

## Environment Variables

Required in `.env`:
```
POSTGRES_HOST=your_host
POSTGRES_PORT=5432
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=sofia
```

## Endpoints

- `GET /health` - Health check
- `GET /api/security/map` - Map points (ACLED + BR local)
- `GET /api/security/countries` - Country scores (hybrid)
- `GET /api/security/countries/{code}/local` - Local detail

## Dependencies

- fastapi==0.109.0
- uvicorn==0.27.0
- psycopg2-binary==2.9.9
- python-dotenv==1.0.0

## Notes

- API runs on port 8000
- Requires PostgreSQL with sofia schema
- Views must be refreshed: `SELECT sofia.refresh_security_hybrid_views();`
