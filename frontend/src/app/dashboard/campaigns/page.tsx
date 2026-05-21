'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import Link from 'next/link';
import { Plus, Phone, Users, Calendar } from 'lucide-react';
import { Campaign } from '@/types/types';

export default function CampaignsPage() {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const fetchCampaigns = async () => {
        try {
            const data = await api.get("/campaigns/");
            setCampaigns(data);
        } catch (err) {
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchCampaigns();
    }, []);

    const getStatusStyles = (status: string) => {
        switch (status.toLowerCase()) {
            case 'running': return 'bg-[var(--accent-emerald)]/10 text-[var(--accent-emerald)] border-[var(--accent-emerald)]/20';
            case 'paused': return 'bg-[var(--accent-amber)]/10 text-[var(--accent-amber)] border-[var(--accent-amber)]/20';
            case 'completed': return 'bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] border-[var(--accent-blue)]/20';
            default: return 'bg-[var(--glass-bg)] text-[var(--text-tertiary)] border-[var(--border-subtle)]';
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                        Outbound <span className="text-gradient-brand">Campaigns</span>
                    </h2>
                    <p className="text-xs text-[var(--text-secondary)] mt-1">Manage automated calling campaigns and upload customized contact lists.</p>
                </div>
                <Link href="/dashboard/campaigns/new">
                    <button className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white hover:shadow-lg hover:shadow-[var(--accent-cyan)]/25 transition-all duration-300">
                        <Plus className="w-4 h-4" />
                        New Campaign
                    </button>
                </Link>
            </div>

            {/* Campaign Cards */}
            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {[1, 2, 3].map(i => <div key={i} className="h-64 glass-card animate-pulse" />)}
                </div>
            ) : campaigns.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 bg-[var(--bg-overlay)] rounded-2xl border border-dashed border-[var(--border-default)]">
                    <Phone className="w-10 h-10 text-[var(--text-tertiary)] mb-3" />
                    <h3 className="text-xs font-bold text-[var(--text-primary)]">No campaigns found</h3>
                    <p className="text-[10px] text-[var(--text-tertiary)] mt-1 max-w-xs text-center leading-relaxed">Create your first outbound campaign to automate your voice interactions.</p>
                    <Link href="/dashboard/campaigns/new" className="mt-4">
                        <span className="text-xs font-semibold text-[var(--accent-cyan)] hover:underline cursor-pointer">Create Campaign Now</span>
                    </Link>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {campaigns.map((campaign) => {
                        const progress = campaign.total_contacts && campaign.total_contacts > 0 
                            ? Math.round(((campaign.completed_calls || 0) / campaign.total_contacts) * 100) 
                            : 0;
                        return (
                            <Link
                                key={campaign.id}
                                href={`/dashboard/campaigns/${campaign.id}`}
                                className="group block"
                            >
                                <div className="glass-card p-5 group flex flex-col justify-between h-full hover:border-[var(--border-active)] transition-all relative">
                                    <div className="flex items-start justify-between mb-4 gap-2">
                                        <h3 className="text-sm font-bold text-[var(--text-primary)] group-hover:text-[var(--accent-cyan)] transition-colors truncate max-w-[170px]">{campaign.name}</h3>
                                        <div className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider border shrink-0 ${getStatusStyles(campaign.status)}`}>
                                            {campaign.status}
                                        </div>
                                    </div>

                                    <div className="space-y-4">
                                        {/* Stats */}
                                        <div className="grid grid-cols-3 gap-2">
                                            <div className="text-center p-2 rounded-xl bg-[var(--bg-overlay)] border border-[var(--border-subtle)]">
                                                <p className="text-[9px] text-[var(--text-tertiary)] uppercase font-bold tracking-wider">Total</p>
                                                <p className="text-sm font-mono font-bold text-[var(--text-primary)] mt-0.5">{campaign.total_contacts}</p>
                                            </div>
                                            <div className="text-center p-2 rounded-xl bg-[var(--accent-emerald)]/[0.03] border border-[var(--accent-emerald)]/10">
                                                <p className="text-[9px] text-[var(--accent-emerald)]/70 uppercase font-bold tracking-wider">Success</p>
                                                <p className="text-sm font-mono font-bold text-[var(--accent-emerald)] mt-0.5">{campaign.completed_calls}</p>
                                            </div>
                                            <div className="text-center p-2 rounded-xl bg-[var(--accent-rose)]/[0.03] border border-[var(--accent-rose)]/10">
                                                <p className="text-[9px] text-[var(--accent-rose)]/70 uppercase font-bold tracking-wider">Failed</p>
                                                <p className="text-sm font-mono font-bold text-[var(--accent-rose)] mt-0.5">{campaign.failed_calls}</p>
                                            </div>
                                        </div>

                                        {/* Progress Bar */}
                                        <div className="space-y-1">
                                            <div className="flex justify-between text-[10px] font-semibold text-[var(--text-secondary)]">
                                                <span>Completion Rate</span>
                                                <span className="font-mono">{progress}%</span>
                                            </div>
                                            <div className="h-1.5 w-full bg-[var(--glass-bg)] rounded-full overflow-hidden border border-[var(--border-subtle)]">
                                                <div
                                                    className="h-full bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] transition-all duration-500 rounded-full"
                                                    style={{ width: `${progress}%` }}
                                                />
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-4 pt-4 border-t border-[var(--border-subtle)] text-[10px] text-[var(--text-tertiary)] font-medium">
                                            <div className="flex items-center gap-1.5">
                                                <Users className="w-3.5 h-3.5" />
                                                <span>Agent: #{campaign.agent_id.slice(0, 5)}</span>
                                            </div>
                                            <div className="flex items-center gap-1.5 ml-auto">
                                                <Calendar className="w-3.5 h-3.5" />
                                                <span>{new Date(campaign.created_at).toLocaleDateString()}</span>
                                            </div>
                                        </div>
                                    </div>
                                    {/* Subtle bottom hover line */}
                                    <div className="absolute bottom-0 left-4 right-4 h-[2px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gradient-to-r from-transparent via-[var(--accent-cyan)] to-transparent" />
                                </div>
                            </Link>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
