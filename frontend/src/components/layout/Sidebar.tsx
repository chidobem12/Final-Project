import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Shield, Activity, Map, BarChart2, Settings } from 'lucide-react';
import { useAegisStore } from '../../store/useAegisStore';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

export function Sidebar() {
    const { wsConnected, events, simulationPaused } = useAegisStore();
    const [expanded] = useState(true);

    const navItems = [
        { name: 'Dashboard', path: '/', icon: <Shield size={20} /> },
        { name: 'Feed', path: '/feed', icon: <Activity size={20} /> },
        { name: 'Map', path: '/map', icon: <Map size={20} /> },
        { name: 'Analytics', path: '/analytics', icon: <BarChart2 size={20} /> },
        { name: 'Settings', path: '/settings', icon: <Settings size={20} /> },
    ];

    return (
        <div className={twMerge('flex flex-col h-screen border-r border-bg-border bg-bg-surface transition-all duration-300', expanded ? 'w-[220px]' : 'w-[64px]')}>
            <div className="flex items-center h-12 px-4 border-b border-bg-border">
                {expanded ? (
                    <div className="font-display font-bold text-accent-primary tracking-widest text-lg flex items-center space-x-2">
                        <span className="w-2 h-2 rounded-full bg-accent-primary animate-pulse" />
                        <span>AEGIS</span>
                    </div>
                ) : (
                    <div className="w-2 h-2 rounded-full bg-accent-primary animate-pulse mx-auto" />
                )}
            </div>

            <nav className="flex-1 py-4 space-y-1 px-2">
                {navItems.map((item) => (
                    <NavLink
                        key={item.name}
                        to={item.path}
                        className={({ isActive }) => clsx(
                            "flex items-center px-3 py-2 rounded-md transition-colors",
                            isActive ? "bg-bg-raised text-accent-primary" : "text-text-secondary hover:text-text-primary hover:bg-bg-raised"
                        )}
                    >
                        <div className="flex-shrink-0">{item.icon}</div>
                        {expanded && <span className="ml-3 text-sm font-medium">{item.name}</span>}
                    </NavLink>
                ))}
            </nav>

            {expanded && (
                <div className="p-4 border-t border-bg-border text-xs text-text-secondary font-mono">
                    <div className="flex items-center space-x-2 mb-2">
                        <div className={clsx('w-2 h-2 rounded-full', wsConnected ? 'bg-accent-primary' : 'bg-accent-warning animate-pulse')} />
                        <span>{wsConnected ? 'Connected' : 'Reconnecting'}</span>
                    </div>
                    <div className="flex items-center space-x-2 mb-2">
                        <div className="w-2 h-2 rounded-sm bg-accent-dim" />
                        <span>Simulation: {simulationPaused ? 'PAUSED' : 'ON'}</span>
                    </div>
                    <div className="h-px w-full bg-bg-border my-2" />
                    <div className="flex justify-between mb-1">
                        <span>Events:</span>
                        <span className="text-accent-primary">{events.length.toLocaleString()}</span>
                    </div>
                    <div className="h-px w-full bg-bg-border my-2" />
                    <div className="mt-2 opacity-50 text-[10px]">v1.0.0 • AEGIS</div>
                </div>
            )}
        </div>
    );
}
