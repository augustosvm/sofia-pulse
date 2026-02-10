# insights.generate

Gera insights reais a partir de dados normalizados e agregados.

## Responsabilidade

- Consumir APENAS dados normalizados e agregados
- Gerar insights para: research, tech, jobs, security, economy
- Nunca ler dados brutos
- Evitar spam: usar watermark, hash de evidência
- Salvar em `sofia.insights`

## Exemplos de Insights Válidos

- Crescimento anormal de publicações por país/organização
- Tecnologias com pico súbito de atividade
- Queda relevante em dados econômicos
- Mudança de padrão em security events
- Correlação simples entre fontes

## Uso

```python
from lib.skill_runner import run

# Generate for all domains
result = run("insights.generate", {})

# Generate for specific domains
result = run("insights.generate", {
    "domains": ["research", "tech"]
})

# Incremental (with watermark)
result = run("insights.generate", {
    "since": "2025-12-08T00:00:00Z"
})

# Dry run
result = run("insights.generate", {
    "dry_run": True
})
```
