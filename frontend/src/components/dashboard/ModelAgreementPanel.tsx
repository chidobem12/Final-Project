import { formatPercent } from '../../lib/formatters';
import { useAegisStore } from '../../store/useAegisStore';

const bar = (value: number) => `${Math.max(4, Math.round(value * 100))}%`;

export function ModelAgreementPanel() {
  const { liveAccuracy } = useAegisStore();

  const rows = [
    { key: 'Logistic Regression', metric: liveAccuracy.logistic_regression },
    { key: 'Random Forest', metric: liveAccuracy.random_forest },
    { key: 'Gradient Boosting', metric: liveAccuracy.gradient_boosting },
  ];

  return (
    <div className="bg-bg-surface border border-bg-border rounded-lg p-4 flex flex-col h-full min-h-[250px]">
      <div className="text-text-secondary text-sm font-semibold tracking-wide uppercase mb-1">Model Live Performance</div>
      <div className="text-xs text-text-secondary font-mono mb-4">last 500 events</div>

      <div className="space-y-5">
        {rows.map((row) => (
          <div key={row.key} className="space-y-2">
            <div className="font-mono text-xs text-text-primary">{row.key}</div>
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="w-20 text-text-secondary">Accuracy</span>
              <div className="flex-1 h-2 bg-bg-raised rounded overflow-hidden">
                <div className="h-full bg-accent-primary" style={{ width: bar(row.metric.accuracy) }} />
              </div>
              <span className="text-text-primary w-12 text-right">{formatPercent(row.metric.accuracy)}</span>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="w-20 text-text-secondary">Miss Rate</span>
              <div className="flex-1 h-2 bg-bg-raised rounded overflow-hidden">
                <div className="h-full bg-accent-threat" style={{ width: bar(row.metric.missRate) }} />
              </div>
              <span className="text-text-primary w-12 text-right">{formatPercent(row.metric.missRate)}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-auto pt-4 border-t border-bg-border text-xs font-mono text-text-secondary">
        Agreement Rate: <span className="text-text-primary">{formatPercent(liveAccuracy.agreementRate)}</span>
      </div>
    </div>
  );
}
