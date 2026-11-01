import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { UserButton } from '@clerk/clerk-react';
import { History, Square, Terminal } from 'lucide-react';
import Logo from './Logo';
import ThemeToggle from './ThemeToggle';
import { useApi } from '../services/api';

const NAV = [
  { to: '/', label: 'Console', icon: Terminal, end: true },
  { to: '/history', label: 'History', icon: History, end: false },
];

export default function AppLayout() {
  const api = useApi();
  const [stopMsg, setStopMsg] = useState<string | null>(null);

  async function stop() {
    setStopMsg('Stopping…');
    try { setStopMsg((await api.stopBrowser()).message); }
    catch (e) { setStopMsg((e as Error).message); }
    window.setTimeout(() => setStopMsg(null), 4000);
  }

  const link = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 rounded-lg px-3 h-9 pointer-coarse:h-11 text-small transition-colors ${isActive ? 'bg-hover text-fg font-medium' : 'text-muted hover:text-fg hover:bg-hover'}`;

  return (
    <div className="min-h-screen md:grid md:grid-cols-[232px_1fr]">
      <aside className="md:sticky md:top-0 md:h-screen flex md:flex-col items-center md:items-stretch gap-2 border-b md:border-b-0 md:border-r border-line bg-surface px-3 py-3 md:py-6">
        <div className="px-2 md:mb-6"><Logo size={26} compact /></div>
        <nav className="flex md:flex-col gap-1 flex-1">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={link}>
              <Icon size={16} /><span className="hidden sm:inline">{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="flex md:flex-col gap-2 md:gap-3">
          <button onClick={stop} title="Close every browser the agent has open"
            className="flex items-center gap-3 rounded-lg px-3 h-9 pointer-coarse:h-11 text-small text-muted hover:text-danger hover:bg-hover cursor-pointer">
            <Square size={14} /><span className="hidden md:inline">Stop browsers</span>
          </button>
          {stopMsg && <p role="status" className="hidden md:block px-3 text-caption text-dim">{stopMsg}</p>}
          <div className="flex items-center justify-between md:px-2 md:pt-3 md:border-t border-line gap-2">
            <UserButton />
            <ThemeToggle />
          </div>
        </div>
      </aside>
      <main className="min-w-0"><Outlet /></main>
    </div>
  );
}
