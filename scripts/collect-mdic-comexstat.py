import os
import time
import json
import requests
import urllib3
import psycopg2
from typing import List, Dict, Any
from datetime import datetime, timedelta
import sys
from dotenv import load_dotenv

# Add scripts directory to path to allow importing utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Tech-related NCM codes (Brazilian tariff classification) - 8 Digit Specifics
# Using 8-digits is required for accurate ComexStat filtering
TECH_NCM_CODES = {
    # COMPUTERS
    '84713012': 'Tablets / Laptops Leves (< 350g)',
    '84713019': 'Laptops / Notebooks (Outros)',
    '84714100': 'Desktops / Servidores',
    
    # PHONES (8517.12 was replaced by 8517.13 in 2022/2023 updates, keeping both for history)
    '85171231': 'Smartphones (Histórico/Antigo)',
    '85171300': 'Smartphones (Atual)',
    '85176277': 'Dispositivos IoT / Módulos de Comunicação', # Common for modules
    
    # SEMICONDUCTORS (Chips)
    '85423100': 'Processadores e Controladores (Chips)',
    '85423200': 'Memórias (RAM/Flash)',
    '85423900': 'Outros Circuitos Integrados',
    
    # PERIPHERALS & COMPONENTS
    '85176294': 'Switches / Roteadores',
    '85285200': 'Monitores',
    '85340019': 'Circuitos Impressos (PCBs) Multicamadas', # High tech PCBs
}

COLLECTOR_NAME = 'mdic-regional'

def fetch_comexstat_data(ncm_code: str, flow: str, months_back: int = 12) -> List[Dict[str, Any]]:
    """
    Fetch trade data from MDIC ComexStat API (General - POST)
    """
    # Calculate date range (Fixed year 2024 to ensure data availability)
    # Using 2024 guarantees a full dataset availability
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 1)

    # ComexStat API endpoint (General - POST)
    base_url = "https://api-comexstat.mdic.gov.br/general"

    # POST Payload construction
    payload = {
        "flow": "export" if flow == 'exp' else "import",
        "monthDetail": True,
        "period": {
            "from": "2024-01",
            "to": "2024-12"
        },
        "filters": [
            {
                "filter": "ncm",
                "values": [str(ncm_code)]
            }
        ],
        "details": ["country", "state"],
        "metrics": ["metricFOB", "metricKG"]
    }

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    max_retries = 3
    retry_delay = 30 # seconds

    for attempt in range(max_retries):
        try:
            # Use POST data
            response = requests.post(base_url, json=payload, timeout=60, verify=False)
            
            if response.status_code == 429:
                print(f"   ⚠️  Rate limit (429) hit. Waiting {retry_delay}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                continue

            # ComexStat may return 404 for no data
            if response.status_code == 404:
                print(f"   ℹ️  No data for NCM {ncm_code} ({flow})")
                return []

            response.raise_for_status()
            raw_data = response.json()
            # DEBUG PRINT
            # print(f"   🐛 RAW DATA SAMPLE: {str(raw_data)[:300]}")
            
            # Extract list from wrapper
            data = []
            if isinstance(raw_data, dict):
                if 'data' in raw_data and isinstance(raw_data['data'], dict) and 'list' in raw_data['data']:
                    data = raw_data['data']['list']
                elif 'list' in raw_data:
                    data = raw_data['list']
            elif isinstance(raw_data, list):
                data = raw_data

            if isinstance(data, list) and len(data) > 0:
                print(f"   ✅ NCM {ncm_code} ({flow}): {len(data)} records")
                return data
            elif isinstance(data, list) and len(data) == 0:
                print(f"   ℹ️  No data (empty list) for NCM {ncm_code}")
                return []
            else:
                print(f"   ⚠️  Unexpected data format: {type(raw_data)}")
                return []

        except Exception as e:
            print(f"   ❌ Error fetching NCM {ncm_code}: {e}")
            return []
    
    return []

def init_db(conn):
    """Initialize database table and indexes"""
    cursor = conn.cursor()
    
    # REMOVED DROP TABLE to persist data
    
    # Create table if not exists (Now with state_code and source)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.comexstat_trade (
            id SERIAL PRIMARY KEY,
            flow VARCHAR(10) NOT NULL,
            ncm_code VARCHAR(10) NOT NULL,
            ncm_description TEXT,
            period VARCHAR(10) NOT NULL,
            country_code VARCHAR(5),
            country_name TEXT,
            state_code VARCHAR(2), -- Added for Regionalization
            value_usd NUMERIC(15, 2),
            weight_kg NUMERIC(15, 2),
            source VARCHAR(50) DEFAULT 'mdic-comexstat',
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_trade_record UNIQUE (flow, ncm_code, period, country_code, state_code)
        );
    """)
    conn.commit()
    print("✅ Table sofia.comexstat_trade initialized (Regionalized + Source)")

def save_to_database(conn, ncm_code: str, ncm_description: str, flow: str, data: List[Dict]) -> int:
    """Save ComexStat data to PostgreSQL"""

    if not data:
        return 0

    cursor = conn.cursor()
    inserted = 0

    # State Mapping (Name -> Code)
    STATE_MAP = {
        'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM', 'Bahia': 'BA', 'Ceará': 'CE',
        'Distrito Federal': 'DF', 'Espírito Santo': 'ES', 'Goiás': 'GO', 'Maranhão': 'MA',
        'Mato Grosso': 'MT', 'Mato Grosso do Sul': 'MS', 'Minas Gerais': 'MG', 'Pará': 'PA',
        'Paraíba': 'PB', 'Paraná': 'PR', 'Pernambuco': 'PE', 'Piauí': 'PI', 'Rio de Janeiro': 'RJ',
        'Rio Grande do Norte': 'RN', 'Rio Grande do Sul': 'RS', 'Rondônia': 'RO', 'Roraima': 'RR',
        'Santa Catarina': 'SC', 'São Paulo': 'SP', 'Sergipe': 'SE', 'Tocantins': 'TO',
        'Exterior': 'EX', 'Não Declarada': 'ND'
    }

    for record in data:
        try:
            # Key extraction for POST response: 'year', 'monthNumber', 'country', 'state'
            anno = record.get('year') or record.get('coAno')
            mes = record.get('monthNumber') or record.get('coMes')
            
            if anno and mes:
                period = f"{anno}{str(mes).zfill(2)}"
            else:
                period = record.get('period') or datetime.now().strftime('%Y%m')

            country_name = record.get('country') or record.get('noPais') or 'Unknown'
            country_code = 'XX' 
            
            state_raw = record.get('state') or record.get('sgUf') or 'BR'
            state_code = STATE_MAP.get(state_raw, 'BR')
            if state_code == 'BR' and len(state_raw) == 2:
                state_code = state_raw
            
            val_usd = record.get('metricFOB') or record.get('vlFob') or 0
            val_kg = record.get('metricKG') or record.get('kgLiquido') or 0

            # Filter out invalid metric values
            try: val_usd = float(val_usd)
            except: val_usd = 0
            try: val_kg = float(val_kg) 
            except: val_kg = 0

            cursor.execute("""
                INSERT INTO sofia.comexstat_trade
                (flow, ncm_code, ncm_description, period, country_code, country_name, state_code, value_usd, weight_kg, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'mdic-comexstat')
                ON CONFLICT (flow, ncm_code, period, country_code, state_code)
                DO UPDATE SET
                    value_usd = EXCLUDED.value_usd,
                    weight_kg = EXCLUDED.weight_kg,
                    source = EXCLUDED.source,
                    collected_at = CURRENT_TIMESTAMP
            """, (
                flow,
                ncm_code,
                ncm_description,
                period,
                country_code,
                country_name,
                state_code,
                val_usd,
                val_kg
            ))
            inserted += 1
        except Exception as e:
            print(f"   ⚠️ Error inserting record: {e}")
            conn.rollback()
            continue

    conn.commit()
    return inserted

def log_run_start(conn, collector_name):
    """Log the start of a collector run in the database"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT sofia.start_collector_run(%s)", (collector_name,))
        run_id = cursor.fetchone()[0]
        conn.commit()
        return run_id
    except Exception as e:
        print(f"❌ Failed to log run start: {e}")
        conn.rollback()
        return None

def log_run_finish(conn, run_id, status, items_collected=0, items_failed=0, error_message=None):
    """Log the finish of a collector run"""
    if not run_id:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sofia.finish_collector_run(
                %s, %s, %s, %s, %s
            )
        """, (run_id, status, items_collected, items_failed, error_message))
        conn.commit()
    except Exception as e:
        print(f"❌ Failed to log run finish: {e}")
        conn.rollback()

def main():
    print("======================================================================")
    print("📊 MDIC ComexStat API - Comércio Exterior Brasileiro")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📡 Source: https://api-comexstat.mdic.gov.br/")
    print("======================================================================")

    conn = None
    run_id = None
    total_records = 0
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB')
        )
        print("\n✅ Database connected")

        init_db(conn)
        
        # Log Start
        run_id = log_run_start(conn, COLLECTOR_NAME)

        print("\n📊 Fetching tech products trade data (NCM codes)...\n")
        
        for ncm_code, description in TECH_NCM_CODES.items():
            print(f"📦 {description} (NCM: {ncm_code})")

            # Fetch exports
            export_data = fetch_comexstat_data(ncm_code, 'exp')
            if export_data:
                inserted = save_to_database(conn, ncm_code, description, 'export', export_data)
                total_records += inserted
                print(f"   💾 Exports: {inserted} records")

            time.sleep(5)

            # Fetch imports
            import_data = fetch_comexstat_data(ncm_code, 'imp')
            if import_data:
                inserted = save_to_database(conn, ncm_code, description, 'import', import_data)
                total_records += inserted
                print(f"   💾 Imports: {inserted} records")

            print("   ⏳ Sleeping 5s...")
            time.sleep(5) # Respect rate limits

            print("")
        
        print("="*80)
        print("✅ MDIC COMEXSTAT COLLECTION COMPLETE")
        print(f"💾 Total records: {total_records}")
        print("="*80)
        
        # Log Success
        log_run_finish(conn, run_id, 'success', items_collected=total_records)

    except Exception as e:
        print(f"\n❌ Critical Error: {e}")
        if conn and run_id:
            log_run_finish(conn, run_id, 'error', items_collected=total_records, error_message=str(e))
            
        # Send WhatsApp Alert
        try:
            from utils.whatsapp_alerts import alert_collector_failed
            alert_collector_failed(COLLECTOR_NAME, str(e))
        except Exception as alert_e:
            print(f"⚠️  Could not send alert: {alert_e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    load_dotenv()
    main()
