'use client';

import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { ReactNode } from 'react';

interface DashboardLayoutProps {
    children: ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
    return (
        <div className="flex min-h-screen bg-slate-950 text-white font-sans selection:bg-cyan-500/30">
            <Sidebar />
            <div className="flex-1 flex flex-col max-w-full overflow-hidden">
                <Header />
                <main className="flex-1 overflow-y-auto overflow-x-hidden p-6 relative">
                    {/* Background Gradients */}
                    <div className="fixed inset-0 pointer-events-none z-0">
                        <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-[128px] opacity-50" />
                        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-[128px] opacity-50" />
                    </div>

                    {/* Content */}
                    <div className="relative z-10 max-w-7xl mx-auto w-full">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
}
