#!/usr/bin/env python3
"""
Análise completa dos collectors:
1. Identificar campos de NOME (persons vs organizations)
2. Identificar campos de LOCALIZAÇÃO (country, state, city)
3. Mapear para migração
"""
import os
import re
from collections import defaultdict

def analyze_collector(filepath):
    """Analisa um collector Python"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    result = {
        'file': os.path.basename(filepath),
        'has_name_fields': [],
        'has_location_fields': [],
        'table_name': None,
        'uses_normalize_location': False,
        'entity_type': None  # 'person', 'organization', 'mixed', 'other'
    }

    # Find table name
    table_match = re.search(r'CREATE TABLE IF NOT EXISTS sofia\.(\w+)', content)
    if table_match:
        result['table_name'] = table_match.group(1)

    # Check if uses normalize_location
    result['uses_normalize_location'] = 'normalize_location(conn' in content

    # Find INSERT statements and extract field names
    insert_patterns = [
        r'INSERT INTO sofia\.\w+\s*\((.*?)\)\s*VALUES',
        r'cursor\.execute\(["\']INSERT INTO.*?\((.*?)\)',
    ]

    all_fields = set()
    for pattern in insert_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            fields = match.group(1)
            # Clean and split fields
            fields = re.sub(r'\s+', ' ', fields)
            field_list = [f.strip() for f in fields.split(',')]
            all_fields.update(field_list)

    # Classify name fields
    name_patterns = {
        'person': [
            'person_name', 'author_name', 'speaker_name', 'player_name',
            'athlete_name', 'researcher_name', 'scientist_name', 'first_name',
            'last_name', 'full_name', 'contact_name', 'governor_name'
        ],
        'organization': [
            'company_name', 'organization_name', 'institution_name', 'university_name',
            'bank_name', 'central_bank_name', 'federation_name', 'ngo_name',
            'ministry_name', 'agency_name', 'department_name', 'employer_name',
            'client_name', 'sponsor_name', 'partner_name', 'venue_name'
        ],
        'ambiguous': [
            'name', 'title', 'source_name', 'event_name', 'project_name'
        ]
    }

    for field in all_fields:
        field_lower = field.lower()

        # Check name fields
        for category, patterns in name_patterns.items():
            if any(pattern in field_lower for pattern in patterns):
                result['has_name_fields'].append({
                    'field': field,
                    'category': category
                })

        # Check location fields
        location_keywords = [
            'country', 'state', 'city', 'location', 'region',
            'address', 'place', 'venue', 'geographic'
        ]
        if any(keyword in field_lower for keyword in location_keywords):
            result['has_location_fields'].append(field)

    # Determine entity type
    person_count = sum(1 for f in result['has_name_fields'] if f['category'] == 'person')
    org_count = sum(1 for f in result['has_name_fields'] if f['category'] == 'organization')

    if person_count > 0 and org_count > 0:
        result['entity_type'] = 'mixed'
    elif person_count > 0:
        result['entity_type'] = 'person'
    elif org_count > 0:
        result['entity_type'] = 'organization'
    elif result['has_name_fields']:
        result['entity_type'] = 'ambiguous'
    else:
        result['entity_type'] = 'other'

    return result

def main():
    print("=" * 100)
    print("ANÁLISE COMPLETA DOS COLLECTORS - NOMES E LOCALIZAÇÃO")
    print("=" * 100)
    print()

    collectors_dir = 'scripts'
    results = []

    # Analyze all Python collectors
    for filename in sorted(os.listdir(collectors_dir)):
        if filename.startswith('collect-') and filename.endswith('.py'):
            filepath = os.path.join(collectors_dir, filename)
            result = analyze_collector(filepath)
            if result['has_name_fields'] or result['has_location_fields']:
                results.append(result)

    # Group by entity type
    by_entity_type = defaultdict(list)
    for r in results:
        by_entity_type[r['entity_type']].append(r)

    print("=" * 100)
    print("1. COLLECTORS COM CAMPOS DE NOME (Candidatos para Persons/Organizations)")
    print("=" * 100)
    print()

    for entity_type in ['person', 'organization', 'mixed', 'ambiguous']:
        collectors = by_entity_type[entity_type]
        if not collectors:
            continue

        print(f"\n{'━' * 100}")
        print(f"📋 {entity_type.upper()} ({len(collectors)} collectors)")
        print(f"{'━' * 100}\n")

        for r in collectors:
            norm_status = "✅ USA normalize_location" if r['uses_normalize_location'] else "❌ NÃO normaliza"
            print(f"🔹 {r['file']}")
            print(f"   Tabela: {r['table_name'] or 'N/A'}")
            print(f"   {norm_status}")

            if r['has_name_fields']:
                print(f"   Campos de nome:")
                for field_info in r['has_name_fields']:
                    print(f"     • {field_info['field']} ({field_info['category']})")

            if r['has_location_fields']:
                print(f"   Campos de localização: {', '.join(r['has_location_fields'][:5])}")
                if len(r['has_location_fields']) > 5:
                    print(f"     ... e mais {len(r['has_location_fields']) - 5}")

            print()

    print("\n" + "=" * 100)
    print("2. COLLECTORS COM LOCALIZAÇÃO (Precisam de Normalização)")
    print("=" * 100)
    print()

    location_collectors = [r for r in results if r['has_location_fields']]

    needs_normalization = [r for r in location_collectors if not r['uses_normalize_location']]
    already_normalized = [r for r in location_collectors if r['uses_normalize_location']]

    print(f"✅ JÁ NORMALIZADOS: {len(already_normalized)}/{len(location_collectors)}")
    print(f"❌ PRECISAM NORMALIZAR: {len(needs_normalization)}/{len(location_collectors)}")
    print()

    if needs_normalization:
        print("📋 COLLECTORS QUE PRECISAM DE NORMALIZAÇÃO:")
        print()
        for r in needs_normalization:
            print(f"  • {r['file']}")
            print(f"    Tabela: {r['table_name'] or 'N/A'}")
            print(f"    Localização: {', '.join(r['has_location_fields'][:3])}")
            if r['entity_type'] in ['person', 'organization', 'mixed']:
                print(f"    ⚠️  Também precisa migrar para {r['entity_type'].upper()}")
            print()

    print("\n" + "=" * 100)
    print("3. RESUMO EXECUTIVO")
    print("=" * 100)
    print()

    print(f"📊 ESTATÍSTICAS:")
    print(f"  Total de collectors analisados: {len(results)}")
    print(f"  Com campos de NOME: {len([r for r in results if r['has_name_fields']])}")
    print(f"  Com campos de LOCALIZAÇÃO: {len(location_collectors)}")
    print()

    print(f"🏢 ENTIDADES:")
    print(f"  Organizations: {len(by_entity_type['organization'])} collectors")
    print(f"  Persons: {len(by_entity_type['person'])} collectors")
    print(f"  Mixed (ambos): {len(by_entity_type['mixed'])} collectors")
    print(f"  Ambiguous: {len(by_entity_type['ambiguous'])} collectors")
    print()

    print(f"📍 NORMALIZAÇÃO GEOGRÁFICA:")
    print(f"  ✅ Já normalizados: {len(already_normalized)}")
    print(f"  ❌ Precisam normalizar: {len(needs_normalization)}")
    print(f"  📊 Cobertura: {len(already_normalized)/max(len(location_collectors), 1)*100:.1f}%")
    print()

    print("=" * 100)
    print("4. AÇÕES RECOMENDADAS")
    print("=" * 100)
    print()

    print("✅ PRIORIDADE ALTA - Normalização Geográfica:")
    high_priority = [r for r in needs_normalization if len(r['has_location_fields']) > 2]
    for r in high_priority[:10]:
        print(f"  1. {r['file']} → {len(r['has_location_fields'])} campos geográficos")

    print()
    print("✅ PRIORIDADE ALTA - Migração para Organizations:")
    org_priority = [r for r in by_entity_type['organization'] if not r['uses_normalize_location']]
    for r in org_priority[:10]:
        print(f"  2. {r['file']} → {r['table_name']}")

    print()
    print("✅ PRIORIDADE MÉDIA - Migração para Persons:")
    person_priority = [r for r in by_entity_type['person'] if not r['uses_normalize_location']]
    for r in person_priority[:10]:
        print(f"  3. {r['file']} → {r['table_name']}")

if __name__ == '__main__':
    main()
