'use client';

import { useState } from 'react';
import {
    Settings, Phone, Shield,
    Bell, Globe, CreditCard, Save
} from 'lucide-react';

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState('telephony');

    const tabs = [
        { id: 'profile', name: 'Profile', icon: Settings },
        { id: 'telephony', name: 'Telephony', icon: Phone },
        { id: 'compliance', name: 'Compliance', icon: Shield },
        { id: 'billing', name: 'Billing', icon: CreditCard },
    ];

    return (
        <div className="space-y-8 pb-10">
            <div>
                <h1 className="text-2xl font-bold text-white">System Settings</h1>
                <p className="text-gray-400">Manage your workspace configuration and telephony providers.</p>
            </div>

            <div className="flex flex-col lg:flex-row gap-8">
                {/* Sidebar Tabs */}
                <div className="w-full lg:w-64 space-y-1">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === tab.id
                                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
                                : 'text-gray-400 hover:bg-white/5 hover:text-white'
                                }`}
                        >
                            <tab.icon className="w-4 h-4" />
                            {tab.name}
                        </button>
                    ))}
                </div>

                {/* Content Area */}
                <div className="flex-1 bg-[#141417] border border-white/10 rounded-2xl p-8">
                    {activeTab === 'telephony' && (
                        <div className="space-y-6">
                            <div className="pb-6 border-b border-white/5">
                                <h3 className="text-lg font-semibold text-white">Twilio Configuration</h3>
                                <p className="text-sm text-gray-400 mt-1">Connect your Twilio account to enable PSTN calling.</p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Account SID</label>
                                    <input
                                        type="password"
                                        placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxx"
                                        className="w-full bg-black/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 font-mono text-sm"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Auth Token</label>
                                    <input
                                        type="password"
                                        placeholder="••••••••••••••••••••••••••••"
                                        className="w-full bg-black/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 font-mono text-sm"
                                    />
                                </div>
                            </div>

                            <div className="p-4 bg-blue-500/5 border border-blue-500/10 rounded-xl">
                                <p className="text-xs text-blue-400 leading-relaxed italic">
                                    Tip: Set your Twilio Voice Webhook to: <span className="font-mono bg-black/30 px-1 rounded">https://your-api.com/api/v1/telephony/voice</span>
                                </p>
                            </div>

                            <div className="pt-6 border-t border-white/5">
                                <h3 className="text-lg font-semibold text-white">Default Numbers</h3>
                                <div className="mt-4 space-y-4">
                                    <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5 shadow-inner">
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-full bg-green-500/10 flex items-center justify-center">
                                                <Phone className="w-5 h-5 text-green-500" />
                                            </div>
                                            <div>
                                                <p className="text-sm font-bold text-white">+1 (555) 000-1234</p>
                                                <p className="text-xs text-gray-500 italic">Provisioned in US-East-1</p>
                                            </div>
                                        </div>
                                        <span className="px-2 py-1 rounded bg-blue-500/10 text-blue-500 text-[10px] font-bold uppercase transition-all">Primary</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex justify-end pt-4">
                                <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-6 py-2.5 rounded-xl font-bold text-sm transition-all">
                                    <Save className="w-4 h-4" />
                                    Save Changes
                                </button>
                            </div>
                        </div>
                    )}

                    {activeTab === 'profile' && (
                        <div className="space-y-6">
                            <div className="pb-6 border-b border-white/5">
                                <h3 className="text-lg font-semibold text-white">Organization Profile</h3>
                                <p className="text-sm text-gray-400 mt-1">Update your workspace details and branding.</p>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 opacity-50 cursor-not-allowed">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Workspace Name</label>
                                    <input disabled value="OpenVoice Production" className="w-full bg-black/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none" />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Default Language</label>
                                    <select disabled className="w-full bg-black/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none">
                                        <option>English (US)</option>
                                    </select>
                                </div>
                            </div>
                            <div className="flex flex-col items-center justify-center py-10 text-center bg-white/5 rounded-2xl border border-dashed border-white/10">
                                <div className="w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center mb-4">
                                    <Settings className="w-6 h-6 text-blue-500" />
                                </div>
                                <h4 className="text-white font-medium">Profile Management</h4>
                                <p className="text-gray-500 text-sm mt-1 max-w-xs">User roles and workspace customization will be enabled in the Q1 update.</p>
                            </div>
                        </div>
                    )}

                    {activeTab === 'compliance' && (
                        <div className="space-y-6">
                            <div className="pb-6 border-b border-white/5 flex justify-between items-center">
                                <div>
                                    <h3 className="text-lg font-semibold text-white">Compliance & PII</h3>
                                    <p className="text-sm text-gray-400 mt-1">Configure automated data redaction and GDPR policies.</p>
                                </div>
                                <span className="px-3 py-1 bg-green-500/10 text-green-500 text-[10px] font-bold uppercase rounded-full border border-green-500/20">Active</span>
                            </div>

                            <div className="space-y-4">
                                <div className="p-4 bg-white/5 rounded-xl border border-white/10 flex items-center justify-between">
                                    <div>
                                        <p className="text-sm font-medium text-white">Automated PII Redaction</p>
                                        <p className="text-xs text-gray-500">Automatically mask emails, phones, and credit cards in transcripts.</p>
                                    </div>
                                    <div className="w-10 h-5 bg-blue-600 rounded-full relative">
                                        <div className="absolute right-1 top-1 w-3 h-3 bg-white rounded-full"></div>
                                    </div>
                                </div>
                                <div className="p-4 bg-white/5 rounded-xl border border-white/10 flex items-center justify-between opacity-50">
                                    <div>
                                        <p className="text-sm font-medium text-white">PCI DSS Voice Masking</p>
                                        <p className="text-xs text-gray-500">Stop recording when sensitive payment information is detected.</p>
                                    </div>
                                    <div className="w-10 h-5 bg-gray-700 rounded-full relative">
                                        <div className="absolute left-1 top-1 w-3 h-3 bg-white rounded-full"></div>
                                    </div>
                                </div>
                            </div>

                            <div className="p-4 bg-yellow-500/5 border border-yellow-500/10 rounded-xl">
                                <p className="text-xs text-yellow-500 leading-relaxed">
                                    Note: Advanced custom regex redaction and audit logs are coming in the next release.
                                </p>
                            </div>
                        </div>
                    )}

                    {activeTab === 'billing' && (
                        <div className="flex flex-col items-center justify-center py-20 text-center">
                            <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mb-4">
                                <CreditCard className="w-8 h-8 text-gray-600" />
                            </div>
                            <h3 className="text-lg font-medium text-white">Billing & Subscription</h3>
                            <p className="text-gray-500 text-sm mt-2 max-w-xs italic">Pricing plans are being finalized. You are currently on the <span className="text-blue-500 font-bold">Enterprise Beta</span> (Free Access).</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
