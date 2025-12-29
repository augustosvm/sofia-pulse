# 🛡️ Sofia Pulse - Reliability Blueprint

**Version**: 1.0
**Date**: 2025-11-21
**Status**: ✅ IMPLEMENTED

---

## 📋 Overview

Este documento descreve a infraestrutura de confiabilidade do Sofia Pulse, garantindo:
- ✅ 99.9% de disponibilidade dos coletores
- ✅ Detecção automática de falhas
- ✅ Alertas em tempo real
- ✅ Validação de integridade dos dados
- ✅ Retry automático em falhas de API
- ✅ Logs profissionais e rastreáveis

---

## 🏗️ Arquitetura de Confiabilidade

```
┌─────────────────────────────────────────────────────────────┐
│                    SOFIA PULSE                               │
│                  Reliability Stack                           │
└─────────────────────────────────────────────────────────────┘
           │
           ├─► 1. Professional Logging
           │      /var/log/sofia/collectors/*.log
           │      - Structured logs with timestamps
           │      - Log rotation (60 days retention)
           │      - Compression enabled
           │
           ├─► 2. Retry Logic with Backoff
           │      scripts/utils/retry.py
           │      - Exponential backoff (2s → 32s)
           │      - Random jitter to avoid thundering herd
           │      - Rate limit detection
           │
           ├─► 3. Health Monitoring
           │      healthcheck-collectors.sh
           │      - Checks all collectors
           │      - Detects failures
           │      - Reports status
           │
           ├─► 4. Data Sanity Checks
           │      scripts/sanity-check.py
           │      - Minimum row validation
           │      - Anomaly detection
           │      - Duplicate detection
           │      - Freshness validation
           │
           └─► 5. Alert System
                  scripts/utils/alerts.py
                  - Telegram alerts
                  - WhatsApp alerts
                  - Email alerts (planned)
```

---

## 📦 Components

### 1. Professional Logging

**File**: `scripts/utils/logger.py`

**Features**:
- Structured logging format: `[2025-11-21 10:30:02] LEVEL: message`
- Separate file per collector
- Console + file output
- Automatic log rotation (60 days)

**Usage**:
```python
from scripts.utils.logger import setup_logger, log_collector_start, log_collector_finish

logger = setup_logger('collect-github')
log_collector_start(logger, 'GitHub Trending Collector')

# Your collection code here

log_collector_finish(logger, 'GitHub Trending Collector', rows_inserted=143, duration_seconds=5.1)
```

### 2. Retry Logic with Backoff

**File**: `scripts/utils/retry.py`

**Features**:
- Exponential backoff: 2s → 4s → 8s → 16s → 32s
- Random jitter (50-100% of delay)
- Rate limit detection (HTTP 429)
- Timeout handling
- Connection error recovery

**Usage**:
```python
from scripts.utils.retry import safe_request, retry_with_backoff

# Simple usage
response = safe_request('https://api.github.com/repos', max_retries=5)

# Decorator usage
@retry_with_backoff(max_retries=5)
def fetch_data():
    return requests.get(url)
```

### 3. Health Monitoring

**File**: `healthcheck-collectors.sh`

**Features**:
- Checks all collector logs
- Detects last successful run
- Identifies failures
- Reports summary statistics

**Usage**:
```bash
# Manual check
bash healthcheck-collectors.sh

# Automated (cron)
*/30 * * * * /home/ubuntu/sofia-pulse/healthcheck-collectors.sh
```

**Output**:
```
✅ collect-github-trending.ts — OK
❌ collect-reddit-tech.ts — LAST RUN FAILED
   Error: HTTP 403 - Rate limited

📊 SUMMARY
Total collectors: 16
Healthy: 14
Failed: 2
```

### 4. Data Sanity Checks

**File**: `scripts/sanity-check.py`

**Features**:
- Minimum row count validation
- Future date detection
- Data freshness checks
- Anomaly detection (massive spikes or zeros)
- Duplicate detection

**Checks performed**:
```
✅ Row count OK: 143 rows
✅ No future dates
✅ Recent data: 0 days old
✅ Daily volume normal: 143 rows (avg: 138)
```

**Usage**:
```bash
# Manual check
python3 scripts/sanity-check.py

# After each collection
python3 scripts/sanity-check.py || send_alert "Data validation failed"
```

### 5. Alert System

**File**: `scripts/utils/alerts.py`

**Features**:
- Multi-channel alerts (Telegram, WhatsApp, Email)
- Severity levels (INFO, WARNING, CRITICAL)
- Pre-built alert templates
- Rate limit awareness

**Usage**:
```python
from scripts.utils.alerts import alert_collector_failed, alert_data_anomaly, send_alert

# Generic alert
send_alert("Database connection failed", level='CRITICAL', channels=['telegram', 'whatsapp'])

# Collector failure
alert_collector_failed('collect-github', 'HTTP 403 - Rate limited')

# Data anomaly
alert_data_anomaly('github_trending', 'ZERO_ROWS', 'Expected 100+ rows, got 0')
```

**Configuration**:
```bash
# Telegram
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# WhatsApp (via sofia-mastra-rag)
export WHATSAPP_ENDPOINT="https://your-endpoint/send-message"

# Email
export ALERT_EMAIL="augustosvm@gmail.com"
```

---

## 🚀 Implementation Checklist

### Phase 1: Infrastructure (DONE ✅)
- [x] Create log directories (`/var/log/sofia/`)
- [x] Setup log rotation (60 days retention)
- [x] Create logging utility (`logger.py`)
- [x] Create retry utility (`retry.py`)
- [x] Create alert system (`alerts.py`)
- [x] Create healthcheck script
- [x] Create sanity check script

### Phase 2: Integration (TODO)
- [ ] Update all collectors to use `logger.py`
- [ ] Update all collectors to use `retry.py`
- [ ] Add sanity checks after each collection
- [ ] Setup Telegram bot
- [ ] Configure alert thresholds
- [ ] Add to cron jobs

### Phase 3: Monitoring (TODO)
- [ ] Setup Grafana dashboard
- [ ] Configure Prometheus metrics
- [ ] Add collector runtime metrics
- [ ] Add data volume metrics
- [ ] Setup weekly tests

---

## 📊 Monitoring Dashboard (Planned)

### Metrics to track:
1. **Collector Health**
   - Last successful run timestamp
   - Failure rate (last 24h)
   - Average execution time

2. **Data Volume**
   - Rows inserted per day
   - Anomaly detection (spikes/zeros)
   - Growth trends

3. **API Health**
   - Rate limit status
   - Error rates
   - Response times

4. **Database Health**
   - Connection pool usage
   - Query performance
   - Table sizes

---

## 🔧 Maintenance

### Daily
- Automated healthchecks every 30 minutes
- Automated sanity checks after collections
- Alert on failures

### Weekly
- Review logs for patterns
- Check alert history
- Verify data integrity

### Monthly
- Log rotation (automatic)
- Review collector performance
- Update retry thresholds if needed

---

## 📚 Best Practices

### For Collectors
1. **Always use structured logging**
   ```python
   logger.info(f"FETCHED: {count} records from {api_name}")
   ```

2. **Always use retry logic**
   ```python
   response = safe_request(url, max_retries=5)
   ```

3. **Always validate data**
   ```python
   if rows_inserted == 0:
       logger.warning("Zero rows inserted - possible API issue")
       alert_data_anomaly(...)
   ```

4. **Always handle errors gracefully**
   ```python
   try:
       collect_data()
   except Exception as e:
       log_collector_error(logger, collector_name, str(e))
       alert_collector_failed(collector_name, str(e))
   ```

### For Alerts
- **INFO**: Informational (rate limits, retries)
- **WARNING**: Recoverable issues (low data volume, slow API)
- **CRITICAL**: System down (collector failed, zero data, database unreachable)

---

## 🎯 Success Criteria

Sofia Pulse reliability is achieved when:

- ✅ **99.9% uptime** for all collectors
- ✅ **< 5 minute** detection time for failures
- ✅ **< 15 minute** recovery time for transient failures
- ✅ **Zero data corruption** (guaranteed delivery)
- ✅ **Complete audit trail** (all logs retained 60 days)
- ✅ **Proactive alerts** (issues detected before user impact)

---

## 📞 Support

**Issues**: https://github.com/augustosvm/sofia-pulse/issues
**Email**: augustosvm@gmail.com
**Status**: Check `/var/log/sofia/collectors/` for real-time status

---

**Last Updated**: 2025-11-21 21:30 UTC
**Branch**: `claude/fix-github-rate-limits-012Xm4nfg6i34xKQHSDbWfq3`
