"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
    Activity, Phone, Clock, DollarSign, Loader2, CheckCircle2, Wifi, Zap, Bot,
    TrendingDown, BarChart3, Target, Gauge, PieChart as PieChartIcon
} from "lucide-react";
import api, { fetchMyOrganization } from "@/lib/api";
import {
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, Legend
} from 'recharts';

const COLORS = ['hsl(var(--primary))', '#ef4444', '#6b7280'];

function KpiCard({ title, value, sub, icon: Icon, color }: any) {
    return (
        <Card className="hover:shadow-md transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
                <div className={`size-9 rounded-lg ${color.bg} flex items-center justify-center`}>
                    <Icon className={`h-4 w-4 ${color.text}`} />
                </div>
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-semibold">{value}</div>
                <p className="text-xs text-muted-foreground mt-1">{sub}</p>
            </CardContent>
        </Card>
    );
}

export default function DashboardPage() {
    const router = useRouter();
    const [kpi, setKpi] = useState<any>(null);
    const [trends, setTrends] = useState<any[]>([]);
    const [peakHours, setPeakHours] = useState<any>(null);
    const [quality, setQuality] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const init = async () => {
            try {
                const org = await fetchMyOrganization();
                if (!org.settings?.onboarding_completed) {
                    router.replace('/dashboard/onboarding');
                    return;
                }
            } catch { /* ignore */ }

            try {
                const [kpiData, trendData, peakData, qualityData] = await Promise.all([
                    api.get("/analytics/kpi"),
                    api.get("/analytics/weekly-trend"),
                    api.get("/analytics/peak-hours"),
                    api.get("/analytics/quality"),
                ]);
                setKpi(kpiData);
                setTrends(trendData || []);
                setPeakHours(peakData);
                setQuality(qualityData);
            } catch (error) {
                console.error("Failed to fetch dashboard data:", error);
            } finally {
                setLoading(false);
            }
        };

        init();
    }, [router]);

    if (loading) {
        return (
            <div className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    {[1, 2, 3, 4].map((i) => (
                        <Card key={i} className="h-28 animate-pulse bg-muted/50" />
                    ))}
                </div>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                    <Card className="col-span-4 h-80 animate-pulse bg-muted/50" />
                    <Card className="col-span-3 h-80 animate-pulse bg-muted/50" />
                </div>
            </div>
        );
    }

    const hasData = kpi && kpi.total_calls > 0;

    const kpiCards = [
        {
            title: "Cost per Call",
            value: hasData ? `₹${kpi.cost_per_call}` : "—",
            icon: DollarSign,
            color: { bg: "bg-primary/10", text: "text-primary" },
            sub: hasData ? `${kpi.total_calls} total calls` : "No calls yet"
        },
        {
            title: "Avg Handle Time",
            value: hasData ? `${kpi.avg_handle_time_sec}s` : "—",
            icon: Clock,
            color: { bg: "bg-secondary/20", text: "text-secondary-foreground" },
            sub: hasData ? `${kpi.avg_turns_per_call} avg turns` : "—"
        },
        {
            title: "Success Rate",
            value: hasData ? `${kpi.success_rate}%` : "—",
            icon: CheckCircle2,
            color: { bg: "bg-green-500/10", text: "text-green-600" },
            sub: hasData ? `${kpi.outcome_breakdown.success} succeeded` : "—"
        },
        {
            title: "Abandonment",
            value: hasData ? `${kpi.abandonment_rate}%` : "—",
            icon: TrendingDown,
            color: { bg: "bg-red-500/10", text: "text-red-500" },
            sub: hasData ? `${kpi.outcome_breakdown.failure} failed` : "—"
        },
    ];

    const outcomeData = hasData ? [
        { name: 'Success', value: kpi.outcome_breakdown.success },
        { name: 'Failed', value: kpi.outcome_breakdown.failure },
        { name: 'Neutral', value: kpi.outcome_breakdown.neutral },
    ].filter(d => d.value > 0) : [];

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h2 className="text-2xl font-semibold tracking-tight">
                        <span className="text-primary">Overview</span>
                    </h2>
                    <p className="text-sm text-muted-foreground mt-1">Business KPIs, call volume, and platform health at a glance.</p>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {kpiCards.map((s) => (
                    <KpiCard key={s.title} {...s} />
                ))}
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                {/* Call Volume Trend */}
                <Card className="col-span-full lg:col-span-4 hover:shadow-md transition-all">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Activity className="h-4 w-4 text-primary" />
                            Call Volume (14d)
                        </CardTitle>
                        <CardDescription>Daily calls, minutes, cost, and latency trend.</CardDescription>
                    </CardHeader>
                    <CardContent className="pl-0 h-[250px]">
                        {trends.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%" minHeight={250}>
                                <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-border" opacity={0.5} />
                                    <XAxis dataKey="date" className="text-muted-foreground" fontSize={12} tickLine={false} axisLine={false} />
                                    <YAxis className="text-muted-foreground" fontSize={12} tickLine={false} axisLine={false} />
                                    <Tooltip contentStyle={{ backgroundColor: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: '8px', fontSize: '12px' }}
                                        itemStyle={{ color: 'var(--color-foreground)' }} />
                                    <Area type="monotone" dataKey="calls" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.2} name="Calls" />
                                </AreaChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex items-center justify-center h-full">
                                <p className="text-xs text-muted-foreground">No trend data yet</p>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Quality Score + System Status */}
                <Card className="col-span-full lg:col-span-3 hover:shadow-md transition-all">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Gauge className="h-4 w-4 text-primary" />
                            Call Quality
                        </CardTitle>
                        <CardDescription>Composite quality score based on latency, turns, and outcome.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {hasData ? (
                            <>
                                <div className="flex items-center justify-center py-2">
                                    <div className="relative size-24">
                                        <svg className="size-24 -rotate-90" viewBox="0 0 36 36">
                                            <circle cx="18" cy="18" r="16" fill="none" stroke="hsl(var(--muted))" strokeWidth="3" />
                                            <circle cx="18" cy="18" r="16" fill="none" stroke="hsl(var(--primary))" strokeWidth="3"
                                                strokeDasharray={`${(quality?.score || 0) * 1.01} 100`}
                                                strokeLinecap="round" />
                                        </svg>
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <span className="text-xl font-bold">{quality?.grade || "—"}</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-2 text-center text-xs">
                                    <div className="p-2 bg-muted/50 rounded-lg">
                                        <p className="text-muted-foreground">Latency</p>
                                        <p className="font-semibold">{quality?.latency_ms || "—"} ms</p>
                                    </div>
                                    <div className="p-2 bg-muted/50 rounded-lg">
                                        <p className="text-muted-foreground">Turns</p>
                                        <p className="font-semibold">{quality?.avg_turns || "—"}</p>
                                    </div>
                                    <div className="p-2 bg-muted/50 rounded-lg">
                                        <p className="text-muted-foreground">Outcome</p>
                                        <p className="font-semibold">{quality?.outcome_score || "—"}</p>
                                    </div>
                                    <div className="p-2 bg-muted/50 rounded-lg">
                                        <p className="text-muted-foreground">Score</p>
                                        <p className="font-semibold">{quality?.score || "—"}/100</p>
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="flex flex-col items-center justify-center py-8 text-center">
                                <Gauge className="size-8 text-muted-foreground mb-2" />
                                <p className="text-xs text-muted-foreground">No call data yet</p>
                            </div>
                        )}

                        <div className="border-t border-border pt-4 space-y-2">
                            <div className="flex items-center justify-between text-xs">
                                <span className="text-muted-foreground">Platform</span>
                                <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium bg-green-500/10 text-green-600">Online</span>
                            </div>
                            <div className="flex items-center justify-between text-xs">
                                <span className="text-muted-foreground">Avg Latency</span>
                                <span className="font-mono font-semibold">{hasData ? `${Math.round(kpi.avg_latency_ms)} ms` : "—"}</span>
                            </div>
                            <div className="flex items-center justify-between text-xs">
                                <span className="text-muted-foreground">Total Tokens</span>
                                <span className="font-mono font-semibold">{hasData ? kpi.total_tokens.toLocaleString() : "—"}</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                {/* Outcome Distribution */}
                <Card className="col-span-full lg:col-span-3 hover:shadow-md transition-all">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <PieChartIcon className="h-4 w-4 text-primary" />
                            Outcome Distribution
                        </CardTitle>
                        <CardDescription>Breakdown of call results.</CardDescription>
                    </CardHeader>
                    <CardContent className="h-[220px]">
                        {outcomeData.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%" minHeight={220}>
                                <PieChart>
                                    <Pie data={outcomeData} cx="50%" cy="50%" outerRadius={70} dataKey="value" label={({ name, percent }: any) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}>
                                        {outcomeData.map((_, i) => (
                                            <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex items-center justify-center h-full">
                                <p className="text-xs text-muted-foreground">No outcome data yet</p>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Peak Hours */}
                <Card className="col-span-full lg:col-span-4 hover:shadow-md transition-all">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <BarChart3 className="h-4 w-4 text-primary" />
                            Peak Hours
                        </CardTitle>
                        <CardDescription>
                            {hasData
                                ? `Busiest hour: ${peakHours?.peak_hour ?? "—"}:00 (${peakHours?.peak_volume ?? 0} calls)`
                                : "Call volume by hour of day"}
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="pl-0 h-[220px]">
                        {hasData ? (
                            <ResponsiveContainer width="100%" height="100%" minHeight={220}>
                                <BarChart data={peakHours?.distribution || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-border" opacity={0.5} />
                                    <XAxis dataKey="hour" className="text-muted-foreground" fontSize={12} tickLine={false} axisLine={false}
                                        tickFormatter={(h) => `${h}:00`} />
                                    <YAxis className="text-muted-foreground" fontSize={12} tickLine={false} axisLine={false} />
                                    <Tooltip contentStyle={{ backgroundColor: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: '8px', fontSize: '12px' }}
                                        itemStyle={{ color: 'var(--color-foreground)' }} labelFormatter={(h) => `${h}:00`} />
                                    <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} maxBarSize={20} name="Calls" />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex items-center justify-center h-full">
                                <p className="text-xs text-muted-foreground">No hourly data yet</p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Trend Details */}
            {trends.length > 0 && (
                <Card className="hover:shadow-md transition-all">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <BarChart3 className="h-4 w-4 text-primary" />
                            Daily Trend Details
                        </CardTitle>
                        <CardDescription>Minutes, cost, and latency per day.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="overflow-x-auto">
                            <table className="w-full text-xs">
                                <thead>
                                    <tr className="border-b border-border">
                                        <th className="text-left py-2 px-2 font-semibold text-muted-foreground">Date</th>
                                        <th className="text-right py-2 px-2 font-semibold text-muted-foreground">Calls</th>
                                        <th className="text-right py-2 px-2 font-semibold text-muted-foreground">Minutes</th>
                                        <th className="text-right py-2 px-2 font-semibold text-muted-foreground">Cost</th>
                                        <th className="text-right py-2 px-2 font-semibold text-muted-foreground">Avg Latency</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {trends.slice().reverse().map((d: any) => (
                                        <tr key={d.date} className="border-b border-border/50 hover:bg-muted/30">
                                            <td className="py-2 px-2 font-medium">{d.date}</td>
                                            <td className="py-2 px-2 text-right">{d.calls}</td>
                                            <td className="py-2 px-2 text-right font-mono">{d.total_minutes}</td>
                                            <td className="py-2 px-2 text-right font-mono">₹{d.total_cost}</td>
                                            <td className="py-2 px-2 text-right font-mono">{d.avg_latency_ms} ms</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
