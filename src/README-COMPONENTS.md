# 🎨 Sofia Pulse - Dashboard Components

Componentes React criados para o dashboard do Sofia Pulse, seguindo o padrão do VirtualArena.

## 📁 Estrutura de Arquivos

```
src/
├── components/
│   ├── regional-cards.tsx           # Cards regionais simples e discretos
│   ├── insights-carousel.tsx        # Carrossel com 15 insights + auto-play
│   ├── top-technologies.tsx         # TOP 6 tecnologias (gráfico vertical cyan)
│   ├── top-ais.tsx                  # TOP 6 IAs (gráfico vertical purple)
│   └── academia-vs-mercado.tsx      # 4 quadrantes com 5 techs cada
├── pages/
│   └── pulse.tsx                    # Página principal que integra todos
└── styles/
    └── globals.css                  # CSS com animações (shimmer, fade-in, etc.)
```

## 🚀 Como Usar

### Opção 1: Integrar em Next.js/React

1. Copie a pasta `src/components` para seu projeto
2. Copie `src/styles/globals.css` para seu projeto
3. Importe os componentes na sua página:

```tsx
import { RegionalCards } from '@/components/regional-cards';
import { InsightsCarousel } from '@/components/insights-carousel';
import { TopTechnologies } from '@/components/top-technologies';
import { TopAIs } from '@/components/top-ais';
import { AcademiaVsMercado } from '@/components/academia-vs-mercado';

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <RegionalCards />
      <InsightsCarousel />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TopTechnologies />
        <TopAIs />
      </div>
      <AcademiaVsMercado />
    </div>
  );
}
```

### Opção 2: Versão HTML Standalone

Use o arquivo `pulse-dashboard.html` (standalone) para testar sem framework:

```bash
# Abrir no navegador
open pulse-dashboard.html
```

## 📊 Componentes

### 1. RegionalCards
- **Descrição**: Cards simples mostrando insights regionais
- **Features**:
  - 4 regiões (Oceania, Europa, América do Norte, Ásia)
  - Gradientes de cores diferentes por região
  - Hover effect com scale
  - Crescimento em %

### 2. InsightsCarousel
- **Descrição**: Carrossel com 15 insights de tecnologia
- **Features**:
  - ✅ **15 insights** (aumentado de 5)
  - ✅ **Auto-play** a cada 5 segundos
  - Navegação manual (prev/next)
  - Indicadores de posição (dots)
  - 2 categorias: Skills (verde) e Tecnologias Mortas (vermelho)
  - 3 cards visíveis por vez

### 3. TopTechnologies
- **Descrição**: TOP 6 tecnologias mais populares
- **Features**:
  - 6 plataformas: GitHub, npm, PyPI, HN, StackOverflow, Reddit
  - Gráficos horizontais com gradiente **cyan-blue-purple**
  - Shimmer effect nas barras
  - Crescimento em %
  - Métricas diferentes por plataforma (stars, downloads, mentions, etc.)

### 4. TopAIs
- **Descrição**: TOP 6 IAs mais citadas
- **Features**:
  - 6 plataformas: Papers, GitHub, npm, HN, StackOverflow, Reddit
  - Gráficos horizontais com gradiente **purple-pink-rose** (diferente!)
  - Shimmer effect nas barras
  - Crescimento em %
  - Métricas diferentes por plataforma

### 5. AcademiaVsMercado
- **Descrição**: Quadrantes com 5 tecnologias cada
- **Features**:
  - 4 quadrantes:
    1. **Líderes** 🏆 (alto papers + alto jobs) - roxo
    2. **Apenas Pesquisa** 🔬 (alto papers, baixo jobs) - cyan
    3. **Pronto para Produção** 📦 (baixo papers, alto jobs) - verde
    4. **Emergentes** 🌱 (baixo papers, baixo jobs) - laranja
  - Gráficos horizontais para Papers e Jobs
  - 5 tecnologias por quadrante

## 🎨 CSS e Animações

O arquivo `globals.css` inclui:

- ✅ **Shimmer animation** - Efeito brilhante nas barras
- ✅ **Fade-in animation** - Entrada suave dos cards
- ✅ **Custom scrollbar** - Scrollbar estilizada
- ✅ **Hover effects** - Scale, shadows, etc.
- ✅ **Gradient text utilities** - Textos com gradiente
- ✅ **Backdrop blur** - Efeito de blur nos cards

## 🔧 Customização

### Mudar cores dos quadrantes

Edite `academia-vs-mercado.tsx`:

```tsx
// Líderes (roxo)
<div className="bg-purple-900/30 ... border-purple-500/30">

// Apenas Pesquisa (cyan)
<div className="bg-cyan-900/30 ... border-cyan-500/30">

// Pronto para Produção (verde)
<div className="bg-green-900/30 ... border-green-500/30">

// Emergentes (laranja)
<div className="bg-orange-900/30 ... border-orange-500/30">
```

### Mudar auto-play speed

Edite `insights-carousel.tsx`:

```tsx
// Linha 123: 5000ms = 5 segundos
const interval = setInterval(() => {
  // ...
}, 5000); // Mude para 3000 (3 segundos), 10000 (10 segundos), etc.
```

### Adicionar mais insights

Edite `insights-carousel.tsx`:

```tsx
const INSIGHTS = [
  // ... insights existentes
  {
    categoria: "Skill",
    titulo: "Novo insight",
    descricao: "Descrição do insight...",
    badge: "BADGE TEXTO",
    cor: "green" // ou "red"
  }
];
```

## ✅ Checklist de Implementação

- [x] Regional cards SIMPLES (com blur e hover)
- [x] Insights carousel com **15 insights**
- [x] Insights carousel com **auto-play**
- [x] Top Tecnologias: TOP 6, gráfico VERTICAL (horizontal bars), gradiente cyan
- [x] Top IAs: TOP 6, gráfico VERTICAL (horizontal bars), gradiente purple (DIFERENTE!)
- [x] Academia vs Mercado: 5 techs por quadrante, gráficos HORIZONTAIS

## 🎯 Próximos Passos

1. **Conectar com API real** - Substituir dados mockados por dados do Sofia Pulse
2. **Responsividade mobile** - Testar em dispositivos móveis
3. **Dark/Light mode** - Adicionar toggle de tema
4. **Exportar relatórios** - Botão para download de insights em PDF/CSV
5. **Filtros** - Adicionar filtros por data, região, categoria

## 📦 Dependências

Se usar Next.js/React:

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "next": "^14.0.0",
    "tailwindcss": "^3.4.0"
  }
}
```

**IMPORTANTE**: Nenhuma biblioteca adicional necessária! Apenas React e TailwindCSS.

## 🐛 Troubleshooting

### "Cannot find module '@/components/...'"

Adicione ao `tsconfig.json`:

```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### CSS não está funcionando

1. Verifique se `globals.css` está importado no `_app.tsx` ou `layout.tsx`
2. Verifique se TailwindCSS está configurado corretamente

### Auto-play não funciona

Verifique se o componente está marcado como `'use client'` (Next.js 13+):

```tsx
'use client';

import { useState, useEffect } from 'react';
// ...
```

---

**Criado em**: 18 Dez 2025
**Autor**: Claude + Sofia Pulse Team
**Versão**: 1.0.0
