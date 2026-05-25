'use client';

import { useState, useEffect } from 'react';
import {
    Settings, Phone, Shield, MessageSquare,
    CreditCard, Save, CheckCircle2, Sun, Moon,
    ShieldAlert, Plus, Trash2, Edit2, ShieldCheck, AlertCircle,
    TrendingUp, Clock, Loader2, Users, Globe, Building2, Mail
} from 'lucide-react';
import { LANGUAGES, languageDisplay } from '@/lib/languages';
import { fetchPolicyRules, createPolicyRule, updatePolicyRule, deletePolicyRule, fetchBillingUsage, fetchBillingSubscription, fetchRateCard, estimateCallCost, fetchUsageRecords, fetchMyOrganization, updateMyOrganization, fetchOrgMembers, updateMemberRole } from '@/lib/api';
import { PolicyRule, UsageSummary, SubscriptionInfo, RateCardInfo, UsageRecordItem, OrganizationInfo, OrgMember } from '@/types/types';
import { useTheme } from '@/contexts/ThemeContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function SettingsPage() {
    const { theme, setTheme } = useTheme();
    const [activeTab, setActiveTab] = useState('appearance');
    
    // Form states
    const [accountSid, setAccountSid] = useState(() => typeof window !== 'undefined' ? localStorage.getItem('openvoice_twilio_sid') || '' : '');
    const [authToken, setAuthToken] = useState(() => typeof window !== 'undefined' ? localStorage.getItem('openvoice_twilio_token') || '' : '');
    const [piiRedaction, setPiiRedaction] = useState(() => {
        if (typeof window !== 'undefined') {
            const saved = localStorage.getItem('openvoice_pii_redaction');
            return saved !== null ? saved === 'true' : true;
        }
        return true;
    });
    const [pciMasking, setPciMasking] = useState(() => {
        if (typeof window !== 'undefined') {
            const saved = localStorage.getItem('openvoice_pci_masking');
            return saved !== null ? saved === 'true' : false;
        }
        return false;
    });
    
    // Policy engine state
    const [policyRules, setPolicyRules] = useState<PolicyRule[]>([]);
    const [policyLoading, setPolicyLoading] = useState(false);
    const [showNewRuleForm, setShowNewRuleForm] = useState(false);
    const [editingRuleId, setEditingRuleId] = useState<string | null>(null);
    const [ruleForm, setRuleForm] = useState({ name: '', description: '', tool_name: '*', action: 'escalate', priority: 100, enabled: true, conditions: '{}' });

    // Billing state
    const [billingUsage, setBillingUsage] = useState<UsageSummary | null>(null);
    const [billingSubscription, setBillingSubscription] = useState<SubscriptionInfo | null>(null);
    const [rateCard, setRateCard] = useState<RateCardInfo | null>(null);
    const [usageRecords, setUsageRecords] = useState<UsageRecordItem[]>([]);
    const [billingLoading, setBillingLoading] = useState(false);
    const [estimating, setEstimating] = useState(false);
    const [costEstimate, setCostEstimate] = useState<{ plan: string; estimated_cost: number } | null>(null);
    const [estimateForm, setEstimateForm] = useState({ duration_minutes: 5, stt_seconds: 300, tts_seconds: 300, llm_tokens: 5000 });

    // Organization state
    const [orgInfo, setOrgInfo] = useState<OrganizationInfo | null>(null);
    const [orgMembers, setOrgMembers] = useState<OrgMember[]>([]);
    const [orgLoading, setOrgLoading] = useState(false);
    const [orgSaving, setOrgSaving] = useState(false);
    const [orgForm, setOrgForm] = useState({ name: '' });

    // UI state
    const [isSaving, setIsSaving] = useState(false);
    const [showToast, setShowToast] = useState(false);
    const [toastMessage, setToastMessage] = useState('');

    // Load policy rules
    const loadPolicyRules = async () => {
        setPolicyLoading(true);
        try {
            const data = await fetchPolicyRules();
            setPolicyRules(data);
        } catch (err) {
            console.error('Failed to load policy rules:', err);
        } finally {
            setPolicyLoading(false);
        }
    };

    // Load billing data
    const loadBillingData = async () => {
        setBillingLoading(true);
        try {
            const [usage, sub, card, records] = await Promise.all([
                fetchBillingUsage(),
                fetchBillingSubscription(),
                fetchRateCard(),
                fetchUsageRecords(),
            ]);
            setBillingUsage(usage);
            setBillingSubscription(sub);
            setRateCard(card);
            setUsageRecords(records.records || []);
        } catch (err) {
            console.error('Failed to load billing data:', err);
        } finally {
            setBillingLoading(false);
        }
    };

    const handleEstimateCost = async () => {
        setEstimating(true);
        try {
            const result = await estimateCallCost(estimateForm);
            setCostEstimate(result);
        } catch (err) {
            console.error('Failed to estimate cost:', err);
        } finally {
            setEstimating(false);
        }
    };

    // Load organization data
    const loadOrgData = async () => {
        setOrgLoading(true);
        try {
            const [org, members] = await Promise.all([
                fetchMyOrganization(),
                fetchOrgMembers(),
            ]);
            setOrgInfo(org);
            setOrgMembers(members);
            setOrgForm({ name: org.name || '' });
        } catch (err) {
            console.error('Failed to load organization data:', err);
        } finally {
            setOrgLoading(false);
        }
    };

    const handleSaveOrg = async () => {
        setOrgSaving(true);
        try {
            const updated = await updateMyOrganization({ name: orgForm.name });
            setOrgInfo(updated);
            setToastMessage('Workspace updated successfully');
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
        } catch (err: any) {
            setToastMessage(err.message || 'Failed to update workspace');
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
        } finally {
            setOrgSaving(false);
        }
    };

    const handleMemberRoleChange = async (userId: string, role: string) => {
        try {
            await updateMemberRole(userId, role);
            setOrgMembers(prev => prev.map(m => m.id === userId ? { ...m, role } : m));
            setToastMessage('Member role updated');
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
        } catch (err: any) {
            setToastMessage(err.message || 'Failed to update role');
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
        }
    };

    useEffect(() => {
        if (activeTab === 'policy') {
            loadPolicyRules();
        }
        if (activeTab === 'billing') {
            loadBillingData();
        }
        if (activeTab === 'profile') {
            loadOrgData();
        }
    }, [activeTab]);

    const handleSaveRule = async () => {
        try {
            const payload = {
                ...ruleForm,
                conditions: JSON.parse(ruleForm.conditions || '{}'),
            };
            if (editingRuleId) {
                await updatePolicyRule(editingRuleId, payload);
            } else {
                await createPolicyRule(payload);
            }
            setShowNewRuleForm(false);
            setEditingRuleId(null);
            setRuleForm({ name: '', description: '', tool_name: '*', action: 'escalate', priority: 100, enabled: true, conditions: '{}' });
            setToastMessage(editingRuleId ? 'Rule updated successfully' : 'Rule created successfully');
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
            await loadPolicyRules();
        } catch (err: any) {
            setToastMessage(err.message || 'Failed to save rule');
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
        }
    };

    const handleDeleteRule = async (id: string) => {
        try {
            await deletePolicyRule(id);
            setToastMessage('Rule deleted successfully');
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
            await loadPolicyRules();
        } catch (err: any) {
            setToastMessage(err.message || 'Failed to delete rule');
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
        }
    };

    const startEditRule = (rule: PolicyRule) => {
        setEditingRuleId(rule.id);
        setRuleForm({
            name: rule.name,
            description: rule.description,
            tool_name: rule.tool_name,
            action: rule.action,
            priority: rule.priority,
            enabled: rule.enabled,
            conditions: JSON.stringify(rule.conditions, null, 2),
        });
        setShowNewRuleForm(true);
    };

    const handleSaveChanges = () => {
        setIsSaving(true);
        
        setTimeout(() => {
            localStorage.setItem('openvoice_twilio_sid', accountSid);
            localStorage.setItem('openvoice_twilio_token', authToken);
            localStorage.setItem('openvoice_pii_redaction', String(piiRedaction));
            localStorage.setItem('openvoice_pci_masking', String(pciMasking));
            
            setIsSaving(false);
            setToastMessage('Workspace settings successfully saved!');
            setShowToast(true);
            
            setTimeout(() => {
                setShowToast(false);
            }, 3500);
        }, 600);
    };

    const tabs = [
        { id: 'appearance', name: 'Appearance', icon: Sun },
        { id: 'profile', name: 'Profile', icon: Settings },
        { id: 'telephony', name: 'Telephony', icon: Phone },
        { id: 'compliance', name: 'Compliance', icon: Shield },
        { id: 'policy', name: 'Policy Engine', icon: ShieldAlert },
        { id: 'whatsapp', name: 'WhatsApp', icon: MessageSquare },
        { id: 'billing', name: 'Billing', icon: CreditCard },
    ];

    return (
        <div className="space-y-6 pb-10 relative">
            {/* Premium Toast Notification */}
            {showToast && (
                <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-4 bg-green-500/10 border border-green-500/30 backdrop-blur-xl rounded-2xl shadow-xl text-green-600 dark:text-green-400 text-sm font-semibold transition-all duration-300 animate-in fade-in">
                    <CheckCircle2 className="size-5 text-green-500" />
                    <span>{toastMessage}</span>
                </div>
            )}

            <div>
                <h2 className="text-2xl font-bold tracking-tight text-foreground">
                    System <span className="text-primary font-semibold">Settings</span>
                </h2>
                <p className="text-xs text-muted-foreground mt-1">Manage your workspace metadata configuration, telemetry, and payment setups.</p>
            </div>

            <div className="flex flex-col lg:flex-row gap-8">
                {/* Sidebar Tabs */}
                <div className="w-full lg:w-64 space-y-1" role="tablist" aria-label="Settings Categories">
                    {tabs.map((tab) => {
                        const isActive = activeTab === tab.id;
                        return (
                            <button
                                key={tab.id}
                                id={`tab-${tab.id}`}
                                role="tab"
                                type="button"
                                aria-selected={isActive}
                                aria-controls={`panel-${tab.id}`}
                                onClick={() => setActiveTab(tab.id)}
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-semibold uppercase tracking-wider transition-all focus:outline-none focus:ring-2 focus:ring-primary/40 ${
                                    isActive
                                        ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/15'
                                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                                }`}
                            >
                                <tab.icon className="size-4" aria-hidden="true" />
                                {tab.name}
                            </button>
                        );
                    })}
                </div>

                {/* Content Area */}
                <div className="flex-1 min-h-[450px]">

                    {/* APPEARANCE TAB */}
                    {activeTab === 'appearance' && (
                        <Card className="hover:shadow-md transition-all">
                            <CardHeader>
                                <CardTitle className="text-lg">Theme & Presentation</CardTitle>
                                <CardDescription className="text-xs">
                                    Choose how Voise AI looks across the dashboard and marketing pages.
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-lg">
                                    <button
                                        type="button"
                                        onClick={() => setTheme('light')}
                                        className={`flex flex-col items-start gap-3 p-5 rounded-2xl border-2 transition-all text-left ${
                                            theme === 'light'
                                                ? 'border-primary bg-primary/5 shadow-sm'
                                                : 'border-border bg-muted hover:border-foreground/30'
                                        }`}
                                    >
                                        <div className="flex items-center gap-2 text-foreground font-semibold text-sm">
                                            <Sun className="size-4 text-amber-500" />
                                            Light Mode
                                        </div>
                                        <p className="text-[10px] text-muted-foreground leading-relaxed">
                                            Bright workspace with soft shadows—best for daytime use.
                                        </p>
                                        <div className="w-full h-14 rounded-lg bg-background border border-border flex items-center px-3 gap-2">
                                            <div className="size-4 rounded bg-primary" />
                                            <div className="h-2 w-16 bg-muted rounded" />
                                        </div>
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setTheme('dark')}
                                        className={`flex flex-col items-start gap-3 p-5 rounded-2xl border-2 transition-all text-left ${
                                            theme === 'dark'
                                                ? 'border-primary bg-primary/5 shadow-sm'
                                                : 'border-border bg-muted hover:border-foreground/30'
                                        }`}
                                    >
                                        <div className="flex items-center gap-2 text-foreground font-semibold text-sm">
                                            <Moon className="size-4 text-primary" />
                                            Dark Mode
                                        </div>
                                        <p className="text-[10px] text-muted-foreground leading-relaxed">
                                            Glassmorphic dark UI—default Voise AI experience.
                                        </p>
                                        <div className="w-full h-14 rounded-lg bg-zinc-950 border border-border flex items-center px-3 gap-2">
                                            <div className="size-4 rounded bg-primary" />
                                            <div className="h-2 w-16 bg-muted rounded" />
                                        </div>
                                    </button>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                    
                    {/* WHATSAPP TAB */}
                    {activeTab === 'whatsapp' && (
                        <Card className="hover:shadow-md transition-all">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <MessageSquare className="size-5 text-accent" />
                                    WhatsApp Business
                                </CardTitle>
                                <CardDescription>
                                    Configure Twilio WhatsApp Business API integration.
                                    Requires a Twilio account with WhatsApp Business approved sender number.
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-5">
                                <div className="rounded-lg bg-muted/50 p-4 space-y-2">
                                    <h4 className="text-sm font-semibold">Setup Checklist</h4>
                                    <ul className="space-y-1.5 text-xs text-muted-foreground">
                                        <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-green-500 shrink-0" />1. Enable WhatsApp Business in your Twilio Console</li>
                                        <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-green-500 shrink-0" />2. Submit your sender number for Meta approval (24-48h)</li>
                                        <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-green-500 shrink-0" />3. Create message templates in Twilio Content API for proactive outreach</li>
                                        <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-amber-500 shrink-0" />4. Set your status callback URL for delivery tracking</li>
                                    </ul>
                                </div>

                                <div className="grid gap-4 md:grid-cols-2">
                                    <label className="block space-y-1.5">
                                        <span className="text-xs font-medium">WhatsApp Sender Number</span>
                                        <input
                                            type="text"
                                            className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
                                            placeholder="whatsapp:+919999999999"
                                            defaultValue="whatsapp:+919999999999"
                                        />
                                        <p className="text-[10px] text-muted-foreground">Twilio India sandbox number. Replace with your approved business number.</p>
                                    </label>
                                    <label className="block space-y-1.5">
                                        <span className="text-xs font-medium">Status Callback URL</span>
                                        <input
                                            type="text"
                                            className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
                                            placeholder="https://your-domain.com/api/v1/workflows/whatsapp/callback"
                                        />
                                        <p className="text-[10px] text-muted-foreground">Public URL for delivery status webhooks from Twilio.</p>
                                    </label>
                                </div>

                                <details className="rounded-lg bg-muted/30 p-3">
                                    <summary className="text-xs font-semibold cursor-pointer text-muted-foreground hover:text-foreground transition-colors">
                                        Available Message Templates
                                    </summary>
                                    <div className="mt-3 space-y-2 text-xs text-muted-foreground">
                                        <p><code className="bg-muted px-1.5 py-0.5 rounded text-[10px]">payment_reminder</code> — Payment reminder with amount and due date</p>
                                        <p><code className="bg-muted px-1.5 py-0.5 rounded text-[10px]">lead_nurture</code> — Lead follow-up with company info</p>
                                        <p><code className="bg-muted px-1.5 py-0.5 rounded text-[10px]">appointment_confirm</code> — Appointment confirmation with reply options</p>
                                        <p><code className="bg-muted px-1.5 py-0.5 rounded text-[10px]">payment_received</code> — Payment confirmation notice</p>
                                        <p><code className="bg-muted px-1.5 py-0.5 rounded text-[10px]">escalation_notice</code> — Case escalation notification</p>
                                        <p><code className="bg-muted px-1.5 py-0.5 rounded text-[10px]">collection_final</code> — Final collection notice (urgent)</p>
                                        <p><code className="bg-muted px-1.5 py-0.5 rounded text-[10px]">satisfaction_survey</code> — Post-call satisfaction survey</p>
                                    </div>
                                </details>

                                <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
                                    <p className="text-xs text-amber-600 dark:text-amber-400">
                                        <strong>Note:</strong> WhatsApp Business requires pre-approved templates for proactive (business-initiated) messages.
                                        Free-form messages can only be sent within 24 hours of a user-initiated message.
                                        Use the <code className="bg-amber-500/10 px-1.5 py-0.5 rounded">POST /api/v1/workflows/whatsapp/templates</code> API to create templates via the Twilio Content API.
                                    </p>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* TELEPHONY TAB */}
                    {activeTab === 'telephony' && (
                        <Card className="hover:shadow-md transition-all">
                            <CardHeader>
                                <CardTitle className="text-lg">Phone & SIP Integrations</CardTitle>
                                <CardDescription className="text-xs">
                                    Connect your business phone account for outbound and inbound calls.
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <Label htmlFor="account-sid" className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Account ID</Label>
                                        <Input
                                            id="account-sid"
                                            type="password"
                                            value={accountSid}
                                            onChange={(e) => setAccountSid(e.target.value)}
                                            placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxx"
                                            className="font-mono text-xs"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="auth-token" className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Secret Key</Label>
                                        <Input
                                            id="auth-token"
                                            type="password"
                                            value={authToken}
                                            onChange={(e) => setAuthToken(e.target.value)}
                                            placeholder="••••••••••••••••••••••••••••"
                                            className="font-mono text-xs"
                                        />
                                    </div>
                                </div>

                                <div className="p-4 bg-primary/5 border border-primary/10 rounded-xl">
                                    <p className="text-[11px] text-primary leading-relaxed">
                                        Need help connecting phone numbers? Contact Voise AI support—we’ll configure inbound routing for you.
                                    </p>
                                </div>

                                <div className="pt-6 border-t border-border">
                                    <div className="flex items-center justify-between mb-3">
                                        <h4 className="text-xs font-semibold text-foreground">Phone Numbers</h4>
                                        <a href="/dashboard/phone-numbers" className="text-[10px] text-primary hover:underline">Manage</a>
                                    </div>
                                    <p className="text-[10px] text-muted-foreground">
                                        Configure and provision phone numbers in the <a href="/dashboard/phone-numbers" className="text-primary hover:underline">Phone Numbers</a> page.
                                    </p>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* PROFILE TAB */}
                    {activeTab === 'profile' && (
                        <div className="space-y-4">
                            {/* Workspace Info */}
                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0">
                                    <div>
                                        <CardTitle className="text-lg flex items-center gap-2">
                                            <Building2 className="size-4 text-primary" />
                                            Workspace
                                        </CardTitle>
                                        <CardDescription className="text-xs mt-1">
                                            Manage your organization profile and preferences.
                                        </CardDescription>
                                    </div>
                                    {orgInfo && (
                                        <span className={`px-3 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wider border ${
                                            orgInfo.subscription_plan === 'enterprise' ? 'bg-primary/10 text-primary border-primary/20' :
                                            orgInfo.subscription_plan === 'professional' ? 'bg-blue-500/10 text-blue-500 border-blue-500/20' :
                                            'bg-muted text-muted-foreground border-border'
                                        }`}>
                                            {orgInfo.subscription_plan}
                                        </span>
                                    )}
                                </CardHeader>
                                <CardContent>
                                    {orgLoading ? (
                                        <div className="flex items-center justify-center py-8">
                                            <Loader2 className="size-5 animate-spin text-muted-foreground" />
                                        </div>
                                    ) : orgInfo ? (
                                        <div className="space-y-5">
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                <div className="space-y-1.5">
                                                    <Label className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Workspace Name</Label>
                                                    <Input
                                                        value={orgForm.name}
                                                        onChange={e => setOrgForm({ ...orgForm, name: e.target.value })}
                                                        className="text-xs"
                                                    />
                                                </div>
                                                <div className="space-y-1.5">
                                                    <Label className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Language</Label>
                                                    <select
                                                        value={orgInfo.settings?.language || 'en'}
                                                        onChange={e => updateMyOrganization({ settings: { ...orgInfo.settings, language: e.target.value } }).then(setOrgInfo)}
                                                        className="w-full bg-background border border-border rounded-xl px-4 py-2.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                                                    >
                                                        {LANGUAGES.map(l => (
                                                            <option key={l.code} value={l.code}>
                                                                {languageDisplay(l.code)}
                                                            </option>
                                                        ))}
                                                    </select>
                                                </div>
                                            </div>
                                            {orgInfo.domain && (
                                                <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-xl">
                                                    <Globe className="size-4 text-muted-foreground" />
                                                    <span className="text-xs text-muted-foreground">Domain:</span>
                                                    <span className="text-xs font-mono font-semibold">{orgInfo.domain}</span>
                                                </div>
                                            )}
                                            <div className="flex justify-end">
                                                <Button type="button" onClick={handleSaveOrg} disabled={orgSaving} className="gap-2 text-xs">
                                                    {orgSaving ? <Loader2 className="size-3 animate-spin" /> : <Save className="size-3" />}
                                                    {orgSaving ? 'Saving...' : 'Save Changes'}
                                                </Button>
                                            </div>
                                        </div>
                                    ) : (
                                        <p className="text-xs text-muted-foreground">No organization data available.</p>
                                    )}
                                </CardContent>
                            </Card>

                            {/* Team Members */}
                            <Card>
                                <CardHeader>
                                    <CardTitle className="text-lg flex items-center gap-2">
                                        <Users className="size-4 text-primary" />
                                        Team Members
                                    </CardTitle>
                                    <CardDescription className="text-xs">
                                        Manage team members and their roles.
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {orgLoading ? (
                                        <div className="flex items-center justify-center py-8">
                                            <Loader2 className="size-5 animate-spin text-muted-foreground" />
                                        </div>
                                    ) : orgMembers.length > 0 ? (
                                        <div className="space-y-2">
                                            {orgMembers.map((member) => (
                                                <div key={member.id} className="flex items-center justify-between p-3 bg-muted/30 border border-border rounded-xl hover:border-primary/20 transition-all">
                                                    <div className="flex items-center gap-3 min-w-0">
                                                        <div className="size-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xs font-bold shrink-0">
                                                            {member.full_name?.[0]?.toUpperCase() || member.email[0].toUpperCase()}
                                                        </div>
                                                        <div className="min-w-0">
                                                            <p className="text-xs font-semibold text-foreground truncate">
                                                                {member.full_name || member.email}
                                                            </p>
                                                            <p className="text-[10px] text-muted-foreground truncate">{member.email}</p>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-2 shrink-0">
                                                        <span className={`px-2 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wider border ${
                                                            member.role === 'admin' ? 'bg-primary/10 text-primary border-primary/20' :
                                                            member.role === 'manager' ? 'bg-blue-500/10 text-blue-500 border-blue-500/20' :
                                                            'bg-muted text-muted-foreground border-border'
                                                        }`}>
                                                            {member.role}
                                                        </span>
                                                        <select
                                                            value={member.role}
                                                            onChange={e => handleMemberRoleChange(member.id, e.target.value)}
                                                            className="text-[10px] bg-transparent border border-border rounded-lg px-2 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                                                            title="Change role"
                                                        >
                                                            <option value="admin">Admin</option>
                                                            <option value="manager">Manager</option>
                                                            <option value="agent">Agent</option>
                                                            <option value="viewer">Viewer</option>
                                                        </select>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="text-xs text-muted-foreground">No members found.</p>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    )}

                    {/* COMPLIANCE TAB */}
                    {activeTab === 'compliance' && (
                        <Card className="hover:shadow-md transition-all">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0">
                                <div>
                                    <CardTitle className="text-lg">Data Privacy & PII Compliance</CardTitle>
                                    <CardDescription className="text-xs mt-1">
                                        Compliant with DPDP Act, 2023. Automatically mask sensitive information in transcripts and recordings.
                                    </CardDescription>
                                </div>
                                <span className="px-2 py-0.5 bg-green-500/10 text-green-600 dark:text-green-400 text-[9px] font-semibold uppercase rounded-full border border-green-500/20 shrink-0">Active</span>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="space-y-4">
                                    {/* PII Redaction Toggle */}
                                    <div className="p-4 bg-muted/50 border border-border rounded-xl flex items-center justify-between">
                                        <div>
                                            <p className="text-xs font-semibold text-foreground">Automated PII Masking</p>
                                            <p className="text-[10px] text-muted-foreground mt-1">
                                                Automatically redact phone digits, email strings, and numbers from transcript buffers.
                                            </p>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => setPiiRedaction(!piiRedaction)}
                                            role="switch"
                                            aria-checked={piiRedaction}
                                            aria-label="Automated PII Redaction switch"
                                            className={`w-11 h-6 rounded-full p-1 transition-all duration-300 focus:outline-none ${
                                                piiRedaction ? 'bg-primary' : 'bg-input'
                                            }`}
                                        >
                                            <div
                                                className={`size-4 bg-white rounded-full transition-all duration-300 transform ${
                                                    piiRedaction ? 'translate-x-5' : 'translate-x-0'
                                                }`}
                                            />
                                        </button>
                                    </div>

                                    {/* PCI DSS Voice Masking Toggle */}
                                    <div className="p-4 bg-muted/50 border border-border rounded-xl flex items-center justify-between">
                                        <div>
                                            <p className="text-xs font-semibold text-foreground">PCI DSS Audio Redaction</p>
                                            <p className="text-[10px] text-muted-foreground mt-1">
                                                Instantly mute call streams if sensitive credit card credentials are detected.
                                            </p>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => setPciMasking(!pciMasking)}
                                            role="switch"
                                            aria-checked={pciMasking}
                                            aria-label="PCI DSS Voice Masking switch"
                                            className={`w-11 h-6 rounded-full p-1 transition-all duration-300 focus:outline-none ${
                                                pciMasking ? 'bg-primary' : 'bg-input'
                                            }`}
                                        >
                                            <div
                                                className={`size-4 bg-white rounded-full transition-all duration-300 transform ${
                                                    pciMasking ? 'translate-x-5' : 'translate-x-0'
                                                }`}
                                            />
                                        </button>
                                    </div>
                                </div>

                                <div className="flex justify-end pt-4 border-t border-border">
                                    <Button
                                        type="button"
                                        onClick={handleSaveChanges}
                                        disabled={isSaving}
                                        className="gap-2"
                                    >
                                        <Save className="size-4" />
                                        {isSaving ? 'Saving...' : 'Save Changes'}
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* POLICY ENGINE TAB */}
                    {activeTab === 'policy' && (
                        <Card className="hover:shadow-md transition-all">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0">
                                <div>
                                    <CardTitle className="text-lg">Pre-Execution Policy Engine</CardTitle>
                                    <CardDescription className="text-xs mt-1">
                                        Define rules that automatically deny, escalate, or permit agent tool calls before execution. DENY &gt; ESCALATE &gt; PERMIT.
                                    </CardDescription>
                                </div>
                                <Button
                                    type="button"
                                    onClick={() => { setShowNewRuleForm(!showNewRuleForm); setEditingRuleId(null); setRuleForm({ name: '', description: '', tool_name: '*', action: 'escalate', priority: 100, enabled: true, conditions: '{}' }); }}
                                    className="gap-2"
                                    size="sm"
                                >
                                    <Plus className="size-4" />
                                    {showNewRuleForm ? 'Cancel' : 'Add Rule'}
                                </Button>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                {/* New / Edit Rule Form */}
                                {showNewRuleForm && (
                                    <div className="p-5 bg-muted/50 border border-border rounded-xl space-y-4">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div className="space-y-1.5">
                                                <Label className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Rule Name</Label>
                                                <Input value={ruleForm.name} onChange={e => setRuleForm({...ruleForm, name: e.target.value})} placeholder="e.g. Block large refunds" className="text-xs bg-background" />
                                            </div>
                                            <div className="space-y-1.5">
                                                <Label className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Tool Name</Label>
                                                <Input value={ruleForm.tool_name} onChange={e => setRuleForm({...ruleForm, tool_name: e.target.value})} placeholder="* (all tools) or refund_customer" className="text-xs font-mono bg-background" />
                                            </div>
                                            <div className="space-y-1.5">
                                                <Label className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Action</Label>
                                                <select value={ruleForm.action} onChange={e => setRuleForm({...ruleForm, action: e.target.value})} className="w-full bg-background border border-border rounded-xl px-4 py-2.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary">
                                                    <option value="permit">PERMIT — allow execution</option>
                                                    <option value="deny">DENY — block execution</option>
                                                    <option value="escalate">ESCALATE — require human approval</option>
                                                </select>
                                            </div>
                                            <div className="space-y-1.5">
                                                <Label className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Priority (higher = first)</Label>
                                                <Input type="number" value={ruleForm.priority} onChange={e => setRuleForm({...ruleForm, priority: parseInt(e.target.value) || 0})} className="text-xs font-mono bg-background" />
                                            </div>
                                        </div>
                                        <div className="space-y-1.5">
                                            <Label className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Description</Label>
                                            <Input value={ruleForm.description} onChange={e => setRuleForm({...ruleForm, description: e.target.value})} placeholder="Why this rule exists" className="text-xs bg-background" />
                                        </div>
                                        <div className="space-y-1.5">
                                            <Label className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Conditions (JSON) — e.g. {'{"amount": {"gt": 500}}'}</Label>
                                            <textarea value={ruleForm.conditions} onChange={e => setRuleForm({...ruleForm, conditions: e.target.value})} rows={3} placeholder='{"amount": {"gt": 500}}' className="w-full bg-background border border-border rounded-xl px-4 py-2.5 text-xs text-foreground font-mono focus:outline-none focus:ring-1 focus:ring-primary" />
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <button
                                                type="button"
                                                onClick={() => setRuleForm({...ruleForm, enabled: !ruleForm.enabled})}
                                                className={`w-11 h-6 rounded-full p-1 transition-all ${ruleForm.enabled ? 'bg-primary' : 'bg-input'}`}
                                            >
                                                <div className={`size-4 bg-white rounded-full transition-all ${ruleForm.enabled ? 'translate-x-5' : 'translate-x-0'}`} />
                                            </button>
                                            <span className="text-xs text-muted-foreground">{ruleForm.enabled ? 'Enabled' : 'Disabled'}</span>
                                        </div>
                                        <div className="flex justify-end gap-3 pt-2 border-t border-border">
                                            <Button type="button" variant="outline" onClick={() => { setShowNewRuleForm(false); setEditingRuleId(null); }} className="text-xs">Cancel</Button>
                                            <Button type="button" onClick={handleSaveRule} className="text-xs">
                                                {editingRuleId ? 'Update Rule' : 'Create Rule'}
                                            </Button>
                                        </div>
                                    </div>
                                )}

                                {/* Rules List */}
                                {policyLoading ? (
                                    <div className="space-y-3">
                                        {[1, 2].map(i => <div key={i} className="h-20 bg-muted/30 border border-border rounded-xl animate-pulse" />)}
                                    </div>
                                ) : policyRules.length === 0 && !showNewRuleForm ? (
                                    <div className="flex flex-col items-center justify-center py-16 bg-muted/40 rounded-2xl border border-dashed border-border">
                                        <ShieldAlert className="size-10 text-muted-foreground mb-3" />
                                        <h4 className="text-xs font-semibold text-foreground">No policy rules configured</h4>
                                        <p className="text-[10px] text-muted-foreground mt-1 max-w-xs text-center">All tool calls will be permitted by default. Add a rule to enforce pre-execution policies.</p>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {policyRules.map((rule) => (
                                            <div key={rule.id} className="p-4 bg-card border border-border rounded-xl flex items-start justify-between gap-4 hover:border-primary/30 transition-all">
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span className={`px-2 py-0.5 rounded-full text-[9px] font-semibold uppercase tracking-wider border ${
                                                            rule.action === 'deny' ? 'bg-red-500/10 text-red-500 border-red-500/20' :
                                                            rule.action === 'escalate' ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' :
                                                            'bg-green-500/10 text-green-600 border-green-500/20'
                                                        }`}>{rule.action}</span>
                                                        <span className={`size-2 rounded-full ${rule.enabled ? 'bg-green-500' : 'bg-muted-foreground'}`} />
                                                        <span className="text-[10px] text-muted-foreground font-mono">#{rule.priority}</span>
                                                    </div>
                                                    <h4 className="text-sm font-semibold text-foreground">{rule.name}</h4>
                                                    <p className="text-[10px] text-muted-foreground mt-0.5">{rule.description}</p>
                                                    <div className="flex items-center gap-3 mt-1.5">
                                                        <span className="text-[9px] font-mono text-primary bg-primary/5 px-2 py-0.5 rounded">{rule.tool_name === '*' ? 'ALL TOOLS' : `tool: ${rule.tool_name}`}</span>
                                                        {Object.keys(rule.conditions).length > 0 && (
                                                            <span className="text-[9px] font-mono text-muted-foreground">{JSON.stringify(rule.conditions).slice(0, 40)}...</span>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2 shrink-0">
                                                    <Button type="button" variant="ghost" size="sm" onClick={() => startEditRule(rule)} className="text-[10px] h-7 px-2">Edit</Button>
                                                    <Button type="button" variant="ghost" size="sm" onClick={() => handleDeleteRule(rule.id)} className="h-7 w-7 p-0 text-red-500 hover:text-red-600 hover:bg-red-500/10">
                                                        <Trash2 className="size-3.5" />
                                                    </Button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                <div className="p-4 bg-amber-500/5 border border-amber-500/10 rounded-2xl flex items-start gap-4">
                                    <ShieldAlert className="size-5 text-amber-500 shrink-0 mt-0.5" />
                                    <div>
                                        <h4 className="text-xs font-semibold text-foreground">Policy Precedence</h4>
                                        <p className="text-[10px] text-muted-foreground mt-1 leading-relaxed">
                                            Rules are evaluated in priority order (highest first). The first matching rule with action DENY immediately blocks execution. If no DENY matches but an ESCALATE matches, the action is sent for human approval. If no rule matches, the action is PERMITted by default.
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* BILLING TAB */}
                    {activeTab === 'billing' && (
                        <div className="space-y-4">
                            {/* Trial Banner */}
                            {billingUsage?.trial?.active && billingUsage.trial.days_remaining !== undefined && billingUsage.trial.days_remaining >= 0 && (
                                <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 dark:bg-emerald-500/10">
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="flex items-start gap-3">
                                            <div className="size-8 rounded-full bg-emerald-500/15 flex items-center justify-center shrink-0 mt-0.5">
                                                <Clock className="size-4 text-emerald-500" />
                                            </div>
                                            <div>
                                                <p className="text-sm font-semibold text-foreground">Trial Active</p>
                                                <p className="text-xs text-muted-foreground mt-0.5">
                                                    {billingUsage.trial.days_remaining > 0
                                                        ? `${billingUsage.trial.days_remaining} day${billingUsage.trial.days_remaining !== 1 ? 's' : ''} remaining`
                                                        : 'Less than a day remaining'}
                                                    {' — '}
                                                    {billingUsage.limits?.call_minutes === 50
                                                        ? '50 call minutes included. No credit card required.'
                                                        : `${billingUsage.usage?.call_minutes ?? 0} / ${billingUsage.limits?.call_minutes ?? 50} minutes used.`}
                                                </p>
                                            </div>
                                        </div>
                                        <span className="px-2.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-widest bg-emerald-500/15 text-emerald-500 border border-emerald-500/20 shrink-0">
                                            {billingUsage.trial.days_remaining}d left
                                        </span>
                                    </div>
                                </div>
                            )}

                            {/* Plan + Subscription Summary */}
                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0">
                                    <div>
                                        <CardTitle className="text-lg">Billing & Plan</CardTitle>
                                        <CardDescription className="text-xs mt-1">
                                            Usage metering, subscription, and rate card details.
                                        </CardDescription>
                                    </div>
                                    {billingSubscription && (
                                        <span className={`px-3 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wider border ${
                                            billingSubscription.plan === 'enterprise' ? 'bg-primary/10 text-primary border-primary/20' :
                                            billingSubscription.plan === 'professional' ? 'bg-blue-500/10 text-blue-500 border-blue-500/20' :
                                            'bg-muted text-muted-foreground border-border'
                                        }`}>
                                            {billingSubscription.plan}
                                        </span>
                                    )}
                                </CardHeader>
                                <CardContent>
                                    {billingLoading ? (
                                        <div className="flex items-center justify-center py-8">
                                            <Loader2 className="size-5 animate-spin text-muted-foreground" />
                                        </div>
                                    ) : billingSubscription ? (
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                            <div className="p-3 bg-muted/50 rounded-xl">
                                                <p className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Plan</p>
                                                <p className="text-sm font-bold text-foreground mt-1 capitalize">{billingSubscription.plan}</p>
                                            </div>
                                            <div className="p-3 bg-muted/50 rounded-xl">
                                                <p className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Status</p>
                                                <p className="text-sm font-bold text-foreground mt-1 capitalize">{billingSubscription.status}</p>
                                            </div>
                                            <div className="p-3 bg-muted/50 rounded-xl">
                                                <p className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Period Start</p>
                                                <p className="text-sm font-bold text-foreground mt-1">{new Date(billingSubscription.billing_period_start).toLocaleDateString()}</p>
                                            </div>
                                            {billingSubscription.billing_period_end && (
                                                <div className="p-3 bg-muted/50 rounded-xl">
                                                    <p className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Period End</p>
                                                    <p className="text-sm font-bold text-foreground mt-1">{new Date(billingSubscription.billing_period_end).toLocaleDateString()}</p>
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <p className="text-xs text-muted-foreground">No subscription data available.</p>
                                    )}
                                </CardContent>
                            </Card>

                            {/* Usage Bars */}
                            {billingUsage && billingUsage.usage && (
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="text-lg flex items-center gap-2">
                                            <TrendingUp className="size-4 text-primary" />
                                            Usage This Period
                                        </CardTitle>
                                        <CardDescription className="text-xs">
                                            Current billing period usage against plan limits.
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        {Object.entries(billingUsage.usage).map(([metric, used]) => {
                                            const limit = billingUsage.limits?.[metric];
                                            const pct = billingUsage.percentages?.[metric] ?? (limit && limit > 0 ? Math.round((used / limit) * 100) : 0);
                                            const isNear = pct >= 80 && pct < 100;
                                            const isOver = pct >= 100;
                                            return (
                                                <div key={metric} className="space-y-1.5">
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-xs font-medium text-foreground capitalize">{metric.replace(/_/g, ' ')}</span>
                                                        <span className={`text-[10px] font-mono ${isOver ? 'text-red-500' : isNear ? 'text-amber-500' : 'text-muted-foreground'}`}>
                                                            {used}{limit !== undefined ? ` / ${limit}` : ''}
                                                        </span>
                                                    </div>
                                                    {limit !== undefined && limit > 0 && (
                                                        <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                                                            <div
                                                                className={`h-full rounded-full transition-all duration-500 ${
                                                                    isOver ? 'bg-red-500' : isNear ? 'bg-amber-500' : 'bg-primary'
                                                                }`}
                                                                style={{ width: `${Math.min(pct, 100)}%` }}
                                                            />
                                                        </div>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </CardContent>
                                </Card>
                            )}

                            {/* Rate Card */}
                            {rateCard && rateCard.rates && (
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="text-lg">Rate Card</CardTitle>
                                        <CardDescription className="text-xs">
                                            Pricing per unit for the <strong className="capitalize">{rateCard.plan}</strong> plan.
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-xs">
                                                <thead>
                                                    <tr className="border-b border-border">
                                                        <th className="text-left py-2 px-2 font-semibold text-muted-foreground">Metric</th>
                                                        <th className="text-right py-2 px-2 font-semibold text-muted-foreground">Unit</th>
                                                        <th className="text-right py-2 px-2 font-semibold text-muted-foreground">Price/Unit</th>
                                                        <th className="text-right py-2 px-2 font-semibold text-muted-foreground">Included</th>
                                                        <th className="text-right py-2 px-2 font-semibold text-muted-foreground">Overage</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {Object.entries(rateCard.rates).map(([metric, rate]) => (
                                                        <tr key={metric} className="border-b border-border/50 hover:bg-muted/30">
                                                            <td className="py-2 px-2 font-medium capitalize">{metric.replace(/_/g, ' ')}</td>
                                                            <td className="py-2 px-2 text-right text-muted-foreground">{rate.unit}</td>
                                                            <td className="py-2 px-2 text-right font-mono">₹{rate.price_per_unit.toFixed(4)}</td>
                                                            <td className="py-2 px-2 text-right font-mono">{rate.included_units.toLocaleString()}</td>
                                                            <td className="py-2 px-2 text-right font-mono">{rate.overage_price_per_unit != null ? `₹${Number(rate.overage_price_per_unit).toFixed(4)}` : '—'}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </CardContent>
                                </Card>
                            )}

                            {/* Cost Estimator */}
                            <Card>
                                <CardHeader>
                                    <CardTitle className="text-lg flex items-center gap-2">
                                        <Clock className="size-4 text-primary" />
                                        Cost Estimator
                                    </CardTitle>
                                    <CardDescription className="text-xs">
                                        Estimate call costs based on current rate card.
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <div className="space-y-1.5">
                                            <Label className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">Duration (min)</Label>
                                            <Input type="number" min={0} value={estimateForm.duration_minutes} onChange={e => setEstimateForm({...estimateForm, duration_minutes: parseFloat(e.target.value) || 0})} className="text-xs" />
                                        </div>
                                        <div className="space-y-1.5">
                                            <Label className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">STT (sec)</Label>
                                            <Input type="number" min={0} value={estimateForm.stt_seconds} onChange={e => setEstimateForm({...estimateForm, stt_seconds: parseFloat(e.target.value) || 0})} className="text-xs" />
                                        </div>
                                        <div className="space-y-1.5">
                                            <Label className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">TTS (sec)</Label>
                                            <Input type="number" min={0} value={estimateForm.tts_seconds} onChange={e => setEstimateForm({...estimateForm, tts_seconds: parseFloat(e.target.value) || 0})} className="text-xs" />
                                        </div>
                                        <div className="space-y-1.5">
                                            <Label className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider">LLM Tokens</Label>
                                            <Input type="number" min={0} value={estimateForm.llm_tokens} onChange={e => setEstimateForm({...estimateForm, llm_tokens: parseInt(e.target.value) || 0})} className="text-xs" />
                                        </div>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <Button type="button" onClick={handleEstimateCost} disabled={estimating} className="gap-2 text-xs">
                                            {estimating ? <Loader2 className="size-3 animate-spin" /> : null}
                                            {estimating ? 'Estimating...' : 'Estimate Cost'}
                                        </Button>
                                        {costEstimate !== null && (
                                            <div className="text-right">
                                                <p className="text-[10px] text-muted-foreground">Estimated cost ({costEstimate.plan})</p>
                                                <p className="text-lg font-bold text-primary">₹{costEstimate.estimated_cost.toFixed(4)}</p>
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Recent Usage Records */}
                            {usageRecords.length > 0 && (
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="text-lg">Recent Usage Records</CardTitle>
                                        <CardDescription className="text-xs">Latest {usageRecords.length} usage events this period.</CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-2 max-h-64 overflow-y-auto">
                                            {usageRecords.slice(0, 20).map((rec) => (
                                                <div key={rec.id} className="flex items-center justify-between p-2 bg-muted/30 rounded-lg">
                                                    <div>
                                                        <span className="text-xs font-medium text-foreground capitalize">{rec.metric.replace(/_/g, ' ')}</span>
                                                        <span className="text-[10px] text-muted-foreground ml-2">{rec.unit}</span>
                                                    </div>
                                                    <div className="text-right">
                                                        <span className="text-xs font-mono font-semibold">{rec.quantity}</span>
                                                        <span className="text-[9px] text-muted-foreground ml-2">{new Date(rec.recorded_at).toLocaleString()}</span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
