"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Check } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export interface VerticalStat {
  value: string;
  label: string;
}

export interface VerticalUseCase {
  title: string;
  description: string;
  outcome: string;
}

export interface VerticalStep {
  step: string;
  title: string;
  description: string;
}

export interface VerticalPageProps {
  industry: string;
  badge: string;
  headline: string;
  subheadline: string;
  stats: VerticalStat[];
  useCases: VerticalUseCase[];
  howItWorks: VerticalStep[];
  demoLabel: string;
  ctaHeadline: string;
  ctaDescription: string;
}

export default function VerticalPage({
  industry,
  badge,
  headline,
  subheadline,
  stats,
  useCases,
  howItWorks,
  demoLabel,
  ctaHeadline,
  ctaDescription,
}: VerticalPageProps) {
  return (
    <main className="min-h-screen bg-background text-foreground relative overflow-x-clip">
      <Navbar />

      {/* Hero */}
      <section className="relative min-h-[75vh] bg-background pt-32 pb-20 flex items-center overflow-hidden">
        <div className="absolute top-[15%] left-[-8%] w-[300px] h-[300px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute bottom-[10%] right-[-8%] w-[350px] h-[350px] bg-accent/5 rounded-full blur-[130px] pointer-events-none" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(0,0,0,0.015)_1px,_transparent_1px),_linear-gradient(90deg,_rgba(0,0,0,0.015)_1px,_transparent_1px)] dark:bg-[linear-gradient(rgba(255,255,255,0.015)_1px,_transparent_1px),_linear-gradient(90deg,_rgba(255,255,255,0.015)_1px,_transparent_1px)] bg-[size:32px_32px] pointer-events-none" />

        <div className="container mx-auto px-4 max-w-5xl relative z-10">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-semibold tracking-wider mb-6 w-fit"
          >
            {badge}
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            className="font-display font-black text-4xl sm:text-5xl xl:text-6xl leading-[1.05] tracking-tight mb-6 uppercase max-w-3xl"
            dangerouslySetInnerHTML={{ __html: headline }}
          />

          <motion.p
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-muted-foreground text-base sm:text-lg leading-relaxed mb-10 max-w-xl"
          >
            {subheadline}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="flex flex-col sm:flex-row gap-4 mb-12"
          >
            <Link
              href="/register"
              className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-primary to-cyan-500 text-primary-foreground font-bold text-sm h-12 px-6 rounded-xl hover:brightness-110 active:scale-[0.98] transition-all duration-200 shadow-lg shadow-primary/20"
            >
              {demoLabel}
              <ArrowRight className="size-4" />
            </Link>
            <Link
              href="/#pricing"
              className="inline-flex items-center justify-center gap-2 border border-border text-foreground font-semibold text-sm h-12 px-6 rounded-xl hover:bg-muted/50 transition-colors"
            >
              See Pricing
            </Link>
          </motion.div>

          {/* Stats row */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex items-center gap-8 border-t border-border pt-8 flex-wrap"
          >
            {stats.map((s, i) => (
              <div key={i} className="flex items-center gap-6">
                {i > 0 && <div className="w-px h-8 bg-border hidden sm:block" />}
                <div>
                  <span className="block text-2xl font-black text-foreground">{s.value}</span>
                  <span className="text-xs text-muted-foreground font-medium">{s.label}</span>
                </div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-20 border-t border-border bg-muted/20">
        <div className="container mx-auto px-4 max-w-5xl">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-14"
          >
            <span className="text-[10px] font-bold text-accent uppercase tracking-[0.25em] block mb-3">
              {industry.toUpperCase()} USE CASES
            </span>
            <h2 className="font-display font-black text-3xl sm:text-4xl tracking-tight text-foreground uppercase">
              WHAT VOISE AI HANDLES
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {useCases.map((uc, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.07 }}
                className="rounded-2xl border border-border bg-card p-6 flex flex-col gap-3 hover:shadow-md hover:border-zinc-300 dark:hover:border-zinc-800 transition-all duration-300"
              >
                <h3 className="font-bold text-sm text-foreground">{uc.title}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed flex-1">{uc.description}</p>
                <div className="flex items-start gap-2 bg-primary/5 border border-primary/15 rounded-xl px-3 py-2 mt-1">
                  <Check className="size-3.5 text-primary shrink-0 mt-0.5" />
                  <span className="text-[11px] font-semibold text-primary leading-relaxed">{uc.outcome}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 border-t border-border">
        <div className="container mx-auto px-4 max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-14"
          >
            <span className="text-[10px] font-bold text-primary uppercase tracking-[0.25em] block mb-3">
              DEPLOYMENT
            </span>
            <h2 className="font-display font-black text-3xl sm:text-4xl tracking-tight text-foreground uppercase">
              UP IN MINUTES, NOT MONTHS
            </h2>
          </motion.div>

          <div className="relative">
            <div className="hidden md:block absolute top-7 left-8 right-8 h-px bg-border" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {howItWorks.map((step, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: i * 0.1 }}
                  className="flex flex-col items-center md:items-start text-center md:text-left"
                >
                  <div className="size-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-4 relative z-10">
                    <span className="font-display font-black text-lg text-primary">{step.step}</span>
                  </div>
                  <h3 className="font-bold text-sm text-foreground mb-2">{step.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{step.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 border-t border-border bg-muted/20">
        <div className="container mx-auto px-4 max-w-3xl text-center">
          <motion.h2
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
            className="font-display font-black text-3xl sm:text-4xl text-foreground uppercase mb-4"
            dangerouslySetInnerHTML={{ __html: ctaHeadline }}
          />
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-muted-foreground text-sm sm:text-base mb-8 max-w-lg mx-auto leading-relaxed"
          >
            {ctaDescription}
          </motion.p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/register"
              className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-primary to-cyan-500 text-primary-foreground font-bold text-sm h-12 px-8 rounded-xl hover:brightness-110 active:scale-[0.98] transition-all shadow-lg shadow-primary/20"
            >
              See a Live Demo
              <ArrowRight className="size-4" />
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center justify-center gap-2 border border-border text-foreground font-bold text-sm h-12 px-8 rounded-xl hover:bg-muted/50 transition-colors"
            >
              Start Free Trial
            </Link>
          </div>
          <p className="mt-5 text-[10px] text-muted-foreground font-bold uppercase tracking-widest">
            No credit card required — 50 free call minutes
          </p>
        </div>
      </section>

      <Footer />
    </main>
  );
}
