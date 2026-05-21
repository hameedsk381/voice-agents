"use client";

import { motion } from "framer-motion";
import { ArrowRight, Play, CheckCircle } from "lucide-react";
import Link from "next/link";

const waveBarCount = 32;

export default function Hero() {
    return (
        <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden pt-24 pb-16">
            {/* Ambient Gradient Orbs */}
            <div className="absolute top-[-200px] right-[-100px] w-[700px] h-[700px] rounded-full bg-[radial-gradient(circle,rgba(0,212,170,0.15)_0%,transparent_70%)] blur-[20px] animate-[float-slow_20s_ease-in-out_infinite] pointer-events-none" />
            <div className="absolute bottom-[-300px] left-[-200px] w-[900px] h-[900px] rounded-full bg-[radial-gradient(circle,rgba(139,92,246,0.12)_0%,transparent_70%)] blur-[20px] animate-[float-slow_25s_ease-in-out_infinite_reverse] pointer-events-none" />
            <div className="absolute top-[30%] left-[50%] w-[400px] h-[400px] rounded-full bg-[radial-gradient(circle,rgba(59,130,246,0.08)_0%,transparent_70%)] blur-[20px] animate-[float-slow_18s_ease-in-out_infinite] pointer-events-none" />

            {/* Dot Grid */}
            <div className="absolute inset-0 dot-grid opacity-[0.04] pointer-events-none" />

            {/* Gradient fade at bottom */}
            <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-[var(--bg-base)] to-transparent pointer-events-none z-10" />

            <div className="container mx-auto px-4 relative z-20 text-center">
                {/* Badge */}
                <motion.div
                    initial={{ opacity: 0, y: 15, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.5, delay: 0.1, type: "spring", stiffness: 200 }}
                    className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-[var(--glass-bg)] border border-[var(--border-default)] text-sm text-[var(--accent-cyan)] mb-8 backdrop-blur-sm"
                >
                    <span className="flex h-2 w-2 rounded-full bg-[var(--accent-cyan)] animate-[pulse-glow_2s_ease-in-out_infinite] shadow-[0_0_8px_var(--accent-cyan)]" />
                    <span className="font-medium">AI-Powered Voice Automation</span>
                </motion.div>

                {/* Headline */}
                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.7, delay: 0.2, type: "spring", stiffness: 100 }}
                    className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold tracking-tight leading-[1.05] mb-7"
                >
                    <span className="text-[var(--text-primary)]">AI Voice Automation</span>
                    <br />
                    <span className="text-gradient-shimmer">For Operations</span>
                </motion.h1>

                {/* Subtitle */}
                <motion.p
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.35 }}
                    className="text-lg md:text-xl text-[var(--text-secondary)] max-w-2xl mx-auto mb-10 leading-relaxed"
                >
                    Deploy AI outbound call agents for payment reminders, lead qualification, and appointment confirmation — fully automated.
                </motion.p>

                {/* CTAs */}
                <motion.div
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.45 }}
                    className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
                >
                    <Link href="/register">
                        <button className="group px-8 py-4 bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white font-semibold rounded-full flex items-center gap-2 transition-all duration-300 hover:shadow-[0_4px_25px_rgba(0,212,170,0.3),0_0_50px_rgba(139,92,246,0.15)] hover:-translate-y-0.5 active:scale-95">
                            Start Free Trial
                            <ArrowRight className="w-5 h-5 group-hover:translate-x-0.5 transition-transform" />
                        </button>
                    </Link>

                    <a href="#features">
                        <button className="px-8 py-4 bg-[var(--glass-bg)] hover:bg-[var(--glass-bg-hover)] text-[var(--text-primary)] font-semibold rounded-full flex items-center gap-2 border border-[var(--border-default)] hover:border-white/[0.15] transition-all duration-300 backdrop-blur-sm active:scale-95">
                            <Play className="w-4 h-4 fill-current" />
                            Watch Demo
                        </button>
                    </a>
                </motion.div>

                {/* Waveform Visualizer */}
                <motion.div
                    initial={{ opacity: 0, y: 30, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.8, delay: 0.6, type: "spring", stiffness: 80 }}
                    className="relative max-w-xl mx-auto mb-16"
                >
                    <div className="glass-card p-6 md:p-8">
                        <div className="flex items-center gap-3 mb-5">
                            <div className="w-3 h-3 rounded-full bg-[var(--accent-cyan)] shadow-[0_0_10px_var(--accent-cyan)] animate-[pulse-glow_2s_ease-in-out_infinite]" />
                            <span className="text-xs font-semibold text-[var(--accent-cyan)] uppercase tracking-widest">Live Agent • Processing</span>
                        </div>
                        <div className="flex items-end justify-center gap-[3px] h-20">
                            {Array.from({ length: waveBarCount }).map((_, i) => (
                                <div
                                    key={i}
                                    className="w-[3px] rounded-full bg-gradient-to-t from-[var(--accent-cyan)] to-[var(--accent-purple)]"
                                    style={{
                                        height: '20%',
                                        animation: `waveform-bar ${0.6 + Math.random() * 0.8}s ease-in-out ${i * 0.04}s infinite alternate`,
                                        opacity: 0.5 + Math.random() * 0.5,
                                    }}
                                />
                            ))}
                        </div>
                        <div className="flex items-center justify-between mt-5 text-xs text-[var(--text-tertiary)]">
                            <span>Platform online</span>
                            <span>Voice agents ready</span>
                            <span className="px-2 py-0.5 rounded-full bg-[var(--accent-emerald)]/10 text-[var(--accent-emerald)] font-bold text-[10px] uppercase">Active</span>
                        </div>
                    </div>
                    {/* Glow underneath */}
                    <div className="absolute -inset-1 bg-gradient-to-r from-[var(--accent-cyan)]/10 to-[var(--accent-purple)]/10 rounded-2xl blur-xl -z-10" />
                </motion.div>

                {/* Feature Pills */}
                <motion.div
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.8 }}
                    className="flex flex-wrap justify-center gap-6 text-sm text-[var(--text-secondary)]"
                >
                    {["Outbound Call Agents", "Payment Reminders", "Lead Qualification", "Appointment Automation"].map((feat, i) => (
                        <div key={i} className="flex items-center gap-2">
                            <CheckCircle className="w-4 h-4 text-[var(--accent-cyan)]" />
                            <span>{feat}</span>
                        </div>
                    ))}
                </motion.div>
            </div>
        </section>
    );
}
