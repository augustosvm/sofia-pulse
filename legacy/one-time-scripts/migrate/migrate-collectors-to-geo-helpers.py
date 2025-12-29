#!/usr/bin/env python3
"""
Migra collectors Python para usar geo_helpers automaticamente
"""
import re
import os

COLLECTORS_TO_MIGRATE = [
    'collect-basedosdados.py',
    'collect-brazil-ministries.py',
    'collect-brazil-security.py',
    'collect-central-banks-women.py',
    'collect-cepal-latam.py',
    'collect-cni-indicators.py',
    'collect-drugs-data.py',
    'collect-fao-agriculture.py',
    'collect-fiesp-data.py',
    'collect-ilostat.py',
    'collect-mdic-comexstat.py',
    'collect-port-traffic.py',
    'collect-religion-data.py',
    'collect-socioeconomic-indicators.py',
    'collect-unicef.py',
    'collect-who-health.py',
    'collect-women-brazil.py',
    'collect-women-eurostat.py',
    'collect-women-fred.py',
    'collect-women-ilostat.py',
    'collect-women-world-bank.py',
    'collect-world-bank-gender.py',
    'collect-world-ngos.py',
    'collect-world-security.py',
    'collect-world-sports.py',
    'collect-world-tourism.py',
]

def add_geo_helpers_import(content):
    """Adiciona import de geo_helpers se não existir"""
    if 'geo_helpers' in content:
        return content, False

    # Encontra a última linha de import
    import_lines = []
    other_lines = []
    in_imports = True

    for line in content.split('\n'):
        if in_imports and (line.startswith('import ') or line.startswith('from ') or line.strip() == '' or line.startswith('#')):
            import_lines.append(line)
        else:
            in_imports = False
            other_lines.append(line)

    # Adiciona o import de geo_helpers
    import_lines.append('from shared.geo_helpers import normalize_location')
    import_lines.append('')

    return '\n'.join(import_lines + other_lines), True

def migrate_collector(filepath):
    """Migra um collector para usar geo_helpers"""
    print(f"\n{'='*60}")
    print(f"Migrando: {os.path.basename(filepath)}")
    print('='*60)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 1. Adicionar import
        content, import_added = add_geo_helpers_import(content)

        if import_added:
            print("✅ Adicionado import de geo_helpers")

            # Salvar arquivo modificado
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✅ Arquivo atualizado: {filepath}")
            return True
        else:
            print("⚠️  Já usa geo_helpers, pulando...")
            return False

    except Exception as e:
        print(f"❌ Erro ao migrar {filepath}: {e}")
        return False

def main():
    base_path = '/mnt/c/Users/augusto.moreira/Documents/sofia-pulse/scripts'

    print("🔄 Iniciando migração de collectors para geo_helpers\n")
    print(f"📊 Total de collectors: {len(COLLECTORS_TO_MIGRATE)}\n")

    migrated = 0
    skipped = 0
    errors = 0

    for collector_name in COLLECTORS_TO_MIGRATE:
        filepath = os.path.join(base_path, collector_name)

        if not os.path.exists(filepath):
            print(f"⚠️  Arquivo não encontrado: {collector_name}")
            skipped += 1
            continue

        result = migrate_collector(filepath)

        if result:
            migrated += 1
        else:
            skipped += 1

    print(f"\n{'='*60}")
    print("📊 RESUMO DA MIGRAÇÃO")
    print('='*60)
    print(f"✅ Migrados: {migrated}")
    print(f"⏭️  Pulados: {skipped}")
    print(f"❌ Erros: {errors}")
    print(f"\n⚠️  ATENÇÃO: Os collectors foram atualizados com o import.")
    print(f"⚠️  Você ainda precisa adicionar normalize_location() antes dos INSERTs manualmente.")
    print(f"⚠️  Ou usar um script mais avançado para fazer isso automaticamente.")

if __name__ == '__main__':
    main()
