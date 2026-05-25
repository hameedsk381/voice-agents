'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Network, Cpu, Trash2, Plus, X, Search } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface Capability {
    id: string;
    agent_id: string;
    name: string;
    description: string;
    input_schema: Record<string, any>;
    output_schema: Record<string, any>;
    cost_per_call: number;
}

interface RegistryAgent {
    agent_id: string;
    agent_name: string;
    role: string;
    description: string | null;
    capabilities: Capability[];
}

export default function RegistryPage() {
    const [registry, setRegistry] = useState<RegistryAgent[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [selectedAgent, setSelectedAgent] = useState('');
    const [agents, setAgents] = useState<any[]>([]);
    const [capForm, setCapForm] = useState({ name: '', description: '', cost_per_call: 0 });

    const loadRegistry = async () => {
        try {
            const data = await api.get('/agent-registry/registry');
            setRegistry(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const loadAgents = async () => {
        try {
            const data = await api.get('/agents/');
            setAgents(data);
        } catch (err) {
            console.error(err);
        }
    };

    useEffect(() => {
        loadRegistry();
        loadAgents();
    }, []);

    const handleAddCapability = async () => {
        if (!selectedAgent || !capForm.name) return;
        try {
            await api.post('/agent-registry/capabilities', {
                agent_id: selectedAgent,
                ...capForm,
                input_schema: {},
                output_schema: {},
            });
            setShowForm(false);
            setCapForm({ name: '', description: '', cost_per_call: 0 });
            await loadRegistry();
        } catch (err) {
            console.error(err);
        }
    };

    const handleDeleteCapability = async (id: string) => {
        try {
            await api.delete(`/agent-registry/capabilities/${id}`);
            await loadRegistry();
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="space-y-6 pb-10">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                        Agent <span className="text-primary font-semibold">Registry</span>
                    </h2>
                    <p className="text-xs text-muted-foreground mt-1">Registered agents and their discoverable capabilities for multi-agent orchestration.</p>
                </div>
                <Button
                    type="button"
                    onClick={() => setShowForm(!showForm)}
                    className="gap-2"
                >
                    {showForm ? <X className="size-4" /> : <Plus className="size-4" />}
                    {showForm ? 'Cancel' : 'Register Capability'}
                </Button>
            </div>

            {/* Register Capability Form */}
            {showForm && (
                <Card className="hover:shadow-md transition-all animate-in fade-in slide-in-from-top-4 duration-200">
                    <CardHeader>
                        <CardTitle className="text-base">Register Agent Capability</CardTitle>
                        <CardDescription className="text-xs">Expose specific skills or interfaces from your voice agent for automated orchestration.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="space-y-1.5">
                                <Label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Select Agent</Label>
                                <select
                                    value={selectedAgent}
                                    onChange={e => setSelectedAgent(e.target.value)}
                                    className="w-full bg-muted border border-border rounded-xl px-4 py-2.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                                >
                                    <option value="">Select agent...</option>
                                    {agents.map((a: any) => (
                                        <option key={a.id} value={a.id}>{a.name} ({a.role})</option>
                                    ))}
                                </select>
                            </div>
                            <div className="space-y-1.5">
                                <Label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Capability Name</Label>
                                <Input
                                    value={capForm.name}
                                    onChange={e => setCapForm({ ...capForm, name: e.target.value })}
                                    placeholder="e.g. payment-collection"
                                    className="font-mono text-xs bg-muted"
                                />
                            </div>
                            <div className="space-y-1.5">
                                <Label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Cost Per Call ($)</Label>
                                <Input
                                    type="number"
                                    step="0.0001"
                                    value={capForm.cost_per_call}
                                    onChange={e => setCapForm({ ...capForm, cost_per_call: parseFloat(e.target.value) || 0 })}
                                    className="font-mono text-xs bg-muted"
                                />
                            </div>
                        </div>
                        <div className="space-y-1.5">
                            <Label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Description</Label>
                            <Input
                                value={capForm.description}
                                onChange={e => setCapForm({ ...capForm, description: e.target.value })}
                                placeholder="What this capability allows the agent to execute"
                                className="text-xs bg-muted"
                            />
                        </div>
                        <div className="flex justify-end pt-2">
                            <Button
                                type="button"
                                onClick={handleAddCapability}
                                disabled={!selectedAgent || !capForm.name}
                                className="px-6"
                            >
                                Register
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Registry List */}
            {loading ? (
                <div className="space-y-3">
                    {[1, 2].map(i => <div key={i} className="h-24 bg-muted/30 border border-border rounded-xl animate-pulse" />)}
                </div>
            ) : registry.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 bg-muted/40 rounded-2xl border border-dashed border-border">
                    <Network className="size-10 text-muted-foreground mb-3" />
                    <h3 className="text-xs font-semibold text-foreground">No agents registered</h3>
                    <p className="text-[10px] text-muted-foreground mt-1 max-w-xs text-center leading-relaxed">
                        Register capabilities for your agents to enable multi-agent orchestration and task routing.
                    </p>
                </div>
            ) : (
                <div className="space-y-4">
                    {registry.map((entry) => (
                        <Card key={entry.agent_id} className="hover:shadow-md transition-all">
                            <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-4">
                                <div className="flex items-center gap-3">
                                    <div className="size-9 rounded-xl bg-primary/10 flex items-center justify-center text-primary shrink-0">
                                        <Cpu className="size-4" />
                                    </div>
                                    <div>
                                        <CardTitle className="text-sm font-semibold">{entry.agent_name}</CardTitle>
                                        <CardDescription className="text-[10px] mt-0.5">
                                            {entry.role} — {entry.description || 'No description'}
                                        </CardDescription>
                                    </div>
                                </div>
                                <span className="px-2.5 py-0.5 rounded-full bg-primary/10 text-primary text-[9px] font-semibold uppercase border border-primary/20 shrink-0">
                                    {entry.capabilities.length} capabilities
                                </span>
                            </CardHeader>

                            {entry.capabilities.length > 0 && (
                                <CardContent className="pt-0">
                                    <div className="space-y-2 mt-2 pt-3 border-t border-border">
                                        {entry.capabilities.map((cap) => (
                                            <div key={cap.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-xl border border-border">
                                                <div className="flex items-center gap-3 min-w-0">
                                                    <Search className="w-3.5 h-3.5 text-primary shrink-0" />
                                                    <div className="min-w-0">
                                                        <span className="text-xs font-semibold text-foreground font-mono truncate block">{cap.name}</span>
                                                        <p className="text-[9px] text-muted-foreground truncate">{cap.description}</p>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-3 shrink-0 ml-4">
                                                    <span className="text-[9px] text-muted-foreground font-mono">${cap.cost_per_call.toFixed(4)}/call</span>
                                                    <Button
                                                        type="button"
                                                        variant="ghost"
                                                        onClick={() => handleDeleteCapability(cap.id)}
                                                        className="h-8 w-8 p-0 text-red-500 hover:text-red-600 hover:bg-red-500/10"
                                                    >
                                                        <Trash2 className="w-3.5 h-3.5" />
                                                    </Button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            )}
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
