#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sofia Pulse - Generate AI Insights Automatically
Gera insights de TODOS os dados do banco usando Gemini AI
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy import stats
import google.generativeai as genai
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("🔬 Sofia Pulse - Gerador Automático de Insights")
print("=" * 60)

# Carregar .env
from dotenv import load_dotenv
load_dotenv('/home/ubuntu/sofia-pulse/.env')

# Configuração PostgreSQL
DB_USER = os.getenv('DB_USER', 'sofia')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'sofia123strong')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'sofia_db')

connection_string = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(connection_string)

print("\n📊 1. Carregando dados do PostgreSQL...")

# Carregar dados finance
try:
    df_b3 = pd.read_sql('SELECT * FROM sofia.market_data_brazil ORDER BY collected_at DESC', engine)
    print(f"   ✅ B3: {len(df_b3)} registros")
except Exception as e:
    print(f"   ⚠️  B3: {e}")
    df_b3 = pd.DataFrame()

try:
    df_nasdaq = pd.read_sql('SELECT * FROM sofia.market_data_nasdaq ORDER BY collected_at DESC', engine)
    print(f"   ✅ NASDAQ: {len(df_nasdaq)} registros")
except Exception as e:
    print(f"   ⚠️  NASDAQ: {e}")
    df_nasdaq = pd.DataFrame()

try:
    df_funding = pd.read_sql('SELECT * FROM sofia.funding_rounds ORDER BY amount_usd DESC', engine)
    print(f"   ✅ Funding: {len(df_funding)} registros")
except Exception as e:
    print(f"   ⚠️  Funding: {e}")
    df_funding = pd.DataFrame()

# Database overview
try:
    tables = pd.read_sql("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'sofia'
    """, engine)

    table_counts = []
    for table in tables['table_name']:
        try:
            count = pd.read_sql(f'SELECT COUNT(*) as cnt FROM sofia."{table}"', engine).iloc[0]['cnt']
            table_counts.append({'table': table, 'rows': count})
        except:
            table_counts.append({'table': table, 'rows': 0})

    df_overview = pd.DataFrame(table_counts).sort_values('rows', ascending=False)
    total_records = df_overview['rows'].sum()
    tables_with_data = (df_overview['rows'] > 0).sum()
    print(f"   ✅ Total: {total_records:,} registros em {tables_with_data} tabelas")
except Exception as e:
    print(f"   ⚠️  Overview: {e}")
    df_overview = pd.DataFrame()
    total_records = 0
    tables_with_data = 0

print("\n🔍 2. Analisando correlações...")

# Agregar por setor
correlation_df = pd.DataFrame()

if not df_funding.empty and not df_b3.empty:
    funding_by_sector = df_funding.groupby('sector').agg({
        'amount_usd': 'sum',
        'company_name': 'count'
    }).reset_index()
    funding_by_sector.columns = ['sector', 'total_funding', 'num_deals']

    b3_by_sector = df_b3.groupby('sector').agg({
        'change_pct': 'mean',
        'ticker': 'count',
        'volume': 'sum'
    }).reset_index()
    b3_by_sector.columns = ['sector', 'avg_performance', 'num_companies', 'total_volume']

    correlation_df = funding_by_sector.merge(b3_by_sector, on='sector', how='outer')
    correlation_df = correlation_df.fillna(0)

    # Calcular correlação
    numeric_cols = ['total_funding', 'avg_performance', 'total_volume']
    corr_matrix = correlation_df[numeric_cols].corr()

    print(f"   ✅ Correlações calculadas para {len(correlation_df)} setores")
else:
    corr_matrix = pd.DataFrame()
    print("   ⚠️  Dados insuficientes para correlações")

print("\n🎯 3. Clustering de setores...")

if not correlation_df.empty and len(correlation_df) >= 3:
    features = correlation_df[['total_funding', 'avg_performance', 'total_volume']].fillna(0)
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=min(3, len(correlation_df)), random_state=42, n_init=10)
    correlation_df['cluster'] = kmeans.fit_predict(features_scaled)

    print(f"   ✅ {len(correlation_df)} setores agrupados em {correlation_df['cluster'].nunique()} clusters")
else:
    print("   ⚠️  Dados insuficientes para clustering")

print("\n⚠️  4. Detectando anomalias...")

anomaly_sectors = pd.DataFrame()

if not correlation_df.empty and len(correlation_df) > 0:
    features_for_anomaly = correlation_df[['total_funding', 'avg_performance', 'total_volume']].fillna(0)
    z_scores = np.abs(stats.zscore(features_for_anomaly))
    anomalies = (z_scores > 2).any(axis=1)
    correlation_df['is_anomaly'] = anomalies
    anomaly_sectors = correlation_df[correlation_df['is_anomaly']]

    print(f"   ✅ {len(anomaly_sectors)} anomalias detectadas")
else:
    print("   ⚠️  Dados insuficientes para detecção de anomalias")

print("\n🤖 5. Gerando insights com Gemini AI...")

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("   ⚠️  GEMINI_API_KEY não encontrada no .env")
    print("      Obtenvha grátis em: https://aistudio.google.com/app/apikey")
    gemini_insights = "API key não configurada. Configure GEMINI_API_KEY no .env para gerar insights com IA."
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')

        # Preparar summary
        data_summary = f"""
# Sofia Pulse - Data Mining Report

## Database Overview:
- Total de registros: {total_records:,}
- Tabelas com dados: {tables_with_data}

## Finance Data:
- B3 (Brasil): {len(df_b3)} stocks
  - Performance média: {df_b3['change_pct'].mean():.2f}% (se houver dados)
  - Volume total: {df_b3['volume'].sum():,.0f} (se houver dados)

- NASDAQ: {len(df_nasdaq)} stocks
  - Performance média: {df_nasdaq['change_pct'].mean():.2f}% (se houver dados)

- Funding Rounds: {len(df_funding)} deals
  - Total investido: ${df_funding['amount_usd'].sum():,.0f} (se houver dados)
  - Maior deal: ${df_funding['amount_usd'].max():,.0f} (se houver dados)

## Correlações:
{corr_matrix.to_string() if not corr_matrix.empty else 'Dados insuficientes'}

## Clusters:
{correlation_df[['sector', 'cluster', 'total_funding', 'avg_performance']].to_string() if not correlation_df.empty else 'Dados insuficientes'}

## Anomalias:
{anomaly_sectors[['sector', 'total_funding', 'avg_performance']].to_string() if len(anomaly_sectors) > 0 else 'Nenhuma anomalia detectada'}
"""

        prompt = f"""
Você é um analista financeiro expert. Analise os dados abaixo do Sofia Pulse e gere um relatório executivo em português.

{data_summary}

Forneça:
1. **Principais Insights** (3-5 bullet points mais importantes)
2. **Correlações Significativas** (o que os dados revelam sobre relação funding vs performance?)
3. **Setores Quentes** (quais setores estão recebendo mais funding E performando bem?)
4. **Oportunidades** (onde investir baseado nos dados?)
5. **Riscos** (anomalias ou setores com baixa performance apesar de funding alto?)

Seja direto, use números, e destaque padrões acionáveis.
"""

        response = model.generate_content(prompt)
        gemini_insights = response.text

        print("   ✅ Insights gerados com sucesso!")

    except Exception as e:
        print(f"   ⚠️  Erro ao gerar insights: {e}")
        gemini_insights = f"Erro ao gerar insights com Gemini: {e}"

print("\n💾 6. Salvando resultados...")

# Criar diretórios
os.makedirs('/home/ubuntu/sofia-pulse/analytics/insights', exist_ok=True)
os.makedirs('/home/ubuntu/sofia-pulse/analytics/reports', exist_ok=True)

# Salvar correlações
if not correlation_df.empty:
    correlation_df.to_csv('/home/ubuntu/sofia-pulse/analytics/insights/correlation-analysis.csv', index=False)
    print("   ✅ analytics/insights/correlation-analysis.csv")

# Salvar clusters
if not correlation_df.empty and 'cluster' in correlation_df.columns:
    cluster_summary = correlation_df[['sector', 'cluster', 'total_funding', 'avg_performance', 'total_volume']]
    cluster_summary.to_csv('/home/ubuntu/sofia-pulse/analytics/insights/sector-clusters.csv', index=False)
    print("   ✅ analytics/insights/sector-clusters.csv")

# Salvar anomalias
if len(anomaly_sectors) > 0:
    anomaly_sectors.to_csv('/home/ubuntu/sofia-pulse/analytics/insights/anomalies-detected.csv', index=False)
    print("   ✅ analytics/insights/anomalies-detected.csv")

# Salvar top performers B3
if not df_b3.empty:
    top_b3 = df_b3.nlargest(20, 'change_pct')[['ticker', 'company', 'price', 'change_pct', 'sector']]
    top_b3.to_csv('/home/ubuntu/sofia-pulse/analytics/insights/top-performers-b3.csv', index=False)
    print("   ✅ analytics/insights/top-performers-b3.csv")

# Salvar top funding
if not df_funding.empty:
    top_funding = df_funding.nlargest(20, 'amount_usd')[['company_name', 'sector', 'round_type', 'amount_usd', 'valuation_usd']]
    top_funding.to_csv('/home/ubuntu/sofia-pulse/analytics/insights/top-funding-deals.csv', index=False)
    print("   ✅ analytics/insights/top-funding-deals.csv")

# Salvar insights Gemini
insights_md = f"""# Sofia Pulse - AI Insights

**Gerado em**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Modelo**: Gemini Pro
**Custo**: ~$0.0013 por análise

---

## 📊 Resumo dos Dados

- **Total de registros**: {total_records:,}
- **Tabelas com dados**: {tables_with_data}
- **B3**: {len(df_b3)} stocks
- **NASDAQ**: {len(df_nasdaq)} stocks
- **Funding**: {len(df_funding)} deals
- **Anomalias detectadas**: {len(anomaly_sectors)}

---

## 🤖 Insights Gemini AI

{gemini_insights}

---

## 📈 Próximos Passos

1. Revisar setores quentes identificados
2. Investigar anomalias detectadas
3. Analisar correlações entre funding e performance
4. Ajustar estratégia de coleta baseado em insights

---

**Arquivos gerados**:
- `correlation-analysis.csv` - Correlações numéricas
- `sector-clusters.csv` - Clusters identificados
- `anomalies-detected.csv` - Outliers detectados
- `top-performers-b3.csv` - Top 20 B3
- `top-funding-deals.csv` - Top 20 funding rounds

**Acesse Jupyter Lab**: http://91.98.158.19:8889/?token=e5bc3d4f86a4f1ee83d8f046da6af8f9bd36f4728d14dd34
"""

with open('/home/ubuntu/sofia-pulse/analytics/insights/gemini-insights-latest.md', 'w', encoding='utf-8') as f:
    f.write(insights_md)

print("   ✅ analytics/insights/gemini-insights-latest.md")

# Salvar também em TXT para fácil visualização
with open('/home/ubuntu/sofia-pulse/analytics/insights/gemini-insights-latest.txt', 'w', encoding='utf-8') as f:
    f.write(gemini_insights)

print("   ✅ analytics/insights/gemini-insights-latest.txt")

print("\n" + "=" * 60)
print("✅ INSIGHTS GERADOS COM SUCESSO!")
print("=" * 60)
print("\n📄 Para ver os insights:")
print("   cat ~/sofia-pulse/analytics/insights/gemini-insights-latest.txt")
print("\n📊 Arquivos CSV:")
print("   ls -lh ~/sofia-pulse/analytics/insights/*.csv")
print("\n🌐 Jupyter Lab:")
print(f"   http://91.98.158.19:8889/?token=e5bc3d4f86a4f1ee83d8f046da6af8f9bd36f4728d14dd34")
print("\n" + "=" * 60)
