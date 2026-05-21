"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import Link from "next/link";

export default function CTA() {
    return (
        <section className="py-32 relative overflow-hidden">
            {/* Background effects */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] bg-gradient-to-br from-[var(--accent-cyan)]/15 to-[var(--accent-purple)]/10 rounded-full blur-[120px] -z-10 pointer-events-none" />

            <div className="container mx-auto px-4 text-center relative z-10">
                <motion.h2
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="text-4xl md:text-6xl font-bold text-[var(--text-primary)] mb-6 leading-tight"
                >
                    Ready to Automate Your <br />
                    <span className="text-gradient-brand">Operational Workflows?</span>
                </motion.h2>

                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, delay: 0.15 }}
                    className="text-[var(--text-secondary)] text-lg max-w-2xl mx-auto mb-10 leading-relaxed"
                >
                    Deploy AI outbound call agents for payment reminders, lead qualification, and appointment confirmation in minutes.
                </motion.p>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, delay: 0.3 }}
                >
                    <Link href="/register" className="inline-block">
                        <button className="px-10 py-5 bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white font-bold rounded-full hover:shadow-[0_4px_25px_rgba(0,212,170,0.3)] transition-all duration-300 hover:-translate-y-0.5 active:scale-95 flex items-center gap-2">
                            Get Started Now
                            <ArrowRight className="w-5 h-5" />
                        </button>
                    </Link>
                </motion.div>
                
                <motion.p 
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, delay: 0.45 }}
                    className="mt-6 text-xs text-[var(--text-tertiary)] uppercase tracking-wider font-semibold"
                >
                    AI-powered voice automation for operational workflows
                </motion.p>
            </div>
        </section>
    );
}
