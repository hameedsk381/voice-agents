'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { ArrowLeft, Save, Settings, Trash2, HelpCircle } from 'lucide-react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function NewCampaignPage() {
    const router = useRouter();

    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [agentId, setAgentId] = useState('');
    const [agents, setAgents] = useState<any[]>([]);
    const [concurrency, setConcurrency] = useState(1);
    const [greeting, setGreeting] = useState('');
    const [workflowId, setWorkflowId] = useState('');
    const [workflows, setWorkflows] = useState<{ id: string; name: string }[]>([]);

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAgents = async () => {
            try {
                const data = await api.get("/agents/");
                setAgents(data);
                if (data.length > 0) setAgentId(data[0].id);
            } catch (err) {
                console.error(err);
            }
        };
        fetchAgents();
        api.get('/workflows/active').then(setWorkflows).catch(() => {});
    }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            const data = await api.post("/campaigns/", {
                name,
                description,
                agent_id: agentId,
                concurrency_limit: concurrency,
                greeting: greeting.trim() || undefined,
                workflow_id: workflowId || undefined,
            });
            router.push(`/dashboard/campaigns/${data.id}?new=true`);
        } catch (err: any) {
            setError(err.message || 'System error. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-6 pb-12">
            <div className="flex items-center gap-4">
                <Link href="/dashboard/campaigns" className="p-2 rounded-lg bg-muted hover:bg-muted/70 text-muted-foreground transition-colors">
                    <ArrowLeft className="size-5" />
                </Link>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-foreground">Create New Campaign</h1>
                    <p className="text-xs text-muted-foreground mt-1">Configure your automated outbound dialing strategy.</p>
                </div>
            </div>

            <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Main Config */}
                <div className="md:col-span-2 space-y-6">
                    <Card className="hover:shadow-md transition-all">
                        <CardHeader>
                            <CardTitle className="text-base">Campaign Details</CardTitle>
                            <CardDescription className="text-xs">Provide a primary name and metadata for tracking this campaign.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="campaign-name" className="text-xs font-semibold text-muted-foreground">Campaign Name</Label>
                                <Input
                                    id="campaign-name"
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="E.g. Q1 Product Feedback"
                                    className="text-xs bg-muted/30"
                                    required
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="campaign-description" className="text-xs font-semibold text-muted-foreground">Description (Optional)</Label>
                                <textarea
                                    id="campaign-description"
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    placeholder="Describe the purpose of this campaign..."
                                    className="w-full bg-muted/30 border border-border rounded-xl px-4 py-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary transition-all h-28"
                                />
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="hover:shadow-md transition-all">
                        <CardHeader>
                            <CardTitle className="text-base flex items-center gap-2">
                                <Settings className="size-4 text-primary" />
                                Dialing Strategy & Logic
                            </CardTitle>
                            <CardDescription className="text-xs">Configure the underlying voice agent greeting and parallel line handling.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-5">
                            <div className="space-y-2">
                                <Label htmlFor="campaign-greeting" className="text-xs font-semibold text-muted-foreground">Opening Greeting (Optional)</Label>
                                <Input
                                    id="campaign-greeting"
                                    type="text"
                                    value={greeting}
                                    onChange={(e) => setGreeting(e.target.value)}
                                    placeholder="Hi, this is your team calling about your appointment…"
                                    className="text-xs bg-muted/30"
                                />
                                <p className="text-[10px] text-muted-foreground">Overrides the agent’s default greeting for everyone in this campaign.</p>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label className="text-xs font-semibold text-muted-foreground">Assign AI Agent</Label>
                                    <select
                                        value={agentId}
                                        onChange={(e) => setAgentId(e.target.value)}
                                        className="w-full bg-muted/30 border border-border rounded-xl px-4 py-2.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary transition-all"
                                        required
                                    >
                                        {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                                    </select>
                                </div>

                                <div className="space-y-2">
                                    <Label className="text-xs font-semibold text-muted-foreground">Concurrency Limit</Label>
                                    <Input
                                        type="number"
                                        min="1"
                                        max="50"
                                        value={concurrency}
                                        onChange={(e) => setConcurrency(parseInt(e.target.value) || 1)}
                                        className="text-xs bg-muted/30 font-mono"
                                    />
                                </div>

                                <div className="space-y-2 sm:col-span-2">
                                    <Label className="text-xs font-semibold text-muted-foreground">Workflow Automation (Optional)</Label>
                                    <select
                                        value={workflowId}
                                        onChange={(e) => setWorkflowId(e.target.value)}
                                        className="w-full bg-muted/30 border border-border rounded-xl px-4 py-2.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                                    >
                                        <option value="">None — calls only</option>
                                        {workflows.map((w) => (
                                            <option key={w.id} value={w.id}>{w.name}</option>
                                        ))}
                                    </select>
                                    <p className="text-[10px] text-muted-foreground mt-1">
                                        Published workflows run per contact when you start the campaign (call → retry → email → escalate).
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Sidebar Info */}
                <div className="space-y-6">
                    <Card className="bg-primary/5 border border-primary/10 hover:shadow-sm transition-all">
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-semibold text-primary flex items-center gap-1.5">
                                <HelpCircle className="size-4 text-primary" />
                                Execution Flow
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ul className="text-xs text-muted-foreground space-y-3.5 list-none pl-0">
                                <li className="flex gap-2">
                                    <span className="text-primary font-bold">1.</span>
                                    Setup campaign config and assign a voice agent.
                                </li>
                                <li className="flex gap-2">
                                    <span className="text-primary font-bold">2.</span>
                                    Upload your contact list (.csv).
                                </li>
                                <li className="flex gap-2">
                                    <span className="text-primary font-bold">3.</span>
                                    Start the campaign and watch live results & transcripts.
                                </li>
                            </ul>
                        </CardContent>
                    </Card>

                    <Button
                        type="submit"
                        disabled={isLoading}
                        className="w-full h-12 text-sm font-semibold rounded-2xl gap-2 shadow-lg shadow-primary/15"
                    >
                        {isLoading ? 'Creating...' : (
                            <>
                                <Save className="size-4" />
                                Create Campaign
                            </>
                        )}
                    </Button>

                    {error && (
                        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-500 text-xs flex items-center gap-2 animate-in fade-in duration-200">
                            <Trash2 className="size-4 shrink-0 text-red-500" />
                            <span>{error}</span>
                        </div>
                    )}
                </div>
            </form>
        </div>
    );
}
