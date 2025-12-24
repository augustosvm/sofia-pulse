// components/regional-cards.tsx

const REGIOES = [
  {
    nome: "Oceania",
    emoji: "🌏",
    papers: 165,
    crescimento: 20,
    cor: "from-teal-600 to-cyan-800"
  },
  {
    nome: "Europa",
    emoji: "🇪🇺",
    papers: 1620,
    crescimento: 28,
    cor: "from-purple-600 to-pink-800"
  },
  {
    nome: "América do Norte",
    emoji: "🇺🇸",
    papers: 635,
    crescimento: 25,
    cor: "from-blue-600 to-cyan-800"
  },
  {
    nome: "Ásia",
    emoji: "🌏",
    papers: 891,
    crescimento: 45,
    cor: "from-orange-600 to-red-800"
  }
];

export function RegionalCards() {
  return (
    <div className="mb-6">
      <h2 className="text-lg font-semibold text-slate-300 mb-3 flex items-center gap-2">
        <span className="text-base">🌍</span>
        Insights Regionais
      </h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {REGIOES.map((regiao) => (
          <div
            key={regiao.nome}
            className={`
              bg-gradient-to-br ${regiao.cor}
              rounded-lg p-3 border border-white/5
              hover:border-white/20 transition-all
              hover:scale-102 duration-200
              opacity-90 hover:opacity-100
            `}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">{regiao.emoji}</span>
              <div>
                <p className="text-white/50 text-xs">{regiao.nome}</p>
              </div>
            </div>

            <div className="flex items-baseline gap-1 mb-1">
              <span className="text-xl font-bold text-white">
                {regiao.papers}
              </span>
              <span className="text-white/50 text-xs">papers</span>
            </div>

            <div className="text-green-300/70 text-xs font-medium">
              +{regiao.crescimento}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
