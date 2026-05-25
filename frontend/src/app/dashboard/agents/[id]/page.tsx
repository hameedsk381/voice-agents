"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import api from "@/lib/api";
import { LANGUAGES, languageDisplay } from "@/lib/languages";
import { useUltravoxSession } from "@/hooks/useUltravoxSession";
import { PERSONALIZATION_FIELDS, personalizationToken } from "@/lib/product-copy";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ArrowLeft, Save, Play, Mic, Square, Trash2, Sliders, Activity, History, Shield, Globe, Volume2, Book, FileText, Plus, Search, Bot, Phone, PhoneOff, MicOff, CheckCircle, XCircle, AlertTriangle, Clock, DollarSign, BarChart3, RotateCcw, Tag, Eye, EyeOff, RefreshCw, ChevronDown, ChevronUp, TrendingUp } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface Agent {
    id: string;
    name: string;
    role: string;
    persona: string;
    language: string;
    is_active: boolean;
    description?: string;
    goals?: string[];
    success_criteria?: string[];
    failure_conditions?: string[];
    exit_actions?: string[];
    config?: any;
    tools?: any[];
    active_version_id?: string;
    created_at?: string;
    updated_at?: string;
}

interface AgentVersion {
    id: string;
    agent_id: string;
    version_number: number;
    persona?: string;
    tools?: any[];
    policy?: any;
    success_criteria?: string[];
    failure_conditions?: string[];
    exit_actions?: string[];
    change_log?: string;
    token_limit?: number;
    fallback_model?: string;
    created_at: string;
    created_by?: string;
    weight?: number;
    is_canary?: boolean;
}

interface Voice {
    id: string;
    name: string;
    type: string;
    primaryLanguage: string;
}

export default function AgentDetailPage() {
    const params = useParams();
    const router = useRouter();
    const [agent, setAgent] = useState<Agent | null>(null);
    const [voices, setVoices] = useState<Voice[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState("playground");
    const [saving, setSaving] = useState(false);

    const [input, setInput] = useState("");

    // Form State
    const [formData, setFormData] = useState<Partial<Agent>>({});
    const [selectedVoice, setSelectedVoice] = useState("auto");
    const [greeting, setGreeting] = useState("");
    // Playground — live voice test
    const uvx = useUltravoxSession(
        (params.id as string) || "",
        agent?.language,
        selectedVoice
    );

    // Knowledge Base State
    const [knowledgeItems, setKnowledgeItems] = useState<any[]>([]);
    const [newKnowledge, setNewKnowledge] = useState({ title: "", content: "" });
    const [isAddingKnowledge, setIsAddingKnowledge] = useState(false);
    const [knowledgeSearch, setKnowledgeSearch] = useState("");
    const [queryResults, setQueryResults] = useState<any[]>([]);

    // Analytics State
    const [analytics, setAnalytics] = useState<any>(null);
    const [calls, setCalls] = useState<any[]>([]);
    const [analyticsLoading, setAnalyticsLoading] = useState(false);

    // Versions State
    const [versions, setVersions] = useState<AgentVersion[]>([]);
    const [versionsLoading, setVersionsLoading] = useState(false);

    // Policy State
    const [policy, setPolicy] = useState<any>(null);
    const [compliance, setCompliance] = useState<any>(null);
    const [policyLoading, setPolicyLoading] = useState(false);

    const fetchKnowledge = useCallback(async () => {
        try {
            const data = await api.get(`/knowledge/${params.id}`);
            setKnowledgeItems(data);
        } catch (err) {
            console.error("Failed to fetch knowledge", err);
        }
    }, [params.id]);

    const fetchVoices = useCallback(async (lang: string) => {
        try {
            const data = await api.get(`/voices/?primaryLanguage=${encodeURIComponent(lang)}`);
            setVoices(data);
        } catch {
            setVoices([]);
        }
    }, []);

    const loadData = useCallback(async () => {
        try {
            const agentData = await api.get(`/agents/${params.id}`);
            setAgent(agentData);
            setFormData(agentData);
            setSelectedVoice(agentData.config?.voice || "auto");
            setGreeting(agentData.config?.greeting || "");
            await fetchVoices(agentData.language || "hi");
        } catch (error) {
            console.error("Failed to load data", error);
        } finally {
            setLoading(false);
        }
    }, [params.id, fetchVoices]);

    const loadAnalytics = useCallback(async () => {
        setAnalyticsLoading(true);
        try {
            const [analyticsData, callsData] = await Promise.all([
                api.get(`/agents/${params.id}/analytics`),
                api.get(`/agents/${params.id}/calls?limit=10`),
            ]);
            setAnalytics(analyticsData);
            setCalls(callsData);
        } catch (err) {
            console.error("Failed to load analytics", err);
        } finally {
            setAnalyticsLoading(false);
        }
    }, [params.id]);

    const loadVersions = useCallback(async () => {
        setVersionsLoading(true);
        try {
            const data = await api.get(`/agents/${params.id}/versions`);
            setVersions(data);
        } catch (err) {
            console.error("Failed to load versions", err);
        } finally {
            setVersionsLoading(false);
        }
    }, [params.id]);

    const loadPolicy = useCallback(async () => {
        setPolicyLoading(true);
        try {
            const [policyData, complianceData] = await Promise.all([
                api.get(`/agents/${params.id}/policy`),
                api.get(`/agents/${params.id}/compliance`),
            ]);
            setPolicy(policyData);
            setCompliance(complianceData);
        } catch (err) {
            console.error("Failed to load policy", err);
        } finally {
            setPolicyLoading(false);
        }
    }, [params.id]);

    useEffect(() => {
        if (params.id) {
            loadData();
        }
    }, [params.id, loadData]);

    useEffect(() => {
        if (activeTab === "knowledge" && params.id) {
            fetchKnowledge();
        }
    }, [activeTab, params.id, fetchKnowledge]);

    useEffect(() => {
        if (formData.language) {
            fetchVoices(formData.language);
            if (selectedVoice !== "auto") {
                setSelectedVoice("auto");
            }
        }
    }, [formData.language, selectedVoice, fetchVoices]);

    useEffect(() => {
        if (activeTab === "analytics" && params.id) {
            loadAnalytics();
        }
    }, [activeTab, params.id, loadAnalytics]);

    useEffect(() => {
        if (activeTab === "versions" && params.id) {
            loadVersions();
        }
    }, [activeTab, params.id, loadVersions]);

    useEffect(() => {
        if (activeTab === "policy" && params.id) {
            loadPolicy();
        }
    }, [activeTab, params.id, loadPolicy]);

    const handleAddKnowledge = async () => {
        if (!newKnowledge.title || !newKnowledge.content) return;
        try {
            await api.post(`/knowledge/${params.id}`, newKnowledge);
            setNewKnowledge({ title: "", content: "" });
            setIsAddingKnowledge(false);
            fetchKnowledge();
        } catch (err) {
            console.error("Failed to add knowledge", err);
        }
    };

    const handleDeleteKnowledge = async (kid: string) => {
        try {
            await api.delete(`/knowledge/${kid}`);
            fetchKnowledge();
        } catch (err) {
            console.error("Failed to delete knowledge", err);
        }
    };

    const runKnowledgeQuery = async (q: string) => {
        if (!q) return;
        try {
            const data = await api.get(`/knowledge/${params.id}/query?q=${encodeURIComponent(q)}`);
            setQueryResults(data);
        } catch (err) {
            console.error("Query failed", err);
        }
    };

    const createVersion = async () => {
        if (!agent) return;
        try {
            const nextNum = versions.length > 0 ? Math.max(...versions.map(v => v.version_number)) + 1 : 1;
            await api.post(`/agents/${params.id}/versions`, {
                version_number: nextNum,
                persona: agent.persona,
                tools: agent.tools || [],
                success_criteria: agent.success_criteria || [],
                failure_conditions: agent.failure_conditions || [],
                exit_actions: agent.exit_actions || [],
                token_limit: (agent as any).token_limit,
                fallback_model: (agent as any).fallback_model,
                change_log: `Snapshot v${nextNum}`,
            });
            loadVersions();
        } catch (err) {
            console.error("Failed to create version", err);
        }
    };

    const pinVersion = async (versionId: string) => {
        try {
            await api.post(`/agents/${params.id}/pin/${versionId}`, {});
            loadVersions();
        } catch (err) {
            console.error("Failed to pin version", err);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const updatedConfig = {
                ...(agent?.config || {}),
                voice: selectedVoice,
                greeting: greeting.trim() || undefined,
            };

            await api.put(`/agents/${params.id}`, {
                ...formData,
                config: updatedConfig
            });
            // Reload to confirm save
            loadData();
        } catch (err) {
            console.error("Failed to save", err);
        } finally {
            setSaving(false);
        }
    };

    const insertPersonalization = (key: string, target: "persona" | "greeting") => {
        const token = personalizationToken(key);
        if (target === "greeting") {
            setGreeting((g) => (g ? `${g} ${token}` : token).trim());
        } else {
            setFormData((f) => ({
                ...f,
                persona: ((f.persona || "") + " " + token).trim(),
            }));
        }
    };

    const sendMessage = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || !uvx.isCalling) return;
        uvx.sendText(input);
        setInput("");
    };

    if (loading) return <div className="p-8 text-foreground">Loading agent…</div>;
    if (!agent) return <div className="p-8 text-foreground">Agent not found</div>;

    return (
        <div className="space-y-6 h-[calc(100vh-100px)] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between shrink-0">
                <div className="flex items-center gap-4">
                    <button type="button" aria-label="Back to agents" onClick={() => router.push('/dashboard/agents')} className="text-muted-foreground hover:text-foreground transition-colors">
                        <ArrowLeft className="size-5" />
                    </button>
                    <div>
                        <h2 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
                            {agent.name}
                            <span className={`px-2 py-0.5 rounded-full text-xs border ${agent.is_active ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-red-500/10 text-red-500 border-red-500/20'}`}>
                                {agent.is_active ? 'Active' : 'Inactive'}
                            </span>
                        </h2>
                        <p className="text-sm text-muted-foreground">{agent.role} · {agent.language}</p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <button type="button" onClick={handleSave} disabled={saving} className="flex items-center gap-2 bg-primary hover:brightness-110 text-white px-4 py-2 rounded-md font-medium transition-colors disabled:opacity-50">
                        <Save className="size-4" />
                        {saving ? "Saving..." : "Save Changes"}
                    </button>
                </div>
            </div>

            {/* Tabs & Main Content */}
            <div className="flex items-start gap-6 h-full overflow-hidden">
                {/* Sidebar Navigation */}
                <div className="w-64 shrink-0 space-y-1">
                    {[
                        { id: "configuration", label: "Configuration", icon: Sliders },
                        { id: "playground", label: "Playground", icon: Play },
                        { id: "knowledge", label: "Knowledge Base", icon: Book },
                        { id: "analytics", label: "Analytics", icon: Activity },
                        { id: "versions", label: "Versions", icon: History },
                        { id: "policy", label: "Policy & Safety", icon: Shield },
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            type="button"
                            onClick={() => setActiveTab(tab.id)}
                            className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === tab.id
                                ? "bg-primary/10 text-primary border border-primary/20"
                                : "text-muted-foreground hover:bg-muted hover:text-foreground"
                                }`}
                        >
                            <tab.icon className="size-4" />
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Content Area */}
                <div className="flex-1 h-full overflow-y-auto pr-2">
                    {/* CONFIGURATION TAB */}
                    {activeTab === "configuration" && (
                        <div className="space-y-6 max-w-3xl">
                            <Card className="border-border bg-card">
                                <CardHeader>
                                    <CardTitle>Core Profile</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label htmlFor="agent-name" className="block text-sm font-medium text-muted-foreground mb-1">Name</label>
                                            <input
                                                id="agent-name"
                                                value={formData.name}
                                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                                                className="w-full bg-muted border border-border rounded-md px-3 py-2 text-foreground focus:outline-none focus:border-ring"
                                            />
                                        </div>
                                        <div>
                                            <label htmlFor="agent-role" className="block text-sm font-medium text-muted-foreground mb-1">Role/Title</label>
                                            <input
                                                id="agent-role"
                                                value={formData.role}
                                                onChange={e => setFormData({ ...formData, role: e.target.value })}
                                                className="w-full bg-muted border border-border rounded-md px-3 py-2 text-foreground focus:outline-none focus:border-ring"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label htmlFor="agent-language" className="block text-sm font-medium text-muted-foreground mb-1">Language</label>
                                        <div className="flex items-center gap-2">
                                            <Globe className="size-4 text-muted-foreground" />
                                            <select
                                                id="agent-language"
                                                value={formData.language}
                                                onChange={e => setFormData({ ...formData, language: e.target.value })}
                                                className="w-full bg-muted border border-border rounded-md px-3 py-2 text-foreground focus:outline-none focus:border-ring"
                                            >
                                                {LANGUAGES.map(l => (
                                                    <option key={l.code} value={l.code}>
                                                        {languageDisplay(l.code)}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>
                                    <div>
                                        <label htmlFor="agent-description" className="block text-sm font-medium text-muted-foreground mb-1">Short description (internal)</label>
                                        <input
                                            id="agent-description"
                                            value={formData.description || ""}
                                            onChange={e => setFormData({ ...formData, description: e.target.value })}
                                            placeholder="e.g. Handles payment reminders and billing questions."
                                            className="w-full bg-muted border border-border rounded-md px-3 py-2 text-foreground focus:outline-none focus:border-ring"
                                        />
                                    </div>
                                    <div>
                                        <label htmlFor="agent-greeting" className="block text-sm font-medium text-muted-foreground mb-1">Opening Greeting (optional)</label>
                                        <input
                                            id="agent-greeting"
                                            value={greeting}
                                            onChange={e => setGreeting(e.target.value)}
                                            placeholder="Hello, this is Alex from Acme Corp…"
                                            className="w-full bg-muted border border-border rounded-md px-3 py-2 text-foreground focus:outline-none focus:border-ring text-sm"
                                        />
                                        <p className="text-xs text-muted-foreground mt-1">Spoken first when the call connects. Use personalization fields below to tailor each call.</p>
                                    </div>
                                    <div>
                                        <label htmlFor="agent-persona" className="block text-sm font-medium text-muted-foreground mb-1">System Persona (Instructions)</label>
                                        <textarea
                                            id="agent-persona"
                                            value={formData.persona}
                                            onChange={e => setFormData({ ...formData, persona: e.target.value })}
                                            rows={8}
                                            placeholder="You are a friendly payment specialist. Confirm the customer's balance and offer a payment plan…"
                                            className="w-full bg-muted border border-border rounded-md px-3 py-2 text-foreground focus:outline-none focus:border-ring font-mono text-sm leading-relaxed shadow-inner"
                                        />
                                        <p className="text-xs text-muted-foreground mt-2">
                                            Click a field to insert personalization into instructions or greeting.
                                        </p>
                                        <div className="mt-2 flex flex-wrap gap-2">
                                            {PERSONALIZATION_FIELDS.map((v) => (
                                                <button
                                                    key={v.key}
                                                    type="button"
                                                    title={v.hint}
                                                    onClick={() => insertPersonalization(v.key, "persona")}
                                                    className="text-[10px] px-2 py-0.5 rounded-full bg-muted border border-border text-gray-300 hover:border-cyan/30 hover:text-cyan"
                                                >
                                                    {v.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            <Card className="border-border bg-card">
                                <CardHeader>
                                    <CardTitle className="text-primary flex items-center gap-2">
                                        <Shield className="size-4" />
                                        Goals & outcomes
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div>
                                        <label htmlFor="success-criteria" className="block text-sm font-medium text-muted-foreground mb-1">Success criteria</label>
                                        <div className="space-y-2">
                                            {(formData.success_criteria || []).map((goal, idx) => (
                                                <div key={`success-${idx}`} className="flex gap-2">
                                                    <input
                                                        aria-label="Success criteria input"
                                                        value={goal}
                                                        onChange={(e) => {
                                                            const newGoals = [...(formData.success_criteria || [])];
                                                            newGoals[idx] = e.target.value;
                                                            setFormData({ ...formData, success_criteria: newGoals });
                                                        }}
                                                        className="flex-1 bg-muted border border-border rounded-md px-3 py-2 text-foreground text-sm"
                                                    />
                                                    <button type="button" aria-label="Remove criteria" onClick={() => {
                                                        const newGoals = (formData.success_criteria || []).filter((_, i) => i !== idx);
                                                        setFormData({ ...formData, success_criteria: newGoals });
                                                    }} className="text-red-500 p-2"><Trash2 className="size-4" /></button>
                                                </div>
                                            ))}
                                            <button
                                                type="button"
                                                onClick={() => setFormData({ ...formData, success_criteria: [...(formData.success_criteria || []), ""] })}
                                                className="text-xs text-primary hover:text-primary/80"
                                            >+ Add Criteria</button>
                                        </div>
                                    </div>

                                    <div>
                                        <label htmlFor="failure-conditions" className="block text-sm font-medium text-muted-foreground mb-1">When to end or escalate</label>
                                        <div className="space-y-2">
                                            {(formData.failure_conditions || []).map((cond, idx) => (
                                                <div key={`failure-${idx}`} className="flex gap-2">
                                                    <input
                                                        aria-label="Failure condition input"
                                                        value={cond}
                                                        onChange={(e) => {
                                                            const newConds = [...(formData.failure_conditions || [])];
                                                            newConds[idx] = e.target.value;
                                                            setFormData({ ...formData, failure_conditions: newConds });
                                                        }}
                                                        className="flex-1 bg-muted border border-border rounded-md px-3 py-2 text-foreground text-sm"
                                                    />
                                                    <button type="button" aria-label="Remove condition" onClick={() => {
                                                        const newConds = (formData.failure_conditions || []).filter((_, i) => i !== idx);
                                                        setFormData({ ...formData, failure_conditions: newConds });
                                                    }} className="text-red-500 p-2"><Trash2 className="size-4" /></button>
                                                </div>
                                            ))}
                                            <button
                                                type="button"
                                                onClick={() => setFormData({ ...formData, failure_conditions: [...(formData.failure_conditions || []), ""] })}
                                                className="text-xs text-red-400 hover:text-red-300"
                                            >+ Add Failure Condition</button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            <Card className="border-border bg-card">
                                <CardHeader>
                                    <CardTitle>Voice Settings</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div>
                                        <label htmlFor="voice-identity" className="block text-sm font-medium text-muted-foreground mb-1">Voice Identity</label>
                                        <div className="flex items-center gap-2">
                                            <Volume2 className="size-4 text-muted-foreground" />
                                            <select
                                                id="voice-identity"
                                                value={selectedVoice}
                                                onChange={e => setSelectedVoice(e.target.value)}
                                                className="w-full bg-muted border border-border rounded-md px-3 py-2 text-foreground focus:outline-none focus:border-ring"
                                            >
                                                <option value="auto">Auto-Select</option>
                                                {voices.map(v => (
                                                    <option key={v.id} value={v.id}>{v.name} ({v.type})</option>
                                                ))}
                                            </select>
                                        </div>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            Manage clones in the <a href="/dashboard/voices" className="text-primary hover:underline">Voice Lab</a>.
                                        </p>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    )}

                    {/* PLAYGROUND TAB */}
                    {activeTab === "playground" && (
                        <div className="h-full flex flex-col pb-6">
                            <Card className="flex-1 flex flex-col border-border bg-card overflow-hidden">
                                <div className="p-4 border-b border-border flex items-center justify-between bg-muted/50">
                                    <div className="flex items-center gap-2">
                                        <div className={`size-2 rounded-full ${uvx.isConnected ? "bg-green-500" : "bg-red-500"}`} />
                                        <span className="text-sm font-medium text-gray-300">
                                            {uvx.isConnected ? "Connected" : "Not connected"} · {uvx.isCalling ? "On call" : "Ready"}
                                        </span>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => (uvx.isCalling ? uvx.leaveCall() : uvx.startCall())}
                                        className={`px-3 py-1.5 rounded text-xs font-medium border ${uvx.isCalling ? "border-red-500/20 text-red-400 hover:bg-red-500/10" : "border-green-500/20 text-green-400 hover:bg-green-500/10"}`}
                                    >
                                        {uvx.isCalling ? "End call" : "Start call"}
                                    </button>
                                </div>

                                {uvx.isCalling ? (
                                    <div className="flex-1 flex flex-col items-center justify-center space-y-8 animate-in fade-in duration-500">
                                        <div className="relative">
                                            <div className={`absolute -inset-4 bg-primary/20 rounded-full blur-xl transition-all duration-700 ${uvx.agentSpeaking ? 'scale-150 opacity-100' : 'scale-100 opacity-50'}`} />
                                            <div className={`relative size-32 rounded-full border-2 flex items-center justify-center transition-all duration-300 ${uvx.agentSpeaking ? 'border-primary bg-primary/10 shadow-[0_0_30px_rgba(11,116,176,0.5)]' : 'border-border bg-muted'}`}>
                                                <Bot className={`size-16 transition-all duration-300 ${uvx.agentSpeaking ? 'text-primary scale-110' : 'text-muted-foreground'}`} />
                                            </div>
                                            {uvx.agentSpeaking && (
                                                <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                                                    {[1, 2, 3, 4, 5].map(i => (
                                                        <div key={i} className="w-1 bg-primary rounded-full animate-bounce" style={{ height: `${8 + (i % 3) * 6}px`, animationDelay: `${i * 0.1}s` }} />
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                        <div className="text-center space-y-2">
                                            <h3 className="text-xl font-semibold text-foreground">{uvx.agentSpeaking ? "Agent is speaking..." : "Listening..."}</h3>
                                            <p className="text-sm text-muted-foreground">Live voice test</p>
                                        </div>
                                        <div className="flex gap-4">
                                            <button type="button" aria-label={uvx.isMuted ? "Unmute microphone" : "Mute microphone"} onClick={uvx.toggleMute} className={`p-4 rounded-full border transition-all ${uvx.isMuted ? 'bg-red-500/10 border-red-500/50 text-red-500' : 'bg-muted border-border text-muted-foreground hover:bg-muted'}`}>
                                                {uvx.isMuted ? <MicOff className="size-6" /> : <Mic className="size-6" />}
                                            </button>
                                            <button type="button" aria-label="Leave call" onClick={uvx.leaveCall} className="p-4 rounded-full bg-red-600 text-white hover:bg-red-500 transition-all shadow-lg shadow-red-600/20">
                                                <PhoneOff className="size-6" />
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                                        {uvx.chatHistory.length === 0 && (
                                            <div className="flex flex-col items-center justify-center h-full text-gray-600 space-y-2">
                                                <Bot className="size-10 opacity-20" />
                                                <p className="text-sm">Start the conversation to test the agent</p>
                                            </div>
                                        )}
                                        {uvx.chatHistory.map((msg, i) => (
                                            <div key={`chat-${i}`} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                                <div className={`max-w-[80%] rounded-lg px-4 py-3 text-sm ${msg.role === 'user'
                                                    ? 'bg-primary text-white'
                                                    : msg.role === 'system'
                                                        ? 'bg-muted text-muted-foreground italic font-mono text-xs border border-border'
                                                        : 'bg-white/10 text-gray-200'
                                                    }`}>
                                                    {msg.content}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                <div className="p-4 border-t border-border bg-muted/50">
                                    <div className="flex gap-2 items-center mb-4 px-2">
                                        <div className="flex-1 h-px bg-muted" />
                                        <button
                                            type="button"
                                            onClick={uvx.isCalling ? uvx.leaveCall : uvx.startCall}
                                            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold transition-all ${uvx.isCalling ? 'bg-red-600 text-white animate-pulse' : 'bg-green-600/10 text-green-400 border border-green-500/20 hover:bg-green-600/20'}`}
                                        >
                                            {uvx.isCalling ? <PhoneOff className="size-4" /> : <Phone className="size-4" />}
                                            {uvx.isCalling ? "End call" : "Start test call"}
                                        </button>
                                        <div className="flex-1 h-px bg-muted" />
                                    </div>
                                    <form onSubmit={sendMessage} className="flex gap-2">
                                        <input
                                            value={input}
                                            onChange={e => setInput(e.target.value)}
                                            placeholder="Type a message..."
                                            disabled={!uvx.isCalling}
                                            className="flex-1 bg-muted border border-border rounded-md px-4 py-2.5 text-foreground focus:outline-none focus:border-ring disabled:opacity-50"
                                        />
                                        <button
                                            type="submit"
                                            aria-label="Send message"
                                            disabled={!uvx.isCalling}
                                            className="p-2.5 bg-primary text-white rounded-md hover:brightness-110 disabled:opacity-50 disabled:hover:bg-primary"
                                        >
                                            <Play className="size-5 fill-current" />
                                        </button>
                                    </form>
                                    <div className="flex justify-center mt-2">
                                        <p className="text-[10px] text-gray-600">
                                            Use your microphone to talk with this agent before going live on campaigns.
                                        </p>
                                    </div>
                                </div>
                            </Card>
                        </div>
                    )}

                    {/* KNOWLEDGE BASE TAB */}
                    {activeTab === "knowledge" && (
                        <div className="space-y-6 pb-12">
                            <div className="flex items-center justify-between">
                                <h3 className="text-xl font-semibold text-foreground flex items-center gap-2">
                                    <Book className="size-5 text-primary" />
                                    Knowledge Base
                                </h3>
                                <button
                                    type="button"
                                    onClick={() => setIsAddingKnowledge(true)}
                                    className="flex items-center gap-2 bg-primary/10 text-primary border border-primary/20 px-4 py-2 rounded-md hover:bg-primary/20 transition-colors"
                                >
                                    <Plus className="size-4" />
                                    Add Document
                                </button>
                            </div>

                            <Card className="border-border bg-card">
                                <CardContent className="p-0">
                                    <div className="divide-y divide-white/5">
                                        {knowledgeItems.length === 0 && !isAddingKnowledge && (
                                            <div className="p-12 text-center text-muted-foreground">
                                                <FileText className="size-12 mx-auto mb-4 opacity-10" />
                                                <p>No documents found. Add knowledge to improve agent accuracy.</p>
                                            </div>
                                        )}

                                        {isAddingKnowledge && (
                                            <div className="p-6 bg-primary/5 animate-in fade-in slide-in-from-top-4 duration-300">
                                                <div className="space-y-4">
                                                    <div>
                                                        <label htmlFor="knowledge-title" className="block text-sm font-medium text-muted-foreground mb-1">Document Title</label>
                                                        <input
                                                            id="knowledge-title"
                                                            value={newKnowledge.title}
                                                            onChange={e => setNewKnowledge({ ...newKnowledge, title: e.target.value })}
                                                            className="w-full bg-muted border border-border rounded-md px-3 py-2 text-foreground"
                                                            placeholder="e.g. Return Policy 2024"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label htmlFor="knowledge-content" className="block text-sm font-medium text-muted-foreground mb-1">Content (Knowledge Chunk)</label>
                                                        <textarea
                                                            id="knowledge-content"
                                                            value={newKnowledge.content}
                                                            onChange={e => setNewKnowledge({ ...newKnowledge, content: e.target.value })}
                                                            className="w-full bg-muted border border-border rounded-md px-3 py-2 text-foreground h-32"
                                                            placeholder="Paste document text here..."
                                                        />
                                                    </div>
                                                    <div className="flex gap-2 justify-end">
                                                    <button
                                                        type="button"
                                                        onClick={() => setIsAddingKnowledge(false)}
                                                        className="px-4 py-2 text-sm text-muted-foreground"
                                                    >Cancel</button>
                                                    <button
                                                        type="button"
                                                        onClick={handleAddKnowledge}
                                                        className="px-4 py-2 text-sm bg-primary text-white rounded-md"
                                                    >Ingest Knowledge</button>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {knowledgeItems.map((item) => (
                                            <div key={item.id} className="p-4 flex items-start justify-between group hover:bg-muted">
                                                <div className="flex-1">
                                                    <h4 className="font-medium text-foreground text-sm flex items-center gap-2">
                                                        <FileText className="size-3 text-muted-foreground" />
                                                        {item.title}
                                                    </h4>
                                                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2 leading-relaxed">
                                                        {item.content}
                                                    </p>
                                                </div>
                                                <button
                                                    type="button"
                                                    aria-label="Delete document"
                                                    onClick={() => handleDeleteKnowledge(item.id)}
                                                    className="p-2 text-muted-foreground hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                                                >
                                                    <Trash2 className="size-4" />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Semantic Search Tester */}
                            <div className="mt-8 space-y-4">
                                <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-widest">RAG Query Tester</h4>
                                <div className="flex gap-2">
                                    <div className="relative flex-1">
                                        <Search className="size-4 absolute left-3 top-2.5 text-muted-foreground" />
                                        <input
                                            value={knowledgeSearch}
                                            onChange={e => setKnowledgeSearch(e.target.value)}
                                            onKeyDown={e => e.key === 'Enter' && runKnowledgeQuery(knowledgeSearch)}
                                            placeholder="Test semantic retrieval... (e.g. What is the return limit?)"
                                            className="w-full bg-muted border border-border rounded-full pl-10 pr-4 py-2 text-sm text-foreground focus:outline-none focus:border-ring/50"
                                        />
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => runKnowledgeQuery(knowledgeSearch)}
                                        className="bg-muted text-foreground px-4 py-2 rounded-full text-sm font-medium hover:bg-muted/70"
                                    >Test</button>
                                </div>

                                {queryResults.length > 0 && (
                                    <div className="space-y-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
                                        {queryResults.map((res, i) => (
                                            <div key={`query-${res.title}-${i}`} className="p-3 bg-green-500/5 border border-green-500/10 rounded-lg">
                                                <div className="flex justify-between items-center mb-1">
                                                    <span className="text-[10px] font-semibold text-green-500 uppercase tracking-tighter">Match Score: {(res.score * 100).toFixed(1)}%</span>
                                                    <span className="text-[10px] text-gray-600">{res.title}</span>
                                                </div>
                                                <p className="text-xs text-gray-300 italic">"{res.content}"</p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* ANALYTICS TAB */}
                    {activeTab === "analytics" && (
                        <div className="space-y-6 max-w-4xl pb-12">
                            {analyticsLoading ? (
                                <div className="grid grid-cols-3 gap-4">
                                    {[1,2,3,4,5,6].map(i => <div key={i} className="bg-card border border-border rounded-xl h-24 animate-pulse" />)}
                                </div>
                            ) : analytics ? (
                                <>
                                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                        <div className="bg-card border border-border rounded-xl p-4">
                                            <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1"><Phone className="w-3.5 h-3.5" /> Total Calls</div>
                                            <div className="font-display font-semibold text-2xl">{analytics.total_calls}</div>
                                        </div>
                                        <div className="bg-card border border-border rounded-xl p-4">
                                            <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1"><Clock className="w-3.5 h-3.5" /> Total Minutes</div>
                                            <div className="font-display font-semibold text-2xl">{analytics.total_minutes}</div>
                                        </div>
                                        <div className="bg-card border border-border rounded-xl p-4">
                                            <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1"><BarChart3 className="w-3.5 h-3.5" /> Avg Duration</div>
                                            <div className="font-display font-semibold text-2xl">{analytics.avg_duration_seconds}s</div>
                                        </div>
                                        <div className="bg-card border border-border rounded-xl p-4">
                                            <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1"><Activity className="w-3.5 h-3.5" /> Avg Latency</div>
                                            <div className="font-display font-semibold text-2xl">{analytics.avg_latency_ms}ms</div>
                                        </div>
                                        <div className="bg-card border border-border rounded-xl p-4">
                                            <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1"><DollarSign className="w-3.5 h-3.5" /> Total Cost</div>
                                            <div className="font-display font-semibold text-2xl">${analytics.total_cost}</div>
                                        </div>
                                        <div className="bg-card border border-border rounded-xl p-4">
                                            <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1"><TrendingUp className="w-3.5 h-3.5" /> Success Rate</div>
                                            <div className="font-display font-semibold text-2xl">{analytics.success_rate}%</div>
                                            <div className="w-full bg-muted rounded-full h-1.5 mt-2">
                                                <div className="bg-primary rounded-full h-1.5 transition-all" style={{ width: `${analytics.success_rate}%` }} />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {/* Outcome breakdown */}
                                        <Card className="border-border bg-card">
                                            <CardHeader><CardTitle className="text-sm">Outcome Breakdown</CardTitle></CardHeader>
                                            <CardContent>
                                                <div className="space-y-2">
                                                    {Object.entries(analytics.outcome_breakdown || {}).map(([outcome, count]) => (
                                                        <div key={outcome} className="flex items-center justify-between text-sm">
                                                            <span className="flex items-center gap-2">
                                                                {outcome === "SUCCESS" ? <CheckCircle className="size-4 text-green-500" /> :
                                                                 outcome === "FAILURE" ? <XCircle className="size-4 text-red-500" /> :
                                                                 <AlertTriangle className="size-4 text-yellow-500" />}
                                                                {outcome}
                                                            </span>
                                                            <span className="font-mono font-semibold">{String(count)}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </CardContent>
                                        </Card>

                                        {/* Daily trend chart */}
                                        <Card className="border-border bg-card">
                                            <CardHeader><CardTitle className="text-sm">Daily Call Volume (7d)</CardTitle></CardHeader>
                                            <CardContent>
                                                {analytics.daily_trends?.length > 0 ? (
                                                    <div className="h-[160px]">
                                                        <ResponsiveContainer width="100%" height="100%">
                                                            <AreaChart data={analytics.daily_trends}>
                                                                <defs>
                                                                    <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                                                                        <stop offset="0%" stopColor="#6C5CE7" stopOpacity={0.3} />
                                                                        <stop offset="100%" stopColor="#6C5CE7" stopOpacity={0} />
                                                                    </linearGradient>
                                                                </defs>
                                                                <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
                                                                <XAxis dataKey="date" className="text-muted-foreground" fontSize={10} tickLine={false} axisLine={false} />
                                                                <YAxis className="text-muted-foreground" fontSize={10} tickLine={false} axisLine={false} allowDecimals={false} />
                                                                <Area type="monotone" dataKey="count" stroke="#6C5CE7" fill="url(#trendGradient)" strokeWidth={2} />
                                                            </AreaChart>
                                                        </ResponsiveContainer>
                                                    </div>
                                                ) : <p className="text-sm text-muted-foreground">No daily data yet.</p>}
                                            </CardContent>
                                        </Card>
                                    </div>

                                    {/* Recent calls */}
                                    <Card className="border-border bg-card">
                                        <CardHeader><CardTitle className="text-sm">Recent Calls</CardTitle></CardHeader>
                                        <CardContent>
                                            {calls.length === 0 ? (
                                                <p className="text-sm text-muted-foreground">No calls recorded yet.</p>
                                            ) : (
                                                <div className="overflow-x-auto">
                                                    <table className="w-full text-sm">
                                                        <thead>
                                                            <tr className="text-muted-foreground text-xs text-left border-b border-border">
                                                                <th className="pb-2 font-medium">Outcome</th>
                                                                <th className="pb-2 font-medium">Duration</th>
                                                                <th className="pb-2 font-medium">Latency</th>
                                                                <th className="pb-2 font-medium">Turns</th>
                                                                <th className="pb-2 font-medium">Cost</th>
                                                                <th className="pb-2 font-medium">Time</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {calls.map((c: any) => (
                                                                <tr key={c.id} className="border-b border-border/50 text-foreground">
                                                                    <td className="py-2.5">
                                                                        <span className={`inline-flex items-center gap-1 text-xs ${
                                                                            c.outcome === "SUCCESS" ? "text-green-500" :
                                                                            c.outcome === "FAILURE" ? "text-red-500" : "text-yellow-500"
                                                                        }`}>
                                                                            {c.outcome === "SUCCESS" ? <CheckCircle className="size-3" /> :
                                                                             c.outcome === "FAILURE" ? <XCircle className="size-3" /> :
                                                                             <AlertTriangle className="size-3" />}
                                                                            {c.outcome || "N/A"}
                                                                        </span>
                                                                    </td>
                                                                    <td className="py-2.5 font-mono text-xs">{c.duration_seconds.toFixed(1)}s</td>
                                                                    <td className="py-2.5 font-mono text-xs">{c.avg_latency_ms.toFixed(0)}ms</td>
                                                                    <td className="py-2.5 font-mono text-xs">{c.total_turns}</td>
                                                                    <td className="py-2.5 font-mono text-xs">${c.estimated_cost.toFixed(4)}</td>
                                                                    <td className="py-2.5 text-xs text-muted-foreground">
                                                                        {c.start_time ? new Date(c.start_time).toLocaleString() : "-"}
                                                                    </td>
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            )}
                                        </CardContent>
                                    </Card>
                                </>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-[300px] text-muted-foreground">
                                    <BarChart3 className="size-10 mb-2 opacity-50" />
                                    <p>No analytics available yet.</p>
                                </div>
                            )}
                        </div>
                    )}

                    {/* VERSIONS TAB */}
                    {activeTab === "versions" && (
                        <div className="space-y-6 max-w-3xl pb-12">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                                    <History className="size-5 text-primary" />
                                    Version History
                                </h3>
                                <button
                                    type="button"
                                    onClick={createVersion}
                                    disabled={versionsLoading}
                                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-xl text-xs font-semibold hover:brightness-110 transition-all disabled:opacity-50"
                                >
                                    <Save className="w-3.5 h-3.5" />
                                    Snapshot Current
                                </button>
                            </div>

                            {versionsLoading ? (
                                <div className="space-y-3">
                                    {[1,2,3].map(i => <div key={i} className="bg-card border border-border rounded-xl h-20 animate-pulse" />)}
                                </div>
                            ) : versions.length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-[300px] text-muted-foreground border border-dashed border-border rounded-xl">
                                    <History className="size-10 mb-2 opacity-50" />
                                    <p className="text-sm font-semibold">No versions yet</p>
                                    <p className="text-xs mt-1">Snapshot the current agent configuration to track changes.</p>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {versions.map((v, i) => {
                                        const isActive = agent?.active_version_id === v.id;
                                        const isFirst = i === 0;
                                        return (
                                            <div key={v.id} className={`bg-card border rounded-xl p-5 transition-all ${
                                                isActive ? "border-primary/40 bg-primary/[0.02]" : "border-border"
                                            }`}>
                                                <div className="flex items-start justify-between">
                                                    <div className="flex items-start gap-3">
                                                        <div className={`size-8 rounded-lg flex items-center justify-center text-xs font-semibold ${
                                                            isActive ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                                                        }`}>
                                                            v{v.version_number}
                                                        </div>
                                                        <div>
                                                            <div className="flex items-center gap-2">
                                                                <span className="font-semibold text-sm text-foreground">Version {v.version_number}</span>
                                                                {isActive && <span className="px-2 py-0.5 bg-primary/10 text-primary text-[9px] font-semibold uppercase rounded-full border border-primary/20">Active</span>}
                                                                {isFirst && !isActive && <span className="px-2 py-0.5 bg-cyan/10 text-cyan text-[9px] font-semibold uppercase rounded-full border border-cyan/20">Latest</span>}
                                                            </div>
                                                            <p className="text-xs text-muted-foreground mt-0.5">
                                                                {v.change_log || "No description"} &middot; {new Date(v.created_at).toLocaleString()}
                                                            </p>
                                                            {v.created_by && <p className="text-[10px] text-muted-foreground mt-0.5">by {v.created_by}</p>}
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        {!isActive && (
                                                            <button
                                                                type="button"
                                                                onClick={() => pinVersion(v.id)}
                                                                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-primary text-primary-foreground hover:brightness-110 transition-all"
                                                            >
                                                                <RotateCcw className="size-3 inline mr-1" />
                                                                Rollback
                                                            </button>
                                                        )}
                                                        {v.weight !== undefined && v.weight > 0 && (
                                                            <span className="text-[10px] text-muted-foreground font-mono">{v.weight}% traffic</span>
                                                        )}
                                                        {v.is_canary && <Tag className="size-3 text-yellow-500" />}
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    )}

                    {/* POLICY & SAFETY TAB */}
                    {activeTab === "policy" && (
                        <div className="space-y-6 max-w-3xl pb-12">
                            {policyLoading ? (
                                <div className="grid grid-cols-2 gap-4">
                                    {[1,2,3,4].map(i => <div key={i} className="bg-card border border-border rounded-xl h-24 animate-pulse" />)}
                                </div>
                            ) : (
                                <>
                                    {/* Compliance summary */}
                                    {compliance && (
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                            <div className="bg-card border border-border rounded-xl p-4">
                                                <div className="text-muted-foreground text-xs mb-1">Turns Audited</div>
                                                <div className="font-display font-semibold text-2xl">{compliance.total_turns_audited}</div>
                                            </div>
                                            <div className="bg-card border border-border rounded-xl p-4">
                                                <div className="text-muted-foreground text-xs mb-1">Violations</div>
                                                <div className="font-display font-semibold text-2xl">{compliance.total_violations}</div>
                                            </div>
                                            <div className="bg-card border border-border rounded-xl p-4">
                                                <div className="text-muted-foreground text-xs mb-1">Max Risk Score</div>
                                                <div className="font-display font-semibold text-2xl">{(compliance.max_risk_score * 100).toFixed(0)}%</div>
                                            </div>
                                            <div className="bg-card border border-border rounded-xl p-4">
                                                <div className="text-muted-foreground text-xs mb-1">Status</div>
                                                <div className={`font-display font-semibold text-lg ${compliance.is_compliant ? 'text-green-500' : 'text-red-500'}`}>
                                                    {compliance.is_compliant ? 'Compliant' : 'Non-Compliant'}
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Active Rules */}
                                    <Card className="border-border bg-card">
                                        <CardHeader>
                                            <CardTitle className="text-sm flex items-center gap-2">
                                                <Shield className="size-4 text-primary" />
                                                Active Guardrails
                                            </CardTitle>
                                            <CardDescription>Rules checked on every call turn</CardDescription>
                                        </CardHeader>
                                        <CardContent>
                                            {compliance?.active_rules?.length > 0 ? (
                                                <div className="space-y-2">
                                                    {(compliance.active_rules as any[]).map((rule: any) => (
                                                        <div key={rule.id} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50 border border-border/50">
                                                            <Shield className={`size-4 shrink-0 mt-0.5 ${
                                                                rule.severity === "critical" ? "text-red-500" :
                                                                rule.severity === "warning" ? "text-yellow-500" : "text-muted-foreground"
                                                            }`} />
                                                            <div className="flex-1 min-w-0">
                                                                <div className="flex items-center gap-2">
                                                                    <span className="text-sm font-semibold text-foreground">{rule.name}</span>
                                                                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase ${
                                                                        rule.severity === "critical" ? "bg-red-500/10 text-red-500" :
                                                                        rule.severity === "warning" ? "bg-yellow-500/10 text-yellow-600" : "bg-muted text-muted-foreground"
                                                                    }`}>{rule.severity}</span>
                                                                </div>
                                                                <p className="text-xs text-muted-foreground mt-0.5">{rule.description}</p>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p className="text-sm text-muted-foreground">No guardrails defined.</p>
                                            )}
                                        </CardContent>
                                    </Card>

                                    {/* Recent Violations */}
                                    <Card className="border-border bg-card">
                                        <CardHeader>
                                            <CardTitle className="text-sm flex items-center gap-2">
                                                <AlertTriangle className="size-4 text-red-500" />
                                                Recent Violations
                                            </CardTitle>
                                            <CardDescription>Last 10 non-compliant turns</CardDescription>
                                        </CardHeader>
                                        <CardContent>
                                            {compliance?.recent_violations?.length > 0 ? (
                                                <div className="space-y-3">
                                                    {(compliance.recent_violations as any[]).map((v: any, i: number) => (
                                                        <div key={i} className="border border-border rounded-lg p-3">
                                                            <div className="flex items-center justify-between mb-1">
                                                                <span className="text-xs text-muted-foreground">Turn {v.turn_index}</span>
                                                                <div className="flex items-center gap-2">
                                                                    <span className="text-[10px] text-red-500 font-semibold">Risk: {(v.risk_score * 100).toFixed(0)}%</span>
                                                                    {v.state_name && <span className="text-[10px] text-muted-foreground">State: {v.state_name}</span>}
                                                                </div>
                                                            </div>
                                                            {v.violations?.length > 0 && (
                                                                <div className="space-y-1 mt-2">
                                                                    {(v.violations as any[]).map((violation: any, j: number) => (
                                                                        <div key={j} className="text-xs text-red-400 bg-red-500/5 rounded px-2 py-1">
                                                                            {violation.rule_name || violation.rule_id}: {violation.reason}
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            )}
                                                            <p className="text-[10px] text-muted-foreground mt-1">{new Date(v.created_at).toLocaleString()}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <div className="flex flex-col items-center py-8 text-muted-foreground">
                                                    <CheckCircle className="size-8 mb-2 text-green-500/50" />
                                                    <p className="text-sm">No violations recorded</p>
                                                    <p className="text-xs mt-1">All audited turns have been compliant.</p>
                                                </div>
                                            )}
                                        </CardContent>
                                    </Card>

                                    {/* Policy definition */}
                                    <Card className="border-border bg-card">
                                        <CardHeader>
                                            <CardTitle className="text-sm flex items-center gap-2">
                                                <Eye className="size-4 text-primary" />
                                                Conversation Policy
                                            </CardTitle>
                                            <CardDescription>State machine definition for this agent</CardDescription>
                                        </CardHeader>
                                        <CardContent>
                                            {policy?.states && Object.keys(policy.states).length > 0 ? (
                                                <div className="space-y-3">
                                                    <p className="text-xs text-muted-foreground">
                                                        Initial state: <span className="font-mono text-foreground">{policy.initial_state}</span>
                                                    </p>
                                                    {Object.entries(policy.states).map(([name, state]: [string, any]) => (
                                                        <details key={name} className="group">
                                                            <summary className="flex items-center gap-2 text-sm font-medium text-foreground cursor-pointer hover:text-primary transition-colors">
                                                                <ChevronDown className="w-3.5 h-3.5 text-muted-foreground group-open:rotate-180 transition-transform" />
                                                                {name}
                                                                {state.is_sensitive && <Shield className="size-3 text-red-500" />}
                                                            </summary>
                                                            <div className="mt-2 ml-5 space-y-2 text-xs text-muted-foreground">
                                                                {state.enforce_script && <p>Script: <span className="font-mono text-foreground">{state.enforce_script}</span></p>}
                                                                {state.allowed_intents?.length > 0 && (
                                                                    <p>Allowed intents: {state.allowed_intents.join(", ")}</p>
                                                                )}
                                                                {state.mandatory_phrases?.length > 0 && (
                                                                    <p>Mandatory phrases: {state.mandatory_phrases.join(", ")}</p>
                                                                )}
                                                                {state.transitions?.length > 0 && (
                                                                    <div>
                                                                        <p className="font-medium mb-1">Transitions:</p>
                                                                        {state.transitions.map((t: any, i: number) => (
                                                                            <div key={i} className="text-[10px] flex items-center gap-2">
                                                                                <span className="text-primary">{t.event}</span>
                                                                                <span className="text-muted-foreground">&rarr;</span>
                                                                                <span>{t.target_state}</span>
                                                                                {t.condition && <span className="text-muted-foreground">[{t.condition}]</span>}
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </details>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p className="text-sm text-muted-foreground">No conversation policy defined. The agent uses default behavior.</p>
                                            )}
                                        </CardContent>
                                    </Card>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </div >
        </div >
    );
}

