"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

const stack = [
  { name: "Twilio", tag: "TELEPHONY" },
  { name: "Ultravox", tag: "VOICE AI" },
  { name: "OpenAI", tag: "LANGUAGE" },
  { name: "PostgreSQL", tag: "DATA" },
  { name: "Redis", tag: "REAL-TIME" },
  { name: "Kubernetes", tag: "INFRA" },
  { name: "FastAPI", tag: "BACKEND" },
  { name: "Next.js", tag: "FRONTEND" },
];

export default function LogoWall() {
  return (
    <section className="py-16 relative border-t border-border dark:border-zinc-900 bg-muted/20 dark:bg-zinc-950/20">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="flex items-center justify-center gap-2 mb-8">
          <Sparkles className="size-3 text-accent animate-pulse" />
          <p className="text-[10px] font-bold text-muted-foreground tracking-[0.2em] uppercase text-center">
            BUILT ON PROVEN ENTERPRISE INFRASTRUCTURE
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
          {stack.map((item, i) => (
            <motion.div
              key={item.name}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.05 }}
              className="group relative flex flex-col items-center justify-center py-4 px-6 rounded-xl border border-border dark:border-zinc-900 bg-card/60 dark:bg-zinc-950/40 hover:border-zinc-300 dark:hover:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900/40 hover:shadow-sm dark:hover:shadow-none transition-all duration-350 cursor-default select-none"
            >
              <span className="font-display text-sm font-extrabold text-muted-foreground group-hover:text-foreground transition-colors tracking-tight">
                {item.name}
              </span>
              <span className="text-[7px] font-extrabold tracking-widest text-zinc-400 dark:text-zinc-600 group-hover:text-primary transition-colors mt-0.5">
                {item.tag}
              </span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
