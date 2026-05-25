'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    AreaChart, Area
} from 'recharts';
import {
    TrendingUp, Clock, Zap, DollarSign,
    CheckCircle2, PhoneIncoming, BarChart3, Loader2, Activity
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

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
        { label: 'Total Calls', value: overview?.total_calls || 0, icon: PhoneIncoming, iconStyle: 'bg-primary/10 text-primary' },
        { label: 'Success Rate', value: `${overview?.success_rate || 0}%`, icon: CheckCircle2, iconStyle: 'bg-green-500/10 text-green-600' },
        { label: 'Avg Response Time', value: `${overview?.avg_latency_ms || 0} ms`, icon: Zap, iconStyle: 'bg-secondary/20 text-secondary-foreground' },
        { label: 'Total Minutes', value: overview?.total_minutes || 0, icon: Clock, iconStyle: 'bg-primary/10 text-primary' },
        { label: 'Cost Avoided', value: `₹${overview?.total_cost || 0}`, icon: DollarSign, iconStyle: 'bg-secondary/20 text-secondary-foreground' },
    ];

    if (isLoading) {
        return (
            <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
                    {[1, 2, 3, 4, 5].map((i) => (
                        <Card key={i} className="h-28 animate-pulse" />
                    ))}
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card className="h-80 animate-pulse" />
                    <Card className="h-80 animate-pulse" />
                </div>
                <div className="flex items-center justify-center py-12 text-muted-foreground gap-2">
                    <Loader2 className="size-5 animate-spin" />
                    <span className="text-sm">Loading analytics data...</span>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6 pb-20">
            {/* Page Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
                        <Activity className="size-6 text-primary" />
                        Observability &{' '}
                        <span className="text-primary">
                            Analytics
                        </span>
                    </h2>
                    <p className="text-sm text-muted-foreground mt-1">
                        Call volume, success rates, and agent performance across your organization.
                    </p>
                </div>
            </div>

            {/* Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
                {stats.map((s, i) => (
                    <Card key={i} className="hover:shadow-md transition-all">
                        <CardContent className="pt-1">
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                    {s.label}
                                </span>
                                <div className={`size-9 rounded-lg flex items-center justify-center ${s.iconStyle}`}>
                                    <s.icon className="size-4" />
                                </div>
                            </div>
                            <p className="text-2xl font-semibold text-foreground">{s.value}</p>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Call Volume Trend */}
                <Card className="hover:shadow-md transition-all">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-sm">
                            <div className="size-7 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                                <TrendingUp className="size-4" />
                            </div>
                            Call Volume Trend
                        </CardTitle>
                        <CardDescription>Daily call volume over the selected period</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[280px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>

                                    <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
                                    <XAxis dataKey="date" className="text-muted-foreground" fontSize={10} fontWeight={600} tickLine={false} axisLine={false} />
                                    <YAxis className="text-muted-foreground" fontSize={10} fontWeight={600} tickLine={false} axisLine={false} />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: 'var(--color-card, #1c1c1e)',
                                            border: '1px solid var(--color-border, #2a2a2e)',
                                            borderRadius: '12px',
                                            color: 'var(--color-foreground, #fff)',
                                        }}
                                        itemStyle={{ color: 'var(--color-foreground, #fff)' }}
                                    />
                                    <Area type="monotone" dataKey="count" stroke="#6C5CE7" fill="#6C5CE7" fillOpacity={0.15} strokeWidth={2} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* Agent Distribution */}
                <Card className="hover:shadow-md transition-all">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-sm">
                            <div className="size-7 rounded-lg bg-secondary/20 text-secondary-foreground flex items-center justify-center">
                                <BarChart3 className="size-4" />
                            </div>
                            Agent Distribution
                        </CardTitle>
                        <CardDescription>Call distribution across active agents</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[280px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={performance} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
                                    <XAxis dataKey="name" className="text-muted-foreground" fontSize={10} fontWeight={600} tickLine={false} axisLine={false} />
                                    <YAxis className="text-muted-foreground" fontSize={10} fontWeight={600} tickLine={false} axisLine={false} />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: 'var(--color-card, #1c1c1e)',
                                            border: '1px solid var(--color-border, #2a2a2e)',
                                            borderRadius: '12px',
                                            color: 'var(--color-foreground, #fff)',
                                        }}
                                    />
                                    <Bar dataKey="calls" fill="#6C5CE7" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Performance Metrics Table */}
            <Card className="hover:shadow-md transition-all">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-sm">
                        <div className="size-7 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                            <Zap className="size-4" />
                        </div>
                        Agent Efficiency Metrics
                    </CardTitle>
                    <CardDescription>Per-agent latency, call volume, and health status</CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-border bg-muted/50">
                                    <th className="px-6 py-3 text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">Agent Name</th>
                                    <th className="px-6 py-3 text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">Total Calls</th>
                                    <th className="px-6 py-3 text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">Avg Duration</th>
                                    <th className="px-6 py-3 text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">Avg Latency</th>
                                    <th className="px-6 py-3 text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                {performance.map((p, i) => (
                                    <tr key={i} className="hover:bg-muted/50 transition-colors">
                                        <td className="px-6 py-4 text-xs font-semibold text-foreground">{p.name}</td>
                                        <td className="px-6 py-4 text-xs text-muted-foreground">{p.calls}</td>
                                        <td className="px-6 py-4 text-xs text-muted-foreground">{p.avg_duration}s</td>
                                        <td className="px-6 py-4 text-xs font-mono font-semibold text-primary">{p.avg_latency}ms</td>
                                        <td className="px-6 py-4">
                                            {p.avg_latency > 350 ? (
                                                <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-yellow-500/10 text-yellow-600">
                                                    Degraded
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-500/10 text-green-600">
                                                    Healthy
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                                {performance.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-12 text-center">
                                            <div className="flex flex-col items-center gap-2">
                                                <BarChart3 className="size-8 text-muted-foreground/50" />
                                                <p className="text-sm text-muted-foreground">No agent data available yet.</p>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
