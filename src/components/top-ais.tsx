// components/top-ais.tsx

'use client';

import { useState } from 'react';

const PLATAFORMAS = ['Papers', 'GitHub', 'npm', 'HN', 'StackOverflow', 'Reddit'];

const IAS: Record<string, Array<{ rank: number; nome: string; citacoes?: number; stars?: number; downloads?: number; mentions?: number; questions?: number; posts?: number; crescimento: number }>> = {
  Papers: [
    { rank: 1, nome: 'GPT-4', citacoes: 5678, crescimento: 234 },
    { rank: 2, nome: 'Claude', citacoes: 3124, crescimento: 189 },
    { rank: 3, nome: 'Gemini', citacoes: 1892, crescimento: 156 },
    { rank: 4, nome: 'LLaMA', citacoes: 1234, crescimento: 92 },
    { rank: 5, nome: 'Mistral', citacoes: 678, crescimento: 267 },
    { rank: 6, nome: 'PaLM', citacoes: 543, crescimento: 78 }
  ],
  GitHub: [
    { rank: 1, nome: 'Stable Diffusion', stars: 45600, crescimento: 312 },
    { rank: 2, nome: 'LLaMA', stars: 38900, crescimento: 267 },
    { rank: 3, nome: 'GPT4All', stars: 34500, crescimento: 234 },
    { rank: 4, nome: 'LocalAI', stars: 28900, crescimento: 189 },
    { rank: 5, nome: 'Ollama', stars: 25600, crescimento: 456 },
    { rank: 6, nome: 'LangChain', stars: 22300, crescimento: 178 }
  ],
  npm: [
    { rank: 1, nome: 'openai', downloads: 8900000, crescimento: 456 },
    { rank: 2, nome: '@anthropic-ai/sdk', downloads: 2340000, crescimento: 312 },
    { rank: 3, nome: 'langchain', downloads: 1890000, crescimento: 267 },
    { rank: 4, nome: '@google/generative-ai', downloads: 1560000, crescimento: 189 },
    { rank: 5, nome: 'llamaindex', downloads: 987000, crescimento: 234 },
    { rank: 6, nome: 'ai', downloads: 876000, crescimento: 178 }
  ],
  HN: [
    { rank: 1, nome: 'ChatGPT', mentions: 3456, crescimento: 456 },
    { rank: 2, nome: 'Claude', mentions: 2340, crescimento: 312 },
    { rank: 3, nome: 'GPT-4', mentions: 1890, crescimento: 234 },
    { rank: 4, nome: 'Mistral', mentions: 1560, crescimento: 389 },
    { rank: 5, nome: 'Gemini', mentions: 1234, crescimento: 267 },
    { rank: 6, nome: 'LLaMA', mentions: 987, crescimento: 189 }
  ],
  StackOverflow: [
    { rank: 1, nome: 'ChatGPT', questions: 234000, crescimento: 789 },
    { rank: 2, nome: 'OpenAI API', questions: 189000, crescimento: 456 },
    { rank: 3, nome: 'GPT-4', questions: 156000, crescimento: 312 },
    { rank: 4, nome: 'LangChain', questions: 134000, crescimento: 267 },
    { rank: 5, nome: 'Hugging Face', questions: 98000, crescimento: 189 },
    { rank: 6, nome: 'Claude', questions: 87000, crescimento: 234 }
  ],
  Reddit: [
    { rank: 1, nome: 'ChatGPT', posts: 67800, crescimento: 567 },
    { rank: 2, nome: 'Midjourney', posts: 54300, crescimento: 456 },
    { rank: 3, nome: 'Stable Diffusion', posts: 43200, crescimento: 389 },
    { rank: 4, nome: 'GPT-4', posts: 38900, crescimento: 312 },
    { rank: 5, nome: 'Claude', posts: 32100, crescimento: 267 },
    { rank: 6, nome: 'Gemini', posts: 27800, crescimento: 234 }
  ]
};

export function TopAIs() {
  const [plataforma, setPlataforma] = useState('Papers');
  const ias = IAS[plataforma];

  const getMetricLabel = () => {
    switch (plataforma) {
      case 'Papers': return 'citações';
      case 'GitHub': return 'stars';
      case 'npm': return 'downloads';
      case 'HN': return 'mentions';
      case 'StackOverflow': return 'questions';
      case 'Reddit': return 'posts';
      default: return 'count';
    }
  };

  const maxValue = Math.max(...ias.map(ia => {
    const key = Object.keys(ia).find(k => k !== 'rank' && k !== 'nome' && k !== 'crescimento');
    return key ? (ia as any)[key] : 0;
  }));

  return (
    <div className="bg-gradient-to-br from-slate-900/80 to-slate-800/80 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/20 shadow-2xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-lg">
          <span className="text-2xl">🤖</span>
        </div>
        <div>
          <h3 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            IAs Mais Citadas
          </h3>
          <p className="text-xs text-slate-400">Top 6 modelos de IA mais populares</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {PLATAFORMAS.map((plat) => (
          <button
            key={plat}
            onClick={() => setPlataforma(plat)}
            className={`
              px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap
              ${plataforma === plat
                ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg shadow-purple-500/50'
                : 'bg-slate-800/50 text-slate-400 hover:bg-slate-700/50 hover:text-white'
              }
            `}
          >
            {plat}
          </button>
        ))}
      </div>

      {/* GRÁFICO VERTICAL - Estilo 2: Barras com gradiente ROXO (diferente do outro) */}
      <div className="space-y-4">
        {ias.map((ia, index) => {
          const key = Object.keys(ia).find(k => k !== 'rank' && k !== 'nome' && k !== 'crescimento');
          const value = key ? (ia as any)[key] : 0;
          const heightPct = (value / maxValue) * 100;

          return (
            <div key={ia.rank} className="group" style={{ animationDelay: `${index * 50}ms` }}>
              {/* Info */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-purple-400 w-8">
                    #{ia.rank}
                  </span>
                  <span className="text-white font-semibold">{ia.nome}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-slate-400 text-sm">
                    {value.toLocaleString()} {getMetricLabel()}
                  </span>
                  <div className={`
                    flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-full
                    ${ia.crescimento > 0
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-red-500/20 text-red-400'
                    }
                  `}>
                    {ia.crescimento > 0 ? '↗' : '↘'} {Math.abs(ia.crescimento)}%
                  </div>
                </div>
              </div>

              {/* Barra horizontal com gradiente ROXO (diferente do outro) */}
              <div className="relative h-3 bg-slate-800/50 rounded-full overflow-hidden">
                <div
                  className="
                    h-full rounded-full transition-all duration-1000 ease-out
                    bg-gradient-to-r from-purple-500 via-pink-500 to-rose-500
                    group-hover:shadow-lg group-hover:shadow-purple-500/50
                  "
                  style={{
                    width: `${heightPct}%`,
                    transitionDelay: `${index * 50}ms`
                  }}
                />
                {/* Shimmer effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
