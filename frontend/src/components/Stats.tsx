"use client";

import { motion, useInView } from "framer-motion";
import { useRef, useEffect, useState } from "react";
import { Activity, ShieldCheck, Languages, Zap } from "lucide-react";

const stats = [
  {
    label: "Supported Languages",
    value: 12,
    suffix: "",
    icon: Languages,
    color: "primary",
    desc: "Fluent Indian language models.",
  },
  {
    label: "Real-Time Architecture",
    value: true,
    icon: Zap,
    color: "accent",
    title: "Sub-second voice pipeline",
    desc: "STT → LLM → TTS in a single API call.",
  },
  {
    label: "Built for India",
    value: true,
    icon: Activity,
    color: "primary",
    title: "DPDP Act 2023 Compliant",
    desc: "Indian language-native platform with PII redaction.",
  },
  {
    label: "Cloud-Native",
    value: true,
    icon: ShieldCheck,
    color: "accent",
    title: "Kubernetes-Native Deployment",
    desc: "Auto-scaling infrastructure managed via Helm.",
    isStatic: true,
  },
];

function AnimatedNumber({
  value,
  suffix = "",
  prefix = "",
  decimal = false,
}: {
  value: number;
  suffix?: string;
  prefix?: string;
  decimal?: boolean;
}) {
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
    <span ref={ref} className="font-mono tabular-nums">
      {prefix}
      {decimal ? display.toFixed(2) : Math.floor(display)}
      {suffix}
    </span>
  );
}

export default function Stats() {
  return (
    <section className="py-24 relative border-t border-border dark:border-zinc-900 bg-muted/20 dark:bg-zinc-950/40">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom,_rgba(250,204,21,0.01)_0%,_transparent_75%)] pointer-events-none" />
      <div className="container mx-auto px-4 max-w-5xl">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className="text-[10px] font-bold text-accent uppercase tracking-[0.25em] block mb-3">
            PERFORMANCE AT SCALE
          </span>
          <h2 className="font-display font-black text-3xl sm:text-4xl tracking-tight text-foreground uppercase">
            BY THE NUMBERS
          </h2>
          <p className="text-muted-foreground text-sm sm:text-base max-w-xl mx-auto mt-4 leading-relaxed">
            High-volume operations teams trust Voise AI to automate calls reliably, securely, and cost-effectively.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, i) => {
            const Icon = stat.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.08 }}
                className="group relative rounded-2xl border border-border dark:border-zinc-900 bg-card dark:bg-zinc-950/80 p-6 hover:border-zinc-300 dark:hover:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900/20 hover:shadow-md dark:hover:shadow-none transition-all duration-300"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-2 rounded-lg bg-muted dark:bg-zinc-900 group-hover:bg-zinc-100 dark:group-hover:bg-zinc-850 transition-colors ${
                    stat.color === "primary" ? "text-primary" : "text-accent"
                  }`}>
                    <Icon className="size-4" />
                  </div>
                  <span className="text-[8px] font-bold text-zinc-400 dark:text-zinc-600 uppercase tracking-widest">
                    METRIC_0{i + 1}
                  </span>
                </div>

                <div className={`font-display font-black text-3xl sm:text-4xl tracking-tighter mb-2 leading-none ${
                  stat.color === "primary" ? "text-primary" : "text-accent"
                }`}>
                  {typeof stat.value === 'number' ? (
                    stat.isStatic ? (
                      <span className="font-mono tabular-nums">
                        {stat.value}{stat.suffix}
                      </span>
                    ) : (
                      <AnimatedNumber
                        value={stat.value}
                        suffix={stat.suffix}
                        prefix=""
                        decimal={stat.decimal || false}
                      />
                    )
                  ) : (
                    <span className="font-mono tabular-nums text-2xl font-bold opacity-80">
                      {stat.title || stat.label}
                    </span>
                  )}
                </div>
                <div className="text-xs font-bold text-foreground mb-1">
                  {stat.label}
                </div>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  {stat.desc}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
