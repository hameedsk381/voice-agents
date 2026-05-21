"use client";

import { motion } from "framer-motion";
import { Phone, Users, Activity, Lock, Cpu, Globe } from "lucide-react";

const features = [
    {
        icon: Phone,
        title: "AI Outbound Call Agents",
        description: "Deploy intelligent voice agents that make outbound calls at scale — natural conversations for payment collection, reminders, and follow-ups.",
        accent: "from-cyan-400 to-teal-500",
        glow: "rgba(0,212,170,0.15)",
    },
    {
        icon: Users,
        title: "Payment Reminder Calls",
        description: "Automate payment collection with polite, persistent AI voice calls. Reduce delinquencies without hiring more agents.",
        accent: "from-violet-400 to-purple-500",
        glow: "rgba(139,92,246,0.15)",
    },
    {
        icon: Activity,
        title: "Lead Qualification Calls",
        description: "AI agents that screen, qualify, and route leads autonomously — capturing intent and booking meetings without human intervention.",
        accent: "from-blue-400 to-indigo-500",
        glow: "rgba(59,130,246,0.15)",
    },
    {
        icon: Lock,
        title: "Appointment Automation",
        description: "Confirm, reschedule, and cancel appointments with natural voice conversations. Reduce no-shows and free up your front desk.",
        accent: "from-emerald-400 to-green-500",
        glow: "rgba(16,185,129,0.15)",
    },
    {
        icon: Globe,
        title: "Fits Your Workflow",
        description: "Connect your CRM, calendar, and payment systems. Voise AI slots into how your team already works—no IT project required.",
        accent: "from-amber-400 to-orange-500",
        glow: "rgba(245,158,11,0.15)",
    },
    {
        icon: Cpu,
        title: "Enterprise-Grade Reliability",
        description: "Compliance-ready, monitored, and auditable. Built for regulated industries that need trust, transparency, and control.",
        accent: "from-rose-400 to-pink-500",
        glow: "rgba(244,63,94,0.15)",
    },
];

export default function Features() {
    return (
        <section id="features" className="py-28 relative">
            <div className="container mx-auto px-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, margin: "-100px" }}
                    transition={{ duration: 0.6 }}
                    className="text-center mb-16"
                >
                    <h2 className="text-3xl md:text-5xl font-bold mb-6 text-[var(--text-primary)]">
                        Voice Automation for{" "}
                        <br className="hidden md:block" />
                        <span className="text-gradient-brand">Operational Workflows</span>
                    </h2>
                    <p className="text-[var(--text-secondary)] max-w-2xl mx-auto text-lg">
                        Deploy AI voice agents that handle outbound calls, payment reminders, lead qualification, and appointment scheduling — all from one platform.
                    </p>
                </motion.div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {features.map((feature, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-50px" }}
                            transition={{ duration: 0.5, delay: index * 0.08 }}
                            className="group relative p-7 rounded-2xl bg-[var(--bg-overlay)] border border-[var(--border-subtle)] hover:border-[var(--border-active)] hover:bg-[var(--glass-bg-hover)] transition-all duration-300 backdrop-blur-sm"
                            style={{
                                boxShadow: 'none',
                            }}
                            onMouseEnter={(e) => {
                                (e.currentTarget as HTMLElement).style.boxShadow = `0 0 40px ${feature.glow}`;
                            }}
                            onMouseLeave={(e) => {
                                (e.currentTarget as HTMLElement).style.boxShadow = 'none';
                            }}
                        >
                            <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${feature.accent} flex items-center justify-center mb-5 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                                <feature.icon className="w-5 h-5 text-white" />
                            </div>
                            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2.5">{feature.title}</h3>
                            <p className="text-[var(--text-secondary)] leading-relaxed text-sm">
                                {feature.description}
                            </p>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
}
