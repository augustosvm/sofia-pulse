# Investigação: Fontes de Dados Brasileiras 🇧🇷
Data: 22/12/2025
Status: **Investigação Inicial Concluída**

## 1. MDIC ComexStat API (Ministério da Indústria, Comércio Exterior e Serviços)
**Status**: ✅ **CONFIRMADO** (API Pública Disponível)
**URL Base**: `https://api-comexstat.mdic.gov.br`
**Documentação**: `https://api-comexstat.mdic.gov.br/docs`

### Dados Disponíveis:
*   **Exportações e Importações**: Detalhadas por NCM, país, estado, município e via.
*   **Séries Históricas**: Dados mensais atualizados.
*   **Granularidade**: Alta (produto a produto).

### Estratégia de Implementação:
*   ✅ **IMPLEMENTADO**: `scripts/collect-mdic-comexstat.py`
*   Foca em: "Exportações de Alta Tecnologia" e "Importações de Insumos Estratégicos".
*   Cruzar com dados de produção industrial.

---

## 2. CNI (Confederação Nacional da Indústria)
*   **Status**: Investigado.
*   **Descoberta**: O portal "Perfil da Indústria" possui endpoints JSON ocultos que alimentam os cards e gráficos.
*   **Endpoints Verificados**:
    *   Basic Indicators: `https://industriabrasileira.portaldaindustria.com.br/cards/json/?page=total`
    *   Featured: `https://industriabrasileira.portaldaindustria.com.br/get_info_chart_featured/json/?page=total`
*   **Dados Disponíveis**: Produção Industrial, Utilização da Capacidade Instalada (UCI), Emprego Industrial, Massa Salarial.
*   **Limitação**: O endpoint de gráficos históricos (`/graph/json`) retorna HTML/protegido, mas os cards fornecem o "pulso" atual (variação mensal/anual).

### Estratégia de Implementação:
*   Criar coletor `scripts/collect-cni-indicators.py`.
*   Coletar o snapshot diário dos indicadores.
*   Armazenar histórico em `sofia.cni_industrial_indicators`.

---

## 3. FIESP (Federação das Indústrias do Estado de São Paulo)
*   **Status**: Investigado.
*   **Descoberta**: O site disponibiliza séries históricas completas em arquivos **Excel (.xlsx)** hospedados no Azure Blob Storage.
*   **Indicadores Disponíveis**:
    *   **INA (Indicador de Nível de Atividade)**: Vendas, Emprego, Salários, UCI.
    *   **Sensor Fiesp**: Pesquisa qualitativa (Mercado, Estoques, Investimento).
*   **URLs de Exemplo (Excel)**:
    *   Sensor (Com Ajuste): `https://sitefiespstorage.blob.core.windows.net/.../sensor-de-novembro-com-ajuste.xlsx`
    *   INA (Com Ajuste): `https://sitefiespstorage.blob.core.windows.net/.../lcdessazonalizadoout25.xlsx`
*   **Estratégia de Coleta**:
    *   Os links mudam mensalmente (contêm timestamp/data).
    *   É necessário um script que faça "scraping leve" da página de índices (`https://www.fiesp.com.br/indices-pesquisas-e-publicacoes/`) para encontrar os links mais recentes do mês corrente.

### Estratégia de Implementação:
*   Criar coletor `scripts/collect-fiesp-data.py`.
*   Usar `BeautifulSoup` para raspar a página de índices e encontrar os hrefs `.xlsx` mais recentes.
*   Baixar os arquivos para `data/raw/fiesp/`.
*   Processar com `pandas` e salvar em `sofia.fiesp_ina` e `sofia.fiesp_sensor`.

---

## Plano de Ação Recomendado

1.  **Imediato**: Implementar coletor do **MDIC ComexStat** (Dados de Comércio Exterior).
2.  **Segunda Fase**: Investigação profunda (Engenharia Reversa) nos portais da CNI para extrair JSONs ocultos.
3.  **Terceira Fase**: Monitoramento do FIESP (possivelmente via PDF parsing ou scraping mais complexo).

**Recomendação**: Iniciar implementação do **MDIC ComexStat** agora.
