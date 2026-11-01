import type { BrowserAction } from '../types';

/** The one-line, human-readable target of an action. */
export function actionTarget(a: BrowserAction): string {
  switch (a.action) {
    case 'navigate': return a.url ?? '';
    case 'fill': return `${a.locator ?? ''}  ←  "${a.text ?? ''}"`;
    case 'press': return `${a.key ?? ''}${a.locator ? ` on ${a.locator}` : ''}`;
    case 'select': return `${a.locator ?? ''}  ←  ${a.value ?? ''}`;
    case 'wait': return a.time_ms ? `${a.time_ms} ms` : a.locator ?? '';
    default: return a.locator ?? '';
  }
}

export default function ActionList({ actions, activeIndex }: { actions: BrowserAction[]; activeIndex?: number }) {
  return (
    <ol className="font-mono text-[13px] divide-y divide-line">
      {actions.map((a, i) => (
        <li key={i} className={`flex items-baseline gap-3 px-4 py-2.5 rise ${i === activeIndex ? 'bg-accent-soft' : ''}`}
          style={{ animationDelay: `${i * 60}ms` }}>
          <span className="text-dim w-5 shrink-0 text-right">{i + 1}</span>
          <span className="w-[86px] shrink-0 text-accent">{a.action}</span>
          <span className="text-fg/90 break-all">{actionTarget(a)}</span>
        </li>
      ))}
    </ol>
  );
}
