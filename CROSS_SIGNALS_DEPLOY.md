# Cross Signals - Deployment Guide

**Status**: ✅ Ready for Production
**Date**: 2026-01-27
**Version**: 1.0.0

---

## 📋 What Was Implemented

### 1. **Null Rates Calculation** ✅
- Real calculation of `deep_read_null_rate`, `engagement_null_rate`, `chat_activation_null_rate`
- Replaces placeholder `{}` with actual metrics from database
- Graceful fallback to 1.0 if tables don't exist

### 2. **GitHub & Funding Reactions** ✅
- GitHub activity correlation (stars, language, description matching)
- Funding rounds correlation (based on companies, technologies, topics)
- Both with confidence scoring (0.75-0.80)

### 3. **Smart Classification** ✅
- **Domain classification**: 12 domains (SECURITY, AI, DEVTOOLS, SPACE, JOBS, etc.)
- **Region extraction**: ISO country codes from entities (with country name → code mapping)
- **Entity conversion**: JSONB → schema format (companies, technologies, people, countries, frameworks)

### 4. **Email Renderer (Safe Plug-in)** ✅
- `scripts/utils/cross_signals_email_renderer.py` - standalone renderer
- Renders top N insights (configurable via `render_hints.max_items_email`)
- Shows warnings, confidence distribution, reaction sources
- **Safe**: If JSON missing or 0 insights → returns empty string (no email break)
- **Integrated**: Added to `send-email-mega.py` with try/except (silent failure)

### 5. **Cron Schedule** ✅
- `run-cross-signals-builder.sh` - runs builder + refreshes materialized views
- `update-crontab-with-cross-signals.sh` - installs cron schedule
- **Schedule**: 21:30 UTC (30 min before email at 22:00 UTC)

---

## 🚀 Quick Deploy (Production)

### Step 1: Apply Database Migrations

```bash
cd ~/sofia-pulse

# Apply VSCode Marketplace migration
psql -h localhost -U postgres -d sofia -f database/migrations/061_create_vscode_extensions_daily.sql

# Apply News Items migration
psql -h localhost -U postgres -d sofia -f database/migrations/062_create_news_items.sql
```

### Step 2: Test the Builder

```bash
# Dry run
python3 scripts/build-cross-signals.py --dry-run

# Real run
python3 scripts/build-cross-signals.py

# Check output
cat outputs/cross_signals.json | python3 -m json.tool | head -50
```

### Step 3: Test Email Renderer

```bash
python3 scripts/utils/cross_signals_email_renderer.py
```

### Step 4: Make Scripts Executable

```bash
chmod +x run-cross-signals-builder.sh
chmod +x update-crontab-with-cross-signals.sh
```

### Step 5: Test Full Pipeline

```bash
bash run-cross-signals-builder.sh
```

### Step 6: Install Cron Schedule

```bash
bash update-crontab-with-cross-signals.sh
crontab -l  # Verify
```

---

## 📊 New Schedule

```
10:00 UTC - Fast APIs collection
16:00 UTC - Limited APIs collection
21:30 UTC - Cross Signals Builder ⭐ NEW
22:00 UTC - Analytics + Reports
22:05 UTC - Email (with Cross Signals block)
```

---

## 🔧 Configuration

### Adjust Analysis Window

```bash
python3 scripts/build-cross-signals.py --window-days 14  # Default: 7
```

### Adjust Email Rendering

Edit `render_hints` in builder output (line 585-590 of build-cross-signals.py):
- `max_items_email`: Top N insights in email (default: 5)
- `highlight_domains`: Domains to emphasize (default: ['SECURITY', 'AI'])

---

## 🧪 Testing

### Validate JSON Schema

```bash
npm install -g ajv-cli
ajv validate -s schemas/cross_signals.schema.json -d outputs/cross_signals.json
```

### Test Email with Cross Signals

Check email body includes:
```
========================================
🔗 CROSS SIGNALS - Multi-Source Intelligence
========================================
```

---

## 🐛 Troubleshooting

### No insights generated

```bash
# Check news_items count
psql -d sofia -c "SELECT COUNT(*) FROM sofia.news_items WHERE published_at >= NOW() - INTERVAL '7 days';"

# Try longer window
python3 scripts/build-cross-signals.py --window-days 14
```

### Email doesn't show Cross Signals

```bash
# Test renderer
python3 scripts/utils/cross_signals_email_renderer.py

# Check JSON exists
ls -lh outputs/cross_signals.json
```

---

## 🔄 Rollback

```bash
# Restore old crontab
crontab ~/sofia-pulse-crontab-backup-*.txt

# Revert email changes
git checkout send-email-mega.py
```

---

**Full Documentation**: See inline comments in `scripts/build-cross-signals.py`
