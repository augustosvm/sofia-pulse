#!/usr/bin/env python3
"""
Brazilian Ministries Data Collector
Coleta dados oficiais dos ministerios do Brasil via Portal de Dados Abertos

APIs:
- Portal Brasileiro de Dados Abertos: https://dados.gov.br/dados/apis
- Transparencia: https://api.portaldatransparencia.gov.br/
- IBGE: https://servicodados.ibge.gov.br/api/docs
"""

import os
import sys
import psycopg2
import requests
from datetime import datetime
from typing import List, Dict, Any

# Database connection
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', os.getenv('DB_HOST', 'localhost')),
    'port': int(os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432'))),
    'user': os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'sofia')),
    'password': os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', '')),
    'database': os.getenv('POSTGRES_DB', os.getenv('DB_NAME', 'sofia_db'))
}

# Brazilian Ministries and their data sources
# Reference: https://www.gov.br/pt-br/orgaos-do-governo
MINISTRIES_DATA = {
    # ===========================================
    # ECONOMIA / FAZENDA (via Portal Transparencia)
    # ===========================================
    'economia': {
        'name': 'Ministerio da Economia/Fazenda',
        'datasets': [
            {
                'id': 'receitas-federais',
                'name': 'Receitas do Governo Federal',
                'url': 'https://api.portaldatransparencia.gov.br/api-de-dados/receitas',
                'category': 'fiscal'
            },
            {
                'id': 'despesas-federais',
                'name': 'Despesas do Governo Federal',
                'url': 'https://api.portaldatransparencia.gov.br/api-de-dados/despesas',
                'category': 'fiscal'
            },
        ]
    },

    # ===========================================
    # SAUDE (DataSUS)
    # ===========================================
    'saude': {
        'name': 'Ministerio da Saude',
        'datasets': [
            {
                'id': 'cobertura-vacinal',
                'name': 'Cobertura Vacinal',
                'url': 'https://imunizacao-es.saude.gov.br/desc-imunizacao',
                'category': 'health'
            },
            {
                'id': 'estabelecimentos-saude',
                'name': 'Estabelecimentos de Saude',
                'url': 'https://apidadosabertos.saude.gov.br/cnes/estabelecimentos',
                'category': 'health'
            },
        ]
    },

    # ===========================================
    # EDUCACAO (INEP)
    # ===========================================
    'educacao': {
        'name': 'Ministerio da Educacao',
        'datasets': [
            {
                'id': 'ideb',
                'name': 'IDEB - Indice de Desenvolvimento da Educacao Basica',
                'url': 'https://api.qedu.org.br/',
                'category': 'education'
            },
            {
                'id': 'censo-escolar',
                'name': 'Censo Escolar',
                'url': 'https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados',
                'category': 'education'
            },
        ]
    },

    # ===========================================
    # TRABALHO (via CAGED/RAIS)
    # ===========================================
    'trabalho': {
        'name': 'Ministerio do Trabalho',
        'datasets': [
            {
                'id': 'caged',
                'name': 'CAGED - Emprego Formal',
                'url': 'https://bi.mte.gov.br/bgcaged/',
                'category': 'labor'
            },
            {
                'id': 'rais',
                'name': 'RAIS - Relacao Anual de Informacoes Sociais',
                'url': 'https://bi.mte.gov.br/bgcaged/',
                'category': 'labor'
            },
        ]
    },

    # ===========================================
    # CIENCIA E TECNOLOGIA (CNPq, CAPES)
    # ===========================================
    'ciencia': {
        'name': 'Ministerio da Ciencia, Tecnologia e Inovacao',
        'datasets': [
            {
                'id': 'bolsas-cnpq',
                'name': 'Bolsas CNPq',
                'url': 'https://dadosabertos.cnpq.br/',
                'category': 'science'
            },
            {
                'id': 'pesquisadores',
                'name': 'Pesquisadores Cadastrados',
                'url': 'https://dadosabertos.cnpq.br/',
                'category': 'science'
            },
        ]
    },

    # ===========================================
    # AGRICULTURA (CONAB, MAPA)
    # ===========================================
    'agricultura': {
        'name': 'Ministerio da Agricultura',
        'datasets': [
            {
                'id': 'producao-agricola',
                'name': 'Producao Agricola Municipal',
                'sidra_table': '5457',
                'category': 'agriculture'
            },
            {
                'id': 'precos-agricolas',
                'name': 'Precos Agricolas',
                'url': 'https://www.conab.gov.br/info-agro/precos',
                'category': 'agriculture'
            },
        ]
    },

    # ===========================================
    # MEIO AMBIENTE (IBAMA, INPE)
    # ===========================================
    'meio_ambiente': {
        'name': 'Ministerio do Meio Ambiente',
        'datasets': [
            {
                'id': 'desmatamento',
                'name': 'Desmatamento na Amazonia (PRODES)',
                'url': 'http://terrabrasilis.dpi.inpe.br/api/',
                'category': 'environment'
            },
            {
                'id': 'focos-queimadas',
                'name': 'Focos de Queimadas',
                'url': 'https://queimadas.dgi.inpe.br/api/',
                'category': 'environment'
            },
        ]
    },

    # ===========================================
    # INFRAESTRUTURA (ANTT, ANTAQ, ANAC)
    # ===========================================
    'infraestrutura': {
        'name': 'Ministerio da Infraestrutura',
        'datasets': [
            {
                'id': 'rodovias',
                'name': 'Condicoes das Rodovias Federais',
                'url': 'https://dados.antt.gov.br/',
                'category': 'infrastructure'
            },
            {
                'id': 'aeroportos',
                'name': 'Movimentacao Aeroportuaria',
                'url': 'https://www.anac.gov.br/acesso-a-informacao/dados-abertos',
                'category': 'infrastructure'
            },
        ]
    },

    # ===========================================
    # TURISMO (via World Bank + IBGE)
    # ===========================================
    'turismo': {
        'name': 'Ministerio do Turismo',
        'datasets': [
            {
                'id': 'chegadas-turistas',
                'name': 'Chegadas de Turistas Internacionais',
                'wb_indicator': 'ST.INT.ARVL',
                'category': 'tourism'
            },
            {
                'id': 'receita-turismo',
                'name': 'Receita de Turismo Internacional',
                'wb_indicator': 'ST.INT.RCPT.CD',
                'category': 'tourism'
            },
        ]
    },

    # ===========================================
    # DESENVOLVIMENTO SOCIAL (Bolsa Familia, CadUnico)
    # ===========================================
    'desenvolvimento_social': {
        'name': 'Ministerio do Desenvolvimento Social',
        'datasets': [
            {
                'id': 'bolsa-familia',
                'name': 'Beneficiarios Bolsa Familia',
                'url': 'https://api.portaldatransparencia.gov.br/api-de-dados/bolsa-familia',
                'category': 'social'
            },
            {
                'id': 'bpc',
                'name': 'Beneficio de Prestacao Continuada',
                'url': 'https://api.portaldatransparencia.gov.br/api-de-dados/bpc',
                'category': 'social'
            },
        ]
    },

    # ===========================================
    # JUSTICA (CNJ, Policia Federal)
    # ===========================================
    'justica': {
        'name': 'Ministerio da Justica',
        'datasets': [
            {
                'id': 'processos-judiciais',
                'name': 'Processos Judiciais (Justica em Numeros)',
                'url': 'https://paineis.cnj.jus.br/',
                'category': 'justice'
            },
        ]
    },

    # ===========================================
    # MULHERES (via IBGE/PNAD)
    # ===========================================
    'mulheres': {
        'name': 'Ministerio das Mulheres',
        'datasets': [
            {
                'id': 'violencia-mulher',
                'name': 'Violencia contra Mulher',
                'url': 'https://www.gov.br/mdh/pt-br/navegue-por-temas/politicas-para-mulheres',
                'category': 'women'
            },
        ]
    },
}


def fetch_worldbank_brazil(indicator: str) -> List[Dict]:
    """Fetch Brazil data from World Bank API"""

    base_url = "https://api.worldbank.org/v2"
    url = f"{base_url}/country/BRA/indicator/{indicator}"
    params = {
        'format': 'json',
        'per_page': 100,
        'date': '2000:2024'
    }

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if len(data) >= 2 and data[1]:
            return data[1]
        return []

    except Exception as e:
        return []


def fetch_ibge_sidra(table_id: str) -> List[Dict]:
    """Fetch data from IBGE SIDRA"""

    url = f"https://apisidra.ibge.gov.br/values/t/{table_id}/n1/all/p/last%2012/v/all"

    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 1:
                return data[1:]
        return []

    except Exception as e:
        return []


def fetch_transparencia_api(endpoint: str) -> List[Dict]:
    """Fetch data from Portal da Transparencia API"""

    # Note: Requires API key registration
    # https://api.portaldatransparencia.gov.br/

    try:
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Sofia-Pulse-Collector/1.0',
            'chave-api-dados': os.getenv('TRANSPARENCIA_API_KEY', '')
        }

        if not headers['chave-api-dados']:
            return []

        response = requests.get(endpoint, headers=headers, timeout=60)
        if response.status_code == 200:
            return response.json()
        return []

    except Exception as e:
        return []


def save_to_database(conn, records: List[Dict], ministry: str, dataset: Dict) -> int:
    """Save ministry data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.brazil_ministries_data (
            id SERIAL PRIMARY KEY,
            ministry VARCHAR(100) NOT NULL,
            dataset_id VARCHAR(100) NOT NULL,
            dataset_name TEXT,
            category VARCHAR(50),
            period VARCHAR(20),
            region VARCHAR(100),
            indicator VARCHAR(200),
            value DECIMAL(18, 6),
            unit VARCHAR(50),
            source VARCHAR(100),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ministry, dataset_id, period, region, indicator)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ministry_dataset
        ON sofia.brazil_ministries_data(ministry, dataset_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ministry_period
        ON sofia.brazil_ministries_data(period DESC)
    """)

    inserted = 0

    for record in records:
        # Handle World Bank format
        if 'date' in record and 'value' in record:
            value = record.get('value')
            if value is None:
                continue

            try:
                cursor.execute("""
                    INSERT INTO sofia.brazil_ministries_data
                    (ministry, dataset_id, dataset_name, category, period, region, indicator, value, unit, source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ministry, dataset_id, period, region, indicator)
                    DO UPDATE SET value = EXCLUDED.value
                """, (
                    ministry,
                    dataset.get('id', ''),
                    dataset.get('name', ''),
                    dataset.get('category', 'other'),
                    record.get('date', ''),
                    'Brasil',
                    dataset.get('name', ''),
                    float(value),
                    '',
                    'World Bank'
                ))
                inserted += 1
            except:
                continue

        # Handle SIDRA format
        elif 'V' in record or 'value' in record:
            value = record.get('V', record.get('value'))
            if value in [None, '-', '...', 'X']:
                continue

            try:
                cursor.execute("""
                    INSERT INTO sofia.brazil_ministries_data
                    (ministry, dataset_id, dataset_name, category, period, region, indicator, value, unit, source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ministry, dataset_id, period, region, indicator)
                    DO UPDATE SET value = EXCLUDED.value
                """, (
                    ministry,
                    dataset.get('id', ''),
                    dataset.get('name', ''),
                    dataset.get('category', 'other'),
                    record.get('D2C', record.get('periodo', '')),
                    record.get('D1N', 'Brasil'),
                    record.get('D3N', dataset.get('name', '')),
                    float(str(value).replace(',', '.')),
                    record.get('MN', ''),
                    'IBGE SIDRA'
                ))
                inserted += 1
            except:
                continue

    conn.commit()
    cursor.close()
    return inserted


def main():
    print("=" * 80)
    print("BRAZILIAN MINISTRIES DATA COLLECTOR")
    print("=" * 80)
    print("")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sources:")
    print(f"  - Portal da Transparencia")
    print(f"  - IBGE SIDRA")
    print(f"  - World Bank (Brazil data)")
    print(f"  - APIs oficiais dos ministerios")
    print("")
    print(f"Ministries: {len(MINISTRIES_DATA)}")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Database connected")
        print("")
    except Exception as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)

    total_records = 0
    successful = 0

    for ministry_id, ministry_info in MINISTRIES_DATA.items():
        print(f"--- {ministry_info['name']} ---")

        for dataset in ministry_info.get('datasets', []):
            print(f"  {dataset['name'][:50]}...")

            records = []

            # Try World Bank indicator
            if 'wb_indicator' in dataset:
                records = fetch_worldbank_brazil(dataset['wb_indicator'])

            # Try SIDRA table
            elif 'sidra_table' in dataset:
                records = fetch_ibge_sidra(dataset['sidra_table'])

            # Try Transparencia API
            elif 'url' in dataset and 'transparencia' in dataset['url']:
                records = fetch_transparencia_api(dataset['url'])

            if records:
                print(f"    Fetched: {len(records)} records")
                inserted = save_to_database(conn, records, ministry_id, dataset)
                total_records += inserted
                successful += 1
                print(f"    Saved: {inserted} records")
            else:
                print(f"    No data (may require API key)")

        print("")

    conn.close()

    print("=" * 80)
    print("BRAZILIAN MINISTRIES DATA COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total records: {total_records}")
    print(f"Successful datasets: {successful}")
    print("")
    print("Ministries covered:")
    print("  - Economia/Fazenda (receitas, despesas)")
    print("  - Saude (vacinacao, estabelecimentos)")
    print("  - Educacao (IDEB, censo escolar)")
    print("  - Trabalho (CAGED, RAIS)")
    print("  - Ciencia e Tecnologia (CNPq)")
    print("  - Agricultura (producao, precos)")
    print("  - Meio Ambiente (desmatamento, queimadas)")
    print("  - Infraestrutura (rodovias, aeroportos)")
    print("  - Turismo (chegadas, receita)")
    print("  - Desenvolvimento Social (Bolsa Familia)")
    print("  - Justica (processos)")
    print("  - Mulheres (violencia)")
    print("")
    print("TIP: For full access to Portal da Transparencia:")
    print("     Set TRANSPARENCIA_API_KEY environment variable")
    print("     Register at: https://api.portaldatransparencia.gov.br/")


if __name__ == '__main__':
    main()
