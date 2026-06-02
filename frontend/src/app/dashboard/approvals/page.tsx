'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import {
    ShieldCheck, Clock, UserCheck, XCircle,
    CheckCircle, AlertTriangle, Phone, Activity
} from 'lucide-react';
import { PendingAction } from '@/types/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { LiveInterventionModal } from '@/components/dashboard/LiveInterventionModal';

export default function ApprovalsPage() {
    const [activeTab, setActiveTab] = useState<'pending' | 'live'>('pending');
    const [actions, setActions] = useState<PendingAction[]>([]);
    const [sessions, setSessions] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    
    // Intervention Modal State
    const [selectedSession, setSelectedSession] = useState<any | null>(null);

    const fetchData = async () => {
        try {
            const [actionsData, sessionsData] = await Promise.all([
                api.get("/hitl/pending"),
                api.get("/hitl/active-sessions")
            ]);
            setActions(actionsData);
            setSessions(sessionsData);
        } catch (err) {
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleDecision = async (id: string, decision: 'approved' | 'rejected') => {
        try {
            await api.post(`/hitl/${id}/decide`, { decision });
            setActions(prev => prev.filter(a => a.id !== id));
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="space-y-6 pb-10">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                    Human-in-the-Loop <span className="text-primary font-semibold">Command Center</span>
                </h2>
                <p className="text-xs text-muted-foreground mt-1">Review pending agent actions and monitor active live sessions.</p>
            </div>

            {/* Custom Tabs */}
            <div className="flex p-1 bg-muted/30 rounded-lg w-fit border border-border">
                <button
                    onClick={() => setActiveTab('pending')}
                    className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all ${
                        activeTab === 'pending' 
                        ? 'bg-background shadow-sm text-foreground' 
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                >
                    Pending Approvals
                    {actions.length > 0 && (
                        <span className="ml-2 bg-red-500 text-white px-1.5 py-0.5 rounded-full text-[10px]">
                            {actions.length}
                        </span>
                    )}
                </button>
                <button
                    onClick={() => setActiveTab('live')}
                    className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center gap-2 ${
                        activeTab === 'live' 
                        ? 'bg-background shadow-sm text-foreground' 
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                >
                    Live Sessions
                    {sessions.length > 0 && (
                        <span className="flex size-2 bg-green-500 rounded-full animate-pulse" />
                    )}
                </button>
            </div>

            {isLoading && actions.length === 0 && sessions.length === 0 ? (
                <div className="grid grid-cols-1 gap-4">
                    {[1, 2].map(i => <div key={i} className="h-32 bg-muted/30 border border-border rounded-xl animate-pulse" />)}
                </div>
            ) : activeTab === 'pending' ? (
                /* PENDING APPROVALS TAB */
                actions.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 bg-muted/40 rounded-2xl border border-dashed border-border">
                        <UserCheck className="size-10 text-muted-foreground mb-3" />
                        <h3 className="text-xs font-semibold text-foreground">No pending approvals</h3>
                        <p className="text-[10px] text-muted-foreground mt-1 max-w-xs text-center leading-relaxed">
                            All voice agent events have been authorized or none require administrator attention.
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 gap-5">
                        {actions.map((action) => (
                            <Card key={action.id} className="hover:shadow-md transition-all border-amber-500/20">
                                <CardHeader className="flex flex-col md:flex-row md:items-start justify-between gap-4 pb-4">
                                    <div className="space-y-1">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-500 text-[9px] font-semibold uppercase tracking-wider border border-amber-500/20">
                                                {action.action_type}
                                            </span>
                                            <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                                                <Clock className="w-3.5 h-3.5" />
                                                {new Date(action.created_at).toLocaleString()}
                                            </span>
                                        </div>
                                        <CardTitle className="text-sm font-semibold mt-2">{action.description}</CardTitle>
                                        <CardDescription className="text-[10px] font-mono mt-0.5">
                                            Agent ID: #{action.agent_id.slice(0, 8)} | Session: #{action.session_id.slice(0, 8)}
                                        </CardDescription>
                                    </div>

                                    <div className="flex items-center gap-3 shrink-0">
                                        <Button
                                            type="button"
                                            variant="outline"
                                            onClick={() => handleDecision(action.id, 'rejected')}
                                            className="h-9 px-4 text-red-500 hover:text-red-600 hover:bg-red-500/10 border-red-500/20"
                                        >
                                            <XCircle className="size-4 mr-1.5" />
                                            Reject
                                        </Button>
                                        <Button
                                            type="button"
                                            onClick={() => handleDecision(action.id, 'approved')}
                                            className="h-9 px-4 bg-green-600 hover:bg-green-500 dark:bg-green-700 dark:hover:bg-green-600 text-white font-semibold shadow-md shadow-green-500/10 border-0"
                                        >
                                            <CheckCircle className="size-4 mr-1.5" />
                                            Approve
                                        </Button>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <div className="p-4 bg-muted/60 rounded-xl border border-border">
                                        <p className="text-[9px] text-muted-foreground font-semibold uppercase tracking-wider mb-2">Request Payload</p>
                                        <pre className="text-xs text-primary dark:text-cyan-400 font-mono overflow-x-auto select-all leading-relaxed p-1">
                                            {JSON.stringify(action.payload, null, 2)}
                                        </pre>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )
            ) : (
                /* LIVE SESSIONS TAB */
                sessions.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 bg-muted/40 rounded-2xl border border-dashed border-border">
                        <Phone className="size-10 text-muted-foreground mb-3" />
                        <h3 className="text-xs font-semibold text-foreground">No active sessions</h3>
                        <p className="text-[10px] text-muted-foreground mt-1 max-w-xs text-center leading-relaxed">
                            There are currently no active voice agent calls taking place.
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
                        {sessions.map((session) => (
                            <Card key={session.session_id} className="hover:border-primary/50 transition-all">
                                <CardHeader className="pb-3">
                                    <div className="flex justify-between items-start">
                                        <div className="flex items-center gap-2">
                                            <Activity className="size-4 text-green-500 animate-pulse" />
                                            <CardTitle className="text-sm font-semibold">Active Call</CardTitle>
                                        </div>
                                        <Badge variant={session.status === 'escalated' ? 'destructive' : 'default'} className="text-[9px]">
                                            {session.status}
                                        </Badge>
                                    </div>
                                    <CardDescription className="text-[10px] flex flex-col gap-1 mt-2">
                                        <span className="flex items-center gap-1"><Clock className="size-3" /> Started {new Date(session.created_at).toLocaleTimeString()}</span>
                                        <span className="font-mono mt-1">Session: {session.session_id.substring(0, 8)}</span>
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="pb-4">
                                    <div className="text-xs space-y-2 bg-muted/50 p-3 rounded-md border border-border">
                                        <div className="flex justify-between">
                                            <span className="text-muted-foreground">Caller ID</span>
                                            <span className="font-medium">{session.caller_id || 'Unknown'}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-muted-foreground">Agent ID</span>
                                            <span className="font-medium font-mono">{session.agent_id.substring(0, 8)}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-muted-foreground">Floor Owner</span>
                                            <Badge variant="outline" className="text-[9px] capitalize">{(session.metadata?.floor_owner) || 'user'}</Badge>
                                        </div>
                                    </div>
                                </CardContent>
                                <CardFooter>
                                    <Button 
                                        onClick={() => setSelectedSession(session)} 
                                        className="w-full text-xs h-8 bg-primary/10 text-primary hover:bg-primary/20 hover:text-primary"
                                        variant="secondary"
                                    >
                                        <ShieldCheck className="size-3 mr-1.5" />
                                        Intervene
                                    </Button>
                                </CardFooter>
                            </Card>
                        ))}
                    </div>
                )
            )}

            {/* Compliance Note */}
            <div className="p-4 bg-amber-500/5 border border-amber-500/10 rounded-2xl flex items-start gap-4">
                <AlertTriangle className="size-5 text-amber-500 shrink-0 mt-0.5" />
                <div>
                    <h4 className="text-xs font-semibold text-foreground">HIPAA & Compliance Shield Active</h4>
                    <p className="text-[10px] text-muted-foreground mt-1 leading-relaxed">
                        All conversation payloads, parameters, and action logs are automatically scrubbed of sensitive PII (Emails, Card Numbers, Addresses) using workspace middleware privacy filters.
                    </p>
                </div>
            </div>

            <LiveInterventionModal 
                open={!!selectedSession} 
                session={selectedSession} 
                onClose={() => setSelectedSession(null)} 
            />
        </div>
    );
}
