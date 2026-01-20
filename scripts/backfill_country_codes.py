import psycopg2
import os

DB_HOST = "91.98.158.19"
DB_NAME = "sofia_db"
DB_USER = "sofia"
DB_PASS = "SofiaPulse2025Secure@DB"
DB_PORT = "5432"

# Mapping Dictionary (Top countries from ACLED/HDX)
COUNTRY_MAP = {
    'Ukraine': 'UA',
    'Brazil': 'BR',
    'Mexico': 'MX',
    'Azerbaijan': 'AZ',
    'France': 'FR',
    'El Salvador': 'SV',
    'Italy': 'IT',
    'Venezuela': 'VE',
    'Costa Rica': 'CR',
    'Haiti': 'HT',
    'Colombia': 'CO',
    'Syria': 'SY',
    'Yemen': 'YE',
    'Sudan': 'SD',
    'Nigeria': 'NG',
    'Somalia': 'SO',
    'Democratic Republic of Congo': 'CD',
    'Myanmar': 'MM',
    'Iraq': 'IQ',
    'Afghanistan': 'AF',
    'Burkina Faso': 'BF',
    'Mali': 'ML',
    'United States': 'US',
    'Russia': 'RU',
    'Palestine': 'PS',
    'Israel': 'IL',
    'Lebanon': 'LB',
    'Turkey': 'TR',
    'India': 'IN',
    'Pakistan': 'PK',
    'Philippines': 'PH',
    'Ethiopia': 'ET',
    'Kenya': 'KE',
    'South Sudan': 'SS',
    'Cameroon': 'CM',
    'Central African Republic': 'CF',
    'Niger': 'NE',
    'Chad': 'TD',
    'Libya': 'LY',
    'Egypt': 'EG',
    'Mozambique': 'MZ',
    'Guatemala': 'GT',
    'Honduras': 'HN',
    'Jamaica': 'JM',
    'Trinidad and Tobago': 'TT',
    'Chile': 'CL',
    'Paraguay': 'PY',
    'Ecuador': 'EC',
    'Peru': 'PE',
    'Bolivia': 'BO',
    'Argentina': 'AR',
    'United Kingdom': 'GB',
    'Germany': 'DE',
    'Greece': 'GR',
    'Sweden': 'SE',
    'Netherlands': 'NL',
    'Belgium': 'BE',
    'Spain': 'ES',
    'Portugal': 'PT',
    'Poland': 'PL',
    'Belarus': 'BY',
    'Iran': 'IR',
    'Saudi Arabia': 'SA',
    'United Arab Emirates': 'AE',
    'Qatar': 'QA',
    'Jordan': 'JO',
    'China': 'CN',
    'South Korea': 'KR',
    'North Korea': 'KP',
    'Japan': 'JP',
    'Taiwan': 'TW',
    'Thailand': 'TH',
    'Vietnam': 'VN',
    'Indonesia': 'ID',
    'Malaysia': 'MY',
    'Bangladesh': 'BD',
    'Sri Lanka': 'LK',
    'Nepal': 'NP',
    'Papua New Guinea': 'PG',
    'Australia': 'AU',
    'New Zealand': 'NZ',
    'Canada': 'CA',
    'Bulgaria': 'BG',
    'Serbia': 'RS',
    'Romania': 'RO',
    'Kazakhstan': 'KZ',
    'Puerto Rico': 'PR',
    'Croatia': 'HR',
    'Norway': 'NO',
    'Dominican Republic': 'DO',
    'Moldova': 'MD',
    'Switzerland': 'CH',
    'Cyprus': 'CY',
    'Slovakia': 'SK',
    'Kyrgyzstan': 'KG',
    'Georgia': 'GE',
    'Montenegro': 'ME',
    'Austria': 'AT',
    'Cuba': 'CU',
    'Czech Republic': 'CZ',
    'Hungary': 'HU',
    'Finland': 'FI',
    'Ireland': 'IE',
    'Sweden': 'SE',
    'Denmark': 'DK',
    'Estonia': 'EE',
    'Latvia': 'LV',
    'Lithuania': 'LT',
    'Slovenia': 'SI',
    'Albania': 'AL',
    'North Macedonia': 'MK',
    'Bosnia and Herzegovina': 'BA',
    'Iceland': 'IS',
    'Armenia': 'AM',
    'Tajikistan': 'TJ',
    'Uzbekistan': 'UZ',
    'Turkmenistan': 'TM',
    'Mongolia': 'MN',
    'Kosovo': 'XK'
}

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    cur = conn.cursor()
    
    print("Starting Country Code Backfill...")
    
    updated_total = 0
    
    for name, code in COUNTRY_MAP.items():
        cur.execute("""
            UPDATE sofia.security_events
            SET country_code = %s
            WHERE country_name = %s 
              AND country_code IS NULL
        """, (code, name))
        rows = cur.rowcount
        if rows > 0:
            print(f"Updated {rows} events for {name} ({code})")
            updated_total += rows
            
    conn.commit()
    print(f"Total rows updated: {updated_total}")
    
    cur.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
