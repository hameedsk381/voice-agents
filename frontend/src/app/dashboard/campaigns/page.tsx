'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { Plus, ListFilter, Play, Pause, CheckCircle2, AlertCircle, Phone, Users, Calendar } from 'lucide-react';

interface Campaign {
    id: string;
    name: string;
    status: string;
    total_contacts: number;
    completed_calls: number;
    failed_calls: number;
    created_at: string;
    agent_id: string;
}

export default function CampaignsPage() {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const { token } = useAuth();

    const fetchCampaigns = async () => {
        try {
            const res = await fetch('http://localhost:8001/api/v1/campaigns/', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setCampaigns(data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchCampaigns();
    }, [token]);

    const getStatusStyles = (status: string) => {
        switch (status.toLowerCase()) {
            case 'running': return 'bg-green-500/10 text-green-500 border-green-500/20';
            case 'paused': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
            case 'completed': return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
            default: return 'bg-gray-500/10 text-gray-500 border-white/10';
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Outbound Campaigns</h1>
                    <p className="text-gray-400">Manage automated calling campaigns and contact lists.</p>
                </div>
                <Link href="/dashboard/campaigns/new">
                    <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition-all">
                        <Plus className="w-5 h-5" />
                        New Campaign
                    </button>
                </Link>
            </div>

            {/* Campaign Cards */}
            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map(i => <div key={i} className="h-64 rounded-2xl bg-white/5 animate-pulse border border-white/10" />)}
                </div>
            ) : campaigns.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 bg-white/5 rounded-3xl border border-dashed border-white/10">
                    <Phone className="w-12 h-12 text-gray-600 mb-4" />
                    <h3 className="text-xl font-medium text-white">No campaigns found</h3>
                    <p className="text-gray-400 mt-2 max-w-sm text-center">Create your first outbound campaign to automate your voice interactions.</p>
                    <Link href="/dashboard/campaigns/new" className="mt-6">
                        <button className="text-blue-500 hover:text-blue-400 font-medium underline underline-offset-4">Create Campaign Now</button>
                    </Link>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {campaigns.map((campaign) => (
                        <Link
                            key={campaign.id}
                            href={`/dashboard/campaigns/${campaign.id}`}
                            className="bg-[#141417] border border-white/10 rounded-2xl p-6 hover:border-blue-500/50 transition-all group"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors">{campaign.name}</h3>
                                <div className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border ${getStatusStyles(campaign.status)}`}>
                                    {campaign.status}
                                </div>
                            </div>

                            <div className="space-y-4">
                                {/* Stats */}
                                <div className="grid grid-cols-3 gap-2">
                                    <div className="text-center p-2 rounded-lg bg-white/5 border border-white/5">
                                        <p className="text-xs text-gray-500 uppercase font-bold">Total</p>
                                        <p className="text-lg font-mono text-white">{campaign.total_contacts}</p>
                                    </div>
                                    <div className="text-center p-2 rounded-lg bg-green-500/5 border border-green-500/10">
                                        <p className="text-xs text-green-500/50 uppercase font-bold">Success</p>
                                        <p className="text-lg font-mono text-green-400">{campaign.completed_calls}</p>
                                    </div>
                                    <div className="text-center p-2 rounded-lg bg-red-500/5 border border-red-500/10">
                                        <p className="text-xs text-red-500/50 uppercase font-bold">Failed</p>
                                        <p className="text-lg font-mono text-red-400">{campaign.failed_calls}</p>
                                    </div>
                                </div>

                                {/* Progress Bar */}
                                <div className="space-y-1.5">
                                    <div className="flex justify-between text-[11px] text-gray-500">
                                        <span>Progress</span>
                                        <span>{campaign.total_contacts > 0 ? Math.round((campaign.completed_calls / campaign.total_contacts) * 100) : 0}%</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-blue-500 transition-all duration-500"
                                            style={{ width: `${campaign.total_contacts > 0 ? (campaign.completed_calls / campaign.total_contacts) * 100 : 0}%` }}
                                        />
                                    </div>
                                </div>

                                <div className="flex items-center gap-4 pt-2 border-t border-white/5 text-xs text-gray-500">
                                    <div className="flex items-center gap-1">
                                        <Users className="w-3 h-3" />
                                        <span>Agent #{campaign.agent_id.slice(0, 4)}</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <Calendar className="w-3 h-3" />
                                        <span>{new Date(campaign.created_at).toLocaleDateString()}</span>
                                    </div>
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}
