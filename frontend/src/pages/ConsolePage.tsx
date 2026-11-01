import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { ArrowUpRight, CornerDownLeft, Loader2 } from 'lucide-react';
import { useApi } from '../services/api';
import { useExecution } from '../hooks/useExecution';
import ActionList from '../components/ActionList';
import RunResult, { ErrorNote } from '../components/RunResult';
import type { CommandResponse } from '../types';

const EXAMPLES = [
  'Go to news.ycombinator.com and open the top story',
  'Search Wikipedia for "Playwright (software)"',
  'Open github.com/trending and switch to Python',
];

export default function ConsolePage() {
  const api = useApi();
  const [command, setCommand] = useState('');
  const [context, setContext] = useState('');
  const [showContext, setShowContext] = useState(false);
  const [planning, setPlanning] = useState(false);
  const [plan, setPlan] = useState<CommandResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const run = useExecution(plan?.request_id);

  async function submit(e?: FormEvent) {
    e?.preventDefault();
    if (!command.trim() || planning) return;
    setPlanning(true); setError(null); setPlan(null);
    try { setPlan(await api.runCommand(command.trim(), context.trim())); }
    catch (err) { setError((err as Error).message); }
    finally { setPlanning(false); }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-8 py-10 md:py-16">
      <h1 className="font-display text-3xl font-semibold tracking-tight">What should the browser do?</h1>
      <p className="mt-2 text-muted">Describe the task in plain English. You'll see the plan before the result.</p>

      <form onSubmit={submit} className="mt-8 rounded-xl border border-line bg-surface focus-within:border-accent transition-colors">
        <label htmlFor="cmd" className="sr-only">Command</label>
        <textarea id="cmd" value={command} onChange={e => setCommand(e.target.value)} rows={3} autoFocus
          onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit(); }}
          placeholder='e.g. Open github.com and search for "playwright python"'
          className="w-full resize-none bg-transparent px-4 pt-4 pb-2 font-mono text-[14px] outline-none placeholder:text-dim" />
        {showContext && (
          <div className="px-4 pb-2">
            <label htmlFor="ctx" className="text-xs text-dim">Extra context (optional)</label>
            <input id="ctx" value={context} onChange={e => setContext(e.target.value)}
              placeholder="e.g. I'm already logged in; prefer the first result"
              className="mt-1 w-full rounded-md bg-raised border border-line px-3 h-9 text-sm outline-none focus:border-accent" />
          </div>
        )}
        <div className="flex items-center justify-between gap-3 border-t border-line px-3 py-2">
          <button type="button" onClick={() => setShowContext(s => !s)} className="text-xs text-dim hover:text-fg px-1 cursor-pointer">
            {showContext ? 'Hide context' : '+ Add context'}
          </button>
          <button type="submit" disabled={!command.trim() || planning}
            className="inline-flex items-center gap-2 rounded-lg bg-accent text-ink px-4 h-9 text-sm font-semibold disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed">
            {planning ? <><Loader2 size={15} className="animate-spin" /> Planning</> : <>Run <CornerDownLeft size={14} /></>}
          </button>
        </div>
      </form>
      <p className="mt-2 text-xs text-dim">⌘/Ctrl + Enter to run · commands are saved to history, so keep passwords out of them.</p>

      {!plan && !planning && !error && (
        <div className="mt-10">
          <p className="text-xs uppercase tracking-[0.15em] text-dim font-mono">Try one</p>
          <div className="mt-3 flex flex-col gap-2">
            {EXAMPLES.map(ex => (
              <button key={ex} onClick={() => setCommand(ex)}
                className="text-left rounded-lg border border-line px-4 py-3 text-sm text-muted hover:text-fg hover:bg-hover transition-colors cursor-pointer">
                {ex}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && <div className="mt-8"><ErrorNote message={error} /></div>}

      {plan && (
        <div className="mt-10 space-y-8">
          <section>
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold">Plan · {plan.actions.length} steps</h2>
              <Link to={`/runs/${plan.request_id}`} className="inline-flex items-center gap-1 text-xs text-dim hover:text-fg">
                Run page <ArrowUpRight size={13} />
              </Link>
            </div>
            <div className="mt-3 rounded-xl border border-line bg-surface overflow-hidden">
              <ActionList actions={plan.actions} />
            </div>
          </section>
          <section>
            <h2 className="text-sm font-semibold mb-3">Result</h2>
            <RunResult {...run} />
          </section>
        </div>
      )}
    </div>
  );
}
