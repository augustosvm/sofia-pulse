#!/usr/bin/env python3
"""
SEC Form D Collector - Capital Signals
Coleta dados de ofertas privadas registradas na SEC (EUA)
Fonte: https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=D&company=&dateb=&owner=include&count=100&output=atom
"""

import os
import sys
import json
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import psycopg2
from psycopg2.extras import execute_values

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sec_form_d_collector')

# Configuração do banco
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '91.98.158.19'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', 'SofiaPulse2025Secure@DB'),
    'dbname': os.getenv('DB_NAME', 'sofia_db')
}

# SEC API endpoints
SEC_FORM_D_FEED = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=D&company=&dateb=&owner=include&count=100&output=atom"
SEC_BASE_URL = "https://www.sec.gov"

# Mapeamento de indústrias SEC para setores
INDUSTRY_MAPPING = {
    'Technology': 'Technology',
    'Biotechnology': 'Healthcare/Biotech',
    'Health Care': 'Healthcare',
    'Financial Services': 'Financial Services',
    'Real Estate': 'Real Estate',
    'Energy': 'Energy',
    'Manufacturing': 'Manufacturing',
    'Retail': 'Retail',
    'Other': 'Other'
}

def get_db_connection():
    """Cria conexão com o banco de dados"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {e}")
        raise

def parse_sec_atom_feed(xml_content: str) -> List[Dict]:
    """Parse do feed Atom da SEC"""
    events = []

    try:
        root = ET.fromstring(xml_content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        for entry in root.findall('atom:entry', ns):
            try:
                title = entry.find('atom:title', ns)
                link = entry.find('atom:link', ns)
                updated = entry.find('atom:updated', ns)
                summary = entry.find('atom:summary', ns)

                if title is not None and link is not None:
                    # Parse do título para extrair informações
                    title_text = title.text or ''
                    parts = title_text.split(' - ')

                    entity_name = parts[0].strip() if len(parts) > 0 else 'Unknown'

                    # Extrair data
                    event_date = None
                    if updated is not None and updated.text:
                        try:
                            event_date = datetime.fromisoformat(updated.text.replace('Z', '+00:00')).date()
                        except:
                            event_date = datetime.now().date()

                    # Extrair link
                    href = link.get('href', '')
                    source_id = href.split('/')[-1] if href else f"sec_{datetime.now().timestamp()}"

                    event = {
                        'source': 'SEC_FORM_D',
                        'event_type': 'PRIVATE_OFFERING',
                        'source_id': source_id,
                        'event_date': event_date,
                        'country_code': 'USA',
                        'entity_name': entity_name[:500],
                        'source_url': SEC_BASE_URL + href if href.startswith('/') else href,
                        'raw_payload': json.dumps({
                            'title': title_text,
                            'summary': summary.text if summary is not None else None
                        })
                    }
                    events.append(event)

            except Exception as e:
                logger.warning(f"Erro ao processar entry: {e}")
                continue

    except ET.ParseError as e:
        logger.error(f"Erro ao fazer parse do XML: {e}")

    return events

def fetch_sec_form_d_recent() -> List[Dict]:
    """Busca Form D recentes da SEC"""
    logger.info("Buscando Form D recentes da SEC...")

    headers = {
        'User-Agent': 'Sofia Pulse Research Bot (contact: research@sofiapulse.com)',
        'Accept': 'application/atom+xml'
    }

    try:
        response = requests.get(SEC_FORM_D_FEED, headers=headers, timeout=30)
        response.raise_for_status()

        events = parse_sec_atom_feed(response.text)
        logger.info(f"Encontrados {len(events)} eventos Form D")
        return events

    except requests.RequestException as e:
        logger.error(f"Erro ao buscar dados da SEC: {e}")
        return []

def fetch_sec_form_d_dataset() -> List[Dict]:
    """
    Busca dados do dataset completo da SEC (quando disponível)
    Alternativa: usar dados do data.sec.gov
    """
    logger.info("Tentando buscar dataset completo da SEC...")

    # SEC disponibiliza datasets em: https://www.sec.gov/data-research/sec-markets-data/form-d-filings-data-sets
    dataset_url = "https://www.sec.gov/files/formd.json"

    headers = {
        'User-Agent': 'Sofia Pulse Research Bot (contact: research@sofiapulse.com)'
    }

    events = []

    try:
        response = requests.get(dataset_url, headers=headers, timeout=60)

        if response.status_code == 200:
            data = response.json()

            for item in data.get('filings', [])[:500]:  # Limitar para não sobrecarregar
                try:
                    event = {
                        'source': 'SEC_FORM_D',
                        'event_type': 'PRIVATE_OFFERING',
                        'source_id': item.get('accessionNumber', f"sec_{datetime.now().timestamp()}"),
                        'event_date': datetime.strptime(item.get('fileDate', ''), '%Y-%m-%d').date() if item.get('fileDate') else None,
                        'country_code': 'USA',
                        'state_code': item.get('state'),
                        'city': item.get('city'),
                        'entity_name': item.get('entityName', 'Unknown')[:500],
                        'amount': float(item.get('totalOfferingAmount', 0)) if item.get('totalOfferingAmount') else None,
                        'currency': 'USD',
                        'amount_usd': float(item.get('totalOfferingAmount', 0)) if item.get('totalOfferingAmount') else None,
                        'sector': INDUSTRY_MAPPING.get(item.get('industryGroupType'), item.get('industryGroupType')),
                        'source_url': f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={item.get('cik')}&type=D",
                        'raw_payload': json.dumps(item)
                    }
                    events.append(event)
                except Exception as e:
                    logger.warning(f"Erro ao processar item: {e}")
                    continue

        else:
            logger.warning(f"Dataset não disponível (status {response.status_code}), usando feed RSS")
            events = fetch_sec_form_d_recent()

    except Exception as e:
        logger.warning(f"Erro ao buscar dataset: {e}, usando feed RSS")
        events = fetch_sec_form_d_recent()

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
                    event.get('country_code', 'USA'),
                    event.get('state_code'),
                    event.get('city'),
                    event.get('entity_name'),
                    event.get('amount'),
                    event.get('currency', 'USD'),
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
        logger.info(f"Inseridos/atualizados {inserted} eventos")

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
    logger.info("=== SEC Form D Collector - Iniciando ===")

    try:
        # Buscar eventos
        events = fetch_sec_form_d_dataset()

        if events:
            # Inserir no banco
            inserted = insert_events(events)
            logger.info(f"Total de eventos processados: {inserted}")
        else:
            logger.warning("Nenhum evento encontrado")

    except Exception as e:
        logger.error(f"Erro na execução: {e}")
        sys.exit(1)

    logger.info("=== SEC Form D Collector - Finalizado ===")

if __name__ == '__main__':
    main()
