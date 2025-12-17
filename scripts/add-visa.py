import psycopg2, os
from dotenv import load_dotenv
load_dotenv()
c = psycopg2.connect(host=os.getenv('POSTGRES_HOST'), port=os.getenv('POSTGRES_PORT', '5432'), user=os.getenv('POSTGRES_USER'), password=os.getenv('POSTGRES_PASSWORD'), database=os.getenv('POSTGRES_DB'))
cur = c.cursor()
cur.execute('ALTER TABLE sofia.jobs ADD COLUMN IF NOT EXISTS has_visa_sponsorship BOOLEAN DEFAULT FALSE')
c.commit()
print('✅ has_visa_sponsorship adicionada')
c.close()
