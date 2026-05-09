import { Outlet } from 'react-router-dom';

import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { ErrorBoundary } from '../shared/ErrorBoundary';
import { useWebSocket } from '../../hooks/useWebSocket';

export function AppLayout() {
  useWebSocket();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg-void text-text-primary selection:bg-accent-primary/30">
      <Sidebar />
      <div className="flex-1 flex flex-col h-screen min-w-0 overflow-auto">
        <TopBar />
        <main className="flex-1 overflow-y-auto relative">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}