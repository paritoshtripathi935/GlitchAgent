export default function Logo({ size = 28, compact = false }: { size?: number; compact?: boolean }) {
  return (
    <span className="inline-flex items-center gap-3">
      <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
        <rect width="32" height="32" rx="8" className="fill-raised stroke-line" strokeWidth="1" />
        <path d="M8 11l6 5-6 5" fill="none" className="stroke-accent" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        <rect x="16" y="19" width="8" height="2.5" rx="1.25" className="fill-accent caret" />
      </svg>
      <span className={`font-display font-semibold text-body ${compact ? 'hidden md:inline' : ''}`}>GlitchAgent</span>
    </span>
  );
}
