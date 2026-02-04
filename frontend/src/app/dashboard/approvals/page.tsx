'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
    ShieldCheck, Clock, UserCheck, XCircle,
    CheckCircle, MessageSquare, AlertTriangle, ArrowRight
} from 'lucide-react';

interface PendingAction {
    id: string;
    action_type: string;
    description: string;
    payload: any;
    status: string;
    created_at: string;
    agent_id: string;
    session_id: string;
}

export default function ApprovalsPage() {
    const { token } = useAuth();
    const [actions, setActions] = useState<PendingAction[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const fetchActions = async () => {
        try {
            const res = await fetch('http://localhost:8001/api/v1/hitl/pending', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                setActions(await res.json());
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (token) fetchActions();
    }, [token]);

    const handleDecision = async (id: string, decision: 'approved' | 'rejected') => {
        try {
            const res = await fetch(`http://localhost:8001/api/v1/hitl/${id}/decide`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ decision })
            });
            if (res.ok) {
                setActions(prev => prev.filter(a => a.id !== id));
            }
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="space-y-8 pb-10">
            <div>
                <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                    <ShieldCheck className="w-6 h-6 text-blue-500" />
                    Human-in-the-Loop Approvals
                </h1>
                <p className="text-gray-400">Review and authorize sensitive agent actions before execution.</p>
            </div>

            {isLoading ? (
                <div className="grid grid-cols-1 gap-4">
                    {[1, 2].map(i => <div key={i} className="h-32 bg-white/5 animate-pulse rounded-2xl border border-white/10" />)}
                </div>
            ) : actions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 bg-white/5 rounded-3xl border border-dashed border-white/10">
                    <UserCheck className="w-12 h-12 text-gray-600 mb-4" />
                    <h3 className="text-xl font-medium text-white">No pending approvals</h3>
                    <p className="text-gray-400 mt-2">All agent actions have been processed or none are required.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-6">
                    {actions.map((action) => (
                        <div key={action.id} className="bg-[#141417] border border-white/10 rounded-2xl p-6 hover:border-white/20 transition-all">
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                        <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 text-[10px] font-bold uppercase tracking-wider">
                                            {action.action_type}
                                        </span>
                                        <span className="text-xs text-gray-500 flex items-center gap-1">
                                            <Clock className="w-3 h-3" />
                                            {new Date(action.created_at).toLocaleString()}
                                        </span>
                                    </div>
                                    <h3 className="text-lg font-semibold text-white">{action.description}</h3>
                                    <p className="text-sm text-gray-400">Agent ID: #{action.agent_id.slice(0, 8)} | Session: #{action.session_id.slice(0, 8)}</p>
                                </div>

                                <div className="flex items-center gap-3">
                                    <button
                                        onClick={() => handleDecision(action.id, 'rejected')}
                                        className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-xl text-sm font-bold border border-red-500/20 transition-all flex items-center gap-2"
                                    >
                                        <XCircle className="w-4 h-4" />
                                        Reject
                                    </button>
                                    <button
                                        onClick={() => handleDecision(action.id, 'approved')}
                                        className="px-4 py-2 bg-green-500/10 hover:bg-green-500/20 text-green-500 rounded-xl text-sm font-bold border border-green-500/20 transition-all flex items-center gap-2"
                                    >
                                        <CheckCircle className="w-4 h-4" />
                                        Approve
                                    </button>
                                </div>
                            </div>

                            {/* Data Payload Panel */}
                            <div className="mt-4 p-4 bg-black/40 rounded-xl border border-white/5">
                                <p className="text-[10px] text-gray-500 font-bold uppercase mb-2">Request Payload</p>
                                <pre className="text-xs text-blue-300 font-mono overflow-x-auto">
                                    {JSON.stringify(action.payload, null, 2)}
                                </pre>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Compliance Note */}
            <div className="p-4 bg-yellow-500/5 border border-yellow-500/10 rounded-2xl flex items-start gap-4">
                <AlertTriangle className="w-5 h-5 text-yellow-500 shrink-0 mt-0.5" />
                <div>
                    <h4 className="text-sm font-semibold text-white">PII & Compliance Active</h4>
                    <p className="text-xs text-gray-400 mt-1 leading-relaxed">
                        All conversation data and action logs are automatically scrubbed of sensitive PII (Emails, Phone Numbers, Credit Cards) before being displayed here or stored in the database.
                        <strong> HIPPA/GDPR/SOC2</strong> compliance filters are active on this workspace.
                    </p>
                </div>
            </div>
        </div>
    );
}
