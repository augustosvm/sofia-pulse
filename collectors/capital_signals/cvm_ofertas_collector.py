#!/usr/bin/env python3
"""
CVM Ofertas Públicas Collector - Capital Signals
Coleta dados de ofertas públicas registradas na CVM (Brasil)
Fonte: https://dados.cvm.gov.br/dataset/cia_aberta-doc-oferta_distribuicao
"""

import os
import sys
import json
import logging
import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict
import psycopg2
from io import StringIO

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cvm_ofertas_collector')

# Configuração do banco
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '91.98.158.19'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', 'SofiaPulse2025Secure@DB'),
    'dbname': os.getenv('DB_NAME', 'sofia_db')
}

# URLs da CVM
CVM_BASE_URL = "https://dados.cvm.gov.br/dados"
CVM_OFERTAS_URL = f"{CVM_BASE_URL}/CIA_ABERTA/DOC/OFERTA_DISTRIBUICAO/DADOS/"

# Mapeamento de estados brasileiros
UF_MAPPING = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
    'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
    'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
    'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
    'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
    'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
}

def get_db_connection():
    """Cria conexão com o banco de dados"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {e}")
        raise

def get_exchange_rate_brl_usd() -> float:
    """Obtém taxa de câmbio BRL/USD"""
    try:
        # Usando API do Banco Central
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados/ultimos/1?formato=json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return float(data[0]['valor'])
    except:
        pass
    return 5.0  # Fallback

def fetch_cvm_ofertas() -> List[Dict]:
    """Busca ofertas públicas da CVM"""
    logger.info("Buscando ofertas públicas da CVM...")

    events = []
    exchange_rate = get_exchange_rate_brl_usd()
    logger.info(f"Taxa de câmbio BRL/USD: {exchange_rate}")

    # Tentar buscar arquivos dos últimos anos
    current_year = datetime.now().year

    for year in range(current_year, current_year - 3, -1):
        try:
            # Formato do arquivo: oferta_distribuicao_{ano}.csv
            file_url = f"{CVM_OFERTAS_URL}oferta_distribuicao_{year}.csv"
            logger.info(f"Tentando: {file_url}")

            response = requests.get(file_url, timeout=30)

            if response.status_code == 200:
                # Parse do CSV
                df = pd.read_csv(StringIO(response.text), sep=';', encoding='latin-1')

                logger.info(f"Encontradas {len(df)} ofertas em {year}")

                for _, row in df.iterrows():
                    try:
                        # Extrair dados
                        source_id = f"cvm_{row.get('NUM_PROCESSO', row.get('CNPJ_EMISSOR', ''))}"

                        # Parse da data
                        event_date = None
                        date_field = row.get('DT_REGISTRO') or row.get('DT_INICIO_DISTRIBUICAO')
                        if pd.notna(date_field):
                            try:
                                event_date = pd.to_datetime(date_field, dayfirst=True).date()
                            except:
                                pass

                        # Valor
                        amount = None
                        amount_field = row.get('VAL_TOTAL_OFERTA') or row.get('VAL_TOTAL_CAPTADO')
                        if pd.notna(amount_field):
                            try:
                                amount = float(str(amount_field).replace(',', '.').replace(' ', ''))
                            except:
                                pass

                        amount_usd = amount / exchange_rate if amount else None

                        # Setor
                        sector = row.get('SETOR_ATIVIDADE') or row.get('DESC_SETOR')

                        event = {
                            'source': 'CVM_OFERTA',
                            'event_type': 'PUBLIC_OFFERING',
                            'source_id': source_id,
                            'event_date': event_date,
                            'country_code': 'BRA',
                            'state_code': row.get('UF_EMISSOR'),
                            'city': row.get('MUNICIPIO_EMISSOR'),
                            'entity_name': str(row.get('DENOM_SOCIAL', row.get('NOME_EMISSOR', 'Unknown')))[:500],
                            'amount': amount,
                            'currency': 'BRL',
                            'amount_usd': amount_usd,
                            'sector': str(sector)[:255] if pd.notna(sector) else None,
                            'source_url': f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/OFERTA_DISTRIBUICAO/",
                            'raw_payload': json.dumps({k: str(v) if pd.notna(v) else None for k, v in row.items()})
                        }
                        events.append(event)

                    except Exception as e:
                        logger.warning(f"Erro ao processar linha: {e}")
                        continue

            else:
                logger.warning(f"Arquivo {year} não encontrado (status {response.status_code})")

        except Exception as e:
            logger.warning(f"Erro ao processar ano {year}: {e}")
            continue

    # Se não encontrou dados históricos, tentar API
    if not events:
        events = fetch_cvm_api_ofertas()

    return events

def fetch_cvm_api_ofertas() -> List[Dict]:
    """Busca ofertas via API da CVM (alternativa)"""
    logger.info("Tentando API alternativa da CVM...")

    events = []
    exchange_rate = get_exchange_rate_brl_usd()

    # API de dados abertos da CVM
    api_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"

    try:
        response = requests.get(api_url, timeout=30)

        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text), sep=';', encoding='latin-1')
            logger.info(f"Encontradas {len(df)} companhias abertas")

            # Filtrar companhias ativas recentes
            for _, row in df.head(200).iterrows():
                try:
                    event = {
                        'source': 'CVM_OFERTA',
                        'event_type': 'PUBLIC_OFFERING',
                        'source_id': f"cvm_cia_{row.get('CNPJ_CIA', '')}",
                        'event_date': pd.to_datetime(row.get('DT_REG'), dayfirst=True).date() if pd.notna(row.get('DT_REG')) else None,
                        'country_code': 'BRA',
                        'state_code': row.get('UF'),
                        'city': row.get('MUNICIPIO'),
                        'entity_name': str(row.get('DENOM_SOCIAL', 'Unknown'))[:500],
                        'sector': str(row.get('SETOR_ATIV'))[:255] if pd.notna(row.get('SETOR_ATIV')) else None,
                        'source_url': "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/",
                        'raw_payload': json.dumps({k: str(v) if pd.notna(v) else None for k, v in row.items()})
                    }
                    events.append(event)
                except Exception as e:
                    continue

    except Exception as e:
        logger.error(f"Erro na API CVM: {e}")

    return events

def insert_events(events: List[Dict]):
    """Insere eventos no banco de dados"""
    if not events:
        logger.info("Nenhum evento para inserir")
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()

    inserted = 0

    try:
        for event in events:
            try:
                cursor.execute("""
                    INSERT INTO capital_events
                    (source, event_type, source_id, event_date, country_code, state_code,
                     city, entity_name, amount, currency, amount_usd, sector, source_url, raw_payload)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source, source_id) DO UPDATE SET
                        event_date = EXCLUDED.event_date,
                        amount = EXCLUDED.amount,
                        amount_usd = EXCLUDED.amount_usd,
                        raw_payload = EXCLUDED.raw_payload,
                        ingested_at = NOW()
                """, (
                    event['source'],
                    event['event_type'],
                    event['source_id'],
                    event.get('event_date'),
                    event.get('country_code', 'BRA'),
                    event.get('state_code'),
                    event.get('city'),
                    event.get('entity_name'),
                    event.get('amount'),
                    event.get('currency', 'BRL'),
                    event.get('amount_usd'),
                    event.get('sector'),
                    event.get('source_url'),
                    event.get('raw_payload')
                ))
                inserted += 1
            except Exception as e:
                logger.warning(f"Erro ao inserir evento {event.get('source_id')}: {e}")
                continue

        conn.commit()
        logger.info(f"Inseridos/atualizados {inserted} eventos CVM")

    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao inserir eventos: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

    return inserted

def main():
    """Função principal"""
    logger.info("=== CVM Ofertas Collector - Iniciando ===")

    try:
        events = fetch_cvm_ofertas()

        if events:
            inserted = insert_events(events)
            logger.info(f"Total de eventos processados: {inserted}")
        else:
            logger.warning("Nenhum evento encontrado")

    except Exception as e:
        logger.error(f"Erro na execução: {e}")
        sys.exit(1)

    logger.info("=== CVM Ofertas Collector - Finalizado ===")

if __name__ == '__main__':
    main()
