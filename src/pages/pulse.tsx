// pages/pulse.tsx

'use client';

import { RegionalCards } from '@/components/regional-cards';
import { InsightsCarousel } from '@/components/insights-carousel';
import { TopTechnologies } from '@/components/top-technologies';
import { TopAIs } from '@/components/top-ais';
import { AcademiaVsMercado } from '@/components/academia-vs-mercado';

export default function PulsePage() {
  return (
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

      {/* 1. Regional Cards */}
      <RegionalCards />

      {/* 2. Insights Carousel */}
      <InsightsCarousel />

      {/* 3. Top Tecnologias + IAs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <TopTechnologies />
        <TopAIs />
      </div>

      {/* 4. Academia vs Mercado */}
      <AcademiaVsMercado />

    </div>
  );
}
