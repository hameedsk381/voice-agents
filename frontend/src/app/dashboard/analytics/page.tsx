'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    AreaChart, Area
} from 'recharts';
import {
    TrendingUp, Clock, Zap, DollarSign,
    CheckCircle2, PhoneIncoming, BarChart3
} from 'lucide-react';

export default function AnalyticsPage() {
    const [overview, setOverview] = useState<any>(null);
    const [trends, setTrends] = useState<any[]>([]);
    const [performance, setPerformance] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [overviewData, trendsData, perfData] = await Promise.all([
                    api.get("/analytics/overview"),
                    api.get("/analytics/daily-trends"),
                    api.get("/analytics/agent-performance")
                ]);

                setOverview(overviewData);
                setTrends(trendsData);
                setPerformance(perfData);
            } catch (err) {
                console.error("Failed to fetch analytics", err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, []);

    const stats = [
        { label: 'Total Calls', value: overview?.total_calls || 0, icon: PhoneIncoming, color: 'var(--accent-cyan)', glow: 'hover:shadow-[0_0_20px_rgba(0,212,170,0.08)]' },
        { label: 'Success Rate', value: `${overview?.success_rate || 0}%`, icon: CheckCircle2, color: 'var(--accent-emerald)', glow: 'hover:shadow-[0_0_20px_rgba(16,185,129,0.08)]' },
        { label: 'Avg response time', value: `${overview?.avg_latency_ms || 0} ms`, icon: Zap, color: 'var(--accent-purple)', glow: 'hover:shadow-[0_0_20px_rgba(139,92,246,0.08)]' },
        { label: 'Total Minutes', value: overview?.total_minutes || 0, icon: Clock, color: 'var(--accent-blue)', glow: 'hover:shadow-[0_0_20px_rgba(59,130,246,0.08)]' },
        { label: 'Cost Avoided', value: `$${overview?.total_cost || 0}`, icon: DollarSign, color: 'var(--accent-amber)', glow: 'hover:shadow-[0_0_20px_rgba(245,158,11,0.08)]' },
    ];

    if (isLoading) {
        return (
            <div className="grid gap-6">
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-5">
                    {[1, 2, 3, 4, 5].map((i) => (
                        <div key={i} className="glass-card h-28 animate-pulse" />
                    ))}
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="glass-card h-80 animate-pulse" />
                    <div className="glass-card h-80 animate-pulse" />
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6 pb-20">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                    Observability & <span className="text-gradient-brand">Analytics</span>
                </h2>
                <p className="text-xs text-[var(--text-secondary)] mt-1">Call volume, success rates, and agent performance across your organization.</p>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-5">
                {stats.map((s, i) => (
                    <div key={i} className={`glass-card p-5 group flex flex-col justify-between relative transition-all duration-300 ${s.glow}`}>
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">{s.label}</span>
                            <div className="w-8 h-8 rounded-lg bg-[var(--bg-overlay)] border border-[var(--border-subtle)] flex items-center justify-center">
                                <s.icon className="w-4 h-4" style={{ color: s.color }} />
                            </div>
                        </div>
                        <p className="text-2xl font-extrabold text-[var(--text-primary)] tracking-tight">{s.value}</p>
                        {/* Subtle accent bottom bar */}
                        <div className="absolute bottom-0 left-4 right-4 h-[2px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300" style={{ background: `linear-gradient(90deg, transparent, ${s.color}, transparent)` }} />
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Traffic Trend */}
                <div className="glass-card p-6">
                    <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-6 flex items-center gap-2">
                        <TrendingUp className="w-4.5 h-4.5 text-[var(--accent-cyan)]" />
                        Call Volume Trend
                    </h3>
                    <div className="h-[280px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="var(--accent-cyan)" stopOpacity={0.15} />
                                        <stop offset="95%" stopColor="var(--accent-cyan)" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                                <XAxis dataKey="date" stroke="var(--text-tertiary)" fontSize={10} fontWeight={600} tickLine={false} axisLine={false} />
                                <YAxis stroke="var(--text-tertiary)" fontSize={10} fontWeight={600} tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: 'var(--bg-surface)', border: '1px solid border-[var(--border-default)]', borderRadius: '12px' }}
                                    itemStyle={{ color: 'var(--text-primary)' }}
                                />
                                <Area type="monotone" dataKey="count" stroke="var(--accent-cyan)" fillOpacity={1} fill="url(#colorCount)" strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Agent Comparison */}
                <div className="glass-card p-6">
                    <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-6 flex items-center gap-2">
                        <BarChart3 className="w-4.5 h-4.5 text-[var(--accent-purple)]" />
                        Agent Distribution
                    </h3>
                    <div className="h-[280px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={performance} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                                <XAxis dataKey="name" stroke="var(--text-tertiary)" fontSize={10} fontWeight={600} tickLine={false} axisLine={false} />
                                <YAxis stroke="var(--text-tertiary)" fontSize={10} fontWeight={600} tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: 'var(--bg-surface)', border: '1px solid border-[var(--border-default)]', borderRadius: '12px' }}
                                />
                                <Bar dataKey="calls" fill="var(--accent-purple)" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Performance Metrics Table */}
            <div className="glass-card overflow-hidden p-0">
                <div className="px-6 py-4 border-b border-[var(--border-subtle)]">
                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">Agent Efficiency Metrics</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-[var(--bg-overlay)] text-[10px] uppercase tracking-wider font-bold text-[var(--text-tertiary)]">
                            <tr>
                                <th className="px-6 py-4 border-b border-[var(--border-subtle)]">Agent Name</th>
                                <th className="px-6 py-4 border-b border-[var(--border-subtle)]">Total Calls</th>
                                <th className="px-6 py-4 border-b border-[var(--border-subtle)]">Avg Duration</th>
                                <th className="px-6 py-4 border-b border-[var(--border-subtle)]">Avg Latency</th>
                                <th className="px-6 py-4 border-b border-[var(--border-subtle)]">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/[0.04]">
                            {performance.map((p, i) => (
                                <tr key={i} className="hover:bg-[var(--bg-overlay)] transition-colors">
                                    <td className="px-6 py-4 text-xs font-bold text-[var(--text-primary)]">{p.name}</td>
                                    <td className="px-6 py-4 text-xs text-[var(--text-secondary)]">{p.calls}</td>
                                    <td className="px-6 py-4 text-xs text-[var(--text-secondary)]">{p.avg_duration}s</td>
                                    <td className="px-6 py-4 text-xs font-mono font-semibold text-[var(--accent-purple)]">{p.avg_latency}ms</td>
                                    <td className="px-6 py-4">
                                        {p.avg_latency > 350 ? (
                                            <span className="px-2 py-0.5 rounded-full bg-[var(--accent-amber)]/10 text-[var(--accent-amber)] text-[9px] font-bold uppercase tracking-wider border border-[var(--accent-amber)]/20">Degraded</span>
                                        ) : (
                                            <span className="px-2 py-0.5 rounded-full bg-[var(--accent-emerald)]/10 text-[var(--accent-emerald)] text-[9px] font-bold uppercase tracking-wider border border-[var(--accent-emerald)]/20">Healthy</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {performance.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="px-6 py-10 text-center text-[var(--text-tertiary)] text-xs italic">No agent data available yet.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
