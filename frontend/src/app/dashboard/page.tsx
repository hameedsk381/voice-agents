"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Activity, Phone, Clock, DollarSign, Loader2, CheckCircle2 } from "lucide-react";
import api from "@/lib/api";
import {
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    AreaChart,
    Area
} from 'recharts';

export default function DashboardPage() {
    const [stats, setStats] = useState<any>(null);
    const [trends, setTrends] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                const [overviewData, trendsData] = await Promise.all([
                    api.get("/analytics/overview"),
                    api.get("/analytics/daily-trends"),
                ]);
                setStats(overviewData);
                setTrends(trendsData);
            } catch (error) {
                console.error("Failed to fetch dashboard data:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    if (loading) {
        return (
            <div className="grid gap-6">
                <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="glass-card h-28 animate-pulse" />
                    ))}
                </div>
                <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-7">
                    <div className="glass-card col-span-4 h-80 animate-pulse" />
                    <div className="glass-card col-span-3 h-80 animate-pulse" />
                </div>
            </div>
        );
    }

    const cards = [
        {
            title: "Total Calls",
            value: stats?.total_calls || 0,
            icon: Phone,
            accent: "var(--accent-cyan)",
            glowClass: "hover:shadow-[0_0_20px_rgba(0,212,170,0.08)]",
            sub: "Total interactions"
        },
        {
            title: "Talk time",
            value: `${stats?.total_minutes || 0} min`,
            icon: Clock,
            accent: "var(--accent-purple)",
            glowClass: "hover:shadow-[0_0_20px_rgba(139,92,246,0.08)]",
            sub: "Minutes on calls"
        },
        {
            title: "Success Rate",
            value: `${stats?.success_rate || 0}%`,
            icon: CheckCircle2,
            accent: "var(--accent-emerald)",
            glowClass: "hover:shadow-[0_0_20px_rgba(16,185,129,0.08)]",
            sub: "Goal completion"
        },
        {
            title: "Total Cost",
            value: `$${stats?.total_cost || 0}`,
            icon: DollarSign,
            accent: "var(--accent-amber)",
            glowClass: "hover:shadow-[0_0_20px_rgba(245,158,11,0.08)]",
            sub: "Estimated spend"
        },
    ];

    return (
        <div className="space-y-6">
            {/* Top Row: Mission Control Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                        Overview
                    </h2>
                    <p className="text-xs text-[var(--text-secondary)] mt-1">Overview of live agents, call volume, and platform health.</p>
                </div>
            </div>

            {/* Metric Cards */}
            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
                {cards.map((stat) => (
                    <div 
                        key={stat.title} 
                        className={`glass-card p-5 group flex flex-col justify-between relative transition-all duration-300 ${stat.glowClass}`}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">
                                {stat.title}
                            </span>
                            <div className="w-8 h-8 rounded-lg bg-[var(--bg-overlay)] border border-[var(--border-subtle)] flex items-center justify-center text-[var(--text-secondary)] group-hover:scale-105 transition-all">
                                <stat.icon className="h-4 w-4" style={{ color: stat.accent }} />
                            </div>
                        </div>
                        <div>
                            <div className="text-2xl font-extrabold text-[var(--text-primary)] tracking-tight">
                                {stat.value}
                            </div>
                            <p className="text-[10px] text-[var(--text-tertiary)] mt-1 font-medium">{stat.sub}</p>
                        </div>
                        {/* Subtle bottom gradient bar */}
                        <div className="absolute bottom-0 left-4 right-4 h-[2px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300" style={{ background: `linear-gradient(90deg, transparent, ${stat.accent}, transparent)` }} />
                    </div>
                ))}
            </div>

            {/* Layout Grid */}
            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-7">
                {/* Chart Card */}
                <div className="col-span-full lg:col-span-4 glass-card p-6">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h3 className="text-sm font-semibold text-[var(--text-primary)]">Call Volume</h3>
                            <p className="text-[10px] text-[var(--text-secondary)] mt-0.5">Daily total call distributions over the last 7 days.</p>
                        </div>
                    </div>
                    <div className="h-72">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="var(--accent-cyan)" stopOpacity={0.15} />
                                        <stop offset="95%" stopColor="var(--accent-cyan)" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    stroke="var(--text-tertiary)"
                                    fontSize={10}
                                    fontWeight={600}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <YAxis
                                    stroke="var(--text-tertiary)"
                                    fontSize={10}
                                    fontWeight={600}
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={(value) => `${value}`}
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: 'var(--bg-surface)', border: '1px solid border-[var(--border-default)]', borderRadius: '12px' }}
                                    itemStyle={{ color: 'var(--text-primary)' }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="count"
                                    stroke="var(--accent-cyan)"
                                    strokeWidth={2}
                                    fillOpacity={1}
                                    fill="url(#colorCount)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* System Health */}
                <div className="col-span-full lg:col-span-3 glass-card p-6">
                    <div className="mb-6">
                        <h3 className="text-sm font-semibold text-[var(--text-primary)]">System Status</h3>
                        <p className="text-[10px] text-[var(--text-secondary)] mt-0.5">Service health at a glance.</p>
                    </div>
                    
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-overlay)] border border-[var(--border-subtle)]">
                            <span className="text-xs font-semibold text-[var(--text-secondary)]">Platform</span>
                            <div className="flex items-center gap-2">
                                <span className={`text-xs font-bold uppercase tracking-wider ${stats ? "text-[var(--accent-emerald)]" : "text-[var(--accent-rose)]"}`}>
                                    {stats ? "Online" : "Offline"}
                                </span>
                                <div className={`status-dot ${stats ? "status-dot-active" : "status-dot-error"}`} />
                            </div>
                        </div>

                        <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-overlay)] border border-[var(--border-subtle)]">
                            <span className="text-xs font-semibold text-[var(--text-secondary)]">Call handling</span>
                            <div className="flex items-center gap-2">
                                <span className={`text-xs font-bold uppercase tracking-wider ${stats ? "text-[var(--accent-emerald)]" : "text-[var(--text-tertiary)]"}`}>
                                    {stats ? "Healthy" : "Unavailable"}
                                </span>
                                <div className={`status-dot ${stats ? "status-dot-active" : "status-dot-warning"}`} />
                            </div>
                        </div>

                        <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-overlay)] border border-[var(--border-subtle)]">
                            <span className="text-xs font-semibold text-[var(--text-secondary)]">Avg response time</span>
                            <span className="text-xs font-bold text-[var(--accent-purple)]">
                                {stats ? `${Math.round(stats.avg_latency_ms || 0)} ms` : "—"}
                            </span>
                        </div>

                        <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-overlay)] border border-[var(--border-subtle)]">
                            <span className="text-xs font-semibold text-[var(--text-secondary)]">Voice agents</span>
                            <span className={`text-xs font-bold uppercase tracking-wider ${stats ? "text-[var(--accent-emerald)]" : "text-[var(--text-tertiary)]"}`}>
                                {stats ? "Active" : "Inactive"}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    );
}
