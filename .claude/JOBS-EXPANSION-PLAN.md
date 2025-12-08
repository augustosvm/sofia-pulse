# 🌍 FONTES DE DADOS DE EMPREGOS - PLANO DE EXPANSÃO

**Data**: 2025-12-08  
**Status Atual**: 24 vagas (muito pouco)  
**Meta**: 1000+ vagas/dia de fontes globais

---

## 📊 STATUS ATUAL

### Fontes Ativas
- ✅ **Remotive** - 7 vagas coletadas
- ✅ **Outra plataforma** - 12 vagas coletadas
- **Total**: 19 vagas/coleta (insuficiente)

### Coletores Existentes
1. `collect-jobs-api-only.ts` - Funcionando
2. `collect-jobs-brazil-specific.ts` - Não testado
3. `collect-jobs-global-platforms.ts` - Não testado
4. `collect-jobs-multi-platform.ts` - Não testado
5. `collect-linkedin-jobs.ts` - Não testado

---

## 🎯 NOVAS FONTES RECOMENDADAS

### Tier 1: APIs Gratuitas (Implementar AGORA)

#### 1. **Adzuna API** ⭐⭐⭐⭐⭐
- **URL**: https://developer.adzuna.com/
- **Cobertura**: 20+ países (UK, US, CA, AU, DE, FR, BR, etc)
- **Volume**: ~50k vagas tech/dia
- **API**: Gratuita (5000 calls/mês)
- **Dados**: Salário, empresa, localização, remote
- **Prioridade**: ALTA

#### 2. **The Muse API** ⭐⭐⭐⭐
- **URL**: https://www.themuse.com/developers/api/v2
- **Cobertura**: Global, foco em tech
- **Volume**: ~10k vagas tech
- **API**: Gratuita
- **Dados**: Empresa, benefícios, cultura
- **Prioridade**: ALTA

#### 3. **GitHub Jobs API** ⭐⭐⭐⭐
- **URL**: https://jobs.github.com/api
- **Cobertura**: Global, 100% tech
- **Volume**: ~5k vagas
- **API**: Gratuita, sem limite
- **Dados**: Remote-first, tech stack
- **Prioridade**: ALTA

#### 4. **Remotive API** ⭐⭐⭐⭐
- **URL**: https://remotive.com/api
- **Cobertura**: Global, remote-first
- **Volume**: ~2k vagas
- **API**: Gratuita
- **Dados**: Remote, tech, startups
- **Prioridade**: MÉDIA (já temos)

#### 5. **Arbeitnow API** ⭐⭐⭐⭐
- **URL**: https://www.arbeitnow.com/api
- **Cobertura**: Europa (DE, NL, UK, FR)
- **Volume**: ~8k vagas tech
- **API**: Gratuita
- **Dados**: Visa sponsorship, relocation
- **Prioridade**: ALTA

#### 6. **USAJOBS API** ⭐⭐⭐
- **URL**: https://developer.usajobs.gov/
- **Cobertura**: USA (governo)
- **Volume**: ~5k vagas tech
- **API**: Gratuita, requer registro
- **Dados**: Salário público, benefícios
- **Prioridade**: MÉDIA

### Tier 2: Web Scraping (Implementar depois)

#### 7. **LinkedIn Jobs** ⭐⭐⭐⭐⭐
- **Volume**: 100k+ vagas tech/dia
- **Método**: Scraping (já temos script)
- **Desafio**: Rate limiting, anti-bot
- **Prioridade**: ALTA (testar script existente)

#### 8. **Indeed API** ⭐⭐⭐⭐⭐
- **URL**: https://opensource.indeedeng.io/api-documentation/
- **Cobertura**: 60+ países
- **Volume**: 200k+ vagas tech/dia
- **API**: Requer parceria
- **Prioridade**: MÉDIA

#### 9. **Glassdoor API** ⭐⭐⭐⭐
- **Volume**: 50k+ vagas tech
- **Dados**: Salários, reviews de empresas
- **API**: Requer parceria
- **Prioridade**: BAIXA

#### 10. **AngelList (Wellfound)** ⭐⭐⭐⭐
- **URL**: https://wellfound.com/
- **Cobertura**: Startups globais
- **Volume**: 20k+ vagas
- **Método**: Scraping
- **Prioridade**: ALTA

### Tier 3: Agregadores Regionais

#### 11. **Catho (Brasil)** ⭐⭐⭐
- **Volume**: 10k+ vagas tech BR
- **Método**: Scraping
- **Prioridade**: MÉDIA

#### 12. **InfoJobs (LATAM/Europa)** ⭐⭐⭐
- **Volume**: 15k+ vagas
- **Cobertura**: BR, ES, IT
- **Prioridade**: MÉDIA

#### 13. **Seek (Austrália/NZ)** ⭐⭐⭐
- **Volume**: 8k+ vagas tech
- **API**: Limitada
- **Prioridade**: BAIXA

#### 14. **StepStone (Europa)** ⭐⭐⭐
- **Volume**: 20k+ vagas
- **Cobertura**: DE, UK, NL, BE
- **Prioridade**: MÉDIA

---

## 🚀 PLANO DE IMPLEMENTAÇÃO

### Fase 1: Quick Wins (Esta Semana)
1. ✅ Implementar **Adzuna API** (5 países principais)
2. ✅ Implementar **The Muse API**
3. ✅ Implementar **GitHub Jobs API**
4. ✅ Implementar **Arbeitnow API**
5. ✅ Testar `collect-linkedin-jobs.ts` existente

**Meta**: 500+ vagas/dia

### Fase 2: Expansão (Próxima Semana)
6. ⏳ Implementar **USAJOBS API**
7. ⏳ Implementar **AngelList scraper**
8. ⏳ Testar `collect-jobs-global-platforms.ts`
9. ⏳ Adicionar mais países no Adzuna

**Meta**: 1000+ vagas/dia

### Fase 3: Otimização (Mês que vem)
10. ⏳ Implementar deduplicação avançada
11. ⏳ Adicionar Indeed (se conseguir parceria)
12. ⏳ Adicionar agregadores regionais
13. ⏳ Criar sistema de scoring de qualidade

**Meta**: 2000+ vagas/dia

---

## 💻 CÓDIGO EXEMPLO - Adzuna API

```typescript
// scripts/collect-jobs-adzuna.ts
import axios from 'axios';
import { Client } from 'pg';

const ADZUNA_APP_ID = process.env.ADZUNA_APP_ID;
const ADZUNA_API_KEY = process.env.ADZUNA_API_KEY;

const COUNTRIES = ['us', 'gb', 'ca', 'au', 'de', 'fr', 'br', 'nl'];
const KEYWORDS = ['software engineer', 'data scientist', 'devops', 'frontend', 'backend'];

async function collectAdzunaJobs() {
  const client = new Client({...dbConfig});
  await client.connect();

  for (const country of COUNTRIES) {
    for (const keyword of KEYWORDS) {
      const url = `https://api.adzuna.com/v1/api/jobs/${country}/search/1`;
      const params = {
        app_id: ADZUNA_APP_ID,
        app_key: ADZUNA_API_KEY,
        what: keyword,
        results_per_page: 50,
        category: 'it-jobs'
      };

      const response = await axios.get(url, { params });
      
      for (const job of response.data.results) {
        await client.query(`
          INSERT INTO sofia.tech_jobs (
            job_id, platform, title, company, location, country,
            description, posted_date, salary_min, salary_max,
            salary_currency, url, search_keyword, collected_at
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW())
          ON CONFLICT (job_id, platform) DO NOTHING
        `, [
          job.id, 'adzuna', job.title, job.company.display_name,
          job.location.display_name, country.toUpperCase(),
          job.description, job.created, 
          job.salary_min, job.salary_max, 'USD',
          job.redirect_url, keyword
        ]);
      }
      
      await new Promise(r => setTimeout(r, 1000)); // Rate limit
    }
  }

  await client.end();
}
```

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### Preparação
- [ ] Registrar em Adzuna API
- [ ] Registrar em The Muse API
- [ ] Registrar em USAJOBS API
- [ ] Adicionar API keys no `.env`

### Desenvolvimento
- [ ] Criar `collect-jobs-adzuna.ts`
- [ ] Criar `collect-jobs-themuse.ts`
- [ ] Criar `collect-jobs-github.ts`
- [ ] Criar `collect-jobs-arbeitnow.ts`
- [ ] Atualizar `cron-collect-jobs.sh` para rodar todos

### Testes
- [ ] Testar cada coletor individualmente
- [ ] Verificar deduplicação
- [ ] Validar dados de salário
- [ ] Testar cron job completo

### Deploy
- [ ] Commitar novos coletores
- [ ] Atualizar crontab
- [ ] Monitorar logs por 24h
- [ ] Validar volume de dados

---

## 📊 MÉTRICAS DE SUCESSO

### Atual
- Vagas/dia: 19
- Empresas: 8
- Países: 2-3

### Meta Fase 1 (1 semana)
- Vagas/dia: 500+
- Empresas: 200+
- Países: 10+

### Meta Fase 2 (1 mês)
- Vagas/dia: 1000+
- Empresas: 500+
- Países: 20+

### Meta Final (3 meses)
- Vagas/dia: 2000+
- Empresas: 1000+
- Países: 30+

---

**Última Atualização**: 2025-12-08 16:47
