import { useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { apiFetch } from '../lib/api';
import { useAegisStore } from '../store/useAegisStore';

interface LoginResponse {
  token: string;
  user: { name: string; email: string; role: string };
}

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setAuth } = useAegisStore();

  const [email, setEmail] = useState('analyst@keystone.bank');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const reason = useMemo(() => new URLSearchParams(location.search).get('reason'), [location.search]);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await apiFetch<LoginResponse>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      setAuth(result.user, result.token);
      navigate('/');
    } catch {
      setError('Authentication failed — invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-screen bg-bg-void flex items-center justify-center">
      <div className="w-full max-w-md border border-bg-border bg-bg-surface rounded-lg p-8 shadow-lg">
        <div className="mb-8 text-center">
          <div className="font-display text-3xl tracking-widest text-accent-primary font-bold">AEGIS</div>
          <div className="font-mono text-xs text-text-secondary mt-2">Keystone Bank Security Operations</div>
          {reason === 'expired' && <div className="font-mono text-xs text-accent-warning mt-3">Session expired. Authenticate again.</div>}
        </div>

        <form className="space-y-4" onSubmit={onSubmit}>
          <input
            className="w-full bg-bg-raised border border-bg-border rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-primary"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            placeholder="email"
            autoComplete="username"
            required
          />
          <input
            className="w-full bg-bg-raised border border-bg-border rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-primary"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            placeholder="password"
            autoComplete="current-password"
            required
          />

          <button
            disabled={loading}
            type="submit"
            className="w-full bg-accent-primary text-bg-void py-2 rounded font-display font-bold tracking-widest disabled:opacity-60"
          >
            {loading ? 'AUTHENTICATING...' : 'AUTHENTICATE'}
          </button>

          {error && <div className="text-accent-threat text-xs font-mono text-center">{error}</div>}
        </form>
      </div>
    </div>
  );
}
