'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import api from '@/lib/api';
import {
    Phone, User, MessageSquare, Zap, ShieldAlert,
    ArrowLeft, Activity, Box, Terminal, ChevronRight
} from 'lucide-react';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001';

interface Event {
    type: string;
    data: any;
    timestamp: number;
}

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
}

export default function SessionMonitoringPage() {
    const { session_id } = useParams();
    const router = useRouter();

    const [messages, setMessages] = useState<Message[]>([]);
    const [currentChunk, setCurrentChunk] = useState('');
    const [status, setStatus] = useState('active');
    const [details, setDetails] = useState<any>(null);
    const [logs, setLogs] = useState<any[]>([]);
    const [isConnected, setIsConnected] = useState(false);

    const scrollRef = useRef<HTMLDivElement>(null);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, currentChunk]);

    useEffect(() => {
        // Fetch initial state
        const fetchInitial = async () => {
            try {
                const data = await api.get(`/monitoring/session/${session_id}`);
                setDetails(data);
                setMessages(data.history || []);
                setStatus(data.status);
            } catch (err) {
                console.error("Failed to fetch session metadata", err);
            }
        };

        fetchInitial();

        // Connect WebSocket
        const ws = new WebSocket(`${WS_URL}/api/v1/monitoring/stream/${session_id}`);
        wsRef.current = ws;

        ws.onopen = () => setIsConnected(true);
        ws.onclose = () => setIsConnected(false);
        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            handleMonitoringEvent(msg);
        };

        return () => ws.close();
    }, [session_id]);

    const handleMonitoringEvent = (event: any) => {
        const { type, data } = event;

        switch (type) {
            case 'transcription':
                if (data.role === 'assistant') {
                    setCurrentChunk(''); // Clear streaming chunk
                }
                setMessages(prev => [...prev, {
                    role: data.role,
                    content: data.text,
                    timestamp: new Date().toISOString()
                }]);
                break;

            case 'text_chunk':
                setCurrentChunk(prev => prev + data.text);
                break;

            case 'intent_detected':
                setLogs(prev => [{ type: 'intent', content: data.intent, time: new Date() }, ...prev]);
                break;

            case 'tool_call':
                setLogs(prev => [{ type: 'tool', content: `Calling ${data.name}`, detail: data.arguments, time: new Date() }, ...prev]);
                break;

            case 'tool_result':
                setLogs(prev => [{ type: 'result', content: `Tool ${data.name} returned`, detail: data.result, time: new Date() }, ...prev]);
                break;

            case 'agent_switch':
                setLogs(prev => [{ type: 'switch', content: `Switch: ${data.from} → ${data.to}`, time: new Date() }, ...prev]);
                break;

            case 'escalation':
                setStatus('escalated');
                setLogs(prev => [{ type: 'alert', content: `ESCALATION: ${data.reason}`, time: new Date() }, ...prev]);
                break;

            case 'compliance_alert':
                setLogs(prev => [{ type: 'critical', content: `COMPLIANCE ALERT: Risk Score ${data.risk_score}`, detail: "Real-time violation blocked", time: new Date() }, ...prev]);
                break;
        }
    };

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col gap-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button
                        type="button"
                        onClick={() => router.back()}
                        className="p-2 rounded-lg bg-muted hover:bg-muted text-muted-foreground transition-colors"
                    >
                        <ArrowLeft className="size-5" />
                    </button>
                    <div>
                        <h1 className="text-xl font-semibold text-foreground flex items-center gap-2">
                            Session Monitor
                            <span className="text-xs font-mono text-muted-foreground font-normal">#{session_id?.toString().slice(0, 8)}</span>
                        </h1>
                        <div className="flex items-center gap-4 mt-1">
                            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                                <User className="size-3" />
                                {details?.caller_id || 'Anonymous'}
                            </div>
                            <div className={`flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider ${isConnected ? 'text-green-500' : 'text-red-500'
                                }`}>
                                <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                                {isConnected ? 'Live' : 'Disconnected'}
                            </div>
                        </div>
                    </div>
                </div>

                <div className={`px-4 py-2 rounded-xl border flex items-center gap-2 ${status === 'escalated'
                    ? 'bg-red-500/10 border-red-500/30 text-red-500'
                    : 'bg-green-500/10 border-green-500/30 text-green-500'
                    }`}>
                    {status === 'escalated' ? <ShieldAlert className="size-4" /> : <Activity className="size-4" />}
                    <span className="text-sm font-semibold capitalize">{status}</span>
                </div>
            </div>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 overflow-hidden">
                {/* Main Transcript Panel */}
                <div className="lg:col-span-2 flex flex-col bg-[var(--bg-raised)] border border-border rounded-2xl overflow-hidden">
                    <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted">
                        <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                            <MessageSquare className="size-4 text-blue-400" />
                            Live Transcript
                        </div>
                    </div>

                    <div
                        ref={scrollRef}
                        className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-white/10"
                    >
                        {messages.length === 0 && !currentChunk && (
                            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                                <Activity className="size-8 mb-2 opacity-20" />
                                <p className="text-sm">Waiting for conversation to start...</p>
                            </div>
                        )}

                        {messages.map((msg, i) => (
                            <div key={`msg-${msg.timestamp}`} className={`flex ${msg.role === 'user' ? 'justify-start' : 'justify-end'}`}>
                                <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${msg.role === 'user'
                                    ? 'bg-muted border border-border text-gray-200'
                                    : 'bg-blue-600/20 border border-blue-500/30 text-blue-50'
                                    }`}>
                                    <div className="text-[10px] uppercase tracking-wider font-semibold mb-1 opacity-50">
                                        {msg.role}
                                    </div>
                                    <p className="text-sm leading-relaxed">{msg.content}</p>
                                </div>
                            </div>
                        ))}

                        {currentChunk && (
                            <div className="flex justify-end">
                                <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-blue-600/20 border border-blue-500/30 text-blue-50">
                                    <div className="text-[10px] uppercase tracking-wider font-semibold mb-1 opacity-50 flex items-center gap-2">
                                        assistant
                                        <Zap className="size-3 animate-pulse text-yellow-500" />
                                    </div>
                                    <p className="text-sm leading-relaxed">
                                        {currentChunk}
                                        <span className="inline-block w-1.5 h-4 ml-1 bg-blue-400 animate-pulse align-middle" />
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Sidebar Decision Trace */}
                <div className="flex flex-col bg-[var(--bg-raised)] border border-border rounded-2xl overflow-hidden">
                    <div className="px-6 py-4 border-b border-border flex items-center gap-2 bg-muted text-sm font-medium text-foreground">
                        <Terminal className="size-4 text-purple-400" />
                        Decision Trace
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {logs.length === 0 && (
                            <p className="text-center text-xs text-muted-foreground mt-10 italic">No events recorded yet</p>
                        )}
                        {logs.map((log, i) => (
                            <div key={`log-${log.time}`} className="group relative pl-4 border-l border-border py-1">
                                <div className={`absolute -left-[5px] top-2.5 size-2 rounded-full                         border border-border ${log.type === 'alert' || log.type === 'critical' ? 'bg-red-500' :
                                        log.type === 'tool' ? 'bg-purple-500' :
                                            log.type === 'intent' ? 'bg-yellow-500' : 'bg-blue-500'
                                    }`} />
                                <div className="text-[10px] text-muted-foreground mb-0.5">
                                    {new Date(log.time).toLocaleTimeString()}
                                </div>
                                <div className="text-xs font-medium text-foreground group-hover:text-blue-400 transition-colors">
                                    {log.content}
                                </div>
                                {log.detail && (
                                    <div className="mt-2 p-2 rounded bg-muted border border-border text-[10px] text-muted-foreground font-mono break-all line-clamp-2 group-hover:line-clamp-none transition-all">
                                        {typeof log.detail === 'object' ? JSON.stringify(log.detail) : log.detail}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>

                    {/* Agent Info Footnote */}
                    <div className="p-4 bg-muted border-t border-border">
                        <div className="flex items-center gap-3">
                            <div className="size-10 rounded-xl bg-primary flex items-center justify-center text-white font-semibold">
                                {details?.agent_id?.slice(0, 1).toUpperCase()}
                            </div>
                            <div>
                                <p className="text-xs text-muted-foreground">Current Agent</p>
                                <p className="text-sm font-semibold text-foreground">#{details?.agent_id?.slice(0, 8)}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
