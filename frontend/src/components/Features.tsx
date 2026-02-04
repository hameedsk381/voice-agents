"use client";

import { motion } from "framer-motion";
import { Phone, Users, Activity, Lock, Cpu, Globe } from "lucide-react";

const features = [
    {
        icon: Phone,
        title: "Inbound & Outbound",
        description: "Handle customer support calls and proactive outreach campaigns with natural-sounding AI agents.",
    },
    {
        icon: Users,
        title: "Agent Swarms",
        description: "Orchestrate multiple specialized agents to handle complex workflows and hand-offs seamlessly.",
    },
    {
        icon: Activity,
        title: "Real-time Observability",
        description: "Monitor call latency, costs, and success rates in real-time with built-in Grafana dashboards.",
    },
    {
        icon: Lock,
        title: "Enterprise Security",
        description: "Role-based access control, PII redaction, and on-premise deployment options for full data sovereignty.",
    },
    {
        icon: Globe,
        title: "Multilingual Support",
        description: "Native support for English, Hindi, and regional dialects with accent-tolerant speech recognition.",
    },
    {
        icon: Cpu,
        title: "Pluggable Architecture",
        description: "Swap STT/TTS providers or LLMs easily. No vendor lock-in. Built on Temporal and Python.",
    },
];

export default function Features() {
    return (
        <section id="features" className="py-24 bg-black relative">
            <div className="container mx-auto px-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="text-center mb-16"
                >
                    <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">
                        Everything you need for <br />
                        <span className="text-blue-500">Production Voice AI</span>
                    </h2>
                    <p className="text-gray-400 max-w-2xl mx-auto">
                        Stop stitching together disparate APIs. OpenVoice provides a cohesive, open-source operating system for your voice agents.
                    </p>
                </motion.div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {features.map((feature, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5, delay: index * 0.1 }}
                            className="p-8 rounded-2xl bg-white/5 border border-white/10 hover:border-blue-500/50 hover:bg-white/[0.07] transition-all group"
                        >
                            <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center mb-6 group-hover:bg-blue-500/20 transition-colors">
                                <feature.icon className="w-6 h-6 text-blue-400 group-hover:text-blue-300" />
                            </div>
                            <h3 className="text-xl font-semibold text-white mb-3">{feature.title}</h3>
                            <p className="text-gray-400 leading-relaxed text-sm">
                                {feature.description}
                            </p>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
}
