import requests
import sys

try:
    r = requests.get('http://localhost:8000/api/security/countries')
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(r.text)
        sys.exit(1)
        
    data = r.json()
    countries = data.get('countries', [])
    print(f"Total countries in API: {len(countries)}")
    
    found = [c for c in countries if c['country_code'] in ['BR', 'AR', 'CO', 'MX']]
    if found:
        print("✅ Found Latin American countries:")
        for c in found:
            print(f" - {c['country_name']} ({c['country_code']})")
    else:
        print("❌ Latin America NOT found in API.")
        
except Exception as e:
    print(f"Error: {e}")
