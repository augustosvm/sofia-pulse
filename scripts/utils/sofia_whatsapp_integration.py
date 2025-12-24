#!/usr/bin/env python3
"""
Sofia Pulse - WhatsApp Integration with Sofia API Intelligence
Sends technical alerts to WhatsApp with Sofia's AI analysis
"""

import os
import sys
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Load .env file
try:
    from dotenv import load_dotenv
    # Find .env file - look in project root
    current_dir = Path(__file__).resolve()
    # Go up from scripts/utils/ to project root
    project_root = current_dir.parent.parent.parent
    env_path = project_root / '.env'
    
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[DEBUG] Loaded .env from: {env_path}")
    else:
        load_dotenv()  # Try current directory
        print(f"[DEBUG] .env not found at {env_path}, using environment variables")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Falling back to environment variables only")

# Configuration - use WHATSAPP_SENDER (TIE number) as primary
_whatsapp_raw = os.getenv('WHATSAPP_SENDER') or os.getenv('WHATSAPP_NUMBER', '')
# Fallback to production number if placeholder detected (for local dev environments)
PLACEHOLDERS = ['YOUR_WHATSAPP_NUMBER', 'YOUR_BUSINESS_NUMBER', 'your_whatsapp_number_here', '']
WHATSAPP_NUMBER = '551151990773' if _whatsapp_raw in PLACEHOLDERS else _whatsapp_raw

SOFIA_API_URL = os.getenv('SOFIA_API_URL', 'http://localhost:8001/api/v2/chat')

_whatsapp_api = os.getenv('WHATSAPP_API_URL', '')
WHATSAPP_API_URL = 'http://91.98.158.19:3001/send' if _whatsapp_api in ['your_api_url_here', ''] else _whatsapp_api

_enabled = os.getenv('WHATSAPP_ENABLED') or os.getenv('ALERT_WHATSAPP_ENABLED', 'true')
WHATSAPP_ENABLED = _enabled.lower() == 'true'

print(f"[DEBUG] WhatsApp Number loaded: {WHATSAPP_NUMBER}")
print(f"[DEBUG] WhatsApp Enabled: {WHATSAPP_ENABLED}")

class SofiaWhatsAppIntegration:
    """Integrates Sofia API intelligence with WhatsApp alerts"""

    def __init__(self):
        self.sofia_api_url = SOFIA_API_URL
        self.whatsapp_api_url = WHATSAPP_API_URL
        self.whatsapp_number = WHATSAPP_NUMBER
        self.enabled = WHATSAPP_ENABLED

        # Backward compatibility
        self.api_url = SOFIA_API_URL

    def ask_sofia(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Ask Sofia API for technical analysis

        Args:
            query: Question or error description
            context: Additional context (optional)

        Returns:
            Sofia's response text or None if failed
        """
        try:
            payload = {
                'query': query,
                'user_id': 'sistema-alertas',
                'channel': 'whatsapp'
            }

            # Add context if provided
            if context:
                payload['context'] = context

            print(f"[DEBUG] Enviando para Sofia API: {self.api_url}")
            print(f"[DEBUG] Payload: query={query[:100]}..., user_id=sistema-alertas")

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=30  # Allow time for AI processing
            )

            print(f"[DEBUG] Sofia API status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                sofia_response = data.get('response', None)

                print(f"[DEBUG] Sofia retornou resposta: {sofia_response is not None}")
                if sofia_response:
                    print(f"[DEBUG] Tamanho da resposta: {len(sofia_response)} caracteres")
                    print(f"[DEBUG] Primeiros 100 chars: {sofia_response[:100]}")

                return sofia_response
            else:
                print(f"⚠️  Sofia API returned HTTP {response.status_code}")
                print(f"[DEBUG] Response body: {response.text[:200]}")
                return None

        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to Sofia API at {self.api_url}")
            print("   Is sofia-mastra-api running? Check: docker ps | grep sofia")
            return None
        except requests.exceptions.Timeout:
            print("⏱️  Sofia API timeout (may be processing)")
            return None
        except Exception as e:
            print(f"❌ Error querying Sofia: {e}")
            import traceback
            traceback.print_exc()
            return None

    def send_whatsapp(self, message: str) -> bool:
        """
        Send message to WhatsApp via Sofia API

        Args:
            message: Formatted message to send

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            print("⚠️  WhatsApp disabled (set WHATSAPP_ENABLED=true)")
            return False

        print("\n" + "="*60)
        print("[WHATSAPP DEBUG] Iniciando envio de mensagem")
        print("="*60)

        try:
            payload = {
                'query': message,
                'user_id': 'sofia-pulse',
                'channel': 'whatsapp',
                'phone': self.whatsapp_number
            }

            print(f"[WHATSAPP DEBUG] Configuração:")
            print(f"  • API URL: {self.api_url}")
            print(f"  • Número destino: {self.whatsapp_number}")
            print(f"  • WhatsApp enabled: {self.enabled}")
            print(f"  • Tamanho mensagem: {len(message)} caracteres")
            print(f"  • Primeiros 100 chars: {message[:100]}")
            print(f"\n[WHATSAPP DEBUG] Payload enviado:")
            print(f"  • user_id: {payload['user_id']}")
            print(f"  • channel: {payload['channel']}")
            print(f"  • phone: {payload['phone']}")

            print(f"\n[WHATSAPP DEBUG] Enviando POST para {self.api_url}...")

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=10
            )

            print(f"[WHATSAPP DEBUG] Resposta recebida:")
            print(f"  • Status code: {response.status_code}")
            print(f"  • Headers: {dict(response.headers)}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"[WHATSAPP DEBUG] Response JSON:")
                    print(f"  • Keys: {list(data.keys())}")
                    print(f"  • Response field: {data.get('response', 'N/A')[:100] if data.get('response') else 'VAZIO'}")
                except:
                    print(f"[WHATSAPP DEBUG] Response body (não é JSON): {response.text[:200]}")

                print(f"\n✅ WhatsApp sent to {self.whatsapp_number}")
                print("="*60 + "\n")
                return True
            else:
                print(f"\n❌ WhatsApp failed: HTTP {response.status_code}")
                print(f"[WHATSAPP DEBUG] Error body: {response.text[:500]}")
                print("="*60 + "\n")
                return False

        except Exception as e:
            print(f"\n❌ WhatsApp send error: {e}")
            print("🔄 Falling back to direct send...")
            return self.send_whatsapp_direct(message)

    def send_whatsapp_direct(self, message: str) -> bool:
        """
        Send message directly to WhatsApp API (Baileys)

        This method sends directly to the WhatsApp Baileys API
        instead of going through Sofia API first.

        Args:
            message: Message to send

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            print("⚠️  WhatsApp disabled (set WHATSAPP_ENABLED=true)")
            return False

        print("\n" + "="*60)
        print("[WHATSAPP DIRECT] Sending via Baileys API")
        print("="*60)

        try:
            payload = {
                'to': self.whatsapp_number,
                'message': message
            }

            print(f"[WHATSAPP DIRECT] Configuration:")
            print(f"  • API URL: {self.whatsapp_api_url}")
            print(f"  • Número destino: {self.whatsapp_number}")
            print(f"  • Tamanho mensagem: {len(message)} caracteres")

            print(f"\n[WHATSAPP DIRECT] Enviando POST...")

            response = requests.post(
                self.whatsapp_api_url,
                json=payload,
                timeout=10
            )

            print(f"[WHATSAPP DIRECT] Resposta:")
            print(f"  • Status code: {response.status_code}")

            if response.status_code == 200:
                print(f"\n✅ WhatsApp sent directly to {self.whatsapp_number}")
                print("="*60 + "\n")
                return True
            else:
                print(f"\n❌ WhatsApp direct send failed: HTTP {response.status_code}")
                print(f"[WHATSAPP DIRECT] Error: {response.text[:500]}")
                print("="*60 + "\n")
                return False

        except Exception as e:
            print(f"\n❌ WhatsApp direct send error: {e}")
            import traceback
            traceback.print_exc()
            print("="*60 + "\n")
            return False

    def alert_with_analysis(
        self,
        title: str,
        error_details: Dict[str, Any],
        ask_sofia: bool = True
    ) -> bool:
        """
        Send alert with Sofia's technical analysis

        Args:
            title: Alert title (e.g., "API Error")
            error_details: Error information dict
            ask_sofia: Whether to ask Sofia for analysis (default: True)

        Returns:
            True if alert sent successfully

        Example:
            integration.alert_with_analysis(
                title="Bressan API Error",
                error_details={
                    'api': 'Bressan API',
                    'status': 500,
                    'error': 'Internal Server Error',
                    'timestamp': '2025-11-22 10:30:00'
                }
            )
        """
        # Build context for Sofia
        context_text = "\n".join([
            f"- {key}: {value}"
            for key, value in error_details.items()
        ])

        # Ask Sofia for analysis if enabled
        sofia_analysis = None
        if ask_sofia:
            query = f"""
Alerta de erro detectado:

{title}

Detalhes:
{context_text}

Por favor, forneça:
1. Possível causa do erro
2. Como resolver
3. Impacto no sistema
4. Ações imediatas recomendadas
""".strip()

            print(f"🤖 Consultando Sofia para análise...")
            sofia_analysis = self.ask_sofia(query, context=error_details)

        # Build final WhatsApp message
        message_parts = [
            f"🚨 *{title}*",
            "",
            "*Detalhes:*",
            context_text,
            ""
        ]

        if sofia_analysis:
            message_parts.extend([
                "---",
                "*Análise da Sofia:*",
                sofia_analysis,
                ""
            ])

        message_parts.extend([
            "---",
            f"_Sofia Pulse - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        ])

        final_message = "\n".join(message_parts)

        # Send to WhatsApp (using direct Baileys API)
        return self.send_whatsapp_direct(final_message)

    def alert_api_error(
        self,
        api_name: str,
        status_code: int,
        error_message: str,
        endpoint: Optional[str] = None
    ) -> bool:
        """
        Quick helper: Send API error alert with Sofia analysis

        Example:
            integration.alert_api_error(
                api_name="Bressan API",
                status_code=500,
                error_message="Internal Server Error",
                endpoint="/api/v1/data"
            )
        """
        details = {
            'API': api_name,
            'Status': status_code,
            'Erro': error_message,
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        if endpoint:
            details['Endpoint'] = endpoint

        return self.alert_with_analysis(
            title=f"Erro na {api_name}",
            error_details=details,
            ask_sofia=True
        )

    def alert_collector_failed(
        self,
        collector_name: str,
        error: str,
        suggestions: bool = True
    ) -> bool:
        """
        Quick helper: Send collector failure alert

        Example:
            integration.alert_collector_failed(
                collector_name="collect-github-trending",
                error="HTTP 403 - Rate limit exceeded"
            )
        """
        details = {
            'Collector': collector_name,
            'Erro': error,
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return self.alert_with_analysis(
            title="Collector Falhou",
            error_details=details,
            ask_sofia=suggestions
        )

    def alert_data_anomaly(
        self,
        table_name: str,
        anomaly_type: str,
        details: str
    ) -> bool:
        """
        Quick helper: Send data anomaly alert

        Example:
            integration.alert_data_anomaly(
                table_name="funding_rounds",
                anomaly_type="Missing records",
                details="Expected 50 records, got 3"
            )
        """
        error_details = {
            'Tabela': table_name,
            'Tipo': anomaly_type,
            'Detalhes': details,
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return self.alert_with_analysis(
            title="Anomalia nos Dados",
            error_details=error_details,
            ask_sofia=True
        )

    def test_integration(self) -> bool:
        """Test the full integration"""
        print("=" * 60)
        print("🧪 TESTING SOFIA WHATSAPP INTEGRATION")
        print("=" * 60)
        print()

        # Test 1: Sofia API connection
        print("1️⃣  Testing Sofia API connection...")
        test_query = "Sistema de testes ativo. Responda com 'OK' se receber esta mensagem."
        sofia_response = self.ask_sofia(test_query)

        if sofia_response:
            print(f"   ✅ Sofia API working")
            print(f"   Response: {sofia_response[:100]}...")
        else:
            print("   ❌ Sofia API not responding")
            return False

        print()

        # Test 2: Send test alert with analysis
        print("2️⃣  Sending test alert with Sofia analysis...")
        success = self.alert_api_error(
            api_name="Test API",
            status_code=200,
            error_message="Test integration successful",
            endpoint="/test"
        )

        if success:
            print("   ✅ Alert sent with Sofia analysis")
        else:
            print("   ❌ Alert failed")
            return False

        print()
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print()
        print("Configuration:")
        print(f"  • Sofia API: {self.api_url}")
        print(f"  • WhatsApp: {self.whatsapp_number}")
        print(f"  • Enabled: {self.enabled}")
        print()

        return True


# Convenience functions for direct use
_integration = SofiaWhatsAppIntegration()

def alert_api_error(api_name: str, status_code: int, error_message: str, endpoint: str = None):
    """Quick function: Alert API error with Sofia analysis"""
    return _integration.alert_api_error(api_name, status_code, error_message, endpoint)

def alert_collector_failed(collector_name: str, error: str):
    """Quick function: Alert collector failure with Sofia suggestions"""
    return _integration.alert_collector_failed(collector_name, error)

def alert_data_anomaly(table_name: str, anomaly_type: str, details: str):
    """Quick function: Alert data anomaly with Sofia analysis"""
    return _integration.alert_data_anomaly(table_name, anomaly_type, details)

def ask_sofia(query: str, context: Dict[str, Any] = None) -> Optional[str]:
    """Quick function: Ask Sofia a question"""
    return _integration.ask_sofia(query, context)


if __name__ == '__main__':
    # Run integration test
    integration = SofiaWhatsAppIntegration()
    integration.test_integration()
