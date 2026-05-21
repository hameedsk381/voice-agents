'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { Mic, ArrowRight } from 'lucide-react';

export default function RegisterPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { register } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        if (password.length < 8) {
            setError('Password must be at least 8 characters');
            return;
        }

        setIsLoading(true);

        try {
            await register(email, password, fullName || undefined);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Registration failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex bg-[var(--bg-base)]">
            {/* LEFT PANEL — Brand Display (hidden on mobile) */}
            <div className="hidden lg:flex w-1/2 bg-[var(--bg-surface)] relative overflow-hidden flex-col justify-between p-16 border-r border-[var(--border-subtle)]">
                {/* Background ambient orbs */}
                <div className="absolute top-[-200px] left-[-100px] w-[500px] h-[500px] rounded-full bg-[radial-gradient(circle,rgba(0,212,170,0.15)_0%,transparent_70%)] blur-[40px] pointer-events-none" />
                <div className="absolute bottom-[-200px] right-[-100px] w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle,rgba(139,92,246,0.12)_0%,transparent_70%)] blur-[40px] pointer-events-none" />
                
                {/* Dot grid */}
                <div className="absolute inset-0 dot-grid opacity-[0.03] pointer-events-none" />

                {/* Top header */}
                <Link href="/" className="flex items-center gap-2.5 z-10">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--accent-cyan)] to-[var(--accent-purple)] flex items-center justify-center shadow-lg shadow-[var(--accent-cyan)]/25">
                        <span className="text-white font-bold text-sm">V</span>
                    </div>
                    <span className="text-lg font-semibold tracking-tight text-[var(--text-primary)]">Voise AI</span>
                </Link>

                {/* Middle illustration / copy */}
                <div className="space-y-6 z-10 max-w-md my-auto">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--accent-cyan)]/10 to-[var(--accent-purple)]/10 border border-[var(--border-default)] flex items-center justify-center text-[var(--accent-cyan)] glow-brand">
                        <Mic className="w-7 h-7" />
                    </div>
                    <h2 className="text-3xl font-bold leading-tight">
                        Automate Your <span className="text-gradient-brand">Operational Workflows</span>
                    </h2>
                    <p className="text-[var(--text-secondary)] leading-relaxed">
                        Create an account to deploy AI outbound call agents, send payment reminders, qualify leads, and confirm appointments automatically.
                    </p>
                    
                    <div className="space-y-3 pt-4">
                        {[
                            "AI outbound call agents",
                            "Payment reminder calls",
                            "Lead qualification & appointment automation"
                        ].map((item, idx) => (
                            <div key={idx} className="flex items-center gap-2.5 text-sm text-[var(--text-secondary)]">
                                <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent-cyan)] shadow-[0_0_6px_var(--accent-cyan)]" />
                                <span>{item}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Footer info */}
                <div className="z-10 text-xs text-[var(--text-tertiary)] flex items-center justify-between">
                    <span>Voise AI</span>
                    <span>v1.2.0-beta</span>
                </div>
            </div>

            {/* RIGHT PANEL — Register Form */}
            <div className="flex-1 flex flex-col justify-center items-center px-4 sm:px-6 lg:px-8 py-12 relative">
                {/* Decorative background gradients for mobile */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[350px] rounded-full bg-[radial-gradient(circle,rgba(0,212,170,0.08)_0%,transparent_70%)] blur-[30px] lg:hidden pointer-events-none" />

                <div className="w-full max-w-[420px] z-10">
                    {/* Header Logo for Mobile */}
                    <div className="flex flex-col items-center mb-8 lg:hidden">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[var(--accent-cyan)] to-[var(--accent-purple)] flex items-center justify-center mb-3">
                            <span className="text-white font-bold text-lg">V</span>
                        </div>
                        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Voise AI</h1>
                        <p className="text-[var(--text-secondary)] text-sm mt-1">Create your free account</p>
                    </div>

                    <div className="hidden lg:block mb-8">
                        <h1 className="text-3xl font-bold text-[var(--text-primary)]">Get started</h1>
                        <p className="text-[var(--text-secondary)] mt-2 text-sm">Launch your first voice automation workflow in minutes.</p>
                    </div>

                    {/* Glass form card */}
                    <div className="glass-card p-8 shadow-xl">
                        <form onSubmit={handleSubmit} className="space-y-4">
                            {error && (
                                <div className="bg-[var(--accent-rose)]/10 border border-[var(--accent-rose)]/20 text-[var(--accent-rose)] text-sm rounded-xl p-3.5 font-medium animate-fade">
                                    {error}
                                </div>
                            )}

                            <div>
                                <label htmlFor="fullName" className="block text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">
                                    Full Name <span className="text-gray-600 font-normal">(optional)</span>
                                </label>
                                <input
                                    id="fullName"
                                    type="text"
                                    value={fullName}
                                    onChange={(e) => setFullName(e.target.value)}
                                    className="w-full px-4 py-2.5 bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent-cyan)] focus:ring-4 focus:ring-[var(--accent-cyan)]/5 transition-all text-sm"
                                    placeholder="John Doe"
                                />
                            </div>

                            <div>
                                <label htmlFor="email" className="block text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">
                                    Email Address
                                </label>
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full px-4 py-2.5 bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent-cyan)] focus:ring-4 focus:ring-[var(--accent-cyan)]/5 transition-all text-sm"
                                    placeholder="name@company.com"
                                    required
                                />
                            </div>

                            <div>
                                <label htmlFor="password" className="block text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">
                                    Password
                                </label>
                                <input
                                    id="password"
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full px-4 py-2.5 bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent-cyan)] focus:ring-4 focus:ring-[var(--accent-cyan)]/5 transition-all text-sm"
                                    placeholder="Min. 8 characters"
                                    required
                                />
                            </div>

                            <div>
                                <label htmlFor="confirmPassword" className="block text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">
                                    Confirm Password
                                </label>
                                <input
                                    id="confirmPassword"
                                    type="password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="w-full px-4 py-2.5 bg-[var(--bg-overlay)] border border-[var(--border-default)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent-cyan)] focus:ring-4 focus:ring-[var(--accent-cyan)]/5 transition-all text-sm"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={isLoading}
                                className="w-full py-3.5 mt-2 bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] hover:shadow-lg hover:shadow-[var(--accent-cyan)]/25 text-white font-semibold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 hover:-translate-y-0.5 active:translate-y-0 active:scale-98"
                            >
                                {isLoading ? (
                                    <span className="flex items-center gap-2">
                                        <svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24" fill="none">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                        </svg>
                                        Creating Account...
                                    </span>
                                ) : (
                                    <>
                                        Get Started Free
                                        <ArrowRight className="w-4 h-4" />
                                    </>
                                )}
                            </button>
                        </form>

                        <div className="mt-6 pt-6 border-t border-[var(--border-subtle)] text-center">
                            <p className="text-[var(--text-secondary)] text-sm">
                                Already have an account?{' '}
                                <Link href="/login" className="text-[var(--accent-cyan)] hover:text-[var(--accent-cyan)]/80 font-medium transition-colors">
                                    Sign in
                                </Link>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
