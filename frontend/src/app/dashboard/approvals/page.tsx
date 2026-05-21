'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import {
    ShieldCheck, Clock, UserCheck, XCircle,
    CheckCircle, AlertTriangle
} from 'lucide-react';
import { PendingAction } from '@/types/types';

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
                <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)] flex items-center gap-2">
                    Human-in-the-Loop <span className="text-gradient-brand">Approvals</span>
                </h2>
                <p className="text-xs text-[var(--text-secondary)] mt-1">Review and authorize sensitive agent actions before execution.</p>
            </div>

            {isLoading ? (
                <div className="grid grid-cols-1 gap-4">
                    {[1, 2].map(i => <div key={i} className="h-32 glass-card animate-pulse" />)}
                </div>
            ) : actions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 bg-[var(--bg-overlay)] rounded-2xl border border-dashed border-[var(--border-default)]">
                    <UserCheck className="w-10 h-10 text-[var(--text-tertiary)] mb-3" />
                    <h3 className="text-xs font-bold text-[var(--text-primary)]">No pending approvals</h3>
                    <p className="text-[10px] text-[var(--text-tertiary)] mt-1 max-w-xs text-center leading-relaxed">All voice agent events have been authorized or none require administrator attention.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-5">
                    {actions.map((action) => (
                        <div key={action.id} className="glass-card p-6 hover:border-[var(--border-active)] transition-all">
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                        <span className="px-2 py-0.5 rounded-full bg-[var(--accent-cyan)]/10 text-[var(--accent-cyan)] text-[9px] font-bold uppercase tracking-wider border border-[var(--accent-cyan)]/25">
                                            {action.action_type}
                                        </span>
                                        <span className="text-[10px] text-[var(--text-tertiary)] flex items-center gap-1">
                                            <Clock className="w-3.5 h-3.5" />
                                            {new Date(action.created_at).toLocaleString()}
                                        </span>
                                    </div>
                                    <h3 className="text-sm font-bold text-[var(--text-primary)] mt-2">{action.description}</h3>
                                    <p className="text-[10px] text-[var(--text-tertiary)] font-mono">Agent ID: #{action.agent_id.slice(0, 8)} | Session: #{action.session_id.slice(0, 8)}</p>
                                </div>

                                <div className="flex items-center gap-3">
                                    <button
                                        onClick={() => handleDecision(action.id, 'rejected')}
                                        className="px-4 py-2 bg-[var(--accent-rose)]/10 hover:bg-[var(--accent-rose)]/20 text-[var(--accent-rose)] rounded-xl text-xs font-bold border border-[var(--accent-rose)]/20 transition-all flex items-center gap-2"
                                    >
                                        <XCircle className="w-4 h-4" />
                                        Reject
                                    </button>
                                    <button
                                        onClick={() => handleDecision(action.id, 'approved')}
                                        className="px-4 py-2 bg-[var(--accent-emerald)]/10 hover:bg-[var(--accent-emerald)]/20 text-[var(--accent-emerald)] rounded-xl text-xs font-bold border border-[var(--accent-emerald)]/25 transition-all flex items-center gap-2"
                                    >
                                        <CheckCircle className="w-4 h-4" />
                                        Approve
                                    </button>
                                </div>
                            </div>

                            {/* Data Payload Panel */}
                            <div className="mt-4 p-4 bg-[var(--bg-inset)] rounded-xl border border-[var(--border-subtle)]">
                                <p className="text-[9px] text-[var(--text-tertiary)] font-bold uppercase tracking-wider mb-2">Request Payload</p>
                                <pre className="text-xs text-[var(--accent-cyan)] font-mono overflow-x-auto select-all leading-normal p-1 bg-[var(--bg-inset)] rounded">
                                    {JSON.stringify(action.payload, null, 2)}
                                </pre>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Compliance Note */}
            <div className="p-4 bg-[var(--accent-amber)]/5 border border-[var(--accent-amber)]/10 rounded-2xl flex items-start gap-4">
                <AlertTriangle className="w-5 h-5 text-[var(--accent-amber)] shrink-0 mt-0.5" />
                <div>
                    <h4 className="text-xs font-bold text-[var(--text-primary)]">HIPAA & Compliance Shield Active</h4>
                    <p className="text-[10px] text-[var(--text-secondary)] mt-1 leading-relaxed">
                        All conversation payloads, parameters, and action logs are automatically scrubbed of sensitive PII (Emails, Card Numbers, Addresses) using workspace middleware privacy filters.
                    </p>
                </div>
            </div>
        </div>
    );
}
