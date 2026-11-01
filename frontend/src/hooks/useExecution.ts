import { useEffect, useState } from 'react';
import { useApi } from '../services/api';
import type { ExecutionResult } from '../types';

const POLL_MS = 2000;

/** Polls a run until it leaves the running state. */
export function useExecution(runId: string | undefined) {
  const api = useApi();
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) return;
    let cancelled = false;
    let timer: number | undefined;
    setResult(null);
    setError(null);
    const tick = async () => {
      try {
        const r = await api.getExecution(runId);
        if (cancelled) return;
        setResult(r);
        if (r.status === 'running' || r.status === 'pending') timer = window.setTimeout(tick, POLL_MS);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      }
    };
    tick();
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [runId, api]);

  return { result, error };
}
