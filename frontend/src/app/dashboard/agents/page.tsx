"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api, { fetchAgents, createAgent } from "@/lib/api";
import { LANGUAGES, defaultLanguage, languageDisplay } from "@/lib/languages";
import { Plus, Bot, MoreVertical, Globe, ArrowRight, Loader2, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Agent {
    id: string;
    name: string;
    role: string;
    persona: string;
    is_active: boolean;
    language: string;
}

interface Voice {
    id: string;
    name: string;
    type: string;
    primaryLanguage: string;
}

export default function AgentsPage() {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [voices, setVoices] = useState<Voice[]>([]);
    const [selectedVoice, setSelectedVoice] = useState("auto");
    const [createLang, setCreateLang] = useState(defaultLanguage());

    useEffect(() => {
        loadAgents();
    }, []);

    useEffect(() => {
        if (isModalOpen) {
            const fetchVoices = async () => {
                try {
                    const data = await api.get(`/voices/?primaryLanguage=${encodeURIComponent(createLang)}`);
                    setVoices(data);
                } catch {
                    setVoices([]);
                }
            };
            fetchVoices();
            setSelectedVoice("auto");
        }
    }, [createLang, isModalOpen]);

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

    const openCreateModal = async () => {
        setIsModalOpen(true);
        setSelectedVoice("auto");
        setCreateLang(defaultLanguage());
        try {
            const data = await api.get(`/voices/?primaryLanguage=${encodeURIComponent(defaultLanguage())}`);
            setVoices(data);
        } catch {
            setVoices([]);
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
            language: formData.get('language') || defaultLanguage(),
            tools: [],
            goals: [],
            config: { voice: selectedVoice !== 'auto' ? selectedVoice : undefined }
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
                    <h2 className="text-2xl font-semibold tracking-tight text-foreground">
                        Voice{" "}
                        <span className="text-primary">
                            Agents
                        </span>
                    </h2>
                    <p className="text-sm text-muted-foreground mt-1">
                        Deploy, monitor, and configure your autonomous voice agent workforce.
                    </p>
                </div>
                <Button
                    onClick={openCreateModal}
                    className="flex items-center gap-2"
                >
                    <Plus className="size-4" />
                    Create New Agent
                </Button>
            </div>

            {loading ? (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {[1, 2, 3].map((i) => (
                        <Card key={i} className="h-44 animate-pulse" />
                    ))}
                </div>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {agents.map((agent) => (
                        <Link href={`/dashboard/agents/${agent.id}`} key={agent.id} className="group block">
                            <Card className="flex flex-col justify-between h-full min-h-[180px] hover:shadow-md transition-all hover:border-primary/50">
                                <CardHeader>
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="size-10 rounded-lg bg-primary flex items-center justify-center">
                                                <Bot className="size-5 text-white" />
                                            </div>
                                            <div>
                                                <CardTitle className="text-sm font-semibold tracking-tight truncate max-w-[150px]">
                                                    {agent.name}
                                                </CardTitle>
                                                <CardDescription className="text-xs mt-0.5 truncate max-w-[150px]">
                                                    {agent.role}
                                                </CardDescription>
                                            </div>
                                        </div>
                                        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground">
                                            <MoreVertical className="size-4" />
                                        </Button>
                                    </div>
                                </CardHeader>

                                <CardContent>
                                    <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                                        {agent.persona}
                                    </p>
                                </CardContent>

                                <CardFooter className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                            agent.is_active
                                                ? 'bg-green-500/10 text-green-600'
                                                : 'bg-muted text-muted-foreground'
                                        }`}>
                                            {agent.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                        <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium bg-primary/10 text-primary">
                                            <Globe className="size-3" />
                                            {agent.language}
                                        </span>
                                    </div>
                                    <div className="text-muted-foreground group-hover:text-primary transition-all group-hover:translate-x-0.5">
                                        <ArrowRight className="size-4" />
                                    </div>
                                </CardFooter>
                            </Card>
                        </Link>
                    ))}

                    {/* Empty State */}
                    {agents.length === 0 && (
                        <Card className="col-span-full border-dashed">
                            <CardContent className="py-16 text-center">
                                <div className="size-12 rounded-lg bg-primary/10 flex items-center justify-center mx-auto mb-4">
                                    <Bot className="size-6 text-primary" />
                                </div>
                                <p className="text-sm font-semibold text-foreground">No active agents found</p>
                                <p className="text-xs text-muted-foreground mt-1">
                                    Create your first voice agent to start making outbound calls.
                                </p>
                                <Button
                                    onClick={openCreateModal}
                                    className="mt-4"
                                    size="sm"
                                >
                                    <Plus className="size-4 mr-2" />
                                    Create Agent
                                </Button>
                            </CardContent>
                        </Card>
                    )}
                </div>
            )}

            {/* Create Agent Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
                    <Card className="w-full max-w-md shadow-2xl">
                        <CardHeader>
                            <div className="flex items-center gap-3">
                                <div className="size-10 rounded-lg bg-primary flex items-center justify-center">
                                    <Sparkles className="size-5 text-white" />
                                </div>
                                <div>
                                    <CardTitle className="text-base font-semibold">Create Voice Agent</CardTitle>
                                    <CardDescription className="text-xs">
                                        Configure a new autonomous voice agent for your workflow.
                                    </CardDescription>
                                </div>
                            </div>
                        </CardHeader>

                        <form onSubmit={handleCreateAgent}>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="agent-name" className="text-xs font-semibold uppercase tracking-wider">
                                        Agent Name
                                    </Label>
                                    <Input
                                        id="agent-name"
                                        name="name"
                                        required
                                        placeholder="e.g. Inbound Sales Assistant"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="agent-role" className="text-xs font-semibold uppercase tracking-wider">
                                        Primary Role
                                    </Label>
                                    <Input
                                        id="agent-role"
                                        name="role"
                                        required
                                        placeholder="e.g. Lead Qualification"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="agent-language" className="text-xs font-semibold uppercase tracking-wider">
                                        Language Profile
                                    </Label>
                                    <select
                                        id="agent-language"
                                        name="language"
                                        value={createLang}
                                        onChange={e => setCreateLang(e.target.value)}
                                        className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                                    >
                                        {LANGUAGES.map(l => (
                                        <option key={l.code} value={l.code}>
                                            {languageDisplay(l.code)}
                                        </option>
                                    ))}
                                    </select>
                                </div>

                                <div className="space-y-2">
                                    <Label className="text-xs font-semibold uppercase tracking-wider">Voice</Label>
                                    <select
                                        value={selectedVoice}
                                        onChange={e => setSelectedVoice(e.target.value)}
                                        className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                                    >
                                        <option value="auto">Auto-Select</option>
                                        {voices.map(v => (
                                            <option key={v.id} value={v.id}>{v.name} ({v.type})</option>
                                        ))}
                                    </select>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="agent-persona" className="text-xs font-semibold uppercase tracking-wider">
                                        System Persona (Instructions)
                                    </Label>
                                    <textarea
                                        id="agent-persona"
                                        name="persona"
                                        required
                                        rows={4}
                                        className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
                                        placeholder="Define the behavior constraints and goals of the voice bot..."
                                    />
                                </div>
                            </CardContent>

                            <CardFooter className="flex justify-end gap-3">
                                <Button
                                    type="button"
                                    variant="ghost"
                                    onClick={() => setIsModalOpen(false)}
                                >
                                    Cancel
                                </Button>
                                <Button
                                    type="submit"
                                    disabled={submitting}
                                    className="flex items-center gap-2"
                                >
                                    {submitting ? (
                                        <>
                                            <Loader2 className="size-4 animate-spin" />
                                            Creating...
                                        </>
                                    ) : (
                                        'Deploy Agent'
                                    )}
                                </Button>
                            </CardFooter>
                        </form>
                    </Card>
                </div>
            )}
        </div>
    );
}
