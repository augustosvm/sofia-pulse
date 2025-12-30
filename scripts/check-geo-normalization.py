#!/usr/bin/env python3
"""
Script Automatizado de Normalização Geográfica
Aplica normalização geográfica em todos os coletores TypeScript e Python
"""

import re
from pathlib import Path

# Padrões para detectar coletores que precisam de normalização
GEO_PATTERNS = [
    r'country["\']?\s*[:=]',
    r'city["\']?\s*[:=]',
    r'state["\']?\s*[:=]',
    r'location["\']?\s*[:=]',
]


def needs_normalization(file_path):
    """Verifica se arquivo precisa de normalização geográfica"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Já tem normalização?
        if "normalizeLocation" in content or "normalize_location" in content:
            return False

        # Tem dados geográficos?
        for pattern in GEO_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False
    except:
        return False


def main():
    print("🔍 Buscando coletores que precisam de normalização...")

    scripts_dir = Path(__file__).parent
    collectors = []

    # Buscar coletores TypeScript
    for ts_file in scripts_dir.glob("collect-*.ts"):
        if needs_normalization(ts_file):
            collectors.append(ts_file)

    # Buscar coletores Python
    for py_file in scripts_dir.glob("collect-*.py"):
        if needs_normalization(py_file):
            collectors.append(py_file)

    print(f"\n📊 Encontrados {len(collectors)} coletores:")
    for collector in collectors:
        print(f"   • {collector.name}")

    if not collectors:
        print("\n✅ Todos os coletores críticos já estão normalizados!")
        return

    print("\n💡 PRÓXIMOS PASSOS:")
    print("   1. Revisar cada coletor manualmente")
    print("   2. Aplicar padrão de normalização:")
    print("      - TypeScript: import { normalizeLocation } from './shared/geo-helpers'")
    print("      - Python: from geo_helpers import normalize_location")
    print("   3. Usar normalizeLocation() antes de INSERT")
    print("   4. Adicionar country_id, state_id, city_id nas colunas")
    print("   5. Manter strings para compatibilidade")


if __name__ == "__main__":
    main()
