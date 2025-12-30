#!/usr/bin/env python3
"""Análise de cobertura expandida com TODAS as áreas tech"""
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()
c = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    database=os.getenv("POSTGRES_DB"),
)
cur = c.cursor()

# Áreas expandidas
areas = {
    "Gestão/Liderança": ["cto", "engineering manager", "tech lead", "vp engineering", "director"],
    "Arquitetura": ["architect", "solutions architect", "software architect", "cloud architect"],
    "QA/Testes": ["qa", "quality assurance", "test engineer", "sdet", "automation test"],
    "Frontend": ["frontend", "react", "vue", "angular", "javascript"],
    "Backend": ["backend", "java", "python", "node", "api", "microservices"],
    "Full Stack": ["full stack", "fullstack"],
    "Mobile": ["mobile", "android", "ios", "swift", "kotlin", "flutter"],
    "Data Science": ["data scientist", "data analyst", "data engineer", "big data"],
    "AI/ML": ["ai", "machine learning", "ml engineer", "artificial intelligence"],
    "LLM/RAG": ["llm", "large language model", "rag", "gpt", "openai"],
    "DevOps/SRE": ["devops", "sre", "kubernetes", "docker", "terraform"],
    "Cloud": ["aws", "azure", "gcp", "cloud engineer"],
    "Segurança": ["security", "cybersecurity", "infosec", "penetration"],
    "DBA": ["dba", "database admin", "postgresql", "mysql"],
    "Redes": ["network", "cisco", "routing", "network admin"],
    "Blockchain": ["blockchain", "web3", "solidity", "smart contract"],
    "IoT/Embedded": ["iot", "embedded", "firmware"],
    "Gaming": ["game developer", "unity", "unreal"],
    "Fintech": ["fintech", "payment", "stripe", "paypal"],
}

print("=" * 80)
print("📊 ANÁLISE EXPANDIDA DE COBERTURA - SOFIA PULSE")
print("=" * 80)

cur.execute("SELECT COUNT(*) FROM sofia.jobs")
total = cur.fetchone()[0]
print(f"\n🔍 Analisando {total} vagas totais\n")

results = {}
for area, keywords in areas.items():
    conditions = []
    for kw in keywords:
        conditions.append(
            f"(LOWER(title) LIKE '%{kw.lower()}%' OR LOWER(COALESCE(description, '')) LIKE '%{kw.lower()}%')"
        )

    query = f"SELECT COUNT(*) FROM sofia.jobs WHERE {' OR '.join(conditions)}"
    cur.execute(query)
    count = cur.fetchone()[0]
    results[area] = count

sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

print("📈 VAGAS POR ÁREA:\n")
for area, count in sorted_results:
    pct = (count / total * 100) if total > 0 else 0
    icon = "✅" if count > 100 else "⚠️" if count > 20 else "❌"
    bar = "█" * min(int(pct / 2), 40)
    print(f"{icon} {area:20s}: {count:5d} vagas ({pct:5.1f}%) {bar}")

print("\n" + "=" * 80)

# Áreas com baixa cobertura
low = [a for a, c in results.items() if c < 50]
medium = [a for a, c in results.items() if 50 <= c < 150]
high = [a for a, c in results.items() if c >= 150]

print(f"\n📊 RESUMO:")
print(f"   ✅ Alta cobertura (>150): {len(high)} áreas - {', '.join(high) if high else 'Nenhuma'}")
print(f"   ⚠️  Média cobertura (50-150): {len(medium)} áreas - {', '.join(medium) if medium else 'Nenhuma'}")
print(f"   ❌ Baixa cobertura (<50): {len(low)} áreas - {', '.join(low) if low else 'Nenhuma'}")

c.close()
