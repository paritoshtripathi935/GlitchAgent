import { AlertTriangle, Loader2 } from 'lucide-react';
import type { ExecutionResult } from '../types';
import StatusBadge from './StatusBadge';

export default function RunResult({ result, error }: { result: ExecutionResult | null; error: string | null }) {
  if (error) return <ErrorNote message={error} />;
  if (!result) return <p className="flex items-center gap-2 text-small text-dim"><Loader2 size={15} className="animate-spin" /> Checking run…</p>;
  const live = result.status === 'running' || result.status === 'pending';
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <StatusBadge status={result.status} />
        <span className="text-small text-muted">{result.message}</span>
      </div>
      {live && <p className="flex items-center gap-2 text-small text-dim"><Loader2 size={15} className="animate-spin" /> The browser is working. This page updates on its own.</p>}
      {result.error && <ErrorNote message={result.error} />}
      {result.screenshot ? (
        <figure className="rounded-xl border border-line overflow-hidden bg-raised">
          <img src={`data:image/png;base64,${result.screenshot}`} alt="Screenshot of the browser when the run finished" className="w-full" />
          <figcaption className="px-4 py-2 text-caption text-dim border-t border-line">Final page · {new Date(result.completed_at).toLocaleString()}</figcaption>
        </figure>
      ) : !live && (
        <p className="text-small text-dim">No screenshot kept for this run (screenshots live in server memory until it restarts).</p>
      )}
    </div>
  );
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <div role="alert" className="flex gap-3 rounded-lg border border-danger/40 bg-danger/10 px-4 py-3 text-small">
      <AlertTriangle size={16} className="text-danger shrink-0 mt-0.5" />
      <span className="break-words min-w-0">{message}</span>
    </div>
  );
}
