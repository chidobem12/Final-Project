import { useState, useEffect } from 'react';
import { useAegisStore } from '../../store/useAegisStore';
import clsx from 'clsx';
import { format } from 'date-fns';
import { apiFetch } from '../../lib/api';

export function TopBar() {
    const { wsConnected, wsReconnectAttempt, eventsPerMinute, threatLevel, threatRatePercent, reconnectRecoveredAt, user, clearAuth } = useAegisStore();
    const [time, setTime] = useState<Date>(new Date());
    const [tick, setTick] = useState(0);

    useEffect(() => {
        const int = setInterval(() => setTime(new Date()), 50);
        return () => clearInterval(int);
    }, []);

    useEffect(() => {
        const int = setInterval(() => setTick((prev) => prev + 1), 1000);
        return () => clearInterval(int);
    }, []);

    const levelStyles: Record<typeof threatLevel, { text: string; tint: string; pulse: boolean }> = {
        NOMINAL: { text: 'text-accent-primary', tint: 'bg-transparent', pulse: false },
        ELEVATED: { text: 'text-accent-warning', tint: 'bg-accent-warning/10', pulse: false },
        HIGH: { text: 'text-accent-high', tint: 'bg-accent-high/10', pulse: false },
        CRITICAL: { text: 'text-accent-threat', tint: 'bg-accent-threat/10', pulse: true },
    };

    const recoveredRecently = reconnectRecoveredAt ? Date.now() - reconnectRecoveredAt < 2000 : false;

    const onLogout = async () => {
        try {
            await apiFetch('/api/auth/logout', { method: 'POST' });
        } catch {
            // Ignore and clear local session regardless.
        }
        clearAuth();
        window.location.href = '/login';
    };

    return (
        <div className={clsx('border-b border-bg-border select-none transition-colors', levelStyles[threatLevel].tint, levelStyles[threatLevel].pulse && 'animate-threat-pulse', recoveredRecently && 'bg-accent-primary/10')}>
            <div className={clsx('h-12 bg-bg-surface/90 flex items-center px-4 justify-between', threatLevel === 'CRITICAL' && 'border-b border-accent-threat/70')}>
                <div className="font-display font-bold text-text-primary text-sm tracking-wider">
                    AEGIS CYBERSECURITY PLATFORM
                </div>

                <div className="flex items-center space-x-6 font-mono text-xs">
                    <div className="text-text-secondary">
                        [time: <span className="text-text-primary">{format(time, 'HH:mm:ss.SSS')}</span>]
                    </div>

                    <div className={clsx('flex items-center space-x-2 px-2 py-1 rounded border', wsConnected ? 'border-accent-primary/50 text-accent-primary bg-accent-primary/10' : 'border-accent-warning/50 text-accent-warning bg-accent-warning/10')}>
                        <div className={clsx('w-2 h-2 rounded-full', wsConnected ? 'bg-accent-primary' : 'bg-accent-warning animate-pulse')} />
                        <span>{wsConnected ? 'LIVE' : 'RECONNECTING'}</span>
                    </div>

                    <div className="flex items-center space-x-2 text-text-secondary">
                        <span>[⚡</span>
                        <span className="text-text-primary w-16 text-right">{eventsPerMinute} ev/m</span>
                        <span>]</span>
                    </div>

                    <div className={clsx('flex items-center px-3 py-1 border rounded font-bold tracking-widest uppercase transition-all duration-300', levelStyles[threatLevel].text, threatLevel === 'NOMINAL' ? 'border-accent-primary/40' : 'border-current')}>
                        [THREAT LEVEL: {threatLevel} {threatRatePercent.toFixed(1)}%]
                    </div>

                    {user && (
                        <div className="flex items-center gap-3">
                            <span className="text-text-secondary">{user.name}</span>
                            <button onClick={onLogout} className="border border-bg-border px-2 py-1 rounded text-text-secondary hover:text-text-primary">
                                LOGOUT
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {!wsConnected && (
                <div className="h-7 bg-accent-warning/15 text-accent-warning font-mono text-xs flex items-center px-4">
                    ⚠ Connection interrupted — attempting reconnect (attempt {Math.min(wsReconnectAttempt, 5)}/5)
                </div>
            )}
            {!wsConnected && tick > -1 && null}
            {recoveredRecently && wsConnected && (
                <div className="h-1 bg-accent-primary/50" />
            )}
            <div className="hidden">{tick}</div>
        </div>
    );
}
