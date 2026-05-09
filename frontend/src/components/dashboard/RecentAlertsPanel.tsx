import { useAegisStore } from '../../store/useAegisStore';
import clsx from 'clsx';
import { ShieldAlert, Activity } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { formatPercent, formatRelativeSeconds } from '../../lib/formatters';

export function RecentAlertsPanel() {
    const navigate = useNavigate();
    const { events, setSelectedEventId } = useAegisStore();
    const alerts = events.filter(e => e.prediction === 'ATTACK').slice(0, 8);

    const colors = {
        CRITICAL: "text-accent-threat bg-accent-threat/10 border-accent-threat/30",
        HIGH: "text-accent-warning bg-accent-warning/10 border-accent-warning/30",
        MEDIUM: "text-accent-info bg-accent-info/10 border-accent-info/30",
        LOW: "text-text-primary bg-bg-raised border-bg-border",
        NONE: "text-text-secondary bg-bg-void border-bg-border",
    };

    return (
        <div className="bg-bg-surface border border-bg-border rounded-lg p-4 flex flex-col h-full overflow-hidden min-h-[250px]">
            <div className="text-text-secondary text-sm font-semibold tracking-wide uppercase mb-4 flex items-center justify-between">
                <span>Recent Threats</span>
                <span className="text-accent-threat animate-pulse text-xs">{events.filter(e => e.prediction === 'ATTACK').length} Active</span>
            </div>
            <div className="flex-1 overflow-y-auto pr-2 space-y-2">
                {alerts.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center opacity-50">
                        <Activity className="w-8 h-8 mb-2" />
                        <span className="font-mono text-xs">No recent threats</span>
                    </div>
                ) : (
                    alerts.map(a => (
                        <button
                            key={a.event_id}
                            onClick={() => {
                                setSelectedEventId(a.event_id);
                                navigate('/feed');
                            }}
                            className={clsx('w-full text-left p-3 rounded border flex items-center space-x-3', colors[a.severity])}
                        >
                            <ShieldAlert className="w-4 h-4 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                                <div className="flex justify-between items-center mb-1">
                                    <span className="font-display font-bold text-sm tracking-wide truncate">{a.attack_type}</span>
                                    <span className="font-mono text-[10px] opacity-70">{formatRelativeSeconds(a.timestamp)}</span>
                                </div>
                                <div className="flex justify-between items-center font-mono text-[10px] opacity-90">
                                    <span className="truncate">{a.source_ip} → {a.destination_ip}:{a.destination_port}</span>
                                    <span className="font-bold border border-current px-1 rounded bg-black/20">{formatPercent(a.confidence)}</span>
                                </div>
                            </div>
                        </button>
                    ))
                )}
            </div>
        </div>
    );
}
