#!/usr/bin/env python3
"""Base dos Dados Intelligence"""
import os, psycopg2
from datetime import datetime

def get_connection():
    return psycopg2.connect(host=os.getenv('POSTGRES_HOST','localhost'),port=os.getenv('POSTGRES_PORT','5432'),
        dbname=os.getenv('POSTGRES_DB','sofia'),user=os.getenv('POSTGRES_USER','postgres'),password=os.getenv('POSTGRES_PASSWORD',''))

def main():
    conn = get_connection()
    cur = conn.cursor()
    r = ["="*80, "📚 BASE DOS DADOS INTELLIGENCE", "="*80, f"Generated: {datetime.now()}", ""]

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.basedosdados_indicators")
        r.append(f"Records: {cur.fetchone()[0]:,}")
        cur.execute("SELECT dataset, indicator, value, region, year FROM sofia.basedosdados_indicators ORDER BY year DESC LIMIT 30")
        for ds,ind,v,reg,y in cur.fetchall():
            r.append(f"  • {ds[:20]}: {ind[:25]} = {v:,.2f} ({reg}, {y})")
    except Exception as e: r.append(f"⚠️ {e}")

    cur.close()
    conn.close()
    text = "\n".join(r)
    print(text)
    with open("analytics/basedosdados-intelligence.txt",'w') as f: f.write(text)
    print("\n✅ Saved")

if __name__ == "__main__": main()
