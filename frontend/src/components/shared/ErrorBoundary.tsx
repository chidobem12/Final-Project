import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            return (
                <div className="flex flex-col items-center justify-center p-6 bg-bg-surface border border-accent-threat rounded-lg m-4 text-center">
                    <AlertTriangle className="w-12 h-12 text-accent-threat mb-4 mx-auto animate-pulse" />
                    <h2 className="text-xl font-display font-bold text-accent-threat mb-2">Component Crashed</h2>
                    <p className="text-sm font-mono text-text-secondary mb-4">
                        An unexpected error occurred in this subsystem.
                    </p>
                    <div className="bg-bg-void border border-bg-border p-4 rounded text-xs font-mono text-left w-full overflow-auto text-accent-threat">
                        {this.state.error?.message || "Unknown error"}
                    </div>
                    <button
                        className="mt-4 px-4 py-2 bg-bg-raised border border-bg-border hover:text-accent-primary transition-colors text-sm font-mono rounded"
                        onClick={() => this.setState({ hasError: false })}
                    >
                        Attempt Recovery
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}
