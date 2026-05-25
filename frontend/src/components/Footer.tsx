import Link from "next/link";
import { BRAND } from "@/lib/brand";
import { LogoIcon } from "@/components/Logo";

export default function Footer() {
  return (
    <footer className="border-t border-border dark:border-zinc-900 bg-card/60 dark:bg-zinc-950/60 relative">
      <div className="container mx-auto px-4 py-16 max-w-6xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 mb-16">
          
          {/* Logo & Headline */}
          <div className="lg:col-span-4 flex flex-col items-start gap-4">
            <Link href="/" className="flex items-center gap-2.5 hover:opacity-95 transition-opacity">
              <LogoIcon className="size-8" />
              <span className="font-display font-black tracking-tight text-foreground text-lg uppercase">
                Voise <span className="text-accent">AI</span>
              </span>
            </Link>
            <p className="text-xs text-muted-foreground leading-relaxed max-w-xs font-medium">
              Autonomous, real-time conversational voice agents for high-volume Indian operations teams.
            </p>
            <div className="mt-2 text-[9px] font-bold text-accent uppercase tracking-widest bg-accent/5 border border-accent/15 px-3 py-1 rounded-full">
              DPDP ACT 2023 COMPLIANT
            </div>
          </div>

          {/* Links Grid */}
          <div className="lg:col-span-8 grid grid-cols-2 sm:grid-cols-4 gap-8">
            <div>
              <h4 className="text-[10px] font-bold text-foreground uppercase tracking-widest mb-4">Product</h4>
              <ul className="space-y-2.5 text-xs font-semibold">
                <li>
                  <a href="#features" className="text-muted-foreground hover:text-foreground transition-colors">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#how-it-works" className="text-muted-foreground hover:text-foreground transition-colors">
                    How It Works
                  </a>
                </li>
                <li>
                  <a href="#pricing" className="text-muted-foreground hover:text-foreground transition-colors">
                    Pricing
                  </a>
                </li>
                <li>
                  <Link href="/register" className="text-muted-foreground hover:text-foreground transition-colors">
                    Get Started
                  </Link>
                </li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-[10px] font-bold text-foreground uppercase tracking-widest mb-4">Resources</h4>
              <ul className="space-y-2.5 text-xs font-semibold">
                <li>
                  <a href="/" className="text-muted-foreground hover:text-foreground transition-colors">
                    Documentation
                  </a>
                </li>
                <li>
                  <a href="/" className="text-muted-foreground hover:text-foreground transition-colors">
                    API Reference
                  </a>
                </li>
                <li>
                  <a href="/" className="text-muted-foreground hover:text-foreground transition-colors">
                    Support
                  </a>
                </li>
                <li>
                  <a href="/" className="text-muted-foreground hover:text-foreground transition-colors">
                    System Status
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="text-[10px] font-bold text-foreground uppercase tracking-widest mb-4">Company</h4>
              <ul className="space-y-2.5 text-xs font-semibold">
                <li>
                  <a href="/" className="text-muted-foreground hover:text-foreground transition-colors">
                    About Us
                  </a>
                </li>
                <li>
                  <a href="/" className="text-muted-foreground hover:text-foreground transition-colors">
                    Careers
                  </a>
                </li>
                <li>
                  <a href="/" className="text-muted-foreground hover:text-foreground transition-colors">
                    Contact Us
                  </a>
                </li>
                <li>
                  <a href="/" className="text-muted-foreground hover:text-foreground transition-colors">
                    Press Room
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="text-[10px] font-bold text-foreground uppercase tracking-widest mb-4">Legal</h4>
              <ul className="space-y-2.5 text-xs font-semibold">
                <li>
                  <a href="/" className="text-muted-foreground hover:text-foreground transition-colors">
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a href="/" className="text-muted-foreground hover:text-foreground transition-colors">
                    Terms of Service
                  </a>
                </li>
                <li>
                  <a href="/" className="text-muted-foreground hover:text-foreground transition-colors">
                    Data Consent
                  </a>
                </li>
              </ul>
            </div>
          </div>

        </div>

        {/* Footer Base */}
        <div className="pt-8 border-t border-border dark:border-zinc-900 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-[10px] font-bold text-muted-foreground tracking-widest uppercase">
            {BRAND.copyright}
          </p>
          <p className="text-[10px] text-zinc-400 dark:text-zinc-500 font-bold uppercase tracking-wider">
            Engineered with intention. Built for high scale.
          </p>
        </div>
      </div>
    </footer>
  );
}
