'use client';

import { useState, useEffect, useMemo } from 'react';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';
import {
    ShoppingBag, Star, Download, Shield,
    Zap, TrendingUp, Filter, Sparkles,
    HeartPulse, Globe, Briefcase, Key, Rocket,
    Search, Phone, Users, HeadphonesIcon,
    AlertCircle,
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

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
    'Outbound Collections': <Phone className="size-5 text-red-500" />,
    'Outbound Sales': <TrendingUp className="size-5 text-green-600" />,
    'Healthcare & Services': <HeartPulse className="size-5 text-red-500" />,
    Customer: <HeadphonesIcon className="size-5 text-primary" />,
    Security: <Key className="size-5 text-primary" />,
    Corporate: <Briefcase className="size-5 text-amber-500" />,
    Travel: <Globe className="size-5 text-green-600" />,
    Technical: <Zap className="size-5 text-amber-500" />,
    'Outbound CX': <Users className="size-5 text-blue-500" />,
};

const getCategoryIcon = (category: string) => {
    for (const [key, icon] of Object.entries(CATEGORY_ICONS)) {
        if (category.toLowerCase().includes(key.toLowerCase())) return icon;
    }
    return <Sparkles className="size-5 text-primary" />;
};

const ALL_CATEGORIES = [
    'Outbound Collections', 'Outbound Sales', 'Healthcare & Services',
    'Customer Support', 'Security', 'Corporate', 'Travel',
    'Technical', 'Outbound CX',
];

export default function MarketplacePage() {
    const router = useRouter();
    const [templates, setTemplates] = useState<Template[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [installing, setInstalling] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [categoryFilter, setCategoryFilter] = useState<string>('All');
    const [showFilterDropdown, setShowFilterDropdown] = useState(false);

    useEffect(() => {
        const fetchTemplates = async () => {
            try {
                setError(null);
                const data = await api.get('/marketplace/templates');
                setTemplates(data);
            } catch (err) {
                console.error(err);
                setError('Failed to load marketplace templates. Please try again.');
            } finally {
                setIsLoading(false);
            }
        };

        fetchTemplates();
    }, []);

    const filteredTemplates = useMemo(() => {
        return templates.filter(t => {
            const matchesSearch = !searchQuery ||
                t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                t.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                t.category.toLowerCase().includes(searchQuery.toLowerCase());
            const matchesCategory = categoryFilter === 'All' || t.category === categoryFilter;
            return matchesSearch && matchesCategory;
        });
    }, [templates, searchQuery, categoryFilter]);

    const categories = useMemo(
        () => Array.from(new Set(templates.map(t => t.category))),
        [templates],
    );

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

    const formatCategoryLabel = (category: string) => {
        const labels: Record<string, string> = {
            Orchestration: 'Workflow packs',
            Technical: 'Specialized',
        };
        return labels[category] || category;
    };

    if (isLoading) {
        return (
            <div className="space-y-6">
                <div className="bg-card border text-card-foreground shadow-sm rounded-xl h-52 animate-pulse" />
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="bg-card border text-card-foreground shadow-sm rounded-xl h-64 animate-pulse" />
                    ))}
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center py-20 gap-4">
                <AlertCircle className="size-12 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">{error}</p>
                <button
                    type="button"
                    onClick={() => { setIsLoading(true); setError(null); window.location.reload(); }}
                    className="bg-primary text-white px-4 py-2 rounded-xl text-xs font-semibold"
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-6 pb-20">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
                        Agent <span className="text-primary">Marketplace</span>
                    </h2>
                    <p className="text-xs text-muted-foreground mt-1">
                        Deploy pre-configured voice agents in one click.
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    {/* Search */}
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
                        <input
                            type="text"
                            placeholder="Search templates..."
                            value={searchQuery}
                            onChange={e => setSearchQuery(e.target.value)}
                            className="bg-muted border border-border rounded-xl pl-9 pr-3 py-1.5 text-xs w-48 focus:outline-none focus:ring-1 focus:ring-primary/30"
                        />
                    </div>

                    {/* Category filter */}
                    <div className="relative">
                        <button
                            type="button"
                            onClick={() => setShowFilterDropdown(!showFilterDropdown)}
                            className="bg-muted border border-border hover:bg-muted rounded-xl px-3.5 py-1.5 flex items-center gap-2 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors"
                        >
                            <Filter className="w-3.5 h-3.5" />
                            <span>{categoryFilter}</span>
                        </button>
                        {showFilterDropdown && (
                            <>
                                <div className="fixed inset-0 z-10" onClick={() => setShowFilterDropdown(false)} />
                                <div className="absolute right-0 top-full mt-1 z-20 bg-popover border border-border rounded-xl shadow-lg py-1 min-w-44">
                                    <button
                                        type="button"
                                        onClick={() => { setCategoryFilter('All'); setShowFilterDropdown(false); }}
                                        className={`w-full text-left px-3.5 py-1.5 text-xs ${categoryFilter === 'All' ? 'bg-primary/10 text-primary font-semibold' : 'text-muted-foreground hover:text-foreground'}`}
                                    >
                                        All Categories
                                    </button>
                                    {ALL_CATEGORIES.map(cat => (
                                        <button
                                            key={cat}
                                            type="button"
                                            onClick={() => { setCategoryFilter(cat); setShowFilterDropdown(false); }}
                                            className={`w-full text-left px-3.5 py-1.5 text-xs ${categoryFilter === cat ? 'bg-primary/10 text-primary font-semibold' : 'text-muted-foreground hover:text-foreground'}`}
                                        >
                                            {cat}
                                        </button>
                                    ))}
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>

            {/* Featured Banner */}
            {templates.length > 0 && (
                <div className="relative overflow-hidden bg-muted/50 border border-border rounded-2xl p-6 md:p-8 flex flex-col md:flex-row items-center gap-6 shadow-2xl relative">
                    <div className="absolute top-0 right-0 size-64 bg-pink-500/10 blur-[100px] pointer-events-none -z-10" />
                    <div className="absolute bottom-0 left-0 size-64 bg-blue-500/10 blur-[100px] pointer-events-none -z-10" />

                    <div className="flex-1 space-y-4">
                        <span className="bg-primary text-white text-[9px] font-black uppercase px-2.5 py-1 rounded shadow-md tracking-wider">
                            Most Popular
                        </span>
                        <h2 className="text-2xl md:text-3xl font-extrabold text-foreground">
                            {templates.reduce((a, b) => (a.popularity > b.popularity ? a : b)).name}
                        </h2>
                        <p className="text-xs text-muted-foreground max-w-xl leading-relaxed">
                            {templates.reduce((a, b) => (a.popularity > b.popularity ? a : b)).description}
                        </p>
                        <button
                            type="button"
                            onClick={() => handleInstall(templates.reduce((a, b) => (a.popularity > b.popularity ? a : b)).id)}
                            className="bg-white text-black px-5 py-2.5 rounded-xl font-bold text-xs hover:-translate-y-0.5 hover:shadow-lg transition-all active:scale-98"
                        >
                            {installing === templates.reduce((a, b) => (a.popularity > b.popularity ? a : b)).id ? (
                                <div className="flex items-center gap-2">
                                    <div className="size-3 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                                    <span>Installing</span>
                                </div>
                            ) : (
                                'Deploy Now'
                            )}
                        </button>
                    </div>
                    <div className="relative size-40 bg-muted rounded-full flex items-center justify-center border border-border group backdrop-blur-sm shrink-0">
                        <Rocket className="size-16 text-primary group-hover:scale-110 transition-transform duration-500" />
                    </div>
                </div>
            )}

            {/* No results */}
            {filteredTemplates.length === 0 && !isLoading && (
                <div className="flex flex-col items-center justify-center py-16 gap-3">
                    <ShoppingBag className="size-10 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                        {searchQuery || categoryFilter !== 'All'
                            ? 'No templates match your filters.'
                            : 'No templates available yet.'}
                    </p>
                </div>
            )}

            {/* Categorized Grid */}
            {categories.map(category => {
                const catTemplates = filteredTemplates.filter(t => t.category === category);
                if (catTemplates.length === 0) return null;
                return (
                    <div key={category} className="space-y-4 pt-4">
                        <div className="flex items-center gap-4">
                            <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-widest">
                                {formatCategoryLabel(category)}
                            </h3>
                            <div className="h-[1px] flex-1 bg-white/[0.06]" />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                            {catTemplates.map(template => (
                                <div
                                    key={template.id}
                                    className="group relative bg-card border text-card-foreground shadow-sm rounded-xl overflow-hidden hover:border-[var(--border-active)] transition-all flex flex-col h-full"
                                >
                                    <div className="p-5 flex flex-col h-full">
                                        <div className="flex justify-between items-start mb-4">
                                            <div className="size-10 bg-muted rounded-xl flex items-center justify-center border border-border group-hover:scale-105 transition-all">
                                                {getCategoryIcon(template.category)}
                                            </div>
                                            <div className="flex items-center gap-1 text-[9px] font-black text-yellow-500 bg-yellow-500/10 px-2 py-0.5 rounded-full border border-yellow-500/20">
                                                <Star className="size-3 fill-current" />
                                                {template.rating}
                                            </div>
                                        </div>

                                        <h4 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                                            {template.name}
                                        </h4>
                                        <p className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider mt-0.5">
                                            {template.role}
                                        </p>

                                        <p className="text-xs text-muted-foreground mt-3 mb-6 line-clamp-2 leading-relaxed h-8">
                                            {template.description}
                                        </p>

                                        <div className="mt-auto pt-4 border-t border-border flex items-center justify-between">
                                            <div className="flex -space-x-1.5">
                                                {template.recommended_tools.slice(0, 3).map((tool, i) => (
                                                    <div
                                                        key={i}
                                                        className="w-6.5 h-6.5 bg-muted border border-border rounded-full flex items-center justify-center text-[9px] text-muted-foreground uppercase font-black hover:z-10 transition-all select-none"
                                                        title={tool}
                                                    >
                                                        {tool[0]}
                                                    </div>
                                                ))}
                                                {template.recommended_tools.length > 3 && (
                                                    <div className="w-6.5 h-6.5 bg-muted border border-border rounded-full flex items-center justify-center text-[9px] text-muted-foreground font-semibold">
                                                        +{template.recommended_tools.length - 3}
                                                    </div>
                                                )}
                                            </div>

                                            <button
                                                type="button"
                                                onClick={() => handleInstall(template.id)}
                                                disabled={installing === template.id}
                                                className="flex items-center gap-2 bg-primary text-white px-3.5 py-2 rounded-xl text-xs font-semibold transition-all disabled:opacity-50 hover:-translate-y-0.5 active:translate-y-0 active:scale-98"
                                            >
                                                {installing === template.id ? (
                                                    <div className="flex items-center gap-2">
                                                        <div className="size-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
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
                );
            })}
        </div>
    );
}
