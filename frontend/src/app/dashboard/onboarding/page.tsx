'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { CheckCircle2, PhoneOff, Phone, MicOff, Mic, Play, ArrowRight, Bot, Loader2, Sparkles, Wand2 } from 'lucide-react';
import api from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LogoIcon } from '@/components/Logo';
import { useLiveKitSession } from '@/hooks/useLiveKitSession';

const STEPS = [
    { id: 'welcome', title: 'Welcome' },
    { id: 'setup', title: 'Setup' },
    { id: 'test', title: 'Live Test' },
];

export default function OnboardingPage() {
    const router = useRouter();
    const [step, setStep] = useState(0);
    
    // Form State
    const [agentName, setAgentName] = useState('');
    const [channel, setChannel] = useState('web');
    const [description, setDescription] = useState('');
    
    // Generation State
    const [isGenerating, setIsGenerating] = useState(false);
    const [agent, setAgent] = useState<any>(null);

    // LiveKit Session (initially empty string ID until agent generated)
    const uvx = useLiveKitSession(agent?.id || "", "en-IN", "auto");
    const [input, setInput] = useState("");

    const handleGenerate = async () => {
        if (!agentName.trim() || !description.trim()) return;
        setIsGenerating(true);
        try {
            const data = await api.post('/agents/quickstart', {
                name: agentName,
                channel: channel,
                description: description
            });
            setAgent(data);
            setStep(2); // Move to test step
        } catch (e) {
            console.error("Failed to generate agent", e);
        } finally {
            setIsGenerating(false);
        }
    };

    const sendMessage = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || !uvx.isCalling) return;
        uvx.sendText(input);
        setInput("");
    };

    return (
        <div className="min-h-screen bg-background flex flex-col p-6">
            <div className="w-full max-w-2xl mx-auto flex-1 flex flex-col">
                {/* Progress Header */}
                <div className="mb-8 flex items-center justify-between shrink-0 mt-8">
                    <div className="flex items-center gap-2">
                        <LogoIcon className="size-7 text-primary" />
                        <span className="text-sm font-bold">Voise <span className="text-primary">AI</span></span>
                    </div>
                    <div className="flex items-center gap-2">
                        {STEPS.map((s, i) => (
                            <div key={s.id} className="flex items-center gap-2">
                                <div className={`size-7 rounded-full flex items-center justify-center text-[10px] font-bold transition-all ${
                                    i < step ? 'bg-primary text-primary-foreground' :
                                    i === step ? 'bg-primary/20 text-primary border-2 border-primary' :
                                    'bg-muted text-muted-foreground'
                                }`}>
                                    {i < step ? <CheckCircle2 className="size-3.5" /> : i + 1}
                                </div>
                                {i < STEPS.length - 1 && (
                                    <div className={`h-px w-8 transition-all ${i < step ? 'bg-primary' : 'bg-border'}`} />
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Main Content Card */}
                <Card className="border-border/50 shadow-2xl flex-1 flex flex-col bg-card/80 backdrop-blur-xl">
                    <CardContent className="p-8 flex-1 flex flex-col justify-center">
                        
                        {/* Step 0: Welcome */}
                        {step === 0 && (
                            <div className="text-center space-y-6 animate-in fade-in duration-500">
                                <div className="size-20 rounded-3xl bg-primary/10 flex items-center justify-center mx-auto shadow-inner shadow-primary/20">
                                    <Sparkles className="size-10 text-primary" />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold text-foreground">Zero to Bot in 2 minutes.</h2>
                                    <p className="text-sm text-muted-foreground mt-3 max-w-md mx-auto leading-relaxed">
                                        Describe your use case in plain English. Voise AI will automatically provision an agent, generate its brain, and put you on a live call with it.
                                    </p>
                                </div>
                                <Button onClick={() => setStep(1)} size="lg" className="rounded-xl px-8 font-semibold shadow-lg shadow-primary/20 gap-2">
                                    Let's Build <ArrowRight className="size-4" />
                                </Button>
                            </div>
                        )}

                        {/* Step 1: Form */}
                        {step === 1 && (
                            <div className="space-y-6 animate-in fade-in duration-300 w-full max-w-md mx-auto">
                                <div className="text-center pb-4">
                                    <h2 className="text-xl font-bold text-foreground">Describe your AI Agent</h2>
                                    <p className="text-xs text-muted-foreground mt-1">We'll handle the prompting and setup.</p>
                                </div>
                                
                                <div className="space-y-4">
                                    <div className="space-y-1.5">
                                        <Label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Agent Name</Label>
                                        <Input
                                            value={agentName}
                                            onChange={e => setAgentName(e.target.value)}
                                            placeholder="e.g. Sales SDR"
                                            className="bg-muted/50 border-border"
                                            autoFocus
                                        />
                                    </div>
                                    <div className="space-y-1.5">
                                        <Label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Channel</Label>
                                        <div className="flex gap-2">
                                            {['web', 'inbound', 'outbound'].map(c => (
                                                <button
                                                    key={c}
                                                    type="button"
                                                    onClick={() => setChannel(c)}
                                                    className={`flex-1 py-2 rounded-lg border text-xs font-semibold capitalize transition-all ${channel === c ? 'bg-primary text-white border-primary shadow-md' : 'bg-muted border-border text-muted-foreground hover:bg-muted/80'}`}
                                                >
                                                    {c}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="space-y-1.5">
                                        <Label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Use Case (5-10 words)</Label>
                                        <textarea
                                            value={description}
                                            onChange={e => setDescription(e.target.value)}
                                            rows={3}
                                            placeholder="Call leads who abandoned cart and offer a 10% discount."
                                            className="w-full rounded-lg bg-muted/50 border border-border px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                                        />
                                    </div>
                                </div>

                                <Button 
                                    onClick={handleGenerate} 
                                    disabled={!agentName || !description || isGenerating}
                                    className="w-full gap-2 rounded-xl py-6 text-sm"
                                >
                                    {isGenerating ? <Loader2 className="size-4 animate-spin" /> : <Wand2 className="size-4" />}
                                    {isGenerating ? 'Provisioning AI Brain...' : 'Generate & Test'}
                                </Button>
                            </div>
                        )}

                        {/* Step 2: Live Test (LiveKit integration) */}
                        {step === 2 && agent && (
                            <div className="flex-1 flex flex-col animate-in zoom-in-95 duration-500">
                                <div className="text-center mb-6">
                                    <h2 className="text-xl font-bold text-foreground">Meet {agent.name}</h2>
                                    <p className="text-xs text-muted-foreground mt-1">Your AI is ready. Start the web call to test its brain.</p>
                                </div>

                                <div className="flex-1 bg-muted/30 border border-border rounded-2xl flex flex-col overflow-hidden relative shadow-inner">
                                    {/* Call Status Header */}
                                    <div className="p-3 border-b border-border/50 flex justify-between items-center bg-background/50 backdrop-blur">
                                        <div className="flex items-center gap-2">
                                            <div className={`size-2 rounded-full ${uvx.isConnected ? "bg-green-500" : "bg-red-500"} ${uvx.isCalling ? "animate-pulse" : ""}`} />
                                            <span className="text-xs font-semibold text-muted-foreground">
                                                {uvx.isConnected ? "Engine Connected" : "Connecting..."}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Call UI */}
                                    <div className="flex-1 flex flex-col items-center justify-center p-6 relative">
                                        <div className="relative">
                                            <div className={`absolute -inset-8 bg-primary/20 rounded-full blur-2xl transition-all duration-700 ${uvx.agentSpeaking ? 'scale-150 opacity-100' : 'scale-100 opacity-0'}`} />
                                            <div className={`relative size-32 rounded-full border-4 flex items-center justify-center transition-all duration-300 z-10 ${uvx.isCalling ? (uvx.agentSpeaking ? 'border-primary bg-primary/10' : 'border-primary/50 bg-background') : 'border-border bg-muted'}`}>
                                                <Bot className={`size-14 transition-all duration-300 ${uvx.isCalling ? 'text-primary' : 'text-muted-foreground'} ${uvx.agentSpeaking ? 'scale-110' : ''}`} />
                                            </div>
                                            {uvx.agentSpeaking && (
                                                <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 flex gap-1 z-20 bg-background/80 px-2 py-1 rounded-full border border-border backdrop-blur">
                                                    {[1, 2, 3].map(i => (
                                                        <div key={i} className="w-1.5 bg-primary rounded-full animate-bounce" style={{ height: `${6 + (i % 2) * 4}px`, animationDelay: `${i * 0.15}s` }} />
                                                    ))}
                                                </div>
                                            )}
                                        </div>

                                        <div className="mt-8 text-center h-12">
                                            {!uvx.isCalling ? (
                                                <p className="text-sm font-medium text-muted-foreground">Ready for testing</p>
                                            ) : uvx.agentSpeaking ? (
                                                <p className="text-lg font-bold text-primary animate-pulse">Speaking...</p>
                                            ) : (
                                                <p className="text-sm font-medium text-foreground">Listening for your voice...</p>
                                            )}
                                        </div>
                                        
                                        <div className="mt-8 flex gap-4">
                                            {!uvx.isCalling ? (
                                                <Button 
                                                    onClick={uvx.startCall}
                                                    size="lg" 
                                                    className="rounded-full px-8 bg-green-600 hover:bg-green-500 text-white gap-2 shadow-lg shadow-green-900/20"
                                                >
                                                    <Phone className="size-4" /> Start Web Call
                                                </Button>
                                            ) : (
                                                <>
                                                    <Button 
                                                        onClick={uvx.toggleMute}
                                                        variant="outline"
                                                        size="icon"
                                                        className={`rounded-full size-14 ${uvx.isMuted ? 'border-red-500/50 bg-red-500/10 text-red-500 hover:bg-red-500/20' : 'border-border'}`}
                                                    >
                                                        {uvx.isMuted ? <MicOff className="size-5" /> : <Mic className="size-5" />}
                                                    </Button>
                                                    <Button 
                                                        onClick={uvx.leaveCall}
                                                        size="icon"
                                                        className="rounded-full size-14 bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-900/20"
                                                    >
                                                        <PhoneOff className="size-5" />
                                                    </Button>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                    
                                    {/* Text fallback */}
                                    <div className="p-3 border-t border-border/50 bg-background/50">
                                        <form onSubmit={sendMessage} className="flex gap-2">
                                            <Input
                                                value={input}
                                                onChange={e => setInput(e.target.value)}
                                                placeholder="Or type a message to the agent..."
                                                disabled={!uvx.isCalling}
                                                className="bg-background border-border"
                                            />
                                            <Button type="submit" disabled={!uvx.isCalling} size="icon" className="shrink-0">
                                                <Play className="size-4 fill-current" />
                                            </Button>
                                        </form>
                                    </div>
                                </div>

                                <div className="mt-6 text-center">
                                    <Button variant="ghost" onClick={() => router.push(`/dashboard/agents/${agent.id}`)} className="text-xs">
                                        Go to Agent Dashboard <ArrowRight className="size-3 ml-1" />
                                    </Button>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
