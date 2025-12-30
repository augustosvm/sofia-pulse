#!/usr/bin/env python3
"""
Sofia Pulse - Exemplos de Uso da Integração WhatsApp + Sofia API
"""

import os
import sys

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "utils"))

from sofia_whatsapp_integration import (
    SofiaWhatsAppIntegration,
    alert_api_error,
    alert_collector_failed,
    alert_data_anomaly,
    ask_sofia,
)


def example_1_api_error():
    """Exemplo 1: Alerta de erro em API externa"""
    print("\n" + "=" * 60)
    print("EXEMPLO 1: Erro em API Externa")
    print("=" * 60 + "\n")

    # Simular erro da Bressan API
    alert_api_error(
        api_name="Bressan API",
        status_code=500,
        error_message="Internal Server Error - Database connection failed",
        endpoint="/api/v1/transactions",
    )

    print("\n✅ Alerta enviado com análise da Sofia!")
    print("   Verifique seu WhatsApp")


def example_2_collector_failed():
    """Exemplo 2: Alerta de collector que falhou"""
    print("\n" + "=" * 60)
    print("EXEMPLO 2: Collector Falhou")
    print("=" * 60 + "\n")

    # Simular falha no collector do GitHub
    alert_collector_failed(
        collector_name="collect-github-trending",
        error="HTTP 403 - API rate limit exceeded. Reset time: 2025-11-22 15:30:00 UTC",
    )

    print("\n✅ Alerta enviado com sugestões da Sofia!")


def example_3_data_anomaly():
    """Exemplo 3: Alerta de anomalia nos dados"""
    print("\n" + "=" * 60)
    print("EXEMPLO 3: Anomalia nos Dados")
    print("=" * 60 + "\n")

    # Simular anomalia detectada
    alert_data_anomaly(
        table_name="funding_rounds",
        anomaly_type="Queda abrupta de registros",
        details="Esperado: ~50 registros/dia. Recebido: 3 registros. Possível problema na API.",
    )

    print("\n✅ Alerta enviado com análise da Sofia!")


def example_4_custom_alert():
    """Exemplo 4: Alerta customizado com análise"""
    print("\n" + "=" * 60)
    print("EXEMPLO 4: Alerta Customizado")
    print("=" * 60 + "\n")

    integration = SofiaWhatsAppIntegration()

    # Criar alerta personalizado
    integration.alert_with_analysis(
        title="Sistema de Backup Falhou",
        error_details={
            "Sistema": "Backup PostgreSQL",
            "Erro": "Disk full - Cannot write backup file",
            "Espaço Disponível": "0 MB",
            "Espaço Necessário": "2.5 GB",
            "Último Backup": "2025-11-20 22:00:00",
            "Criticidade": "ALTA",
        },
        ask_sofia=True,  # Pede análise da Sofia
    )

    print("\n✅ Alerta customizado enviado!")


def example_5_ask_sofia_only():
    """Exemplo 5: Apenas consultar Sofia (sem enviar WhatsApp)"""
    print("\n" + "=" * 60)
    print("EXEMPLO 5: Consultar Sofia (sem WhatsApp)")
    print("=" * 60 + "\n")

    # Apenas perguntar à Sofia
    question = """
    Tenho um servidor com os seguintes problemas:
    - Disco 95% cheio
    - CPU 80% de uso constante
    - Memória RAM 90% utilizada
    - Logs crescendo 500MB/dia

    Qual a ordem de prioridade para resolver?
    """

    print("Perguntando à Sofia...")
    response = ask_sofia(question)

    if response:
        print("\n" + "-" * 60)
        print("RESPOSTA DA SOFIA:")
        print("-" * 60)
        print(response)
        print("-" * 60)
    else:
        print("❌ Sofia não respondeu")


def example_6_integration_monitoring():
    """Exemplo 6: Monitoramento de API com alerta automático"""
    print("\n" + "=" * 60)
    print("EXEMPLO 6: Monitoramento de APIs")
    print("=" * 60 + "\n")

    import requests

    # Lista de APIs para monitorar
    apis_to_monitor = [
        {"name": "GitHub API", "url": "https://api.github.com/rate_limit"},
        {"name": "HackerNews API", "url": "https://hacker-news.firebaseio.com/v0/maxitem.json"},
        # Adicione suas APIs aqui
    ]

    for api in apis_to_monitor:
        try:
            response = requests.get(api["url"], timeout=10)

            if response.status_code != 200:
                # Erro detectado - enviar alerta com análise da Sofia
                alert_api_error(
                    api_name=api["name"],
                    status_code=response.status_code,
                    error_message=f"API returned non-200 status",
                    endpoint=api["url"],
                )
                print(f"❌ {api['name']}: HTTP {response.status_code} - Alerta enviado")
            else:
                print(f"✅ {api['name']}: OK")

        except requests.exceptions.RequestException as e:
            # Erro de conexão - enviar alerta
            alert_api_error(
                api_name=api["name"], status_code=0, error_message=f"Connection error: {str(e)}", endpoint=api["url"]
            )
            print(f"❌ {api['name']}: Connection error - Alerta enviado")


def menu():
    """Menu interativo"""
    print("\n" + "=" * 60)
    print("SOFIA PULSE - EXEMPLOS DE INTEGRAÇÃO WHATSAPP + SOFIA")
    print("=" * 60)
    print()
    print("Escolha um exemplo:")
    print()
    print("  1. Erro em API Externa (Bressan API)")
    print("  2. Collector Falhou (GitHub)")
    print("  3. Anomalia nos Dados (funding_rounds)")
    print("  4. Alerta Customizado (Backup)")
    print("  5. Apenas Consultar Sofia (sem WhatsApp)")
    print("  6. Monitoramento de APIs (auto-detect)")
    print()
    print("  0. Sair")
    print()

    choice = input("Opção: ").strip()

    examples = {
        "1": example_1_api_error,
        "2": example_2_collector_failed,
        "3": example_3_data_anomaly,
        "4": example_4_custom_alert,
        "5": example_5_ask_sofia_only,
        "6": example_6_integration_monitoring,
    }

    if choice == "0":
        print("\n👋 Até logo!")
        return False

    if choice in examples:
        examples[choice]()
        input("\n\nPressione ENTER para continuar...")
        return True
    else:
        print("\n❌ Opção inválida")
        return True


if __name__ == "__main__":
    # Verificar configuração
    print("\n🔍 Verificando configuração...")
    print(f"   WHATSAPP_NUMBER: {os.getenv('WHATSAPP_NUMBER', 'NOT SET')}")
    print(f"   SOFIA_API_URL: {os.getenv('SOFIA_API_URL', 'http://localhost:8001/api/v2/chat')}")
    print(f"   WHATSAPP_ENABLED: {os.getenv('WHATSAPP_ENABLED', 'true')}")

    # Menu interativo
    while menu():
        pass
