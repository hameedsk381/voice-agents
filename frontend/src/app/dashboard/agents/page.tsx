"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchAgents, createAgent } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Bot, MoreVertical } from "lucide-react";

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
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Agents</h2>
                    <p className="text-gray-400">Manage and orchestrate your voice workforce.</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-md font-medium transition-colors"
                >
                    <Plus className="w-4 h-4" />
                    Create New Agent
                </button>
            </div>

            {loading ? (
                <div className="text-white">Loading agents...</div>
            ) : (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {agents.map((agent) => (
                        <Link href={`/dashboard/agents/${agent.id}`} key={agent.id}>
                            <Card className="group relative overflow-hidden transition-all hover:border-blue-500/50 cursor-pointer">
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-400">
                                            <Bot className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <CardTitle className="text-base font-semibold text-white">{agent.name}</CardTitle>
                                            <p className="text-xs text-gray-500">{agent.role}</p>
                                        </div>
                                    </div>
                                    <button className="text-gray-500 hover:text-white">
                                        <MoreVertical className="w-5 h-5" />
                                    </button>
                                </CardHeader>
                                <CardContent className="mt-4">
                                    <p className="text-sm text-gray-400 line-clamp-3 h-[60px]">
                                        {agent.persona}
                                    </p>
                                    <div className="mt-4 flex items-center gap-2">
                                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${agent.is_active ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-gray-500/10 text-gray-400 border-gray-500/20'}`}>
                                            {agent.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-white/5 text-gray-400 border border-white/10">
                                            {agent.language}
                                        </span>
                                    </div>
                                </CardContent>
                            </Card>
                        </Link>
                    ))}

                    {/* Empty State if no agents */}
                    {agents.length === 0 && (
                        <div className="col-span-full py-12 text-center text-gray-500 border border-dashed border-white/10 rounded-xl">
                            No agents found. Create your first agent to get started.
                        </div>
                    )}
                </div>
            )}

            {/* Simple Modal for MVP (Replace with Dialog component later) */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="w-full max-w-md bg-[#0f0f10] border border-white/10 rounded-xl p-6 shadow-2xl">
                        <h3 className="text-xl font-bold text-white mb-4">Create New Agent</h3>
                        <form onSubmit={handleCreateAgent} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Name</label>
                                <input name="name" required className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-white focus:outline-none focus:border-blue-500" placeholder="e.g. Sales Assistant" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Role</label>
                                <input name="role" required className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-white focus:outline-none focus:border-blue-500" placeholder="e.g. Customer Qualification" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Language</label>
                                <select
                                    name="language"
                                    defaultValue="en-US"
                                    className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-white focus:outline-none focus:border-blue-500 appearance-none shadow-inner"
                                >
                                    <option value="en-US">English (US)</option>
                                    <option value="en-GB">English (UK)</option>
                                    <option value="hi">Hindi (हिन्दी)</option>
                                    <option value="es">Spanish (Español)</option>
                                    <option value="fr">French (Français)</option>
                                    <option value="de">German (Deutsch)</option>
                                    <option value="pt">Portuguese (Português)</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">System Prompt (Persona)</label>
                                <textarea name="persona" required rows={4} className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-white focus:outline-none focus:border-blue-500" placeholder="You are a helpful..."></textarea>
                            </div>
                            <div className="flex justify-end gap-3 mt-6">
                                <button type="button" onClick={() => setIsModalOpen(false)} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancel</button>
                                <button type="submit" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-md text-sm font-medium">Create Agent</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
