'use client';

import { useState, useEffect } from 'react';
import {
    Phone, Clock, Search,
    Filter, Download, ChevronRight,
    PlayCircle, MessageSquare, Info
} from 'lucide-react';
import { format } from 'date-fns';
import api from '@/lib/api';
import { CallLog } from '@/types/types';

export default function CallLogsPage() {
    const [logs, setLogs] = useState<CallLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedLog, setSelectedLog] = useState<CallLog | null>(null);
    const [searchQuery, setSearchQuery] = useState('');

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

    const handleExport = () => {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(filteredLogs, null, 2));
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", `call_logs_export_${new Date().toISOString()}.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
    };

    const getStatusColor = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'completed': return 'text-green-600 bg-green-500/10 border-green-500/20';
            case 'failed': return 'text-red-600 bg-red-500/10 border-red-500/20';
            case 'escalated': return 'text-primary bg-primary/10 border-primary/20';
            default: return 'text-muted-foreground bg-muted border-border';
        }
    };

    const filteredLogs = logs.filter(log => 
        log.agent_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (log.caller_id && log.caller_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
        log.session_id?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="space-y-6">
            <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4 select-none">
                <div>
                    <h2 className="text-2xl font-semibold tracking-tight text-foreground">
                        Call <span className="text-primary">Logs</span>
                    </h2>
                    <p className="text-xs text-muted-foreground mt-1">Review detailed history, recordings, and transcripts of all active voice events.</p>
                </div>
                
                <div className="flex flex-wrap items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                        <input
                            type="text"
                            placeholder="Search calls..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="bg-muted border border-border rounded-xl pl-10 pr-4 py-2 text-xs text-foreground focus:outline-none focus:border-primary transition-all w-60"
                        />
                    </div>
                    
                    <button type="button" className="flex items-center gap-2 px-4 py-2 bg-muted border border-border hover:bg-muted rounded-xl text-xs font-semibold text-muted-foreground hover:text-foreground transition-all">
                        <Filter className="w-3.5 h-3.5" />
                        Filter
                    </button>
                    
                    <button type="button" onClick={handleExport} className="flex items-center gap-2 px-4 py-2 bg-primary hover:shadow-lg text-white rounded-xl text-xs font-semibold transition-all">
                        <Download className="w-3.5 h-3.5" />
                        Export log
                    </button>
                </div>
            </div>

            <div className="flex gap-6 overflow-hidden max-h-[calc(100vh-220px)]">
                {/* Logs Table */}
                <div className={`flex-1 overflow-auto transition-all duration-300 ${selectedLog ? 'w-2/3 hidden md:block' : 'w-full'}`}>
                    <div className="bg-card border text-card-foreground shadow-sm rounded-xl p-0 overflow-hidden">
                        <table className="w-full text-left border-collapse">
                            <thead className="bg-muted text-[10px] uppercase tracking-wider font-semibold text-muted-foreground border-b border-border">
                                <tr>
                                    <th className="px-6 py-4">Agent</th>
                                    <th className="px-6 py-4">Caller</th>
                                    <th className="px-6 py-4">Start Time</th>
                                    <th className="px-6 py-4">Duration</th>
                                    <th className="px-6 py-4">Latency</th>
                                    <th className="px-6 py-4">Status</th>
                                    <th className="px-6 py-4"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/[0.04]">
                                {loading ? (
                                    Array(5).fill(0).map((_, i) => (
                                        <tr key={i} className="animate-pulse">
                                            <td colSpan={7} className="px-6 py-5">
                                                <div className="h-4 bg-muted rounded w-full"></div>
                                            </td>
                                        </tr>
                                    ))
                                ) : filteredLogs.length === 0 ? (
                                    <tr>
                                        <td colSpan={7} className="px-6 py-20 text-center">
                                            <div className="flex flex-col items-center gap-2">
                                                <div className="size-10 bg-muted rounded-full flex items-center justify-center mb-2">
                                                    <Clock className="size-5 text-muted-foreground" />
                                                </div>
                                                <p className="text-xs font-semibold text-foreground">No call logs found</p>
                                                <p className="text-[10px] text-muted-foreground">Session history will appear here once calls are initiated.</p>
                                            </div>
                                        </td>
                                    </tr>
                                ) : (
                                    filteredLogs.map((log) => (
                                        <tr
                                            key={log.id}
                                            onClick={() => setSelectedLog(log)}
                                            className={`hover:bg-muted cursor-pointer transition-colors group ${selectedLog?.id === log.id ? 'bg-muted' : ''}`}
                                        >
                                            <td className="px-6 py-4 text-xs font-semibold text-foreground">{log.agent_name || 'Unknown Agent'}</td>
                                            <td className="px-6 py-4 text-xs text-muted-foreground font-mono">{log.caller_id || 'Inbound PSTN'}</td>
                                            <td className="px-6 py-4 text-xs text-muted-foreground">
                                                {format(new Date(log.start_time), 'MMM d, HH:mm:ss')}
                                            </td>
                                            <td className="px-6 py-4 text-xs text-muted-foreground">
                                                {Math.floor(log.duration_seconds / 60)}m {Math.floor(log.duration_seconds % 60)}s
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`text-xs font-mono font-semibold ${log.avg_latency_ms > 500 ? 'text-yellow-600' : 'text-green-600'}`}>
                                                    {Math.round(log.avg_latency_ms)}ms
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2 py-0.5 rounded-full text-[9px] font-semibold uppercase tracking-wider border ${getStatusColor(log.status)}`}>
                                                    {log.status || 'Success'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <ChevronRight className={`w-4.5 h-4.5 text-muted-foreground group-hover:text-foreground transition-all ${selectedLog?.id === log.id ? 'rotate-90 text-primary' : ''}`} />
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
                    <div className="w-full md:w-1/3 flex flex-col bg-card border border-border rounded-2xl overflow-hidden animate-in slide-in-from-right duration-200">
                        <div className="p-4 border-b border-border flex items-center justify-between">
                            <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">Call Details</h3>
                            <button
                                type="button"
                                onClick={() => setSelectedLog(null)}
                                className="text-muted-foreground hover:text-foreground text-lg font-bold p-1 transition-colors"
                            >
                                ×
                            </button>
                        </div>

                        <div className="flex-1 overflow-auto p-5 space-y-6">
                            {/* Stats */}
                            <div className="grid grid-cols-2 gap-3">
                                <div className="p-3 bg-muted rounded-xl border border-border">
                                    <p className="text-[9px] text-muted-foreground font-semibold uppercase mb-1">Turns</p>
                                    <p className="text-base font-extrabold text-foreground">{selectedLog.total_turns ?? 0}</p>
                                </div>
                                <div className="p-3 bg-muted rounded-xl border border-border">
                                    <p className="text-[9px] text-muted-foreground font-semibold uppercase mb-1">Cost</p>
                                    <p className="text-base font-mono font-extrabold text-foreground">₹{(selectedLog.estimated_cost ?? 0).toFixed(4)}</p>
                                </div>
                            </div>

                            {/* Transcript */}
                            <div className="space-y-3">
                                <div className="flex items-center gap-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                                    <MessageSquare className="w-3.5 h-3.5 text-primary" />
                                    Transcript
                                </div>
                                <div className="space-y-3 p-3 bg-muted rounded-xl border border-border max-h-60 overflow-y-auto">
                                    {selectedLog.transcript?.length > 0 ? (
                                        selectedLog.transcript.map((msg: any, i: number) => (
                                            <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                                <span className="text-[8px] text-muted-foreground uppercase tracking-wider mb-1 font-semibold">{msg.role}</span>
                                                <div className={`max-w-[90%] px-3.5 py-2 rounded-2xl text-xs leading-relaxed ${msg.role === 'user'
                                                        ? 'bg-primary text-white rounded-tr-none'
                                                        : 'bg-muted text-muted-foreground border border-border rounded-tl-none'
                                                    }`}>
                                                    {msg.content}
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="text-center py-6">
                                            <p className="text-[10px] text-muted-foreground italic">No transcript recorded for this session.</p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* System Info */}
                            <div className="space-y-3">
                                <div className="flex items-center gap-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                                    <Info className="w-3.5 h-3.5 text-primary" />
                                    Call details
                                </div>
                                <div className="p-4 bg-muted rounded-xl space-y-2.5 font-mono text-[10px]">
                                    <div className="flex justify-between">
                                        <span className="text-muted-foreground">Session ID:</span>
                                        <span className="text-primary truncate max-w-[130px] font-semibold">{selectedLog.session_id}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-muted-foreground">End Reason:</span>
                                        <span className="text-muted-foreground">{selectedLog.end_reason || "Normal Completion"}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-muted-foreground">Outcome:</span>
                                        <span className="text-muted-foreground">{selectedLog.outcome || "—"}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="p-4 bg-muted border-t border-border flex gap-2">
                            <button type="button" className="w-full flex items-center justify-center gap-2 py-2.5 bg-primary text-white rounded-xl text-xs font-semibold hover:shadow-lg transition-all active:scale-98">
                                <PlayCircle className="size-4" />
                                Listen Recording
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
