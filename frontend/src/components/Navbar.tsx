"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import ThemeToggle from "@/components/ThemeToggle";
import { LogoFull } from "@/components/Logo";

export default function Navbar() {
  const { isAuthenticated } = useAuth();

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="fixed top-4 left-1/2 -translate-x-1/2 z-50 w-[calc(100%-2rem)] max-w-5xl"
    >
      <div className="flex items-center justify-between px-6 py-3 rounded-2xl bg-white/70 dark:bg-zinc-950/80 backdrop-blur-xl border border-zinc-200/80 dark:border-zinc-800/80 shadow-2xl shadow-black/5 dark:shadow-black/20">
        <Link href="/" className="flex items-center gap-2 hover:opacity-95 transition-opacity">
          <LogoFull />
        </Link>

        {/* Navigation Items */}
        <div className="hidden md:flex items-center gap-1.5">
          {[
            { label: "Features", href: "#features" },
            { label: "How It Works", href: "#how-it-works" },
            { label: "Pricing", href: "#pricing" },
            { label: "FAQ", href: "#faq" },
          ].map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className="px-3.5 py-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground transition-all rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-900/50 relative group"
            >
              {item.label}
              <span className="absolute bottom-1 left-3.5 right-3.5 h-[1.5px] bg-primary scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-200" />
            </Link>
          ))}
        </div>

        {/* Right side actions */}
        <div className="flex items-center gap-3">
          <ThemeToggle />
          {isAuthenticated ? (
            <Link
              href="/dashboard"
              className="text-xs font-bold bg-primary text-primary-foreground px-4 py-2 rounded-xl hover:brightness-110 active:scale-[0.98] transition-all shadow-md shadow-primary/10"
            >
              Dashboard
            </Link>
          ) : (
            <>
              <Link
                href="/login"
                className="text-xs font-bold text-muted-foreground hover:text-foreground transition-colors hidden sm:inline px-2 py-1"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="text-xs font-extrabold bg-gradient-to-r from-primary to-cyan-500 text-primary-foreground px-4.5 py-2.5 rounded-xl hover:brightness-110 active:scale-[0.98] transition-all shadow-md shadow-primary/20"
              >
                Get Started
              </Link>
            </>
          )}
        </div>
      </div>
    </motion.nav>
  );
}
