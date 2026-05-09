import { useEffect, useState } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { apiFetch } from '../../lib/api';
import { useAegisStore } from '../../store/useAegisStore';

interface MeResponse {
  name: string;
  email: string;
  role: string;
}

export function ProtectedRoute() {
  const location = useLocation();
  const { token, user, setAuth, clearAuth } = useAegisStore();
  const [checking, setChecking] = useState(true);
  const [expired, setExpired] = useState(false);

  useEffect(() => {
    let mounted = true;
    const validate = async () => {
      if (!token) {
        if (mounted) setChecking(false);
        return;
      }

      try {
        if (!user) {
          const me = await apiFetch<MeResponse>('/api/auth/me');
          if (mounted) setAuth(me, token);
        }
      } catch {
        if (mounted) {
          setExpired(true);
          clearAuth();
        }
      } finally {
        if (mounted) setChecking(false);
      }
    };

    validate();
    return () => {
      mounted = false;
    };
  }, [token, user, setAuth, clearAuth]);

  if (checking) {
    return <div className="h-screen w-screen bg-bg-void" />;
  }

  if (!token) {
    const query = expired ? '?reason=expired' : '';
    return <Navigate to={`/login${query}`} replace state={{ from: location }} />;
  }

  return <Outlet />;
}
