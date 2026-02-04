'use client';

import { useState, useEffect } from 'react';
import {
    Phone, Clock, BarChart3, Search,
    Filter, Download, ChevronRight,
    PlayCircle, MessageSquare, Info
} from 'lucide-react';
import { format } from 'date-fns';
import api from '@/lib/api';

interface CallLog {
    id: string;
    session_id: string;
    agent_id: string;
    agent_name: string;
    caller_id: string;
    start_time: string;
    duration_seconds: number;
    avg_latency_ms: number;
    status: string;
    end_reason: string;
    transcript: any[];
}

export default function CallLogsPage() {
    const [logs, setLogs] = useState<CallLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedLog, setSelectedLog] = useState<CallLog | null>(null);

    useEffect(() => {
        fetchLogs();
    }, []);

    const fetchLogs = async () => {
        try {
            const data = await api.get('/analytics');
            setLogs(data);
        } catch (error) {
            console.error('Failed to fetch logs:', error);
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'completed': return 'text-green-500 bg-green-500/10';
            case 'failed': return 'text-red-500 bg-red-500/10';
            case 'escalated': return 'text-blue-500 bg-blue-500/10';
            default: return 'text-gray-400 bg-gray-400/10';
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Call Logs</h1>
                    <p className="text-gray-400">Review detailed history and transcripts of all voice sessions.</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                        <input
                            type="text"
                            placeholder="Search calls..."
                            className="bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-all w-64"
                        />
                    </div>
                    <button className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm font-medium text-gray-300 hover:bg-white/10 transition-all">
                        <Filter className="w-4 h-4" />
                        Filter
                    </button>
                    <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-medium transition-all">
                        <Download className="w-4 h-4" />
                        Export log
                    </button>
                </div>
            </div>

            <div className="flex gap-6 overflow-hidden max-h-[calc(100vh-200px)]">
                {/* Logs Table */}
                <div className={`flex-1 overflow-auto transition-all duration-300 ${selectedLog ? 'w-2/3' : 'w-full'}`}>
                    <div className="bg-[#141417] border border-white/10 rounded-2xl">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-white/5">
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Agent</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Caller</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Start Time</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Duration</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Latency</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-4"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {loading ? (
                                    Array(5).fill(0).map((_, i) => (
                                        <tr key={i} className="animate-pulse">
                                            <td colSpan={7} className="px-6 py-4">
                                                <div className="h-10 bg-white/5 rounded-lg w-full"></div>
                                            </td>
                                        </tr>
                                    ))
                                ) : logs.length === 0 ? (
                                    <tr>
                                        <td colSpan={7} className="px-6 py-20 text-center">
                                            <div className="flex flex-col items-center gap-2">
                                                <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center mb-2">
                                                    <Clock className="w-6 h-6 text-gray-600" />
                                                </div>
                                                <p className="text-white font-medium">No call logs found</p>
                                                <p className="text-gray-500 text-sm">Session history will appear here once calls are initiated.</p>
                                            </div>
                                        </td>
                                    </tr>
                                ) : (
                                    logs.map((log) => (
                                        <tr
                                            key={log.id}
                                            onClick={() => setSelectedLog(log)}
                                            className={`hover:bg-white/5 cursor-pointer transition-colors group ${selectedLog?.id === log.id ? 'bg-blue-600/5' : ''}`}
                                        >
                                            <td className="px-6 py-4 font-medium text-white">{log.agent_name}</td>
                                            <td className="px-6 py-4 text-gray-400 font-mono text-xs">{log.caller_id || 'Inbound PSTN'}</td>
                                            <td className="px-6 py-4 text-gray-400">
                                                {format(new Date(log.start_time), 'MMM d, HH:mm:ss')}
                                            </td>
                                            <td className="px-6 py-4 text-gray-400">
                                                {Math.floor(log.duration_seconds / 60)}m {Math.floor(log.duration_seconds % 60)}s
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`text-xs ${log.avg_latency_ms > 500 ? 'text-yellow-500' : 'text-green-500'}`}>
                                                    {Math.round(log.avg_latency_ms)}ms
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${getStatusColor(log.status)}`}>
                                                    {log.status || 'Success'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <ChevronRight className={`w-4 h-4 text-gray-600 group-hover:text-blue-500 transition-all ${selectedLog?.id === log.id ? 'rotate-90 text-blue-500' : ''}`} />
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Detail Panel */}
                {selectedLog && (
                    <div className="w-1/3 flex flex-col bg-[#141417] border border-white/10 rounded-2xl overflow-hidden animate-in slide-in-from-right duration-300">
                        <div className="p-6 border-b border-white/5 flex items-center justify-between">
                            <h2 className="font-bold text-white">Call Details</h2>
                            <button
                                onClick={() => setSelectedLog(null)}
                                className="text-gray-500 hover:text-white"
                            >
                                ×
                            </button>
                        </div>

                        <div className="flex-1 overflow-auto p-6 space-y-8">
                            {/* Stats */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                                    <p className="text-[10px] text-gray-500 font-bold uppercase mb-1">Turns</p>
                                    <p className="text-xl font-bold text-white">12</p>
                                </div>
                                <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                                    <p className="text-[10px] text-gray-500 font-bold uppercase mb-1">Cost</p>
                                    <p className="text-xl font-bold text-white">$0.04</p>
                                </div>
                            </div>

                            {/* Transcript */}
                            <div className="space-y-4">
                                <div className="flex items-center gap-2 text-xs font-bold text-gray-500 uppercase tracking-widest">
                                    <MessageSquare className="w-3 h-3" />
                                    Transcript
                                </div>
                                <div className="space-y-4">
                                    {selectedLog.transcript?.length > 0 ? (
                                        selectedLog.transcript.map((msg: any, i: number) => (
                                            <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                                <div className={`max-w-[85%] px-4 py-2 rounded-2xl text-sm ${msg.role === 'user'
                                                        ? 'bg-blue-600 text-white rounded-tr-none'
                                                        : 'bg-white/5 text-gray-300 border border-white/10 rounded-tl-none'
                                                    }`}>
                                                    {msg.content}
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="text-center py-10">
                                            <p className="text-gray-500 text-xs italic">No transcript recorded for this session.</p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* System Info */}
                            <div className="space-y-3">
                                <div className="flex items-center gap-2 text-xs font-bold text-gray-500 uppercase tracking-widest">
                                    <Info className="w-3 h-3" />
                                    System Metadata
                                </div>
                                <div className="p-4 bg-black/30 rounded-xl space-y-2 font-mono text-[10px]">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Session ID:</span>
                                        <span className="text-blue-400">{selectedLog.session_id.slice(0, 12)}...</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">End Reason:</span>
                                        <span className="text-gray-400">{selectedLog.end_reason}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Model:</span>
                                        <span className="text-gray-400">llama3-70b-v4</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="p-4 bg-white/5 border-t border-white/5 flex gap-2">
                            <button className="flex-1 flex items-center justify-center gap-2 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-bold transition-all">
                                <PlayCircle className="w-4 h-4" />
                                Listen Recording
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

