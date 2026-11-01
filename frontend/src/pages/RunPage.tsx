import { Link, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useExecution } from '../hooks/useExecution';
import RunResult from '../components/RunResult';

export default function RunPage() {
  const { runId } = useParams();
  const run = useExecution(runId);
  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-8 py-10 md:py-16">
      <Link to="/history" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-fg"><ArrowLeft size={15} /> History</Link>
      <h1 className="mt-4 font-display text-2xl font-semibold tracking-tight">Run</h1>
      <p className="mt-1 font-mono text-xs text-dim break-all">{runId}</p>
      <div className="mt-8"><RunResult {...run} /></div>
    </div>
  );
}
