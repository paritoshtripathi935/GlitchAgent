import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useApi } from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { ErrorNote } from '../components/RunResult';
import type { HistoryItem } from '../types';

const PAGE = 20;

function duration(h: HistoryItem) {
  if (!h.completed_at) return '—';
  const s = (new Date(h.completed_at).getTime() - new Date(h.created_at).getTime()) / 1000;
  return s < 60 ? `${s.toFixed(1)}s` : `${Math.round(s / 60)}m`;
}

export default function HistoryPage() {
  const api = useApi();
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [more, setMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (skip: number) => {
    setLoading(true); setError(null);
    try {
      const page = await api.getHistory(skip, PAGE);
      setItems(prev => (skip === 0 ? page : [...prev, ...page]));
      setMore(page.length === PAGE);
    } catch (e) { setError((e as Error).message); }
    finally { setLoading(false); }
  }, [api]);

  useEffect(() => { load(0); }, [load]);

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-8 py-12 md:py-16">
      <h1 className="font-display text-h2 font-semibold">History</h1>
      <p className="mt-2 text-muted">Every command you've run, newest first.</p>

      {error && <div className="mt-8"><ErrorNote message={error} /></div>}

      {!loading && !error && items.length === 0 && (
        <div className="mt-12 rounded-xl border border-dashed border-line p-12 text-center">
          <p className="text-muted">No runs yet.</p>
          <Link to="/" className="mt-2 inline-block py-3 text-small text-accent hover:underline">Run your first command</Link>
        </div>
      )}

      {items.length > 0 && (
        <ul className="mt-8 rounded-xl border border-line bg-surface divide-y divide-line overflow-hidden">
          {items.map(h => (
            <li key={h.request_id}>
              <Link to={`/runs/${h.request_id}`} className="grid grid-cols-[72px_1fr] sm:grid-cols-[88px_1fr_150px_56px] items-center gap-x-4 gap-y-1 px-4 py-4 hover:bg-hover transition-colors">
                <StatusBadge status={h.status} />
                <span className="font-mono text-small truncate">{h.command || <em className="text-dim">(no command text)</em>}</span>
                <span className="col-start-2 sm:col-start-auto text-caption text-dim">{new Date(h.created_at).toLocaleString()}</span>
                <span className="hidden sm:block text-caption text-dim text-right">{duration(h)}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}

      {loading && <p className="mt-6 flex items-center gap-2 text-small text-dim"><Loader2 size={15} className="animate-spin" /> Loading…</p>}
      {more && !loading && (
        <button onClick={() => load(items.length)} className="mt-6 rounded-lg border border-line px-4 h-9 pointer-coarse:h-11 text-small hover:bg-hover cursor-pointer">Load more</button>
      )}
    </div>
  );
}
