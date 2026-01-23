# GA4 BigQuery Collector - Server Deployment Guide

## Prerequisites

- GA4 property with BigQuery Export enabled
- Service account JSON with BigQuery Data Viewer role
- SSH access to Sofia Pulse server
- Python 3.x with google-cloud-bigquery, psycopg2, python-dotenv

## Files Created

1. `scripts/verify_ga4_bq.py` - Verification script
2. `scripts/collect_ga4_bigquery.py` - Main collector
3. `database/migrations/061_create_analytics_events_table.sql` - Database schema

## Step 1: Upload Files to Server

```bash
# From local machine
scp scripts/verify_ga4_bq.py root@your_server:/home/ubuntu/sofia-pulse/scripts/
scp scripts/collect_ga4_bigquery.py root@your_server:/home/ubuntu/sofia-pulse/scripts/
scp database/migrations/061_create_analytics_events_table.sql root@your_server:/home/ubuntu/sofia-pulse/database/migrations/
```

## Step 2: Update Environment Variables

SSH to server and edit `/home/ubuntu/sofia-pulse.env`:

```bash
ssh root@your_server
nano /home/ubuntu/sofia-pulse.env
```

Add these lines:

```bash
# GA4 BigQuery Analytics
GCP_PROJECT_ID=tiespecialistas-tts
GA4_BQ_DATASET=  # Leave empty for auto-detection
GOOGLE_APPLICATION_CREDENTIALS=/opt/sofia/secrets/ga_bigquery.json
```

Verify service account JSON exists:

```bash
ls -la /opt/sofia/secrets/ga_bigquery.json
```

## Step 3: Apply Database Migration

```bash
cd /home/ubuntu/sofia-pulse

# Method 1: Using psql
psql -h localhost -U sofia -d sofia_db -f database/migrations/061_create_analytics_events_table.sql

# Method 2: Using run-migrations.sh (if available)
bash run-migrations.sh
```

Verify table was created:

```bash
psql -h localhost -U sofia -d sofia_db -c "\d sofia.analytics_events"
```

## Step 4: Install Python Dependencies

```bash
pip3 install google-cloud-bigquery psycopg2-binary python-dotenv
```

## Step 5: Run Verification Script

```bash
cd /home/ubuntu/sofia-pulse
source /home/ubuntu/sofia-pulse.env  # Load environment variables
export GOOGLE_APPLICATION_CREDENTIALS=/opt/sofia/secrets/ga_bigquery.json

python3 scripts/verify_ga4_bq.py
```

Expected output:

```
================================================================================
GA4 BIGQUERY EXPORT VERIFICATION
================================================================================

Project ID: tiespecialistas-tts
GA4 Dataset Override: (auto-detect)

[OK] BigQuery client initialized

Scanning for GA4 datasets in project: tiespecialistas-tts

[FOUND] GA4 dataset: analytics_XXXXXXXXX

--------------------------------------------------------------------------------

Listing event tables in tiespecialistas-tts.analytics_XXXXXXXXX...

Event tables (daily): XX
Latest 5 tables:
  - events_20260122 (2026-01-22)
  - events_20260121 (2026-01-21)
  ...

Event tables (intraday): X
Latest 3 tables:
  - events_intraday_20260122
  ...
```

## Step 6: Run Test Collection

Collect last 7 days (default):

```bash
python3 scripts/collect_ga4_bigquery.py
```

Collect specific date range:

```bash
python3 scripts/collect_ga4_bigquery.py --start 2026-01-01 --end 2026-01-22
```

Collect last 30 days:

```bash
python3 scripts/collect_ga4_bigquery.py --days 30
```

Include intraday tables (today's incomplete data):

```bash
python3 scripts/collect_ga4_bigquery.py --days 1 --include_intraday
```

Expected output:

```
================================================================================
GA4 BIGQUERY COLLECTOR
================================================================================

Date Range: 2026-01-15 to 2026-01-21 (7 days)
Project: tiespecialistas-tts
Include Intraday: False

[OK] BigQuery client initialized
[INFO] Auto-detected dataset: analytics_XXXXXXXXX

[INFO] Fetching events from 20260115 to 20260121...
[OK] Fetched 12,345 events from BigQuery

[OK] Connected to Postgres

[INFO] Inserting events to Postgres...
[BATCH] Inserted 1000/1000 (batch 1)
[BATCH] Inserted 1000/1000 (batch 2)
...
[BATCH] Inserted 345/345 (batch 13)

================================================================================
COLLECTION COMPLETE
================================================================================

Fetched from BigQuery: 12,345 events
Inserted to Postgres:  12,345 events
Skipped (duplicates):  0 events

[OK] Collection successful
```

## Step 7: Verify Data in Postgres

```bash
psql -h localhost -U sofia -d sofia_db
```

```sql
-- Check total events
SELECT COUNT(*) FROM sofia.analytics_events;

-- Check date range
SELECT MIN(event_date), MAX(event_date) FROM sofia.analytics_events;

-- Top events
SELECT event_name, COUNT(*) as count
FROM sofia.analytics_events
GROUP BY event_name
ORDER BY count DESC
LIMIT 10;

-- Top pages
SELECT page_path, COUNT(*) as views
FROM sofia.analytics_events
WHERE event_name = 'page_view'
GROUP BY page_path
ORDER BY views DESC
LIMIT 10;

-- Daily traffic
SELECT event_date, COUNT(*) as events, COUNT(DISTINCT user_pseudo_id) as users
FROM sofia.analytics_events
GROUP BY event_date
ORDER BY event_date DESC
LIMIT 7;
```

## Step 8: Schedule Daily Collection (Cron)

Edit crontab:

```bash
crontab -e
```

Add daily collection at 16:00 UTC (13:00 BRT):

```bash
# GA4 BigQuery Collector (daily at 16:00 UTC)
0 16 * * * cd /home/ubuntu/sofia-pulse && source /home/ubuntu/sofia-pulse.env && python3 scripts/collect_ga4_bigquery.py --days 7 >> /var/log/sofia-ga4-collector.log 2>&1
```

## Troubleshooting

### Error: "No GA4 dataset found"

Check BigQuery export is configured:
1. Go to GA4 Admin > Property > BigQuery Links
2. Verify link to project `tiespecialistas-tts`
3. Verify daily export is enabled
4. Wait 24h for first export

### Error: "Failed to initialize BigQuery client"

Check service account credentials:

```bash
# Verify file exists
ls -la /opt/sofia/secrets/ga_bigquery.json

# Verify environment variable
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test authentication
gcloud auth activate-service-account --key-file=/opt/sofia/secrets/ga_bigquery.json
```

### Error: "psycopg2 connect failed"

Check Postgres connection in .env:

```bash
grep POSTGRES /home/ubuntu/sofia-pulse.env
```

Test connection:

```bash
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;"
```

### No events fetched

Check table suffix dates:

```bash
python3 scripts/verify_ga4_bq.py
```

Verify events exist in BigQuery:

```sql
SELECT COUNT(*) FROM `tiespecialistas-tts.analytics_XXXXXXXXX.events_20260122`;
```

### Duplicate events (skipped count high)

This is normal on re-runs. The collector is idempotent (event_hash deduplication).

## Next Steps

1. Run collector daily via cron
2. Use data for analytics reports
3. Create dashboards in Grafana/Metabase
4. Correlate GA4 events with funding rounds, job postings, etc.

## Example Queries

Page views by source/medium:

```sql
SELECT source, medium, COUNT(*) as views
FROM sofia.analytics_events
WHERE event_name = 'page_view'
    AND event_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY source, medium
ORDER BY views DESC
LIMIT 20;
```

User engagement by device:

```sql
SELECT device_category,
       COUNT(DISTINCT user_pseudo_id) as users,
       SUM(engagement_time_ms) / 1000 / 60 as total_minutes
FROM sofia.analytics_events
WHERE engagement_time_ms > 0
GROUP BY device_category
ORDER BY users DESC;
```

Top countries:

```sql
SELECT country, COUNT(*) as events, COUNT(DISTINCT user_pseudo_id) as users
FROM sofia.analytics_events
WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY country
ORDER BY events DESC
LIMIT 10;
```
