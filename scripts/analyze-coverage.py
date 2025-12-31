#!/usr/bin/env python3
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()
c = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT', '5432'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)
cur = c.cursor()

# Áreas solicitadas
areas = {
    'Cybersegurança': ['cybersecurity', 'security', 'infosec', 'penetration', 'ethical hacking'],
    'Mobile': ['mobile', 'android', 'ios', 'swift', 'kotlin', 'react native', 'flutter'],
    'Vision/CV': ['computer vision', 'opencv', 'image processing', 'vision'],
    'Payment': ['payment', 'fintech', 'billing', 'stripe', 'paypal'],
    'DBA': ['dba', 'database admin', 'postgresql', 'mysql', 'oracle dba'],
    'Gestão Projetos': ['project manager', 'scrum master', 'agile', 'pmo'],
    'Governança': ['governance', 'compliance', 'itil', 'cobit'],
    'AI/ML': ['artificial intelligence', 'machine learning', 'ai engineer', 'ml engineer'],
    'LLM': ['llm', 'large language model', 'gpt', 'chatgpt', 'openai'],
    'RAG': ['rag', 'retrieval augmented', 'vector database'],
    'Admin Redes': ['network admin', 'network engineer', 'cisco', 'routing'],
    'DevOps': ['devops', 'sre', 'kubernetes', 'docker', 'terraform'],
    'Cloud': ['aws', 'azure', 'gcp', 'cloud engineer'],
    'Data': ['data scientist', 'data engineer', 'data analyst', 'big data'],
    'Frontend': ['frontend', 'react', 'vue', 'angular'],
    'Backend': ['backend', 'api', 'microservices', 'java', 'python', 'node'],
    'Full Stack': ['full stack', 'fullstack']
}

print("=" * 80)
print("📊 ANÁLISE DE COBERTURA POR ÁREA TECH")
print("=" * 80)
print(f"\n🔍 Buscando em {cur.execute('SELECT COUNT(*) FROM sofia.jobs'); cur.fetchone()[0]} vagas totais\n")

results = {}
for area, keywords in areas.items():
    # Buscar vagas que contenham qualquer keyword
    query = "SELECT COUNT(*) FROM sofia.jobs WHERE " + " OR ".join([
        f"LOWER(title) LIKE LOWER('%{kw}%') OR LOWER(description) LIKE LOWER('%{kw}%') OR LOWER(COALESCE(skills_required::text, '')) LIKE LOWER('%{kw}%')"
        for kw in keywords
    ])
    cur.execute(query)
    count = cur.fetchone()[0]
    results[area] = count

# Ordenar por quantidade
sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

print("📈 VAGAS POR ÁREA:\n")
for area, count in sorted_results:
    icon = "✅" if count > 50 else "⚠️" if count > 10 else "❌"
    print(f"{icon} {area:20s}: {count:4d} vagas")

print("\n" + "=" * 80)
print(f"\n💡 RECOMENDAÇÃO:")
low_coverage = [area for area, count in results.items() if count < 50]
if low_coverage:
    print(f"   Áreas com baixa cobertura (<50 vagas): {', '.join(low_coverage)}")
    print(f"   Sugestão: Adicionar keywords específicas para estas áreas nos coletores")
else:
    print(f"   ✅ Boa cobertura em todas as áreas!")

c.close()
