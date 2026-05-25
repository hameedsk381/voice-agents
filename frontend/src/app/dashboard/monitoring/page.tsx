'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import Link from 'next/link';
import { Phone, User, Clock, Activity, Loader2, Radio } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

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
            {/* Page Header */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 select-none">
                <div>
                    <h2 className="text-2xl font-semibold tracking-tight text-foreground">
                        Live{' '}
                        <span className="text-primary">
                            Monitoring
                        </span>
                    </h2>
                    <p className="text-sm text-muted-foreground mt-1">
                        Supervise ongoing conversational sessions and monitor latency in real-time.
                    </p>
                </div>
                <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 text-green-600 border border-green-500/20 text-xs font-semibold uppercase tracking-wider">
                    <Activity className="w-3.5 h-3.5 animate-pulse" />
                    {sessions.length} Active Calls
                </span>
            </div>

            {/* Content */}
            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[1, 2, 3].map((i) => (
                        <Card key={i} className="h-48 animate-pulse">
                            <CardContent className="p-5">
                                <div className="space-y-3">
                                    <div className="flex items-center justify-between">
                                        <div className="size-10 rounded-lg bg-muted" />
                                        <div className="w-16 h-5 rounded-full bg-muted" />
                                    </div>
                                    <div className="space-y-2 mt-4">
                                        <div className="w-3/4 h-4 rounded bg-muted" />
                                        <div className="w-1/2 h-3 rounded bg-muted" />
                                        <div className="w-2/3 h-3 rounded bg-muted" />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            ) : sessions.length === 0 ? (
                <Card className="border-dashed">
                    <CardContent className="flex flex-col items-center justify-center py-20 text-center">
                        <div className="bg-primary/10 rounded-lg p-3 mb-4">
                            <Phone className="size-8 text-primary" />
                        </div>
                        <h3 className="text-sm font-semibold text-foreground">No Active Calls</h3>
                        <p className="text-xs text-muted-foreground mt-1.5 max-w-xs leading-relaxed">
                            There are currently no ongoing conversational sessions to monitor.
                        </p>
                        <Button variant="outline" size="sm" className="mt-4" onClick={fetchSessions}>
                            <Activity className="w-3.5 h-3.5 mr-1.5" />
                            Refresh
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {sessions.map((session) => (
                        <Link
                            key={session.session_id}
                            href={`/dashboard/monitoring/${session.session_id}`}
                            className="group block"
                        >
                            <Card className="hover:shadow-md transition-all h-full">
                                <CardHeader className="pb-3">
                                    <div className="flex items-start justify-between">
                                        <div className="bg-primary/10 rounded-lg p-2.5 group-hover:scale-105 transition-transform">
                                            <Phone className="size-4 text-primary" />
                                        </div>
                                        <span
                                            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                                session.status === 'escalated'
                                                    ? 'bg-red-500/10 text-red-600 border border-red-500/20'
                                                    : 'bg-green-500/10 text-green-600 border border-green-500/20'
                                            }`}
                                        >
                                            {session.status}
                                        </span>
                                    </div>
                                </CardHeader>

                                <CardContent className="space-y-4">
                                    <div className="space-y-2">
                                        <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                                            <User className="w-3.5 h-3.5 text-muted-foreground" />
                                            <span className="truncate">
                                                {session.caller_id || 'Anonymous Caller'}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                            <Clock className="w-3.5 h-3.5" />
                                            <span>
                                                Started{' '}
                                                {new Date(session.created_at).toLocaleTimeString()}
                                            </span>
                                        </div>
                                        <div className="text-[10px] text-muted-foreground font-mono truncate">
                                            ID: {session.session_id.slice(0, 12)}...
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between pt-4 border-t border-border">
                                        <Button variant="outline" size="sm" className="text-xs">
                                            <Radio className="w-3.5 h-3.5 mr-1.5" />
                                            Listen Live
                                        </Button>
                                        <div className="size-7 rounded-full bg-primary/10 flex items-center justify-center group-hover:bg-primary group-hover:text-primary-foreground transition-all">
                                            <Activity className="w-3.5 h-3.5" />
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}
