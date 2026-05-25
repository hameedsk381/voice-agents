"use client";

import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";

export default function CTA() {
  const router = useRouter();

  return (
    <section className="py-24 relative overflow-hidden border-t border-border dark:border-zinc-900 bg-muted/20 dark:bg-zinc-950/40">
      {/* Background visual components */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-primary/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute top-1/2 left-1/3 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[200px] bg-accent/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="container mx-auto px-4 text-center relative z-10 max-w-3xl">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-accent/25 bg-accent/5 text-accent text-[10px] font-bold tracking-widest uppercase mb-6"
        >
          <Sparkles className="size-3 animate-pulse" />
          <span>IMMEDIATE PILOT SETUP</span>
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="font-display font-black text-4xl sm:text-5xl leading-tight text-foreground mb-6 uppercase"
        >
          READY TO AUTOMATE YOUR <br />
          <span className="text-primary">
            OUTBOUND CALLS?
          </span>
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="text-muted-foreground text-sm sm:text-base mb-10 max-w-xl mx-auto leading-relaxed font-medium"
        >
          Deploy your first autonomous conversational voice agent in less than 5 minutes.
          Enjoy a risk-free trial including 50 call minutes — no credit card required.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <button
            onClick={() => router.push('/register')}
            className="inline-flex items-center justify-center gap-2 h-12 px-8 rounded-xl bg-gradient-to-r from-primary to-cyan-500 text-primary-foreground font-extrabold text-sm hover:brightness-110 active:scale-[0.98] transition-all shadow-lg shadow-primary/20 cursor-pointer"
          >
            Start Free Trial
            <ArrowRight className="size-4" />
          </button>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="mt-6 text-[10px] text-zinc-400 dark:text-zinc-500 font-bold uppercase tracking-widest"
        >
          Instant deployment — No credit card required — Cancel anytime
        </motion.p>
      </div>
    </section>
  );
}
