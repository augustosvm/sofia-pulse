#!/usr/bin/env python3
"""
Implementação automatizada de normalize_location para collectors simples
Apenas para collectors que têm country_code/country_name (não state/city)
"""
import os
import re

SIMPLE_COLLECTORS = {
    'collect-hdx-humanitarian.py': 'hdx_humanitarian_data',
    'collect-cepal-latam.py': 'cepal_latam_data',
    'collect-world-sports.py': 'world_sports_data',
}

def add_column_if_needed(content, table_name):
    """Add ALTER TABLE after CREATE TABLE if not exists"""
    # Find CREATE TABLE
    pattern = f'CREATE TABLE IF NOT EXISTS sofia\\.{table_name}'
    match = re.search(pattern, content)

    if not match:
        return content

    # Check if already has ALTER TABLE for country_id
    if 'ALTER TABLE' in content and 'country_id' in content:
        return content

    # Find the end of CREATE TABLE statement
    start = match.end()
    paren_count = 0
    in_parens = False
    end_pos = start

    for i in range(start, len(content)):
        if content[i] == '(':
            in_parens = True
            paren_count += 1
        elif content[i] == ')':
            paren_count -= 1
            if paren_count == 0 and in_parens:
                end_pos = i + 1
                break

    # Find next line after CREATE TABLE
    next_newline = content.find('\n', end_pos)
    if next_newline == -1:
        return content

    # Insert ALTER TABLE
    alter_sql = f'''
    # Add geographic normalization columns
    cursor.execute("""
        ALTER TABLE sofia.{table_name}
        ADD COLUMN IF NOT EXISTS country_id INTEGER REFERENCES sofia.countries(id)
    """)
'''

    return content[:next_newline] + alter_sql + content[next_newline:]

def add_normalization_before_insert(content):
    """Add normalize_location before INSERT statements"""

    # Pattern to find INSERT INTO
    pattern = r'(\s+)(cursor\.execute\(["\'])\s*(INSERT INTO sofia\.\w+)'

    def replace_func(match):
        indent = match.group(1)
        prefix = match.group(2)
        insert_stmt = match.group(3)

        # Add normalization code before INSERT
        norm_code = f'''{indent}# Normalize geographic location
{indent}location = normalize_location(conn, {{'country': country_code or country_name}})
{indent}country_id = location['country_id']

{indent}{prefix}{insert_stmt}'''

        return norm_code

    # Apply replacement
    result = re.sub(pattern, replace_func, content, count=1)  # Only first occurrence

    return result

def update_insert_fields(content, table_name):
    """Add country_id to INSERT fields and VALUES"""

    # Find INSERT INTO statement
    pattern = f'INSERT INTO sofia\\.{table_name}\\s*\\((.*?)\\)\\s*VALUES\\s*\\((.*?)\\)'

    def replace_func(match):
        fields = match.group(1)
        values = match.group(2)

        # Add country_id if not present
        if 'country_id' not in fields:
            # Add country_id after country fields
            new_fields = re.sub(
                r'(country_name|country_code)',
                r'\1, country_id',
                fields,
                count=1
            )
            # Add %s after last value placeholder
            new_values = values.rstrip() + ', %s'

            return f'INSERT INTO sofia.{table_name}\n({new_fields})\nVALUES ({new_values})'

        return match.group(0)

    result = re.sub(pattern, replace_func, content, flags=re.DOTALL)

    return result

def update_on_conflict(content):
    """Add country_id to ON CONFLICT DO UPDATE"""

    pattern = r'(ON CONFLICT.*?DO UPDATE SET.*?)'

    def replace_func(match):
        clause = match.group(1)
        if 'country_id' not in clause and 'EXCLUDED' in clause:
            # Add country_id update
            clause = clause.rstrip() + ', country_id = EXCLUDED.country_id'
        return clause

    result = re.sub(pattern, replace_func, content, flags=re.DOTALL)

    return result

def add_country_id_to_values(content):
    """Add country_id to the VALUES tuple"""

    # Find the closing parenthesis of VALUES tuple
    pattern = r'(\)\s*\)\s*inserted \+= 1)'

    def replace_func(match):
        return ',\ncountry_id\n' + match.group(1)

    result = re.sub(pattern, replace_func, content, count=1)

    return result

def process_collector(filepath, table_name):
    """Process a single collector file"""

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"\n🔹 {os.path.basename(filepath)}")

    # Step 1: Add ALTER TABLE
    content = add_column_if_needed(content, table_name)
    print("  ✅ ALTER TABLE added")

    # Step 2: Add normalization before INSERT
    new_content = add_normalization_before_insert(content)
    if new_content != content:
        content = new_content
        print("  ✅ normalize_location() added")
    else:
        print("  ⚠️  Could not auto-add normalization (manual needed)")
        return False

    # Step 3: Update INSERT fields
    content = update_insert_fields(content, table_name)
    print("  ✅ INSERT fields updated")

    # Step 4: Update ON CONFLICT
    content = update_on_conflict(content)
    print("  ✅ ON CONFLICT updated")

    # Step 5: Add country_id to values
    content = add_country_id_to_values(content)
    print("  ✅ VALUES updated")

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print("  💾 File saved")
    return True

def main():
    print("=" * 80)
    print("BATCH NORMALIZATION: Simple country-only collectors")
    print("=" * 80)

    success = 0
    failed = []

    for filename, table_name in SIMPLE_COLLECTORS.items():
        filepath = f'scripts/{filename}'

        if not os.path.exists(filepath):
            print(f"\n⚠️  Not found: {filename}")
            failed.append(filename)
            continue

        try:
            if process_collector(filepath, table_name):
                success += 1
            else:
                failed.append(filename)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed.append(filename)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Success: {success}/{len(SIMPLE_COLLECTORS)}")
    if failed:
        print(f"❌ Failed: {len(failed)}")
        for name in failed:
            print(f"  - {name}")

if __name__ == '__main__':
    main()
