# 🔑 API Keys Setup Guide

Quick guide to configure all API keys for Sofia Pulse.

**ALL APIs are FREE** (no credit card required, just registration)

---

## ⚡ Quick Setup

```bash
# 1. Copy example file
cp .env.example .env

# 2. Edit .env and add your keys
nano .env

# 3. Test APIs
python3 test-apis.py

# 4. Run collectors
bash run-all-now.sh
```

---

## 📝 API Keys Required

### 1. ⚡ EIA (U.S. Energy Information Administration)

**Used for**: Electricity consumption data (global)

**Sign up**: https://www.eia.gov/opendata/register.php

**Free tier**: Unlimited requests

**Setup**:
1. Visit https://www.eia.gov/opendata/register.php
2. Fill in: Name, Email, Organization
3. Receive API key instantly by email
4. Add to `.env`: `EIA_API_KEY=your_key_here`

**Example key format**: `QKUixUcUGWnmT7ffUKPeIzeS7OrInmtd471qboys`

---

### 2. 📈 API Ninjas (Commodity Prices)

**Used for**: Real-time commodity prices (oil, gold, copper, wheat, etc.)

**Sign up**: https://api-ninjas.com/

**Free tier**: 20 requests/minute (28,800/day)

**Setup**:
1. Visit https://api-ninjas.com/
2. Click "Sign Up" (top right)
3. Verify email
4. Go to "My Account" → API Key
5. Add to `.env`: `API_NINJAS_KEY=your_key_here`

**Example key format**: `IsggR55vW5kTD5w71PKRzg==DU8KUx0G1gYwbO2I`

---

### 3. 📊 Alpha Vantage (Stock Market Data)

**Used for**: NASDAQ, stock prices, financial data

**Sign up**: https://www.alphavantage.co/support/#api-key

**Free tier**: 25 requests/day

**Setup**:
1. Visit https://www.alphavantage.co/support/#api-key
2. Enter email
3. Receive key instantly
4. Add to `.env`: `ALPHA_VANTAGE_API_KEY=your_key_here`

---

### 4. 🔴 Reddit API (Optional)

**Used for**: Tech subreddits (r/programming, r/machinelearning, etc.)

**Sign up**: https://www.reddit.com/prefs/apps

**Free tier**: 60 requests/minute

**Setup**:
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Select "script" type
4. Fill in:
   - Name: `sofia-pulse`
   - Redirect URI: `http://localhost:8080`
5. Copy `client_id` (under app name) and `secret`
6. Add to `.env`:
   ```
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_secret
   ```

**Note**: If you get "You cannot create any more applications" error, contact Reddit support at https://support.reddithelp.com/hc/en-us/requests/new?ticket_form_id=14868593862164

---

## ✅ APIs That Don't Need Keys

These work out-of-the-box:

- ✅ **GitHub Trending** - Public
- ✅ **HackerNews** - Public API
- ✅ **NPM** - Public
- ✅ **PyPI** - Public
- ✅ **ArXiv** - Public
- ✅ **World Bank** - Public API
- ✅ **Launch Library 2** (Space launches) - Free API
- ✅ **NVD** (CVEs) - Public
- ✅ **CISA** - Public
- ✅ **GDELT** - Free (requires Google Cloud account)

---

## 🧪 Testing Your Setup

### Quick Test (All APIs)

```bash
python3 test-apis.py
```

Expected output:
```
✅ EIA API working! Status: 200
✅ API Ninjas working! Gold price: $2050.00
✅ World Bank API working!
```

### Test Individual Collectors

```bash
# Test electricity consumption
python3 scripts/collect-electricity-consumption.py

# Test commodity prices
python3 scripts/collect-commodity-prices.py

# Test port traffic
python3 scripts/collect-port-traffic.py

# Test semiconductors
python3 scripts/collect-semiconductor-sales.py
```

---

## 🔒 Security Notes

1. **Never commit `.env` to git** (it's in `.gitignore`)
2. Use `.env.example` for documentation
3. API keys are personal - don't share publicly
4. For production, use environment variables or secret managers

---

## 📊 Current Status

| API | Required? | Free Tier | Daily Limit | Status |
|-----|-----------|-----------|-------------|--------|
| **EIA** | Recommended | Yes | Unlimited | ✅ Configured |
| **API Ninjas** | Recommended | Yes | 28,800/day | ✅ Configured |
| **Alpha Vantage** | Already set | Yes | 25/day | ✅ Working |
| **Reddit** | Optional | Yes | 86,400/day | ⚠️  Pending (app quota) |
| **World Bank** | Auto | Yes | Unlimited | ✅ Working |
| **GitHub** | Auto | Yes | 60/hour (5,000 auth) | ✅ Working |

---

## 🚀 Next Steps After Setup

1. **Create tables**:
   ```bash
   python3 create-tables-python.py
   ```

2. **Run collectors**:
   ```bash
   bash run-all-now.sh
   ```

3. **Setup cron** (daily at 22:00 UTC):
   ```bash
   bash update-crontab-simple.sh
   ```

4. **Check email** (19h BRT):
   - 8 TXT reports
   - CSV exports

---

**Last Updated**: 2025-11-19
**Status**: ✅ All APIs configured and ready
