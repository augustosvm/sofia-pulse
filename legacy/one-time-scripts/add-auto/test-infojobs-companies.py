#!/usr/bin/env python3
"""Quick test to verify company name extraction"""
import requests
from bs4 import BeautifulSoup

url = "https://www.infojobs.com.br/empregos.aspx?palabra=desenvolvedor&page=1"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

response = requests.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(response.text, 'html.parser')
job_items = soup.find_all('div', class_='js_vacancyLoad')

print(f"Testing company extraction on {len(job_items)} jobs...\n")

for i, item in enumerate(job_items[:5], 1):
    # Título
    title_elem = item.find('h2') or item.find('h3')
    title = title_elem.get_text(strip=True) if title_elem else 'N/A'

    # Empresa - usando novo método
    company_elem = item.find('a', class_='text-body text-decoration-none')

    if company_elem:
        company = company_elem.get_text(strip=True)
    else:
        company = 'Não informado'

    if company and len(company) > 100:
        company = 'Não informado (texto muito longo)'

    if 'empresaconfidencial' in company.lower().replace(' ', ''):
        company = 'Confidencial'

    print(f"{i}. {title[:50]}...")
    print(f"   Company: {company}")
    print()
