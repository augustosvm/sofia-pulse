import psycopg2, os
from dotenv import load_dotenv
load_dotenv()
c = psycopg2.connect(host=os.getenv('POSTGRES_HOST'), port=os.getenv('POSTGRES_PORT', '5432'), user=os.getenv('POSTGRES_USER'), password=os.getenv('POSTGRES_PASSWORD'), database=os.getenv('POSTGRES_DB'))
cur = c.cursor()

# Criar UNIQUE constraint no job_id
try:
    cur.execute('ALTER TABLE sofia.jobs ADD CONSTRAINT jobs_job_id_unique UNIQUE (job_id)')
    c.commit()
    print('✅ UNIQUE constraint criada em job_id')
except Exception as e:
    if 'already exists' in str(e):
        print('✅ Constraint já existe')
    else:
        print(f'❌ Erro: {e}')
        c.rollback()

c.close()
