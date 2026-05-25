"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Check, ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";

const tiers = [
  {
    name: "Starter",
    priceMonthly: "₹9,999",
    priceAnnual: "₹7,999",
    period: "/month",
    description: "Ideal for small teams launching their first automated voice pilot.",
    features: [
      "Up to 1,000 automated calls/month",
      "5 concurrent agent profiles",
      "Hindi + English native models",
      "Basic webhook events & logs",
      "Standard email assistance",
    ],
    cta: "Start Free Trial",
    featured: false,
  },
  {
    name: "Growth",
    priceMonthly: "₹29,999",
    priceAnnual: "₹23,999",
    period: "/month",
    description: "Designed for scaling operations needing deep integrations.",
    features: [
      "Up to 10,000 automated calls/month",
      "Unlimited agent profiles",
      "All 12 fluent Indian languages",
      "Advanced analytics & telemetry reports",
      "Two-way CRM integration (Salesforce/HubSpot)",
      "Priority customer manager support",
    ],
    cta: "Start Free Trial",
    featured: true,
  },
  {
    name: "Enterprise",
    priceMonthly: "Custom",
    priceAnnual: "Custom",
    period: "",
    description: "For high-volume operations requiring dedicated instances.",
    features: [
      "Unlimited monthly calls",
      "Priority API rate limits",
      "Custom voice model tuning",
      "Advanced audit logs & compliance",
      "99.9% uptime target",
      "Dedicated solutions engineer",
    ],
    cta: "Contact Sales",
    featured: false,
  },
];

export default function Pricing() {
  const [isAnnual, setIsAnnual] = useState(false);

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
            MEMBERSHIP TIERS
          </span>
          <h2 className="font-display font-black text-3xl sm:text-4xl tracking-tight text-foreground uppercase">
            TRANSPARENT PRICING
          </h2>
          <p className="text-muted-foreground text-sm sm:text-base max-w-xl mx-auto mt-4 leading-relaxed">
            Choose a plan that fits your call volume. No setup fees, cancel anytime.
          </p>
        </motion.div>

        {/* Annual Billing Toggle */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="flex items-center justify-center gap-3 mb-16"
        >
          <span className={`text-xs font-semibold ${!isAnnual ? "text-foreground" : "text-muted-foreground"}`}>
            Monthly Billing
          </span>
          <button
            type="button"
            onClick={() => setIsAnnual(!isAnnual)}
            className="w-12 h-6.5 rounded-full bg-muted border border-border dark:bg-zinc-900 dark:border-zinc-800 p-0.5 relative transition-colors duration-200 cursor-pointer"
          >
            <span
              className={`block size-5 rounded-full bg-primary transition-transform duration-200 ${
                isAnnual ? "translate-x-5.5 bg-accent" : "translate-x-0"
              }`}
            />
          </button>
          <div className="flex items-center gap-1.5">
            <span className={`text-xs font-semibold ${isAnnual ? "text-foreground" : "text-muted-foreground"}`}>
              Annual Billing
            </span>
            <span className="text-[9px] font-extrabold uppercase bg-accent/15 text-accent border border-accent/20 px-2 py-0.5 rounded-full">
              Save 20%
            </span>
          </div>
        </motion.div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {tiers.map((tier, i) => {
            const price = isAnnual ? tier.priceAnnual : tier.priceMonthly;
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
                  href={
                    tier.featured
                      ? "/register"
                      : tier.name === "Enterprise"
                      ? "/contact"
                      : "/register"
                  }
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
