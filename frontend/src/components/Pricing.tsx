"use client";

import { motion } from "framer-motion";
import { Check, ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";

const tiers = [
  {
    name: "Free Pilot",
    priceMonthly: "₹0",
    priceAnnual: "₹0",
    period: "/30 days",
    description: "Prove it on your own borrowers before you pay a rupee.",
    features: [
      "Full collections agent deployment",
      "Hindi, Tamil or Telugu voice",
      "DLT-compliant outbound calling",
      "Promise-to-pay & payment-link capture",
      "30-day recovery outcome report",
    ],
    cta: "Apply for a Pilot",
    href: "/pilot",
    featured: false,
  },
  {
    name: "Pay Per Outcome",
    priceMonthly: "₹50",
    priceAnnual: "₹50",
    period: "/ recovered EMI",
    description: "You only pay when we actually recover money. No minutes, no retainers.",
    features: [
      "₹50 per recovered EMI (or % of amount)",
      "₹20 per promise-to-pay captured",
      "Unlimited calls — minutes are free",
      "Razorpay payment-link collection",
      "RBI-compliant, fully audited calls",
      "Two-way CRM integration",
    ],
    cta: "Start Free Trial",
    href: "/register",
    featured: true,
  },
  {
    name: "Enterprise",
    priceMonthly: "Custom",
    priceAnnual: "Custom",
    period: "",
    description: "For NBFCs and high-volume recovery teams needing dedicated infra.",
    features: [
      "Volume outcome pricing",
      "Dedicated DLT entity onboarding",
      "Custom voice model tuning",
      "Advanced audit logs & compliance",
      "99.9% uptime target",
      "Dedicated solutions engineer",
    ],
    cta: "Contact Sales",
    href: "/contact",
    featured: false,
  },
];

export default function Pricing() {
  return (
    <section id="pricing" className="py-24 relative border-t border-border dark:border-zinc-900 bg-muted/10 dark:bg-zinc-950/40">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(56,189,248,0.015)_0%,_transparent_70%)] pointer-events-none" />
      
      <div className="container mx-auto px-4 max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-10"
        >
          <span className="text-[10px] font-bold text-accent uppercase tracking-[0.25em] block mb-3">
            OUTCOME-BASED PRICING
          </span>
          <h2 className="font-display font-black text-3xl sm:text-4xl tracking-tight text-foreground uppercase">
            PAY FOR RESULTS, NOT MINUTES
          </h2>
          <p className="text-muted-foreground text-sm sm:text-base max-w-xl mx-auto mt-4 leading-relaxed">
            Start with a free pilot. Then pay only when we recover money — per promise-to-pay
            and per recovered EMI. No setup fees, no retainers.
          </p>
        </motion.div>

        <div className="mb-16" />

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {tiers.map((tier, i) => {
            const price = tier.priceMonthly;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.08 }}
                className={`relative rounded-2xl border p-8 flex flex-col justify-between transition-all duration-350 ${
                  tier.featured
                    ? "border-accent/40 bg-card dark:bg-zinc-950/90 shadow-xl shadow-accent/5 dark:shadow-accent/2 ring-1 ring-accent/20"
                    : "border-border dark:border-zinc-900 bg-card/60 dark:bg-zinc-950/60 shadow-sm dark:shadow-none"
                }`}
              >
                {/* Popular Badge */}
                {tier.featured && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-accent text-accent-foreground text-[10px] font-black rounded-full tracking-widest flex items-center gap-1 shadow-lg">
                    <Sparkles className="size-3" />
                    MOST POPULAR
                  </div>
                )}

                <div>
                  <div className="mb-6">
                    <h3 className="font-display font-extrabold text-lg text-foreground mb-1">
                      {tier.name}
                    </h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {tier.description}
                    </p>
                  </div>

                  <div className="flex items-baseline gap-1.5 mb-8">
                    <span className="font-display font-black text-4xl text-foreground">
                      {price}
                    </span>
                    {tier.period && (
                      <span className="text-zinc-400 dark:text-zinc-500 text-xs font-semibold">{tier.period}</span>
                    )}
                  </div>

                  {/* Feature Checklist */}
                  <ul className="space-y-3.5 mb-8">
                    {tier.features.map((f, j) => (
                      <li key={j} className="flex items-start gap-2.5 text-xs">
                        <Check
                          className={`size-4 shrink-0 mt-0.5 ${
                            tier.featured ? "text-accent" : "text-primary"
                          }`}
                          strokeWidth={2.5}
                        />
                        <span className="text-muted-foreground dark:text-zinc-300 font-medium leading-relaxed">{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <Link
                  href={tier.href}
                  className={`inline-flex items-center justify-center gap-2 h-11.5 rounded-xl font-bold text-xs transition-all active:scale-[0.98] ${
                    tier.featured
                      ? "bg-gradient-to-r from-accent to-amber-500 text-accent-foreground hover:brightness-110 shadow-lg shadow-accent/15"
                      : "border border-border dark:border-zinc-800 text-foreground hover:bg-zinc-50 dark:hover:bg-zinc-900/50"
                  }`}
                >
                  {tier.cta}
                  <ArrowRight className="size-3.5" />
                </Link>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
