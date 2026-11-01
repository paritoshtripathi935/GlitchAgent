export type ActionType =
  | 'navigate' | 'click' | 'fill' | 'wait' | 'submit' | 'press'
  | 'select' | 'hover' | 'screenshot' | 'extract';

export interface BrowserAction {
  action: ActionType;
  locator?: string | null;
  url?: string | null;
  text?: string | null;
  time_ms?: number | null;
  key?: string | null;
  value?: string | null;
}

export interface CommandResponse {
  request_id: string;
  actions: BrowserAction[];
  status: string;
  message?: string | null;
  created_at: string;
}

export type RunStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface ExecutionResult {
  request_id: string;
  success: boolean;
  status: RunStatus;
  message: string;
  screenshot?: string | null;
  extracted_data?: Record<string, unknown> | null;
  error?: string | null;
  completed_at: string;
}

export interface HistoryItem {
  request_id: string;
  command: string;
  success: boolean;
  status: RunStatus;
  created_at: string;
  completed_at?: string | null;
}
