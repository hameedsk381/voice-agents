"use client";

import { motion } from "framer-motion";
import { Quote, Star } from "lucide-react";

const reviews = [
  {
    initials: "SC",
    name: "Sarah Chen",
    role: "VP of Operations, FinServ Corp",
    quote:
      "Voise AI successfully replaced our legacy manual calling team of 45 people. Payment recovery rates instantly soared 3x. Our customers actually prefer interacting with the voice bot — no hold times, no language barrier, and immediate updates.",
    rating: 5,
  },
  {
    initials: "RK",
    name: "Rahul Krishnan",
    role: "Director of Patient Experience, HealthBridge",
    quote:
      "Automating patient appointment confirmations in Tamil and Kannada was an absolute breeze. No-shows plummeted by 60% within the first month. Setup took our administrative team less than an hour, zero IT tickets needed.",
    rating: 5,
  },
  {
    initials: "AM",
    name: "Amit Mehta",
    role: "Head of Growth, QuickCollect India",
    quote:
      "The debt collection compliance tools built into Voise AI are top-tier. Dynamic negotiation algorithms handle stressed customers with extreme empathy and support, logging promises directly to our databases instantly.",
    rating: 5,
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
          className="text-center mb-16"
        >
          <span className="text-[10px] font-bold text-primary uppercase tracking-[0.25em] block mb-3">
            CUSTOMER TRUST
          </span>
          <h2 className="font-display font-black text-3xl sm:text-4xl tracking-tight text-foreground uppercase">
            OPERATIONAL SUCCESS STORIES
          </h2>
          <p className="text-muted-foreground text-sm sm:text-base max-w-xl mx-auto mt-4 leading-relaxed">
            Real operations teams solving real outbound challenges with next-gen conversational voice automation.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {reviews.map((rev, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              className="group relative rounded-2xl border border-border dark:border-zinc-900 bg-card dark:bg-zinc-950/80 p-6 flex flex-col justify-between hover:border-zinc-300 dark:hover:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900/10 hover:shadow-md dark:hover:shadow-none transition-all duration-350"
            >
              <div>
                {/* Rating & Quote Icon */}
                <div className="flex items-center justify-between mb-6">
                  <div className="flex gap-0.5 text-accent">
                    {Array.from({ length: rev.rating }).map((_, s) => (
                      <Star key={s} className="size-3.5 fill-current" />
                    ))}
                  </div>
                  <Quote className="size-5 text-zinc-300 dark:text-zinc-800 group-hover:text-primary transition-colors" strokeWidth={1.5} />
                </div>

                {/* Quote Text */}
                <blockquote className="text-xs md:text-sm leading-relaxed text-muted-foreground dark:text-zinc-300 mb-6 font-medium">
                  &ldquo;{rev.quote}&rdquo;
                </blockquote>
              </div>

              {/* Profile details */}
              <div className="flex items-center gap-3 pt-4 border-t border-border dark:border-zinc-900">
                <div className="size-10 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xs font-black">
                  {rev.initials}
                </div>
                <div className="truncate">
                  <p className="text-xs font-bold text-foreground leading-none mb-1">
                    {rev.name}
                  </p>
                  <p className="text-[10px] text-muted-foreground truncate">
                    {rev.role}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
