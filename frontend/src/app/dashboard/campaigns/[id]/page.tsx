'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import api from '@/lib/api';
import {
    Phone, Users, BarChart3, Upload, Play, Pause,
    ArrowLeft, CheckCircle2, AlertCircle, Clock, Trash2, FileText, GitBranch,
    RefreshCw
} from 'lucide-react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';

export default function CampaignDetailsPage() {
    const { id } = useParams();
    const router = useRouter();

    const [campaign, setCampaign] = useState<any>(null);
    const [stats, setStats] = useState<any>({});
    const [workflowInfo, setWorkflowInfo] = useState<any>(null);
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
            setWorkflowInfo(data.workflow || null);
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

    if (isLoading) return <div className="p-20 text-center text-foreground font-semibold flex items-center justify-center gap-2"><RefreshCw className="size-5 animate-spin text-primary" /> Loading campaign details...</div>;
    if (!campaign) return <div className="p-20 text-center text-foreground font-semibold">Campaign not found.</div>;

    const total = campaign.total_contacts || 0;
    const progress = total > 0 ? Math.round(((stats.completed || 0) / total) * 100) : 0;

    return (
        <div className="space-y-8 pb-20">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard/campaigns" className="p-2 rounded-lg bg-muted hover:bg-muted/70 text-muted-foreground transition-colors">
                        <ArrowLeft className="size-5" />
                    </Link>
                    <div>
                        <div className="flex items-center gap-3">
                            <h1 className="text-3xl font-bold tracking-tight text-foreground">{campaign.name}</h1>
                            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider border ${campaign.status === 'running' ? 'bg-green-500/10 text-green-600 border-green-500/20' : 'bg-muted text-muted-foreground border-border'}`}>
                                {campaign.status}
                            </span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">{campaign.description || 'No description provided.'}</p>
                    </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                    {campaign.status === 'draft' && total > 0 && (
                        <Button
                            type="button"
                            onClick={handleStartCampaign}
                            disabled={isStarting}
                            className="bg-green-600 hover:bg-green-500 text-white font-semibold rounded-xl transition-all shadow-lg shadow-green-500/10 border-0"
                        >
                            <Play className="size-4 mr-1.5 fill-current" />
                            Start Campaign
                        </Button>
                    )}
                    {campaign.status === 'running' && (
                        <Button
                            type="button"
                            className="bg-amber-600 hover:bg-amber-500 text-white font-semibold rounded-xl transition-all shadow-lg shadow-amber-500/10 border-0"
                        >
                            <Pause className="size-4 mr-1.5 fill-current" />
                            Pause
                        </Button>
                    )}
                </div>
            </div>

            {workflowInfo?.workflow_id && (
                <Card className="border-primary/20 hover:shadow-md transition-all">
                    <CardContent className="p-5 flex flex-wrap items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <div className="size-9 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                                <GitBranch className="size-5" />
                            </div>
                            <div>
                                <p className="text-sm font-semibold text-foreground">
                                    Workflow: {workflowInfo.workflow_name || 'Linked automation'}
                                </p>
                                <p className="text-xs text-muted-foreground mt-0.5">
                                    {workflowInfo.instance_count ?? 0} instances ·{' '}
                                    {Object.entries(workflowInfo.instances_by_status || {})
                                        .map(([k, v]) => `${k}: ${v}`)
                                        .join(' · ') || 'No runs yet'}
                                </p>
                            </div>
                        </div>
                        <Link
                            href={`/dashboard/workflows/${workflowInfo.workflow_id}`}
                            className="text-xs font-semibold text-primary hover:underline"
                        >
                            Open workflow editor
                        </Link>
                    </CardContent>
                </Card>
            )}

            {/* Stats Overview */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
                <Card className="hover:shadow-md transition-all">
                    <CardContent className="p-6">
                        <div className="flex items-center gap-2 text-muted-foreground mb-2">
                            <Users className="size-4" />
                            <span className="text-[10px] font-semibold uppercase tracking-wider">Total Reach</span>
                        </div>
                        <p className="text-3xl font-extrabold text-foreground">{total}</p>
                    </CardContent>
                </Card>
                <Card className="hover:shadow-md transition-all">
                    <CardContent className="p-6">
                        <div className="flex items-center gap-2 text-green-500 mb-2">
                            <CheckCircle2 className="size-4" />
                            <span className="text-[10px] font-semibold uppercase tracking-wider">Success</span>
                        </div>
                        <p className="text-3xl font-extrabold text-foreground">{stats.completed || 0}</p>
                    </CardContent>
                </Card>
                <Card className="hover:shadow-md transition-all">
                    <CardContent className="p-6">
                        <div className="flex items-center gap-2 text-red-500 mb-2">
                            <AlertCircle className="size-4" />
                            <span className="text-[10px] font-semibold uppercase tracking-wider">Failed</span>
                        </div>
                        <p className="text-3xl font-extrabold text-foreground">{stats.failed || 0}</p>
                    </CardContent>
                </Card>
                <Card className="hover:shadow-md transition-all">
                    <CardContent className="p-6">
                        <div className="flex items-center gap-2 text-primary mb-2">
                            <BarChart3 className="size-4" />
                            <span className="text-[10px] font-semibold uppercase tracking-wider">Conversion</span>
                        </div>
                        <p className="text-3xl font-extrabold text-foreground">
                            {total > 0 ? Math.round(((stats.completed || 0) / total) * 100) : 0}%
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Contact List / Upload */}
                <div className="lg:col-span-2 space-y-6">
                    <Card className="overflow-hidden hover:shadow-md transition-all">
                        <CardHeader className="bg-muted flex flex-row items-center justify-between pb-4 space-y-0">
                            <div>
                                <CardTitle className="text-base flex items-center gap-2">
                                    <FileText className="size-4.5 text-primary" />
                                    Contact List
                                </CardTitle>
                                <CardDescription className="text-xs">CSV containing targets, retry counters and call outcomes.</CardDescription>
                            </div>
                            {total === 0 && !uploading && (
                                <label className="flex items-center gap-2 px-3 py-1.5 bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold rounded-lg cursor-pointer transition-all shadow-md shadow-primary/10">
                                    <Upload className="size-3.5" />
                                    Upload CSV
                                    <input type="file" accept=".csv" className="hidden" onChange={handleFileUpload} />
                                </label>
                            )}
                        </CardHeader>

                        <CardContent className="p-6">
                            {total === 0 ? (
                                <div className="text-center py-12 border-2 border-dashed border-border rounded-2xl bg-muted/20">
                                    {uploading ? (
                                        <div className="flex flex-col items-center gap-4">
                                            <div className="size-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                                            <p className="text-xs text-muted-foreground">Processing contact file...</p>
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center gap-4">
                                            <Upload className="size-10 text-muted-foreground" />
                                            <div>
                                                <p className="text-xs font-semibold text-foreground">No contacts imported</p>
                                                <p className="text-[10px] text-muted-foreground mt-1">Upload a CSV file with <code className="text-primary font-mono font-semibold">phone_number</code> column.</p>
                                            </div>
                                            <label className="mt-2 px-5 py-2 bg-muted hover:bg-muted/70 border border-border text-xs font-semibold text-foreground rounded-xl cursor-pointer transition-all">
                                                Select File
                                                <input type="file" accept=".csv" className="hidden" onChange={handleFileUpload} />
                                            </label>
                                            {uploadError && <p className="text-red-400 text-[10px] mt-2 font-semibold">{uploadError}</p>}
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between text-xs">
                                        <span className="text-muted-foreground font-semibold">Campaign processing progress</span>
                                        <span className="text-foreground font-bold">{progress}%</span>
                                    </div>
                                    <div className="h-4 w-full bg-muted rounded-full overflow-hidden border border-border p-1">
                                        <div
                                            className="h-full bg-gradient-to-r from-primary to-secondary rounded-full transition-all duration-1000 shadow-lg shadow-primary/10"
                                            style={{ width: `${progress}%` }}
                                        />
                                    </div>
                                    
                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-8 border-t border-border">
                                        <div className="space-y-1">
                                            <p className="text-[9px] uppercase font-semibold text-muted-foreground">Queued</p>
                                            <p className="text-lg font-bold text-foreground">{stats.pending || 0}</p>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-[9px] uppercase font-semibold text-muted-foreground">Active</p>
                                            <p className="text-lg font-bold text-primary">{stats.in_progress || 0}</p>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-[9px] uppercase font-semibold text-muted-foreground">Completed</p>
                                            <p className="text-lg font-bold text-green-500">{stats.completed || 0}</p>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-[9px] uppercase font-semibold text-muted-foreground">Failed</p>
                                            <p className="text-lg font-bold text-red-500">{stats.failed || 0}</p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Sidebar Config */}
                <div className="space-y-6">
                    <Card className="hover:shadow-md transition-all">
                        <CardHeader className="pb-3 border-b border-border">
                            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-foreground">Configuration</CardTitle>
                        </CardHeader>
                        <CardContent className="pt-4 space-y-4">
                            <div>
                                <p className="text-[9px] text-muted-foreground uppercase font-semibold">Assigned Agent</p>
                                <p className="text-xs text-foreground font-semibold mt-1">Linked to your voice agent</p>
                            </div>
                            <div>
                                <p className="text-[9px] text-muted-foreground uppercase font-semibold">Concurrency</p>
                                <p className="text-xs text-foreground font-semibold mt-1">{campaign.concurrency_limit} parallel calls</p>
                            </div>
                            <div>
                                <p className="text-[9px] text-muted-foreground uppercase font-semibold">Retry Logic</p>
                                <p className="text-xs text-foreground font-semibold mt-1">{campaign.retry_config?.max_retries || 3} attempts</p>
                            </div>
                            {campaign.workflow_id && (
                                <div>
                                    <p className="text-[9px] text-muted-foreground uppercase font-semibold">Workflow</p>
                                    <p className="text-xs text-cyan-500 mt-1 font-mono truncate">{workflowInfo?.workflow_name || campaign.workflow_id}</p>
                                </div>
                            )}
                            <div className="space-y-2.5">
                                <Label className="text-[9px] text-muted-foreground uppercase font-semibold block">Campaign Greeting</Label>
                                <textarea
                                    value={greeting}
                                    onChange={(e) => setGreeting(e.target.value)}
                                    rows={3}
                                    placeholder="Hi {{contactName}}..."
                                    className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                                />
                                <Button
                                    type="button"
                                    onClick={handleSaveGreeting}
                                    disabled={savingGreeting}
                                    variant="outline"
                                    size="sm"
                                    className="h-8 text-[11px]"
                                >
                                    {savingGreeting ? 'Saving…' : 'Save Greeting'}
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                    {contacts.length > 0 && (
                        <Card className="hover:shadow-md transition-all">
                            <CardHeader className="pb-3 border-b border-border">
                                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Dial Contacts</CardTitle>
                            </CardHeader>
                            <CardContent className="pt-4 max-h-80 overflow-y-auto">
                                <ul className="space-y-3 pl-0 list-none">
                                    {contacts.slice(0, 20).map((c) => (
                                        <li key={c.id} className="flex flex-col gap-1 text-xs border-b border-border/50 pb-2 last:border-0 last:pb-0">
                                            <div className="flex items-center justify-between gap-2">
                                                <span className="text-foreground font-medium truncate">{c.contact_name || c.phone_number}</span>
                                                <Button
                                                    type="button"
                                                    disabled={dialingId === c.id || c.status === 'completed'}
                                                    onClick={() => handleDialContact(c.id)}
                                                    className="h-6 px-2.5 text-[9px] bg-green-600 hover:bg-green-500 dark:bg-green-700 dark:hover:bg-green-600 text-white font-semibold rounded-md shadow-sm shrink-0 border-0"
                                                >
                                                    {dialingId === c.id ? '…' : 'Dial'}
                                                </Button>
                                            </div>
                                            {c.workflow_instance && (
                                                <p className="text-[9px] text-muted-foreground mt-0.5">
                                                    WF Status: <span className="text-primary font-semibold">{c.workflow_instance.status}</span>
                                                    {c.workflow_instance.current_node_id && (
                                                        <> · {c.workflow_instance.current_node_id}</>
                                                    )}
                                                </p>
                                            )}
                                        </li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>
                    )}

                    <Button
                        type="button"
                        variant="outline"
                        className="w-full text-red-500 hover:text-red-600 hover:bg-red-500/10 border-red-500/20"
                    >
                        <Trash2 className="size-4 mr-1.5" />
                        Delete Campaign
                    </Button>
                </div>
            </div>
        </div>
    );
}
