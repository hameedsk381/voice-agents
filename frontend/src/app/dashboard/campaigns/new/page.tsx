'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { ArrowLeft, Save, Users, Settings, Phone, Upload, X, Trash2 } from 'lucide-react';
import Link from 'next/link';

export default function NewCampaignPage() {
    const router = useRouter();
    const { token } = useAuth();

    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [agentId, setAgentId] = useState('');
    const [agents, setAgents] = useState<any[]>([]);
    const [concurrency, setConcurrency] = useState(1);

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAgents = async () => {
            try {
                const res = await fetch('http://localhost:8001/api/v1/agents/', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    setAgents(data);
                    if (data.length > 0) setAgentId(data[0].id);
                }
            } catch (err) {
                console.error(err);
            }
        };
        fetchAgents();
    }, [token]);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            const res = await fetch('http://localhost:8001/api/v1/campaigns/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    name,
                    description,
                    agent_id: agentId,
                    concurrency_limit: concurrency
                })
            });

            if (res.ok) {
                const data = await res.json();
                router.push(`/dashboard/campaigns/${data.id}?new=true`);
            } else {
                const err = await res.json();
                setError(err.detail || 'Failed to create campaign');
            }
        } catch (err) {
            setError('System error. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center gap-4">
                <Link href="/dashboard/campaigns" className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 transition-colors">
                    <ArrowLeft className="w-5 h-5" />
                </Link>
                <div>
                    <h1 className="text-2xl font-bold text-white">Create New Campaign</h1>
                    <p className="text-gray-400">Configure your automated outbound dialing strategy.</p>
                </div>
            </div>

            <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Main Config */}
                <div className="md:col-span-2 space-y-6">
                    <div className="bg-[#141417] border border-white/10 rounded-2xl p-6 space-y-6">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-400">Campaign Name</label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="E.g. Q1 Product Feedback"
                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-400">Description (Optional)</label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Describe the purpose of this campaign..."
                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-gray-600 focus:outline-none focus:border-blue-500 transition-colors h-32"
                            />
                        </div>
                    </div>

                    <div className="bg-[#141417] border border-white/10 rounded-2xl p-6 space-y-6">
                        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                            <Settings className="w-5 h-5 text-blue-500" />
                            Dialing Strategy
                        </h3>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-gray-400">Assign AI Agent</label>
                                <select
                                    value={agentId}
                                    onChange={(e) => setAgentId(e.target.value)}
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-colors appearance-none"
                                    required
                                >
                                    {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                                </select>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium text-gray-400">Concurrency Limit</label>
                                <input
                                    type="number"
                                    min="1"
                                    max="50"
                                    value={concurrency}
                                    onChange={(e) => setConcurrency(parseInt(e.target.value))}
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-colors"
                                />
                                <p className="text-[10px] text-gray-500">Max parallel calls allowed.</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Sidebar Info */}
                <div className="space-y-6">
                    <div className="bg-blue-500/10 border border-blue-500/20 rounded-2xl p-6">
                        <h3 className="text-blue-400 font-semibold mb-2">How it works</h3>
                        <ul className="text-sm text-gray-400 space-y-3">
                            <li className="flex gap-2">
                                <span className="text-blue-500 font-bold">1.</span>
                                Setup campaign config and assign an agent.
                            </li>
                            <li className="flex gap-2">
                                <span className="text-blue-500 font-bold">2.</span>
                                Upload your contact list (CSV).
                            </li>
                            <li className="flex gap-2">
                                <span className="text-blue-500 font-bold">3.</span>
                                Start the campaign and watch live results.
                            </li>
                        </ul>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full py-4 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-white font-bold rounded-2xl transition-all shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2"
                    >
                        {isLoading ? 'Creating...' : (
                            <>
                                <Save className="w-5 h-5" />
                                Create Campaign
                            </>
                        )}
                    </button>

                    {error && (
                        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs flex items-center gap-2">
                            <Trash2 className="w-4 h-4" />
                            {error}
                        </div>
                    )}
                </div>
            </form>
        </div>
    );
}
