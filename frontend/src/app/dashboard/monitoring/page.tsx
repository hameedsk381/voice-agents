'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import Link from 'next/link';
import { Phone, User, Clock, Activity } from 'lucide-react';

interface ActiveSession {
    session_id: string;
    agent_id: string;
    caller_id: string | null;
    status: string;
    created_at: string;
    metadata: {
        channel: string;
    };
}

export default function MonitoringPage() {
    const [sessions, setSessions] = useState<ActiveSession[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const fetchSessions = async () => {
        try {
            const data = await api.get('/monitoring/active-sessions');
            setSessions(data);
        } catch (error) {
            console.error('Failed to fetch active sessions:', error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchSessions();
        const interval = setInterval(fetchSessions, 5000); // Poll every 5s
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 select-none">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                        Live <span className="text-gradient-brand">Monitoring</span>
                    </h2>
                    <p className="text-xs text-[var(--text-secondary)] mt-1">Supervise ongoing conversational sessions and monitor latency in real-time.</p>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--accent-emerald)]/10 border border-[var(--accent-emerald)]/20 text-[var(--accent-emerald)] text-xs font-bold uppercase tracking-wider">
                    <Activity className="w-3.5 h-3.5 animate-pulse" />
                    <span>{sessions.length} Active Calls</span>
                </div>
            </div>

            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="h-48 glass-card animate-pulse" />
                    ))}
                </div>
            ) : sessions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 bg-[var(--bg-overlay)] border border-dashed border-[var(--border-default)] rounded-2xl text-center">
                    <Phone className="w-10 h-10 text-[var(--text-tertiary)] mb-3" />
                    <h3 className="text-xs font-bold text-[var(--text-primary)]">No Active Calls</h3>
                    <p className="text-[10px] text-[var(--text-tertiary)] mt-1 max-w-xs leading-relaxed">There are currently no ongoing conversational sessions to monitor.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {sessions.map((session) => (
                        <Link
                            key={session.session_id}
                            href={`/dashboard/monitoring/${session.session_id}`}
                            className="group block"
                        >
                            <div className="glass-card p-5 group flex flex-col justify-between h-full hover:border-[var(--border-active)] transition-all relative">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="p-2.5 rounded-xl bg-[var(--bg-overlay)] border border-[var(--border-subtle)] text-[var(--text-secondary)] group-hover:scale-105 transition-all">
                                        <Phone className="w-4.5 h-4.5" />
                                    </div>
                                    <div className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider border ${
                                        session.status === 'escalated' 
                                            ? 'bg-[var(--accent-rose)]/10 text-[var(--accent-rose)] border-[var(--accent-rose)]/25' 
                                            : 'bg-[var(--accent-emerald)]/10 text-[var(--accent-emerald)] border-[var(--accent-emerald)]/25'
                                    }`}>
                                        {session.status}
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <div className="flex items-center gap-2 text-xs font-bold text-[var(--text-primary)]">
                                        <User className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
                                        <span className="truncate">{session.caller_id || 'Anonymous Caller'}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
                                        <Clock className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
                                        <span>Started {new Date(session.created_at).toLocaleTimeString()}</span>
                                    </div>
                                    <div className="text-[10px] text-[var(--text-tertiary)] font-mono truncate">
                                        ID: {session.session_id.slice(0, 12)}...
                                    </div>
                                </div>

                                <div className="mt-5 flex items-center justify-between text-xs pt-4 border-t border-[var(--border-subtle)]">
                                    <span className="text-[var(--text-secondary)] font-medium">Listen Live</span>
                                    <div className="w-7 h-7 rounded-full bg-[var(--bg-overlay)] border border-[var(--border-subtle)] flex items-center justify-center group-hover:bg-gradient-to-r group-hover:from-[var(--accent-cyan)] group-hover:to-[var(--accent-purple)] group-hover:text-[var(--text-primary)] transition-all">
                                        <Activity className="w-3.5 h-3.5 text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]" />
                                    </div>
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}
