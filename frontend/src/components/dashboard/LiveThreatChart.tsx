import { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useAegisStore } from '../../store/useAegisStore';
import { format } from 'date-fns';

export function LiveThreatChart() {
    const { events, wsConnected, lastEventTime } = useAegisStore();
    const [data, setData] = useState<{ time: string; normal: number; threat: number }[]>([]);
    const [secondsAgo, setSecondsAgo] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            if (!lastEventTime) return;
            setSecondsAgo(Math.floor((Date.now() - lastEventTime) / 1000));
        }, 1000);
        return () => clearInterval(interval);
    }, [lastEventTime]);

    useEffect(() => {
        // Generate buckets for last 60 seconds
        const now = Date.now();
        const buckets = new Map();

        for (let i = 0; i < 60; i++) {
            const timeKey = format(new Date(now - i * 1000), 'HH:mm:ss');
            buckets.set(timeKey, { time: timeKey, normal: 0, threat: 0 });
        }

        events.forEach(e => {
            const eventTime = new Date(e.timestamp).getTime();
            if (now - eventTime < 60000) {
                const timeKey = format(new Date(e.timestamp), 'HH:mm:ss');
                if (buckets.has(timeKey)) {
                    const b = buckets.get(timeKey);
                    if (e.prediction === 'ATTACK') b.threat += 1;
                    else b.normal += 1;
                }
            }
        });

        const arr = Array.from(buckets.values()).reverse();
        setData(arr);
    }, [events]);

    return (
        <div className="h-64 w-full bg-bg-surface border border-bg-border rounded-lg p-4 flex flex-col">
            <div className="text-text-secondary text-sm font-semibold tracking-wide uppercase mb-4 flex items-center justify-between">
                <span>Live Traffic Analysis (60s Rolling)</span>
                <span className="text-[10px] font-mono">{wsConnected ? 'Connected' : `Last updated ${secondsAgo}s ago`}</span>
            </div>
            <div className="flex-1 w-full min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorNormal" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#00ff88" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#00ff88" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorThreat" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#ff3a3a" stopOpacity={0.5} />
                                <stop offset="95%" stopColor="#ff3a3a" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <XAxis dataKey="time" stroke="#1a1d27" tick={{ fill: '#6b7280', fontSize: 10, fontFamily: 'IBM Plex Mono' }} tickFormatter={(val) => val.substring(3)} />
                        <YAxis stroke="#1a1d27" tick={{ fill: '#6b7280', fontSize: 10, fontFamily: 'IBM Plex Mono' }} />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#0a0b0f', borderColor: '#1a1d27', fontFamily: 'IBM Plex Mono' }}
                            itemStyle={{ color: '#e8eaf2' }}
                            labelStyle={{ color: '#00ff88' }}
                        />
                        <Area type="stepBefore" dataKey="normal" stroke="#00ff88" fillOpacity={1} fill="url(#colorNormal)" isAnimationActive={false} />
                        <Area type="stepBefore" dataKey="threat" stroke="#ff3a3a" fillOpacity={1} fill="url(#colorThreat)" isAnimationActive={false} />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
