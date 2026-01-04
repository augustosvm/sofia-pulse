#!/usr/bin/env python3
"""
SOFIA PULSE - CAUSAL INSIGHTS com MACHINE LEARNING
Gera insights PICA conectando TODOS os dados
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from collections import defaultdict
import json
from dotenv import load_dotenv
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr
import re

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or 'localhost',
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5432'),
    'user': os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME') or 'sofia_db',
}

# ============================================================================
# 1. SINAIS FRACOS (Weak Signals) - GitHub → Funding
# ============================================================================

def detect_weak_signals(conn):
    """
    Detecta tecnologias com crescimento explosivo ANTES de funding

    Lógica:
    - GitHub stars crescendo >200% últimos 3 meses
    - Ainda sem funding significativo
    - = Sinal Fraco de próximo unicórnio
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Technologies trending no GitHub
    cur.execute("""
        SELECT
            unnest(topics) as tech,
            SUM(stars) as total_stars,
            COUNT(*) as repo_count,
            AVG(stars) as avg_stars_per_repo
        FROM sofia.github_trending
        WHERE topics IS NOT NULL
            AND created_at >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY tech
        HAVING SUM(stars) > 1000
        ORDER BY total_stars DESC
        LIMIT 20
    """)

    trending_techs = cur.fetchall()

    # Check if there's funding for these techs
    signals = []

    for tech in trending_techs:
        # Buscar funding relacionado
        cur.execute("""
            SELECT COUNT(*) as deal_count, SUM(amount_usd) as total_funding
            FROM sofia.funding_rounds
            WHERE LOWER(company_name) LIKE %s
                OR LOWER(sector) LIKE %s
                AND announced_date >= CURRENT_DATE - INTERVAL '180 days'
        """, (f"%{tech['tech']}%", f"%{tech['tech']}%"))

        funding = cur.fetchone()

        # Sinal Fraco = Alto GitHub + Baixo Funding
        if tech['total_stars'] > 2000 and (funding['deal_count'] or 0) < 3:
            signals.append({
                'tech': tech['tech'],
                'github_stars': int(tech['total_stars']),
                'repos': int(tech['repo_count']),
                'funding_deals': int(funding['deal_count'] or 0),
                'funding_total': float(funding['total_funding'] or 0),
                'signal_strength': 'FORTE' if tech['total_stars'] > 5000 else 'MÉDIO'
            })

    return signals

# ============================================================================
# 2. LAG TEMPORAL (Papers → Funding)
# ============================================================================

def analyze_temporal_lag(conn):
    """
    Descobre LAG entre papers e funding

    Se papers sobre "AI Agents" explodiram em Jan 2024,
    quando vem o funding? (hipótese: 6-12 meses)
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Papers count por mês
    cur.execute("""
        SELECT
            DATE_TRUNC('month', published_date) as month,
            COUNT(*) as paper_count
        FROM sofia.arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY month
        ORDER BY month
    """)

    papers_timeline = {r['month']: r['paper_count'] for r in cur.fetchall()}

    # Funding count por mês
    cur.execute("""
        SELECT
            DATE_TRUNC('month', announced_date) as month,
            COUNT(*) as funding_count,
            SUM(amount_usd) as total_amount
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY month
        ORDER BY month
    """)

    funding_timeline = {r['month']: {
        'count': r['funding_count'],
        'amount': float(r['total_amount'] or 0)
    } for r in cur.fetchall()}

    # Calcular correlação (básica, pode melhorar com scipy)
    lags = []

    for month_paper, paper_count in papers_timeline.items():
        # Checar se 6 meses depois teve funding spike
        future_month = month_paper + timedelta(days=180)

        if future_month in funding_timeline:
            funding_data = funding_timeline[future_month]

            # Se papers >100 E funding >$1B = correlação
            if paper_count > 100 and funding_data['amount'] > 1e9:
                lags.append({
                    'paper_month': month_paper.strftime('%Y-%m'),
                    'paper_count': paper_count,
                    'funding_month': future_month.strftime('%Y-%m'),
                    'funding_amount': funding_data['amount'],
                    'lag_months': 6
                })

    return lags

# ============================================================================
# 3. CONVERGÊNCIA DE SETORES
# ============================================================================

def detect_sector_convergence(conn):
    """
    Detecta quando 2+ setores estão convergindo

    Ex: Defense ($2B) + Space (700 launches) + Cybersecurity CVEs
    = Nova categoria "Space Defense Cyber"
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Top setores de funding
    cur.execute("""
        SELECT sector, SUM(amount_usd) as total, COUNT(*) as deals
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY sector
        ORDER BY total DESC
        LIMIT 10
    """)

    top_sectors = cur.fetchall()

    # Space activity
    cur.execute("""
        SELECT COUNT(*) as launches
        FROM sofia.space_industry
        WHERE launch_date >= CURRENT_DATE - INTERVAL '90 days'
    """)
    space_count = cur.fetchone()['launches']

    # Cybersecurity CVEs
    cur.execute("""
        SELECT COUNT(*) as cve_count
        FROM sofia.cybersecurity_events
        WHERE published_date >= CURRENT_DATE - INTERVAL '90 days'
    """)
    cve_count = cur.fetchone()['cve_count']

    convergences = []

    # Lógica: Se Defense + Space ativo + CVEs alto = Convergência
    for sector in top_sectors:
        if sector['sector'] and 'defense' in sector['sector'].lower() and space_count > 50:
            convergences.append({
                'type': 'Defense + Space',
                'funding': float(sector['total']),
                'space_launches': space_count,
                'insight': f"Defense Tech (${sector['total']/1e9:.1f}B) + Space ({space_count} launches) = Oportunidade em Space Defense"
            })

        if sector['sector'] and 'cyber' in sector['sector'].lower() and cve_count > 500:
            convergences.append({
                'type': 'Cybersecurity + High CVE Activity',
                'funding': float(sector['total']),
                'cve_count': cve_count,
                'insight': f"Cybersecurity funding (${sector['total']/1e9:.1f}B) com {cve_count} CVEs = Mercado aquecido"
            })

    return convergences

# ============================================================================
# 4. ARBITRAGEM GEOGRÁFICA
# ============================================================================

def detect_geographic_arbitrage(conn):
    """
    Encontra gaps: Research forte MAS funding fraco = Oportunidade

    Ex: Brasil tem 8 universidades fazendo Edge AI, mas zero startups funded
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Universidades por país (via global_universities_progress)
    cur.execute("""
        SELECT country_code, COUNT(*) as uni_count
        FROM sofia.global_universities_progress
        WHERE country_code IS NOT NULL
        GROUP BY country_code
        ORDER BY uni_count DESC
    """)

    universities_by_country = {r['country_code']: r['uni_count'] for r in cur.fetchall()}

    # Funding by country (using country_code to match universities)
    cur.execute("""
        SELECT
            COALESCE(co.iso_alpha2, LEFT(fr.country, 2)) as country_code,
            COUNT(*) as deals,
            SUM(fr.amount_usd) as total_funding
        FROM sofia.funding_rounds fr
        LEFT JOIN sofia.countries co ON fr.country_id = co.id
        WHERE (fr.country_id IS NOT NULL OR fr.country IS NOT NULL)
        GROUP BY co.iso_alpha2, fr.country
        ORDER BY total_funding DESC NULLS LAST
        LIMIT 20
    """)

    funding_by_country = {r['country_code']: {
        'deals': r['deals'],
        'total': float(r['total_funding'] or 0)
    } for r in cur.fetchall()}

    gaps = []

    for country, uni_count in universities_by_country.items():
        funding = funding_by_country.get(country, {'deals': 0, 'total': 0})

        # Gap = Muitas universidades MAS pouco funding
        if uni_count > 5 and funding['deals'] < 3:
            gaps.append({
                'country': country,
                'universities': uni_count,
                'funding_deals': funding['deals'],
                'funding_total': funding['total'],
                'opportunity': f"{country}: {uni_count} universidades mas apenas {funding['deals']} deals - Arbitragem!"
            })

    return gaps

# ============================================================================
# 5. ML CORRELATION & REGRESSION (Sklearn)
# ============================================================================

def ml_correlation_analysis(conn):
    """
    Usa sklearn para encontrar correlações e fazer previsões

    Análise:
    - Correlação Papers vs Funding (Pearson r)
    - Regressão Linear para previsão de funding baseado em papers
    - Score de confiança da previsão
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Buscar dados temporais
    cur.execute("""
        SELECT
            DATE_TRUNC('month', published_date) as month,
            COUNT(*) as paper_count
        FROM sofia.arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY month
        ORDER BY month
    """)

    papers_data = cur.fetchall()

    cur.execute("""
        SELECT
            DATE_TRUNC('month', announced_date) as month,
            COUNT(*) as funding_count,
            SUM(amount_usd) as total_amount
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY month
        ORDER BY month
    """)

    funding_data = {r['month']: {'count': r['funding_count'], 'amount': float(r['total_amount'] or 0)} for r in cur.fetchall()}

    # Preparar dados para ML
    X = []  # Papers count
    y = []  # Funding amount
    months = []

    for p in papers_data:
        month = p['month']
        # Lag de 6 meses: papers em Jan → funding em Jul
        future_month = month + timedelta(days=180)

        if future_month in funding_data:
            X.append([p['paper_count']])
            y.append([funding_data[future_month]['amount']])
            months.append((month, future_month))

    if len(X) < 2:
        return None

    X = np.array(X)
    y = np.array(y)

    # Regressão Linear
    model = LinearRegression()
    model.fit(X, y)

    # Score (R²)
    score = model.score(X, y)

    # Correlação de Pearson
    if len(X) > 0:
        correlation, p_value = pearsonr(X.flatten(), y.flatten())
    else:
        correlation, p_value = 0, 1

    # Previsão: Se tivermos N papers este mês, quanto funding em 6 meses?
    latest_papers = papers_data[-1]['paper_count'] if papers_data else 0
    predicted_funding = model.predict([[latest_papers]])[0][0] if latest_papers > 0 else 0

    return {
        'correlation': correlation,
        'p_value': p_value,
        'r_squared': score,
        'latest_papers': latest_papers,
        'predicted_funding_6m': predicted_funding,
        'confidence': 'ALTA' if score > 0.7 else 'MÉDIA' if score > 0.4 else 'BAIXA'
    }

# ============================================================================
# 6. SECTOR CLUSTERING (KMeans)
# ============================================================================

def cluster_sectors(conn):
    """
    Agrupa setores similares usando KMeans

    Features:
    - Total funding
    - Number of deals
    - Average deal size
    - Growth rate
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Dados de funding por setor
    cur.execute("""
        SELECT
            sector,
            COUNT(*) as deals,
            SUM(amount_usd) as total_funding,
            AVG(amount_usd) as avg_deal_size
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '90 days'
            AND sector IS NOT NULL
        GROUP BY sector
        HAVING COUNT(*) >= 2
    """)

    sectors_data = cur.fetchall()

    if len(sectors_data) < 3:
        return []

    # Preparar features
    sectors = []
    features = []

    for s in sectors_data:
        sectors.append(s['sector'])
        features.append([
            float(s['total_funding']),
            float(s['deals']),
            float(s['avg_deal_size'])
        ])

    # Normalizar
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # KMeans clustering (3 clusters: High/Medium/Low activity)
    n_clusters = min(3, len(sectors_data))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(features_scaled)

    # Agrupar resultados
    result = []
    for i, sector in enumerate(sectors):
        result.append({
            'sector': sector,
            'cluster': int(clusters[i]),
            'total_funding': float(sectors_data[i]['total_funding']),
            'deals': int(sectors_data[i]['deals'])
        })

    # Ordenar por cluster
    result.sort(key=lambda x: (x['cluster'], -x['total_funding']))

    return result

# ============================================================================
# 7. NLP TOPIC EXTRACTION
# ============================================================================

def extract_topics_nlp(conn):
    """
    Extrai tópicos automaticamente de papers usando NLP básico

    Técnica: TF-IDF simplificado + keyword frequency
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Buscar papers recentes
    cur.execute("""
        SELECT title, abstract, keywords
        FROM sofia.arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '90 days'
        LIMIT 100
    """)

    papers = cur.fetchall()

    if not papers:
        return []

    # Contar keywords
    keyword_freq = defaultdict(int)

    for paper in papers:
        keywords = paper.get('keywords') or []
        for kw in keywords:
            keyword_freq[kw] += 1

    # Extrair termos técnicos dos títulos/abstracts
    tech_terms = defaultdict(int)

    # Padrões técnicos comuns
    patterns = [
        r'\b(transformer|attention|bert|gpt|llm)\b',
        r'\b(diffusion|gan|vae|autoencoder)\b',
        r'\b(reinforcement learning|supervised|unsupervised)\b',
        r'\b(vision|nlp|robotics|speech)\b',
        r'\b(neural network|deep learning|machine learning)\b',
        r'\b(quantum|edge|federated|distributed)\b',
    ]

    for paper in papers:
        text = f"{paper['title']} {paper['abstract']}".lower()

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                tech_terms[match.lower()] += 1

    # Top topics
    topics = []

    # Keywords estruturados
    for kw, count in sorted(keyword_freq.items(), key=lambda x: -x[1])[:10]:
        topics.append({
            'topic': kw,
            'count': count,
            'source': 'keywords'
        })

    # Termos técnicos
    for term, count in sorted(tech_terms.items(), key=lambda x: -x[1])[:5]:
        topics.append({
            'topic': term,
            'count': count,
            'source': 'nlp_extraction'
        })

    return topics

# ============================================================================
# 8. TIME SERIES FORECASTING
# ============================================================================

def forecast_time_series(conn):
    """
    Previsão para próximos 3-6 meses usando regressão linear simples

    Prevê:
    - Número de papers
    - Volume de funding
    - Tendências de setores
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Histórico de papers (últimos 12 meses)
    cur.execute("""
        SELECT
            DATE_TRUNC('month', published_date) as month,
            COUNT(*) as paper_count
        FROM sofia.arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY month
        ORDER BY month
    """)

    papers_history = cur.fetchall()

    # Histórico de funding
    cur.execute("""
        SELECT
            DATE_TRUNC('month', announced_date) as month,
            SUM(amount_usd) as total_funding
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY month
        ORDER BY month
    """)

    funding_history = cur.fetchall()

    predictions = []

    # Previsão de Papers
    if len(papers_history) >= 3:
        X = np.array([[i] for i in range(len(papers_history))])
        y = np.array([r['paper_count'] for r in papers_history])

        model = LinearRegression()
        model.fit(X, y)

        # Próximos 3 meses
        future_months = []
        for i in range(1, 4):
            future_idx = len(papers_history) + i
            pred = model.predict([[future_idx]])[0]
            future_months.append(int(max(0, pred)))

        predictions.append({
            'metric': 'Papers (próximos 3 meses)',
            'values': future_months,
            'trend': 'CRESCENDO' if future_months[-1] > papers_history[-1]['paper_count'] else 'ESTÁVEL'
        })

    # Previsão de Funding
    if len(funding_history) >= 3:
        X = np.array([[i] for i in range(len(funding_history))])
        y = np.array([float(r['total_funding'] or 0) for r in funding_history])

        model = LinearRegression()
        model.fit(X, y)

        # Próximos 3 meses
        future_funding = []
        for i in range(1, 4):
            future_idx = len(funding_history) + i
            pred = model.predict([[future_idx]])[0]
            future_funding.append(max(0, pred))

        predictions.append({
            'metric': 'Funding (próximos 3 meses)',
            'values': future_funding,
            'trend': 'CRESCENDO' if future_funding[-1] > y[-1] else 'ESTÁVEL'
        })

    return predictions

# ============================================================================
# MAIN - Gerar Relatório
# ============================================================================

def generate_report(conn):
    report = []

    report.append("=" * 80)
    report.append("SOFIA PULSE - CAUSAL INSIGHTS (Machine Learning Enhanced)")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # 1. Sinais Fracos
    report.append("=" * 80)
    report.append("🔥 SINAIS FRACOS (GitHub → Funding Prediction)")
    report.append("=" * 80)
    report.append("")

    signals = detect_weak_signals(conn)

    if signals:
        report.append("⚡ TECNOLOGIAS PRESTES A EXPLODIR:")
        report.append("")
        for s in signals[:5]:
            report.append(f"• {s['tech']}")
            report.append(f"  GitHub: {s['github_stars']:,} stars em {s['repos']} repos")
            report.append(f"  Funding: Apenas {s['funding_deals']} deals (${s['funding_total']/1e9:.2f}B)")
            report.append(f"  PREVISÃO: Funding esperado em 3-6 meses")
            report.append(f"  Signal: {s['signal_strength']}")
            report.append("")
    else:
        report.append("(Nenhum sinal fraco detectado)")

    # 2. Lag Temporal
    report.append("=" * 80)
    report.append("📅 LAG TEMPORAL (Papers → Funding)")
    report.append("=" * 80)
    report.append("")

    lags = analyze_temporal_lag(conn)

    if lags:
        report.append("⏱️  CORRELAÇÕES TEMPORAIS DETECTADAS:")
        report.append("")
        for lag in lags[:3]:
            report.append(f"• Papers: {lag['paper_month']} ({lag['paper_count']} publicações)")
            report.append(f"  → Funding: {lag['funding_month']} (${lag['funding_amount']/1e9:.1f}B)")
            report.append(f"  LAG: {lag['lag_months']} meses")
            report.append("")
    else:
        report.append("(Aguardando mais dados temporais)")

    # 3. Convergência
    report.append("=" * 80)
    report.append("🔗 CONVERGÊNCIA DE SETORES")
    report.append("=" * 80)
    report.append("")

    convergences = detect_sector_convergence(conn)

    if convergences:
        for conv in convergences[:3]:
            report.append(f"• {conv['type']}")
            report.append(f"  {conv['insight']}")
            report.append("")
    else:
        report.append("(Nenhuma convergência forte detectada)")

    # 4. Arbitragem Geográfica
    report.append("=" * 80)
    report.append("🌍 ARBITRAGEM GEOGRÁFICA")
    report.append("=" * 80)
    report.append("")

    gaps = detect_geographic_arbitrage(conn)

    if gaps:
        report.append("💎 OPORTUNIDADES (Research sem Funding):")
        report.append("")
        for gap in gaps[:3]:
            report.append(f"• {gap['opportunity']}")
            report.append("")
    else:
        report.append("(Nenhuma arbitragem detectada)")

    # 5. ML Correlation & Regression
    report.append("=" * 80)
    report.append("🤖 ML CORRELATION & REGRESSION (Sklearn)")
    report.append("=" * 80)
    report.append("")

    ml_corr = ml_correlation_analysis(conn)

    if ml_corr:
        report.append("📊 CORRELAÇÃO PAPERS → FUNDING:")
        report.append("")
        report.append(f"• Correlação de Pearson: {ml_corr['correlation']:.3f}")
        report.append(f"• P-value: {ml_corr['p_value']:.4f}")
        report.append(f"• R² Score: {ml_corr['r_squared']:.3f}")
        report.append(f"• Confiança: {ml_corr['confidence']}")
        report.append("")
        report.append(f"📈 PREVISÃO (próximos 6 meses):")
        report.append(f"• Papers este mês: {ml_corr['latest_papers']}")
        report.append(f"• Funding previsto: ${ml_corr['predicted_funding_6m']/1e9:.2f}B")
        report.append("")
    else:
        report.append("(Dados insuficientes para correlação)")

    # 6. Sector Clustering
    report.append("=" * 80)
    report.append("🎯 SECTOR CLUSTERING (KMeans)")
    report.append("=" * 80)
    report.append("")

    clusters = cluster_sectors(conn)

    if clusters:
        report.append("🔬 SETORES AGRUPADOS POR SIMILARIDADE:")
        report.append("")

        # Agrupar por cluster
        cluster_groups = defaultdict(list)
        for c in clusters:
            cluster_groups[c['cluster']].append(c)

        for cluster_id, sectors in cluster_groups.items():
            total = sum(s['total_funding'] for s in sectors)
            report.append(f"• Cluster {cluster_id} (${total/1e9:.2f}B total):")
            for s in sectors[:3]:  # Top 3 por cluster
                report.append(f"  - {s['sector']}: ${s['total_funding']/1e9:.2f}B ({s['deals']} deals)")
            report.append("")
    else:
        report.append("(Dados insuficientes para clustering)")

    # 7. NLP Topic Extraction
    report.append("=" * 80)
    report.append("💬 NLP TOPIC EXTRACTION")
    report.append("=" * 80)
    report.append("")

    topics = extract_topics_nlp(conn)

    if topics:
        report.append("🔥 TÓPICOS EMERGENTES (extraídos automaticamente):")
        report.append("")

        for topic in topics[:10]:
            source_label = "Keywords" if topic['source'] == 'keywords' else "NLP"
            report.append(f"• {topic['topic']}: {topic['count']} menções ({source_label})")

        report.append("")
    else:
        report.append("(Nenhum tópico detectado)")

    # 8. Time Series Forecasting
    report.append("=" * 80)
    report.append("📈 TIME SERIES FORECASTING")
    report.append("=" * 80)
    report.append("")

    forecasts = forecast_time_series(conn)

    if forecasts:
        report.append("🔮 PREVISÕES (próximos 3 meses):")
        report.append("")

        for forecast in forecasts:
            report.append(f"• {forecast['metric']}:")
            if forecast['metric'].startswith('Papers'):
                report.append(f"  Mês 1: {forecast['values'][0]} papers")
                report.append(f"  Mês 2: {forecast['values'][1]} papers")
                report.append(f"  Mês 3: {forecast['values'][2]} papers")
            else:
                report.append(f"  Mês 1: ${forecast['values'][0]/1e9:.2f}B")
                report.append(f"  Mês 2: ${forecast['values'][1]/1e9:.2f}B")
                report.append(f"  Mês 3: ${forecast['values'][2]/1e9:.2f}B")
            report.append(f"  Tendência: {forecast['trend']}")
            report.append("")
    else:
        report.append("(Dados insuficientes para previsões)")

    report.append("=" * 80)
    report.append("✅ Análise completa com ML!")
    report.append("")

    return "\n".join(report)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to database")
        print()

        report = generate_report(conn)

        # Print
        print(report)

        # Save
        with open('analytics/causal-insights-latest.txt', 'w') as f:
            f.write(report)

        print("💾 Saved to: analytics/causal-insights-latest.txt")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
