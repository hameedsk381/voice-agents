'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { Phone, User, Clock, ShieldAlert, Activity } from 'lucide-react';

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
    const { token } = useAuth();

    const fetchSessions = async () => {
        try {
            const response = await fetch('http://localhost:8001/api/v1/monitoring/active-sessions', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (response.ok) {
                const data = await response.json();
                setSessions(data);
            }
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
    }, [token]);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Live Monitoring</h1>
                    <p className="text-gray-400">Track and supervise active voice conversations in real-time.</p>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-sm">
                    <Activity className="w-4 h-4 animate-pulse" />
                    <span>{sessions.length} Active Calls</span>
                </div>
            </div>

            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="h-48 rounded-2xl bg-white/5 animate-pulse border border-white/10" />
                    ))}
                </div>
            ) : sessions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 border border-dashed border-white/10 rounded-3xl bg-white/5 text-center">
                    <Phone className="w-12 h-12 text-gray-600 mb-4" />
                    <h3 className="text-xl font-medium text-white">No Active Calls</h3>
                    <p className="text-gray-400 max-w-xs mt-2">There are currently no ongoing conversations to monitor.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {sessions.map((session) => (
                        <Link
                            key={session.session_id}
                            href={`/dashboard/monitoring/${session.session_id}`}
                            className="group bg-[#141417] border border-white/10 rounded-2xl p-6 hover:border-blue-500/50 hover:bg-blue-500/5 transition-all duration-300"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="p-3 rounded-xl bg-blue-500/10 text-blue-400 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                                    <Phone className="w-5 h-5" />
                                </div>
                                <div className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider ${session.status === 'escalated' ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
                                    }`}>
                                    {session.status}
                                </div>
                            </div>

                            <div className="space-y-3">
                                <div className="flex items-center gap-2 text-white">
                                    <User className="w-4 h-4 text-gray-400" />
                                    <span className="font-medium truncate">{session.caller_id || 'Anonymous Caller'}</span>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-gray-400">
                                    <Clock className="w-4 h-4" />
                                    <span>Started {new Date(session.created_at).toLocaleTimeString()}</span>
                                </div>
                                <div className="flex items-center gap-2 text-xs text-gray-500 font-mono truncate">
                                    ID: {session.session_id.slice(0, 8)}...
                                </div>
                            </div>

                            <div className="mt-6 flex items-center justify-between text-sm">
                                <span className="text-gray-400">Listen Live</span>
                                <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-blue-500 group-hover:text-white transition-all">
                                    <Activity className="w-4 h-4" />
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}
