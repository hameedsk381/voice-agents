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
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Voice Lab</h2>
                    <p className="text-gray-400">Design unique voices or clone existing ones for your agents.</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => setActiveTab("design")}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${activeTab === 'design' ? 'bg-purple-600 text-white' : 'bg-white/5 text-gray-300 hover:bg-white/10'}`}
                    >
                        <Wand2 className="w-4 h-4" />
                        Design Voice
                    </button>
                    <button
                        onClick={() => setActiveTab("clone")}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${activeTab === 'clone' ? 'bg-blue-600 text-white' : 'bg-white/5 text-gray-300 hover:bg-white/10'}`}
                    >
                        <Mic className="w-4 h-4" />
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
        if (!confirm("Are you sure you want to delete this voice?")) return;
        try {
            await api.delete(`/voices/${id}`);
            onDelete();
        } catch (e) {
            console.error(e);
            alert("Failed to delete voice");
        }
    };

    if (loading) return <div className="text-white">Loading voices...</div>;

    return (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {voices.map((voice) => (
                <Card key={voice.id} className="bg-[#0f0f10] border-white/10 group">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-base font-semibold text-white">{voice.name}</CardTitle>
                        {voice.type === 'cloned' && (
                            <button onClick={() => handleDelete(voice.id)} className="text-gray-500 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity">
                                <Trash2 className="w-4 h-4" />
                            </button>
                        )}
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center gap-2 mt-2">
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${voice.type === 'standard' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : 'bg-purple-500/10 text-purple-400 border-purple-500/20'}`}>
                                {voice.type === 'standard' ? 'Standard' : 'Cloned'}
                            </span>
                            <span className="text-xs text-gray-500 font-mono">{voice.id.slice(0, 8)}...</span>
                        </div>
                    </CardContent>
                </Card>
            ))}
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

            // Use raw fetch for form data if api wrapper doesn't support it
            const token = localStorage.getItem('access_token');
            const res = await fetch("http://localhost:8001/api/v1/voices/design", {
                method: "POST",
                headers: token ? { "Authorization": `Bearer ${token}` } : {},
                body: form
            });

            if (!res.ok) throw new Error("Design failed");

            const data = await res.json();
            setAudio(data.audio_base64);
        } catch (err) {
            console.error(err);
            alert("Failed to generate voice preview");
        } finally {
            setGenerating(false);
        }
    };

    return (
        <Card className="bg-[#0f0f10] border-white/10 max-w-2xl">
            <CardHeader>
                <CardTitle className="text-white">Voice Designer</CardTitle>
                <CardDescription>Describe a voice and generate a preview using Qwen-TTS.</CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleDesign} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Voice Description (Prompt)</label>
                        <textarea
                            required
                            value={instruct}
                            onChange={e => setInstruct(e.target.value)}
                            placeholder="e.g., A deep, raspy elderly male voice with a slow pace and wisdom."
                            rows={3}
                            className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Sample Text</label>
                        <input
                            value={text}
                            onChange={e => setText(e.target.value)}
                            className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                        />
                    </div>

                    <div className="flex items-center gap-4">
                        <button
                            type="submit"
                            disabled={generating}
                            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-md font-medium disabled:opacity-50"
                        >
                            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
                            {generating ? "Generating..." : "Generate Preview"}
                        </button>
                        <button type="button" onClick={onBack} className="text-gray-400 hover:text-white">Cancel</button>
                    </div>
                </form>

                {audio && (
                    <div className="mt-8 p-4 bg-white/5 rounded-lg border border-white/10">
                        <h4 className="text-sm font-medium text-white mb-2">Preview</h4>
                        <audio controls src={`data:audio/wav;base64,${audio}`} className="w-full" />
                        <p className="text-xs text-gray-500 mt-2">
                            Note: This is a generated sample. To save this voice, you would verify it and then register it (Not implemented in this demo).
                        </p>
                    </div>
                )}
            </CardContent>
        </Card>
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

            const token = localStorage.getItem('access_token');
            const res = await fetch("http://localhost:8001/api/v1/voices/register", {
                method: "POST",
                headers: token ? { "Authorization": `Bearer ${token}` } : {},
                body: form
            });

            if (!res.ok) throw new Error("Cloning failed");

            alert("Voice cloned successfully!");
            onBack();
        } catch (err) {
            console.error(err);
            alert("Failed to clone voice");
        } finally {
            setCloning(false);
        }
    };

    return (
        <Card className="bg-[#0f0f10] border-white/10 max-w-2xl">
            <CardHeader>
                <CardTitle className="text-white">Clone Voice</CardTitle>
                <CardDescription>Upload a clear audio sample (10-30s) to create a voice clone.</CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleClone} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Voice Name</label>
                        <input
                            required
                            value={name}
                            onChange={e => setName(e.target.value)}
                            placeholder="e.g. Founder Voice"
                            className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Reference Text (Transcript)</label>
                        <textarea
                            required
                            value={refText}
                            onChange={e => setRefText(e.target.value)}
                            placeholder="What was said in the audio clip? Accurate text improves cloning quality."
                            rows={3}
                            className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Audio File (WAV/MP3)</label>
                        <div className="border-2 border-dashed border-white/10 rounded-lg p-6 flex flex-col items-center justify-center text-center hover:border-blue-500/50 transition-colors">
                            <Upload className="w-8 h-8 text-gray-500 mb-2" />
                            <input
                                type="file"
                                accept="audio/*"
                                onChange={e => setFile(e.target.files?.[0] || null)}
                                className="block w-full text-sm text-gray-400
                                  file:mr-4 file:py-2 file:px-4
                                  file:rounded-full file:border-0
                                  file:text-sm file:font-semibold
                                  file:bg-blue-600 file:text-white
                                  hover:file:bg-blue-500
                                "
                            />
                        </div>
                    </div>

                    <div className="flex items-center gap-4 mt-6">
                        <button
                            type="submit"
                            disabled={cloning || !file}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-md font-medium disabled:opacity-50"
                        >
                            {cloning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mic className="w-4 h-4" />}
                            {cloning ? "Cloning..." : "Clone Voice"}
                        </button>
                        <button type="button" onClick={onBack} className="text-gray-400 hover:text-white">Cancel</button>
                    </div>
                </form>
            </CardContent>
        </Card>
    );
}
