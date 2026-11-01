import type { RunStatus } from '../types';

const STYLE: Record<RunStatus, [string, string]> = {
  pending: ['Queued', 'text-warn'],
  running: ['Running', 'text-warn'],
  completed: ['Done', 'text-accent'],
  failed: ['Failed', 'text-danger'],
};

export default function StatusBadge({ status }: { status: RunStatus }) {
  const [label, color] = STYLE[status] ?? STYLE.failed;
  const live = status === 'pending' || status === 'running';
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${color}`}>
      <span className={`h-1.5 w-1.5 rounded-full bg-current ${live ? 'animate-pulse' : ''}`} />
      {label}
    </span>
  );
}
