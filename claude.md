# 🤖 CLAUDE - Sofia Pulse Context (Current)

**Date**: 2025-12-23  
**Status**: Production Active - 85% Operational ✅

> [!NOTE]
> History moved to `CLAUDE_HISTORY.md` due to size.

---

## 🎯 Current Status: Production Deployment Complete

Successfully unified **70+ collectors** and deployed to production server with WhatsApp notifications.

### ✅ What's Working (11/13 collectors - 85%)

**Production Server**: `api-tiespecialistas`  
**Last Run**: 704 records inserted in 1m 24s  
**WhatsApp**: Active on 551151990773 (TIE Especialistas)

| Collector | Records/Run | Status |
|:---|:---:|:---|
| GitHub | 100 | ✅ |
| HackerNews | 4 | ✅ |
| StackOverflow | 100 | ✅ |
| Himalayas | 0 | ✅ |
| RemoteOK | Active | ✅ |
| AI Companies | Active | ✅ |
| Universities | Active | ✅ |
| NGOs | Active | ✅ |
| YC Companies | 500 | ✅ |
| NVD | Active | ✅ |
| GDELT | Active | ✅ |

### ❌ Known Issues (2 collectors)

| Collector | Error | Impact | Priority |
|:---|:---|:---|:---|
| MDIC Regional | Timeout | Missing Brazil trade data | Medium |
| FIESP Data | Timeout | Missing industry sentiment | Medium |

**CISA**: Removed (permanently blocked HTTP 403)

---

## 📊 System Architecture

### Unified CLI
```bash
npx tsx scripts/collect.ts [collector-name]
npx tsx scripts/collect.ts --all
```

### Data Tables

| Table | Records | Update Frequency | Status |
|:---|:---:|:---|:---|
| `sofia.tech_trends` | 200+ | Hourly | ✅ Active |
| `sofia.jobs` | 7,848 | Hourly | ✅ Active |
| `sofia.funding_rounds` | 2,577 | Hourly | ✅ Active |
| `sofia.organizations` | Active | Hourly | ✅ Active |
| `sofia.industry_signals` | Active | Hourly | ✅ Active |
| `sofia.comexstat_trade` | 1,596 | - | ⚠️ Not updating |
| `sofia.fiesp_sensor` | 234 | - | ⚠️ Not updating |
| `sofia.data_sources` | 58 | Static | ✅ Compliance |

### 70+ Collectors Unified

**Native TypeScript** (27 collectors):
- Tech Trends: GitHub, HackerNews, NPM, PyPI, StackOverflow
- Jobs: Himalayas, RemoteOK, Arbeitnow
- Organizations: AI Companies, Universities, NGOs
- Funding: YC Companies, Product Hunt
- Industry: NVD, GDELT, Space, AI Regulation
- Developer Tools: VSCode, JetBrains
- Conferences: Confs.tech, Meetup

**Python Bridge** (43 legacy collectors):
- Security (4), Economic (13), Social/Health (6)
- Women/Gender (6), Sports (3), Jobs (7), Other (4)

---

## 🔧 Recent Fixes (All in GitHub)

### 1. Python Compatibility
**Issue**: `spawn python ENOENT` on Ubuntu  
**Fix**: Changed to `python3` in python-bridge-collector.ts  
**Commit**: 3256db7

### 2. WhatsApp Configuration
**Issue**: Using wrong number (027 instead of 011)  
**Fix**: Prioritize `WHATSAPP_SENDER` over `WHATSAPP_NUMBER`  
**Commit**: 31d024c

### 3. CISA Removal
**Issue**: HTTP 403 (permanently blocked)  
**Fix**: Removed from production collector list  
**Commit**: de61bdf

### 4. Notification System
**Feature**: WhatsApp notifications with INSERT counts  
**Implementation**: `run-collectors-with-notifications.sh`  
**Commit**: 57a6e73

---

## 📱 WhatsApp Notifications

**Recipient**: 551151990773 (TIE Especialistas)  
**Frequency**: After each collector + final summary

**Format**:
```
✅ github
📊 100 novos registros
⏱️ [1/13]

🏁 Sofia Pulse - Coleta Finalizada
✅ Sucesso: 11/13 (85%)
❌ Falhas: 2/13
📊 Total Inserido: 704 registros
⏱️ Duração: 1m 24s
```

---

## 🔜 Pending Tasks

### Priority 1: Fix MDIC & FIESP Timeouts
- [ ] Investigate python3 compatibility issues
- [ ] Test with increased timeout (currently 300s)
- [ ] Verify API endpoints are accessible
- [ ] Check file permissions for FIESP Excel files

### Priority 2: Improve Insert Tracking
- [ ] Some collectors show "?" for insert counts
- [ ] Standardize output format across all collectors
- [ ] Better regex patterns in notification script

### Priority 3: Monitoring & Alerts
- [ ] Add Grafana dashboard for collector metrics
- [ ] Alert on repeated failures (3+ consecutive)
- [ ] Track insert trends over time
- [ ] Monitor API rate limits

### Priority 4: Systemd Integration
- [ ] Update systemd service to use notification script
- [ ] Configure proper restart policies
- [ ] Set up log rotation
- [ ] Add health check endpoint

---

## 🚀 Deployment Commands

### Update Code
```bash
cd /home/ubuntu/sofia-pulse
git pull origin master
```

### Run Collectors
```bash
./run-collectors-with-notifications.sh
```

### Check Status
```bash
sudo systemctl status sofia-pulse-collectors.timer
tail -f logs/collectors-*.log
```

### View Database
```sql
-- Recent collector runs
SELECT collector_name, status, started_at, completed_at 
FROM sofia.collector_runs 
ORDER BY started_at DESC 
LIMIT 20;

-- Data freshness
SELECT source, COUNT(*), MAX(collected_at) as last_update
FROM sofia.tech_trends
GROUP BY source;
```

---

## 📈 Success Metrics

- ✅ **Unification**: 70+ collectors → 1 CLI
- ✅ **Automation**: Systemd timer active (hourly)
- ✅ **Notifications**: WhatsApp working (551151990773)
- ✅ **Governance**: 58 sources tracked in `data_sources`
- ✅ **Production**: 85% success rate (11/13)
- ✅ **Code Quality**: All fixes in GitHub (no manual edits)

---

## 🐛 Troubleshooting

### Collectors Not Running
```bash
# Check systemd
sudo systemctl status sofia-pulse-collectors.timer
sudo journalctl -u sofia-pulse-collectors.service -f

# Check logs
tail -100 logs/collectors-*.log

# Test manually
npx tsx scripts/collect.ts github
```

### WhatsApp Not Sending
```bash
# Verify .env
grep WHATSAPP .env

# Check API
curl http://91.98.158.19:3001/status

# Test integration
python3 scripts/utils/sofia_whatsapp_integration.py
```

### Database Connection Issues
```bash
# Verify .env
grep DB_ .env

# Test connection
psql -h localhost -U sofia -d sofia_db
```

---

## 📝 Documentation

- **Setup Guide**: `SERVER_SETUP.md`
- **Deploy Guide**: `DEPLOY_GUIDE.md`
- **Walkthrough**: `walkthrough.md`
- **Task List**: `task.md`
- **History**: `CLAUDE_HISTORY.md`

---

**Status**: 🟢 **PRODUCTION ACTIVE**  
**Next Execution**: Automatic (hourly via systemd)  
**Monitoring**: WhatsApp notifications enabled

---

*Last Updated: 2025-12-23 16:59 BRT*
