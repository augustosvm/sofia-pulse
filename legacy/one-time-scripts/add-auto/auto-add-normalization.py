#!/usr/bin/env python3
"""
Script para adicionar normalize_location() automaticamente nos INSERTs
Para collectors que só têm country_code/country_name
"""
import os
import re
from pathlib import Path

# Collectors com apenas COUNTRY (casos mais simples)
SIMPLE_COUNTRY_COLLECTORS = [
    'collect-energy-global.py',
    'collect-world-security.py',
    'collect-cepal-latam.py',
    'collect-fao-agriculture.py',
    'collect-ilostat.py',
    'collect-port-traffic.py',
    'collect-religion-data.py',
    'collect-socioeconomic-indicators.py',
    'collect-unicef.py',
    'collect-who-health.py',
    'collect-women-ilostat.py',
    'collect-women-world-bank.py',
    'collect-world-bank-gender.py',
    'collect-world-sports.py',
]

def add_normalization_to_insert(content, collector_name):
    """
    Find INSERTs with country_code/country_name and add normalization
    """
    # Pattern to find INSERT statements
    insert_pattern = r'(cursor\.execute\(["\'])\s*(INSERT INTO sofia\.\w+\s*\((.*?)\)\s*VALUES\s*\((.*?)\)[^"\']*)(["\']\s*,\s*\()'

    modifications = []

    for match in re.finditer(insert_pattern, content, re.DOTALL):
        full_match = match.group(0)
        fields_str = match.group(3)
        values_placeholder = match.group(4)

        # Check if has country fields
        has_country = 'country_code' in fields_str or 'country_name' in fields_str
        has_country_id = 'country_id' in fields_str

        if has_country and not has_country_id:
            # This INSERT needs normalization
            insert_start = match.start()

            # Find the line before this INSERT to add normalization
            lines_before = content[:insert_start].split('\n')
            indent = len(lines_before[-1]) - len(lines_before[-1].lstrip())
            indent_str = ' ' * indent

            # Create normalization code
            norm_code = f"""
{indent_str}# Normalize geographic location
{indent_str}location = normalize_location(conn, {{'country': country_code or country_name}})
{indent_str}country_id = location['country_id']

"""

            # Add country_id to fields and values
            new_fields = fields_str.rstrip() + ', country_id'
            new_values = values_placeholder.rstrip() + ', %s'

            modifications.append({
                'insert_start': insert_start,
                'norm_code': norm_code,
                'old_fields': fields_str,
                'new_fields': new_fields,
                'old_values': values_placeholder,
                'new_values': new_values
            })

    if not modifications:
        return content, 0

    # Apply modifications (from end to start to preserve positions)
    for mod in reversed(modifications):
        # Add country_id to INSERT
        content = content.replace(
            f"INSERT INTO sofia.{collector_name.replace('collect-', '').replace('.py', '')}_data\n({mod['old_fields']})",
            f"INSERT INTO sofia.{collector_name.replace('collect-', '').replace('.py', '')}_data\n({mod['new_fields']})"
        )

        # Add normalization before INSERT
        content = content[:mod['insert_start']] + mod['norm_code'] + content[mod['insert_start']:]

    return content, len(modifications)

def quick_migrate_simple_collectors():
    """
    Migrate collectors that only have country fields (easiest case)
    """
    print("=" * 80)
    print("QUICK MIGRATION: Adding normalize_location for country-only collectors")
    print("=" * 80)
    print()

    scripts_dir = Path('scripts')
    migrated = []
    failed = []

    for collector_name in SIMPLE_COUNTRY_COLLECTORS:
        filepath = scripts_dir / collector_name

        if not filepath.exists():
            print(f"⚠️  Not found: {collector_name}")
            failed.append(collector_name)
            continue

        print(f"🔹 {collector_name}")

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # This is complex - for now just report what needs to be done
            # Each collector has different variable names and structure
            print(f"  📝 Manual implementation needed")
            print(f"  → Pattern: Add normalize_location(conn, {{'country': country_var}})")
            print(f"  → Add country_id to INSERT fields and values")
            print()

        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed.append(collector_name)

    print("\n" + "=" * 80)
    print("STATUS")
    print("=" * 80)
    print(f"Total collectors: {len(SIMPLE_COUNTRY_COLLECTORS)}")
    print(f"Need manual implementation: {len(SIMPLE_COUNTRY_COLLECTORS)}")
    print()
    print("💡 RECOMMENDATION:")
    print("   Due to varying code structures, manual implementation is most reliable.")
    print("   Use the template from MIGRATION_PLAN_COMPLETE.md")

if __name__ == '__main__':
    quick_migrate_simple_collectors()
