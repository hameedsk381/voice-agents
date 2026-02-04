"use client";

import { motion } from "framer-motion";
import { ArrowRight, Play, CheckCircle } from "lucide-react";
import Link from "next/link";

export default function Hero() {
    return (
        <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden pt-20">
            {/* Background Effects */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-blue-600/20 rounded-full blur-[120px] -z-10" />
            <div className="absolute bottom-0 right-0 w-[800px] h-[600px] bg-purple-600/10 rounded-full blur-[120px] -z-10" />

            <div className="container mx-auto px-4 relative z-10 text-center">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-sm text-blue-300 mb-8"
                >
                    <span className="flex h-2 w-2 rounded-full bg-blue-400 animate-pulse"></span>
                    <span>Open Source Enterprise Voice AI</span>
                </motion.div>

                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.3 }}
                    className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-6 leading-tight"
                >
                    Build Voice Agents <br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
                        Without Limits
                    </span>
                </motion.h1>

                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.4 }}
                    className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10"
                >
                    The open-source orchestration engine for enterprise-grade voice AI.
                    Deploy inbound/outbound agents, handle interruptions, and scale effortlessly.
                </motion.p>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.5 }}
                    className="flex flex-col sm:flex-row items-center justify-center gap-4"
                >
                    <Link href="/register">
                        <button className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-full flex items-center gap-2 transition-all hover:scale-105 active:scale-95 shadow-lg shadow-blue-500/25">
                            Start Building Free
                            <ArrowRight className="w-5 h-5" />
                        </button>
                    </Link>

                    <button className="px-8 py-4 bg-white/5 hover:bg-white/10 text-white font-semibold rounded-full flex items-center gap-2 border border-white/10 transition-all hover:scale-105 active:scale-95 backdrop-blur-sm">
                        <Play className="w-5 h-5 fill-current" />
                        Watch Demo
                    </button>
                </motion.div>

                {/* Features List */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 1, delay: 0.7 }}
                    className="mt-16 flex flex-wrap justify-center gap-8 text-gray-400 text-sm"
                >
                    {["Self-Hosted", "Low Latency (<500ms)", "Multilingual", "100% Customizable"].map((feat, i) => (
                        <div key={i} className="flex items-center gap-2">
                            <CheckCircle className="w-4 h-4 text-blue-500" />
                            <span>{feat}</span>
                        </div>
                    ))}
                </motion.div>
            </div>

            {/* Decorative Grid */}
            <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-20 -z-20 pointer-events-none" />
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/50 to-black -z-10 pointer-events-none" />

        </section>
    );
}
