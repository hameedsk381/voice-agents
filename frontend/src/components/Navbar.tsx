"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";

export default function Navbar() {
    const { isAuthenticated } = useAuth();

    return (
        <motion.nav
            initial={{ y: -100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 bg-black/50 backdrop-blur-md border-b border-white/10"
        >
            <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-xl">V</span>
                </div>
                <span className="text-xl font-bold tracking-tight text-white">
                    OpenVoice
                </span>
            </div>

            <div className="hidden md:flex items-center gap-8">
                {["Features", "Architecture", "Pricing", "Docs"].map((item) => (
                    <Link
                        key={item}
                        href={`#${item.toLowerCase()}`}
                        className="text-sm font-medium text-gray-400 hover:text-white transition-colors"
                    >
                        {item}
                    </Link>
                ))}
            </div>

            <div className="flex items-center gap-4">
                {isAuthenticated ? (
                    <Link
                        href="/dashboard"
                        className="px-5 py-2 text-sm font-medium text-black bg-white rounded-full hover:bg-gray-200 transition-colors"
                    >
                        Dashboard
                    </Link>
                ) : (
                    <>
                        <Link
                            href="/login"
                            className="text-sm font-medium text-white hover:text-blue-400 transition-colors"
                        >
                            Sign In
                        </Link>
                        <Link href="/register">
                            <button className="px-5 py-2 text-sm font-medium text-black bg-white rounded-full hover:bg-gray-200 transition-colors">
                                Get Started
                            </button>
                        </Link>
                    </>
                )}
            </div>
        </motion.nav>
    );
}
