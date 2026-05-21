"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchAgents, createAgent } from "@/lib/api";
import { Plus, Bot, MoreVertical, Globe, Settings, ArrowRight } from "lucide-react";

interface Agent {
    id: string;
    name: string;
    role: string;
    persona: string;
    is_active: boolean;
    language: string;
}

export default function AgentsPage() {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        loadAgents();
    }, []);

    const loadAgents = async () => {
        try {
            const data = await fetchAgents();
            setAgents(data);
        } catch (error) {
            console.error("Failed to load agents", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateAgent = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        const form = e.target as HTMLFormElement;
        const formData = new FormData(form);

        const newAgent = {
            name: formData.get('name'),
            role: formData.get('role'),
            persona: formData.get('persona'),
            language: formData.get('language') || 'en-US',
            tools: [],
            goals: []
        };

        try {
            await createAgent(newAgent);
            setIsModalOpen(false);
            loadAgents(); // Reload list
            form.reset();
        } catch (err) {
            console.error(err);
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div className="space-y-6">
            {/* Header section */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                        Voice <span className="text-gradient-brand">Agents</span>
                    </h2>
                    <p className="text-xs text-[var(--text-secondary)] mt-1">Deploy, monitor, and configure your autonomous voice agent workforce.</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="px-4 py-2 text-xs font-semibold rounded-xl bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white hover:shadow-lg hover:shadow-[var(--accent-cyan)]/25 transition-all duration-300 flex items-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    Create New Agent
                </button>
            </div>

            {loading ? (
                <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="glass-card h-44 animate-pulse" />
                    ))}
                </div>
            ) : (
                <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                    {agents.map((agent, index) => {
                        // Different gradient colors based on index for unique look
                        const gradients = [
                            "from-[var(--accent-cyan)] to-[var(--accent-blue)]",
                            "from-[var(--accent-purple)] to-[var(--accent-rose)]",
                            "from-[var(--accent-blue)] to-[var(--accent-purple)]"
                        ];
                        const grad = gradients[index % gradients.length];
                        
                        return (
                            <Link href={`/dashboard/agents/${agent.id}`} key={agent.id} className="group relative block">
                                <div className="glass-card p-5 group flex flex-col justify-between h-full min-h-[180px] transition-all duration-300 hover:border-white/[0.15] hover:shadow-[0_0_25px_rgba(0,212,170,0.04)] relative">
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${grad} flex items-center justify-center text-white shadow-md shadow-black/35`}>
                                                <Bot className="w-4 h-4" />
                                            </div>
                                            <div>
                                                <h3 className="text-sm font-bold text-[var(--text-primary)] tracking-tight truncate max-w-[150px]">
                                                    {agent.name}
                                                </h3>
                                                <p className="text-[10px] text-[var(--text-secondary)] mt-0.5 font-medium truncate max-w-[150px]">
                                                    {agent.role}
                                                </p>
                                            </div>
                                        </div>
                                        <button className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors p-1">
                                            <MoreVertical className="w-4.5 h-4.5" />
                                        </button>
                                    </div>
                                    
                                    <p className="text-xs text-[var(--text-secondary)] mt-4 line-clamp-2 leading-relaxed">
                                        {agent.persona}
                                    </p>

                                    <div className="mt-5 flex items-center justify-between border-t border-[var(--border-subtle)] pt-4">
                                        <div className="flex items-center gap-2">
                                            <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[9px] font-bold uppercase border ${
                                                agent.is_active 
                                                    ? 'bg-[var(--accent-emerald)]/10 text-[var(--accent-emerald)] border-[var(--accent-emerald)]/20' 
                                                    : 'bg-[var(--glass-bg)] text-[var(--text-tertiary)] border-[var(--border-subtle)]'
                                            }`}>
                                                {agent.is_active ? 'Active' : 'Inactive'}
                                            </span>
                                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-semibold bg-[var(--bg-overlay)] text-[var(--text-secondary)] border border-[var(--border-subtle)]">
                                                <Globe className="w-2.5 h-2.5" />
                                                {agent.language}
                                            </span>
                                        </div>
                                        <div className="text-[var(--text-tertiary)] group-hover:text-[var(--text-primary)] transition-all group-hover:translate-x-0.5">
                                            <ArrowRight className="w-3.5 h-3.5" />
                                        </div>
                                    </div>
                                </div>
                            </Link>
                        );
                    })}

                    {/* Empty State */}
                    {agents.length === 0 && (
                        <div className="col-span-full py-16 text-center text-[var(--text-secondary)] border border-dashed border-[var(--border-default)] rounded-2xl bg-[var(--bg-overlay)]">
                            <Bot className="w-8 h-8 mx-auto mb-3 text-[var(--text-tertiary)]" />
                            <p className="text-sm font-semibold">No active agents found</p>
                            <p className="text-xs text-[var(--text-tertiary)] mt-1">Create your first voice agent to start making outbound calls.</p>
                        </div>
                    )}
                </div>
            )}

            {/* Premium Create Agent Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-4 animate-fade">
                    <div className="w-full max-w-md bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-2xl p-6 shadow-2xl relative overflow-hidden">
                        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)]" />
                        
                        <h3 className="text-base font-bold text-[var(--text-primary)] mb-4">Create Voice Agent</h3>
                        
                        <form onSubmit={handleCreateAgent} className="space-y-4">
                            <div>
                                <label className="block text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Agent Name</label>
                                <input 
                                    name="name" 
                                    required 
                                    className="w-full bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl px-3 py-2.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent-cyan)] focus:ring-4 focus:ring-[var(--accent-cyan)]/5 transition-all" 
                                    placeholder="e.g. Inbound Sales Assistant" 
                                />
                            </div>
                            
                            <div>
                                <label className="block text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Primary Role</label>
                                <input 
                                    name="role" 
                                    required 
                                    className="w-full bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl px-3 py-2.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent-cyan)] focus:ring-4 focus:ring-[var(--accent-cyan)]/5 transition-all" 
                                    placeholder="e.g. Lead Qualification" 
                                />
                            </div>
                            
                            <div>
                                <label className="block text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Language Profile</label>
                                <select
                                    name="language"
                                    defaultValue="en-US"
                                    className="w-full bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl px-3 py-2.5 text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-cyan)] transition-all select-none cursor-pointer"
                                >
                                    <option value="en-US" className="bg-[var(--bg-surface)]">English (US)</option>
                                    <option value="en-GB" className="bg-[var(--bg-surface)]">English (UK)</option>
                                    <option value="hi" className="bg-[var(--bg-surface)]">Hindi (हिन्दी)</option>
                                    <option value="es" className="bg-[var(--bg-surface)]">Spanish (Español)</option>
                                    <option value="fr" className="bg-[var(--bg-surface)]">French (Français)</option>
                                    <option value="de" className="bg-[var(--bg-surface)]">German (Deutsch)</option>
                                    <option value="pt" className="bg-[var(--bg-surface)]">Portuguese (Português)</option>
                                </select>
                            </div>
                            
                            <div>
                                <label className="block text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">System Persona (Instructions)</label>
                                <textarea 
                                    name="persona" 
                                    required 
                                    rows={4} 
                                    className="w-full bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl px-3 py-2.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent-cyan)] focus:ring-4 focus:ring-[var(--accent-cyan)]/5 transition-all resize-none" 
                                    placeholder="Define the behavior constraints and goals of the voice bot..."
                                />
                            </div>
                            
                            <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-[var(--border-subtle)]">
                                <button 
                                    type="button" 
                                    onClick={() => setIsModalOpen(false)} 
                                    className="px-4 py-2.5 text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                                >
                                    Cancel
                                </button>
                                <button 
                                    type="submit" 
                                    disabled={submitting}
                                    className="px-4 py-2.5 bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50 flex items-center gap-2 hover:-translate-y-0.5 active:translate-y-0 active:scale-98"
                                >
                                    {submitting ? 'Creating...' : 'Deploy Agent'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
