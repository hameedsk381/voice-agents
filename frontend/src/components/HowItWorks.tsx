"use client";

import { motion } from "framer-motion";
import { Mic, Settings, PhoneCall, ChevronRight } from "lucide-react";

const steps = [
  {
    icon: Mic,
    title: "1. Configure Voice & Scenarios",
    tagline: "DESIGN INTELLIGENCE",
    description:
      "Choose from ultra-realistic voices. Set language preferences (12 Indian languages supported) and direct the call path conversationally without coding a single script.",
    color: "primary",
  },
  {
    icon: Settings,
    title: "2. Secure Workflow Integration",
    tagline: "PLUG AND PLAY",
    description:
      "Connect your CRM, active dialer lists, or billing API. Voise AI triggers webhooks to update databases, book calendar entries, and send SMS links instantly.",
    color: "accent",
  },
  {
    icon: PhoneCall,
    title: "3. Scaled Launch & Analytics",
    tagline: "AUTONOMOUS SCALE",
    description:
      "Launch campaigns instantly. Scale seamlessly from a handful of verification calls to 100,000 parallel threads without queue latency or agent fatigue.",
    color: "primary",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 relative border-t border-border dark:border-zinc-900 bg-muted/10 dark:bg-zinc-950/20">
      <div className="container mx-auto px-4 max-w-5xl relative">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-20"
        >
          <span className="text-[10px] font-bold text-primary uppercase tracking-[0.25em] block mb-3">
            DEPLOYMENT WORKFLOW
          </span>
          <h2 className="font-display font-black text-3xl sm:text-4xl tracking-tight text-foreground uppercase">
            THREE STEPS. ZERO FRICTION.
          </h2>
          <p className="text-muted-foreground text-sm sm:text-base max-w-xl mx-auto mt-4 leading-relaxed">
            Transition your manual outbound team to high-performing voice automation in less than 5 minutes.
          </p>
        </motion.div>

        {/* Steps Pipeline Layout */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          
          {/* Connector Line in desktop */}
          <div className="hidden md:block absolute top-[28px] left-[15%] right-[15%] h-[1.5px] bg-gradient-to-r from-primary/30 via-accent/30 to-primary/30 z-0" />

          {steps.map((step, i) => {
            const Icon = step.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: i * 0.1 }}
                className="relative z-10 flex flex-col items-center text-center group"
              >
                {/* Step Icon Container */}
                <div
                  className={`size-14 rounded-2xl flex items-center justify-center mb-6 border transition-all duration-300 relative ${
                    step.color === "primary"
                      ? "bg-primary/10 border-primary/20 text-primary group-hover:bg-primary/20"
                      : "bg-accent/10 border-accent/20 text-accent group-hover:bg-accent/20"
                  }`}
                >
                  <Icon className="size-6" strokeWidth={1.5} />
                  
                  {/* Floating index tag */}
                  <span className="absolute -top-1.5 -right-1.5 size-5 bg-card border border-border dark:bg-zinc-900 dark:border-zinc-800 rounded-full flex items-center justify-center text-[9px] font-black text-foreground shadow-sm dark:shadow-none">
                    0{i + 1}
                  </span>
                </div>

                {/* Subtag */}
                <span className="text-[8px] font-black tracking-widest text-zinc-400 dark:text-zinc-500 mb-2 block uppercase">
                  {step.tagline}
                </span>

                {/* Title */}
                <h3 className="font-display font-extrabold text-lg text-foreground mb-3 leading-tight group-hover:text-primary transition-colors">
                  {step.title}
                </h3>

                {/* Description */}
                <p className="text-muted-foreground text-xs leading-relaxed max-w-sm">
                  {step.description}
                </p>

                {/* Arrow helper for desktop steps */}
                {i < steps.length - 1 && (
                  <div className="hidden md:block absolute top-[18px] -right-4 text-zinc-300 dark:text-zinc-700 z-10 animate-pulse">
                    <ChevronRight className="size-5" />
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
