// pages/pulse.tsx

'use client';

import { RegionalCards } from '@/components/regional-cards';
import { InsightsCarousel } from '@/components/insights-carousel';
import { TopTechnologies } from '@/components/top-technologies';
import { TopAIs } from '@/components/top-ais';
import { AcademiaVsMercado } from '@/components/academia-vs-mercado';
import { DashboardLayout } from '@/components/layout/DashboardLayout';

export default function PulsePage() {
  return (
    <DashboardLayout>
      <div className="min-h-screen bg-slate-950 p-6">

        {/* HEADER */}
        <header className="mb-6">
          <h1 className="text-3xl font-bold">
            <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
              Pulse Intelligence
            </span>
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Última atualização: 18 Dez 2025 • 19:24 BRT
          </p>
        </header>

        {/* 1. Insights Regionais (Cards do topo) */}
        <section className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span className="text-2xl">🌍</span> Insights Regionais
          </h2>
          <RegionalCards />
        </section>

        {/* 2. Insights Carousel */}
        <section className="mb-8">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span className="text-2xl">💡</span> Insights de Pautas
          </h2>
          <InsightsCarousel />
        </section>

        {/* 3. Top Tecnologias + IAs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <TopTechnologies />
          <TopAIs />
        </div>

        {/* 4. Academia vs Mercado */}
        <AcademiaVsMercado />

      </div>
    </DashboardLayout>
  );
}
