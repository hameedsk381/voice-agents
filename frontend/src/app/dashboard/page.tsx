"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Phone, Clock, DollarSign, Loader2 } from "lucide-react";
import api from "@/lib/api";
import {
    LineChart,
    Line,
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
    const [shadowStats, setShadowStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                const [overviewData, trendsData, shadowData] = await Promise.all([
                    api.get("/analytics/overview"),
                    api.get("/analytics/daily-trends"),
                    api.get("/analytics/shadow-stats")
                ]);
                setStats(overviewData);
                setTrends(trendsData);
                setShadowStats(shadowData);
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
            <div className="flex items-center justify-center h-96">
                <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
        );
    }

    const cards = [
        {
            title: "Total Calls",
            value: stats?.total_calls || 0,
            icon: Phone,
            color: "text-blue-500",
            sub: "Total interactions"
        },
        {
            title: "Shadow Similarity",
            value: `${((shadowStats?.avg_similarity || 0) * 100).toFixed(1)}%`,
            icon: Activity,
            color: "text-orange-400",
            sub: "Primary vs Shadow match"
        },
        {
            title: "Success Rate",
            value: `${stats?.success_rate || 0}%`,
            icon: Activity,
            color: "text-green-500",
            sub: "Goal completion"
        },
        {
            title: "Total Cost",
            value: `$${stats?.total_cost || 0}`,
            icon: DollarSign,
            color: "text-orange-500",
            sub: "Estimated spend"
        },
    ];

    return (
        <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {cards.map((stat) => (
                    <Card key={stat.title} className="bg-gray-900 border-gray-800">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-gray-400">
                                {stat.title}
                            </CardTitle>
                            <stat.icon className={`h-4 w-4 ${stat.color}`} />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-white">{stat.value}</div>
                            <p className="text-xs text-gray-500 mt-1">{stat.sub}</p>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4 bg-gray-900 border-gray-800">
                    <CardHeader>
                        <CardTitle className="text-white">Call Trends (Last 7 Days)</CardTitle>
                    </CardHeader>
                    <CardContent className="h-80">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={trends}>
                                <defs>
                                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    stroke="#9ca3af"
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <YAxis
                                    stroke="#9ca3af"
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={(value) => `${value}`}
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="count"
                                    stroke="#3b82f6"
                                    fillOpacity={1}
                                    fill="url(#colorCount)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                <Card className="col-span-3 bg-gray-900 border-gray-800">
                    <CardHeader>
                        <CardTitle className="text-white">System Health</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-400">API Gateway</span>
                                <div className="flex items-center gap-2">
                                    <span className="text-sm text-green-400 font-medium">Online</span>
                                    <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                                </div>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-400">Shadow Audit Engine</span>
                                <span className="text-sm text-blue-400 font-medium">Active ({shadowStats?.total_runs || 0} runs)</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-400">Potential Latency Savings</span>
                                <span className="text-sm text-yellow-400">-{shadowStats?.latency_savings || 0}ms</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-400">LLM Provider (Groq)</span>
                                <span className="text-sm text-green-400">99.9% Uptime</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-400">Voice Synthesis (Qwen)</span>
                                <span className="text-sm text-green-400">Active</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {shadowStats?.model_performance?.length > 0 && (
                <Card className="bg-gray-900 border-gray-800">
                    <CardHeader>
                        <CardTitle className="text-white">Shadow Model Optimization</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {shadowStats.model_performance.map((perf: any, idx: number) => (
                                <div key={idx} className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
                                    <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider">Configuration</div>
                                    <div className="text-sm font-medium text-white mb-3">
                                        {perf.primary} ➔ {perf.shadow}
                                    </div>
                                    <div className="flex items-end justify-between">
                                        <div>
                                            <div className="text-2xl font-bold text-blue-400">{(perf.similarity * 100).toFixed(1)}%</div>
                                            <div className="text-[10px] text-gray-400">Similarity Accuracy</div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-sm text-white">{perf.runs}</div>
                                            <div className="text-[10px] text-gray-400">Total Samples</div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
