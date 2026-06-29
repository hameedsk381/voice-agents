"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, CheckCircle2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const INDUSTRIES = [
  "Collections / NBFC",
  "Real Estate Agency",
  "Healthcare Clinic",
  "EdTech / Coaching",
  "Insurance",
  "Logistics / Delivery",
  "Other",
];

const VOLUMES = [
  "Under 500 calls/month",
  "500–2,000 calls/month",
  "2,000–10,000 calls/month",
  "Over 10,000 calls/month",
];

type FormState = "idle" | "submitting" | "done" | "error";

function PilotForm() {
  const searchParams = useSearchParams();
  const prefillIndustry = searchParams.get("industry") || "";

  const [form, setForm] = useState({
    name: "",
    company: "",
    industry: prefillIndustry,
    volume: "",
    phone: "",
    email: "",
    use_case: "",
  });
  const [formState, setFormState] = useState<FormState>("idle");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (prefillIndustry) setForm((f) => ({ ...f, industry: prefillIndustry }));
  }, [prefillIndustry]);

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const valid =
    form.name.trim() &&
    form.company.trim() &&
    form.industry &&
    form.volume &&
    form.phone.replace(/\D/g, "").length >= 10 &&
    form.email.includes("@") &&
    form.use_case.trim().length >= 20;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!valid) return;
    setFormState("submitting");
    setErrorMsg("");

    try {
      const res = await fetch("/api/v1/demo/pilot-apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          phone_number: `+91${form.phone.replace(/\D/g, "").slice(-10)}`,
        }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Submission failed.");
      }
      setFormState("done");
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      setFormState("error");
    }
  };

  if (formState === "done") {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center text-center gap-6 py-16"
      >
        <div className="size-20 rounded-full bg-green-500/10 border border-green-500/30 flex items-center justify-center">
          <CheckCircle2 className="size-9 text-green-500" />
        </div>
        <div>
          <h2 className="font-display font-black text-2xl text-foreground uppercase mb-3">
            Application received.
          </h2>
          <p className="text-muted-foreground text-sm max-w-md leading-relaxed">
            We review pilot applications manually and respond within 48 hours. You&apos;ll
            hear from us at <span className="text-foreground font-semibold">{form.email}</span>.
          </p>
        </div>
        <div className="rounded-2xl border border-border bg-card p-5 text-left max-w-sm w-full">
          <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-3">
            What happens next
          </p>
          {[
            "We review your use case and call volume",
            "30-minute scoping call with our team",
            "Agent deployed in your environment",
            "30-day live pilot, fully supported",
            "You own the outcome data",
          ].map((step, i) => (
            <div key={i} className="flex items-start gap-3 mb-2 last:mb-0">
              <span className="size-5 rounded-full bg-primary/10 text-primary text-[9px] font-black flex items-center justify-center shrink-0 mt-0.5">
                {i + 1}
              </span>
              <p className="text-xs text-foreground/80">{step}</p>
            </div>
          ))}
        </div>
        <Link href="/" className="text-xs text-primary font-semibold hover:underline">
          ← Back to homepage
        </Link>
      </motion.div>
    );
  }

  const inputCls = "w-full border border-border dark:border-zinc-800 rounded-xl px-3.5 py-2.5 text-sm bg-muted/20 dark:bg-zinc-900/40 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/50 transition-colors";
  const labelCls = "block text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-1.5";

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div>
          <label className={labelCls}>Your Name</label>
          <input className={inputCls} placeholder="Priya Sharma" value={form.name} onChange={set("name")} required />
        </div>
        <div>
          <label className={labelCls}>Company Name</label>
          <input className={inputCls} placeholder="Acme Finance Ltd." value={form.company} onChange={set("company")} required />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div>
          <label className={labelCls}>Industry</label>
          <select className={inputCls} value={form.industry} onChange={set("industry")} required>
            <option value="" disabled>Select industry…</option>
            {INDUSTRIES.map((ind) => (
              <option key={ind} value={ind}>{ind}</option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelCls}>Monthly Call Volume</label>
          <select className={inputCls} value={form.volume} onChange={set("volume")} required>
            <option value="" disabled>Select range…</option>
            {VOLUMES.map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div>
          <label className={labelCls}>Mobile Number</label>
          <div className="flex items-center gap-2 border border-border dark:border-zinc-800 rounded-xl px-3.5 py-2.5 bg-muted/20 dark:bg-zinc-900/40 focus-within:border-primary/50 transition-colors">
            <span className="text-xs font-bold text-muted-foreground shrink-0">+91</span>
            <div className="w-px h-4 bg-border" />
            <input
              type="tel"
              value={form.phone}
              onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value.replace(/\D/g, "").slice(0, 10) }))}
              placeholder="98400 00000"
              className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none"
              maxLength={10}
              required
            />
          </div>
        </div>
        <div>
          <label className={labelCls}>Work Email</label>
          <input type="email" className={inputCls} placeholder="priya@acmefinance.in" value={form.email} onChange={set("email")} required />
        </div>
      </div>

      <div>
        <label className={labelCls}>
          Describe your use case
          <span className="text-primary ml-1">*</span>
        </label>
        <textarea
          className={`${inputCls} resize-none h-28`}
          placeholder="E.g. We run an NBFC with 3,000 overdue borrowers each month. Currently have 8 agents calling manually. We want to automate the first-touch reminder call in Hindi and Tamil…"
          value={form.use_case}
          onChange={set("use_case")}
          required
          minLength={20}
        />
        <p className="text-[10px] text-muted-foreground/60 mt-1">
          Min 20 characters. The more detail, the faster we can evaluate fit.
        </p>
      </div>

      {errorMsg && (
        <p className="text-xs text-destructive font-semibold">{errorMsg}</p>
      )}

      <button
        type="submit"
        disabled={!valid || formState === "submitting"}
        className="w-full h-12 rounded-xl bg-gradient-to-r from-primary to-cyan-500 text-primary-foreground font-extrabold text-sm hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-primary/20"
      >
        {formState === "submitting" ? "Submitting…" : "Apply for a Free Pilot →"}
      </button>

      <p className="text-[10px] text-muted-foreground/60 text-center leading-relaxed">
        Pilots are free. We ask for a 30-minute debrief and permission to publish anonymized results.
        We will never share your contact details.
      </p>
    </form>
  );
}

export default function PilotPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />
      <main className="container mx-auto px-4 max-w-2xl py-24">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Link href="/" className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors mb-8">
            <ArrowLeft className="size-3.5" />
            Back to home
          </Link>

          <span className="text-[10px] font-bold text-primary uppercase tracking-[0.25em] block mb-3">
            EARLY ACCESS
          </span>
          <h1 className="font-display font-black text-3xl sm:text-4xl tracking-tight text-foreground uppercase mb-4">
            APPLY FOR A FREE PILOT
          </h1>
          <p className="text-muted-foreground text-sm leading-relaxed mb-10 max-w-lg">
            We have 3 pilot slots open. We deploy Voise AI in your business at zero cost for 30 days.
            You own the data. We earn a case study. No lock-in.
          </p>

          {/* Value exchange box */}
          <div className="rounded-2xl border border-border dark:border-zinc-900 bg-muted/10 dark:bg-zinc-950/40 p-5 mb-10">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-[10px] font-black text-primary uppercase tracking-wider mb-2">You get</p>
                {["Full AI agent deployment", "Your use case, your data", "30 days of live calls", "CRM / calendar integration", "Real outcome report"].map((item) => (
                  <div key={item} className="flex items-center gap-2 mb-1.5">
                    <span className="text-green-500 text-xs font-bold">✓</span>
                    <span className="text-xs text-foreground/80">{item}</span>
                  </div>
                ))}
              </div>
              <div>
                <p className="text-[10px] font-black text-muted-foreground uppercase tracking-wider mb-2">We ask for</p>
                {["30-min debrief call", "Permission to publish results", "Anonymized data is fine"].map((item) => (
                  <div key={item} className="flex items-center gap-2 mb-1.5">
                    <span className="text-muted-foreground text-xs">→</span>
                    <span className="text-xs text-muted-foreground">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <Suspense fallback={<div className="h-96 animate-pulse rounded-2xl bg-muted/20" />}>
            <PilotForm />
          </Suspense>
        </motion.div>
      </main>
      <Footer />
    </div>
  );
}
