# How to Get Crunchbase API Key (FREE Tier)

**Last Updated**: 2026-01-14

---

## 🎯 Overview

Crunchbase offers a **FREE tier** with:
- ✅ **500 requests/month** (enough for 15 rounds/day = 450/month)
- ✅ Access to funding rounds data
- ✅ Company information, investors, amounts, dates
- ✅ No credit card required for signup

---

## 📋 Step-by-Step Guide

### 1. Create Account

1. Go to: **https://www.crunchbase.com/api/**
2. Click **"Sign Up"** or **"Get API Access"**
3. Fill in:
   - Email
   - Password
   - Company name (can use "Personal" or "Research")
4. Verify email

### 2. Get API Key

1. Log in to: **https://data.crunchbase.com/**
2. Navigate to **Account Settings** → **API Keys**
3. Click **"Create New Key"**
4. Select **"Basic (Free)" tier**
5. Copy the API key (looks like: `abcd1234efgh5678...`)

### 3. Add to Sofia Pulse

**Windows (local development)**:
```bash
# Edit .env file
notepad C:\Users\augusto.moreira\Documents\sofia-pulse\.env

# Add this line:
CRUNCHBASE_API_KEY=your_actual_key_here
```

**Linux (production server)**:
```bash
# SSH to server
ssh -i ~/.ssh/id_ed25519_server root@91.98.158.19

# Edit .env
cd /root/sofia-pulse
nano .env

# Add this line:
CRUNCHBASE_API_KEY=your_actual_key_here

# Save: Ctrl+O, Enter, Ctrl+X
```

---

## 🧪 Test the Collector

### Option 1: Using collect.ts (Recommended)

```bash
# Test from local machine (Windows Git Bash)
cd /c/Users/augusto.moreira/Documents/sofia-pulse
npx tsx scripts/collect.ts crunchbase

# Or from production server
cd /root/sofia-pulse
npx tsx scripts/collect.ts crunchbase
```

### Option 2: Direct Test

```bash
# Test API key with curl
curl -X POST "https://api.crunchbase.com/api/v4/searches/funding_rounds" \
  -H "X-cb-user-key: YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "field_ids": ["identifier"],
    "limit": 1
  }'

# Should return JSON with funding rounds data
```

---

## 📊 Expected Output

When successful, you should see:

```
======================================================================
💰 Crunchbase Funding Rounds
   Crunchbase funding rounds (15 recent rounds daily, free tier)
======================================================================

🔍 Run ID: 12345

🔍 Fetching from API...
   URL: https://api.crunchbase.com/api/v4/searches/funding_rounds

✅ API Response: 200 OK
📦 Raw response entities: 15

🔍 Parsed 15 funding rounds
💾 Saving to database...

✅ Summary:
   • Total collected: 15 rounds
   • With amount_usd: 12 rounds (80%)
   • Companies: 15
   • Average amount: $8.5M
   • Date range: 2025-12-15 to 2026-01-14

⏱️  Duration: 2.4s
======================================================================
```

---

## ⚙️ Collector Configuration

**File**: `scripts/configs/funding-config.ts` (lines 140-204)

**Settings**:
- **Limit**: 15 rounds/day = 450/month (buffer for 500 limit)
- **Schedule**: Daily 12:00 UTC
- **Filters**:
  - Last 30 days
  - Round types: seed, pre-seed, series_a/b/c/d/e, venture
- **Fields**: company, amount, date, investors, round type

**To customize** (e.g., change limit or filters):
```bash
# Edit config
nano scripts/configs/funding-config.ts

# Find 'export const crunchbase' (line 140)
# Modify:
#   - limit: 15 → change daily limit
#   - query[0].values: change date range
#   - query[1].values: change round types
```

---

## 🚀 Add to Crontab (Production Server)

```bash
# SSH to server
ssh -i ~/.ssh/id_ed25519_server root@91.98.158.19

# Edit crontab
crontab -e

# Add this line:
0 12 * * * cd /root/sofia-pulse && npx tsx scripts/collect.ts crunchbase >> /var/log/sofia/crunchbase.log 2>&1

# Save and exit
```

**Schedule**: Daily at 12:00 UTC (09:00 BRT)

**Logs**: `/var/log/sofia/crunchbase.log`

---

## 🔍 Troubleshooting

### Error: "Missing API Key"
```
❌ Error: Missing CRUNCHBASE_API_KEY environment variable
```

**Solution**: Make sure `CRUNCHBASE_API_KEY` is in your `.env` file and the file is loaded.

### Error: 401 Unauthorized
```
❌ API Response: 401 Unauthorized
```

**Solution**: API key is invalid or expired. Get a new one from Crunchbase.

### Error: 403 Forbidden
```
❌ API Response: 403 Forbidden
```

**Solution**:
- You've hit the 500 req/month limit
- Wait until next month or upgrade to paid tier
- Check current usage at: https://data.crunchbase.com/

### Error: No data returned
```
✅ API Response: 200 OK
📦 Raw response entities: 0
```

**Solution**: No funding rounds in the last 30 days matching your filters. This is normal if:
- Weekend or holiday (less activity)
- Filter too restrictive (try expanding date range)

---

## 📈 Monitor Usage

### Check API Usage

```bash
# Check how many requests you've made
# Login to: https://data.crunchbase.com/
# Navigate to: Account → API Usage
# See: 450/500 requests used this month
```

### Check Database Growth

```bash
# Connect to database
psql -h 91.98.158.19 -U sofia -d sofia_db

# Check Crunchbase rounds
SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN amount_usd > 0 THEN 1 END) as with_amount,
    MIN(announced_date) as earliest,
    MAX(announced_date) as latest
FROM sofia.funding_rounds
WHERE source = 'crunchbase';

# Expected after 30 days:
# total: ~450 rounds
# with_amount: ~360 rounds (80%)
# earliest: 30 days ago
# latest: today
```

---

## 💡 Tips

1. **Daily Collection**: 15 rounds/day is optimal for free tier
2. **Buffer**: Leaves 50 requests buffer for retries/testing
3. **Coverage**: Focuses on early-stage (seed to Series E)
4. **Data Quality**: ~80% have amount_usd filled
5. **Geographic**: Global coverage (not just USA)

---

## 🔗 Resources

- **Crunchbase API Docs**: https://data.crunchbase.com/docs
- **API Explorer**: https://data.crunchbase.com/reference
- **Rate Limits**: https://data.crunchbase.com/docs/rate-limits
- **Pricing**: https://www.crunchbase.com/api/pricing

---

**Next Steps**:
1. ✅ Get API key (5 minutes)
2. ✅ Add to `.env` file
3. ✅ Test collector: `npx tsx scripts/collect.ts crunchbase`
4. ✅ Add to crontab (production only)
5. ⏳ Wait 7-14 days for data accumulation
6. ✅ Check Early-Stage Deep Dive report quality

**Estimated Time**: 10 minutes setup + 7-14 days data collection
