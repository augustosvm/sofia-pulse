import requests
import json
import urllib3

urllib3.disable_warnings()

url = "https://api-comexstat.mdic.gov.br/general"

# Payload based on Browser Investigation findings
payload = {
    "flow": "export",
    "monthDetail": True,
    "period": {
        "from": "2024-01",
        "to": "2024-02"
    },
    "filters": [
        {
            "filter": "ncm",
            "values": ["85171300"] # Smartphone (High volume)
        }
    ],
    "details": ["country", "state"],
    "metrics": ["metricFOB", "metricKG"]
}

print(f"Testing POST to {url} with details=['country', 'state']")
try:
    resp = requests.post(url, json=payload, verify=False, timeout=30)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print("Success!")
        if 'data' in data and 'list' in data['data']:
            items = data['data']['list']
            print(f"TOTAL RECORDS: {len(items)}")
            if len(items) > 0:
                countries = set(i.get('country') for i in items)
                months = set(i.get('monthNumber') for i in items)
                states = set(i.get('state') for i in items)
                print(f"Unique Countries ({len(countries)}): {list(countries)[:5]}")
                print(f"Unique Months: {months}")
                print(f"Unique States: {len(states)}")
                print(f"First item: {items[0]}")
        else:
            print("Response valid but empty list or unexpected structure.")
            print(str(data)[:500])
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
