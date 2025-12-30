#!/usr/bin/env python3
"""
Debug InfoJobs HTML Structure
Fetch a sample page and analyze the HTML to find correct selectors
"""
import requests
from bs4 import BeautifulSoup

url = "https://www.infojobs.com.br/empregos.aspx?palabra=desenvolvedor&page=1"

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

print("Fetching InfoJobs page...")
response = requests.get(url, headers=headers, timeout=15)

if response.status_code != 200:
    print(f"Error: Status {response.status_code}")
    exit(1)

soup = BeautifulSoup(response.text, "html.parser")

# Find job items
job_items = soup.find_all("div", class_="js_vacancyLoad")

if not job_items:
    print("No job items found with class 'js_vacancyLoad'")
    # Try alternative selectors
    print("\nTrying alternative selectors...")
    job_items = soup.find_all("div", class_="elemento-lista")
    if not job_items:
        job_items = soup.find_all("article")

print(f"\nFound {len(job_items)} job items\n")

# Analyze first 3 jobs
for i, item in enumerate(job_items[:3], 1):
    print("=" * 80)
    print(f"JOB #{i}")
    print("=" * 80)

    # Print all classes in the item
    print("\nAll div/span/p elements with classes:")
    for tag in item.find_all(["div", "span", "p", "a", "h2", "h3"]):
        if tag.get("class"):
            print(f"  <{tag.name} class=\"{' '.join(tag.get('class'))}\">{tag.get_text(strip=True)[:80]}...")

    print("\n" + "=" * 80 + "\n")

# Save HTML for manual inspection
with open("/tmp/infojobs-sample.html", "w", encoding="utf-8") as f:
    f.write(response.text)
    print("Full HTML saved to /tmp/infojobs-sample.html")
