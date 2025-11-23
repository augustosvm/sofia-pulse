#!/usr/bin/env python3
"""Olympics & Sports Intelligence"""
import os, psycopg2
from datetime import datetime

def get_connection():
    return psycopg2.connect(host=os.getenv('POSTGRES_HOST','localhost'),port=os.getenv('POSTGRES_PORT','5432'),
        dbname=os.getenv('POSTGRES_DB','sofia'),user=os.getenv('POSTGRES_USER','postgres'),password=os.getenv('POSTGRES_PASSWORD',''))

def main():
    conn = get_connection()
    cur = conn.cursor()
    r = ["="*80, "🏅 OLYMPICS & SPORTS INTELLIGENCE", "="*80, f"Generated: {datetime.now()}", ""]

    # Olympics
    r.extend(["="*80, "🥇 OLYMPIC MEDALS", "="*80])
    try:
        cur.execute("SELECT COUNT(*) FROM sofia.olympics_medals")
        r.append(f"Records: {cur.fetchone()[0]:,}")
        cur.execute("SELECT country, sport, gold, silver, bronze, year FROM sofia.olympics_medals ORDER BY gold DESC LIMIT 20")
        for c,s,g,si,b,y in cur.fetchall():
            r.append(f"  • {c}: {s} - 🥇{g} 🥈{si} 🥉{b} ({y})")
    except Exception as e: r.append(f"⚠️ {e}")

    # Sports Rankings
    r.extend(["", "="*80, "🏆 SPORTS RANKINGS (FIFA, IOC, etc.)", "="*80])
    try:
        cur.execute("SELECT COUNT(*) FROM sofia.sports_rankings")
        r.append(f"Records: {cur.fetchone()[0]:,}")
        cur.execute("SELECT sport, federation, country, rank, points FROM sofia.sports_rankings ORDER BY rank LIMIT 20")
        for sp,fed,c,rk,pts in cur.fetchall():
            r.append(f"  • {sp} ({fed}): #{rk} {c} ({pts:.0f} pts)")
    except Exception as e: r.append(f"⚠️ {e}")

    # World Sports
    r.extend(["", "="*80, "🏃 WORLD SPORTS DATA", "="*80])
    try:
        cur.execute("SELECT COUNT(*) FROM sofia.world_sports_data")
        r.append(f"Records: {cur.fetchone()[0]:,}")
        cur.execute("SELECT country, indicator, value, year FROM sofia.world_sports_data ORDER BY value DESC LIMIT 20")
        for c,ind,v,y in cur.fetchall():
            r.append(f"  • {c}: {ind[:30]} = {v:.2f} ({y})")
    except Exception as e: r.append(f"⚠️ {e}")

    cur.close()
    conn.close()
    text = "\n".join(r)
    print(text)
    with open("analytics/olympics-sports-intelligence.txt",'w') as f: f.write(text)
    print("\n✅ Saved")

if __name__ == "__main__": main()
