import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import Dashboard from './pages/Dashboard';
import ThreatFeed from './pages/ThreatFeed';
import ThreatMap from './pages/ThreatMap';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import LoginPage from './pages/Login';
import { ProtectedRoute } from './components/shared/ProtectedRoute';
import { AppLayout } from './components/layout/AppLayout';
import { Toaster } from 'react-hot-toast';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/feed" element={<ThreatFeed />} />
            <Route path="/map" element={<ThreatMap />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#0a0b0f',
            color: '#e8eaf2',
            border: '1px solid #1a1d27',
            fontFamily: 'IBM Plex Mono',
            fontSize: '12px',
          },
        }}
      />
    </BrowserRouter>
  );
}
