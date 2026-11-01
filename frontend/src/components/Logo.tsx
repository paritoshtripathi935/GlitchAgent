export default function Logo({ size = 28 }: { size?: number }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
        <rect width="32" height="32" rx="8" className="fill-raised stroke-line" strokeWidth="1" />
        <path d="M8 11l6 5-6 5" fill="none" className="stroke-accent" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        <rect x="16" y="19" width="8" height="2.5" rx="1.25" className="fill-accent caret" />
      </svg>
      <span className="font-display font-semibold tracking-tight text-[17px]">GlitchAgent</span>
    </span>
  );
}
