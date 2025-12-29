#!/usr/bin/env python3
"""Find Python collectors that need geo_helpers migration"""
import os
import glob

print("=== Collectors que precisam de geo_helpers ===\n")

collectors = glob.glob("/mnt/c/Users/augusto.moreira/Documents/sofia-pulse/scripts/collect-*.py")
need_migration = []

for collector in sorted(collectors):
    with open(collector, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

        # Tem dados geográficos?
        has_geo = any(word in content.lower() for word in ['country', 'cidade', 'pais', 'state', 'city'])

        # Já usa geo_helpers?
        uses_geo_helpers = 'geo_helpers' in content

        if has_geo and not uses_geo_helpers:
            name = os.path.basename(collector)
            need_migration.append(name)
            print(f"❌ {name}")

print(f"\n📊 Total: {len(need_migration)} collectors precisam de migração")
