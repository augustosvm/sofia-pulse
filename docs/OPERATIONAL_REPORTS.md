# Sofia Pulse - Relatórios Operacionais

## Objetivo

Gerar **relatórios operacionais REAIS** baseados em dados do banco PostgreSQL, não em mensagens antigas ou estimativas.

O relatório responde objetivamente:
- ✅ O que rodou?
- ✅ O que falhou?
- ✅ O que rodou mas veio vazio?
- ✅ O que NÃO rodou?
- ✅ Quantos registros foram inseridos por collector?

---

## Script: `generate_operational_report.py`

**Localização:** `scripts/generate_operational_report.py`

**Fonte da Verdade:**
- `sofia.collector_runs` (execuções reais no banco)
- **`config/daily_expected_collectors.json`** (expected set OFICIAL - gerado por sync_expected_set.py)
- `sofia.notifications_sent` (opcional)
- `sofia.insights` (opcional)

**NÃO usa:**
- ❌ Mensagens antigas
- ❌ `collector_inventory` (desatualizado)
- ❌ Números hardcoded
- ❌ Outputs simulados

**IMPORTANTE:** O expected set é a ÚNICA fonte da verdade para saber quais collectors DEVEM rodar. Hash SHA256 do arquivo é incluído em todos os relatórios para rastreabilidade.

---

## Uso

### Básico
```bash
cd /path/to/sofia-pulse
source .venv/bin/activate

DATABASE_URL="postgresql://..." python3 scripts/generate_operational_report.py
```

### Com opções
```bash
# Janela customizada (últimas 6 horas)
python3 scripts/generate_operational_report.py --since-hours 6

# Diretório de output customizado
python3 scripts/generate_operational_report.py --output-dir /var/log/sofia/reports

# Ambos
python3 scripts/generate_operational_report.py --since-hours 6 --output-dir /tmp/reports
```

---

## Outputs

O script gera **3 versões** do relatório:

### 1. Relatório Executivo (`report_executive_YYYYMMDD_HHMMSS.txt`)

**Tamanho:** 10-15 linhas
**Uso:** Email diário, resumo rápido

**Exemplo:**
```
═══════════════════════════════════════════════════════════
SOFIA PULSE - RELATÓRIO EXECUTIVO
═══════════════════════════════════════════════════════════

✅ STATUS GERAL: HEALTHY

Execução: abc123de
Janela: 2025-12-10 23:55 → 00:05 BRT
Duração: 600s

NÚMEROS:
• Esperados: 45
• Rodaram: 42 (93%)
• Sucessos: 40
• Vazios: 0
• Falhas: 2
• Não rodaram: 3

GATE (Required+GA4): OK

OBSERVAÇÕES:
• 🚨 Collectors IMPORTANTES falharam: jobs-linkedin
• ⚠️ 3 collectors rodaram mas vieram vazios
```

### 2. Relatório Técnico Completo (`report_technical_YYYYMMDD_HHMMSS.txt`)

**Tamanho:** Completo (todas as 7 seções)
**Uso:** Auditoria manual, validação pós-incidente

**Contém:**
1. Execução Detectada (trace, início, fim, duração, gate status)
2. Resumo Numérico
3. Sucessos (lista completa com saved, fetched, duration, horário)
4. Vazios (lista completa com expected_min, horário)
5. Falhas (lista completa com error_code, mensagem, horário)
6. Não Rodaram (lista completa)
7. Observações Operacionais Automáticas

### 3. Relatório WhatsApp-Friendly (`report_whatsapp_YYYYMMDD_HHMMSS.txt`)

**Tamanho:** Curto (para copiar/colar)
**Uso:** Enviar manualmente via WhatsApp, Slack

**Exemplo:**
```
*Sofia Pulse - Relatório Operacional*

Trace: `abc123de`
Janela: 23:55→00:05 BRT

*Gate:* ✅ HEALTHY
*Esperado/Rodou:* 45/42
*OK/Vazios/Falhas/Missing:* 40/0/2/3

*Observações:*
• ! Collectors IMPORTANTES falharam: jobs-linkedin
• ! 3 collectors rodaram mas vieram vazios
```

---

## Estrutura do Relatório (7 Seções Obrigatórias)

### 1️⃣ EXECUÇÃO DETECTADA
- Trace ID (se existir)
- Início (BRT)
- Fim (BRT)
- Duração total
- Status do Gate (Required + GA4): HEALTHY ou UNHEALTHY

**Se nenhuma execução foi encontrada:** Para aqui e declara explicitamente.

### 2️⃣ RESUMO NUMÉRICO
- Collectors esperados
- Collectors que rodaram
- Sucessos (saved > 0)
- Vazios (saved = 0 ou < expected_min)
- Falhas (ok = false)
- Não rodaram (missing)

### 3️⃣ SUCESSOS (saved > 0)
Para cada collector:
- `collector_id`
- `saved` (NULL = "UNKNOWN")
- `fetched` (se existir)
- `duration_ms`
- Horário BRT

### 4️⃣ VAZIOS
Para cada collector vazio:
- `collector_id`
- `saved`
- `expected_min_records`
- Horário BRT
- Observação: "rodou mas não gerou dados"

### 5️⃣ FALHAS
Para cada falha:
- `collector_id`
- `error_code`
- Mensagem resumida (primeiros 100 chars)
- Horário BRT

### 6️⃣ NÃO RODARAM
Lista objetiva dos collectors que:
- Estavam esperados (enabled=true no inventory)
- NÃO possuem execução na janela

### 7️⃣ OBSERVAÇÕES OPERACIONAIS (AUTOMÁTICAS)

Detecta automaticamente:
- ⚠️ Collectors com números repetidos suspeitos (ex: GDELT sempre igual)
- ⚠️ Collectors rodando mas sempre vazios
- 🚨 Collectors importantes (jobs, GA4, Catho) sem execução recente
- ⚠️ Ausência de notificação WhatsApp para a execução detectada

**Nada de opinião. Só fatos observáveis.**

---

## Timezone

**Sempre usa:** `America/Sao_Paulo` (BRT)

**Conversão automática:**
- Timestamps do banco (UTC) → BRT
- Janela de busca considera timezone local

---

## Janela de Tempo

**Padrão:** Últimas 3 horas

**Configurável via:**
```bash
--since-hours N
```

**Se não houver execução na janela:**
- Relatório declara explicitamente: "Nenhuma execução detectada"
- Ação recomendada: Verificar se cron está rodando

---

## Regras Absolutas

🚫 **PROIBIDO:**
- Inventar dados
- Suavizar falhas
- Assumir que "rodou"

✅ **OBRIGATÓRIO:**
- Se algo estiver ausente → declarar explicitamente
- Se não houver dados frescos → dizer isso claramente
- saved NULL → mostrar "UNKNOWN" (nunca "?")

---

## Casos de Uso

### 1. Email Diário Automático
```bash
# Cron: 01:00 BRT (após run_and_verify às 00:05)
0 1 * * * cd /path/to/sofia-pulse && \
  DATABASE_URL="..." \
  python3 scripts/generate_operational_report.py \
  --output-dir /var/log/sofia/reports && \
  cat /var/log/sofia/reports/report_executive_*.txt | \
  mail -s "Sofia Pulse - Relatório Diário" admin@company.com
```

### 2. Auditoria Manual
```bash
# Verificar última execução
python3 scripts/generate_operational_report.py

# Ver relatório técnico completo
cat reports/report_technical_*.txt | less
```

### 3. Validação Pós-Incidente
```bash
# Verificar janela de 12 horas após crash
python3 scripts/generate_operational_report.py --since-hours 12

# Comparar com execução anterior
diff reports/report_technical_20251209_*.txt \
     reports/report_technical_20251210_*.txt
```

### 4. Base para Insights
```bash
# Gerar relatório JSON (futuro)
python3 scripts/generate_operational_report.py --format json

# Integrar com sistema de alertas
python3 scripts/generate_operational_report.py | \
  grep "UNHEALTHY" && notify-admin.sh
```

---

## Diferença: Pipeline Completo vs Runs Avulsas

### Pipeline Completo ✅
- Execução orquestrada por `run_and_verify.py` ou `daily_pipeline.py`
- Possui `trace_id` (UUID) para rastreamento
- Garante execução coordenada de todos os grupos (required, ga4, tech, research, etc.)
- WhatsApp enviado automaticamente pelo `run_and_verify.py`
- **Evidência:** Todos os runs compartilham o mesmo `trace_id`

### Runs Avulsas ⚠️
- Execuções individuais de collectors fora do pipeline
- Sem `trace_id` ou `trace_id=NULL`
- Pode indicar:
  - Teste manual de collector
  - Execução de GDELT a cada hora (caso configurado)
  - Re-run de collector isolado após falha
- **Evidência:** Runs sem `trace_id` ou com `trace_id` diferentes

**No relatório:**
- Pipeline completo → "Evidência: ✅ PIPELINE COMPLETO"
- Runs avulsas → "Evidência: ⚠️ RUNS AVULSAS DETECTADAS (pipeline completo não comprovado)"

---

## Diferença: Relatório vs WhatsApp (run_and_verify.py)

| Aspecto | run_and_verify.py | generate_operational_report.py |
|---------|-------------------|--------------------------------|
| **Quando** | Imediatamente após execução | A qualquer momento (on-demand) |
| **Fonte** | Runs acabados de executar | Banco de dados (qualquer janela) |
| **Objetivo** | Notificação em tempo real | Auditoria retrospectiva |
| **Formato** | 1 mensagem WhatsApp | 3 versões (Exec, Tech, WhatsApp) |
| **Uso** | Automático (cron 00:05) | Manual ou cron posterior |
| **Expected Source** | daily_expected_collectors.json | daily_expected_collectors.json |

**Complementares:**
- `run_and_verify.py`: "O que acabou de acontecer?"
- `generate_operational_report.py`: "O que aconteceu nas últimas N horas?"

**Ambos incluem:**
- Hash SHA256 do expected set para rastreabilidade
- 4 listas obrigatórias (sucessos, vazios, falhas, missing)
- Detecção de pipeline completo vs runs avulsas

---

## Troubleshooting

### Erro: "DATABASE_URL não configurado"
```bash
export DATABASE_URL="postgresql://sofia:senha@localhost:5432/sofia_db"
python3 scripts/generate_operational_report.py
```

### Relatório diz: "Nenhuma execução detectada"
**Causas possíveis:**
1. Cron não está rodando
2. daily_pipeline.py falhou antes de iniciar collectors
3. Janela de tempo muito curta (aumentar --since-hours)

**Verificação:**
```bash
# Ver runs recentes no banco
psql $DATABASE_URL -c "
  SELECT collector_name, started_at, ok, saved
  FROM sofia.collector_runs
  WHERE started_at >= NOW() - INTERVAL '12 hours'
  ORDER BY started_at DESC
  LIMIT 30;
"
```

### Collectors importantes aparecem em "Não Rodaram"
**Verificar:**
1. Está enabled no inventory?
   ```sql
   SELECT collector_id, enabled
   FROM sofia.collector_inventory
   WHERE collector_id IN ('ga4-analytics', 'jobs-linkedin');
   ```
2. Aparece em `daily_expected_collectors.json`?
3. Foi bloqueado pela denylist?

---

## Próximas Melhorias

- [ ] Formato JSON para integração com dashboards
- [ ] Comparação automática com execução anterior (diff)
- [ ] Envio automático por email (flag --email)
- [ ] Integração com Grafana (export metrics)
- [ ] Histórico de relatórios (banco de dados)

---

**Última atualização:** 2025-12-10
**Versão:** 1.0
**Autor:** Sofia Pulse Team
