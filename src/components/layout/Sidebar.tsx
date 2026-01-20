'use client';

import Link from 'next/link';
import { useRouter } from 'next/router';
import {
    LayoutDashboard,
    Map as MapIcon,
    Settings,
    Bell,
    Search,
    Menu,
    X,
    User,
    Zap,
    ShieldAlert,
    TrendingUp,
    Globe
} from 'lucide-react';
import { useState } from 'react';

const MENU_ITEMS = [
    { name: 'Pulse Intelligence', path: '/pulse', icon: Zap },
    { name: 'Security Map', path: '/map', icon: ShieldAlert },
    { name: 'Global Trends', path: '/trends', icon: TrendingUp },
    { name: 'Admnistration', path: '/admin', icon: Settings },
];

export function Sidebar() {
    const router = useRouter();
    const [collapsed, setCollapsed] = useState(false);

    return (
        <aside className={`
      relative h-screen bg-slate-900/50 backdrop-blur-xl border-r border-slate-800/50
      transition-all duration-300 ease-in-out
      ${collapsed ? 'w-20' : 'w-64'}
      hidden md:flex flex-col
    `}>
            {/* Logo */}
            <div className="h-16 flex items-center px-6 border-b border-slate-800/50">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white font-bold shadow-lg shadow-cyan-500/20">
                        S
                    </div>
                    {!collapsed && (
                        <span className="text-xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                            SOFIA
                        </span>
                    )}
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 py-6 px-3 space-y-1">
                {MENU_ITEMS.map((item) => {
                    const isActive = router.pathname === item.path;
                    return (
                        <Link
                            key={item.path}
                            href={item.path}
                            className={`
                flex items-center gap-3 px-3 py-3 rounded-xl transition-all group
                ${isActive
                                    ? 'bg-gradient-to-r from-cyan-500/10 to-blue-500/10 text-cyan-400 border border-cyan-500/20'
                                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                                }
              `}
                        >
                            <item.icon className={`w-5 h-5 ${isActive ? 'text-cyan-400' : 'text-slate-400 group-hover:text-white'}`} />
                            {!collapsed && <span className="font-medium">{item.name}</span>}
                        </Link>
                    );
                })}
            </nav>

            {/* User Info */}
            <div className="p-4 border-t border-slate-800/50">
                <div className={`flex items-center gap-3 ${collapsed ? 'justify-center' : ''}`}>
                    <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">
                        <User className="w-5 h-5 text-slate-400" />
                    </div>
                    {!collapsed && (
                        <div className="overflow-hidden">
                            <p className="text-sm font-medium text-white truncate">Augusto Moreira</p>
                            <p className="text-xs text-slate-500 truncate">Enterprise Admin</p>
                        </div>
                    )}
                </div>
            </div>
        </aside>
    );
}
