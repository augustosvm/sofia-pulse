import requests
from bs4 import BeautifulSoup
import os
import sys

# Credentials
EMAIL = "augusto@tiespecialistas.com.br"
PASSWORD = os.getenv("ACLED_PASSWORD")

# URLs
BASE_URL = "https://acleddata.com"
LOGIN_URL = "https://acleddata.com/sso/login" 
DOWNLOAD_PAGE = "https://acleddata.com/system/files/2026-01/number_of_political_violence_events_by_country-year_as-of-09Jan2026.xlsx"

def scrape_acled():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": BASE_URL
    })

    print("🔍 1. Visiting Login Page...")
    r = session.get("https://acleddata.com/user/login")
    print(f"   Status: {r.status_code}")
    
    soup = BeautifulSoup(r.text, 'html.parser')
    # Drupal Login Form
    form = soup.find('form', {'id': 'user-login-form'})
    
    if form:
        action = form.get('action') # Often redirects to same page or /user/login
        if not action.startswith('http'):
             action = "https://acleddata.com" + action
             
        print(f"   Form Action: {action}")
        
        # Extract all inputs including hidden ones (CRITICAL for Drupal)
        payload = {}
        for inp in form.find_all('input'):
            name = inp.get('name')
            value = inp.get('value', '')
            if name:
                payload[name] = value
        
        # Fill credentials
        payload['name'] = EMAIL
        payload['pass'] = PASSWORD
        # op is usually "Log in", sometimes required
        if 'op' not in payload:
             payload['op'] = 'Log in'

        print(f"   Login Payload Keys: {list(payload.keys())}")
        
        # POST Login
        print("🔑 2. Logging in...")
        r_login = session.post(action, data=payload)
        print(f"   Login Status: {r_login.status_code}")
        
        # Check if logged in (usually cookies or redirect)
        if any('wordpress_logged_in' in c.name for c in session.cookies) or 'dashboard' in r_login.url:
             print("✅ Login successful (Session Cookies set)")
        else:
             print("⚠️  Login might have failed. Checking cookies...")
             print(session.cookies.get_dict())

    else:
        print("❌ Login form not found automatically.")

    # 3. Download File Directly
    print(f"\n⬇️  3. Downloading File: {DOWNLOAD_PAGE}...")
    r_file = session.get(DOWNLOAD_PAGE, stream=True)
    
    if r_file.status_code == 200:
        filename = "acled_data.xlsx"
        with open(filename, 'wb') as f:
            for chunk in r_file.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Download complete: {filename}")
        print(f"   Size: {os.path.getsize(filename)} bytes")
    elif r_file.status_code == 403:
        print("❌ Download Failed: 403 (Access Denied). Account might not have permission/terms acceptance.")
    else:
        print(f"❌ Download Failed: {r_file.status_code}")

if __name__ == "__main__":
    scrape_acled()
