// pages/map.tsx
'use client';

import { SecurityMap } from '@/components/security-map';
import { DashboardLayout } from '@/components/layout/DashboardLayout';

export default function MapPage() {
  return (
    <DashboardLayout>
      <div className="min-h-screen bg-slate-950 p-6">
        <header className="mb-6">
          <h1 className="text-3xl font-bold">
            <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
              Security Risk Map
            </span>
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Hybrid Model: ACLED + GDELT + World Bank
          </p>
        </header>

        <SecurityMap />
      </div>
    </DashboardLayout>
  );
}
