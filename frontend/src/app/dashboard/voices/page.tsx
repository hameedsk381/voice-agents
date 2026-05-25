"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { languageDisplay } from "@/lib/languages";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Play, Mic, Plus, Trash2, Wand2, Loader2, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Voice {
    id: string;
    name: string;
    type: string;
    primaryLanguage?: string;
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
                    <h2 className="text-2xl font-semibold tracking-tight text-foreground">
                        Voice <span className="text-primary">Lab</span>
                    </h2>
                    <p className="text-sm text-muted-foreground mt-1">Design unique text-to-speech presets or clone custom reference samples.</p>
                </div>
                <div className="flex items-center gap-2">
                    {activeTab !== "gallery" && (
                        <Button
                            type="button"
                            variant="ghost"
                            onClick={() => setActiveTab("gallery")}
                            className="rounded-xl text-xs font-semibold"
                        >
                            Back to Gallery
                        </Button>
                    )}
                    <Button
                        type="button"
                        onClick={() => setActiveTab("design")}
                        variant={activeTab === 'design' ? 'default' : 'secondary'}
                        className="flex items-center gap-2 text-xs font-semibold rounded-xl"
                    >
                        <Wand2 className="size-3.5" />
                        Design Voice
                    </Button>
                    <Button
                        type="button"
                        onClick={() => setActiveTab("clone")}
                        variant={activeTab === 'clone' ? 'default' : 'secondary'}
                        className="flex items-center gap-2 text-xs font-semibold rounded-xl"
                    >
                        <Mic className="size-3.5" />
                        Clone Voice
                    </Button>
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
                    <Card key={i} className="h-32 animate-pulse bg-muted/50" />
                ))}
            </div>
        );
    }

    const grouped = voices.reduce<Record<string, Voice[]>>((acc, v) => {
        const lang = v.primaryLanguage || "unknown";
        if (!acc[lang]) acc[lang] = [];
        acc[lang].push(v);
        return acc;
    }, {});

    const sortedLangs = Object.keys(grouped).sort();

    if (voices.length === 0) {
        return (
            <Card className="col-span-full border-dashed">
                <CardContent className="py-16 text-center text-muted-foreground">
                    <Mic className="size-10 mx-auto mb-4 text-primary" />
                    <p className="text-sm font-semibold text-foreground">No voice profiles registered</p>
                    <p className="text-xs text-muted-foreground mt-1">Design or clone a brand voice for your agents.</p>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="space-y-8">
            {sortedLangs.map((lang) => (
                <div key={lang} className="space-y-3">
                    <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        {languageDisplay(lang)}
                        <span className="ml-2 font-normal text-muted-foreground/60">({grouped[lang].length})</span>
                    </h3>
                    <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                        {grouped[lang].map((voice) => (
                            <Card key={voice.id} className="hover:shadow-md transition-all hover:border-primary/50 flex flex-col justify-between p-5 relative group min-h-[120px]">
                                <div className="flex items-start justify-between mb-4">
                                    <h3 className="text-sm font-semibold text-foreground truncate max-w-[150px]">{voice.name}</h3>
                                    {voice.type === 'cloned' && (
                                        <Button 
                                            type="button"
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => handleDelete(voice.id)} 
                                            className="text-muted-foreground hover:text-destructive h-8 w-8 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                                        >
                                            <Trash2 className="size-4" />
                                        </Button>
                                    )}
                                </div>
                                <div className="flex items-center justify-between mt-auto">
                                    <span className={`px-2.5 py-0.5 rounded-full text-[9px] font-semibold uppercase border ${
                                        voice.type === 'standard' 
                                            ? 'bg-primary/10 text-primary border-primary/20' 
                                            : 'bg-accent/10 text-accent-foreground border-accent/20 dark:text-accent'
                                    }`}>
                                        {voice.type === 'standard' ? 'Standard' : 'Cloned'}
                                    </span>
                                    <span className="text-[10px] text-muted-foreground font-mono">ID: {voice.id.slice(0, 8)}...</span>
                                </div>
                            </Card>
                        ))}
                    </div>
                </div>
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
        <Card className="max-w-2xl">
            <CardHeader>
                <CardTitle className="text-base font-semibold">Voice Prompt Design</CardTitle>
                <CardDescription className="text-xs">
                    Describe tone, pace, and style to preview how your agent will sound.
                </CardDescription>
            </CardHeader>

            <form onSubmit={handleDesign}>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="voice-prompt-description" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Voice Prompt Description</Label>
                        <textarea
                            id="voice-prompt-description"
                            required
                            value={instruct}
                            onChange={e => setInstruct(e.target.value)}
                            placeholder="e.g., A deep, raspy elderly male voice with a slow pace and wisdom."
                            rows={3}
                            className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="sample-synthesis-text" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Sample Synthesis Text</Label>
                        <Input
                            id="sample-synthesis-text"
                            value={text}
                            onChange={e => setText(e.target.value)}
                            className="rounded-xl"
                        />
                    </div>
                </CardContent>

                <CardContent className="flex items-center gap-3 pt-4 border-t border-border/50">
                    <Button
                        type="submit"
                        disabled={generating}
                        className="flex items-center gap-2 rounded-xl text-xs font-semibold"
                    >
                        {generating ? <Loader2 className="size-4 animate-spin" /> : <Wand2 className="size-4" />}
                        {generating ? "Generating…" : "Generate Preview"}
                    </Button>
                    <Button type="button" variant="ghost" onClick={onBack} className="text-xs font-semibold rounded-xl">Cancel</Button>
                </CardContent>
            </form>

            {audio && (
                <CardContent className="mt-4 p-5 bg-muted/40 rounded-xl border border-border/50 animate-fade space-y-3">
                    <h4 className="text-xs font-semibold text-foreground">Generated Auditory Sample</h4>
                    <audio controls src={`data:audio/wav;base64,${audio}`} className="w-full" />
                    <p className="text-[10px] text-muted-foreground italic leading-relaxed">
                        Verify this generated preset clip before mapping it to target voice agent templates.
                    </p>
                </CardContent>
            )}
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
        <Card className="max-w-2xl">
            <CardHeader>
                <CardTitle className="text-base font-semibold">Voice Reference Cloner</CardTitle>
                <CardDescription className="text-xs">
                    Upload a clean audio sample (10-30s) to create an immediate voice clone profile.
                </CardDescription>
            </CardHeader>

            <form onSubmit={handleClone}>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="voice-profile-name" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Voice Profile Name</Label>
                        <Input
                            id="voice-profile-name"
                            required
                            value={name}
                            onChange={e => setName(e.target.value)}
                            placeholder="e.g. Founder Corporate Preset"
                            className="rounded-xl"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="reference-audio-transcript" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Reference Audio Transcript</Label>
                        <textarea
                            id="reference-audio-transcript"
                            required
                            value={refText}
                            onChange={e => setRefText(e.target.value)}
                            placeholder="Accurately input what was said in the audio reference sample clip…"
                            rows={3}
                            className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="voice-reference-file" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Upload Reference File (WAV/MP3)</Label>
                        <div className="border-2 border-dashed border-border bg-muted/40 rounded-xl p-6 flex flex-col items-center justify-center text-center hover:border-primary/50 transition-colors select-none">
                            <Upload className="size-7 text-muted-foreground mb-2 text-primary" />
                            <input
                                id="voice-reference-file"
                                type="file"
                                accept="audio/*"
                                onChange={e => setFile(e.target.files?.[0] || null)}
                                className="block w-full text-xs text-muted-foreground cursor-pointer
                                  file:mr-4 file:py-1.5 file:px-4
                                  file:rounded-full file:border-0
                                  file:text-xs file:font-semibold
                                  file:bg-muted file:text-foreground
                                  file:border file:border-border
                                  hover:file:bg-white/[0.08]"
                            />
                        </div>
                    </div>
                </CardContent>

                <CardContent className="flex items-center gap-3 pt-6 border-t border-border/50">
                    <Button
                        type="submit"
                        disabled={cloning || !file}
                        className="flex items-center gap-2 rounded-xl text-xs font-semibold"
                    >
                        {cloning ? <Loader2 className="size-4 animate-spin" /> : <Mic className="size-4" />}
                        {cloning ? "Cloning…" : "Clone Voice"}
                    </Button>
                    <Button type="button" variant="ghost" onClick={onBack} className="text-xs font-semibold rounded-xl">Cancel</Button>
                </CardContent>
            </form>
        </Card>
    );
}
