#!/usr/bin/env python3
"""
Capital Insights Generator - Text Insights from Capital Signals
Generates automatic text insights from capital_events materialized views
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuracao de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('capital_insights_generator')

# Configuracao do banco
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '91.98.158.19'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', 'SofiaPulse2025Secure@DB'),
    'dbname': os.getenv('DB_NAME', 'sofia_db')
}

# Output file
OUTPUT_FILE = 'analytics/capital-insights-latest.txt'


def get_db_connection():
    """Cria conexao com o banco de dados"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {e}")
        raise


def format_currency(value: float, currency: str = 'BRL') -> str:
    """Formata valor monetario"""
    if value is None:
        return 'N/A'
    if value >= 1_000_000_000:
        return f"{'R$' if currency == 'BRL' else '$'} {value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"{'R$' if currency == 'BRL' else '$'} {value / 1_000_000:.0f}M"
    return f"{'R$' if currency == 'BRL' else '$'} {value:,.0f}"


def calculate_momentum_insight(current: float, previous: float) -> Tuple[str, str]:
    """Calcula insight de momentum"""
    if previous == 0 or previous is None:
        return 'neutral', '0%'

    change = ((current - previous) / previous) * 100

    if change > 20:
        return 'strong_up', f'+{change:.0f}%'
    elif change > 5:
        return 'up', f'+{change:.0f}%'
    elif change < -20:
        return 'strong_down', f'{change:.0f}%'
    elif change < -5:
        return 'down', f'{change:.0f}%'
    else:
        return 'neutral', f'{change:+.0f}%'


def fetch_monthly_trends(conn) -> List[Dict]:
    """Busca tendencias mensais"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT
                month_year,
                total_events,
                total_amount_brl,
                total_amount_usd,
                private_offerings,
                public_offerings,
                disbursements
            FROM mv_capital_signals_monthly
            ORDER BY month_year DESC
            LIMIT 6
        """)
        return cursor.fetchall()
    except Exception as e:
        logger.warning(f"Tabela mv_capital_signals_monthly nao existe: {e}")
        return []
    finally:
        cursor.close()


def fetch_geographic_data(conn) -> List[Dict]:
    """Busca dados geograficos do Brasil"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT
                state_code,
                total_events,
                total_amount_brl,
                avg_amount_brl,
                top_sector
            FROM mv_capital_signals_geo_br
            ORDER BY total_amount_brl DESC
            LIMIT 10
        """)
        return cursor.fetchall()
    except Exception as e:
        logger.warning(f"Tabela mv_capital_signals_geo_br nao existe: {e}")
        return []
    finally:
        cursor.close()


def fetch_sector_data(conn) -> List[Dict]:
    """Busca dados por setor"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT
                sector,
                total_events,
                total_amount_brl,
                total_amount_usd,
                avg_amount_brl
            FROM mv_capital_signals_by_sector
            ORDER BY total_amount_brl DESC
            LIMIT 10
        """)
        return cursor.fetchall()
    except Exception as e:
        logger.warning(f"Tabela mv_capital_signals_by_sector nao existe: {e}")
        return []
    finally:
        cursor.close()


def fetch_momentum_data(conn) -> List[Dict]:
    """Busca dados de momentum"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT
                state_code,
                events_last_90d,
                events_prev_90d,
                amount_last_90d,
                amount_prev_90d,
                momentum_pct
            FROM mv_capital_signals_momentum
            ORDER BY momentum_pct DESC
            LIMIT 15
        """)
        return cursor.fetchall()
    except Exception as e:
        logger.warning(f"Tabela mv_capital_signals_momentum nao existe: {e}")
        return []
    finally:
        cursor.close()


def fetch_recent_events(conn, limit: int = 10) -> List[Dict]:
    """Busca eventos recentes"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT
                source,
                event_type,
                entity_name,
                amount,
                currency,
                amount_usd,
                state_code,
                sector,
                event_date
            FROM capital_events
            WHERE event_date >= NOW() - INTERVAL '30 days'
            ORDER BY amount_usd DESC NULLS LAST
            LIMIT %s
        """, (limit,))
        return cursor.fetchall()
    except Exception as e:
        logger.warning(f"Tabela capital_events nao existe: {e}")
        return []
    finally:
        cursor.close()


def generate_overview_insight(monthly_data: List[Dict]) -> Dict:
    """Gera insight de visao geral"""
    if not monthly_data:
        return {
            'title': 'Dados Insuficientes',
            'content': 'Nao ha dados suficientes para gerar insights de visao geral.',
            'trend': 'neutral',
            'delta': 'N/A'
        }

    current = monthly_data[0] if monthly_data else {}
    previous = monthly_data[1] if len(monthly_data) > 1 else {}

    current_amount = float(current.get('total_amount_brl', 0) or 0)
    previous_amount = float(previous.get('total_amount_brl', 0) or 0)

    trend, delta = calculate_momentum_insight(current_amount, previous_amount)

    return {
        'title': 'Fluxo de Capital Mensal',
        'content': f"O volume de capital registrado atingiu {format_currency(current_amount)} neste mes, "
                   f"{'superando' if trend in ['up', 'strong_up'] else 'abaixo de'} "
                   f"o periodo anterior ({format_currency(previous_amount)}). "
                   f"Total de {current.get('total_events', 0)} eventos registrados.",
        'trend': trend,
        'delta': delta
    }


def generate_geographic_insight(geo_data: List[Dict], momentum_data: List[Dict]) -> Dict:
    """Gera insight geografico"""
    if not geo_data:
        return {
            'title': 'Distribuicao Regional',
            'content': 'Dados geograficos nao disponiveis.',
            'trend': 'neutral',
            'delta': 'N/A'
        }

    # Top 3 estados
    top_states = geo_data[:3]
    top_names = [s.get('state_code', 'N/A') for s in top_states]

    # Estado com maior momentum
    if momentum_data:
        top_momentum = max(momentum_data, key=lambda x: float(x.get('momentum_pct', 0) or 0))
        momentum_state = top_momentum.get('state_code', 'N/A')
        momentum_pct = float(top_momentum.get('momentum_pct', 0) or 0)
    else:
        momentum_state = 'N/A'
        momentum_pct = 0

    trend = 'up' if momentum_pct > 10 else ('down' if momentum_pct < -10 else 'neutral')

    return {
        'title': 'Momentum Regional',
        'content': f"Os estados {', '.join(top_names)} lideram o fluxo de capital no Brasil. "
                   f"{momentum_state} apresenta o maior momentum recente "
                   f"({'crescimento' if momentum_pct > 0 else 'queda'} de {abs(momentum_pct):.0f}% nos ultimos 90 dias).",
        'trend': trend,
        'delta': f"+{momentum_pct:.0f}%" if momentum_pct > 0 else f"{momentum_pct:.0f}%"
    }


def generate_sector_insight(sector_data: List[Dict]) -> Dict:
    """Gera insight setorial"""
    if not sector_data:
        return {
            'title': 'Analise Setorial',
            'content': 'Dados setoriais nao disponiveis.',
            'trend': 'neutral',
            'delta': 'N/A'
        }

    top_sector = sector_data[0] if sector_data else {}
    sector_name = top_sector.get('sector', 'N/A')
    sector_amount = float(top_sector.get('total_amount_brl', 0) or 0)
    sector_events = top_sector.get('total_events', 0)

    # Calcular % do total
    total_amount = sum(float(s.get('total_amount_brl', 0) or 0) for s in sector_data)
    pct = (sector_amount / total_amount * 100) if total_amount > 0 else 0

    return {
        'title': f'{sector_name} Lidera Capital',
        'content': f"O setor de {sector_name} concentra {format_currency(sector_amount)} "
                   f"({pct:.0f}% do total) com {sector_events} eventos registrados. "
                   f"Outros setores em destaque: {', '.join([s.get('sector', 'N/A') for s in sector_data[1:4]])}.",
        'trend': 'up' if pct > 25 else 'neutral',
        'delta': f"{pct:.0f}%"
    }


def generate_event_type_insight(monthly_data: List[Dict]) -> Dict:
    """Gera insight por tipo de evento"""
    if not monthly_data:
        return {
            'title': 'Tipos de Evento',
            'content': 'Dados de tipos de evento nao disponiveis.',
            'trend': 'neutral',
            'delta': 'N/A'
        }

    current = monthly_data[0] if monthly_data else {}

    private = current.get('private_offerings', 0) or 0
    public = current.get('public_offerings', 0) or 0
    disbursements = current.get('disbursements', 0) or 0

    total = private + public + disbursements

    if total == 0:
        return {
            'title': 'Tipos de Evento',
            'content': 'Nenhum evento registrado no periodo.',
            'trend': 'neutral',
            'delta': 'N/A'
        }

    # Determinar tipo dominante
    dominant = max([
        ('Ofertas Privadas', private),
        ('Ofertas Publicas', public),
        ('Desembolsos', disbursements)
    ], key=lambda x: x[1])

    pct = (dominant[1] / total * 100) if total > 0 else 0

    return {
        'title': f'{dominant[0]} em Alta',
        'content': f"{dominant[0]} representam {pct:.0f}% dos eventos ({dominant[1]} de {total}). "
                   f"Distribuicao: {private} ofertas privadas, {public} ofertas publicas, {disbursements} desembolsos.",
        'trend': 'up' if dominant[1] > (total / 3 * 1.5) else 'neutral',
        'delta': f"{pct:.0f}%"
    }


def generate_top_deals_insight(recent_events: List[Dict]) -> Dict:
    """Gera insight dos maiores deals"""
    if not recent_events:
        return {
            'title': 'Maiores Eventos',
            'content': 'Nenhum evento recente encontrado.',
            'trend': 'neutral',
            'delta': 'N/A'
        }

    # Top 3 deals
    top_deals = recent_events[:3]

    deal_texts = []
    for deal in top_deals:
        entity = deal.get('entity_name', 'N/A')[:30]
        amount = float(deal.get('amount_usd', 0) or deal.get('amount', 0) or 0)
        currency = deal.get('currency', 'USD')
        deal_texts.append(f"{entity} ({format_currency(amount, currency)})")

    total_top3 = sum(float(d.get('amount_usd', 0) or d.get('amount', 0) or 0) for d in top_deals)

    return {
        'title': 'Top Deals do Mes',
        'content': f"Maiores eventos registrados: {'; '.join(deal_texts)}. "
                   f"Juntos representam {format_currency(total_top3, 'USD')} em capital.",
        'trend': 'up' if len(top_deals) >= 3 else 'neutral',
        'delta': f"{len(top_deals)} deals"
    }


def generate_all_insights(conn) -> List[Dict]:
    """Gera todos os insights"""
    insights = []

    # Buscar dados
    monthly_data = fetch_monthly_trends(conn)
    geo_data = fetch_geographic_data(conn)
    sector_data = fetch_sector_data(conn)
    momentum_data = fetch_momentum_data(conn)
    recent_events = fetch_recent_events(conn)

    logger.info(f"Dados carregados - Monthly: {len(monthly_data)}, Geo: {len(geo_data)}, "
                f"Sectors: {len(sector_data)}, Momentum: {len(momentum_data)}, Recent: {len(recent_events)}")

    # Gerar insights
    insights.append(generate_overview_insight(monthly_data))
    insights.append(generate_geographic_insight(geo_data, momentum_data))
    insights.append(generate_sector_insight(sector_data))
    insights.append(generate_event_type_insight(monthly_data))
    insights.append(generate_top_deals_insight(recent_events))

    return insights


def format_report(insights: List[Dict]) -> str:
    """Formata relatorio de texto"""
    lines = [
        "=" * 60,
        "CAPITAL SIGNALS INSIGHTS",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "Source: SEC Form D (USA), CVM (Brazil), BNDES (Brazil)",
        "=" * 60,
        ""
    ]

    for i, insight in enumerate(insights, 1):
        trend_emoji = {
            'strong_up': '[++]',
            'up': '[+]',
            'neutral': '[=]',
            'down': '[-]',
            'strong_down': '[--]'
        }.get(insight.get('trend', 'neutral'), '[?]')

        lines.extend([
            f"{i}. {insight.get('title', 'Insight')} {trend_emoji} {insight.get('delta', '')}",
            "-" * 50,
            insight.get('content', 'No content available.'),
            ""
        ])

    lines.extend([
        "=" * 60,
        "METHODOLOGY",
        "=" * 60,
        "Data sources:",
        "- SEC Form D: Private offerings filed with SEC (USA)",
        "- CVM Ofertas: Public offerings registered with CVM (Brazil)",
        "- BNDES Desembolsos: Development bank disbursements (Brazil)",
        "",
        "Note: We do NOT use VC/Crunchbase/PitchBook data due to selection bias.",
        "Government sources provide comprehensive, unbiased capital flow data.",
        "=" * 60
    ])

    return "\n".join(lines)


def export_json(insights: List[Dict], filename: str):
    """Exporta insights em JSON"""
    output = {
        'generated_at': datetime.now().isoformat(),
        'source': 'Capital Signals Analytics',
        'insights': insights
    }

    json_file = filename.replace('.txt', '.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info(f"JSON exportado: {json_file}")


def main():
    """Funcao principal"""
    logger.info("=== Capital Insights Generator - Iniciando ===")

    try:
        conn = get_db_connection()

        # Gerar insights
        insights = generate_all_insights(conn)

        # Formatar relatorio
        report = format_report(insights)

        # Salvar arquivo
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"Relatorio salvo em: {OUTPUT_FILE}")

        # Exportar JSON
        export_json(insights, OUTPUT_FILE)

        # Imprimir resumo
        print(report)

        conn.close()

    except Exception as e:
        logger.error(f"Erro na execucao: {e}")
        sys.exit(1)

    logger.info("=== Capital Insights Generator - Finalizado ===")


if __name__ == '__main__':
    main()
