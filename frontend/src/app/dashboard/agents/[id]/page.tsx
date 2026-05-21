"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import api from "@/lib/api";
import { useUltravoxSession } from "@/hooks/useUltravoxSession";
import { PERSONALIZATION_FIELDS, personalizationToken } from "@/lib/product-copy";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Save, Play, Mic, Square, Trash2, Sliders, Activity, History, Shield, Globe, Volume2, Book, FileText, Plus, Search, Bot, Phone, PhoneOff, MicOff } from "lucide-react";

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
    config?: any;
}

interface Voice {
    id: string;
    name: string;
    type: string;
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

    useEffect(() => {
        if (params.id) {
            loadData();
        }
    }, [params.id]);

    useEffect(() => {
        if (activeTab === "knowledge" && params.id) {
            fetchKnowledge();
        }
    }, [activeTab]);

    const fetchKnowledge = async () => {
        try {
            const data = await api.get(`/knowledge/${params.id}`);
            setKnowledgeItems(data);
        } catch (err) {
            console.error("Failed to fetch knowledge", err);
        }
    };

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

    const loadData = async () => {
        try {
            const [agentData, voicesData] = await Promise.all([
                api.get(`/agents/${params.id}`),
                api.get(`/voices/`)
            ]);
            setAgent(agentData);
            setFormData(agentData);
            setVoices(voicesData);
            setSelectedVoice(agentData.config?.voice || "auto");
            setGreeting(agentData.config?.greeting || "");
        } catch (error) {
            console.error("Failed to load data", error);
        } finally {
            setLoading(false);
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

    if (loading) return <div className="p-8 text-[var(--text-primary)]">Loading agent...</div>;
    if (!agent) return <div className="p-8 text-[var(--text-primary)]">Agent not found</div>;

    return (
        <div className="space-y-6 h-[calc(100vh-100px)] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between shrink-0">
                <div className="flex items-center gap-4">
                    <button onClick={() => router.push('/dashboard/agents')} className="text-gray-400 hover:text-[var(--text-primary)] transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)] flex items-center gap-2">
                            {agent.name}
                            <span className={`px-2 py-0.5 rounded-full text-xs border ${agent.is_active ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-red-500/10 text-red-500 border-red-500/20'}`}>
                                {agent.is_active ? 'Active' : 'Inactive'}
                            </span>
                        </h2>
                        <p className="text-sm text-gray-400">{agent.role} · {agent.language}</p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <button onClick={handleSave} disabled={saving} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-md font-medium transition-colors disabled:opacity-50">
                        <Save className="w-4 h-4" />
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
                            onClick={() => setActiveTab(tab.id)}
                            className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === tab.id
                                ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                                : "text-gray-400 hover:bg-[var(--glass-bg)] hover:text-[var(--text-primary)]"
                                }`}
                        >
                            <tab.icon className="w-4 h-4" />
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Content Area */}
                <div className="flex-1 h-full overflow-y-auto pr-2">
                    {/* CONFIGURATION TAB */}
                    {activeTab === "configuration" && (
                        <div className="space-y-6 max-w-3xl">
                            <Card className="border-[var(--border-default)] bg-[#0f0f10]">
                                <CardHeader>
                                    <CardTitle>Core Profile</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-400 mb-1">Name</label>
                                            <input
                                                value={formData.name}
                                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                                                className="w-full bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-md px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-400 mb-1">Role/Title</label>
                                            <input
                                                value={formData.role}
                                                onChange={e => setFormData({ ...formData, role: e.target.value })}
                                                className="w-full bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-md px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-400 mb-1">Language</label>
                                        <div className="flex items-center gap-2">
                                            <Globe className="w-4 h-4 text-gray-500" />
                                            <select
                                                value={formData.language}
                                                onChange={e => setFormData({ ...formData, language: e.target.value })}
                                                className="w-full bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-md px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                            >
                                                <option value="en-US">English (US)</option>
                                                <option value="en-GB">English (UK)</option>
                                                <option value="hi">Hindi (हिन्दी)</option>
                                                <option value="es">Spanish (Español)</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-400 mb-1">Short description (internal)</label>
                                        <input
                                            value={formData.description || ""}
                                            onChange={e => setFormData({ ...formData, description: e.target.value })}
                                            placeholder="e.g. Handles payment reminders and billing questions."
                                            className="w-full bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-md px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-400 mb-1">Opening Greeting (optional)</label>
                                        <input
                                            value={greeting}
                                            onChange={e => setGreeting(e.target.value)}
                                            placeholder="Hello, this is Alex from Acme Corp…"
                                            className="w-full bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-md px-3 py-2 text-white focus:outline-none focus:border-blue-500 text-sm"
                                        />
                                        <p className="text-xs text-gray-500 mt-1">Spoken first when the call connects. Use personalization fields below to tailor each call.</p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-400 mb-1">System Persona (Instructions)</label>
                                        <textarea
                                            value={formData.persona}
                                            onChange={e => setFormData({ ...formData, persona: e.target.value })}
                                            rows={8}
                                            placeholder="You are a friendly payment specialist. Confirm the customer's balance and offer a payment plan…"
                                            className="w-full bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-md px-3 py-2 text-white focus:outline-none focus:border-blue-500 font-mono text-sm leading-relaxed shadow-inner"
                                        />
                                        <p className="text-xs text-gray-500 mt-2">
                                            Click a field to insert personalization into instructions or greeting.
                                        </p>
                                        <div className="mt-2 flex flex-wrap gap-2">
                                            {PERSONALIZATION_FIELDS.map((v) => (
                                                <button
                                                    key={v.key}
                                                    type="button"
                                                    title={v.hint}
                                                    onClick={() => insertPersonalization(v.key, "persona")}
                                                    className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--glass-bg)] border border-[var(--border-default)] text-gray-300 hover:border-cyan-500/30 hover:text-cyan-300"
                                                >
                                                    {v.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            <Card className="border-[var(--border-default)] bg-[#0f0f10]">
                                <CardHeader>
                                    <CardTitle className="text-blue-400 flex items-center gap-2">
                                        <Shield className="w-4 h-4" />
                                        Goals & outcomes
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-400 mb-1">Success criteria</label>
                                        <div className="space-y-2">
                                            {(formData.success_criteria || []).map((goal, idx) => (
                                                <div key={idx} className="flex gap-2">
                                                    <input
                                                        value={goal}
                                                        onChange={(e) => {
                                                            const newGoals = [...(formData.success_criteria || [])];
                                                            newGoals[idx] = e.target.value;
                                                            setFormData({ ...formData, success_criteria: newGoals });
                                                        }}
                                                        className="flex-1 bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-md px-3 py-2 text-white text-sm"
                                                    />
                                                    <button onClick={() => {
                                                        const newGoals = (formData.success_criteria || []).filter((_, i) => i !== idx);
                                                        setFormData({ ...formData, success_criteria: newGoals });
                                                    }} className="text-red-500 p-2"><Trash2 className="w-4 h-4" /></button>
                                                </div>
                                            ))}
                                            <button
                                                onClick={() => setFormData({ ...formData, success_criteria: [...(formData.success_criteria || []), ""] })}
                                                className="text-xs text-blue-400 hover:text-blue-300"
                                            >+ Add Criteria</button>
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-400 mb-1">When to end or escalate</label>
                                        <div className="space-y-2">
                                            {(formData.failure_conditions || []).map((cond, idx) => (
                                                <div key={idx} className="flex gap-2">
                                                    <input
                                                        value={cond}
                                                        onChange={(e) => {
                                                            const newConds = [...(formData.failure_conditions || [])];
                                                            newConds[idx] = e.target.value;
                                                            setFormData({ ...formData, failure_conditions: newConds });
                                                        }}
                                                        className="flex-1 bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-md px-3 py-2 text-white text-sm"
                                                    />
                                                    <button onClick={() => {
                                                        const newConds = (formData.failure_conditions || []).filter((_, i) => i !== idx);
                                                        setFormData({ ...formData, failure_conditions: newConds });
                                                    }} className="text-red-500 p-2"><Trash2 className="w-4 h-4" /></button>
                                                </div>
                                            ))}
                                            <button
                                                onClick={() => setFormData({ ...formData, failure_conditions: [...(formData.failure_conditions || []), ""] })}
                                                className="text-xs text-red-400 hover:text-red-300"
                                            >+ Add Failure Condition</button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            <Card className="border-[var(--border-default)] bg-[#0f0f10]">
                                <CardHeader>
                                    <CardTitle>Voice Settings</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-400 mb-1">Voice Identity</label>
                                        <div className="flex items-center gap-2">
                                            <Volume2 className="w-4 h-4 text-gray-500" />
                                            <select
                                                value={selectedVoice}
                                                onChange={e => setSelectedVoice(e.target.value)}
                                                className="w-full bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-md px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                                            >
                                                <option value="auto">Auto-Select</option>
                                                {voices.map(v => (
                                                    <option key={v.id} value={v.id}>{v.name} ({v.type})</option>
                                                ))}
                                            </select>
                                        </div>
                                        <p className="text-xs text-gray-500 mt-1">
                                            Manage clones in the <a href="/dashboard/voices" className="text-blue-400 hover:underline">Voice Lab</a>.
                                        </p>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    )}

                    {/* PLAYGROUND TAB */}
                    {activeTab === "playground" && (
                        <div className="h-full flex flex-col pb-6">
                            <Card className="flex-1 flex flex-col border-[var(--border-default)] bg-[#0f0f10] overflow-hidden">
                                <div className="p-4 border-b border-[var(--border-default)] flex items-center justify-between bg-black/20">
                                    <div className="flex items-center gap-2">
                                        <div className={`w-2 h-2 rounded-full ${uvx.isConnected ? "bg-green-500" : "bg-red-500"}`} />
                                        <span className="text-sm font-medium text-gray-300">
                                            {uvx.isConnected ? "Connected" : "Not connected"} · {uvx.isCalling ? "On call" : "Ready"}
                                        </span>
                                    </div>
                                    <button
                                        onClick={() => (uvx.isCalling ? uvx.leaveCall() : uvx.startCall())}
                                        className={`px-3 py-1.5 rounded text-xs font-medium border ${uvx.isCalling ? "border-red-500/20 text-red-400 hover:bg-red-500/10" : "border-green-500/20 text-green-400 hover:bg-green-500/10"}`}
                                    >
                                        {uvx.isCalling ? "End call" : "Start call"}
                                    </button>
                                </div>

                                {uvx.isCalling ? (
                                    <div className="flex-1 flex flex-col items-center justify-center space-y-8 animate-in fade-in duration-500">
                                        <div className="relative">
                                            <div className={`absolute -inset-4 bg-blue-500/20 rounded-full blur-xl transition-all duration-700 ${uvx.agentSpeaking ? 'scale-150 opacity-100' : 'scale-100 opacity-50'}`} />
                                            <div className={`relative w-32 h-32 rounded-full border-2 flex items-center justify-center transition-all duration-300 ${uvx.agentSpeaking ? 'border-blue-400 bg-blue-400/10 shadow-[0_0_30px_rgba(59,130,246,0.5)]' : 'border-[var(--border-default)] bg-[var(--glass-bg)]'}`}>
                                                <Bot className={`w-16 h-16 transition-all duration-300 ${uvx.agentSpeaking ? 'text-blue-400 scale-110' : 'text-gray-500'}`} />
                                            </div>
                                            {uvx.agentSpeaking && (
                                                <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                                                    {[1, 2, 3, 4, 5].map(i => (
                                                        <div key={i} className="w-1 bg-blue-400 rounded-full animate-bounce" style={{ height: `${8 + (i % 3) * 6}px`, animationDelay: `${i * 0.1}s` }} />
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                        <div className="text-center space-y-2">
                                            <h3 className="text-xl font-bold text-[var(--text-primary)]">{uvx.agentSpeaking ? "Agent is speaking..." : "Listening..."}</h3>
                                            <p className="text-sm text-gray-500">Live voice test</p>
                                        </div>
                                        <div className="flex gap-4">
                                            <button onClick={uvx.toggleMute} className={`p-4 rounded-full border transition-all ${uvx.isMuted ? 'bg-red-500/10 border-red-500/50 text-red-500' : 'bg-[var(--glass-bg)] border-[var(--border-default)] text-gray-400 hover:bg-[var(--glass-bg-hover)]'}`}>
                                                {uvx.isMuted ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
                                            </button>
                                            <button onClick={uvx.leaveCall} className="p-4 rounded-full bg-red-600 text-white hover:bg-red-500 transition-all shadow-lg shadow-red-600/20">
                                                <PhoneOff className="w-6 h-6" />
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                                        {uvx.chatHistory.length === 0 && (
                                            <div className="flex flex-col items-center justify-center h-full text-gray-600 space-y-2">
                                                <Bot className="w-10 h-10 opacity-20" />
                                                <p className="text-sm">Start the conversation to test the agent</p>
                                            </div>
                                        )}
                                        {uvx.chatHistory.map((msg, i) => (
                                            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                                <div className={`max-w-[80%] rounded-lg px-4 py-3 text-sm ${msg.role === 'user'
                                                    ? 'bg-blue-600 text-white'
                                                    : msg.role === 'system'
                                                        ? 'bg-gray-800 text-gray-400 italic font-mono text-xs border border-[var(--border-subtle)]'
                                                        : 'bg-white/10 text-gray-200'
                                                    }`}>
                                                    {msg.content}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                <div className="p-4 border-t border-[var(--border-default)] bg-black/20">
                                    <div className="flex gap-2 items-center mb-4 px-2">
                                        <div className="flex-1 h-px bg-[var(--glass-bg)]" />
                                        <button
                                            onClick={uvx.isCalling ? uvx.leaveCall : uvx.startCall}
                                            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold transition-all ${uvx.isCalling ? 'bg-red-600 text-white animate-pulse' : 'bg-green-600/10 text-green-400 border border-green-500/20 hover:bg-green-600/20'}`}
                                        >
                                            {uvx.isCalling ? <PhoneOff className="w-4 h-4" /> : <Phone className="w-4 h-4" />}
                                            {uvx.isCalling ? "End call" : "Start test call"}
                                        </button>
                                        <div className="flex-1 h-px bg-[var(--glass-bg)]" />
                                    </div>
                                    <form onSubmit={sendMessage} className="flex gap-2">
                                        <input
                                            value={input}
                                            onChange={e => setInput(e.target.value)}
                                            placeholder="Type a message..."
                                            disabled={!uvx.isCalling}
                                            className="flex-1 bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-md px-4 py-2.5 text-white focus:outline-none focus:border-blue-500 disabled:opacity-50"
                                        />
                                        <button
                                            type="submit"
                                            disabled={!uvx.isCalling}
                                            className="p-2.5 bg-blue-600 text-white rounded-md hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600"
                                        >
                                            <Play className="w-5 h-5 fill-current" />
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
                                <h3 className="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2">
                                    <Book className="w-5 h-5 text-blue-400" />
                                    Knowledge Base
                                </h3>
                                <button
                                    onClick={() => setIsAddingKnowledge(true)}
                                    className="flex items-center gap-2 bg-blue-600/10 text-blue-400 border border-blue-500/20 px-4 py-2 rounded-md hover:bg-blue-600/20 transition-colors"
                                >
                                    <Plus className="w-4 h-4" />
                                    Add Document
                                </button>
                            </div>

                            <Card className="border-[var(--border-default)] bg-[#0f0f10]">
                                <CardContent className="p-0">
                                    <div className="divide-y divide-white/5">
                                        {knowledgeItems.length === 0 && !isAddingKnowledge && (
                                            <div className="p-12 text-center text-gray-500">
                                                <FileText className="w-12 h-12 mx-auto mb-4 opacity-10" />
                                                <p>No documents found. Add knowledge to improve agent accuracy.</p>
                                            </div>
                                        )}

                                        {isAddingKnowledge && (
                                            <div className="p-6 bg-blue-500/5 animate-in fade-in slide-in-from-top-4 duration-300">
                                                <div className="space-y-4">
                                                    <div>
                                                        <label className="block text-sm font-medium text-gray-400 mb-1">Document Title</label>
                                                        <input
                                                            value={newKnowledge.title}
                                                            onChange={e => setNewKnowledge({ ...newKnowledge, title: e.target.value })}
                                                            className="w-full bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-md px-3 py-2 text-white"
                                                            placeholder="e.g. Return Policy 2024"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="block text-sm font-medium text-gray-400 mb-1">Content (Knowledge Chunk)</label>
                                                        <textarea
                                                            value={newKnowledge.content}
                                                            onChange={e => setNewKnowledge({ ...newKnowledge, content: e.target.value })}
                                                            className="w-full bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-md px-3 py-2 text-white h-32"
                                                            placeholder="Paste document text here..."
                                                        />
                                                    </div>
                                                    <div className="flex gap-2 justify-end">
                                                        <button
                                                            onClick={() => setIsAddingKnowledge(false)}
                                                            className="px-4 py-2 text-sm text-gray-400"
                                                        >Cancel</button>
                                                        <button
                                                            onClick={handleAddKnowledge}
                                                            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md"
                                                        >Ingest Knowledge</button>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {knowledgeItems.map((item) => (
                                            <div key={item.id} className="p-4 flex items-start justify-between group hover:bg-[var(--glass-bg)]">
                                                <div className="flex-1">
                                                    <h4 className="font-medium text-white text-sm flex items-center gap-2">
                                                        <FileText className="w-3 h-3 text-gray-500" />
                                                        {item.title}
                                                    </h4>
                                                    <p className="text-xs text-gray-500 mt-1 line-clamp-2 leading-relaxed">
                                                        {item.content}
                                                    </p>
                                                </div>
                                                <button
                                                    onClick={() => handleDeleteKnowledge(item.id)}
                                                    className="p-2 text-gray-500 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Semantic Search Tester */}
                            <div className="mt-8 space-y-4">
                                <h4 className="text-sm font-bold text-gray-400 uppercase tracking-widest">RAG Query Tester</h4>
                                <div className="flex gap-2">
                                    <div className="relative flex-1">
                                        <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-500" />
                                        <input
                                            value={knowledgeSearch}
                                            onChange={e => setKnowledgeSearch(e.target.value)}
                                            onKeyDown={e => e.key === 'Enter' && runKnowledgeQuery(knowledgeSearch)}
                                            placeholder="Test semantic retrieval... (e.g. What is the return limit?)"
                                            className="w-full bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-full pl-10 pr-4 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-blue-500/50"
                                        />
                                    </div>
                                    <button
                                        onClick={() => runKnowledgeQuery(knowledgeSearch)}
                                        className="bg-zinc-800 text-white px-4 py-2 rounded-full text-sm font-medium hover:bg-zinc-700"
                                    >Test</button>
                                </div>

                                {queryResults.length > 0 && (
                                    <div className="space-y-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
                                        {queryResults.map((res, i) => (
                                            <div key={i} className="p-3 bg-green-500/5 border border-green-500/10 rounded-lg">
                                                <div className="flex justify-between items-center mb-1">
                                                    <span className="text-[10px] font-bold text-green-500 uppercase tracking-tighter">Match Score: {(res.score * 100).toFixed(1)}%</span>
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

                    {/* Placeholder Tabs */}
                    {['analytics', 'versions', 'policy'].includes(activeTab) && (
                        <div className="flex flex-col items-center justify-center h-[400px] text-gray-500 border border-dashed border-[var(--border-default)] rounded-xl">
                            <Activity className="w-10 h-10 mb-2 opacity-50" />
                            <p>This module is currently under development.</p>
                        </div>
                    )}
                </div>
            </div >
        </div >
    );
}

