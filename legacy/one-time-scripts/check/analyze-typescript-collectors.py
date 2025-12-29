#!/usr/bin/env python3
"""
Análise dos collectors TypeScript
"""
import os
import re
from collections import defaultdict

def analyze_ts_collector(filepath):
    """Analisa um collector TypeScript"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    result = {
        'file': os.path.basename(filepath),
        'has_name_fields': [],
        'has_location_fields': [],
        'uses_normalize_location': False,
        'entity_type': None
    }

    # Check if uses normalizeLocation
    result['uses_normalize_location'] = 'normalizeLocation' in content

    # Find field names in the code
    # Look for object properties like { name: ..., company: ..., location: ... }
    field_patterns = [
        r'{\s*(\w+):\s*',  # { field: value }
        r'\.(\w+)\s*=\s*',  # obj.field = value
        r'INSERT INTO.*?\((.*?)\)',  # SQL INSERT
    ]

    all_fields = set()

    # Extract field names
    for pattern in field_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) > 0:
                field = match.group(1).strip()
                if field and not field.startswith('_'):
                    all_fields.add(field.lower())

    # Also look for specific patterns
    if 'companyName' in content or 'company_name' in content:
        all_fields.add('company_name')
    if 'organizationName' in content or 'organization_name' in content:
        all_fields.add('organization_name')
    if 'location' in content.lower():
        all_fields.add('location')
    if 'country' in content.lower():
        all_fields.add('country')
    if 'city' in content.lower():
        all_fields.add('city')

    # Classify fields
    name_patterns = {
        'organization': ['company', 'organization', 'employer', 'institution', 'venue'],
        'person': ['author', 'creator', 'developer', 'maintainer', 'owner'],
        'ambiguous': ['name', 'title']
    }

    for field in all_fields:
        for category, patterns in name_patterns.items():
            if any(p in field for p in patterns):
                result['has_name_fields'].append({
                    'field': field,
                    'category': category
                })

    # Location fields
    location_keywords = ['country', 'city', 'state', 'location', 'region', 'address']
    for field in all_fields:
        if any(k in field for k in location_keywords):
            result['has_location_fields'].append(field)

    # Determine entity type
    org_fields = [f for f in result['has_name_fields'] if f['category'] == 'organization']
    person_fields = [f for f in result['has_name_fields'] if f['category'] == 'person']

    if org_fields and person_fields:
        result['entity_type'] = 'mixed'
    elif org_fields:
        result['entity_type'] = 'organization'
    elif person_fields:
        result['entity_type'] = 'person'
    elif result['has_name_fields']:
        result['entity_type'] = 'ambiguous'

    return result

def main():
    print("=" * 100)
    print("ANÁLISE TYPESCRIPT COLLECTORS - NOMES E LOCALIZAÇÃO")
    print("=" * 100)
    print()

    collectors_dir = 'scripts'
    results = []

    # Analyze all TypeScript collectors
    for filename in sorted(os.listdir(collectors_dir)):
        if filename.startswith('collect-') and filename.endswith('.ts') and 'shared' not in filename:
            filepath = os.path.join(collectors_dir, filename)
            result = analyze_ts_collector(filepath)
            if result['has_name_fields'] or result['has_location_fields']:
                results.append(result)

    # Summary by normalization status
    with_norm = [r for r in results if r['uses_normalize_location']]
    without_norm = [r for r in results if not r['uses_normalize_location']]

    print(f"📊 RESUMO:")
    print(f"  Total collectors TypeScript: {len(results)}")
    print(f"  ✅ Com normalizeLocation: {len(with_norm)} ({len(with_norm)/max(len(results),1)*100:.1f}%)")
    print(f"  ❌ Sem normalizeLocation: {len(without_norm)} ({len(without_norm)/max(len(results),1)*100:.1f}%)")
    print()

    if without_norm:
        print("━" * 100)
        print("❌ COLLECTORS TYPESCRIPT SEM NORMALIZAÇÃO:")
        print("━" * 100)
        print()

        for r in without_norm:
            print(f"🔹 {r['file']}")
            if r['has_location_fields']:
                print(f"   Localização: {', '.join(r['has_location_fields'][:5])}")
            if r['has_name_fields']:
                orgs = [f['field'] for f in r['has_name_fields'] if f['category'] == 'organization']
                if orgs:
                    print(f"   Organizations: {', '.join(orgs[:3])}")
            print()

    print()
    print("=" * 100)
    print("AÇÃO REQUERIDA:")
    print("=" * 100)
    print()
    print(f"📋 {len(without_norm)} collectors TypeScript precisam de normalização geográfica")
    print()

if __name__ == '__main__':
    main()
