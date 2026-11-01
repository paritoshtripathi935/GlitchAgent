/**
 *   /              Console — type a command, watch the run
 *   /history       Past runs
 *   /runs/:id      One run's result + screenshot
 */
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from './components/AppLayout';
import ConsolePage from './pages/ConsolePage';
import HistoryPage from './pages/HistoryPage';
import RunPage from './pages/RunPage';

export default function AuthedApp() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<ConsolePage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="runs/:runId" element={<RunPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
