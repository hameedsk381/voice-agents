'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import {
    ShieldCheck, Clock, UserCheck, XCircle,
    CheckCircle, AlertTriangle
} from 'lucide-react';
import { PendingAction } from '@/types/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function ApprovalsPage() {
    const [actions, setActions] = useState<PendingAction[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const fetchActions = async () => {
        try {
            const data = await api.get("/hitl/pending");
            setActions(data);
        } catch (err) {
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchActions();
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
                    Human-in-the-Loop <span className="text-primary font-semibold">Approvals</span>
                </h2>
                <p className="text-xs text-muted-foreground mt-1">Review and authorize sensitive agent actions before execution.</p>
            </div>

            {isLoading ? (
                <div className="grid grid-cols-1 gap-4">
                    {[1, 2].map(i => <div key={i} className="h-32 bg-muted/30 border border-border rounded-xl animate-pulse" />)}
                </div>
            ) : actions.length === 0 ? (
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
                        <Card key={action.id} className="hover:shadow-md transition-all">
                            <CardHeader className="flex flex-col md:flex-row md:items-start justify-between gap-4 pb-4">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <span className="px-2.5 py-0.5 rounded-full bg-primary/10 text-primary text-[9px] font-semibold uppercase tracking-wider border border-primary/20">
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

                            {/* Data Payload Panel */}
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
        </div>
    );
}
