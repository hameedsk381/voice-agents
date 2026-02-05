'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import {
    ShoppingBag, Star, Download, Shield,
    Zap, Headphones, TrendingUp, Filter, Sparkles,
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
    const { token } = useAuth();
    const router = useRouter();
    const [templates, setTemplates] = useState<Template[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [installing, setInstalling] = useState<string | null>(null);

    useEffect(() => {
        const fetchTemplates = async () => {
            try {
                const res = await fetch('http://localhost:8001/api/v1/marketplace/templates', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) setTemplates(await res.json());
            } catch (err) {
                console.error(err);
            } finally {
                setIsLoading(false);
            }
        };

        if (token) fetchTemplates();
    }, [token]);

    const handleInstall = async (id: string) => {
        setInstalling(id);
        try {
            const res = await fetch(`http://localhost:8001/api/v1/marketplace/install/${id}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                router.push(`/dashboard/agents/${data.agent_id}`);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setInstalling(null);
        }
    };

    const categories = Array.from(new Set(templates.map(t => t.category)));

    const getCategoryIcon = (category: string) => {
        switch (category) {
            case 'Healthcare': return <HeartPulse className="w-6 h-6 text-red-400" />;
            case 'Security': return <Key className="w-6 h-6 text-cyan-400" />;
            case 'Corporate': return <Briefcase className="w-6 h-6 text-orange-400" />;
            case 'Travel': return <Globe className="w-6 h-6 text-emerald-400" />;
            case 'Sales': return <TrendingUp className="w-6 h-6 text-green-400" />;
            case 'Billing': return <Shield className="w-6 h-6 text-blue-400" />;
            case 'Technical': return <Zap className="w-6 h-6 text-yellow-400" />;
            case 'Orchestration': return <Rocket className="w-6 h-6 text-indigo-400" />;
            default: return <Sparkles className="w-6 h-6 text-purple-400" />;
        }
    };

    return (
        <div className="space-y-8 pb-20">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <ShoppingBag className="w-6 h-6 text-pink-500" />
                        Agent Marketplace
                    </h1>
                    <p className="text-gray-400 text-sm">Deploy premium, pre-configured voice agents in one click.</p>
                </div>

                <div className="flex items-center gap-2">
                    <div className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 flex items-center gap-2 text-sm text-gray-400 cursor-pointer hover:bg-white/10 transition-colors">
                        <Filter className="w-4 h-4" />
                        <span>Filter</span>
                    </div>
                    <div className="bg-pink-500/10 border border-pink-500/20 text-pink-400 rounded-lg px-3 py-1.5 flex items-center gap-2 text-sm font-medium">
                        <Sparkles className="w-4 h-4" />
                        <span>Featured</span>
                    </div>
                </div>
            </div>

            {/* Featured Banner */}
            <div className="relative overflow-hidden bg-gradient-to-br from-indigo-600/20 via-purple-600/20 to-pink-600/20 border border-white/10 rounded-3xl p-8 flex flex-col md:flex-row items-center gap-8 shadow-2xl">
                <div className="absolute top-0 right-0 w-64 h-64 bg-pink-500/10 blur-[100px] -z-10" />
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-blue-500/10 blur-[100px] -z-10" />

                <div className="flex-1 space-y-4">
                    <span className="bg-gradient-to-r from-blue-500 to-indigo-500 text-white text-[10px] font-black uppercase px-2 py-1 rounded shadow-lg shadow-blue-500/20">New Arrival</span>
                    <h2 className="text-3xl font-bold text-white">Super-Agent Hub v2</h2>
                    <p className="text-gray-300 max-w-xl leading-relaxed">
                        Our most advanced orchestration system. Uses LangGraph to dynamically route between specialized support, healthcare, and security experts.
                    </p>
                    <button
                        onClick={() => handleInstall('tpl_multi_agent')}
                        className="bg-white text-black px-6 py-2.5 rounded-xl font-bold text-sm hover:translate-y-[-2px] hover:shadow-2xl hover:shadow-white/20 transition-all active:scale-95"
                    >
                        Deploy Hub Now
                    </button>
                </div>
                <div className="relative w-48 h-48 bg-white/5 rounded-full flex items-center justify-center border border-white/10 group backdrop-blur-sm">
                    <div className="absolute inset-0 bg-gradient-to-tr from-pink-500/20 to-blue-500/20 rounded-full animate-pulse" />
                    <Rocket className="w-24 h-24 text-indigo-400 group-hover:scale-110 transition-transform duration-500" />
                </div>
            </div>

            {/* Categorized Grid */}
            {categories.map(category => (
                <div key={category} className="space-y-6">
                    <div className="flex items-center gap-4">
                        <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest">{category}</h3>
                        <div className="h-px flex-1 bg-gradient-to-r from-white/10 to-transparent" />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {templates.filter(t => t.category === category).map(template => (
                            <div key={template.id} className="group relative bg-[#141417]/80 backdrop-blur-md border border-white/10 rounded-2xl overflow-hidden hover:border-pink-500/30 hover:bg-white/5 transition-all duration-300 flex flex-col h-full shadow-lg">
                                <div className="p-6 flex flex-col h-full">
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center border border-white/10 group-hover:bg-white/10 group-hover:scale-110 transition-all duration-300">
                                            {getCategoryIcon(template.category)}
                                        </div>
                                        <div className="flex items-center gap-1 text-[10px] font-black text-yellow-500 bg-yellow-500/10 px-2 py-1 rounded-lg border border-yellow-500/20">
                                            <Star className="w-3 h-3 fill-current" />
                                            {template.rating}
                                        </div>
                                    </div>

                                    <h4 className="text-lg font-bold text-white mb-1 group-hover:text-pink-400 transition-colors">{template.name}</h4>
                                    <p className="text-[10px] font-medium text-gray-500 mb-3 uppercase tracking-wider">{template.role}</p>
                                    <p className="text-sm text-gray-400 mb-6 line-clamp-2 leading-relaxed h-10">
                                        {template.description}
                                    </p>

                                    <div className="mt-auto pt-6 border-t border-white/5 flex items-center justify-between">
                                        <div className="flex -space-x-2">
                                            {template.recommended_tools.slice(0, 3).map((tool, i) => (
                                                <div key={i} className="w-7 h-7 bg-gray-900 border border-white/10 rounded-full flex items-center justify-center text-[10px] text-gray-400 uppercase font-black hover:z-10 transition-all" title={tool}>
                                                    {tool[0]}
                                                </div>
                                            ))}
                                            {template.recommended_tools.length > 3 && (
                                                <div className="w-7 h-7 bg-gray-900 border border-white/10 rounded-full flex items-center justify-center text-[10px] text-gray-500">
                                                    +{template.recommended_tools.length - 3}
                                                </div>
                                            )}
                                        </div>

                                        <button
                                            onClick={() => handleInstall(template.id)}
                                            disabled={installing === template.id}
                                            className="flex items-center gap-2 bg-pink-600 hover:bg-pink-500 disabled:bg-gray-700 text-white px-4 py-2 rounded-xl text-xs font-bold shadow-lg shadow-pink-600/20 active:scale-95 transition-all"
                                        >
                                            {installing === template.id ? (
                                                <div className="flex items-center gap-2">
                                                    <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                                    <span>Installing</span>
                                                </div>
                                            ) : (
                                                <>
                                                    <Download className="w-4 h-4" />
                                                    <span>Deploy Agent</span>
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
