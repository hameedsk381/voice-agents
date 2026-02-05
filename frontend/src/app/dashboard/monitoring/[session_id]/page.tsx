'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import {
    Phone, User, MessageSquare, Zap, ShieldAlert,
    ArrowLeft, Activity, Box, Terminal, ChevronRight
} from 'lucide-react';

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
    const { token } = useAuth();
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
                const res = await fetch(`http://localhost:8001/api/v1/monitoring/session/${session_id}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    setDetails(data);
                    setMessages(data.history || []);
                    setStatus(data.status);
                }
            } catch (err) {
                console.error("Failed to fetch session metadata", err);
            }
        };

        fetchInitial();

        // Connect WebSocket
        const ws = new WebSocket(`ws://localhost:8001/api/v1/monitoring/stream/${session_id}`);
        wsRef.current = ws;

        ws.onopen = () => setIsConnected(true);
        ws.onclose = () => setIsConnected(false);
        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            handleMonitoringEvent(msg);
        };

        return () => ws.close();
    }, [session_id, token]);

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
                        onClick={() => router.back()}
                        className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-xl font-bold text-white flex items-center gap-2">
                            Session Monitor
                            <span className="text-xs font-mono text-gray-500 font-normal">#{session_id?.toString().slice(0, 8)}</span>
                        </h1>
                        <div className="flex items-center gap-4 mt-1">
                            <div className="flex items-center gap-1.5 text-xs text-gray-400">
                                <User className="w-3 h-3" />
                                {details?.caller_id || 'Anonymous'}
                            </div>
                            <div className={`flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider ${isConnected ? 'text-green-500' : 'text-red-500'
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
                    {status === 'escalated' ? <ShieldAlert className="w-4 h-4" /> : <Activity className="w-4 h-4" />}
                    <span className="text-sm font-semibold capitalize">{status}</span>
                </div>
            </div>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 overflow-hidden">
                {/* Main Transcript Panel */}
                <div className="lg:col-span-2 flex flex-col bg-[#141417] border border-white/10 rounded-2xl overflow-hidden">
                    <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-white/[0.02]">
                        <div className="flex items-center gap-2 text-sm font-medium text-white">
                            <MessageSquare className="w-4 h-4 text-blue-400" />
                            Live Transcript
                        </div>
                    </div>

                    <div
                        ref={scrollRef}
                        className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-white/10"
                    >
                        {messages.length === 0 && !currentChunk && (
                            <div className="flex flex-col items-center justify-center h-full text-gray-500">
                                <Activity className="w-8 h-8 mb-2 opacity-20" />
                                <p className="text-sm">Waiting for conversation to start...</p>
                            </div>
                        )}

                        {messages.map((msg, i) => (
                            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-start' : 'justify-end'}`}>
                                <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${msg.role === 'user'
                                    ? 'bg-white/5 border border-white/10 text-gray-200'
                                    : 'bg-blue-600/20 border border-blue-500/30 text-blue-50'
                                    }`}>
                                    <div className="text-[10px] uppercase tracking-wider font-bold mb-1 opacity-50">
                                        {msg.role}
                                    </div>
                                    <p className="text-sm leading-relaxed">{msg.content}</p>
                                </div>
                            </div>
                        ))}

                        {currentChunk && (
                            <div className="flex justify-end">
                                <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-blue-600/20 border border-blue-500/30 text-blue-50">
                                    <div className="text-[10px] uppercase tracking-wider font-bold mb-1 opacity-50 flex items-center gap-2">
                                        assistant
                                        <Zap className="w-3 h-3 animate-pulse text-yellow-500" />
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
                <div className="flex flex-col bg-[#141417] border border-white/10 rounded-2xl overflow-hidden">
                    <div className="px-6 py-4 border-b border-white/10 flex items-center gap-2 bg-white/[0.02] text-sm font-medium text-white">
                        <Terminal className="w-4 h-4 text-purple-400" />
                        Decision Trace
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {logs.length === 0 && (
                            <p className="text-center text-xs text-gray-500 mt-10 italic">No events recorded yet</p>
                        )}
                        {logs.map((log, i) => (
                            <div key={i} className="group relative pl-4 border-l border-white/10 py-1">
                                <div className={`absolute -left-[5px] top-2.5 w-2 h-2 rounded-full border border-[#141417] ${log.type === 'alert' || log.type === 'critical' ? 'bg-red-500' :
                                        log.type === 'tool' ? 'bg-purple-500' :
                                            log.type === 'intent' ? 'bg-yellow-500' : 'bg-blue-500'
                                    }`} />
                                <div className="text-[10px] text-gray-500 mb-0.5">
                                    {new Date(log.time).toLocaleTimeString()}
                                </div>
                                <div className="text-xs font-medium text-white group-hover:text-blue-400 transition-colors">
                                    {log.content}
                                </div>
                                {log.detail && (
                                    <div className="mt-2 p-2 rounded bg-black/40 border border-white/5 text-[10px] text-gray-400 font-mono break-all line-clamp-2 group-hover:line-clamp-none transition-all">
                                        {typeof log.detail === 'object' ? JSON.stringify(log.detail) : log.detail}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>

                    {/* Agent Info Footnote */}
                    <div className="p-4 bg-white/[0.02] border-t border-white/10">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center text-white font-bold">
                                {details?.agent_id?.slice(0, 1).toUpperCase()}
                            </div>
                            <div>
                                <p className="text-xs text-gray-500">Current Agent</p>
                                <p className="text-sm font-semibold text-white">#{details?.agent_id?.slice(0, 8)}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
