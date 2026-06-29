"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { LogoIcon } from "@/components/Logo";
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
    Volume2,
    GitBranch,
    Eye,
    Network,
    Phone,
    MessageSquare,
    PhoneIncoming,
    TrendingUp,
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
            { name: 'Phone Numbers', href: '/dashboard/phone-numbers', icon: Phone },
            { name: 'Collections', href: '/dashboard/collections', icon: TrendingUp },
            { name: 'Campaigns', href: '/dashboard/campaigns', icon: PhoneCall },
            { name: 'Inbound Flows', href: '/dashboard/inbound-flows', icon: PhoneIncoming },
            { name: 'Channels', href: '/dashboard/channels', icon: MessageSquare },
            { name: 'Workflows', href: '/dashboard/workflows', icon: GitBranch },
            { name: 'Monitoring', href: '/dashboard/monitoring', icon: Activity },
            { name: 'Approvals', href: '/dashboard/approvals', icon: ShieldCheck },
            { name: 'Call Logs', href: '/dashboard/logs', icon: PhoneCall },
        ]
    },
    {
        title: "Insights",
        items: [
            { name: 'Analytics', href: '/dashboard/analytics', icon: Activity },
            { name: 'Observability', href: '/dashboard/observability', icon: Eye },
            { name: 'Marketplace', href: '/dashboard/marketplace', icon: ShoppingBag },
        ]
    },
    {
        title: "System",
        items: [
            { name: 'Agent Registry', href: '/dashboard/registry', icon: Network },
            { name: 'Settings', href: '/dashboard/settings', icon: Settings },
        ]
    }
];

export default function Sidebar() {
    const pathname = usePathname();
    const { logout, user } = useAuth();

    return (
        <div className="flex h-full w-64 flex-col bg-card/80 backdrop-blur-xl border-r border-border select-none">
            <div className="flex h-16 items-center gap-2.5 px-6 border-b border-border">
                <LogoIcon className="size-8 text-primary shrink-0" />
                <div className="min-w-0 flex-1">
                    <span className="text-base font-bold tracking-tight text-foreground block leading-tight">Voise <span className="text-primary">AI</span></span>
                    {user?.organization_id && (
                        <span className="text-[10px] font-medium text-muted-foreground/60 block leading-tight truncate">
                            {user.organization_id === "default" ? "Default Org" : user.organization_id}
                        </span>
                    )}
                </div>
            </div>

            <nav aria-label="Dashboard Navigation" className="flex flex-1 flex-col gap-6 p-4 overflow-y-auto">
                {navGroups.map((group) => (
                    <div key={group.title} className="space-y-1.5">
                        <span className="px-3 text-[10px] font-bold uppercase tracking-widest text-muted-foreground/75 block mb-2">
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
                                    className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${isActive
                                        ? 'bg-primary/10 text-primary dark:bg-primary/20 font-semibold'
                                        : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                                        }`}
                                >
                                    <item.icon className={`h-4 w-4 ${isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'}`} aria-hidden="true" />
                                    {item.name}
                                </Link>
                            );
                        })}
                    </div>
                ))}
            </nav>

            <div className="border-t border-border p-4 space-y-2">
                <ThemeToggle className="w-full justify-center" showLabel />
                <button 
                    type="button"
                    onClick={logout}
                    className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-destructive"
                >
                    <LogOut className="h-4 w-4" aria-hidden="true" />
                    Sign Out
                </button>
            </div>
        </div>
    );
}
