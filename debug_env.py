from dotenv import load_dotenv
import os
load_dotenv()
print(f"Host: {os.getenv('POSTGRES_HOST')}")
print(f"Port: {os.getenv('POSTGRES_PORT')}")
print(f"User: {os.getenv('POSTGRES_USER')}")
print(f"DB: {os.getenv('POSTGRES_DB')}")
# Do not print password
