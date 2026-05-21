import Link from "next/link";
import { BRAND } from "@/lib/brand";

export default function Footer() {
    return (
        <footer className="bg-[var(--bg-base)] text-[var(--text-secondary)] text-sm relative">
            {/* Brand gradient top border separator */}
            <div className="h-[1px] w-full bg-gradient-to-r from-transparent via-[var(--accent-cyan)]/30 to-transparent" />
            
            <div className="container mx-auto px-6 py-16">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-10 mb-12">
                    <div className="space-y-4">
                        <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)]">Product</h4>
                        <ul className="space-y-2.5">
                            <li><a href="#features" className="hover:text-[var(--text-primary)] transition-colors">Features</a></li>
                            <li><a href="#stats" className="hover:text-[var(--text-primary)] transition-colors">Results</a></li>
                            <li><a href="#testimonials" className="hover:text-[var(--text-primary)] transition-colors">Testimonials</a></li>
                            <li><Link href="/register" className="hover:text-[var(--text-primary)] transition-colors">Get started</Link></li>
                        </ul>
                    </div>
                    <div className="space-y-4">
                        <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)]">Resources</h4>
                        <ul className="space-y-2.5">
                            <li><a href="#" className="hover:text-[var(--text-primary)] transition-colors">Help center</a></li>
                            <li><Link href="/dashboard" className="hover:text-[var(--text-primary)] transition-colors">Dashboard</Link></li>
                            <li><a href="#" className="hover:text-[var(--text-primary)] transition-colors">Support</a></li>
                            <li><a href="#" className="hover:text-[var(--text-primary)] transition-colors">Status</a></li>
                        </ul>
                    </div>
                    <div className="space-y-4">
                        <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)]">Company</h4>
                        <ul className="space-y-2.5">
                            <li><a href="#" className="hover:text-[var(--text-primary)] transition-colors">About</a></li>
                            <li><a href="#" className="hover:text-[var(--text-primary)] transition-colors">Careers</a></li>
                            <li><a href="#" className="hover:text-[var(--text-primary)] transition-colors">Contact</a></li>
                            <li><a href="#" className="hover:text-[var(--text-primary)] transition-colors">Press</a></li>
                        </ul>
                    </div>
                    <div className="space-y-4">
                        <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)]">Legal</h4>
                        <ul className="space-y-2.5">
                            <li><a href="#" className="hover:text-[var(--text-primary)] transition-colors">Privacy Policy</a></li>
                            <li><a href="#" className="hover:text-[var(--text-primary)] transition-colors">Terms of Service</a></li>
                            <li><a href="#" className="hover:text-[var(--text-primary)] transition-colors">Security</a></li>
                        </ul>
                    </div>
                </div>

                <div className="flex flex-col md:flex-row justify-between items-center pt-8 border-t border-[var(--border-subtle)] gap-4">
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 bg-gradient-to-br from-[var(--accent-cyan)] to-[var(--accent-purple)] rounded flex items-center justify-center text-white font-bold text-xs shadow-md shadow-[var(--accent-cyan)]/10">
                            V
                        </div>
                        <span className="text-[var(--text-primary)] font-semibold text-xs tracking-wide">{BRAND.product}</span>
                    </div>

                    <p className="text-xs text-[var(--text-tertiary)]">{BRAND.copyright}</p>
                </div>
            </div>
        </footer>
    );
}
