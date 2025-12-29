#!/usr/bin/env python3
"""
Script automatizado para adicionar normalize_location() em todos os collectors pendentes
"""
import os
import re
from pathlib import Path

# Collectors pendentes (baseado na análise anterior)
PYTHON_COLLECTORS = [
    'collect-acled-conflicts.py',
    'collect-drugs-data.py',
    'collect-energy-global.py',
    'collect-mdic-comexstat.py',
    'collect-sports-regional.py',
    'collect-world-security.py',
    'collect-cepal-latam.py',
    'collect-electricity-consumption.py',
    'collect-energy-consumption.py',
    'collect-fao-agriculture.py',
    'collect-hdx-humanitarian.py',
    'collect-ilostat.py',
    'collect-port-traffic.py',
    'collect-religion-data.py',
    'collect-sec-edgar-funding.py',
    'collect-semiconductor-sales.py',
    'collect-socioeconomic-indicators.py',
    'collect-sports-federations.py',
    'collect-unicef.py',
    'collect-who-health.py',
    'collect-women-brazil.py',
    'collect-women-fred.py',
    'collect-women-ilostat.py',
    'collect-women-world-bank.py',
    'collect-world-bank-gender.py',
    'collect-world-ngos.py',
    'collect-world-sports.py',
]

def has_normalize_import(content):
    """Check if file already has normalize_location import"""
    return 'from shared.geo_helpers import normalize_location' in content or 'from geo_helpers import normalize_location' in content

def add_normalize_import(content):
    """Add normalize_location import at the top"""
    if has_normalize_import(content):
        return content

    # Find the shebang and add import after it
    lines = content.split('\n')
    insert_pos = 0

    # Find first line after shebang/comments
    for i, line in enumerate(lines):
        if line.startswith('#!') or (line.startswith('#') and not line.startswith('"""')):
            insert_pos = i + 1
        elif line.startswith('"""') or line.startswith("'''"):
            # Skip docstring
            insert_pos = i
            break
        elif line.strip() and not line.startswith('#'):
            insert_pos = i
            break

    # Insert the import
    lines.insert(insert_pos, 'from shared.geo_helpers import normalize_location')
    if insert_pos > 0 and lines[insert_pos - 1].strip():
        lines.insert(insert_pos, '')  # Add blank line

    return '\n'.join(lines)

def find_inserts_needing_normalization(content):
    """Find INSERT statements that have country/state/city fields but no normalize_location"""
    pattern = r'INSERT INTO sofia\.\w+\s*\((.*?)\)\s*VALUES.*?\((.*?)\)'
    matches = []

    for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
        fields_str = match.group(1)

        # Check if has geographic fields
        has_geo = any(keyword in fields_str.lower() for keyword in ['country_code', 'country_name', 'state', 'city', 'region'])
        has_id_fields = 'country_id' in fields_str.lower()

        if has_geo and not has_id_fields:
            matches.append({
                'start': match.start(),
                'end': match.end(),
                'full_text': match.group(0),
                'fields': fields_str
            })

    return matches

def migrate_collector(filepath):
    """Add normalization to a collector file"""
    print(f"\n🔹 Processing: {os.path.basename(filepath)}")

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        original_content = f.read()

    # Check if already has import
    if not has_normalize_import(original_content):
        print("  ✅ Adding normalize_location import")
        content = add_normalize_import(original_content)
    else:
        print("  ✓ Already has import")
        content = original_content

    # Find INSERTs that need normalization
    inserts = find_inserts_needing_normalization(content)

    if inserts:
        print(f"  ⚠️  Found {len(inserts)} INSERT statements without normalization")
        print(f"  → Manual review needed for this collector")
        return False
    else:
        print("  ✓ No INSERTs need updating (or already normalized)")

    # Write back if changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print("  💾 File updated")
        return True

    return False

def main():
    print("=" * 80)
    print("AUTO-MIGRATION: Adding normalize_location to collectors")
    print("=" * 80)

    scripts_dir = Path('scripts')
    updated_count = 0
    needs_manual = []

    for collector_name in PYTHON_COLLECTORS:
        filepath = scripts_dir / collector_name

        if not filepath.exists():
            print(f"\n⚠️  Not found: {collector_name}")
            continue

        was_updated = migrate_collector(filepath)
        if was_updated:
            updated_count += 1
        else:
            needs_manual.append(collector_name)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Collectors processed: {len(PYTHON_COLLECTORS)}")
    print(f"Imports added: {updated_count}")
    print(f"Need manual review: {len(needs_manual)}")

    if needs_manual:
        print("\n📋 Collectors needing manual INSERT updates:")
        for name in needs_manual:
            print(f"  - {name}")

    print("\n✅ Phase 1 complete: Imports added")
    print("📝 Phase 2 needed: Update INSERT statements manually for collectors above")

if __name__ == '__main__':
    main()
