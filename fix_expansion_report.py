#!/usr/bin/env python3
"""
Modifica expansion-location-analyzer.py para mostrar cidade quando disponível
"""
import re

# Ler arquivo
with open('/home/ubuntu/sofia-pulse/analytics/expansion-location-analyzer.py', 'r') as f:
    content = f.read()

# Modificar a parte que formata o nome da localização
# Procurar onde imprime o nome da cidade/país e modificar

# Adicionar função para formatar localização
format_func = '''
def format_location_name(city, country):
    """Formata nome da localização: cidade ou país"""
    if city and city != country:
        return f"📍 {city}, {country}"
    else:
        return f"🌍 {country}"
'''

# Inserir função antes de analyze_locations
if 'def format_location_name' not in content:
    content = content.replace('def analyze_locations(', format_func + '\ndef analyze_locations(')

# Modificar onde imprime o nome
content = re.sub(
    r"print\(f\"#\{rank\} - \{loc\['city'\]\}\"\)",
    "print(f\"#{rank} - {format_location_name(loc['city'], loc['country'])}\")",
    content
)

# Salvar
with open('/home/ubuntu/sofia-pulse/analytics/expansion-location-analyzer.py', 'w') as f:
    f.write(content)

print("✅ Script modificado para mostrar cidade quando disponível!")
