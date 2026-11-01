/**
 * API client. Every call attaches Clerk's session JWT as a Bearer token so
 * the backend can verify the caller once auth is enforced server-side.
 */
import { useCallback, useEffect, useMemo, useRef } from 'react';
import { useAuth } from '@clerk/clerk-react';
import type { CommandResponse, ExecutionResult, HistoryItem } from '../types';

export const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function useApi() {
  const { getToken } = useAuth();
  // Clerk may hand back a new getToken each render; a ref keeps the client
  // (and every effect that depends on it) stable.
  const tokenRef = useRef(getToken);
  useEffect(() => { tokenRef.current = getToken; }, [getToken]);

  const request = useCallback(async <T,>(path: string, init: RequestInit = {}): Promise<T> => {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    try {
      const token = await tokenRef.current();
      if (token) headers.Authorization = `Bearer ${token}`;
    } catch { /* backend answers 401 if it needs the token */ }

    let res: Response;
    try {
      res = await fetch(`${API_URL}${path}`, { ...init, headers: { ...headers, ...init.headers } });
    } catch {
      throw new ApiError(0, `Can't reach the GlitchAgent API at ${API_URL}. Is the backend running?`);
    }
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      throw new ApiError(res.status, body?.detail ?? `Request failed (${res.status})`);
    }
    return res.json() as Promise<T>;
  }, []);

  return useMemo(() => ({
    runCommand: (command: string, context?: string) =>
      request<CommandResponse>('/v1/glitch-agent/command', {
        method: 'POST',
        body: JSON.stringify({ command, context: context || null }),
      }),
    getExecution: (id: string) => request<ExecutionResult>(`/v1/glitch-agent/execution/${encodeURIComponent(id)}`),
    getHistory: (skip = 0, limit = 20) => request<HistoryItem[]>(`/v1/glitch-agent/history?skip=${skip}&limit=${limit}`),
    stopBrowser: () => request<{ message: string }>('/v1/glitch-agent/stop-browser', { method: 'POST' }),
  }), [request]);
}
