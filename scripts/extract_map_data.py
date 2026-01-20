import requests
import json
import os
from datetime import datetime

API_BASE = "http://localhost:8000"

ENDPOINTS = [
    {
        "name": "Capital Intelligence (By Country)",
        "url": "/api/capital/by-country",
        "desc": "Investment volume, momentum, and confidence by country."
    },
    {
        "name": "Security Risk (Country Scores)",
        "url": "/api/security/countries",
        "desc": "Hybrid risk scores (Acute + Structural) by country."
    },
    {
        "name": "Security Map (Geo Points - Global Zoom)",
        "url": "/api/security/map?zoom=2",
        "desc": "Individual security events (ACLED) for global map view."
    }
]

def extract_data():
    results = {}
    
    print(f"Starting extraction from {API_BASE}...")
    
    for ep in ENDPOINTS:
        try:
            full_url = f"{API_BASE}{ep['url']}"
            print(f"Fetching {ep['name']} from {full_url}...")
            
            resp = requests.get(full_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                results[ep['name']] = {
                    "description": ep['desc'],
                    "status": "Success",
                    "url": full_url,
                    "data": data
                }
                print(f"  -> Success ({len(str(data))} bytes)")
            else:
                results[ep['name']] = {
                    "description": ep['desc'],
                    "status": f"Error {resp.status_code}",
                    "url": full_url,
                    "error": resp.text
                }
                print(f"  -> Failed: {resp.status_code}")
                
        except Exception as e:
            results[ep['name']] = {
                "description": ep['desc'],
                "status": "Exception",
                "url": full_url,
                "error": str(e)
            }
            print(f"  -> Exception: {e}")

    # Save raw JSON
    with open("map_data_dump.json", "w", encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("Data saved to map_data_dump.json")

if __name__ == "__main__":
    extract_data()
