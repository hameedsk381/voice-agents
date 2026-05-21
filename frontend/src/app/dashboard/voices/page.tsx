"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Play, Mic, Plus, Trash2, Wand2, Loader2, Upload } from "lucide-react";

interface Voice {
    id: string;
    name: string;
    type: string;
}

export default function VoiceLabPage() {
    const [voices, setVoices] = useState<Voice[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState("gallery"); // gallery, design, clone

    useEffect(() => {
        loadVoices();
    }, []);

    const loadVoices = async () => {
        try {
            const data = await api.get('/voices/');
            setVoices(data);
        } catch (error) {
            console.error("Failed to load voices", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 select-none">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                        Voice <span className="text-gradient-brand">Lab</span>
                    </h2>
                    <p className="text-xs text-[var(--text-secondary)] mt-1">Design unique text-to-speech presets or clone custom reference samples.</p>
                </div>
                <div className="flex gap-2.5">
                    {activeTab !== "gallery" && (
                        <button
                            onClick={() => setActiveTab("gallery")}
                            className="px-4 py-2 text-xs font-semibold rounded-xl bg-[var(--bg-overlay)] border border-[var(--border-default)] hover:bg-[var(--glass-bg-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all duration-300"
                        >
                            Back to Gallery
                        </button>
                    )}
                    <button
                        onClick={() => setActiveTab("design")}
                        className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl transition-all duration-300 ${
                            activeTab === 'design' 
                                ? 'bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white shadow-lg' 
                                : 'bg-[var(--bg-overlay)] border border-[var(--border-default)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--glass-bg-hover)]'
                        }`}
                    >
                        <Wand2 className="w-3.5 h-3.5" />
                        Design Voice
                    </button>
                    <button
                        onClick={() => setActiveTab("clone")}
                        className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl transition-all duration-300 ${
                            activeTab === 'clone' 
                                ? 'bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white shadow-lg' 
                                : 'bg-[var(--bg-overlay)] border border-[var(--border-default)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--glass-bg-hover)]'
                        }`}
                    >
                        <Mic className="w-3.5 h-3.5" />
                        Clone Voice
                    </button>
                </div>
            </div>

            {/* TAB CONTENT */}
            <div className="grid gap-6">
                {activeTab === "gallery" && (
                    <VoiceGallery voices={voices} loading={loading} onDelete={loadVoices} />
                )}
                {activeTab === "design" && (
                    <VoiceDesigner onBack={() => setActiveTab("gallery")} />
                )}
                {activeTab === "clone" && (
                    <VoiceCloner onBack={() => { setActiveTab("gallery"); loadVoices(); }} />
                )}
            </div>
        </div>
    );
}

function VoiceGallery({ voices, loading, onDelete }: { voices: Voice[], loading: boolean, onDelete: () => void }) {
    const handleDelete = async (id: string) => {
        if (!confirm("Are you sure you want to delete this voice preset?")) return;
        try {
            await api.delete(`/voices/${id}`);
            onDelete();
        } catch (e) {
            console.error(e);
            alert("Failed to delete voice preset");
        }
    };

    if (loading) {
        return (
            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="glass-card h-32 animate-pulse" />
                ))}
            </div>
        );
    }

    return (
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {voices.map((voice) => (
                <div key={voice.id} className="glass-card p-5 group flex flex-col justify-between hover:border-[var(--border-active)] transition-all relative">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-bold text-[var(--text-primary)]">{voice.name}</h3>
                        {voice.type === 'cloned' && (
                            <button 
                                onClick={() => handleDelete(voice.id)} 
                                className="text-[var(--text-tertiary)] hover:text-[var(--accent-rose)] opacity-0 group-hover:opacity-100 transition-opacity p-1"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        )}
                    </div>
                    <div className="flex items-center justify-between">
                        <span className={`px-2.5 py-0.5 rounded-full text-[9px] font-bold uppercase border ${
                            voice.type === 'standard' 
                                ? 'bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] border-[var(--accent-blue)]/20' 
                                : 'bg-[var(--accent-purple)]/10 text-[var(--accent-purple)] border-[var(--accent-purple)]/20'
                        }`}>
                            {voice.type === 'standard' ? 'Standard' : 'Cloned'}
                        </span>
                        <span className="text-[10px] text-[var(--text-tertiary)] font-mono">ID: {voice.id.slice(0, 8)}...</span>
                    </div>
                </div>
            ))}

            {voices.length === 0 && (
                <div className="col-span-full py-16 text-center text-[var(--text-secondary)] border border-dashed border-[var(--border-default)] rounded-2xl bg-[var(--bg-overlay)]">
                    <Mic className="w-8 h-8 mx-auto mb-3 text-[var(--text-tertiary)]" />
                    <p className="text-sm font-semibold">No voice profiles registered</p>
                    <p className="text-xs text-[var(--text-tertiary)] mt-1">Design or clone a brand voice for your agents.</p>
                </div>
            )}
        </div>
    );
}

function VoiceDesigner({ onBack }: { onBack: () => void }) {
    const [instruct, setInstruct] = useState("");
    const [text, setText] = useState("Hello, this is a distinct voice created just for you.");
    const [audio, setAudio] = useState<string | null>(null);
    const [generating, setGenerating] = useState(false);

    const handleDesign = async (e: React.FormEvent) => {
        e.preventDefault();
        setGenerating(true);
        setAudio(null);

        try {
            const form = new FormData();
            form.append("text", text);
            form.append("instruct", instruct);

            const data = await api.postFormData('/voices/design', form);
            setAudio(data.audio_base64);
        } catch (err) {
            console.error(err);
            alert("Failed to generate voice preview");
        } finally {
            setGenerating(false);
        }
    };

    return (
        <div className="glass-card p-6 md:p-8 max-w-2xl relative overflow-hidden">
            <div className="pb-5 border-b border-[var(--border-subtle)] mb-6">
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Voice Prompt Design</h3>
                <p className="text-[10px] text-[var(--text-secondary)] mt-1">Describe tone, pace, and style to preview how your agent will sound.</p>
            </div>

            <form onSubmit={handleDesign} className="space-y-5">
                <div className="space-y-1.5">
                    <label className="block text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Voice Prompt Description</label>
                    <textarea
                        required
                        value={instruct}
                        onChange={e => setInstruct(e.target.value)}
                        placeholder="e.g., A deep, raspy elderly male voice with a slow pace and wisdom."
                        rows={3}
                        className="w-full bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl px-3 py-2.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent-cyan)] focus:ring-4 focus:ring-[var(--accent-cyan)]/5 transition-all resize-none"
                    />
                </div>
                <div className="space-y-1.5">
                    <label className="block text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Sample Synthesis Text</label>
                    <input
                        value={text}
                        onChange={e => setText(e.target.value)}
                        className="w-full bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl px-3 py-2.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent-cyan)] focus:ring-4 focus:ring-[var(--accent-cyan)]/5 transition-all"
                    />
                </div>

                <div className="flex items-center gap-4 pt-4 border-t border-[var(--border-subtle)]">
                    <button
                        type="submit"
                        disabled={generating}
                        className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50 hover:-translate-y-0.5 active:scale-98"
                    >
                        {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
                        {generating ? "Generating..." : "Generate Preview"}
                    </button>
                    <button type="button" onClick={onBack} className="text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">Cancel</button>
                </div>
            </form>

            {audio && (
                <div className="mt-8 p-5 bg-[var(--bg-overlay)] rounded-xl border border-[var(--border-subtle)] animate-fade">
                    <h4 className="text-xs font-bold text-[var(--text-primary)] mb-3">Generated Auditory Sample</h4>
                    <audio controls src={`data:audio/wav;base64,${audio}`} className="w-full" />
                    <p className="text-[10px] text-[var(--text-tertiary)] italic mt-3 leading-relaxed">
                        Verify this generated preset clip before mapping it to target voice agent templates.
                    </p>
                </div>
            )}
        </div>
    );
}

function VoiceCloner({ onBack }: { onBack: () => void }) {
    const [name, setName] = useState("");
    const [refText, setRefText] = useState("");
    const [file, setFile] = useState<File | null>(null);
    const [cloning, setCloning] = useState(false);

    const handleClone = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;

        setCloning(true);
        try {
            const form = new FormData();
            form.append("name", name);
            form.append("ref_text", refText);
            form.append("file", file);

            await api.postFormData('/voices/register', form);

            alert("Voice preset cloned successfully!");
            onBack();
        } catch (err) {
            console.error(err);
            alert("Failed to clone voice preset");
        } finally {
            setCloning(false);
        }
    };

    return (
        <div className="glass-card p-6 md:p-8 max-w-2xl relative overflow-hidden">
            <div className="pb-5 border-b border-[var(--border-subtle)] mb-6">
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Voice Reference Cloner</h3>
                <p className="text-[10px] text-[var(--text-secondary)] mt-1">Upload a clean audio sample (10-30s) to create an immediate voice clone profile.</p>
            </div>

            <form onSubmit={handleClone} className="space-y-5">
                <div className="space-y-1.5">
                    <label className="block text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Voice Profile Name</label>
                    <input
                        required
                        value={name}
                        onChange={e => setName(e.target.value)}
                        placeholder="e.g. Founder Corporate Preset"
                        className="w-full bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl px-3 py-2.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent-cyan)] focus:ring-4 focus:ring-[var(--accent-cyan)]/5 transition-all"
                    />
                </div>
                <div className="space-y-1.5">
                    <label className="block text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Reference Audio Transcript</label>
                    <textarea
                        required
                        value={refText}
                        onChange={e => setRefText(e.target.value)}
                        placeholder="Accurately input what was said in the audio reference sample clip..."
                        rows={3}
                        className="w-full bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl px-3 py-2.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent-cyan)] focus:ring-4 focus:ring-[var(--accent-cyan)]/5 transition-all resize-none"
                    />
                </div>
                <div className="space-y-1.5">
                    <label className="block text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Upload Reference File (WAV/MP3)</label>
                    <div className="border-2 border-dashed border-[var(--border-default)] bg-[var(--bg-overlay)] rounded-xl p-6 flex flex-col items-center justify-center text-center hover:border-[var(--accent-cyan)]/50 transition-colors select-none">
                        <Upload className="w-7 h-7 text-[var(--text-tertiary)] mb-2" />
                        <input
                            type="file"
                            accept="audio/*"
                            onChange={e => setFile(e.target.files?.[0] || null)}
                            className="block w-full text-xs text-[var(--text-secondary)] cursor-pointer
                              file:mr-4 file:py-1.5 file:px-4
                              file:rounded-full file:border-0
                              file:text-xs file:font-semibold
                              file:bg-[var(--glass-bg)] file:text-[var(--text-primary)]
                              file:border file:border-[var(--border-default)]
                              hover:file:bg-white/[0.08]"
                        />
                    </div>
                </div>

                <div className="flex items-center gap-4 pt-6 border-t border-[var(--border-subtle)]">
                    <button
                        type="submit"
                        disabled={cloning || !file}
                        className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50 hover:-translate-y-0.5 active:scale-98"
                    >
                        {cloning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mic className="w-4 h-4" />}
                        {cloning ? "Cloning..." : "Clone Voice"}
                    </button>
                    <button type="button" onClick={onBack} className="text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">Cancel</button>
                </div>
            </form>
        </div>
    );
}
