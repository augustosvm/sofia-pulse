import requests
import os

EMAIL = "augusto@tiespecialistas.com.br"
PASSWORD = "75August!@"
TOKEN_URL = "https://acleddata.com/oauth/token"
READ_URL = "https://acleddata.com/api/acled/read"

def test_oauth():
    print("\n--- Testing OAuth ---")
    try:
        # Get Token
        data = {
            "username": EMAIL,
            "password": PASSWORD,
            "grant_type": "password",
            "client_id": "acled"
        }
        r = requests.post(TOKEN_URL, data=data)
        print(f"Token Status: {r.status_code}")
        
        if r.status_code == 200:
            token = r.json().get("access_token")
            print("Token obtained.")
            
            # Test Read with Token
            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            params = {"limit": 1}
            r2 = requests.get(READ_URL, headers=headers, params=params)
            print(f"Read Status (OAuth): {r2.status_code}")
            print(f"Read Resp: {r2.text[:200]}")
        else:
            print(f"Token Failed: {r.text}")
            
    except Exception as e:
        print(f"OAuth Error: {e}")

def test_key_auth():
    print("\n--- Testing Key/Email Query Params ---")
    # Trying with password as key (unlikely but worth a check)
    try:
        params = {
            "email": EMAIL,
            "key": PASSWORD,
            "limit": 1
        }
        headers = {
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        r = requests.get(READ_URL, params=params, headers=headers)
        print(f"Read Status (Key=Password): {r.status_code}")
        print(f"Read Resp: {r.text[:200]}")
    except Exception as e:
        print(f"Key Auth Error: {e}")

if __name__ == "__main__":
    test_oauth()
    test_key_auth()
