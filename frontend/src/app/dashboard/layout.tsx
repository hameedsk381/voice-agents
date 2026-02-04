'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from "@/components/dashboard/Sidebar";
import { useAuth } from "@/contexts/AuthContext";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { user, isLoading, isAuthenticated, logout } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.push('/login');
        }
    }, [isLoading, isAuthenticated, router]);

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[#0a0a0b]">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return null;
    }

    return (
        <div className="flex h-screen overflow-hidden bg-black">
            <Sidebar />
            <div className="flex-1 overflow-y-auto">
                <header className="flex h-16 items-center justify-between border-b border-white/10 bg-black/50 px-6 backdrop-blur-sm sticky top-0 z-10">
                    <h1 className="text-xl font-semibold text-white">Dashboard</h1>

                    {/* User Menu */}
                    <div className="flex items-center gap-4">
                        <div className="text-right">
                            <p className="text-sm font-medium text-white">{user?.full_name || user?.email}</p>
                            <p className="text-xs text-gray-400 capitalize">{user?.role}</p>
                        </div>
                        <div className="relative group">
                            <button className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-medium text-sm">
                                {(user?.full_name?.[0] || user?.email?.[0] || '?').toUpperCase()}
                            </button>
                            <div className="absolute right-0 mt-2 w-48 bg-[#141417] border border-white/10 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                                <div className="p-3 border-b border-white/10">
                                    <p className="text-sm text-white truncate">{user?.email}</p>
                                </div>
                                <button
                                    onClick={logout}
                                    className="w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                                >
                                    Sign Out
                                </button>
                            </div>
                        </div>
                    </div>
                </header>
                <main className="p-6">
                    {children}
                </main>
            </div>
        </div>
    );
}
