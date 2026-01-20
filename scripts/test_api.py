import requests

print("Testando API /countries diretamente...")
r = requests.get('http://localhost:8000/api/security/countries')
data = r.json()

print(f"\nTotal países: {len(data['countries'])}")

# Check LATAM
latam_codes = ['BR','AR','CL','CO','PE','MX','VE','HN','GT','HT']
latam_found = [c for c in data['countries'] if c['country_code'] in latam_codes]

print(f"\nLATAM encontrados: {len(latam_found)}")
for c in latam_found:
    print(f"  {c['country_code']}: {c['country_name']} - risk={c['total_risk']:.1f}")

if not latam_found:
    print("\n❌ NENHUM país LATAM na API!")
    print("\nPrimeiros 10 países:")
    for c in data['countries'][:10]:
        print(f"  {c['country_code']}: {c['country_name']}")
