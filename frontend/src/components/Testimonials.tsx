"use client";

import { motion } from "framer-motion";
import { Quote } from "lucide-react";

const testimonials = [
    {
        quote: "Voise AI replaced our manual calling team. Payment recovery rates went up 3x and our customers actually prefer the AI.",
        name: "Sarah Chen",
        role: "VP of Operations",
        company: "FinServ Corp",
    },
    {
        quote: "We automated 10,000 appointment confirmations per week. No-shows dropped 60% and our front desk team finally has breathing room.",
        name: "Marcus Rivera",
        role: "Director of Operations",
        company: "HealthBridge AI",
    },
    {
        quote: "Lead qualification went from 3 days to 15 minutes. Our sales team only talks to hot leads now. Voise AI is a game changer.",
        name: "Priya Sharma",
        role: "Head of Sales Ops",
        company: "ScaleVox",
    },
];

export default function Testimonials() {
    return (
        <section id="testimonials" className="py-24 relative">
            <div className="container mx-auto px-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="text-center mb-14"
                >
                    <h2 className="text-3xl md:text-4xl font-bold text-[var(--text-primary)] mb-4">
                        Trusted by <span className="text-gradient-brand">Operations Teams</span>
                    </h2>
                    <p className="text-[var(--text-secondary)] max-w-xl mx-auto">
                        Operations teams trust Voise AI to automate their workflows.
                    </p>
                </motion.div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {testimonials.map((t, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5, delay: i * 0.1 }}
                            className="relative p-7 rounded-2xl bg-[var(--bg-overlay)] border border-[var(--border-subtle)] hover:border-[var(--border-active)] hover:bg-[var(--glass-bg-hover)] transition-all duration-300 backdrop-blur-sm group"
                        >
                            <Quote className="w-8 h-8 text-[var(--accent-cyan)]/30 mb-4 group-hover:text-[var(--accent-cyan)]/50 transition-colors" />
                            <p className="text-[var(--text-primary)] leading-relaxed mb-6 text-[15px]">
                                &ldquo;{t.quote}&rdquo;
                            </p>
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[var(--accent-cyan)] to-[var(--accent-purple)] flex items-center justify-center text-white font-bold text-sm">
                                    {t.name[0]}
                                </div>
                                <div>
                                    <p className="text-sm font-semibold text-[var(--text-primary)]">{t.name}</p>
                                    <p className="text-xs text-[var(--text-tertiary)]">{t.role}, {t.company}</p>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
}
