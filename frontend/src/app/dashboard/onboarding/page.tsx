'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { CheckCircle2, ArrowRight, ArrowLeft, Loader2, Phone, Sparkles, Bot, Building2 } from 'lucide-react';
import { fetchMyOrganization, updateMyOrganization, completeOnboarding } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LogoIcon } from '@/components/Logo';

const STEPS = [
    { id: 'welcome', title: 'Welcome' },
    { id: 'workspace', title: 'Workspace' },
    { id: 'next-steps', title: 'Next Steps' },
    { id: 'done', title: 'Done' },
];

export default function OnboardingPage() {
    const router = useRouter();
    const [step, setStep] = useState(0);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [orgName, setOrgName] = useState('');
    const [selectedPaths, setSelectedPaths] = useState<string[]>([]);
    const [showToast, setShowToast] = useState(false);
    const [toastMessage, setToastMessage] = useState('');

    useEffect(() => {
        const init = async () => {
            try {
                const org = await fetchMyOrganization();
                setOrgName(org.name || '');
                if (org.settings?.onboarding_completed) {
                    router.push('/dashboard');
                    return;
                }
            } catch {
                // offline / no org — let onboarding continue
            }
            setLoading(false);
        };
        init();
    }, [router]);

    const handleFinish = async () => {
        setSaving(true);
        try {
            if (orgName.trim()) {
                await updateMyOrganization({ name: orgName.trim() });
            }
            await completeOnboarding();
            router.push('/dashboard');
        } catch {
            setToastMessage('Something went wrong — try again');
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
        } finally {
            setSaving(false);
        }
    };

    const togglePath = (path: string) => {
        setSelectedPaths(prev =>
            prev.includes(path) ? prev.filter(p => p !== path) : [...prev, path]
        );
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <Loader2 className="size-6 animate-spin text-muted-foreground" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-6">
            {showToast && (
                <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-4 bg-green-500/10 border border-green-500/30 backdrop-blur-xl rounded-2xl shadow-xl text-green-600 text-sm font-semibold">
                    <CheckCircle2 className="size-5 text-green-500" />
                    <span>{toastMessage}</span>
                </div>
            )}

            <div className="w-full max-w-xl">
                {/* Progress */}
                <div className="mb-8 flex items-center justify-between">
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

                {/* Step Content */}
                <Card className="border-border/50 shadow-lg">
                    <CardContent className="p-8">
                        {/* Step 0: Welcome */}
                        {step === 0 && (
                            <div className="text-center space-y-6">
                                <div className="size-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto">
                                    <Sparkles className="size-8 text-primary" />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-foreground">Welcome to Voise AI</h2>
                                    <p className="text-xs text-muted-foreground mt-2 max-w-sm mx-auto leading-relaxed">
                                        Let's get your workspace set up in under a minute.
                                        You'll name your workspace, choose what to work on first, and be on your way.
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Step 1: Workspace Name */}
                        {step === 1 && (
                            <div className="space-y-6">
                                <div className="flex items-center gap-3 pb-4 border-b border-border">
                                    <div className="size-10 rounded-xl bg-primary/10 flex items-center justify-center">
                                        <Building2 className="size-5 text-primary" />
                                    </div>
                                    <div>
                                        <h2 className="text-lg font-bold text-foreground">Name Your Workspace</h2>
                                        <p className="text-xs text-muted-foreground">This will be your organization's display name.</p>
                                    </div>
                                </div>
                                <div className="space-y-1.5">
                                    <Label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Workspace Name</Label>
                                    <Input
                                        value={orgName}
                                        onChange={e => setOrgName(e.target.value)}
                                        placeholder="e.g. Acme Corp"
                                        className="text-sm"
                                        autoFocus
                                    />
                                </div>
                            </div>
                        )}

                        {/* Step 2: Next Steps */}
                        {step === 2 && (
                            <div className="space-y-6">
                                <div className="pb-4 border-b border-border">
                                    <h2 className="text-lg font-bold text-foreground">What would you like to do first?</h2>
                                    <p className="text-xs text-muted-foreground mt-1">Pick one or more to get quick-start links after setup.</p>
                                </div>
                                <div className="space-y-3">
                                    {[
                                        { id: 'phone', icon: Phone, title: 'Connect a Phone Number', desc: 'Buy or configure a Twilio phone number for calls' },
                                        { id: 'agent', icon: Bot, title: 'Create an Agent', desc: 'Build your first voice agent with a template' },
                                    ].map(opt => {
                                        const selected = selectedPaths.includes(opt.id);
                                        return (
                                            <button
                                                key={opt.id}
                                                type="button"
                                                onClick={() => togglePath(opt.id)}
                                                className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 text-left transition-all ${
                                                    selected
                                                        ? 'border-primary bg-primary/5'
                                                        : 'border-border bg-muted/30 hover:border-primary/30'
                                                }`}
                                            >
                                                <div className={`size-10 rounded-xl flex items-center justify-center shrink-0 ${
                                                    selected ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                                                }`}>
                                                    <opt.icon className="size-5" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-semibold text-foreground">{opt.title}</p>
                                                    <p className="text-[10px] text-muted-foreground">{opt.desc}</p>
                                                </div>
                                                <div className={`size-5 rounded-full border-2 flex items-center justify-center shrink-0 ${
                                                    selected ? 'border-primary bg-primary' : 'border-muted-foreground'
                                                }`}>
                                                    {selected && <CheckCircle2 className="size-3.5 text-white" />}
                                                </div>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {/* Step 3: Done */}
                        {step === 3 && (
                            <div className="text-center space-y-6">
                                <div className="size-16 rounded-2xl bg-green-500/10 flex items-center justify-center mx-auto">
                                    <CheckCircle2 className="size-8 text-green-500" />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-foreground">You're all set!</h2>
                                    <p className="text-xs text-muted-foreground mt-2 max-w-sm mx-auto leading-relaxed">
                                        Your workspace is ready. Here's where to go next based on your choices:
                                    </p>
                                </div>
                                <div className="space-y-2 text-left">
                                    {selectedPaths.includes('phone') && (
                                        <Button type="button" variant="outline" className="w-full justify-start gap-3 text-xs h-auto py-3 px-4" onClick={() => router.push('/dashboard/phone-numbers')}>
                                            <Phone className="size-4 text-primary" />
                                            Set up your phone number
                                        </Button>
                                    )}
                                    {selectedPaths.includes('agent') && (
                                        <Button type="button" variant="outline" className="w-full justify-start gap-3 text-xs h-auto py-3 px-4" onClick={() => router.push('/dashboard/agents')}>
                                            <Bot className="size-4 text-primary" />
                                            Create your first agent
                                        </Button>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Navigation */}
                        <div className="flex items-center justify-between mt-8 pt-6 border-t border-border">
                            <Button
                                type="button"
                                variant="ghost"
                                onClick={() => step === 0 ? router.push('/dashboard') : setStep(step - 1)}
                                className="gap-2 text-xs"
                                disabled={saving}
                            >
                                <ArrowLeft className="size-3" />
                                {step === 0 ? 'Skip' : 'Back'}
                            </Button>

                            {step < STEPS.length - 1 ? (
                                <Button type="button" onClick={() => setStep(step + 1)} className="gap-2 text-xs">
                                    Next
                                    <ArrowRight className="size-3" />
                                </Button>
                            ) : (
                                <Button type="button" onClick={handleFinish} disabled={saving} className="gap-2 text-xs">
                                    {saving ? <Loader2 className="size-3 animate-spin" /> : <Sparkles className="size-3" />}
                                    {saving ? 'Finishing...' : 'Go to Dashboard'}
                                </Button>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
