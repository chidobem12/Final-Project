import { useAegisStore } from '../../store/useAegisStore';
import clsx from 'clsx';
import { ShieldAlert, CheckCircle2 } from 'lucide-react';
import { useEffect, useState } from 'react';

export function ThreatStatusBanner() {
    const { events, threatRatePercent } = useAegisStore();
    const [activeThreat, setActiveThreat] = useState<string | null>(null);

    useEffect(() => {
        if (events.length > 0) {
            const recent = events[0];
            if (recent.prediction === 'ATTACK' && (Date.now() - new Date(recent.timestamp).getTime() < 5000)) {
                setActiveThreat(recent.attack_type);
            } else if (events.filter(e => e.prediction === 'ATTACK' && Date.now() - new Date(e.timestamp).getTime() < 10000).length === 0) {
                setActiveThreat(null);
            }
        }
    }, [events]);

    const isThreat = activeThreat !== null || threatRatePercent > 10;

    return (
        <div className={clsx(
            "w-full transition-all duration-500 rounded-lg border flex-shrink-0",
            isThreat ? "bg-accent-threat/10 border-accent-threat text-accent-threat animate-threat-pulse p-4" : "bg-bg-surface border-accent-primary/30 text-accent-primary p-3"
        )}>
            <div className="flex items-center space-x-4">
                {isThreat ? (
                    <ShieldAlert className="w-6 h-6 animate-pulse" />
                ) : (
                    <CheckCircle2 className="w-5 h-5" />
                )}
                <div className="flex-1">
                    <div className="font-display font-bold tracking-widest uppercase">
                        {isThreat ? `THREAT DETECTED: ${activeThreat || 'MULTIPLE VECTORS'}` : "ALL SYSTEMS NORMAL — 0 ACTIVE THREATS"}
                    </div>
                    {isThreat && (
                        <div className="text-xs font-mono mt-1 opacity-80">
                            Immediate analyst attention required. Auto-mitigation rules standing by.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}