import { useEffect, useState } from 'react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

interface MetricCardProps {
    title: string;
    value: number | string;
    subtitle?: string;
    trend?: 'up' | 'down' | 'neutral';
    trendValue?: string;
    type?: 'default' | 'threat' | 'warning' | 'primary';
    className?: string;
}

export function MetricCard({ title, value, subtitle, trend, trendValue, type = 'default', className }: MetricCardProps) {
    const [displayValue, setDisplayValue] = useState(value);

    // Simple number animation
    useEffect(() => {
        if (typeof value === 'number' && typeof displayValue === 'number') {
            const step = (value - displayValue) / 10;
            if (Math.abs(step) < 0.1) {
                setDisplayValue(value);
                return;
            }
            const int = setInterval(() => {
                setDisplayValue(prev => {
                    const next = Number(prev) + step;
                    if ((step > 0 && next >= value) || (step < 0 && next <= value)) {
                        clearInterval(int);
                        return value;
                    }
                    return next;
                });
            }, 30);
            return () => clearInterval(int);
        } else {
            setDisplayValue(value);
        }
    }, [value]);

    const formatting = {
        default: "text-text-primary",
        threat: "text-accent-threat",
        warning: "text-accent-warning",
        primary: "text-accent-primary"
    };

    return (
        <div className={twMerge("p-4 bg-bg-surface border border-bg-border rounded-lg flex flex-col justify-between", className)}>
            <div className="text-text-secondary text-sm font-semibold tracking-wide uppercase mb-2">
                {title}
            </div>
            <div className="flex items-end justify-between">
                <div className={clsx("font-mono text-3xl font-bold", formatting[type])}>
                    {typeof displayValue === 'number' ? displayValue.toFixed(title.includes('%') ? 1 : 0) : displayValue}
                </div>
                {trend && (
                    <div className={clsx(
                        "text-xs font-mono flex items-center space-x-1",
                        trend === 'up' && type === 'threat' ? 'text-accent-threat' :
                            trend === 'down' ? 'text-accent-primary' : 'text-text-secondary'
                    )}>
                        <span>{trend === 'up' ? '↗' : trend === 'down' ? '↘' : '→'}</span>
                        <span>{trendValue}</span>
                    </div>
                )}
            </div>
            {subtitle && (
                <div className="text-text-secondary text-xs mt-2 opacity-70">
                    {subtitle}
                </div>
            )}
        </div>
    );
}
