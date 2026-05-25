"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import { ChevronDown, HelpCircle } from "lucide-react";

const faqs = [
  {
    q: "Which Indian languages does Voise AI support?",
    a: "We natively support Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia, Assamese, and English. Each agent is configured for one primary language, and we are actively building cross-language code-switching.",
  },
  {
    q: "How does Voise AI compare to traditional IVR or auto-dialers?",
    a: "Traditional IVRs follow hard-coded branches and dial numbers blindly. Voise AI agents carry natural, dynamic conversations. They track conversational intents, interpret multi-layered context, process human barge-ins gracefully, and adapt tones dynamically. The goal is human-like interaction, and we publish our parity benchmarks openly.",
  },
  {
    q: "Are engineering resources needed to initiate a campaign?",
    a: "No. Voise AI was intentionally designed for operations teams. You configure your agent persona via simple dialogue guidelines, upload your contact spreadsheets, verify database webhooks, and press launch. No coding or complex IT tickets necessary.",
  },
  {
    q: "How does the agent handle escalation to human managers?",
    a: "You define explicit exit actions. When the customer insists on speaking to a manager, triggers a specific keyword, or if the agent encounters persistent low confidence values, the call is transferred seamlessly. The full episodic context and log are instantly piped to the human agent.",
  },
  {
    q: "How do you maintain data privacy and compliance?",
    a: "We comply strictly with India's DPDP Act 2023. Call recordings and transcript logs are encrypted both at rest and in transit. Standard pipelines redacting PII are enabled by default, and we never use customer interaction data to train general models.",
  },
  {
    q: "Can I test the platform before committing to a paid plan?",
    a: "Yes. Our standard trial grants 50 free outbound call minutes. No credit cards or contracts required. You can have a live agent making automated calls in under 5 minutes.",
  },
];

export default function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section id="faq" className="py-24 relative border-t border-border dark:border-zinc-900 bg-muted/10 dark:bg-zinc-950/20">
      <div className="container mx-auto px-4 max-w-3xl">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className="text-[10px] font-bold text-primary uppercase tracking-[0.25em] block mb-3">
            HAVE QUESTIONS?
          </span>
          <h2 className="font-display font-black text-3xl sm:text-4xl tracking-tight text-foreground uppercase">
            FREQUENTLY ASKED QUESTIONS
          </h2>
          <p className="text-muted-foreground text-sm sm:text-base max-w-xl mx-auto mt-4 leading-relaxed">
            Honest, transparent answers about the technology, operations, privacy, and integrations.
          </p>
        </motion.div>

        <div className="space-y-4">
          {faqs.map((faq, i) => {
            const isOpen = openIndex === i;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.03 }}
                className={`rounded-2xl border transition-all duration-300 overflow-hidden ${
                  isOpen
                    ? "border-primary/30 bg-card dark:bg-zinc-950 shadow-lg shadow-primary/5"
                    : "border-border dark:border-zinc-900 bg-card/60 dark:bg-zinc-950/50 hover:border-zinc-300 dark:hover:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900/10 hover:shadow-sm dark:hover:shadow-none"
                }`}
              >
                <button
                  type="button"
                  onClick={() => setOpenIndex(isOpen ? null : i)}
                  className="w-full flex items-center justify-between gap-4 px-6 py-5 text-left transition-colors focus:outline-none cursor-pointer"
                >
                  <span className="font-bold text-foreground text-xs md:text-sm flex items-center gap-2">
                    <HelpCircle className={`size-4 shrink-0 transition-colors ${isOpen ? "text-primary" : "text-zinc-400 dark:text-zinc-500"}`} />
                    {faq.q}
                  </span>
                  <ChevronDown
                    className={`size-4 shrink-0 text-muted-foreground transition-transform duration-300 ${
                      isOpen ? "rotate-180 text-primary" : ""
                    }`}
                    strokeWidth={2.5}
                  />
                </button>
                
                <div
                  className={`overflow-hidden transition-all duration-300 ease-in-out ${
                    isOpen ? "max-h-96 opacity-100" : "max-h-0 opacity-0"
                  }`}
                >
                  <p className="px-6 pb-5 text-xs text-muted-foreground leading-relaxed pl-12">
                    {faq.a}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
