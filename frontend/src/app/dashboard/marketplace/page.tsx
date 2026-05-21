'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';
import {
    ShoppingBag, Star, Download, Shield,
    Zap, TrendingUp, Filter, Sparkles,
    HeartPulse, Globe, Briefcase, Key, Rocket
} from 'lucide-react';

interface Template {
    id: string;
    name: string;
    category: string;
    role: string;
    description: string;
    persona: string;
    language: string;
    recommended_tools: string[];
    popularity: number;
    rating: number;
}

export default function MarketplacePage() {
    const router = useRouter();
    const [templates, setTemplates] = useState<Template[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [installing, setInstalling] = useState<string | null>(null);

    useEffect(() => {
        const fetchTemplates = async () => {
            try {
                const data = await api.get("/marketplace/templates");
                setTemplates(data);
            } catch (err) {
                console.error(err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchTemplates();
    }, []);

    const handleInstall = async (id: string) => {
        setInstalling(id);
        try {
            const data = await api.post(`/marketplace/install/${id}`, {});
            router.push(`/dashboard/agents/${data.agent_id}`);
        } catch (err) {
            console.error(err);
        } finally {
            setInstalling(null);
        }
    };

    const categories = Array.from(new Set(templates.map(t => t.category)));

    const formatCategoryLabel = (category: string) => {
        const labels: Record<string, string> = {
            Orchestration: "Workflow packs",
            Technical: "Specialized",
        };
        return labels[category] || category;
    };

    const getCategoryIcon = (category: string) => {
        switch (category) {
            case 'Healthcare': return <HeartPulse className="w-5 h-5 text-[var(--accent-rose)]" />;
            case 'Security': return <Key className="w-5 h-5 text-[var(--accent-cyan)]" />;
            case 'Corporate': return <Briefcase className="w-5 h-5 text-[var(--accent-amber)]" />;
            case 'Travel': return <Globe className="w-5 h-5 text-[var(--accent-emerald)]" />;
            case 'Sales': return <TrendingUp className="w-5 h-5 text-[var(--accent-emerald)]" />;
            case 'Billing': return <Shield className="w-5 h-5 text-[var(--accent-blue)]" />;
            case 'Technical': return <Zap className="w-5 h-5 text-[var(--accent-amber)]" />;
            case 'Orchestration': return <Rocket className="w-5 h-5 text-[var(--accent-purple)]" />;
            default: return <Sparkles className="w-5 h-5 text-[var(--accent-purple)]" />;
        }
    };

    if (isLoading) {
        return (
            <div className="space-y-6">
                <div className="glass-card h-52 animate-pulse" />
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {[1, 2, 3].map(i => <div key={i} className="glass-card h-64 animate-pulse" />)}
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6 pb-20">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)] flex items-center gap-2">
                        Agent <span className="text-gradient-brand">Marketplace</span>
                    </h2>
                    <p className="text-xs text-[var(--text-secondary)] mt-1">Deploy premium, pre-configured voice agents in one click.</p>
                </div>

                <div className="flex items-center gap-2 select-none">
                    <div className="bg-[var(--bg-overlay)] border border-[var(--border-default)] hover:bg-[var(--glass-bg-hover)] rounded-xl px-3.5 py-1.5 flex items-center gap-2 text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] cursor-pointer transition-colors">
                        <Filter className="w-3.5 h-3.5" />
                        <span>Filter</span>
                    </div>
                    <div className="bg-[var(--accent-purple)]/10 border border-[var(--accent-purple)]/20 text-[var(--accent-purple)] rounded-xl px-3.5 py-1.5 flex items-center gap-2 text-xs font-bold">
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Featured</span>
                    </div>
                </div>
            </div>

            {/* Featured Banner */}
            <div className="relative overflow-hidden bg-gradient-to-br from-indigo-500/10 via-purple-500/10 to-pink-500/10 border border-[var(--border-default)] rounded-2xl p-6 md:p-8 flex flex-col md:flex-row items-center gap-6 shadow-2xl relative">
                <div className="absolute top-0 right-0 w-64 h-64 bg-pink-500/10 blur-[100px] pointer-events-none -z-10" />
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-blue-500/10 blur-[100px] pointer-events-none -z-10" />

                <div className="flex-1 space-y-4">
                    <span className="bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-blue)] text-white text-[9px] font-black uppercase px-2.5 py-1 rounded shadow-md tracking-wider">New Arrival</span>
                    <h2 className="text-2xl md:text-3xl font-extrabold text-[var(--text-primary)]">Super-Agent Hub v2</h2>
                    <p className="text-xs text-[var(--text-secondary)] max-w-xl leading-relaxed">
                        A pre-built multi-scenario agent pack for support, healthcare intake, and security verification—ready to deploy on your campaigns.
                    </p>
                    <button
                        onClick={() => handleInstall('tpl_multi_agent')}
                        className="bg-white text-black px-5 py-2.5 rounded-xl font-bold text-xs hover:-translate-y-0.5 hover:shadow-lg transition-all active:scale-98"
                    >
                        Deploy Hub Now
                    </button>
                </div>
                <div className="relative w-40 h-40 bg-[var(--bg-overlay)] rounded-full flex items-center justify-center border border-[var(--border-subtle)] group backdrop-blur-sm shrink-0">
                    <Rocket className="w-16 h-16 text-[var(--accent-purple)] group-hover:scale-110 transition-transform duration-500" />
                </div>
            </div>

            {/* Categorized Grid */}
            {categories.map(category => (
                <div key={category} className="space-y-4 pt-4">
                    <div className="flex items-center gap-4">
                        <h3 className="text-[10px] font-bold text-[var(--text-tertiary)] uppercase tracking-widest">{formatCategoryLabel(category)}</h3>
                        <div className="h-[1px] flex-1 bg-gradient-to-r from-white/[0.06] to-transparent" />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                        {templates.filter(t => t.category === category).map(template => (
                            <div key={template.id} className="group relative glass-card overflow-hidden hover:border-[var(--border-active)] transition-all flex flex-col h-full">
                                <div className="p-5 flex flex-col h-full">
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="w-10 h-10 bg-[var(--bg-overlay)] rounded-xl flex items-center justify-center border border-[var(--border-subtle)] group-hover:scale-105 transition-all">
                                            {getCategoryIcon(template.category)}
                                        </div>
                                        <div className="flex items-center gap-1 text-[9px] font-black text-yellow-500 bg-yellow-500/10 px-2 py-0.5 rounded-full border border-yellow-500/20">
                                            <Star className="w-3 h-3 fill-current" />
                                            {template.rating}
                                        </div>
                                    </div>

                                    <h4 className="text-sm font-bold text-[var(--text-primary)] group-hover:text-[var(--accent-cyan)] transition-colors">{template.name}</h4>
                                    <p className="text-[9px] font-bold text-[var(--text-tertiary)] uppercase tracking-wider mt-0.5">{template.role}</p>
                                    
                                    <p className="text-xs text-[var(--text-secondary)] mt-3 mb-6 line-clamp-2 leading-relaxed h-8">
                                        {template.description}
                                    </p>

                                    <div className="mt-auto pt-4 border-t border-[var(--border-subtle)] flex items-center justify-between">
                                        <div className="flex -space-x-1.5">
                                            {template.recommended_tools.slice(0, 3).map((tool, i) => (
                                                <div key={i} className="w-6.5 h-6.5 bg-gray-900 border border-[var(--border-default)] rounded-full flex items-center justify-center text-[9px] text-[var(--text-secondary)] uppercase font-black hover:z-10 transition-all select-none" title={tool}>
                                                    {tool[0]}
                                                </div>
                                            ))}
                                            {template.recommended_tools.length > 3 && (
                                                <div className="w-6.5 h-6.5 bg-gray-900 border border-[var(--border-default)] rounded-full flex items-center justify-center text-[9px] text-[var(--text-tertiary)] font-bold">
                                                    +{template.recommended_tools.length - 3}
                                                </div>
                                            )}
                                        </div>

                                        <button
                                            onClick={() => handleInstall(template.id)}
                                            disabled={installing === template.id}
                                            className="flex items-center gap-2 bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white px-3.5 py-2 rounded-xl text-xs font-bold transition-all disabled:opacity-50 hover:-translate-y-0.5 active:translate-y-0 active:scale-98"
                                        >
                                            {installing === template.id ? (
                                                <div className="flex items-center gap-2">
                                                    <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                                    <span>Installing</span>
                                                </div>
                                            ) : (
                                                <>
                                                    <Download className="w-3.5 h-3.5" />
                                                    <span>Deploy</span>
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}
