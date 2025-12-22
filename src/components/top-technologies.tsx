// components/top-technologies.tsx

'use client';

import { useState } from 'react';

const PLATAFORMAS = ['GitHub', 'npm', 'PyPI', 'HN', 'StackOverflow', 'Reddit'];

const REPOS: Record<string, Array<{ rank: number; nome: string; stars?: number; downloads?: number; mentions?: number; questions?: number; posts?: number; crescimento: number }>> = {
  GitHub: [
    { rank: 1, nome: 'Rust', stars: 247000, crescimento: 247 },
    { rank: 2, nome: 'Python', stars: 189000, crescimento: 89 },
    { rank: 3, nome: 'TypeScript', stars: 156000, crescimento: 67 },
    { rank: 4, nome: 'Go', stars: 134000, crescimento: 52 },
    { rank: 5, nome: 'React', stars: 128000, crescimento: 45 },
    { rank: 6, nome: 'Vue', stars: 98000, crescimento: 34 }
  ],
  npm: [
    { rank: 1, nome: 'React', downloads: 24500000, crescimento: 89 },
    { rank: 2, nome: 'lodash', downloads: 18900000, crescimento: 12 },
    { rank: 3, nome: 'chalk', downloads: 15600000, crescimento: 23 },
    { rank: 4, nome: 'commander', downloads: 13400000, crescimento: 34 },
    { rank: 5, nome: 'express', downloads: 12800000, crescimento: 45 },
    { rank: 6, nome: 'axios', downloads: 11900000, crescimento: 67 }
  ],
  PyPI: [
    { rank: 1, nome: 'requests', downloads: 45000000, crescimento: 23 },
    { rank: 2, nome: 'numpy', downloads: 38900000, crescimento: 34 },
    { rank: 3, nome: 'pandas', downloads: 34500000, crescimento: 56 },
    { rank: 4, nome: 'tensorflow', downloads: 28900000, crescimento: 78 },
    { rank: 5, nome: 'pytorch', downloads: 25600000, crescimento: 89 },
    { rank: 6, nome: 'scikit-learn', downloads: 22300000, crescimento: 45 }
  ],
  HN: [
    { rank: 1, nome: 'LLMs', mentions: 1240, crescimento: 234 },
    { rank: 2, nome: 'Rust', mentions: 980, crescimento: 156 },
    { rank: 3, nome: 'AI Safety', mentions: 756, crescimento: 189 },
    { rank: 4, nome: 'Quantum', mentions: 634, crescimento: 92 },
    { rank: 5, nome: 'WebAssembly', mentions: 521, crescimento: 67 },
    { rank: 6, nome: 'Edge Computing', mentions: 456, crescimento: 78 }
  ],
  StackOverflow: [
    { rank: 1, nome: 'JavaScript', questions: 2456000, crescimento: 12 },
    { rank: 2, nome: 'Python', questions: 2134000, crescimento: 34 },
    { rank: 3, nome: 'Java', questions: 1876000, crescimento: 8 },
    { rank: 4, nome: 'C#', questions: 1645000, crescimento: 15 },
    { rank: 5, nome: 'React', questions: 1234000, crescimento: 67 },
    { rank: 6, nome: 'TypeScript', questions: 987000, crescimento: 89 }
  ],
  Reddit: [
    { rank: 1, nome: 'ChatGPT', posts: 34500, crescimento: 456 },
    { rank: 2, nome: 'Midjourney', posts: 28900, crescimento: 312 },
    { rank: 3, nome: 'Stable Diffusion', posts: 23400, crescimento: 267 },
    { rank: 4, nome: 'Claude', posts: 19800, crescimento: 189 },
    { rank: 5, nome: 'GPT-4', posts: 17600, crescimento: 234 },
    { rank: 6, nome: 'Rust', posts: 15400, crescimento: 124 }
  ]
};

export function TopTechnologies() {
  const [plataforma, setPlataforma] = useState('GitHub');
  const repos = REPOS[plataforma];

  const getMetricLabel = () => {
    switch (plataforma) {
      case 'GitHub': return 'stars';
      case 'npm': return 'downloads';
      case 'PyPI': return 'downloads';
      case 'HN': return 'mentions';
      case 'StackOverflow': return 'questions';
      case 'Reddit': return 'posts';
      default: return 'count';
    }
  };

  // Calcular max para normalizar altura das barras
  const maxValue = Math.max(...repos.map(r => {
    const key = Object.keys(r).find(k => k !== 'rank' && k !== 'nome' && k !== 'crescimento');
    return key ? (r as any)[key] : 0;
  }));

  return (
    <div className="bg-gradient-to-br from-slate-900/80 to-slate-800/80 backdrop-blur-xl rounded-2xl p-6 border border-cyan-500/20 shadow-2xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-lg">
          <span className="text-2xl">🔥</span>
        </div>
        <div>
          <h3 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
            Repos & Packages em Alta
          </h3>
          <p className="text-xs text-slate-400">Top 6 tecnologias mais populares</p>
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
                ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/50'
                : 'bg-slate-800/50 text-slate-400 hover:bg-slate-700/50 hover:text-white'
              }
            `}
          >
            {plat}
          </button>
        ))}
      </div>

      {/* GRÁFICO VERTICAL - Estilo 1: Barras com gradiente */}
      <div className="space-y-4">
        {repos.map((repo, index) => {
          const key = Object.keys(repo).find(k => k !== 'rank' && k !== 'nome' && k !== 'crescimento');
          const value = key ? (repo as any)[key] : 0;
          const heightPct = (value / maxValue) * 100;

          return (
            <div key={repo.rank} className="group" style={{ animationDelay: `${index * 50}ms` }}>
              {/* Info */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-cyan-400 w-8">
                    #{repo.rank}
                  </span>
                  <span className="text-white font-semibold">{repo.nome}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-slate-400 text-sm">
                    {value.toLocaleString()} {getMetricLabel()}
                  </span>
                  <div className={`
                    flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-full
                    ${repo.crescimento > 0
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-red-500/20 text-red-400'
                    }
                  `}>
                    {repo.crescimento > 0 ? '↗' : '↘'} {Math.abs(repo.crescimento)}%
                  </div>
                </div>
              </div>

              {/* Barra horizontal com gradiente */}
              <div className="relative h-3 bg-slate-800/50 rounded-full overflow-hidden">
                <div
                  className="
                    h-full rounded-full transition-all duration-1000 ease-out
                    bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500
                    group-hover:shadow-lg group-hover:shadow-cyan-500/50
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
