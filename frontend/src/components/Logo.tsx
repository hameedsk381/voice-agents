export function LogoIcon({ className = "size-8" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} aria-label="Voise AI">
      <defs>
        <linearGradient id="logo-grad" x1="0" y1="0" x2="32" y2="32">
          <stop offset="0%" stopColor="var(--primary, #38bdf8)" />
          <stop offset="100%" stopColor="var(--accent, #facc15)" />
        </linearGradient>
      </defs>
      {/* Outer ring */}
      <circle cx="16" cy="16" r="14" stroke="url(#logo-grad)" strokeWidth="2" opacity="0.3" />
      {/* Sound wave bars */}
      <rect x="10" y="12" width="2.5" height="8" rx="1.25" fill="var(--primary, #38bdf8)" opacity="0.7" />
      <rect x="14.75" y="9" width="2.5" height="14" rx="1.25" fill="url(#logo-grad)" />
      <rect x="19.5" y="11" width="2.5" height="10" rx="1.25" fill="var(--accent, #facc15)" opacity="0.9" />
      {/* Center dot */}
      <circle cx="16" cy="16" r="2" fill="url(#logo-grad)" />
    </svg>
  );
}

export function LogoFull({ showTagline, className }: { showTagline?: boolean; className?: string }) {
  return (
    <div className={`flex items-center gap-2.5 ${className || ""}`}>
      <LogoIcon className="size-9 shrink-0" />
      <div className="flex flex-col">
        <span className="font-display font-bold tracking-tight text-foreground text-lg leading-none">
          Voise <span className="text-accent">AI</span>
        </span>
        {showTagline && (
          <span className="text-[10px] text-muted-foreground leading-tight mt-0.5">
            Voice automation platform
          </span>
        )}
      </div>
    </div>
  );
}
