"use client";

import { motion } from "framer-motion";
import { Phone, CheckSquare, Sparkles, Calendar, Globe, Shield } from "lucide-react";

const features = [
  {
    icon: Phone,
    title: "Real-Time Outbound AI Agents",
    tagline: "AUTONOMOUS VOICE",
    description:
      "Initiate high-volume outbound campaigns with intelligent, fluent conversational bots. Capable of handling complex objectives, overcoming active resistance, and scheduling CRM followups completely on autopilot.",
    span: "lg:col-span-2 lg:row-span-1",
    color: "primary",
  },
  {
    icon: CheckSquare,
    title: "Smart Payment Reminders",
    tagline: "DEBT COLLECTION",
    description:
      "Drastically improve collections and cashflow with empathetic yet persistent AI voice reminders, supporting flexible installment scheduling and instant confirmation.",
    span: "lg:col-span-1",
    color: "accent",
  },
  {
    icon: Sparkles,
    title: "Instant Lead Pre-Screening",
    tagline: "LEAD QUANTIFICATION",
    description:
      "Screen and qualify incoming inbound or newly acquired leads autonomously. Capture buyer intents, evaluate budget thresholds, and book calendar times instantly.",
    span: "lg:col-span-1",
    color: "accent",
  },
  {
    icon: Calendar,
    title: "Automated Appointment Scheduling",
    tagline: "CALENDAR AUTOMATION",
    description:
       "Confirm, rebook, or clear appointments conversationally with zero wait times. Integrated webhooks connect directly to your calendar system.",
    span: "lg:col-span-1",
    color: "primary",
  },
  {
    icon: Globe,
    title: "12 Native Indian Languages",
    tagline: "NATIVE DIVERSITY",
    description:
      "Break geographic barriers with direct models fluent in Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia, Assamese, and English. Supports regional accents across India.",
    span: "lg:col-span-2 lg:row-span-1",
    color: "primary",
  },
  {
    icon: Shield,
    title: "Enterprise Security & Consent",
    tagline: "COMPLIANCE BUILT-IN",
    description:
      "Fully compliant with India's DPDP Act 2023. Featuring end-to-end encrypted logs, PII-aware data storage redactors, and active consent verification modules.",
    span: "lg:col-span-1",
    color: "accent",
  },
];

export default function Features() {
  return (
    <section id="features" className="py-24 relative border-t border-border dark:border-zinc-900 bg-muted/20 dark:bg-zinc-950/40">
      <div className="container mx-auto px-4 max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className="text-[10px] font-bold text-accent uppercase tracking-[0.25em] block mb-3">
            TECHNICAL CAPABILITIES
          </span>
          <h2 className="font-display font-black text-3xl sm:text-4xl tracking-tight text-foreground uppercase">
            WHAT VOISE AI AUTOMATES
          </h2>
          <p className="text-muted-foreground text-sm sm:text-base max-w-xl mx-auto mt-4 leading-relaxed">
            Replace legacy rigid IVR menus with fully-autonomous real-time agents designed for modern businesses.
          </p>
        </motion.div>

        {/* Bento Grid Feature Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-fr">
          {features.map((f, i) => {
            const Icon = f.icon;
            const isPrimary = f.color === "primary";
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.05 }}
                className={`${f.span} group relative overflow-hidden rounded-2xl border border-border dark:border-zinc-900 bg-card dark:bg-zinc-950/60 p-8 hover:border-zinc-300 dark:hover:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900/30 hover:shadow-md dark:hover:shadow-none transition-all duration-300 flex flex-col justify-between`}
              >
                <div>
                  {/* Icon Panel */}
                  <div
                    className={`size-10 rounded-xl flex items-center justify-center mb-6 transition-all duration-300 ${
                      isPrimary
                        ? "bg-primary/10 text-primary border border-primary/20 group-hover:bg-primary/20"
                        : "bg-accent/10 text-accent border border-accent/20 group-hover:bg-accent/20"
                    }`}
                  >
                    <Icon className="size-5" strokeWidth={1.5} />
                  </div>

                  {/* Tagline */}
                  <span className="text-[8px] font-black tracking-widest text-zinc-400 dark:text-zinc-500 uppercase block mb-1.5">
                    {f.tagline}
                  </span>

                  {/* Title */}
                  <h3 className="font-display font-bold text-lg text-foreground mb-3 leading-tight group-hover:text-primary transition-colors">
                    {f.title}
                  </h3>

                  {/* Description */}
                  <p className="text-muted-foreground text-xs leading-relaxed">
                    {f.description}
                  </p>
                </div>

                {/* Subtle bottom indicator line on card */}
                <div
                  className={`h-[2px] w-full absolute bottom-0 left-0 scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-300 ${
                    isPrimary ? "bg-primary" : "bg-accent"
                  }`}
                />
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
