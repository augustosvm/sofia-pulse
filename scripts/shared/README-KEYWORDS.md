# Configuração Centralizada de Keywords

## Visão Geral
Sistema centralizado de keywords multi-idioma reutilizável para todos os coletores e análises do projeto Sofia Pulse.

## Estrutura

### Arquivo Principal
`scripts/shared/keywords-config.ts`

### Categorias Disponíveis (15)
1. **desenvolvimento-geral** - Termos gerais de desenvolvimento
2. **frontend** - React, Vue, Angular, Next.js
3. **backend** - Node.js, Java, Python, .NET, Golang
4. **fullstack** - Full-stack developers
5. **ia-ml** - IA, ML, LLM, Deep Learning, NLP
6. **devops-cloud** - DevOps, SRE, AWS, Azure, GCP, Kubernetes
7. **dados** - Data Engineer, DBA, Big Data, Analytics
8. **qa-testes** - QA, Test Automation, SDET
9. **seguranca** - Cybersecurity, InfoSec, Pentest
10. **redes** - Network Engineer, Infrastructure
11. **gestao-lideranca** - Tech Lead, Engineering Manager, CTO
12. **plataformas-especificas** - Salesforce, SAP, Oracle, TOTVS
13. **mobile** - Android, iOS, React Native, Flutter
14. **web3-blockchain** - Blockchain, Web3, Solidity, DeFi
15. **game-dev** - Unity, Unreal Engine, Game Design

## Idiomas Suportados
- **pt**: Português (Brasil)
- **en**: Inglês
- **es**: Espanhol (opcional)

## Como Usar

### 1. Importar no seu coletor
```typescript
import { getKeywordsByLanguage, getKeywordsByCategory } from './shared/keywords-config';
```

### 2. Obter todas as keywords de um idioma
```typescript
// Português (padrão)
const keywordsPT = getKeywordsByLanguage('pt');

// Inglês
const keywordsEN = getKeywordsByLanguage('en');

// Espanhol
const keywordsES = getKeywordsByLanguage('es');
```

### 3. Obter keywords de uma categoria específica
```typescript
// Apenas keywords de IA/ML em português
const aiKeywords = getKeywordsByCategory('ia-ml', 'pt');

// Apenas keywords de frontend em inglês
const frontendKeywords = getKeywordsByCategory('frontend', 'en');
```

### 4. Listar todas as categorias
```typescript
import { getCategories } from './shared/keywords-config';

const categories = getCategories();
// ['desenvolvimento-geral', 'frontend', 'backend', ...]
```

## Exemplo de Uso em Coletores

### Catho (Português - Brasil)
```typescript
const keywords = getKeywordsByLanguage('pt');
// Retorna todas as keywords em português
```

### LinkedIn/Indeed (Inglês)
```typescript
const keywords = getKeywordsByLanguage('en');
// Retorna todas as keywords em inglês
```

### InfoJobs (Espanhol)
```typescript
const keywords = getKeywordsByLanguage('es');
// Retorna keywords em espanhol (quando disponível)
```

## Expansão Futura

O arquivo já está preparado para outras finalidades:

### Research Keywords
```typescript
export const RESEARCH_KEYWORDS = {
  'ai-research': ['artificial intelligence', 'machine learning', ...],
  'quantum-computing': ['quantum computing', 'quantum algorithms', ...],
  'biotech': ['biotechnology', 'genomics', 'crispr', ...],
};
```

### Trend Keywords
```typescript
export const TREND_KEYWORDS = {
  'emerging-tech': ['generative ai', 'llm', 'chatgpt', ...],
  'sustainability': ['green tech', 'renewable energy', ...],
};
```

## Vantagens

✅ **Centralização**: Uma única fonte de verdade para keywords
✅ **Multi-idioma**: Suporte para PT, EN, ES
✅ **Reutilizável**: Pode ser usado por qualquer coletor
✅ **Organizado**: Keywords agrupadas por categoria
✅ **Expansível**: Fácil adicionar novas categorias ou idiomas
✅ **Manutenível**: Atualizar em um lugar reflete em todos os coletores

## Adicionando Novas Keywords

### 1. Adicionar em categoria existente
```typescript
{
  category: 'frontend',
  keywords: {
    pt: ['frontend', 'front-end', 'svelte'], // Adicionar 'svelte'
    en: ['frontend', 'front-end', 'react', 'vue', 'angular', 'svelte']
  }
}
```

### 2. Criar nova categoria
```typescript
{
  category: 'design',
  keywords: {
    pt: ['ui-designer', 'ux-designer', 'product-designer'],
    en: ['ui-designer', 'ux-designer', 'product-designer', 'figma', 'sketch']
  }
}
```

### 3. Adicionar novo idioma
```typescript
{
  category: 'frontend',
  keywords: {
    pt: ['frontend', 'front-end'],
    en: ['frontend', 'front-end'],
    es: ['frontend', 'desarrollador-frontend'],
    fr: ['frontend', 'développeur-frontend'] // Novo idioma
  }
}
```

## Coletores que Devem Usar

- ✅ `collect-catho-final.ts` (já implementado)
- ⏳ `collect-jobs-adzuna.ts`
- ⏳ `collect-jobs-arbeitnow.ts`
- ⏳ `collect-jobs-github.ts`
- ⏳ `collect-jobs-themuse.ts`
- ⏳ `collect-jobs-usajobs.ts`
- ⏳ Todos os outros coletores de vagas

## Notas Importantes

⚠️ **Atenção ao idioma da plataforma**: Plataformas em português (Catho, InfoJobs Brasil) devem usar `getKeywordsByLanguage('pt')`. Plataformas internacionais devem usar `getKeywordsByLanguage('en')`.

⚠️ **Limitações de API**: Alguns coletores podem ter limite de keywords por requisição. Neste caso, use `keywords.slice(0, N)` para limitar.

## Total de Keywords
- **Português**: ~80 keywords
- **Inglês**: ~100 keywords
- **Espanhol**: ~20 keywords (parcial)
