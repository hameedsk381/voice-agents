"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import ThemeToggle from "@/components/ThemeToggle";
import {
    LayoutDashboard,
    Users,
    PhoneCall,
    Settings,
    LogOut,
    Activity,
    ShieldCheck,
    ShoppingBag,
    Volume2
} from "lucide-react";

const navGroups = [
    {
        title: "Core",
        items: [
            { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
            { name: 'Agents', href: '/dashboard/agents', icon: Users },
            { name: 'Voice Lab', href: '/dashboard/voices', icon: Volume2 },
        ]
    },
    {
        title: "Operations",
        items: [
            { name: 'Campaigns', href: '/dashboard/campaigns', icon: PhoneCall },
            { name: 'Monitoring', href: '/dashboard/monitoring', icon: Activity },
            { name: 'Approvals', href: '/dashboard/approvals', icon: ShieldCheck },
            { name: 'Call Logs', href: '/dashboard/logs', icon: PhoneCall },
        ]
    },
    {
        title: "Insights",
        items: [
            { name: 'Analytics', href: '/dashboard/analytics', icon: Activity },
            { name: 'Marketplace', href: '/dashboard/marketplace', icon: ShoppingBag },
        ]
    },
    {
        title: "System",
        items: [
            { name: 'Settings', href: '/dashboard/settings', icon: Settings },
        ]
    }
];

export default function Sidebar() {
    const pathname = usePathname();
    const { logout } = useAuth();

    return (
        <div className="flex h-full w-64 flex-col bg-[var(--bg-surface)]/80 backdrop-blur-xl border-r border-[var(--border-subtle)] select-none">
            <div className="flex h-16 items-center gap-2.5 px-6 border-b border-[var(--border-subtle)]">
                <div className="w-8 h-8 bg-gradient-to-br from-[var(--accent-cyan)] to-[var(--accent-purple)] rounded-lg flex items-center justify-center shadow-md shadow-[var(--accent-cyan)]/15">
                    <span className="text-white font-bold text-base">V</span>
                </div>
                <span className="text-base font-bold tracking-tight text-[var(--text-primary)]">Voise AI</span>
            </div>

            <nav aria-label="Dashboard Navigation" className="flex flex-1 flex-col gap-6 p-4 overflow-y-auto">
                {navGroups.map((group) => (
                    <div key={group.title} className="space-y-1.5">
                        <span className="px-3 text-[10px] font-bold uppercase tracking-widest text-[var(--text-tertiary)] block mb-2">
                            {group.title}
                        </span>
                        
                        {group.items.map((item) => {
                            // Check if current item href matches active route
                            const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href + '/'));
                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    aria-current={isActive ? "page" : undefined}
                                    className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent-cyan)] ${isActive
                                        ? 'bg-[var(--glass-bg-hover)] text-[var(--accent-cyan)] nav-active-bar font-semibold'
                                        : 'text-[var(--text-secondary)] hover:bg-[var(--bg-overlay)] hover:text-[var(--text-primary)]'
                                        }`}
                                >
                                    <item.icon className={`h-4 w-4 ${isActive ? 'text-[var(--accent-cyan)]' : 'text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]'}`} aria-hidden="true" />
                                    {item.name}
                                </Link>
                            );
                        })}
                    </div>
                ))}
            </nav>

            <div className="border-t border-[var(--border-subtle)] p-4 space-y-2">
                <ThemeToggle className="w-full justify-center" showLabel />
                <button 
                    onClick={logout}
                    className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-[var(--text-tertiary)] hover:bg-rose-500/5 hover:text-[var(--accent-rose)] transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent-rose)]"
                >
                    <LogOut className="h-4 w-4" aria-hidden="true" />
                    Sign Out
                </button>
            </div>
        </div>
    );
}
