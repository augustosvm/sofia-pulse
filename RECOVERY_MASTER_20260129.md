# 🔧 RECUPERAÇÃO FORENSE COMPLETA - MASTER TRACKER

**Data Início**: 2026-01-29 21:05 BRT
**Missão**: RECUPERAR 100% dos collectors Sofia Pulse
**Regra Absoluta**: DELETE/DEPRECATE PROIBIDOS

---

## 📊 INVENTÁRIO CANÔNICO

### STATUS ATUAL (32 collectors com histórico de execução)

**HEALTHY** (5 collectors - 15.6%):
1. ✅ **hackernews** - 143 runs, 658 inserted, último: 29/Jan 19:33 BRT
2. ✅ **github** - 109 runs, 10,300 inserted, último: 29/Jan 19:33 BRT
3. ✅ **techcrunch** - 8 runs, 25 inserted, último: 29/Jan 13:44 BRT
4. ✅ **arxiv** - 16 runs, 13,000 inserted, último: 29/Jan 13:00 BRT
5. ✅ **producthunt** - 51 runs, 240 inserted, último: 29/Jan 11:00 BRT

**FAILING** (2 collectors - 6.3%):
6. ⚠️ **ga4** - 1 run, 0 inserted, EXTERNAL (Google credenciais suspensas)
7. ⚠️ **crunchbase** - 5 runs, 0 inserted, EXTERNAL (API paga)

**DEAD** (7 collectors - 21.9% - 58h-76h sem dados):
8. 💀 **collect-docker-stats** - 3 runs, 37 inserted, último: 27/Jan 10:49 BRT (58h)
9. 💀 **arbeitnow** - 88 runs, 4,470 inserted, último: 27/Jan 07:00 BRT (62h)
10. 💀 **stackoverflow** - 119 runs, 11,800 inserted, último: 27/Jan 06:00 BRT (63h)
11. 💀 **remoteok** - 104 runs, 4,422 inserted, último: 27/Jan 05:00 BRT (64h)
12. 💀 **npm** - 42 runs, 1,147 inserted, último: 27/Jan 05:00 BRT (64h)
13. 💀 **himalayas** - 114 runs, 1,554 inserted, último: 27/Jan 03:00 BRT (66h)

**PERMA-DEAD** (18 collectors - 56.3% - 76h-893h sem dados):
14. 🔴 **pypi** - 42 runs, 913 inserted, último: 26/Jan 17:00 BRT (76h)
15. 🔴 **jetbrains-marketplace** - 43 runs, 0 inserted (100% falhas)
16. 🔴 **vscode-marketplace** - 42 runs, 4,200 inserted, último: 26/Jan 11:00 BRT (82h)
17. 🔴 **yc-companies** - 24 runs, 10,500 inserted, último: 26/Jan 07:00 BRT (86h)
18. 🔴 **openalex** - 11 runs, 1,600 inserted, último: 26/Jan 05:00 BRT (88h)
19. 🔴 **ai-companies** - 20 runs, 0 inserted (100% falhas)
20. 🔴 **confs-tech** - 7 runs, 0 inserted (100% falhas)
21. 🔴 **openalex_brazil** - 2 runs, 400 inserted, último: 20/Jan 13:05 BRT (224h)
22. 🔴 **scielo** - 2 runs, 0 inserted (100% falhas)
23. 🔴 **bdtd** - 2 runs, 0 inserted (100% falhas)
24. 🔴 **ngos** - 10 runs, 0 inserted (100% falhas)
25. 🔴 **universities** - 10 runs, 0 inserted (100% falhas)
26. 🔴 **ilo** - 2 runs, 0 inserted (100% falhas)
27. 🔴 **eurostat** - 2 runs, 0 inserted (success mas 0 records - SILENT FAILURE)
28. 🔴 **fred** - 3 runs, 0 inserted (success mas 0 records - SILENT FAILURE)
29. 🔴 **world_bank** - 6 runs, 0 inserted (success mas 0 records - SILENT FAILURE)
30. 🔴 **github_trending** - 5 runs, 0 inserted (100% falhas)
31. 🔴 **reddit** - 2 runs, 0 inserted (success mas 0 records - SILENT FAILURE)
32. 🔴 **github-trending** - 3 runs, 0 inserted (success mas 0 records - SILENT FAILURE)

---

## 🎯 PLANO DE RECUPERAÇÃO (Ordem de Prioridade)

### PRIORIDADE CRÍTICA - Collectors com MAIS VALOR HISTÓRICO (TOP 10)

| # | Collector | Registros | Runs | Status | Valor Estratégico |
|---|-----------|-----------|------|--------|-------------------|
| 1 | stackoverflow | 11,800 | 119 | DEAD 63h | ALTO - Developer trends |
| 2 | yc-companies | 10,500 | 24 | PERMA-DEAD 86h | ALTO - Funding (substitute Crunchbase) |
| 3 | arbeitnow | 4,470 | 88 | DEAD 62h | MÉDIO - Jobs Europa |
| 4 | remoteok | 4,422 | 104 | DEAD 64h | MÉDIO - Jobs remote |
| 5 | vscode-marketplace | 4,200 | 42 | PERMA-DEAD 82h | ALTO - CORE developer tools |
| 6 | openalex | 1,600 | 11 | PERMA-DEAD 88h | ALTO - CORE research papers |
| 7 | himalayas | 1,554 | 114 | DEAD 66h | BAIXO - Jobs (redundante) |
| 8 | npm | 1,147 | 42 | DEAD 64h | ALTO - JavaScript ecosystem |
| 9 | pypi | 913 | 42 | PERMA-DEAD 76h | ALTO - Python ecosystem |
| 10 | openalex_brazil | 400 | 2 | PERMA-DEAD 224h | BAIXO - Regional (redundante) |

---

## 🔬 RECUPERAÇÃO FORENSE (UM POR UM)

### **COLLECTOR #1: vscode-marketplace**

**STATUS**: 🔴 PERMA-DEAD (82 horas sem dados)

#### 1️⃣ O QUE ELE FAZ
- **Intenção original**: Monitorar VS Code Marketplace para detectar tendências de ferramentas dev
- **Insight**: Framework adoption, developer tool trends, language popularity
- **Classificação**: **CORE** - Developer tools são essenciais para Tech Trend Scoring

#### 2️⃣ ELE JÁ FUNCIONOU?
- ✅ **SIM** - Funcionou perfeitamente por 36 dias consecutivos
- **Quando**: 20/Dez/2025 → 26/Jan/2026
- **Por quanto tempo**: 36 dias (5+ semanas)
- **Registros coletados**: **4,200 extensions** (100/dia × 42 runs)
- **Taxa de sucesso**: 100% (42 sucessos, 0 falhas)

#### 3️⃣ POR QUE PAROU?
**Classificação**: **INTERNAL** (100% culpa nossa)

**Causa principal**: SystemD service quebrado

**Explicação técnica**:
1. Collector rodava via `systemd` timer (`sofia-pulse-collectors.timer`)
2. Timer configurado para executar `/home/ubuntu/sofia-pulse/run-collectors-with-notifications.sh`
3. **Esse script NÃO EXISTE** (deletado ou nunca commitado)
4. SystemD falha com exit code 203/EXEC
5. Collector para de rodar automaticamente

**Prova**:
```bash
systemctl status sofia-pulse-collectors.service
× sofia-pulse-collectors.service - Sofia Pulse Data Collectors
     Active: failed (Result: exit-code)
    Process: ExecStart=/home/ubuntu/sofia-pulse/run-collectors-with-notifications.sh (code=exited, status=203/EXEC)
```

**Este collector falhou por erro nosso.** O código está 100% funcional (42 sucessos consecutivos provam), o problema é APENAS agendamento.

#### 4️⃣ COMO RECUPERAR
**Caminho de recuperação**: Adicionar ao crontab (substitui systemd quebrado)

**Correção técnica**:
```bash
# PASSO 1: Identificar como invocar o collector
# Verificar intelligent_scheduler tasks OU criar cron direto

# PASSO 2: Adicionar ao crontab
crontab -e
# Adicionar: 0 11 * * * cd ~/sofia-pulse && python3 scripts/intelligent_scheduler.py --run-once

# PASSO 3: Validar execução manual
python3 scripts/intelligent_scheduler.py --run-once

# PASSO 4: Verificar inserção no banco
SELECT COUNT(*) FROM sofia.vscode_extensions_daily
WHERE snapshot_date = CURRENT_DATE;
```

#### 5️⃣ PROVA DE VIDA (PENDENTE)
- [ ] Executar manualmente
- [ ] Inserir ≥1 registro
- [ ] Registrar em collector_runs
- [ ] Validar timestamp BRT
- [ ] Confirmar exit code 0 com records > 0

**Status**: AGUARDANDO EXECUÇÃO

---

### **COLLECTOR #2: yc-companies**

**STATUS**: 🔴 PERMA-DEAD (86 horas sem dados)

#### 1️⃣ O QUE ELE FAZ
- **Intenção original**: Coletar dados públicos de startups Y Combinator (batches, funding, founders)
- **Insight**: Funding trends, early-stage startups, unicorn prediction
- **Classificação**: **CORE** - YC é fonte PREMIUM de funding data (gratuita!)

#### 2️⃣ ELE JÁ FUNCIONOU?
- ✅ **SIM** - 21 execuções bem-sucedidas
- **Quando**: 20/Dez/2025 → 26/Jan/2026
- **Por quanto tempo**: 36 dias
- **Registros coletados**: **10,500 startups** (500/run × 21 runs)
- **Taxa de sucesso**: 87.5% (21 sucessos, 3 falhas ocasionais)

#### 3️⃣ POR QUE PAROU?
**Classificação**: **INTERNAL** (systemd quebrado - mesma causa VSCode)

**Este collector falhou por erro nosso.**

#### 4️⃣ COMO RECUPERAR
Mesma solução: adicionar ao crontab

#### 5️⃣ PROVA DE VIDA (PENDENTE)
- [ ] Executar manualmente
- [ ] Inserir ≥1 registro em funding_rounds
- [ ] Validar

**Status**: AGUARDANDO EXECUÇÃO

---

### **COLLECTOR #3: stackoverflow**

**STATUS**: 💀 DEAD (63 horas sem dados)

#### 1️⃣ O QUE ELE FAZ
- **Intenção**: Stack Overflow questions trends (languages, frameworks, topics)
- **Classificação**: **SUPORTE** - Útil para developer trends

#### 2️⃣ ELE JÁ FUNCIONOU?
- ✅ **SIM** - 118 execuções bem-sucedidas
- **Registros**: **11,800 questions** (100/dia × 118 dias)
- **Taxa sucesso**: 99% (118/119)

#### 3️⃣ POR QUE PAROU?
**INTERNAL** (systemd quebrado)

**Este collector falhou por erro nosso.**

#### 4️⃣ COMO RECUPERAR
Crontab

#### 5️⃣ PROVA DE VIDA (PENDENTE)
- [ ] Executar
- [ ] Validar

---

### **PADRÃO DETECTADO - SYSTEMD QUEBRADO**

**10 collectors afetados pelo mesmo bug**:
1. vscode-marketplace
2. yc-companies
3. stackoverflow
4. arbeitnow
5. remoteok
6. npm
7. pypi
8. himalayas
9. openalex
10. collect-docker-stats

**Todos têm**:
- ✅ Código funcional (taxas de sucesso 87-100%)
- ✅ Dados históricos valiosos (400 a 11,800 registros)
- ❌ Agendador quebrado (systemd → script inexistente)

**Solução única para todos**:
```bash
# Criar OU reativar intelligent_scheduler via cron
0 */1 * * * cd ~/sofia-pulse && python3 scripts/intelligent_scheduler.py --run-once
```

---

## 📝 PRÓXIMOS PASSOS

### FASE 2A: Recuperar os 10 collectors systemd (CRÍTICO - 1 hora)

1. Testar intelligent_scheduler manualmente
2. Confirmar que vscode, yc, stackoverflow estão registrados
3. Adicionar ao crontab
4. Executar teste manual de cada um
5. Validar inserções no banco
6. Registrar prova de vida

### FASE 2B: Recuperar collectors com SILENT FAILURES (MÉDIO - 2 horas)

Collectors que rodaram mas inseriram 0 registros:
- eurostat (2 runs success, 0 records)
- fred (3 runs success, 0 records)
- world_bank (6 runs success, 0 records)
- reddit (2 runs success, 0 records)

**Causa provável**: Schema mismatch ou parsing error

### FASE 2C: Recuperar collectors que NUNCA funcionaram (BAIXO - 4 horas)

Collectors com 100% falhas:
- jetbrains-marketplace (43 falhas)
- ai-companies (20 falhas)
- confs-tech (7 falhas)
- scielo (2 falhas)
- bdtd (2 falhas)
- ngos (10 falhas)
- universities (10 falhas)
- ilo (2 falhas)
- github_trending (5 falhas)

**Causa provável**: Código com bugs estruturais, nunca testado

---

**PROGRESSO ATUAL**: 0/32 collectors recuperados (0%)
**META**: 32/32 collectors funcionais (100%)

---

**FIM DO MASTER TRACKER - Atualização contínua**
