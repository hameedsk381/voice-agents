"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Phone, PhoneCall, RotateCcw, ChevronRight } from "lucide-react";

const SCENARIOS = [
  {
    id: "payment_reminder",
    label: "EMI Reminder",
    language: "Hindi",
    preview: "Agent reminds a borrower of an overdue EMI, handles pushback, and negotiates a payment date.",
  },
  {
    id: "lead_qualification",
    label: "Lead Screening",
    language: "English",
    preview: "Agent qualifies a real estate enquiry — captures budget, location, and books a site visit.",
  },
  {
    id: "appointment_booking",
    label: "Appointment Booking",
    language: "English / Tamil",
    preview: "Agent handles an inbound clinic call, checks available slots, and confirms a booking.",
  },
];

type State = "idle" | "calling" | "done" | "error";

export default function LiveDemo() {
  const [phone, setPhone] = useState("");
  const [scenario, setScenario] = useState(SCENARIOS[0].id);
  const [state, setState] = useState<State>("idle");
  const [error, setError] = useState("");

  const selectedScenario = SCENARIOS.find((s) => s.id === scenario)!;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const digits = phone.replace(/\D/g, "");
    if (digits.length < 10) {
      setError("Enter a valid 10-digit mobile number.");
      return;
    }
    setError("");
    setState("calling");

    try {
      const res = await fetch("/api/v1/demo/call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: `+91${digits.slice(-10)}`, scenario }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Call could not be initiated.");
      }
      setState("done");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      setState("error");
    }
  };

  const reset = () => {
    setState("idle");
    setError("");
  };

  return (
    <section className="py-24 relative border-t border-border dark:border-zinc-900 overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-primary/5 rounded-full blur-[140px] pointer-events-none" />

      <div className="container mx-auto px-4 max-w-5xl relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-14"
        >
          <span className="text-[10px] font-bold text-primary uppercase tracking-[0.25em] block mb-3">
            LIVE PRODUCT DEMO
          </span>
          <h2 className="font-display font-black text-3xl sm:text-4xl tracking-tight text-foreground uppercase">
            HEAR IT. DON&apos;T JUST READ ABOUT IT.
          </h2>
          <p className="text-muted-foreground text-sm sm:text-base max-w-xl mx-auto mt-4 leading-relaxed">
            Enter your number. Pick a scenario. Get a real call from our AI agent in under 60 seconds —
            no signup, no credit card.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start"
        >
          {/* Left: Scenario info */}
          <div className="space-y-3">
            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-4">
              CHOOSE YOUR SCENARIO
            </p>
            {SCENARIOS.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => { setScenario(s.id); reset(); }}
                className={`w-full text-left rounded-2xl border p-4 transition-all duration-200 ${
                  scenario === s.id
                    ? "border-primary/40 bg-primary/5 dark:bg-primary/10 shadow-sm"
                    : "border-border bg-card dark:bg-zinc-950/60 hover:border-zinc-300 dark:hover:border-zinc-800"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className={`text-sm font-bold ${scenario === s.id ? "text-primary" : "text-foreground"}`}>
                    {s.label}
                  </span>
                  <span className="text-[10px] font-semibold text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                    {s.language}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">{s.preview}</p>
                {scenario === s.id && (
                  <div className="flex items-center gap-1 mt-2 text-[10px] font-bold text-primary">
                    <ChevronRight className="size-3" />
                    Selected
                  </div>
                )}
              </button>
            ))}
          </div>

          {/* Right: Form / Status */}
          <div className="lg:sticky lg:top-28">
            <div className="rounded-2xl border border-border dark:border-zinc-800 bg-card dark:bg-zinc-950/80 shadow-xl p-6">
              <AnimatePresence mode="wait">
                {state === "idle" || state === "error" ? (
                  <motion.form
                    key="form"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onSubmit={handleSubmit}
                    className="space-y-5"
                  >
                    <div>
                      <label className="block text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-2">
                        Your Mobile Number
                      </label>
                      <div className="flex items-center gap-2 border border-border dark:border-zinc-800 rounded-xl px-3 py-2.5 bg-muted/30 dark:bg-zinc-900/40 focus-within:border-primary/50 transition-colors">
                        <span className="text-xs font-bold text-muted-foreground shrink-0">+91</span>
                        <div className="w-px h-4 bg-border" />
                        <input
                          type="tel"
                          value={phone}
                          onChange={(e) => setPhone(e.target.value.replace(/\D/g, "").slice(0, 10))}
                          placeholder="98400 00000"
                          className="flex-1 bg-transparent text-sm font-semibold text-foreground placeholder:text-muted-foreground/50 focus:outline-none"
                          maxLength={10}
                        />
                        {phone.length === 10 && (
                          <div className="size-4 rounded-full bg-green-500 flex items-center justify-center shrink-0">
                            <span className="text-[8px] text-white font-black">✓</span>
                          </div>
                        )}
                      </div>
                      {error && (
                        <p className="text-xs text-destructive font-semibold mt-1.5">{error}</p>
                      )}
                    </div>

                    <div className="rounded-xl bg-muted/40 dark:bg-zinc-900/40 border border-border dark:border-zinc-800/60 p-3">
                      <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-1">
                        Your call will demonstrate:
                      </p>
                      <ul className="space-y-1">
                        {[
                          "Natural conversation — interruptions welcome",
                          `${selectedScenario.language} language, regional accent`,
                          "Memory, empathy, and goal tracking",
                          selectedScenario.label === "EMI Reminder"
                            ? "Empathetic negotiation under resistance"
                            : selectedScenario.label === "Lead Screening"
                            ? "Budget & intent qualification"
                            : "Slot availability and SMS confirmation",
                        ].map((item) => (
                          <li key={item} className="flex items-start gap-1.5 text-[10px] text-foreground/70 font-medium">
                            <span className="text-primary mt-0.5 shrink-0">→</span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <button
                      type="submit"
                      disabled={phone.length < 10}
                      className="w-full flex items-center justify-center gap-2 h-12 rounded-xl bg-gradient-to-r from-primary to-cyan-500 text-primary-foreground font-extrabold text-sm hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-primary/20"
                    >
                      <Phone className="size-4" />
                      Call Me Now
                    </button>

                    <p className="text-[10px] text-muted-foreground/60 text-center leading-relaxed">
                      One demo call per number per day. We will not add you to any campaign.
                      Call lasts 2–3 minutes.
                    </p>
                  </motion.form>
                ) : state === "calling" ? (
                  <motion.div
                    key="calling"
                    initial={{ opacity: 0, scale: 0.97 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex flex-col items-center justify-center py-8 text-center gap-5"
                  >
                    <div className="relative">
                      <div className="size-16 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center">
                        <PhoneCall className="size-7 text-primary animate-pulse" />
                      </div>
                      {[1, 2, 3].map((ring) => (
                        <div
                          key={ring}
                          className="absolute inset-0 rounded-full border border-primary/20 animate-ping"
                          style={{ animationDelay: `${ring * 0.3}s`, animationDuration: "1.5s" }}
                        />
                      ))}
                    </div>
                    <div>
                      <p className="text-sm font-bold text-foreground">Connecting your call…</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        +91 {phone} · {selectedScenario.label}
                      </p>
                    </div>
                    <p className="text-xs text-muted-foreground max-w-xs leading-relaxed">
                      Your phone will ring within 60 seconds. Pick up and talk naturally —
                      interrupt the agent, push back, ask questions.
                    </p>
                    <div className="w-full rounded-xl bg-muted/40 border border-border p-3 text-left">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">
                        Scenario loaded
                      </p>
                      <p className="text-xs text-foreground font-semibold">{selectedScenario.label}</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">{selectedScenario.preview}</p>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div
                    key="done"
                    initial={{ opacity: 0, scale: 0.97 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex flex-col items-center justify-center py-8 text-center gap-5"
                  >
                    <div className="size-16 rounded-full bg-green-500/10 border border-green-500/30 flex items-center justify-center">
                      <span className="text-2xl">✓</span>
                    </div>
                    <div>
                      <p className="text-sm font-bold text-foreground">Call complete.</p>
                      <p className="text-xs text-muted-foreground mt-1 max-w-xs leading-relaxed">
                        If the product worked for you, we&apos;d love to show you what it looks like
                        deployed in your business.
                      </p>
                    </div>
                    <div className="flex flex-col sm:flex-row gap-3 w-full">
                      <a
                        href="/pilot"
                        className="flex-1 flex items-center justify-center gap-2 h-10 rounded-xl bg-gradient-to-r from-primary to-cyan-500 text-primary-foreground font-bold text-xs hover:brightness-110 transition-all"
                      >
                        Apply for a Free Pilot
                      </a>
                      <button
                        type="button"
                        onClick={reset}
                        className="flex-1 flex items-center justify-center gap-2 h-10 rounded-xl border border-border text-foreground font-semibold text-xs hover:bg-muted/50 transition-colors"
                      >
                        <RotateCcw className="size-3.5" />
                        Try Another Scenario
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
