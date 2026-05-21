'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Sidebar from "@/components/dashboard/Sidebar";
import ThemeToggle from "@/components/ThemeToggle";
import { useAuth } from "@/contexts/AuthContext";
import { Search, Bell } from 'lucide-react';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { user, isLoading, isAuthenticated, logout } = useAuth();
    const router = useRouter();
    const pathname = usePathname();
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.push('/login');
        }
    }, [isLoading, isAuthenticated, router]);

    // Compute simple breadcrumb title from pathname
    const getPageTitle = () => {
        if (pathname === '/dashboard') return 'Overview';
        const parts = pathname.split('/');
        const lastPart = parts[parts.length - 1];
        if (lastPart === 'new') return 'Create Campaign';
        
        // Capitalize words
        return lastPart
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[var(--bg-base)]">
                <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[var(--accent-cyan)] shadow-[0_0_15px_rgba(0,212,170,0.15)]"></div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return null;
    }

    return (
        <div className="flex h-screen overflow-hidden bg-[var(--bg-base)] text-[var(--text-primary)] font-sans relative">
            {/* Ambient subtle background orbs */}
            <div className="absolute top-[-250px] left-1/4 w-[700px] h-[700px] rounded-full bg-[radial-gradient(circle,rgba(0,212,170,0.04)_0%,transparent_70%)] blur-[40px] pointer-events-none -z-10" />
            <div className="absolute bottom-[-300px] right-1/4 w-[800px] h-[800px] rounded-full bg-[radial-gradient(circle,rgba(139,92,246,0.03)_0%,transparent_70%)] blur-[40px] pointer-events-none -z-10" />

            <Sidebar />
            
            <div className="flex-1 flex flex-col overflow-hidden">
                <header className="flex h-16 items-center justify-between border-b border-[var(--border-subtle)] bg-[var(--bg-base)]/40 px-6 backdrop-blur-md sticky top-0 z-10 select-none">
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-[var(--text-tertiary)] font-medium">Dashboard</span>
                        <span className="text-xs text-[var(--text-tertiary)]">/</span>
                        <h1 className="text-sm font-semibold text-[var(--text-primary)]">{getPageTitle()}</h1>
                    </div>

                    <div className="flex items-center gap-6">
                        {/* Global Search Bar */}
                        <div className="relative hidden md:block">
                            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-tertiary)]" />
                            <input 
                                type="text"
                                placeholder="Search everything..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-64 pl-10 pr-12 py-1.5 bg-[var(--bg-overlay)] border border-[var(--border-default)] hover:border-[var(--border-active)] rounded-xl text-xs text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent-cyan)] focus:ring-4 focus:ring-[var(--accent-cyan)]/5 transition-all"
                            />
                            <kbd className="absolute right-3 top-1/2 -translate-y-1/2 px-1.5 py-0.5 rounded bg-[var(--glass-bg-hover)] border border-[var(--border-default)] text-[9px] text-[var(--text-tertiary)] font-mono uppercase tracking-wider font-semibold pointer-events-none">
                                ⌘K
                            </kbd>
                        </div>

                        <ThemeToggle />

                        {/* Notifications */}
                        <button className="relative p-1.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-overlay)] hover:bg-[var(--glass-bg-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all">
                            <Bell className="w-4 h-4" />
                            <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-[var(--accent-cyan)]" />
                        </button>

                        {/* User Menu */}
                        <div className="flex items-center gap-3 pl-2 border-l border-[var(--border-subtle)]">
                            <div className="text-right hidden sm:block">
                                <p className="text-xs font-semibold text-[var(--text-primary)]">{user?.full_name || user?.email}</p>
                                <p className="text-[10px] text-[var(--text-tertiary)] capitalize mt-0.5 font-bold tracking-wider">{user?.role}</p>
                            </div>
                            
                            <div className="relative group">
                                <button className="h-9 w-9 rounded-full bg-gradient-to-br from-[var(--accent-cyan)] to-[var(--accent-purple)] flex items-center justify-center text-white font-semibold text-xs tracking-wider shadow-md shadow-[var(--accent-cyan)]/10 hover:scale-105 active:scale-95 transition-all">
                                    {(user?.full_name?.[0] || user?.email?.[0] || '?').toUpperCase()}
                                </button>
                                
                                <div className="absolute right-0 mt-2 w-48 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                                    <div className="p-3 border-b border-[var(--border-subtle)]">
                                        <p className="text-xs font-semibold text-[var(--text-primary)] truncate">{user?.full_name || 'My Profile'}</p>
                                        <p className="text-[10px] text-[var(--text-tertiary)] truncate mt-0.5">{user?.email}</p>
                                    </div>
                                    <button
                                        onClick={logout}
                                        className="w-full text-left px-3 py-2.5 text-xs text-[var(--accent-rose)] hover:bg-rose-500/5 transition-colors rounded-b-xl font-medium"
                                    >
                                        Sign Out
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </header>
                
                <main className="flex-1 overflow-y-auto p-6 relative">
                    {children}
                </main>
            </div>
        </div>
    );
}
