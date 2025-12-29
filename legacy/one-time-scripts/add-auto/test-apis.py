#!/usr/bin/env python3
"""
Test API keys for Sofia Pulse collectors
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("🔑 TESTING API KEYS")
print("=" * 80)
print()

# Test 1: EIA API
print("1. Testing EIA API...")
eia_key = os.getenv('EIA_API_KEY', '')
if eia_key:
    print(f"   ✅ EIA_API_KEY found: {eia_key[:10]}...")
    try:
        url = f"https://api.eia.gov/v2/international/data/"
        params = {
            'api_key': eia_key,
            'frequency': 'annual',
            'data[0]': 'value',
            'facets[activityId][]': '2',
            'length': 1
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'response' in data:
                print(f"   ✅ EIA API working! Status: {response.status_code}")
            else:
                print(f"   ⚠️  EIA API response unexpected: {data}")
        else:
            print(f"   ❌ EIA API failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ EIA API error: {e}")
else:
    print("   ❌ EIA_API_KEY not found in .env")

print()

# Test 2: API Ninjas
print("2. Testing API Ninjas...")
ninjas_key = os.getenv('API_NINJAS_KEY', '')
if ninjas_key:
    print(f"   ✅ API_NINJAS_KEY found: {ninjas_key[:10]}...")
    try:
        url = "https://api.api-ninjas.com/v1/commodityprice?name=gold"
        headers = {'X-Api-Key': ninjas_key}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'price' in data:
                print(f"   ✅ API Ninjas working! Gold price: ${data['price']}")
            else:
                print(f"   ⚠️  Unexpected response: {data}")
        else:
            print(f"   ❌ API Ninjas failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ API Ninjas error: {e}")
else:
    print("   ❌ API_NINJAS_KEY not found in .env")

print()

# Test 3: World Bank API (no key required)
print("3. Testing World Bank API (no key required)...")
try:
    url = "https://api.worldbank.org/v2/country/USA/indicator/IS.SHP.GOOD.TU"
    params = {'format': 'json', 'per_page': 1}
    response = requests.get(url, params=params, timeout=10)
    if response.status_code == 200:
        data = response.json()
        if len(data) >= 2:
            print(f"   ✅ World Bank API working!")
        else:
            print(f"   ⚠️  Unexpected response format")
    else:
        print(f"   ❌ World Bank API failed: HTTP {response.status_code}")
except Exception as e:
    print(f"   ❌ World Bank API error: {e}")

print()
print("=" * 80)
print("✅ TESTS COMPLETE")
print("=" * 80)
