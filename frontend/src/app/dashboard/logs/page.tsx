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
            case 'completed': return 'text-[var(--accent-emerald)] bg-[var(--accent-emerald)]/10 border-[var(--accent-emerald)]/20';
            case 'failed': return 'text-[var(--accent-rose)] bg-[var(--accent-rose)]/10 border-[var(--accent-rose)]/20';
            case 'escalated': return 'text-[var(--accent-blue)] bg-[var(--accent-blue)]/10 border-[var(--accent-blue)]/20';
            default: return 'text-[var(--text-tertiary)] bg-[var(--glass-bg)] border-[var(--border-subtle)]';
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
                    <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                        Call <span className="text-gradient-brand">Logs</span>
                    </h2>
                    <p className="text-xs text-[var(--text-secondary)] mt-1">Review detailed history, recordings, and transcripts of all active voice events.</p>
                </div>
                
                <div className="flex flex-wrap items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-tertiary)]" />
                        <input
                            type="text"
                            placeholder="Search calls..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl pl-10 pr-4 py-2 text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-cyan)] transition-all w-60"
                        />
                    </div>
                    
                    <button className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-overlay)] border border-[var(--border-default)] hover:bg-[var(--glass-bg-hover)] rounded-xl text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all">
                        <Filter className="w-3.5 h-3.5" />
                        Filter
                    </button>
                    
                    <button onClick={handleExport} className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] hover:shadow-lg text-white rounded-xl text-xs font-bold transition-all">
                        <Download className="w-3.5 h-3.5" />
                        Export log
                    </button>
                </div>
            </div>

            <div className="flex gap-6 overflow-hidden max-h-[calc(100vh-220px)]">
                {/* Logs Table */}
                <div className={`flex-1 overflow-auto transition-all duration-300 ${selectedLog ? 'w-2/3 hidden md:block' : 'w-full'}`}>
                    <div className="glass-card p-0 overflow-hidden">
                        <table className="w-full text-left border-collapse">
                            <thead className="bg-[var(--bg-overlay)] text-[10px] uppercase tracking-wider font-bold text-[var(--text-tertiary)] border-b border-[var(--border-subtle)]">
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
                                                <div className="h-4 bg-[var(--glass-bg)] rounded w-full"></div>
                                            </td>
                                        </tr>
                                    ))
                                ) : filteredLogs.length === 0 ? (
                                    <tr>
                                        <td colSpan={7} className="px-6 py-20 text-center">
                                            <div className="flex flex-col items-center gap-2">
                                                <div className="w-10 h-10 bg-[var(--bg-overlay)] rounded-full flex items-center justify-center mb-2">
                                                    <Clock className="w-5 h-5 text-[var(--text-tertiary)]" />
                                                </div>
                                                <p className="text-xs font-bold text-[var(--text-primary)]">No call logs found</p>
                                                <p className="text-[10px] text-[var(--text-tertiary)]">Session history will appear here once calls are initiated.</p>
                                            </div>
                                        </td>
                                    </tr>
                                ) : (
                                    filteredLogs.map((log) => (
                                        <tr
                                            key={log.id}
                                            onClick={() => setSelectedLog(log)}
                                            className={`hover:bg-[var(--bg-overlay)] cursor-pointer transition-colors group ${selectedLog?.id === log.id ? 'bg-[var(--glass-bg)]' : ''}`}
                                        >
                                            <td className="px-6 py-4 text-xs font-bold text-[var(--text-primary)]">{log.agent_name || 'Unknown Agent'}</td>
                                            <td className="px-6 py-4 text-xs text-[var(--text-secondary)] font-mono">{log.caller_id || 'Inbound PSTN'}</td>
                                            <td className="px-6 py-4 text-xs text-[var(--text-secondary)]">
                                                {format(new Date(log.start_time), 'MMM d, HH:mm:ss')}
                                            </td>
                                            <td className="px-6 py-4 text-xs text-[var(--text-secondary)]">
                                                {Math.floor(log.duration_seconds / 60)}m {Math.floor(log.duration_seconds % 60)}s
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`text-xs font-mono font-bold ${log.avg_latency_ms > 500 ? 'text-[var(--accent-amber)]' : 'text-[var(--accent-emerald)]'}`}>
                                                    {Math.round(log.avg_latency_ms)}ms
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider border ${getStatusColor(log.status)}`}>
                                                    {log.status || 'Success'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <ChevronRight className={`w-4.5 h-4.5 text-[var(--text-tertiary)] group-hover:text-[var(--text-primary)] transition-all ${selectedLog?.id === log.id ? 'rotate-90 text-[var(--accent-cyan)]' : ''}`} />
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
                    <div className="w-full md:w-1/3 flex flex-col bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-2xl overflow-hidden animate-in slide-in-from-right duration-200">
                        <div className="p-4 border-b border-[var(--border-subtle)] flex items-center justify-between">
                            <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)]">Call Details</h3>
                            <button
                                onClick={() => setSelectedLog(null)}
                                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] text-lg font-bold p-1 transition-colors"
                            >
                                ×
                            </button>
                        </div>

                        <div className="flex-1 overflow-auto p-5 space-y-6">
                            {/* Stats */}
                            <div className="grid grid-cols-2 gap-3">
                                <div className="p-3 bg-[var(--bg-overlay)] rounded-xl border border-[var(--border-subtle)]">
                                    <p className="text-[9px] text-[var(--text-tertiary)] font-bold uppercase mb-1">Turns</p>
                                    <p className="text-base font-extrabold text-[var(--text-primary)]">{selectedLog.total_turns ?? 0}</p>
                                </div>
                                <div className="p-3 bg-[var(--bg-overlay)] rounded-xl border border-[var(--border-subtle)]">
                                    <p className="text-[9px] text-[var(--text-tertiary)] font-bold uppercase mb-1">Cost</p>
                                    <p className="text-base font-mono font-extrabold text-[var(--text-primary)]">${(selectedLog.estimated_cost ?? 0).toFixed(4)}</p>
                                </div>
                            </div>

                            {/* Transcript */}
                            <div className="space-y-3">
                                <div className="flex items-center gap-2 text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">
                                    <MessageSquare className="w-3.5 h-3.5 text-[var(--accent-cyan)]" />
                                    Transcript
                                </div>
                                <div className="space-y-3 p-3 bg-black/25 rounded-xl border border-[var(--border-subtle)] max-h-60 overflow-y-auto">
                                    {selectedLog.transcript?.length > 0 ? (
                                        selectedLog.transcript.map((msg: any, i: number) => (
                                            <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                                <span className="text-[8px] text-[var(--text-tertiary)] uppercase tracking-wider mb-1 font-bold">{msg.role}</span>
                                                <div className={`max-w-[90%] px-3.5 py-2 rounded-2xl text-xs leading-relaxed ${msg.role === 'user'
                                                        ? 'bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-blue)] text-white rounded-tr-none'
                                                        : 'bg-[var(--bg-overlay)] text-[var(--text-secondary)] border border-[var(--border-subtle)] rounded-tl-none'
                                                    }`}>
                                                    {msg.content}
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="text-center py-6">
                                            <p className="text-[10px] text-[var(--text-tertiary)] italic">No transcript recorded for this session.</p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* System Info */}
                            <div className="space-y-3">
                                <div className="flex items-center gap-2 text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">
                                    <Info className="w-3.5 h-3.5 text-[var(--accent-purple)]" />
                                    Call details
                                </div>
                                <div className="p-4 bg-[var(--bg-inset)] rounded-xl space-y-2.5 font-mono text-[10px]">
                                    <div className="flex justify-between">
                                        <span className="text-[var(--text-tertiary)]">Session ID:</span>
                                        <span className="text-[var(--accent-cyan)] truncate max-w-[130px] font-semibold">{selectedLog.session_id}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-[var(--text-tertiary)]">End Reason:</span>
                                        <span className="text-[var(--text-secondary)]">{selectedLog.end_reason || "Normal Completion"}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-[var(--text-tertiary)]">Outcome:</span>
                                        <span className="text-[var(--text-secondary)]">{selectedLog.outcome || "—"}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="p-4 bg-[var(--bg-overlay)] border-t border-[var(--border-subtle)] flex gap-2">
                            <button className="w-full flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white rounded-xl text-xs font-bold hover:shadow-lg transition-all active:scale-98">
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
