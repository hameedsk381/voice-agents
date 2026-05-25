'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Sidebar from "@/components/dashboard/Sidebar";
import ThemeToggle from "@/components/ThemeToggle";
import { useAuth } from "@/contexts/AuthContext";
import { Search, Bell, Loader2 } from 'lucide-react';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

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

    const getPageTitle = () => {
        if (pathname === '/dashboard') return 'Overview';
        const parts = pathname.split('/');
        const lastPart = parts[parts.length - 1];
        if (lastPart === 'new') return 'Create Campaign';
        
        return lastPart
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    if (!isAuthenticated) {
        return null;
    }

    return (
        <div className="flex h-screen overflow-hidden bg-background text-foreground font-sans">
            <Sidebar />
            
            <div className="flex-1 flex flex-col overflow-hidden">
                <header className="flex h-16 items-center justify-between border-b px-6 bg-background sticky top-0 z-10 select-none">
                    <div className="flex items-center gap-2 text-sm">
                        <span className="text-muted-foreground font-medium">Dashboard</span>
                        <span className="text-muted-foreground">/</span>
                        <h1 className="font-semibold">{getPageTitle()}</h1>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="relative hidden md:block">
                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                                type="text"
                                placeholder="Search..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-64 pl-8 bg-muted/50 border-none shadow-none"
                            />
                            <kbd className="absolute right-2 top-2.5 pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
                                <span className="text-xs">⌘</span>K
                            </kbd>
                        </div>

                        <ThemeToggle />

                        <Button variant="outline" size="icon" className="relative h-9 w-9">
                            <Bell className="h-4 w-4" />
                            <span className="absolute top-2 right-2 h-1.5 w-1.5 rounded-full bg-primary" />
                        </Button>

                        <div className="flex items-center gap-3 pl-4 ml-2 border-l">
                            <div className="text-right hidden sm:block">
                                <p className="text-sm font-medium leading-none">{user?.full_name || user?.email}</p>
                                <p className="text-xs text-muted-foreground capitalize mt-1 tracking-wider">{user?.role}</p>
                            </div>
                            
                            <Button variant="secondary" className="h-9 w-9 rounded-full bg-primary text-white font-semibold border-0 hover:opacity-90">
                                {(user?.full_name?.[0] || user?.email?.[0] || '?').toUpperCase()}
                            </Button>
                        </div>
                    </div>
                </header>
                
                <main className="flex-1 overflow-y-auto p-6 bg-muted/20">
                    {children}
                </main>
            </div>
        </div>
    );
}
