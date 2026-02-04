'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import {
    ShoppingBag, Star, Download, Shield,
    Zap, Headphones, TrendingUp, Filter, Sparkles
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
                    <div className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 flex items-center gap-2 text-sm text-gray-400">
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
            <div className="relative overflow-hidden bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-white/10 rounded-3xl p-8 flex flex-col md:flex-row items-center gap-8">
                <div className="flex-1 space-y-4">
                    <span className="bg-blue-500 text-white text-[10px] font-black uppercase px-2 py-1 rounded">New Arrival</span>
                    <h2 className="text-3xl font-bold text-white">OmniSupport Pro v4</h2>
                    <p className="text-gray-300 max-w-xl">
                        Our most advanced customer support agent ever. Built-in RAG capabilities, high emotional intelligence, and seamless CRM integration.
                    </p>
                    <button
                        onClick={() => handleInstall('tpl_support_pro')}
                        className="bg-white text-black px-6 py-2.5 rounded-xl font-bold text-sm hover:scale-105 transition-all shadow-xl shadow-white/10"
                    >
                        Install Featured Agent
                    </button>
                </div>
                <div className="w-40 h-40 bg-white/5 rounded-full flex items-center justify-center border border-white/10 animate-pulse">
                    <Headphones className="w-20 h-20 text-blue-400" />
                </div>
            </div>

            {/* Categorized Grid */}
            {categories.map(category => (
                <div key={category} className="space-y-4">
                    <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest">{category} Agents</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
                        {templates.filter(t => t.category === category).map(template => (
                            <div key={template.id} className="group relative bg-[#141417] border border-white/10 rounded-2xl overflow-hidden hover:border-pink-500/30 transition-all duration-300">
                                <div className="p-6">
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center border border-white/10 group-hover:bg-pink-500/10 group-hover:border-pink-500/20 transition-all">
                                            {template.category === 'Sales' ? <TrendingUp className="w-6 h-6 text-green-400" /> :
                                                template.category === 'Billing' ? <Shield className="w-6 h-6 text-blue-400" /> :
                                                    template.category === 'Technical' ? <Zap className="w-6 h-6 text-yellow-400" /> :
                                                        <Sparkles className="w-6 h-6 text-purple-400" />}
                                        </div>
                                        <div className="flex items-center gap-1 text-xs font-bold text-yellow-500 bg-yellow-500/10 px-2 py-1 rounded">
                                            <Star className="w-3 h-3 fill-current" />
                                            {template.rating}
                                        </div>
                                    </div>

                                    <h4 className="text-xl font-bold text-white mb-1">{template.name}</h4>
                                    <p className="text-xs text-gray-500 mb-4">{template.role}</p>
                                    <p className="text-sm text-gray-400 mb-6 line-clamp-2">
                                        {template.description}
                                    </p>

                                    <div className="flex items-center justify-between mt-auto">
                                        <div className="flex -space-x-2">
                                            {template.recommended_tools.slice(0, 3).map((tool, i) => (
                                                <div key={i} className="w-7 h-7 bg-[#1c1c21] border border-white/10 rounded-full flex items-center justify-center text-[10px] text-gray-400 uppercase font-black" title={tool}>
                                                    {tool[0]}
                                                </div>
                                            ))}
                                            {template.recommended_tools.length > 3 && (
                                                <div className="w-7 h-7 bg-[#1c1c21] border border-white/10 rounded-full flex items-center justify-center text-[10px] text-gray-500">
                                                    +{template.recommended_tools.length - 3}
                                                </div>
                                            )}
                                        </div>

                                        <button
                                            onClick={() => handleInstall(template.id)}
                                            disabled={installing === template.id}
                                            className="flex items-center gap-2 bg-pink-600 hover:bg-pink-500 disabled:bg-gray-700 text-white px-4 py-2 rounded-xl text-sm font-bold transition-all"
                                        >
                                            {installing === template.id ? 'Installing...' : (
                                                <>
                                                    <Download className="w-4 h-4" />
                                                    Use Template
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
