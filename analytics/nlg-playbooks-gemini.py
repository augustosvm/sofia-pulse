#!/usr/bin/env python3
"""
NLG Playbooks - Gemini AI

Gera recomendações narrativas baseadas nos dados
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
    'database': os.getenv('POSTGRES_DB', 'sofia_db'),
}

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

def get_top_trends(conn):
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT language as tech, SUM(stars) as stars
        FROM sofia.github_trending
        WHERE language IS NOT NULL
        GROUP BY language
        ORDER BY stars DESC LIMIT 5;
    """)

    trends = cursor.fetchall()
    cursor.close()

    return [{'tech': r['tech'], 'stars': int(r['stars'])} for r in trends]

def get_funding_insights(conn):
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT sector, COUNT(*) as deals, SUM(amount_usd) as total
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY sector
        ORDER BY total DESC LIMIT 10;
    """)

    funding = cursor.fetchall()
    cursor.close()

    return [{
        'sector': r['sector'],
        'deals': int(r['deals']),
        'total': float(r['total']) if r['total'] else 0
    } for r in funding]

def get_paper_topics(conn):
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT
            UNNEST(keywords) as topic,
            COUNT(*) as count
        FROM sofia.arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '90 days'
            AND keywords IS NOT NULL
        GROUP BY topic
        ORDER BY count DESC
        LIMIT 10;
    """)

    topics = cursor.fetchall()
    cursor.close()

    return [{'topic': r['topic'], 'count': int(r['count'])} for r in topics]

def generate_playbook_gemini(trends, funding, papers=None):
    """Gera playbook usando Gemini AI"""

    if not GEMINI_API_KEY or GEMINI_API_KEY == 'your-gemini-api-key-here':
        return generate_playbook_simple(trends, funding)

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        papers_context = ""
        if papers:
            papers_context = f"""
TOP 10 RESEARCH TOPICS (ArXiv últimos 90 dias):
{chr(10).join([f"- {p['topic']}: {p['count']} papers" for p in papers[:10]])}
"""

        prompt = f"""
Você é um analista ESPECIALIZADO em tech intelligence. Analise os dados abaixo e crie recomendações ESPECÍFICAS e ACIONÁVEIS.

TOP 5 TECNOLOGIAS (GitHub):
{chr(10).join([f"- {t['tech']}: {t['stars']:,} stars" for t in trends])}

TOP 10 SETORES (Funding últimos 90 dias):
{chr(10).join([f"- {f['sector']}: ${f['total']/1e9:.2f}B em {f['deals']} deals" for f in funding])}

{papers_context}

IMPORTANTE:
- Seja ESPECÍFICO: Cite tecnologias, empresas e skills EXATAS, não categorias genéricas
- Identifique OPORTUNIDADES: Setores com alto funding MAS ainda não saturados
- Detecte SINAIS FRACOS: Papers + GitHub trends que precedem funding (6-12 meses)

Gere um playbook com:

## 1. Para Desenvolvedores:
- Skills prioritárias (cite tecnologias ESPECÍFICAS, não "Python" genérico)
- Frameworks emergentes (com base em papers E GitHub)
- Certificações/cursos recomendados

## 2. Para Investidores:
- Setores com alto crescimento (cite números)
- Dark horses: Alto potencial mas baixa visibilidade
- Timing: Quando investir (early stage vs growth)

## 3. Para Empresas:
- Onde contratar (cidades/países específicos)
- Skills raras mas críticas
- Salários de mercado (ranges)

Máximo 400 palavras. Use dados ESPECÍFICOS dos inputs.
"""

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print(f"⚠️  Gemini falhou: {e}")
        return generate_playbook_simple(trends, funding)

def generate_playbook_simple(trends, funding):
    """Fallback se Gemini não disponível"""

    playbook = "# PLAYBOOK - TECH INTELLIGENCE\n\n"

    playbook += "## Para Desenvolvedores (Skills)\n\n"
    for i, t in enumerate(trends[:3], 1):
        playbook += f"{i}. **{t['tech']}**: {t['stars']:,} stars - Alta demanda\n"

    playbook += "\n## Para Investidores\n\n"
    for i, f in enumerate(funding[:3], 1):
        playbook += f"{i}. **{f['sector']}**: ${f['total']/1e9:.2f}B investidos - {f['deals']} deals\n"

    playbook += "\n## Para Empresas (Recrutamento)\n\n"
    playbook += f"Contratar: {', '.join([t['tech'] for t in trends[:3]])}\n"

    return playbook

def print_report(playbook, trends, funding):
    print("=" * 80)
    print("NLG PLAYBOOKS - GEMINI AI")
    print("=" * 80)
    print()
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("=" * 80)
    print()

    print(playbook)

    print()
    print("=" * 80)
    print()
    print("📊 Data Sources:")
    print(f"   - GitHub: {len(trends)} technologies")
    print(f"   - Funding: {len(funding)} sectors")
    print()
    print("✅ Playbook generated!")
    print()

def main():
    print("🤖 NLG Playbooks Generator...")
    print()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected")
        print()

        trends = get_top_trends(conn)
        funding = get_funding_insights(conn)

        # Get paper topics for additional context
        try:
            papers = get_paper_topics(conn)
        except Exception as e:
            print(f"⚠️  Could not get paper topics: {e}")
            papers = []

        print("📊 Generating playbook with Gemini AI...")
        playbook = generate_playbook_gemini(trends, funding, papers)

        print_report(playbook, trends, funding)

        # Save
        with open('analytics/playbook-latest.txt', 'w') as f:
            f.write(playbook)

        print("💾 Saved to: analytics/playbook-latest.txt")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
