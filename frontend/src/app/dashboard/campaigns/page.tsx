'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import Link from 'next/link';
import { Plus, Phone, Users, Calendar, Megaphone, Loader2 } from 'lucide-react';
import { Campaign } from '@/types/types';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

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
            case 'running': return 'bg-green-500/10 text-green-600';
            case 'paused': return 'bg-yellow-500/10 text-yellow-600';
            case 'completed': return 'bg-primary/10 text-primary';
            default: return 'bg-muted text-muted-foreground';
        }
    };

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
                        <div className="flex items-center justify-center size-9 rounded-lg bg-primary/10">
                            <Megaphone className="size-5 text-primary" />
                        </div>
                        Outbound{' '}
                        <span className="text-primary">
                            Campaigns
                        </span>
                    </h2>
                    <p className="text-sm text-muted-foreground mt-1">
                        Manage automated calling campaigns and upload customized contact lists.
                    </p>
                </div>
                <Link href="/dashboard/campaigns/new">
                    <Button className="gap-2">
                        <Plus className="size-4" />
                        New Campaign
                    </Button>
                </Link>
            </div>

            {/* Campaign Cards */}
            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {[1, 2, 3].map(i => (
                        <Card key={i} className="h-64 animate-pulse" />
                    ))}
                </div>
            ) : campaigns.length === 0 ? (
                <Card className="border-dashed">
                    <CardContent className="flex flex-col items-center justify-center py-16">
                        <div className="flex items-center justify-center size-14 rounded-full bg-primary/10 mb-4">
                            <Phone className="size-7 text-primary" />
                        </div>
                        <h3 className="text-base font-semibold text-foreground">No campaigns found</h3>
                        <p className="text-sm text-muted-foreground mt-1 max-w-xs text-center leading-relaxed">
                            Create your first outbound campaign to automate your voice interactions.
                        </p>
                        <Link href="/dashboard/campaigns/new" className="mt-5">
                            <Button className="gap-2">
                                <Plus className="size-4" />
                                Create Campaign Now
                            </Button>
                        </Link>
                    </CardContent>
                </Card>
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
                                <Card className="hover:shadow-md transition-all h-full flex flex-col justify-between relative overflow-hidden">
                                    <CardHeader className="pb-0">
                                        <div className="flex items-start justify-between gap-2">
                                            <CardTitle className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors truncate max-w-[170px]">
                                                {campaign.name}
                                            </CardTitle>
                                            <span
                                                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider shrink-0 ${getStatusStyles(campaign.status)}`}
                                            >
                                                {campaign.status}
                                            </span>
                                        </div>
                                    </CardHeader>

                                    <CardContent className="space-y-4 pt-2">
                                        {/* Stats */}
                                        <div className="grid grid-cols-3 gap-2">
                                            <div className="text-center p-2 rounded-xl bg-muted">
                                                <p className="text-[10px] text-muted-foreground uppercase font-semibold tracking-wider">Total</p>
                                                <p className="text-sm font-mono font-semibold text-foreground mt-0.5">{campaign.total_contacts}</p>
                                            </div>
                                            <div className="text-center p-2 rounded-xl bg-green-500/5">
                                                <p className="text-[10px] text-green-600 uppercase font-semibold tracking-wider">Success</p>
                                                <p className="text-sm font-mono font-semibold text-green-600 mt-0.5">{campaign.completed_calls}</p>
                                            </div>
                                            <div className="text-center p-2 rounded-xl bg-red-500/5">
                                                <p className="text-[10px] text-red-600 uppercase font-semibold tracking-wider">Failed</p>
                                                <p className="text-sm font-mono font-semibold text-red-600 mt-0.5">{campaign.failed_calls}</p>
                                            </div>
                                        </div>

                                        {/* Progress Bar */}
                                        <div className="space-y-1">
                                            <div className="flex justify-between text-[11px] font-semibold text-muted-foreground">
                                                <span>Completion Rate</span>
                                                <span className="font-mono">{progress}%</span>
                                            </div>
                                            <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-primary transition-all duration-500 rounded-full"
                                                    style={{ width: `${progress}%` }}
                                                />
                                            </div>
                                        </div>
                                    </CardContent>

                                    <CardFooter className="text-[11px] text-muted-foreground font-medium gap-4">
                                        <div className="flex items-center gap-1.5">
                                            <Users className="w-3.5 h-3.5" />
                                            <span>Agent: #{campaign.agent_id.slice(0, 5)}</span>
                                        </div>
                                        <div className="flex items-center gap-1.5 ml-auto">
                                            <Calendar className="w-3.5 h-3.5" />
                                            <span>{new Date(campaign.created_at).toLocaleDateString()}</span>
                                        </div>
                                    </CardFooter>

                                    {/* Subtle bottom hover line */}
                                    <div className="absolute bottom-0 left-4 right-4 h-[2px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-primary/50" />
                                </Card>
                            </Link>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
