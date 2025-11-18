#!/usr/bin/env python3
"""
Seed Historical Data - Popular banco com dados simulados dos últimos 90 dias
Para demonstrar Sofia Pulse v2.0 funcionando com análises avançadas
"""

import psycopg2
from datetime import datetime, timedelta
import random
import os

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'sofia_db'),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', 'sofia123strong')
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

print("🌱 Seed Historical Data - Sofia Pulse v2.0")
print("=" * 70)
print()

# ============================================================================
# 1. FUNDING ROUNDS (últimos 90 dias)
# ============================================================================

print("1️⃣  Populando Funding Rounds (90 dias históricos)...")

sectors = {
    'Defense AI': {'base': 500_000_000, 'growth': 5.0, 'count_growth': 3.0},  # Explodindo
    'Military Drones': {'base': 200_000_000, 'growth': 4.0, 'count_growth': 2.5},
    'Artificial Intelligence': {'base': 2_000_000_000, 'growth': 1.2, 'count_growth': 1.1},
    'AI Safety': {'base': 800_000_000, 'growth': 0.8, 'count_growth': 0.7},  # Caindo
    'Fintech': {'base': 600_000_000, 'growth': 1.0, 'count_growth': 1.0},
    'Data & Analytics': {'base': 300_000_000, 'growth': 0.6, 'count_growth': 0.5},  # Caindo forte
    'Cybersecurity': {'base': 400_000_000, 'growth': 1.8, 'count_growth': 1.5},
    'Quantum Computing': {'base': 100_000_000, 'growth': 6.0, 'count_growth': 4.0},  # Weak signal
}

companies_pool = [
    'Palantir', 'Anduril', 'Shield AI', 'Scale AI', 'Anthropic',
    'OpenAI', 'Databricks', 'Nubank', 'Stripe', 'Figma',
    'Notion', 'Linear', 'Vercel', 'Supabase', 'PlanetScale',
    'Hugging Face', 'Cohere', 'Stability AI', 'Midjourney', 'Runway',
]

round_types = ['Seed', 'Series A', 'Series B', 'Series C', 'Series D', 'Series E', 'Series F']

now = datetime.now()
total_rounds = 0

for days_ago in range(90, -1, -1):
    date = now - timedelta(days=days_ago)

    # Determinar quantos rounds neste dia (mais recente = mais deals)
    # 90d: 1-2 deals/dia, 30d: 3-5 deals/dia
    if days_ago <= 30:
        num_rounds = random.randint(3, 5)
    elif days_ago <= 60:
        num_rounds = random.randint(1, 3)
    else:
        num_rounds = random.randint(1, 2)

    for _ in range(num_rounds):
        # Escolher setor (mais recente = mais Defense AI, menos Data & Analytics)
        if days_ago <= 30:
            # Últimos 30 dias: muito Defense AI
            sector_weights = {
                'Defense AI': 30,
                'Military Drones': 20,
                'Quantum Computing': 15,
                'Artificial Intelligence': 10,
                'Cybersecurity': 10,
                'Fintech': 8,
                'AI Safety': 5,
                'Data & Analytics': 2,
            }
        elif days_ago <= 60:
            # 30-60 dias: equilíbrio
            sector_weights = {
                'Defense AI': 10,
                'Military Drones': 10,
                'Artificial Intelligence': 20,
                'AI Safety': 15,
                'Fintech': 15,
                'Data & Analytics': 15,
                'Cybersecurity': 10,
                'Quantum Computing': 5,
            }
        else:
            # 60-90 dias: muito Data & Analytics, AI Safety
            sector_weights = {
                'Data & Analytics': 25,
                'AI Safety': 20,
                'Artificial Intelligence': 20,
                'Fintech': 15,
                'Cybersecurity': 10,
                'Defense AI': 5,
                'Military Drones': 3,
                'Quantum Computing': 2,
            }

        sector = random.choices(list(sector_weights.keys()), weights=list(sector_weights.values()))[0]

        # Calcular valor baseado em crescimento
        period_factor = 1.0
        if days_ago <= 30:
            period_factor = sectors[sector]['growth']
        elif days_ago <= 60:
            period_factor = 1.0
        else:
            period_factor = 1.0 / sectors[sector]['growth']

        amount = sectors[sector]['base'] * period_factor * random.uniform(0.7, 1.3)
        valuation = amount * random.uniform(5, 15)

        company = random.choice(companies_pool)
        round_type = random.choice(round_types)

        cur.execute("""
            INSERT INTO sofia.funding_rounds (
                company_name, sector, amount_usd, valuation_usd,
                round_type, announced_date
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (company, sector, amount, valuation, round_type, date))

        total_rounds += 1

conn.commit()
print(f"   ✅ {total_rounds} funding rounds inseridos")

# ============================================================================
# 2. ARXIV PAPERS (últimos 90 dias)
# ============================================================================

print("\n2️⃣  Populando ArXiv Papers (90 dias históricos)...")

categories = {
    'cs.AI': 'Inteligência Artificial',
    'cs.LG': 'Machine Learning',
    'cs.RO': 'Robótica',
    'cs.CV': 'Visão Computacional',
    'cs.CL': 'NLP',
}

universities = [
    'MIT', 'Stanford', 'Berkeley', 'CMU', 'Harvard',
    'Oxford', 'Cambridge', 'ETH Zurich',
    'Tsinghua', 'Peking University',
]

topics = {
    'cs.RO': ['Humanoid Manipulation', 'Autonomous Drones', 'Robot Learning', 'Sim-to-Real'],
    'cs.AI': ['Reasoning', 'Planning', 'Multi-Agent Systems', 'Reinforcement Learning'],
    'cs.LG': ['Transformers', 'Efficient Models', 'Scaling Laws', 'Model Compression'],
    'cs.CV': ['Object Detection', 'Segmentation', 'Vision-Language Models', '3D Vision'],
    'cs.CL': ['Language Models', 'Multilingual', 'Chain of Thought', 'Alignment'],
}

total_papers = 0

for days_ago in range(90, -1, -1):
    date = (now - timedelta(days=days_ago)).date()

    # Mais papers recentemente, especialmente em Robótica (weak signal)
    if days_ago <= 7:
        # Burst em Robótica
        num_papers = random.randint(8, 12)
        category_weights = {
            'cs.RO': 50,  # Burst!
            'cs.LG': 20,
            'cs.AI': 15,
            'cs.CV': 10,
            'cs.CL': 5,
        }
    elif days_ago <= 30:
        num_papers = random.randint(5, 8)
        category_weights = {
            'cs.RO': 25,
            'cs.LG': 25,
            'cs.AI': 20,
            'cs.CV': 15,
            'cs.CL': 15,
        }
    elif days_ago <= 60:
        num_papers = random.randint(3, 5)
        category_weights = {
            'cs.LG': 30,
            'cs.AI': 25,
            'cs.CL': 20,
            'cs.CV': 15,
            'cs.RO': 10,
        }
    else:
        num_papers = random.randint(2, 4)
        category_weights = {
            'cs.LG': 35,
            'cs.CL': 25,
            'cs.AI': 20,
            'cs.CV': 15,
            'cs.RO': 5,
        }

    for _ in range(num_papers):
        category = random.choices(list(category_weights.keys()), weights=list(category_weights.values()))[0]
        topic = random.choice(topics[category])
        title = f"{topic} via {random.choice(['Novel', 'Efficient', 'Scalable', 'Robust'])} {random.choice(['Approach', 'Framework', 'Method', 'Architecture'])}"

        arxiv_id = f"{date.strftime('%y%m')}.{random.randint(10000, 99999)}"

        uni = random.choice(universities)
        authors = [f"Author {i} ({uni})" for i in range(random.randint(2, 5))]

        abstract = f"We propose a {topic.lower()} method..."

        cur.execute("""
            INSERT INTO arxiv_ai_papers (
                arxiv_id, title, authors, categories, published_date, abstract
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (arxiv_id) DO NOTHING
        """, (arxiv_id, title, authors, [category], date, abstract))

        total_papers += 1

conn.commit()
print(f"   ✅ {total_papers} papers inseridos")

# ============================================================================
# 3. MARKET DATA B3 (últimos 90 dias)
# ============================================================================

print("\n3️⃣  Populando Market Data B3 (90 dias históricos)...")

b3_stocks = [
    ('WEGE3', 'WEG', 'Energia'),
    ('PETR4', 'Petrobras', 'Petróleo'),
    ('VALE3', 'Vale', 'Mineração'),
    ('BBDC4', 'Bradesco', 'Financeiro'),
    ('ITUB4', 'Itaú Unibanco', 'Financeiro'),
]

total_b3 = 0

for days_ago in range(90, -1, -1):
    timestamp = now - timedelta(days=days_ago)

    for ticker, company, sector in b3_stocks:
        # Simular preço e mudança
        base_price = random.uniform(20, 100)
        change_pct = random.uniform(-2, 3)

        cur.execute("""
            INSERT INTO market_data_brazil (
                ticker, company, price, change_pct, sector, collected_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (ticker, company, base_price, change_pct, sector, timestamp))

        total_b3 += 1

conn.commit()
print(f"   ✅ {total_b3} registros B3 inseridos")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 70)
print("✅ SEED COMPLETO!")
print("=" * 70)
print()
print(f"📊 Dados inseridos:")
print(f"   • {total_rounds} funding rounds (90 dias)")
print(f"   • {total_papers} papers ArXiv (90 dias)")
print(f"   • {total_b3} registros B3 (90 dias)")
print()
print("🎯 Padrões inseridos:")
print("   • Defense AI: +400% em 30d (rotação massiva)")
print("   • Quantum Computing: +500% em 30d (weak signal)")
print("   • Data & Analytics: -70% em 30d (fuga de capital)")
print("   • Robótica: Burst de papers (+800% últimos 7d)")
print()
print("🚀 Agora execute:")
print("   ./generate-insights-v2.0.sh")
print()
print("   Você verá:")
print("   ✅ Análise temporal detectando rotações")
print("   ✅ Anomalias (mega-rounds)")
print("   ✅ Correlação papers → funding (lag ~30d)")
print("   ✅ Forecasts com série temporal")
print("   ✅ Narrativas ricas com contexto")
print()

conn.close()
