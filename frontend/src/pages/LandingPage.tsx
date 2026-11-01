/**
 * LandingPage — public marketing page for signed-out visitors. Every CTA
 * calls `onStart` (opens the Clerk sign-in); when auth isn't configured on
 * this deploy, CTAs fall back to the source repo.
 */
import { useEffect, useState, type ReactNode } from 'react';
import {
  ArrowRight, Camera, ChevronDown, Eye, GitBranch, History, MessageSquareText, Wrench,
} from 'lucide-react';
import Logo from '../components/Logo';
import ThemeToggle from '../components/ThemeToggle';
import ActionList from '../components/ActionList';
import type { BrowserAction } from '../types';

const REPO = 'https://github.com/paritoshtripathi935/GlitchAgent';

const DEMO_COMMAND = 'search GitHub for "playwright python" and open the first result';
const DEMO_PLAN: BrowserAction[] = [
  { action: 'navigate', url: 'https://github.com/search' },
  { action: 'fill', locator: 'input[name="q"]', text: 'playwright python' },
  { action: 'press', key: 'Enter' },
  { action: 'wait', time_ms: 1500 },
  { action: 'click', locator: '[data-testid="results-list"] a >> nth=0' },
  { action: 'screenshot' },
];

const FEATURES: [typeof MessageSquareText, string, string][] = [
  [MessageSquareText, 'Plain-English commands', 'Write what you want done the way you would ask a colleague. No selectors, no scripts.'],
  [Eye, 'A plan you can read', 'Every command becomes a short list of browser actions you can check before trusting the result.'],
  [Wrench, 'Self-healing selectors', 'When a click or fill misses, the agent reads the page HTML and retries with a better locator.'],
  [Camera, 'Proof in screenshots', 'Each run ends with a screenshot of the final page, so you see what actually happened.'],
  [History, 'Every run on record', 'Commands, outcomes and errors are saved to your history for review later.'],
  [GitBranch, 'Open source', 'FastAPI + Playwright backend and this React frontend, all on GitHub.'],
];

const STEPS: [string, string, string][] = [
  ['01', 'Describe', 'Type the task: "log in, open settings, turn on 2FA".'],
  ['02', 'Review the plan', 'The model turns it into navigate / click / fill / press steps.'],
  ['03', 'Watch it run', 'A real Chromium browser executes them and hands back a screenshot.'],
];

const VOCAB = ['navigate', 'click', 'fill', 'press', 'select', 'hover', 'wait', 'submit', 'screenshot'];

const FAQS: [string, string][] = [
  ['Is it free?', 'Yes. GlitchAgent is an open-source beta; there is nothing to pay for.'],
  ['Which model plans the actions?', 'Llama 3.1 70B Instruct, served by Cloudflare Workers AI.'],
  ['Should I put passwords in commands?', 'No. Commands are saved to your run history as written, so keep secrets out of them.'],
  ['What sites does it work on?', 'Any public site Chromium can open. Sites with CAPTCHAs or heavy bot protection will stop it, by design.'],
  ['Can I see the browser?', 'Runs are headless on the server; you get the action plan and a final screenshot for every run.'],
];

function Cta({ onStart, children, ghost = false }: { onStart?: () => void; children: ReactNode; ghost?: boolean }) {
  const cls = ghost
    ? 'border border-line text-fg hover:bg-hover'
    : 'bg-accent text-ink hover:brightness-110 shadow-[0_0_24px_var(--accent-soft)]';
  const base = `inline-flex items-center justify-center gap-2 rounded-lg px-6 h-11 text-small font-semibold transition-all cursor-pointer ${cls}`;
  return onStart
    ? <button onClick={onStart} className={base}>{children}</button>
    : <a href={REPO} className={base}>{children}</a>;
}

const Eyebrow = ({ children }: { children: ReactNode }) => (
  <p className="font-mono text-caption uppercase tracking-wider text-accent mb-3">{children}</p>
);

/** Types the command, then reveals the plan step by step. */
const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function DemoConsole() {
  const [typed, setTyped] = useState(() => (reducedMotion() ? DEMO_COMMAND.length : 0));
  const [step, setStep] = useState(() => (reducedMotion() ? DEMO_PLAN.length : -1));
  useEffect(() => {
    if (reducedMotion()) return;
    let i = 0;
    const id = window.setInterval(() => {
      i += 1;
      if (i <= DEMO_COMMAND.length) setTyped(i);
      else if (i % 6 === 0) setStep(s => (s >= DEMO_PLAN.length ? s : s + 1));
      if (i > DEMO_COMMAND.length + DEMO_PLAN.length * 6 + 6) window.clearInterval(id);
    }, 45);
    return () => window.clearInterval(id);
  }, []);
  const done = step >= DEMO_PLAN.length;
  return (
    <div className="rounded-2xl border border-line bg-surface overflow-hidden shadow-2xl shadow-black/20">
      <div className="flex items-center gap-2 px-4 h-10 border-b border-line">
        {[0, 1, 2].map(i => <span key={i} className="h-2.5 w-2.5 rounded-full bg-hover" />)}
        <span className="ml-3 font-mono text-caption text-dim">glitch console</span>
      </div>
      <div className="px-4 py-4 font-mono text-small border-b border-line">
        <span className="text-accent">❯ </span>{DEMO_COMMAND.slice(0, typed)}
        {typed < DEMO_COMMAND.length && <span className="caret">▍</span>}
      </div>
      <div className="min-h-[234px]">
        {step >= 0 && <ActionList actions={DEMO_PLAN.slice(0, step + 1)} activeIndex={done ? undefined : step} />}
      </div>
      <div className="px-4 h-10 flex items-center justify-between border-t border-line font-mono text-caption">
        <span className={done ? 'text-accent' : 'text-dim'}>{done ? '✓ completed · screenshot ready' : step >= 0 ? 'running…' : 'planning…'}</span>
        <span className="text-dim">{Math.max(0, Math.min(step + 1, DEMO_PLAN.length))}/{DEMO_PLAN.length}</span>
      </div>
    </div>
  );
}

export default function LandingPage({ onStart }: { onStart?: () => void }) {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <div className="min-h-screen bg-bg text-fg">
      <header className="sticky top-0 z-20 border-b border-line bg-bg/80 backdrop-blur">
        <nav className="mx-auto max-w-6xl px-4 sm:px-6 h-16 flex items-center justify-between">
          <Logo />
          <div className="hidden md:flex items-center gap-8 text-small text-muted">
            <a href="#features" className="py-2 hover:text-fg">Features</a>
            <a href="#how" className="py-2 hover:text-fg">How it works</a>
            <a href="#faq" className="py-2 hover:text-fg">FAQ</a>
            <a href={REPO} className="py-2 hover:text-fg">GitHub</a>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            {onStart && <button onClick={onStart} className="hidden sm:inline text-small text-muted hover:text-fg px-3 cursor-pointer">Sign in</button>}
            <Cta onStart={onStart}>Open console</Cta>
          </div>
        </nav>
      </header>

      <main>
        <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-16 pb-24 md:pt-24 grid lg:grid-cols-[1fr_1.1fr] gap-12 items-center">
          <div>
            <Eyebrow>Natural-language browser automation</Eyebrow>
            <h1 className="font-display text-h1 sm:text-display font-semibold">
              Tell the browser what to do.<br /><span className="text-accent">It does it.</span>
            </h1>
            <p className="mt-6 text-sub text-muted max-w-xl leading-7">
              GlitchAgent turns an English sentence into a plan of clicks, keystrokes and page loads,
              runs it in a real Chromium browser, and hands back a screenshot of the result.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Cta onStart={onStart}>Try a command <ArrowRight size={16} /></Cta>
              <Cta ghost onStart={undefined}>View source</Cta>
            </div>
            <p className="mt-6 text-small text-dim">Free, open-source beta · no scripts to write</p>
          </div>
          <DemoConsole />
        </section>

        <section aria-label="Supported actions" className="border-y border-line bg-surface">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 py-6 flex flex-wrap items-center gap-x-6 gap-y-2 font-mono text-small">
            <span className="text-dim">speaks</span>
            {VOCAB.map(v => <span key={v} className="text-muted">{v}</span>)}
          </div>
        </section>

        <section id="features" className="mx-auto max-w-6xl px-4 sm:px-6 py-24">
          <Eyebrow>What you get</Eyebrow>
          <h2 className="font-display text-h2 md:text-h1 font-semibold max-w-2xl">Automation you can read, check and trust.</h2>
          <div className="mt-12 grid sm:grid-cols-2 lg:grid-cols-3 gap-px rounded-2xl overflow-hidden border border-line bg-line">
            {FEATURES.map(([Icon, title, body]) => (
              <div key={title} className="bg-surface p-8">
                <Icon size={20} className="text-accent" />
                <h3 className="mt-4 font-semibold">{title}</h3>
                <p className="mt-2 text-body text-muted">{body}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="how" className="border-t border-line bg-surface">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 py-24">
            <Eyebrow>How it works</Eyebrow>
            <h2 className="font-display text-h2 md:text-h1 font-semibold">Three steps, one sentence.</h2>
            <ol className="mt-12 grid md:grid-cols-3 gap-8">
              {STEPS.map(([n, title, body]) => (
                <li key={n} className="border-t-2 border-accent pt-6">
                  <span className="font-mono text-small text-accent">{n}</span>
                  <h3 className="mt-2 font-display text-sub font-semibold">{title}</h3>
                  <p className="mt-2 text-muted leading-7">{body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section id="faq" className="mx-auto max-w-3xl px-4 sm:px-6 py-24">
          <Eyebrow>FAQ</Eyebrow>
          <h2 className="font-display text-h2 md:text-h1 font-semibold">Questions, answered.</h2>
          <div className="mt-12 divide-y divide-line border-y border-line">
            {FAQS.map(([q, a], i) => (
              <div key={q}>
                <button onClick={() => setOpen(open === i ? null : i)} aria-expanded={open === i}
                  className="w-full flex items-center justify-between gap-4 py-6 text-left font-medium cursor-pointer">
                  {q}<ChevronDown size={18} className={`shrink-0 text-dim transition-transform ${open === i ? 'rotate-180' : ''}`} />
                </button>
                {open === i && <p className="pb-6 -mt-1 text-muted leading-7">{a}</p>}
              </div>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 sm:px-6 pb-24">
          <div className="rounded-2xl border border-line bg-surface px-6 py-16 text-center">
            <h2 className="font-display text-h2 md:text-h1 font-semibold">Stop writing selectors.</h2>
            <p className="mt-4 text-muted">Describe the task. Get the screenshot.</p>
            <div className="mt-8"><Cta onStart={onStart}>Open the console <ArrowRight size={16} /></Cta></div>
          </div>
        </section>
      </main>

      <footer className="border-t border-line">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-12 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between text-small text-dim">
          <Logo size={22} />
          <div className="flex gap-6">
            <a href={REPO} className="hover:text-fg">Source code</a>
            <a href="https://www.paritosh.online/" className="hover:text-fg">Built by Paritosh</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
