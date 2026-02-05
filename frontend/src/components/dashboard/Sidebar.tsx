"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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

const navigation = [
    { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Marketplace', href: '/dashboard/marketplace', icon: ShoppingBag },
    { name: 'Agents', href: '/dashboard/agents', icon: Users },
    { name: 'Voice Lab', href: '/dashboard/voices', icon: Volume2 },
    { name: 'Campaigns', href: '/dashboard/campaigns', icon: PhoneCall },
    { name: 'Monitoring', href: '/dashboard/monitoring', icon: Activity },
    { name: 'Approvals', href: '/dashboard/approvals', icon: ShieldCheck },
    { name: 'Call Logs', href: '/dashboard/logs', icon: PhoneCall },
    { name: 'Analytics', href: '/dashboard/analytics', icon: Activity },
    { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <div className="flex h-full w-64 flex-col bg-[#0f0f10] border-r border-white/10">
            <div className="flex h-16 items-center gap-2 px-6 border-b border-white/10">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-xl">V</span>
                </div>
                <span className="text-lg font-bold text-white">OpenVoice</span>
            </div>

            <div className="flex flex-1 flex-col gap-1 p-4 overflow-y-auto">
                {navigation.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${isActive
                                ? 'bg-blue-600/10 text-blue-500'
                                : 'text-gray-400 hover:bg-white/5 hover:text-white'
                                }`}
                        >
                            <item.icon className="h-5 w-5" />
                            {item.name}
                        </Link>
                    );
                })}
            </div>

            <div className="border-t border-white/10 p-4">
                <button className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-gray-400 hover:bg-red-500/10 hover:text-red-500 transition-colors">
                    <LogOut className="h-5 w-5" />
                    Sign Out
                </button>
            </div>
        </div>
    );
}
