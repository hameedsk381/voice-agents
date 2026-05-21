"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { BRAND } from "@/lib/brand";
import ThemeToggle from "@/components/ThemeToggle";

export default function Navbar() {
    const { isAuthenticated } = useAuth();

    return (
        <motion.nav
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 bg-[var(--bg-base)]/60 backdrop-blur-xl border-b border-[var(--border-subtle)]"
        >
            <Link href="/" className="flex items-center gap-2.5 group">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--accent-cyan)] to-[var(--accent-purple)] flex items-center justify-center shadow-lg shadow-[var(--accent-cyan)]/20 group-hover:shadow-[var(--accent-cyan)]/40 transition-shadow duration-300">
                    <span className="text-white font-bold text-base">V</span>
                </div>
                <span className="text-lg font-semibold tracking-tight text-[var(--text-primary)]">
                    {BRAND.name}
                </span>
            </Link>

            <div className="hidden md:flex items-center gap-8">
                {[
                    { label: "Features", href: "#features" },
                    { label: "Results", href: "#stats" },
                    { label: "Testimonials", href: "#testimonials" },
                    { label: "Platform", href: "/register" },
                ].map((item) => (
                    <Link
                        key={item.label}
                        href={item.href}
                        className="relative text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors duration-200 group"
                    >
                        {item.label}
                        <span className="absolute -bottom-1 left-0 w-0 h-[2px] bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] group-hover:w-full transition-all duration-300" />
                    </Link>
                ))}
            </div>

            <div className="flex items-center gap-3">
                <ThemeToggle />
                {isAuthenticated ? (
                    <Link
                        href="/dashboard"
                        className="px-5 py-2 text-sm font-semibold rounded-full bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white hover:shadow-lg hover:shadow-[var(--accent-cyan)]/25 transition-all duration-300 hover:-translate-y-0.5"
                    >
                        Dashboard
                    </Link>
                ) : (
                    <>
                        <Link
                            href="/login"
                            className="text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                        >
                            Sign In
                        </Link>
                        <Link href="/register">
                            <button className="px-5 py-2 text-sm font-semibold rounded-full bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-purple)] text-white hover:shadow-lg hover:shadow-[var(--accent-cyan)]/25 transition-all duration-300 hover:-translate-y-0.5 active:scale-95">
                                Get Started
                            </button>
                        </Link>
                    </>
                )}
            </div>
        </motion.nav>
    );
}
