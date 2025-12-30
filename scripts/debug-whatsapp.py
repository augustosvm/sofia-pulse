#!/usr/bin/env python3
"""
Debug WhatsApp Integration - Logs Detalhados
"""

import os
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / "utils"))

# Load .env
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    print(f"✅ Loaded .env from: {env_path}")
except:
    print("⚠️  Could not load .env")

from sofia_whatsapp_integration import SofiaWhatsAppIntegration


def main():
    print("=" * 80)
    print("🔍 DEBUG WHATSAPP INTEGRATION - VERBOSE MODE")
    print("=" * 80)
    print()

    # Show configuration
    print("📋 CONFIGURATION:")
    print(f"  • WHATSAPP_NUMBER: {os.getenv('WHATSAPP_NUMBER', 'NOT SET')}")
    print(f"  • SOFIA_API_URL: {os.getenv('SOFIA_API_URL', 'NOT SET')}")
    print(f"  • WHATSAPP_ENABLED: {os.getenv('WHATSAPP_ENABLED', 'NOT SET')}")
    print()

    # Create integration instance
    integration = SofiaWhatsAppIntegration()

    print("=" * 80)
    print("TEST 1: Ask Sofia (consulta simples)")
    print("=" * 80)
    print()

    query = "Teste de debug WhatsApp. Por favor, responda 'OK' se receber esta mensagem."
    print(f"Query: {query}")
    print()

    response = integration.ask_sofia(query)

    if response:
        print(f"\n✅ Sofia respondeu:")
        print(f"   Tamanho: {len(response)} caracteres")
        print(f"   Resposta completa: {response}")
    else:
        print("\n❌ Sofia não respondeu")
        return

    print("\n" + "=" * 80)
    print("TEST 2: Send WhatsApp (envio direto)")
    print("=" * 80)
    print()

    message = f"""🧪 TESTE DE DEBUG

Mensagem de teste enviada em: {os.popen('date').read().strip()}

Se você está vendo isto, o WhatsApp está funcionando!

---
Sofia Pulse Debug Mode
"""

    print(f"Mensagem a enviar:")
    print(message)
    print()

    success = integration.send_whatsapp(message)

    if success:
        print("\n✅ WhatsApp enviado com sucesso!")
        print("   Verifique seu telefone!")
    else:
        print("\n❌ Falha ao enviar WhatsApp")

    print("\n" + "=" * 80)
    print("TEST 3: Alert with Analysis (fluxo completo)")
    print("=" * 80)
    print()

    success = integration.alert_api_error(
        api_name="Test API (Debug)",
        status_code=200,
        error_message="Este é um teste de debug. Sistema funcionando normalmente.",
        endpoint="/debug/test",
    )

    if success:
        print("\n✅ Alerta completo enviado!")
    else:
        print("\n❌ Falha no alerta completo")

    print("\n" + "=" * 80)
    print("🏁 DEBUG COMPLETE")
    print("=" * 80)
    print()
    print("Próximos passos:")
    print("  1. Verifique os logs acima para identificar onde falha")
    print("  2. Verifique seu WhatsApp para ver se recebeu as mensagens")
    print("  3. Se não recebeu, o problema está na Sofia API não enviando para WhatsApp")
    print()


if __name__ == "__main__":
    main()
