import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { useAegisStore } from '../../store/useAegisStore';
import { useMemo } from 'react';

export function AttackTypeDistribution() {
    const { events } = useAegisStore();

    const data = useMemo(() => {
        const attacks = events.filter(e => e.prediction === 'ATTACK');
        if (attacks.length === 0) return [{ name: "No Attacks", value: 1, color: "#1a1d27" }];

        const counts: Record<string, number> = {};
        attacks.forEach(a => {
            counts[a.attack_type] = (counts[a.attack_type] || 0) + 1;
        });

        const colors = ["#ff3a3a", "#ffaa00", "#ff00dd", "#4da6ff", "#ffffff"];
        return Object.entries(counts).map(([name, value], i) => ({
            name,
            value,
            color: colors[i % colors.length]
        })).sort((a, b) => b.value - a.value).slice(0, 5);
    }, [events]);

    return (
        <div className="bg-bg-surface border border-bg-border rounded-lg p-4 flex flex-col h-full min-h-[250px]">
            <div className="text-text-secondary text-sm font-semibold tracking-wide uppercase mb-2">
                Attack Vector Distribution
            </div>
            <div className="flex-1 w-full min-h-0 relative flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            innerRadius={40}
                            outerRadius={70}
                            paddingAngle={5}
                            dataKey="value"
                            stroke="none"
                            isAnimationActive={true}
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Pie>
                        <Tooltip
                            contentStyle={{ backgroundColor: '#0a0b0f', borderColor: '#1a1d27', fontFamily: 'IBM Plex Mono', fontSize: '12px' }}
                            itemStyle={{ color: '#e8eaf2' }}
                        />
                    </PieChart>
                </ResponsiveContainer>
                {data.length > 0 && data[0].name !== "No Attacks" && (
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
                        <div className="font-mono text-xl text-text-primary">{data[0].value}</div>
                    </div>
                )}
            </div>
            <div className="mt-4 space-y-2">
                {data.map((d, i) => (
                    <div key={i} className="flex items-center justify-between text-xs font-mono">
                        <div className="flex items-center space-x-2">
                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
                            <span className="text-text-secondary truncate w-24">{d.name}</span>
                        </div>
                        <span className="text-text-primary">{d.value}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
