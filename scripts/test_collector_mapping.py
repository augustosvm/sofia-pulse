#!/usr/bin/env python3
import yaml
import psycopg2
from datetime import datetime

with open('/home/ubuntu/sofia-pulse/config/collector_table_map.yml', 'r') as f:
    MAPPING = yaml.safe_load(f)

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='sofia',
    password='SofiaPulse2025Secure@DB',
    database='sofia_db'
)
conn.autocommit = True  # FIX: Autocommit para evitar transaction block

print('='*70)
print('📊 COLLECTOR MAPPING TEST - Last 24h')
print('='*70)
print()

results = []
errors = []

for collector_name, config in sorted(MAPPING.items()):
    table = config['table']
    ts_col = config['ts_col']
    where = config.get('where', '')
    
    try:
        query = f"""
            SELECT COUNT(*) as count, MAX({ts_col}) as last_ts
            FROM {table}
            WHERE {ts_col} >= NOW() - INTERVAL '24 hours'
        """
        
        if where:
            query += f" AND ({where})"
        
        with conn.cursor() as cur:
            cur.execute(query)
            count, last_ts = cur.fetchone()
            
            if count > 0:
                age = datetime.now() - last_ts.replace(tzinfo=None) if last_ts else None
                age_str = str(age).split('.')[0] if age else 'N/A'
                results.append((collector_name, count, last_ts, age_str))
    except Exception as e:
        errors.append((collector_name, str(e)[:80]))

# Print results
if results:
    print(f"{'Collector':<30} | {'Count':<8} | {'Last':<12} | Age")
    print('-' * 70)
    for collector, count, last_ts, age in sorted(results, key=lambda x: x[1], reverse=True):
        ts_str = last_ts.strftime('%H:%M:%S') if last_ts else 'N/A'
        print(f"{collector:<30} | {count:<8} | {ts_str:<12} | {age}")

print()
print(f"✅ Working: {len(results)}/{len(MAPPING)} collectors")
print(f"❌ Errors: {len(errors)}")

if errors:
    print()
    print("Errors (first 5):")
    for coll, err in errors[:5]:
        print(f"  {coll}: {err}")

conn.close()
