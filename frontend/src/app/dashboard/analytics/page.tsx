'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    LineChart, Line, AreaChart, Area, PieChart, Pie, Cell
} from 'recharts';
import {
    TrendingUp, Users, Clock, Zap, DollarSign,
    CheckCircle2, AlertCircle, PhoneIncoming, BarChart3
} from 'lucide-react';

export default function AnalyticsPage() {
    const { token } = useAuth();
    const [overview, setOverview] = useState<any>(null);
    const [trends, setTrends] = useState<any[]>([]);
    const [performance, setPerformance] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const headers = { 'Authorization': `Bearer ${token}` };

                const [overviewRes, trendsRes, perfRes] = await Promise.all([
                    fetch('http://localhost:8001/api/v1/analytics/overview', { headers }),
                    fetch('http://localhost:8001/api/v1/analytics/daily-trends', { headers }),
                    fetch('http://localhost:8001/api/v1/analytics/agent-performance', { headers })
                ]);

                if (overviewRes.ok) setOverview(await overviewRes.json());
                if (trendsRes.ok) setTrends(await trendsRes.json());
                if (perfRes.ok) setPerformance(await perfRes.json());
            } catch (err) {
                console.error("Failed to fetch analytics", err);
            } finally {
                setIsLoading(false);
            }
        };

        if (token) fetchData();
    }, [token]);

    const stats = [
        { label: 'Total Calls', value: overview?.total_calls || 0, icon: PhoneIncoming, color: 'text-blue-500' },
        { label: 'Success Rate', value: `${overview?.success_rate || 0}%`, icon: CheckCircle2, color: 'text-green-500' },
        { label: 'Avg Latency', value: `${overview?.avg_latency_ms || 0}ms`, icon: Zap, color: 'text-yellow-500' },
        { label: 'Total Minutes', value: overview?.total_minutes || 0, icon: Clock, color: 'text-purple-500' },
        { label: 'Cost Avoided', value: `$${overview?.total_cost || 0}`, icon: DollarSign, color: 'text-emerald-500' },
    ];

    if (isLoading) return <div className="p-10 text-white">Loading data insights...</div>;

    return (
        <div className="space-y-8 pb-20">
            <div>
                <h1 className="text-2xl font-bold text-white">Observability & Analytics</h1>
                <p className="text-gray-400">Deep insights into agent performance, latency, and platform usage.</p>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6">
                {stats.map((s, i) => (
                    <div key={i} className="bg-[#141417] border border-white/10 rounded-2xl p-6">
                        <div className="flex items-center gap-3 mb-2">
                            <s.icon className={`w-4 h-4 ${s.color}`} />
                            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">{s.label}</span>
                        </div>
                        <p className="text-2xl font-bold text-white">{s.value}</p>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Traffic Trend */}
                <div className="bg-[#141417] border border-white/10 rounded-2xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-blue-500" />
                        Call Volume Trend
                    </h3>
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={trends}>
                                <defs>
                                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
                                <XAxis dataKey="date" stroke="#525252" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="#525252" fontSize={12} tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f0f10', border: '1px solid #262626', borderRadius: '8px' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Area type="monotone" dataKey="count" stroke="#3b82f6" fillOpacity={1} fill="url(#colorCount)" strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Agent Comparison */}
                <div className="bg-[#141417] border border-white/10 rounded-2xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-purple-500" />
                        Agent Distribution
                    </h3>
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={performance}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
                                <XAxis dataKey="name" stroke="#525252" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="#525252" fontSize={12} tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f0f10', border: '1px solid #262626', borderRadius: '8px' }}
                                />
                                <Bar dataKey="calls" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Performance Metrics Table */}
            <div className="bg-[#141417] border border-white/10 rounded-2xl overflow-hidden">
                <div className="px-6 py-4 border-b border-white/10">
                    <h3 className="font-semibold text-white">Agent Efficiency Metrics</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-white/[0.02] text-[10px] uppercase tracking-wider font-bold text-gray-500">
                            <tr>
                                <th className="px-6 py-4">Agent Name</th>
                                <th className="px-6 py-4">Total Calls</th>
                                <th className="px-6 py-4">Avg Duration</th>
                                <th className="px-6 py-4">Avg Latency</th>
                                <th className="px-6 py-4">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {performance.map((p, i) => (
                                <tr key={i} className="hover:bg-white/[0.01] transition-colors">
                                    <td className="px-6 py-4 text-sm font-medium text-white">{p.name}</td>
                                    <td className="px-6 py-4 text-sm text-gray-400">{p.calls}</td>
                                    <td className="px-6 py-4 text-sm text-gray-400">{p.avg_duration}s</td>
                                    <td className="px-6 py-4 text-sm font-mono text-yellow-500">{p.avg_latency}ms</td>
                                    <td className="px-6 py-4">
                                        <span className="px-2 py-1 rounded bg-green-500/10 text-green-500 text-[10px] font-bold uppercase tracking-tighter">Healthy</span>
                                    </td>
                                </tr>
                            ))}
                            {performance.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="px-6 py-10 text-center text-gray-500 text-sm">No agent data available yet.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
