"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Building2, HeartPulse, TrendingUp } from "lucide-react";

const pilots = [
  {
    icon: TrendingUp,
    industry: "Collections / NBFC",
    color: "primary",
    slots: "2 slots remaining",
    headline: "Recover more EMIs without adding headcount",
    includes: [
      "Full deployment on your contact list",
      "Hindi, Tamil, or Telugu voice agent",
      "CRM integration and call transcripts",
      "30-day outcome report",
    ],
    metric: "Target: 3× recovery rate vs. your current baseline",
  },
  {
    icon: Building2,
    industry: "Real Estate Agency",
    color: "accent",
    slots: "1 slot remaining",
    headline: "Qualify every inbound lead before your team picks up",
    includes: [
      "Lead screening agent in English or Hindi",
      "CRM sync and lead scoring",
      "Site visit calendar booking",
      "30-day qualified lead report",
    ],
    metric: "Target: 5× more qualified conversations per week",
  },
  {
    icon: HeartPulse,
    industry: "Healthcare Clinic",
    color: "primary",
    slots: "1 slot remaining",
    headline: "Cut no-shows with automated appointment reminders",
    includes: [
      "Reminder calls in your patients' language",
      "Reschedule and cancel handling",
      "HMS / Google Calendar integration",
      "30-day attendance report",
    ],
    metric: "Target: 60% reduction in no-shows",
  },
];

export default function Testimonials() {
  return (
    <section id="testimonials" className="py-24 relative border-t border-border dark:border-zinc-900 bg-muted/10 dark:bg-zinc-950/20">
      <div className="container mx-auto px-4 max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-4"
        >
          <span className="text-[10px] font-bold text-primary uppercase tracking-[0.25em] block mb-3">
            EARLY ACCESS
          </span>
          <h2 className="font-display font-black text-3xl sm:text-4xl tracking-tight text-foreground uppercase">
            3 FREE PILOT SLOTS AVAILABLE
          </h2>
          <p className="text-muted-foreground text-sm sm:text-base max-w-xl mx-auto mt-4 leading-relaxed">
            We&apos;re in early access. We&apos;ll deploy Voise AI in your business at no cost.
            You get a working system. We get a real case study. That&apos;s the deal.
          </p>
        </motion.div>

        {/* Honest early-access note */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="flex items-center justify-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-accent/30 bg-accent/5 text-accent text-xs font-semibold">
            <span className="size-2 rounded-full bg-accent animate-pulse" />
            No case studies yet — these pilots will be the first. Honest.
          </div>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          {pilots.map((pilot, i) => {
            const Icon = pilot.icon;
            const isPrimary = pilot.color === "primary";
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.08 }}
                className="group rounded-2xl border border-border dark:border-zinc-900 bg-card dark:bg-zinc-950/80 p-6 flex flex-col hover:border-zinc-300 dark:hover:border-zinc-800 hover:shadow-md dark:hover:shadow-none transition-all duration-300"
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-5">
                  <div className={`size-9 rounded-xl flex items-center justify-center ${isPrimary ? "bg-primary/10 text-primary" : "bg-accent/10 text-amber-600"}`}>
                    <Icon className="size-4" />
                  </div>
                  <span className={`text-[10px] font-black px-2.5 py-1 rounded-full ${isPrimary ? "bg-green-500/10 text-green-600" : "bg-accent/10 text-amber-600"}`}>
                    {pilot.slots}
                  </span>
                </div>

                {/* Industry */}
                <p className={`text-[9px] font-black uppercase tracking-widest mb-2 ${isPrimary ? "text-primary" : "text-amber-600"}`}>
                  {pilot.industry}
                </p>

                {/* Headline */}
                <h3 className="font-bold text-sm text-foreground mb-4 leading-snug">
                  {pilot.headline}
                </h3>

                {/* Includes */}
                <ul className="space-y-2 flex-1 mb-5">
                  {pilot.includes.map((item) => (
                    <li key={item} className="flex items-start gap-2 text-xs text-muted-foreground">
                      <span className={`mt-0.5 shrink-0 font-bold ${isPrimary ? "text-primary" : "text-amber-600"}`}>✓</span>
                      {item}
                    </li>
                  ))}
                </ul>

                {/* Target metric */}
                <div className={`rounded-xl px-3 py-2.5 text-[11px] font-semibold leading-relaxed mb-5 ${isPrimary ? "bg-primary/5 border border-primary/15 text-primary" : "bg-accent/5 border border-accent/20 text-amber-700 dark:text-amber-500"}`}>
                  {pilot.metric}
                </div>

                <Link
                  href={`/pilot?industry=${encodeURIComponent(pilot.industry)}`}
                  className={`inline-flex items-center justify-center gap-2 h-10 rounded-xl font-bold text-xs transition-all active:scale-[0.98] ${isPrimary ? "bg-primary text-primary-foreground hover:brightness-110" : "border border-amber-500/40 text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-950/20"}`}
                >
                  Apply for This Slot
                  <ArrowRight className="size-3.5" />
                </Link>
              </motion.div>
            );
          })}
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center text-[11px] text-muted-foreground"
        >
          Pilots are free. We ask for a 30-minute debrief after 30 days and permission to
          publish anonymized results as a case study.{" "}
          <Link href="/pilot" className="text-primary font-semibold hover:underline">
            Read the full terms →
          </Link>
        </motion.p>
      </div>
    </section>
  );
}
