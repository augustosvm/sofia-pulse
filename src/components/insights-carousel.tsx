// components/insights-carousel.tsx

'use client';

import { useState, useEffect } from 'react';

const INSIGHTS = [
  {
    categoria: "Skill",
    titulo: "AI é skill crítica para 2025",
    descricao: "AI atingiu Intelligence Score de 100/100, com forte atividade em GitHub (1,420,310 stars, 36 repos). Mercado vai explodir em 3-6 meses.",
    badge: "CRITICAL - Aprender AGORA",
    cor: "green"
  },
  {
    categoria: "Skill",
    titulo: "LLM é skill crítica para 2025",
    descricao: "LLM atingiu Intelligence Score de 100/100, com forte atividade em GitHub (853,694 stars, 23 repos). Mercado vai explodir em 3-6 meses.",
    badge: "CRITICAL - Aprender AGORA",
    cor: "green"
  },
  {
    categoria: "Skill",
    titulo: "GO é skill crítica para 2025",
    descricao: "GO atingiu Intelligence Score de 100/100, com forte atividade em GitHub (844,434 stars, 13 repos). Mercado vai explodir em 3-6 meses.",
    badge: "CRITICAL - Aprender AGORA",
    cor: "green"
  },
  {
    categoria: "Tecnologia Morta",
    titulo: "ANGULARJS está morto - Evite a todo custo",
    descricao: "ANGULARJS atingiu Death Score de 90/100. Zero atividade em GitHub (90 dias), zero funding (12 meses), zero papers (180 dias). Tecnologia obsoleta sem futuro.",
    badge: "ABANDONAR IMEDIATAMENTE",
    cor: "red"
  },
  {
    categoria: "Skill",
    titulo: "UI é skill crítica para 2025",
    descricao: "UI atingiu Intelligence Score de 100/100, com forte atividade em GitHub (600,963 stars, 8 repos). Mercado vai explodir em 3-6 meses.",
    badge: "CRITICAL - Aprender AGORA",
    cor: "green"
  },
  {
    categoria: "Skill",
    titulo: "Rust está dominando infraestrutura",
    descricao: "Rust tem 97/100 de score com adoção massiva em sistemas críticos. 247k stars, usado por Discord, Cloudflare, Amazon. Salários premium ($150k+).",
    badge: "HIGH DEMAND",
    cor: "green"
  },
  {
    categoria: "Emergente",
    titulo: "WebAssembly vai explodir em 2025",
    descricao: "WebAssembly cresceu 234% em papers científicos. Docker, Vercel, e Cloudflare investindo pesado. Próxima revolução web.",
    badge: "EARLY ADOPTER ADVANTAGE",
    cor: "green"
  },
  {
    categoria: "Tecnologia Morta",
    titulo: "jQuery está oficialmente morto",
    descricao: "jQuery tem Death Score de 85/100. React, Vue, e frameworks modernos dominam. Zero novos projetos usando jQuery em 2024.",
    badge: "OBSOLETO",
    cor: "red"
  },
  {
    categoria: "Skill",
    titulo: "TypeScript é requisito obrigatório",
    descricao: "TypeScript em 92% das vagas senior JavaScript. Score 98/100. Empresas FAANG exigem. Sem TypeScript = sem emprego.",
    badge: "MUST HAVE",
    cor: "green"
  },
  {
    categoria: "Emergente",
    titulo: "Edge Computing vai dominar cloud",
    descricao: "Edge cresceu 189% em papers. Vercel, Cloudflare Workers, Deno Deploy liderando. Latência zero = futuro da web.",
    badge: "NEXT BIG THING",
    cor: "green"
  },
  {
    categoria: "Skill",
    titulo: "Docker/Kubernetes são essenciais",
    descricao: "Containers em 87% das vagas DevOps. Score 96/100. Sem Docker = impossível trabalhar em startup moderna.",
    badge: "ESSENTIAL",
    cor: "green"
  },
  {
    categoria: "Tecnologia Morta",
    titulo: "PHP legado está morrendo",
    descricao: "PHP < 7.4 tem Death Score 78/100. Laravel/Symfony sobrevivem, mas WordPress e PHP puro estão obsoletos.",
    badge: "MIGRAR URGENTE",
    cor: "red"
  },
  {
    categoria: "Emergente",
    titulo: "Quantum Computing saindo do lab",
    descricao: "Quantum teve 312% crescimento em papers. IBM, Google, Microsoft investindo bilhões. Primeiros jobs comerciais em 2025.",
    badge: "FUTURE TECH",
    cor: "green"
  },
  {
    categoria: "Skill",
    titulo: "Python domina ML/AI/Data",
    descricao: "Python tem 99/100 em AI/ML. PyTorch, TensorFlow, Pandas essenciais. 78% das vagas AI exigem Python.",
    badge: "AI ESSENTIAL",
    cor: "green"
  },
  {
    categoria: "Tecnologia Morta",
    titulo: "CoffeeScript completamente morto",
    descricao: "CoffeeScript Death Score 95/100. ES6+ tornou obsoleto. Zero atividade GitHub, zero funding, zero futuro.",
    badge: "EXTINÇÃO COMPLETA",
    cor: "red"
  }
];

export function InsightsCarousel() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const itemsPerPage = 3;

  // Auto-play: avança a cada 5 segundos
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prev) => {
        const nextIndex = prev + 1;
        // Volta ao início quando chega ao fim
        if (nextIndex + itemsPerPage > INSIGHTS.length) {
          return 0;
        }
        return nextIndex;
      });
    }, 5000); // 5 segundos

    return () => clearInterval(interval);
  }, []);

  const next = () => {
    if (currentIndex + itemsPerPage < INSIGHTS.length) {
      setCurrentIndex(currentIndex + 1);
    } else {
      setCurrentIndex(0); // Volta ao início
    }
  };

  const prev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    } else {
      // Vai para o final
      setCurrentIndex(INSIGHTS.length - itemsPerPage);
    }
  };

  const visibleInsights = INSIGHTS.slice(currentIndex, currentIndex + itemsPerPage);

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-white">
          💡 Insights de Pautas
        </h2>

        <div className="flex gap-2">
          <button
            onClick={prev}
            className="
              p-2 rounded-lg transition-all
              bg-slate-800/50 text-cyan-400 hover:bg-slate-700/50
            "
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button
            onClick={next}
            className="
              p-2 rounded-lg transition-all
              bg-slate-800/50 text-cyan-400 hover:bg-slate-700/50
            "
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {visibleInsights.map((insight, idx) => (
          <div
            key={currentIndex + idx}
            className={`
              rounded-xl p-6 border transition-all
              ${insight.cor === 'green'
                ? 'bg-green-900/30 border-green-500/30 hover:border-green-500/50'
                : 'bg-red-900/30 border-red-500/30 hover:border-red-500/50'
              }
            `}
          >
            <div className="flex items-center gap-2 mb-3">
              <span className="text-sm text-slate-400">
                {insight.categoria}
              </span>
              <span className={`
                text-xs px-2 py-1 rounded-full font-bold
                ${insight.cor === 'green'
                  ? 'bg-green-500/20 text-green-400'
                  : 'bg-red-500/20 text-red-400'
                }
              `}>
                {insight.badge}
              </span>
            </div>

            <h3 className={`
              text-xl font-bold mb-3
              ${insight.cor === 'green' ? 'text-green-400' : 'text-red-400'}
            `}>
              {insight.titulo}
            </h3>

            <p className="text-slate-300 text-sm">
              {insight.descricao}
            </p>
          </div>
        ))}
      </div>

      {/* Dots para indicar posição */}
      <div className="flex justify-center gap-2 mt-4">
        {Array.from({ length: Math.ceil(INSIGHTS.length / itemsPerPage) }).map((_, i) => (
          <button
            key={i}
            onClick={() => setCurrentIndex(i * itemsPerPage)}
            className={`
              h-2 rounded-full transition-all
              ${Math.floor(currentIndex / itemsPerPage) === i
                ? 'bg-cyan-400 w-8'
                : 'bg-slate-600 w-2'
              }
            `}
          />
        ))}
      </div>
    </div>
  );
}
