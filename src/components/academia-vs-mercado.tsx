// components/academia-vs-mercado.tsx

interface Tech {
  nome: string;
  papers: number;
  jobs: number;
}

const QUADRANTES: Record<string, Tech[]> = {
  lideres: [
    { nome: "Python", papers: 85, jobs: 90 },
    { nome: "FastAPI", papers: 70, jobs: 75 },
    { nome: "TypeScript", papers: 68, jobs: 82 },
    { nome: "Docker", papers: 62, jobs: 78 },
    { nome: "Kubernetes", papers: 58, jobs: 72 }
  ],
  pesquisa: [
    { nome: "PyTorch", papers: 90, jobs: 40 },
    { nome: "TensorFlow", papers: 88, jobs: 55 },
    { nome: "Scikit-learn", papers: 82, jobs: 65 },
    { nome: "LangChain", papers: 75, jobs: 45 },
    { nome: "JAX", papers: 72, jobs: 35 }
  ],
  producao: [
    { nome: "JavaScript", papers: 45, jobs: 85 },
    { nome: "React", papers: 40, jobs: 90 },
    { nome: "Node.js", papers: 38, jobs: 82 },
    { nome: "MongoDB", papers: 32, jobs: 75 },
    { nome: "PostgreSQL", papers: 28, jobs: 78 }
  ],
  emergentes: [
    { nome: "Bun", papers: 40, jobs: 15 },
    { nome: "Deno", papers: 35, jobs: 12 },
    { nome: "Astro", papers: 28, jobs: 18 },
    { nome: "Qwik", papers: 22, jobs: 8 },
    { nome: "Solid.js", papers: 18, jobs: 10 }
  ]
};

export function AcademiaVsMercado() {
  return (
    <div className="mb-8">
      <h2 className="text-2xl font-bold text-white mb-4">
        📊 Academia vs Mercado por Quadrante
      </h2>
      <p className="text-slate-400 text-sm mb-6">
        Tecnologias classificadas por uso em papers científicos e mercado de trabalho
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Líderes */}
        <div className="bg-purple-900/30 rounded-xl p-6 border border-purple-500/30">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-2xl">🏆</span>
            <div>
              <h3 className="text-xl font-bold text-purple-400">Líderes</h3>
              <p className="text-slate-400 text-xs">Alto uso em academia E mercado</p>
            </div>
          </div>

          {QUADRANTES.lideres.map((tech, idx) => (
            <div key={tech.nome} className="mb-4">
              <div className="text-white font-medium mb-2">
                #{idx + 1} {tech.nome}
              </div>

              {/* Papers (roxo) */}
              <div className="mb-1">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>Papers</span>
                  <span>{tech.papers}%</span>
                </div>
                <div className="h-2 bg-slate-800/50 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-purple-400 rounded-full"
                    style={{ width: `${tech.papers}%` }}
                  />
                </div>
              </div>

              {/* Jobs (verde) */}
              <div>
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>Jobs</span>
                  <span>{tech.jobs}%</span>
                </div>
                <div className="h-2 bg-slate-800/50 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-green-500 to-green-400 rounded-full"
                    style={{ width: `${tech.jobs}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Apenas Pesquisa */}
        <div className="bg-cyan-900/30 rounded-xl p-6 border border-cyan-500/30">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-2xl">🔬</span>
            <div>
              <h3 className="text-xl font-bold text-cyan-400">Apenas Pesquisa</h3>
              <p className="text-slate-400 text-xs">Muito em papers, pouco em produção</p>
            </div>
          </div>

          {QUADRANTES.pesquisa.map((tech, idx) => (
            <div key={tech.nome} className="mb-4">
              <div className="text-white font-medium mb-2">
                #{idx + 1} {tech.nome}
              </div>

              <div className="mb-1">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>Papers</span>
                  <span>{tech.papers}%</span>
                </div>
                <div className="h-2 bg-slate-800/50 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400 rounded-full"
                    style={{ width: `${tech.papers}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>Jobs</span>
                  <span>{tech.jobs}%</span>
                </div>
                <div className="h-2 bg-slate-800/50 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-green-500 to-green-400 rounded-full"
                    style={{ width: `${tech.jobs}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Pronto para Produção */}
        <div className="bg-green-900/30 rounded-xl p-6 border border-green-500/30">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-2xl">📦</span>
            <div>
              <h3 className="text-xl font-bold text-green-400">Pronto para Produção</h3>
              <p className="text-slate-400 text-xs">Muito no mercado, pouco em papers</p>
            </div>
          </div>

          {QUADRANTES.producao.map((tech, idx) => (
            <div key={tech.nome} className="mb-4">
              <div className="text-white font-medium mb-2">
                #{idx + 1} {tech.nome}
              </div>

              <div className="mb-1">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>Papers</span>
                  <span>{tech.papers}%</span>
                </div>
                <div className="h-2 bg-slate-800/50 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-purple-400 rounded-full"
                    style={{ width: `${tech.papers}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>Jobs</span>
                  <span>{tech.jobs}%</span>
                </div>
                <div className="h-2 bg-slate-800/50 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-green-500 to-green-400 rounded-full"
                    style={{ width: `${tech.jobs}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Emergentes */}
        <div className="bg-orange-900/30 rounded-xl p-6 border border-orange-500/30">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-2xl">🌱</span>
            <div>
              <h3 className="text-xl font-bold text-orange-400">Emergentes</h3>
              <p className="text-slate-400 text-xs">Baixo uso, tecnologias emergentes</p>
            </div>
          </div>

          {QUADRANTES.emergentes.map((tech, idx) => (
            <div key={tech.nome} className="mb-4">
              <div className="text-white font-medium mb-2">
                #{idx + 1} {tech.nome}
              </div>

              <div className="mb-1">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>Papers</span>
                  <span>{tech.papers}%</span>
                </div>
                <div className="h-2 bg-slate-800/50 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-orange-500 to-orange-400 rounded-full"
                    style={{ width: `${tech.papers}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>Jobs</span>
                  <span>{tech.jobs}%</span>
                </div>
                <div className="h-2 bg-slate-800/50 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-green-500 to-green-400 rounded-full"
                    style={{ width: `${tech.jobs}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}
