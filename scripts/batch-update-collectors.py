#!/usr/bin/env python3
"""
Script para atualizar múltiplos coletores Python em batch
Aplica normalização geográfica automaticamente
"""

import re
from pathlib import Path

# Coletores para atualizar
COLLECTORS = [
    "collect-rapidapi-activejobs.py",
    "collect-serpapi-googlejobs.py",
    "collect-freejobs-api.py",
    "collect-rapidapi-linkedin.py",
    "collect-theirstack-api.py",
]

# Template de import
IMPORT_TEMPLATE = """import sys
from pathlib import Path

# Import geo helpers
sys.path.insert(0, str(Path(__file__).parent / 'shared'))
from geo_helpers import normalize_location
"""

# Template de normalização
NORMALIZE_TEMPLATE = """            # Parse location
            location_str = job.get('location', '')
            parts = location_str.split(',') if location_str else []
            city = parts[0].strip() if len(parts) > 0 else None
            country = parts[-1].strip() if len(parts) > 0 else 'Brazil'
            
            # Normalize geographic data
            geo = normalize_location(conn, {
                'country': country,
                'city': city
            })
            """


def update_collector(filepath):
    """Atualiza um coletor com normalização geográfica"""
    print(f"Atualizando {filepath.name}...")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Já tem normalização?
    if "normalize_location" in content:
        print(f"  ✅ Já normalizado")
        return False

    # Adicionar import
    if "from dotenv import load_dotenv" in content:
        content = content.replace(
            "from dotenv import load_dotenv", f"from dotenv import load_dotenv\n{IMPORT_TEMPLATE}"
        )

    # Adicionar normalização antes do INSERT
    # Procurar padrão: for job in jobs: try: cur.execute("""
    pattern = r'(for job in jobs:\s+try:\s+)(cur\.execute\(""")'
    if re.search(pattern, content):
        content = re.sub(pattern, r"\1" + NORMALIZE_TEMPLATE + r"\2", content)

    # Atualizar INSERT para incluir country_id, city_id
    # Procurar: INSERT INTO sofia.jobs (
    insert_pattern = r"INSERT INTO sofia\.jobs \(\s+job_id, title, company, location,"
    if re.search(insert_pattern, content):
        content = re.sub(
            insert_pattern,
            "INSERT INTO sofia.jobs (\n                    job_id, title, company, location, city, country, country_id, city_id,",
            content,
        )

    # Atualizar VALUES
    # Adicionar city, country, geo['country_id'], geo['city_id'] após location
    values_pattern = r"job\['location'\],"
    if re.search(values_pattern, content):
        content = re.sub(
            values_pattern,
            "job['location'],\n                city, country, geo['country_id'], geo['city_id'],",
            content,
        )

    # Salvar
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  ✅ Atualizado")
    return True


def main():
    scripts_dir = Path(__file__).parent
    updated = 0

    for collector in COLLECTORS:
        filepath = scripts_dir / collector
        if filepath.exists():
            if update_collector(filepath):
                updated += 1
        else:
            print(f"⚠️  {collector} não encontrado")

    print(f"\n✅ {updated}/{len(COLLECTORS)} coletores atualizados")


if __name__ == "__main__":
    main()
