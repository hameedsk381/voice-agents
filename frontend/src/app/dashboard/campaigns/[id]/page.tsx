'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import api from '@/lib/api';
import {
    Phone, Users, BarChart3, Upload, Play, Pause,
    ArrowLeft, CheckCircle2, AlertCircle, Clock, Trash2, FileText
} from 'lucide-react';
import Link from 'next/link';

export default function CampaignDetailsPage() {
    const { id } = useParams();
    const router = useRouter();

    const [campaign, setCampaign] = useState<any>(null);
    const [stats, setStats] = useState<any>({});
    const [isLoading, setIsLoading] = useState(true);
    const [isStarting, setIsStarting] = useState(false);

    const [uploading, setUploading] = useState(false);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const [contacts, setContacts] = useState<any[]>([]);
    const [greeting, setGreeting] = useState('');
    const [savingGreeting, setSavingGreeting] = useState(false);
    const [dialingId, setDialingId] = useState<string | null>(null);

    const fetchDetails = async () => {
        try {
            const data = await api.get(`/campaigns/${id}`);
            setCampaign(data.campaign);
            setStats(data.stats);
            setGreeting(data.campaign?.call_config?.greeting || '');
            const contactList = await api.get(`/campaigns/${id}/contacts`);
            setContacts(contactList);
        } catch (err) {
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchDetails();
        const interval = setInterval(fetchDetails, 10000); // Poll every 10s
        return () => clearInterval(interval);
    }, [id]);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        setUploadError(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            await api.postFormData(`/campaigns/${id}/upload-csv`, formData);
            fetchDetails();
        } catch (err) {
            setUploadError('System error uploading file.');
        } finally {
            setUploading(false);
        }
    };

    const handleSaveGreeting = async () => {
        setSavingGreeting(true);
        try {
            await api.put(`/campaigns/${id}/call-config`, { greeting });
            fetchDetails();
        } catch (err) {
            console.error(err);
        } finally {
            setSavingGreeting(false);
        }
    };

    const handleDialContact = async (contactId: string) => {
        setDialingId(contactId);
        try {
            await api.post(`/campaigns/${id}/dial/${contactId}`, {});
            fetchDetails();
        } catch (err) {
            console.error(err);
        } finally {
            setDialingId(null);
        }
    };

    const handleStartCampaign = async () => {
        setIsStarting(true);
        try {
            await api.post(`/campaigns/${id}/start`, {});
            fetchDetails();
        } catch (err) {
            console.error(err);
        } finally {
            setIsStarting(false);
        }
    };

    if (isLoading) return <div className="p-20 text-center text-[var(--text-primary)]">Loading campaign details...</div>;
    if (!campaign) return <div className="p-20 text-center text-[var(--text-primary)]">Campaign not found.</div>;

    const total = campaign.total_contacts || 0;
    const progress = total > 0 ? Math.round(((stats.completed || 0) / total) * 100) : 0;

    return (
        <div className="space-y-8 pb-20">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard/campaigns" className="p-2 rounded-lg bg-[var(--glass-bg)] hover:bg-[var(--glass-bg-hover)] text-gray-400 transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div>
                        <div className="flex items-center gap-3">
                            <h1 className="text-3xl font-bold text-[var(--text-primary)]">{campaign.name}</h1>
                            <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border ${campaign.status === 'running' ? 'bg-green-500/10 text-green-500 border-green-500/20' : 'bg-gray-500/10 text-gray-400 border-[var(--border-default)]'
                                }`}>
                                {campaign.status}
                            </span>
                        </div>
                        <p className="text-gray-400 mt-1">{campaign.description || 'No description provided.'}</p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {campaign.status === 'draft' && total > 0 && (
                        <button
                            onClick={handleStartCampaign}
                            disabled={isStarting}
                            className="flex items-center gap-2 px-6 py-2.5 bg-green-600 hover:bg-green-500 text-white font-bold rounded-xl transition-all shadow-lg shadow-green-500/20"
                        >
                            <Play className="w-5 h-5 fill-current" />
                            Start Campaign
                        </button>
                    )}
                    {campaign.status === 'running' && (
                        <button className="flex items-center gap-2 px-6 py-2.5 bg-yellow-600 hover:bg-yellow-500 text-white font-bold rounded-xl transition-all shadow-lg shadow-yellow-500/20">
                            <Pause className="w-5 h-5 fill-current" />
                            Pause
                        </button>
                    )}
                </div>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-[var(--bg-raised)] border border-[var(--border-default)] rounded-2xl p-6">
                    <div className="flex items-center gap-3 text-gray-400 mb-2">
                        <Users className="w-4 h-4" />
                        <span className="text-xs font-medium uppercase tracking-wider">Total Reach</span>
                    </div>
                    <p className="text-3xl font-bold text-[var(--text-primary)]">{total}</p>
                </div>
                <div className="bg-[var(--bg-raised)] border border-[var(--border-default)] rounded-2xl p-6">
                    <div className="flex items-center gap-3 text-green-400 mb-2">
                        <CheckCircle2 className="w-4 h-4" />
                        <span className="text-xs font-medium uppercase tracking-wider">Success</span>
                    </div>
                    <p className="text-3xl font-bold text-[var(--text-primary)]">{stats.completed || 0}</p>
                </div>
                <div className="bg-[var(--bg-raised)] border border-[var(--border-default)] rounded-2xl p-6">
                    <div className="flex items-center gap-3 text-red-500 mb-2">
                        <AlertCircle className="w-4 h-4" />
                        <span className="text-xs font-medium uppercase tracking-wider">Failed</span>
                    </div>
                    <p className="text-3xl font-bold text-[var(--text-primary)]">{stats.failed || 0}</p>
                </div>
                <div className="bg-[var(--bg-raised)] border border-[var(--border-default)] rounded-2xl p-6">
                    <div className="flex items-center gap-3 text-blue-400 mb-2">
                        <BarChart3 className="w-4 h-4" />
                        <span className="text-xs font-medium uppercase tracking-wider">Conversion</span>
                    </div>
                    <p className="text-3xl font-bold text-[var(--text-primary)]">
                        {total > 0 ? Math.round(((stats.completed || 0) / total) * 100) : 0}%
                    </p>
                </div>
            </div>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Contact List / Upload */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-[var(--bg-raised)] border border-[var(--border-default)] rounded-2xl overflow-hidden">
                        <div className="px-6 py-4 border-b border-[var(--border-default)] flex items-center justify-between bg-[var(--bg-overlay)]">
                            <h3 className="text-lg font-semibold text-[var(--text-primary)] flex items-center gap-2">
                                <FileText className="w-5 h-5 text-blue-500" />
                                Contact List
                            </h3>
                            {total === 0 && !uploading && (
                                <label className="flex items-center gap-2 px-3 py-1.5 bg-blue-500 hover:bg-blue-400 text-white text-xs font-bold rounded-lg cursor-pointer transition-all">
                                    <Upload className="w-4 h-4" />
                                    Upload CSV
                                    <input type="file" accept=".csv" className="hidden" onChange={handleFileUpload} />
                                </label>
                            )}
                        </div>

                        <div className="p-8">
                            {total === 0 ? (
                                <div className="text-center py-12 border-2 border-dashed border-[var(--border-subtle)] rounded-2xl">
                                    {uploading ? (
                                        <div className="flex flex-col items-center gap-4">
                                            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
                                            <p className="text-gray-400">Processing contact file...</p>
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center gap-4">
                                            <Upload className="w-12 h-12 text-gray-700" />
                                            <div>
                                                <p className="text-[var(--text-primary)] font-medium">No contacts imported</p>
                                                <p className="text-sm text-gray-500 mt-1">Upload a CSV file with <code className="text-blue-500">phone_number</code> column.</p>
                                            </div>
                                            <label className="mt-4 px-6 py-2 bg-[var(--glass-bg)] hover:bg-[var(--glass-bg-hover)] border border-[var(--border-default)] text-white font-medium rounded-xl cursor-pointer transition-all">
                                                Select File
                                                <input type="file" accept=".csv" className="hidden" onChange={handleFileUpload} />
                                            </label>
                                            {uploadError && <p className="text-red-400 text-xs mt-2">{uploadError}</p>}
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-gray-400">Campaign processing progress</span>
                                        <span className="text-[var(--text-primary)] font-bold">{progress}%</span>
                                    </div>
                                    <div className="h-4 w-full bg-[var(--glass-bg)] rounded-full overflow-hidden border border-[var(--border-subtle)] p-1">
                                        <div
                                            className="h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full transition-all duration-1000 shadow-lg shadow-blue-500/20"
                                            style={{ width: `${progress}%` }}
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-8 border-t border-[var(--border-subtle)]">
                                        <div className="space-y-1">
                                            <p className="text-[10px] uppercase font-bold text-gray-500">Queued</p>
                                            <p className="text-lg text-[var(--text-primary)]">{stats.pending || 0}</p>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-[10px] uppercase font-bold text-gray-500">Active</p>
                                            <p className="text-lg text-blue-400">{stats.in_progress || 0}</p>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-[10px] uppercase font-bold text-gray-500">Completed</p>
                                            <p className="text-lg text-green-400">{stats.completed || 0}</p>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-[10px] uppercase font-bold text-gray-500">Failed</p>
                                            <p className="text-lg text-red-400">{stats.failed || 0}</p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Sidebar Config */}
                <div className="space-y-6">
                    <div className="bg-[var(--bg-raised)] border border-[var(--border-default)] rounded-2xl p-6">
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 border-b border-[var(--border-subtle)] pb-2">Configuration</h3>
                        <div className="space-y-4">
                            <div>
                                <p className="text-[10px] text-gray-500 uppercase font-bold">Assigned Agent</p>
                                <p className="text-sm text-gray-200 mt-1">Linked to your voice agent</p>
                            </div>
                            <div>
                                <p className="text-[10px] text-gray-500 uppercase font-bold">Concurrency</p>
                                <p className="text-sm text-gray-200 mt-1">{campaign.concurrency_limit} parallel calls</p>
                            </div>
                            <div>
                                <p className="text-[10px] text-gray-500 uppercase font-bold">Retry Logic</p>
                                <p className="text-sm text-gray-200 mt-1">{campaign.retry_config?.max_retries || 3} attempts</p>
                            </div>
                            <div>
                                <p className="text-[10px] text-gray-500 uppercase font-bold mb-1">Campaign Greeting</p>
                                <textarea
                                    value={greeting}
                                    onChange={(e) => setGreeting(e.target.value)}
                                    rows={3}
                                    placeholder="Hi {{contactName}}..."
                                    className="w-full bg-[var(--bg-inset)] border border-[var(--border-default)] rounded-lg px-2 py-1.5 text-xs text-white"
                                />
                                <button
                                    type="button"
                                    onClick={handleSaveGreeting}
                                    disabled={savingGreeting}
                                    className="mt-2 text-xs px-3 py-1 rounded-md bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                                >
                                    {savingGreeting ? 'Saving…' : 'Save greeting'}
                                </button>
                            </div>
                        </div>
                    </div>

                    {contacts.length > 0 && (
                        <div className="bg-[var(--bg-raised)] border border-[var(--border-default)] rounded-2xl p-4 max-h-80 overflow-y-auto">
                            <h3 className="text-xs font-bold text-gray-400 uppercase mb-3">Dial contacts</h3>
                            <ul className="space-y-2">
                                {contacts.slice(0, 20).map((c) => (
                                    <li key={c.id} className="flex items-center justify-between gap-2 text-sm">
                                        <span className="text-gray-300 truncate">{c.contact_name || c.phone_number}</span>
                                        <button
                                            type="button"
                                            disabled={dialingId === c.id || c.status === 'completed'}
                                            onClick={() => handleDialContact(c.id)}
                                            className="shrink-0 text-[10px] px-2 py-1 rounded bg-green-500/10 text-green-400 border border-green-500/20 disabled:opacity-40"
                                        >
                                            {dialingId === c.id ? '…' : 'Dial'}
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <button className="w-full py-3 bg-red-500/10 hover:bg-red-500/20 text-red-500 text-sm font-bold border border-red-500/20 rounded-xl transition-all flex items-center justify-center gap-2">
                        <Trash2 className="w-4 h-4" />
                        Delete Campaign
                    </button>
                </div>
            </div>
        </div>
    );
}
