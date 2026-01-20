#!/usr/bin/env python3
"""
Download and prepare GeoJSON for choropleth
"""
import urllib.request
import json
import sys
from pathlib import Path

print("="*60)
print("CHOROPLETH GEOJSON SETUP")
print("="*60)

# Create directory
data_dir = Path("public/data")
data_dir.mkdir(parents=True, exist_ok=True)
print(f"\n1. Created directory: {data_dir}")

# Download
url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
raw_file = data_dir / "countries-raw.geojson"

print(f"\n2. Downloading from Natural Earth...")
print(f"   URL: {url}")

try:
    urllib.request.urlretrieve(url, raw_file)
    print(f"   Downloaded: {raw_file} ({raw_file.stat().st_size:,} bytes)")
except Exception as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

# Process IDs
print(f"\n3. Processing feature IDs...")

with open(raw_file, 'r', encoding='utf-8') as f:
    geojson = json.load(f)

# Special cases: Natural Earth has -99 for some countries
# Map by ADMIN name to ISO2
SPECIAL_ISO2_MAP = {
    'Norway': 'NO',
    'France': 'FR',
    'Kosovo': 'XK',
    'N. Cyprus': 'XC',  # Not official but useful for mapping
    'Somaliland': 'XS',  # Not official but useful for mapping
    'Northern Cyprus': 'XC',
    'Western Sahara': 'EH',
}

processed = 0
skipped = 0
iso_a2_count = 0
iso_a3_count = 0
special_count = 0

for feature in geojson.get('features', []):
    props = feature.get('properties', {})
    iso_a2 = props.get('ISO_A2', '')
    iso_a3 = props.get('ISO_A3', '')
    admin_name = props.get('ADMIN', '') or props.get('NAME', '')

    if iso_a2 and iso_a2 != '-99':
        feature['id'] = iso_a2
        processed += 1
        iso_a2_count += 1
    elif iso_a3 and iso_a3 != '-99':
        feature['id'] = iso_a3
        processed += 1
        iso_a3_count += 1
    elif admin_name in SPECIAL_ISO2_MAP:
        feature['id'] = SPECIAL_ISO2_MAP[admin_name]
        processed += 1
        special_count += 1
    else:
        skipped += 1
        print(f"   SKIPPED: {admin_name} (ISO_A2={iso_a2}, ISO_A3={iso_a3})")

output_file = data_dir / "countries-110m.geojson"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(geojson, f)

print(f"   Processed: {processed} features")
print(f"   - ISO_A2: {iso_a2_count}")
print(f"   - ISO_A3: {iso_a3_count}")
print(f"   - Special mappings: {special_count}")
print(f"   Skipped: {skipped}")
print(f"   Output: {output_file}")

print("\n" + "="*60)
print("SETUP COMPLETE!")
print("="*60)
print("\nNext steps:")
print("1. Start API: cd ../sofia-pulse/api && python -m uvicorn security-api:app --reload")
print("2. Start Frontend: npm run dev")
print("3. Open browser: http://localhost:3000")
print("4. Check console for logs")
