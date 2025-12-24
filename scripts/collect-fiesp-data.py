import os
import sys
import time
import requests
import psycopg2
import pandas as pd
import re
from datetime import datetime
from bs4 import BeautifulSoup
from io import BytesIO
from typing import Optional, List, Dict
from dotenv import load_dotenv

# Add scripts directory to path to allow importing utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Database connection
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB"),
}

FIESP_BASE_URL = "https://www.fiesp.com.br/indices-pesquisas-e-publicacoes/"
DATA_DIR = os.path.join("data", "raw", "fiesp")
os.makedirs(DATA_DIR, exist_ok=True)

def init_db(conn):
    """Initialize database table"""
    cursor = conn.cursor()
    
    # Table for INA (Industrial Activity Indicator)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.fiesp_ina (
            id SERIAL PRIMARY KEY,
            period DATE NOT NULL,
            general_activity_index DECIMAL,
            real_sales DECIMAL,
            capacity_utilization DECIMAL,
            hours_worked DECIMAL,
            hours_worked_production DECIMAL,
            salarium_mass_real DECIMAL,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(period)
        )
    """)

    # Table for Sensor FIESP (Qualitative)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sofia.fiesp_sensor (
            id SERIAL PRIMARY KEY,
            period DATE NOT NULL,
            market_conditions DECIMAL,
            sales_expectations DECIMAL,
            inventory_levels DECIMAL,
            investment_intention DECIMAL,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(period)
        )
    """)
    
    conn.commit()
    cursor.close()
    print("✅ Database tables initialized (sofia.fiesp_ina, sofia.fiesp_sensor)")

def get_excel_links(url: str) -> Dict[str, str]:
    """Scrape FIESP page for latest Excel links for Sensor and INA"""
    print(f"🔍 Scanning {url} for Excel files...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        links = {}
        
        # Find all links ending in .xlsx
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text().lower().strip()
            
            if not href.endswith('.xlsx'):
                continue
                
            href_lower = href.lower()
            
            # Identify Sensor FIESP (Clean/Sazonal) - We prefer "com ajuste" (Seasonally Adjusted) likely, or we store both.
            # Let's target the main ones.
            if 'sensor' in href_lower and 'com-ajuste' in href_lower:
                links['sensor'] = href
            
            # Identify INA (Levantamento de Conjuntura) - Look for 'lcdessazonalizado' (Levantamento Conjuntura Dessazonalizado)
            # or 'dessazonalizado' inside a context of 'conjuntura'
            if 'dessazonalizado' in href_lower and ('lc' in href_lower or 'conjuntura' in href_lower or 'ina' in href_lower):
                links['ina'] = href

        return links
    except Exception as e:
        print(f"❌ Error scraping FIESP: {e}")
        return {}

def clean_num(n):
    """Clean numeric values from Excel"""
    if pd.isna(n): return None
    if isinstance(n, (int, float)): return float(n)
    try: 
        # Handle formatted strings if necessary (e.g. "1.000,00")
        s = str(n).replace('.', '').replace(',', '.')
        return float(s)
    except: return None

def download_and_parse_sensor(conn, url: str):
    """Download and process Sensor FIESP Excel"""
    print(f"📡 Downloading Sensor: {url}")
    try:
        resp = requests.get(url, timeout=60)
        file_path = os.path.join(DATA_DIR, "latest_sensor.xlsx")
        with open(file_path, 'wb') as f:
            f.write(resp.content)
            
        # Parse with Pandas
        # Sensor usually has months in columns or rows. 
        # Need to inspect structure. Assuming standard time series format.
        # "Leitura": Usually Time Series are in separate sheet or formatted.
        # Read without header first to find the structure
        df_raw = pd.read_excel(file_path, header=None)
        
        # Determine header row
        # Usually looking for 'Leitura' or 'Indicador' or 'Mês'
        header_row_idx = -1
        for idx, row in df_raw.head(15).iterrows():
            row_str = row.astype(str).str.lower().tolist()
            if any('mercado' in s for s in row_str) and any('vendas' in s for s in row_str):
                 header_row_idx = idx
                 break
        
        print(f"   🎯 Detected Header Row: {header_row_idx}")
        
        if header_row_idx != -1:
             df = pd.read_excel(file_path, header=header_row_idx)
             # print(f"   📊 Columns: {df.columns.tolist()}")
        
        # Column Mapping
        col_map = {}
        for col in df.columns:
            cl = str(col).lower().strip()
            if 'data' in cl: col_map['period'] = col
            elif 'mercado' in cl: col_map['market'] = col
            elif 'vendas' in cl: col_map['sales'] = col
            elif 'estoque' in cl: col_map['inventory'] = col
            elif 'investimento' in cl: col_map['investment'] = col
            
        cursor = conn.cursor()
        inserted_count = 0
        
        # Debug Column Map
        print(f"   🔍 Column Map: {col_map}")

        for index, row in df.iterrows():
            try:
                period_raw = row.get(col_map.get('period'))
                
                # Debug first few rows
                if index < 5:
                    print(f"   👉 Row {index} Period Raw: {period_raw} (Type: {type(period_raw)})")
                
                # Date parsing: Usually "nov/25" or datetime object
                period_date = None
                if isinstance(period_raw, datetime):
                    period_date = period_raw.date()
                else:
                    period_date = parse_pt_date(str(period_raw))
                
                if not period_date:
                    continue

                # Helper to clean numbers
                def get_val(key):
                    if key not in col_map: return 0
                    val = row.get(col_map[key])
                    return clean_num(val)

                market_cond = get_val('market')
                sales_exp = get_val('sales')
                inventory = get_val('inventory')
                invest_int = get_val('investment')

                cursor.execute("""
                    INSERT INTO sofia.fiesp_sensor
                    (period, market_conditions, sales_expectations, inventory_levels, investment_intention)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (period) DO UPDATE SET
                        market_conditions = EXCLUDED.market_conditions,
                        sales_expectations = EXCLUDED.sales_expectations,
                        inventory_levels = EXCLUDED.inventory_levels,
                        investment_intention = EXCLUDED.investment_intention,
                        collected_at = CURRENT_TIMESTAMP
                """, (period_date, market_cond, sales_exp, inventory, invest_int))
                
                inserted_count += 1
            except Exception as e:
                # print(f"Error row {index}: {e}")
                continue

        conn.commit()
        print(f"   ✅ Processed {inserted_count} Sensor records.") 

    except Exception as e:
        print(f"❌ Error processing Sensor: {e}")

def parse_pt_date(date_str: str) -> Optional[datetime.date]:
    """Parse Portuguese date string (e.g. 'jan 2001') to date object"""
    if not isinstance(date_str, str):
        return None
        
    months = {
        'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
    }
    
    parts = date_str.lower().strip().split()
    if len(parts) != 2:
        return None
        
    month_name, year = parts
    month_num = months.get(month_name[:3]) # First 3 chars to be safe
    
    if month_num and year.isdigit():
        return datetime(int(year), month_num, 1).date()
    return None

def download_and_parse_ina(conn, url: str):
    """Download and process INA Excel"""
    print(f"📡 Downloading INA: {url}")
    try:
        resp = requests.get(url, timeout=60)
        file_path = os.path.join(DATA_DIR, "latest_ina.xlsx")
        with open(file_path, 'wb') as f:
            f.write(resp.content)
            
        print("   ✅ INA downloaded. Parsing...")
        
        # Read Excel with header=1 (Row 2 in Excel is header)
        df = pd.read_excel(file_path, header=1)
        
        # Clean columns: Strip whitespace and lower case for matching
        df.columns = [str(c).strip() for c in df.columns]
        
        # Column Mapping (Best guess based on standard FIESP layout)
        # Using containment check for robustness
        col_map = {}
        for col in df.columns:
            cl = col.lower()
            if 'ina total' in cl: col_map['general_activity_index'] = col
            elif 'vendas reais' in cl: col_map['real_sales'] = col
            elif 'horas trabalhadas' in cl and 'produção' in cl: col_map['hours_worked_production'] = col
            elif 'massa salarial' in cl: col_map['salarium_mass_real'] = col
            elif 'nuci' in cl or 'utilização' in cl: col_map['capacity_utilization'] = col
            elif 'mes' == cl or 'mês' == cl: col_map['period'] = col

        if 'period' not in col_map:
            # Fallback: Check if first column is period
            col_map['period'] = df.columns[0]
            
        cursor = conn.cursor()
        inserted_count = 0
        
        for index, row in df.iterrows():
            period_raw = row[col_map.get('period')]
            period_date = parse_pt_date(str(period_raw))
            
            if not period_date:
                continue
                
            val_ina = row.get(col_map.get('general_activity_index'))
            val_sales = row.get(col_map.get('real_sales'))
            val_hours = row.get(col_map.get('hours_worked_production'))
            val_wages = row.get(col_map.get('salarium_mass_real'))
            val_nuci = row.get(col_map.get('capacity_utilization'))
            
            # Helper to clean numeric
            def clean_num(n):
                if pd.isna(n): return None
                try: return float(n)
                except: return None

            try:
                # Upsert logic (Update if exists, or Insert)
                # Using specific constraint conflict handling
                cursor.execute("""
                    INSERT INTO sofia.fiesp_ina (period, general_activity_index, real_sales, hours_worked_production, salarium_mass_real, capacity_utilization)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (period) DO UPDATE SET
                        general_activity_index = EXCLUDED.general_activity_index,
                        real_sales = EXCLUDED.real_sales,
                        hours_worked_production = EXCLUDED.hours_worked_production,
                        salarium_mass_real = EXCLUDED.salarium_mass_real,
                        capacity_utilization = EXCLUDED.capacity_utilization,
                        collected_at = CURRENT_TIMESTAMP
                """, (
                    period_date, 
                    clean_num(val_ina), 
                    clean_num(val_sales), 
                    clean_num(val_hours), 
                    clean_num(val_wages), 
                    clean_num(val_nuci)
                ))
                inserted_count += 1
            except Exception as e:
                # print(f"      ❌ Error inserting row {period_raw}: {e}")
                conn.rollback()
                continue
        
        conn.commit()
        print(f"   ✅ Processed {inserted_count} INA records.")
        
    except Exception as e:
        print(f"❌ Error processing INA: {e}")
        conn.rollback()

def main():
    print("================================================================================")
    print("🏭 FIESP Data Collector")
    print("================================================================================")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        init_db(conn)
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    links = get_excel_links(FIESP_BASE_URL)
    
    # Fallback/Enhancement: Check specific sub-pages if not found on main index
    if 'ina' not in links:
        print("⚠️ INA not found on main page, checking sub-page...")
        ina_links = get_excel_links("https://www.fiesp.com.br/indices-pesquisas-e-publicacoes/levantamento-de-conjuntura/")
        if 'ina' in ina_links:
            links['ina'] = ina_links['ina']
            
    if 'sensor' not in links:
         print("⚠️ Sensor not found on main page, checking sub-page...")
         sensor_links = get_excel_links("https://www.fiesp.com.br/indices-pesquisas-e-publicacoes/sensor-fiesp/")
         if 'sensor' in sensor_links:
             links['sensor'] = sensor_links['sensor']
    
    if not links:
        print("❌ Still no links found. Debugging HTML content...")
        # (Optional) Dump HTML to file for inspection if needed
    else:
        print(f"🔗 Found links: {links}")

    if 'sensor' in links:
        download_and_parse_sensor(conn, links['sensor'])
    
    if 'ina' in links:
        download_and_parse_ina(conn, links['ina'])

    conn.close()

if __name__ == "__main__":
    COLLECTOR_NAME = 'fiesp-data'
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            # Assuming sofia.finish_collector_run exists or basic logging
            # For now just alert
            pass
        except: pass

        # Send WhatsApp Alert
        try:
            from utils.whatsapp_alerts import alert_collector_failed
            alert_collector_failed(COLLECTOR_NAME, str(e))
        except Exception as alert_e:
            print(f"⚠️  Could not send alert: {alert_e}")
        
        sys.exit(1)
