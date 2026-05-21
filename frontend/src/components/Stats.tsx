"use client";

import { motion, useInView } from "framer-motion";
import { useRef, useEffect, useState } from "react";

const stats = [
    { label: "Calls Processed", value: 10, suffix: "M+", accent: "var(--accent-cyan)" },
    { label: "Uptime SLA", value: 99.97, suffix: "%", decimal: true, accent: "var(--accent-emerald)" },
    { label: "Avg Latency", value: 380, prefix: "<", suffix: "ms", accent: "var(--accent-purple)" },
    { label: "Enterprise Clients", value: 50, suffix: "+", accent: "var(--accent-blue)" },
];

function AnimatedNumber({ value, suffix = "", prefix = "", decimal = false }: { value: number; suffix?: string; prefix?: string; decimal?: boolean }) {
    const [display, setDisplay] = useState(0);
    const ref = useRef<HTMLSpanElement>(null);
    const isInView = useInView(ref, { once: true, margin: "-100px" });

    useEffect(() => {
        if (!isInView) return;
        const duration = 2000;
        const steps = 60;
        const increment = value / steps;
        let current = 0;
        const timer = setInterval(() => {
            current += increment;
            if (current >= value) {
                current = value;
                clearInterval(timer);
            }
            setDisplay(current);
        }, duration / steps);
        return () => clearInterval(timer);
    }, [isInView, value]);

    return (
        <span ref={ref}>
            {prefix}{decimal ? display.toFixed(2) : Math.floor(display)}{suffix}
        </span>
    );
}

export default function Stats() {
    return (
        <section id="stats" className="py-24 relative">
            <div className="container mx-auto px-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="text-center mb-14"
                >
                    <h2 className="text-3xl md:text-4xl font-bold text-[var(--text-primary)] mb-4">
                        Powering Voice AI at <span className="text-gradient-brand">Scale</span>
                    </h2>
                    <p className="text-[var(--text-secondary)] max-w-xl mx-auto">
                        Trusted by operations teams running high-volume outbound voice programs.
                    </p>
                </motion.div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
                    {stats.map((stat, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5, delay: i * 0.1 }}
                            className="relative group p-7 rounded-2xl bg-[var(--bg-overlay)] border border-[var(--border-subtle)] hover:border-[var(--border-active)] hover:bg-[var(--glass-bg-hover)] transition-all duration-300 text-center backdrop-blur-sm"
                        >
                            <div
                                className="text-4xl md:text-5xl font-bold mb-2"
                                style={{ color: stat.accent }}
                            >
                                <AnimatedNumber
                                    value={stat.value}
                                    suffix={stat.suffix}
                                    prefix={stat.prefix || ""}
                                    decimal={stat.decimal || false}
                                />
                            </div>
                            <div className="text-sm text-[var(--text-secondary)] font-medium">
                                {stat.label}
                            </div>
                            {/* Bottom accent line */}
                            <div
                                className="absolute bottom-0 left-4 right-4 h-[2px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                                style={{ background: `linear-gradient(90deg, transparent, ${stat.accent}, transparent)` }}
                            />
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
}
