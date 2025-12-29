#!/usr/bin/env python3
import sys
sys.path.insert(0, 'scripts/utils')
from sofia_whatsapp_integration import SofiaWhatsAppIntegration

print('\n🧪 Testando notificação via Sofia API...\n')
integration = SofiaWhatsAppIntegration()
print()

message = """🧪 Teste Sofia Pulse - Via Sofia API

✅ Sistema corrigido
📱 Deveria chegar no WhatsApp agora!"""

result = integration.send_whatsapp(message)
print(f'\n{"✅" if result else "❌"} Resultado: {result}\n')
