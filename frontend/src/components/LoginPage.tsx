/**
 * Split-screen sign-in. Left: a replay of a real command → plan → result,
 * so the first thing a visitor sees is what the product does. Right: Clerk.
 */
import { SignIn } from '@clerk/clerk-react';
import { ArrowLeft } from 'lucide-react';
import Logo from './Logo';

const LINES = [
  ['$', 'open news.ycombinator.com and search for "playwright"'],
  ['1', 'navigate  https://news.ycombinator.com'],
  ['2', 'click     role=link[name="search"]'],
  ['3', 'fill      input[name="q"]  ←  "playwright"'],
  ['4', 'press     Enter'],
  ['✓', 'done · screenshot saved'],
];

export default function LoginPage({ onBack }: { onBack: () => void }) {
  return (
    <div className="min-h-screen grid lg:grid-cols-[1.2fr_1fr] bg-bg">
      <aside className="hidden lg:flex flex-col justify-between p-12 border-r border-line bg-surface">
        <Logo />
        <div>
          <p className="font-display text-h2 font-semibold max-w-md">
            You type the intent.<br /><span className="text-accent">It figures out the clicks.</span>
          </p>
          <pre className="mt-8 rounded-xl border border-line bg-bg p-6 font-mono text-small leading-7 overflow-x-auto">
            {LINES.map(([n, l], i) => (
              <div key={i} className="rise" style={{ animationDelay: `${i * 350}ms` }}>
                <span className={n === '$' || n === '✓' ? 'text-accent' : 'text-dim'}>{n.padStart(2)}  </span>{l}
              </div>
            ))}
          </pre>
        </div>
        <p className="text-caption text-dim">Playwright under the hood · Llama 3.1 70B on Cloudflare Workers AI</p>
      </aside>
      <main className="flex flex-col items-center justify-center gap-6 p-6">
        <div className="w-full max-w-sm flex items-center justify-between">
          <button onClick={onBack} className="inline-flex items-center gap-2 text-small text-muted hover:text-fg cursor-pointer">
            <ArrowLeft size={15} /> Back
          </button>
          <span className="lg:hidden"><Logo size={24} /></span>
        </div>
        <SignIn routing="hash" />
      </main>
    </div>
  );
}
