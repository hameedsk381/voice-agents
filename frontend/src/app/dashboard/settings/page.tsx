'use client';

import { useState, useEffect } from 'react';
import {
    Settings, Phone, Shield,
    CreditCard, Save, CheckCircle2, Sun, Moon
} from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';

export default function SettingsPage() {
    const { theme, setTheme } = useTheme();
    const [activeTab, setActiveTab] = useState('appearance');
    
    // Form states
    const [accountSid, setAccountSid] = useState('');
    const [authToken, setAuthToken] = useState('');
    const [piiRedaction, setPiiRedaction] = useState(true);
    const [pciMasking, setPciMasking] = useState(false);
    
    // UI state
    const [isSaving, setIsSaving] = useState(false);
    const [showToast, setShowToast] = useState(false);

    // Hydration-safe client-side loader
    useEffect(() => {
        const savedSid = localStorage.getItem('openvoice_twilio_sid') || '';
        const savedToken = localStorage.getItem('openvoice_twilio_token') || '';
        const savedPii = localStorage.getItem('openvoice_pii_redaction');
        const savedPci = localStorage.getItem('openvoice_pci_masking');
        
        if (savedSid) setAccountSid(savedSid);
        if (savedToken) setAuthToken(savedToken);
        if (savedPii !== null) setPiiRedaction(savedPii === 'true');
        if (savedPci !== null) setPciMasking(savedPci === 'true');
    }, []);

    const handleSaveChanges = () => {
        setIsSaving(true);
        
        setTimeout(() => {
            localStorage.setItem('openvoice_twilio_sid', accountSid);
            localStorage.setItem('openvoice_twilio_token', authToken);
            localStorage.setItem('openvoice_pii_redaction', String(piiRedaction));
            localStorage.setItem('openvoice_pci_masking', String(pciMasking));
            
            setIsSaving(false);
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
        { id: 'billing', name: 'Billing', icon: CreditCard },
    ];

    return (
        <div className="space-y-6 pb-10 relative">
            {/* Premium Toast Notification */}
            {showToast && (
                <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-4 bg-[var(--accent-emerald)]/10 border border-[var(--accent-emerald)]/30 backdrop-blur-xl rounded-2xl shadow-xl text-[var(--accent-emerald)] text-sm font-semibold transition-all duration-300 animate-in">
                    <CheckCircle2 className="w-5 h-5 text-[var(--accent-emerald)]" />
                    <span>Workspace settings successfully saved!</span>
                </div>
            )}

            <div>
                <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                    System <span className="text-gradient-brand">Settings</span>
                </h2>
                <p className="text-xs text-[var(--text-secondary)] mt-1">Manage your workspace metadata configuration, telemetry, and payment setups.</p>
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
                                aria-selected={isActive}
                                aria-controls={`panel-${tab.id}`}
                                onClick={() => setActiveTab(tab.id)}
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-semibold uppercase tracking-wider transition-all focus:outline-none focus:ring-2 focus:ring-[var(--accent-cyan)]/40 ${
                                    isActive
                                        ? 'bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white shadow-lg shadow-[var(--accent-cyan)]/15'
                                        : 'text-[var(--text-secondary)] hover:bg-[var(--bg-overlay)] hover:text-[var(--text-primary)]'
                                }`}
                            >
                                <tab.icon className="w-4 h-4" aria-hidden="true" />
                                {tab.name}
                            </button>
                        );
                    })}
                </div>

                {/* Content Area */}
                <div className="flex-1 glass-card p-8 min-h-[450px]">

                    {/* APPEARANCE TAB */}
                    {activeTab === 'appearance' && (
                        <div id="panel-appearance" role="tabpanel" aria-labelledby="tab-appearance" className="space-y-6 animate-fade">
                            <div className="pb-5 border-b border-[var(--border-subtle)]">
                                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Theme</h3>
                                <p className="text-[10px] text-[var(--text-secondary)] mt-1">
                                    Choose how Voise AI looks across the dashboard and marketing pages.
                                </p>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-lg">
                                <button
                                    type="button"
                                    onClick={() => setTheme('light')}
                                    className={`flex flex-col items-start gap-3 p-5 rounded-2xl border-2 transition-all text-left ${
                                        theme === 'light'
                                            ? 'border-[var(--accent-cyan)] bg-[var(--accent-cyan)]/5 shadow-md'
                                            : 'border-[var(--border-default)] bg-[var(--bg-overlay)] hover:border-[var(--border-active)]'
                                    }`}
                                >
                                    <div className="flex items-center gap-2 text-[var(--text-primary)] font-semibold text-sm">
                                        <Sun className="w-4 h-4 text-[var(--accent-amber)]" />
                                        Light
                                    </div>
                                    <p className="text-[10px] text-[var(--text-secondary)] leading-relaxed">
                                        Bright workspace with soft shadows—best for daytime use.
                                    </p>
                                    <div className="w-full h-14 rounded-lg bg-gradient-to-br from-[#F4F5F9] to-white border border-[var(--border-subtle)]" />
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setTheme('dark')}
                                    className={`flex flex-col items-start gap-3 p-5 rounded-2xl border-2 transition-all text-left ${
                                        theme === 'dark'
                                            ? 'border-[var(--accent-cyan)] bg-[var(--accent-cyan)]/5 shadow-md'
                                            : 'border-[var(--border-default)] bg-[var(--bg-overlay)] hover:border-[var(--border-active)]'
                                    }`}
                                >
                                    <div className="flex items-center gap-2 text-[var(--text-primary)] font-semibold text-sm">
                                        <Moon className="w-4 h-4 text-[var(--accent-purple)]" />
                                        Dark
                                    </div>
                                    <p className="text-[10px] text-[var(--text-secondary)] leading-relaxed">
                                        Glassmorphic dark UI—default Voise AI experience.
                                    </p>
                                    <div className="w-full h-14 rounded-lg bg-gradient-to-br from-[#08080C] to-[#16161E] border border-[var(--border-subtle)]" />
                                </button>
                            </div>
                        </div>
                    )}
                    
                    {/* TELEPHONY TAB */}
                    {activeTab === 'telephony' && (
                        <div id="panel-telephony" role="tabpanel" aria-labelledby="tab-telephony" className="space-y-6 animate-fade">
                            <div className="pb-5 border-b border-[var(--border-subtle)]">
                                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Phone numbers</h3>
                                <p className="text-[10px] text-[var(--text-secondary)] mt-1">Connect your business phone account for outbound and inbound calls.</p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label htmlFor="account-sid" className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Account ID</label>
                                    <input
                                        id="account-sid"
                                        type="password"
                                        value={accountSid}
                                        onChange={(e) => setAccountSid(e.target.value)}
                                        placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxx"
                                        aria-label="Phone account ID"
                                        className="w-full bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl px-4 py-3 text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-cyan)] font-mono transition-all focus:ring-4 focus:ring-[var(--accent-cyan)]/5"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label htmlFor="auth-token" className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Secret key</label>
                                    <input
                                        id="auth-token"
                                        type="password"
                                        value={authToken}
                                        onChange={(e) => setAuthToken(e.target.value)}
                                        placeholder="••••••••••••••••••••••••••••"
                                        aria-label="Phone account secret"
                                        className="w-full bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl px-4 py-3 text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-cyan)] font-mono transition-all focus:ring-4 focus:ring-[var(--accent-cyan)]/5"
                                    />
                                </div>
                            </div>

                            <div className="p-4 bg-[var(--accent-blue)]/5 border border-[var(--accent-blue)]/10 rounded-xl">
                                <p className="text-[11px] text-[var(--accent-blue)] leading-relaxed">
                                    Need help connecting phone numbers? Contact Voise AI support—we’ll configure inbound routing for you.
                                </p>
                            </div>

                            <div className="pt-6 border-t border-[var(--border-subtle)]">
                                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Verified Numbers</h3>
                                <div className="mt-4">
                                    <div className="flex items-center justify-between p-4 bg-[var(--bg-overlay)] rounded-xl border border-[var(--border-subtle)]">
                                        <div className="flex items-center gap-3">
                                            <div className="w-9 h-9 rounded-full bg-[var(--accent-emerald)]/10 flex items-center justify-center text-[var(--accent-emerald)]">
                                                <Phone className="w-4 h-4" />
                                            </div>
                                            <div>
                                                <p className="text-xs font-bold text-[var(--text-primary)]">+1 (555) 000-1234</p>
                                                <p className="text-[9px] text-[var(--text-tertiary)] italic">Provisioned in US-East-1</p>
                                            </div>
                                        </div>
                                        <span className="px-2 py-0.5 rounded bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] text-[9px] font-bold uppercase border border-[var(--accent-blue)]/20">Primary</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex justify-end pt-4 border-t border-[var(--border-subtle)]">
                                <button
                                    onClick={handleSaveChanges}
                                    disabled={isSaving}
                                    className="flex items-center gap-2 bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white px-5 py-2.5 rounded-xl font-bold text-xs transition-all disabled:opacity-60 hover:-translate-y-0.5 active:translate-y-0 active:scale-98"
                                >
                                    <Save className="w-4 h-4" />
                                    {isSaving ? 'Saving...' : 'Save Changes'}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* PROFILE TAB */}
                    {activeTab === 'profile' && (
                        <div id="panel-profile" role="tabpanel" aria-labelledby="tab-profile" className="space-y-6 animate-fade">
                            <div className="pb-5 border-b border-[var(--border-subtle)]">
                                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Organization Metadata</h3>
                                <p className="text-[10px] text-[var(--text-secondary)] mt-1">Configure profile metrics and defaults.</p>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 opacity-40 cursor-not-allowed">
                                <div className="space-y-2">
                                    <label className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Workspace Name</label>
                                    <input disabled value="Voise AI Production" className="w-full bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl px-4 py-3 text-xs text-white" />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider">Workspace Language</label>
                                    <select disabled className="w-full bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl px-4 py-3 text-xs text-white">
                                        <option>English (US)</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div className="flex flex-col items-center justify-center py-10 text-center bg-[var(--bg-overlay)] rounded-2xl border border-dashed border-[var(--border-default)]">
                                <div className="w-10 h-10 bg-[var(--accent-cyan)]/10 rounded-full flex items-center justify-center mb-4">
                                    <Settings className="w-5 h-5 text-[var(--accent-cyan)]" />
                                </div>
                                <h4 className="text-xs font-bold text-[var(--text-primary)]">Enterprise Management</h4>
                                <p className="text-[10px] text-[var(--text-tertiary)] mt-1 max-w-xs leading-relaxed">Additional workspace configs and role integrations will be accessible in the upcoming release.</p>
                            </div>
                        </div>
                    )}

                    {/* COMPLIANCE TAB */}
                    {activeTab === 'compliance' && (
                        <div id="panel-compliance" role="tabpanel" aria-labelledby="tab-compliance" className="space-y-6 animate-fade">
                            <div className="pb-5 border-b border-[var(--border-subtle)] flex justify-between items-center">
                                <div>
                                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">GDPR & PII Compliance</h3>
                                    <p className="text-[10px] text-[var(--text-secondary)] mt-1">Automatically mask sensitive information in transcripts and recordings.</p>
                                </div>
                                <span className="px-2 py-0.5 bg-[var(--accent-emerald)]/10 text-[var(--accent-emerald)] text-[9px] font-bold uppercase rounded-full border border-[var(--accent-emerald)]/20">Active</span>
                            </div>

                            <div className="space-y-4">
                                {/* PII Redaction Toggle */}
                                <div className="p-4 bg-[var(--bg-overlay)] border border-[var(--border-subtle)] rounded-xl flex items-center justify-between">
                                    <div>
                                        <p className="text-xs font-bold text-[var(--text-primary)]">Automated PII Masking</p>
                                        <p className="text-[10px] text-[var(--text-secondary)] mt-1">Automatically redact phone digits, email strings, and numbers from transcript buffers.</p>
                                    </div>
                                    <button
                                        onClick={() => setPiiRedaction(!piiRedaction)}
                                        role="switch"
                                        aria-checked={piiRedaction}
                                        aria-label="Automated PII Redaction switch"
                                        className={`w-11 h-6 rounded-full p-1 transition-all duration-300 focus:outline-none ${
                                            piiRedaction ? 'bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)]' : 'bg-white/[0.08]'
                                        }`}
                                    >
                                        <div
                                            className={`w-4 h-4 bg-white rounded-full transition-all duration-300 transform ${
                                                piiRedaction ? 'translate-x-5' : 'translate-x-0'
                                            }`}
                                        />
                                    </button>
                                </div>

                                {/* PCI DSS Voice Masking Toggle */}
                                <div className="p-4 bg-[var(--bg-overlay)] border border-[var(--border-subtle)] rounded-xl flex items-center justify-between">
                                    <div>
                                        <p className="text-xs font-bold text-[var(--text-primary)]">PCI DSS Audio Redaction</p>
                                        <p className="text-[10px] text-[var(--text-secondary)] mt-1">Instantly mute call streams if sensitive credit card credentials are detected.</p>
                                    </div>
                                    <button
                                        onClick={() => setPciMasking(!pciMasking)}
                                        role="switch"
                                        aria-checked={pciMasking}
                                        aria-label="PCI DSS Voice Masking switch"
                                        className={`w-11 h-6 rounded-full p-1 transition-all duration-300 focus:outline-none ${
                                            pciMasking ? 'bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)]' : 'bg-white/[0.08]'
                                        }`}
                                    >
                                        <div
                                            className={`w-4 h-4 bg-white rounded-full transition-all duration-300 transform ${
                                                pciMasking ? 'translate-x-5' : 'translate-x-0'
                                            }`}
                                        />
                                    </button>
                                </div>
                            </div>

                            <div className="flex justify-end pt-4 border-t border-[var(--border-subtle)]">
                                <button
                                    onClick={handleSaveChanges}
                                    disabled={isSaving}
                                    className="flex items-center gap-2 bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white px-5 py-2.5 rounded-xl font-bold text-xs transition-all disabled:opacity-60 hover:-translate-y-0.5 active:translate-y-0 active:scale-98"
                                >
                                    <Save className="w-4 h-4" />
                                    {isSaving ? 'Saving...' : 'Save Changes'}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* BILLING TAB */}
                    {activeTab === 'billing' && (
                        <div id="panel-billing" role="tabpanel" aria-labelledby="tab-billing" className="flex flex-col items-center justify-center py-20 text-center animate-fade">
                            <div className="w-12 h-12 bg-[var(--bg-overlay)] border border-[var(--border-subtle)] rounded-full flex items-center justify-center mb-4 text-[var(--text-tertiary)]">
                                <CreditCard className="w-5 h-5" />
                            </div>
                            <h3 className="text-xs font-bold text-[var(--text-primary)]">Billing & Plan</h3>
                            <p className="text-[10px] text-[var(--text-tertiary)] mt-2 max-w-xs italic leading-relaxed">
                                Pricing schemes are currently inactive. You are on the free tier <span className="text-[var(--accent-cyan)] font-bold">Enterprise Beta</span> plan.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
