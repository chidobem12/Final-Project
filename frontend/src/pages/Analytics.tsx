import { useEffect, useMemo, useState } from 'react';
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { apiFetch } from '../lib/api';
import { formatPercent } from '../lib/formatters';
import { ModelAgreementPanel } from '../components/dashboard/ModelAgreementPanel';
import { useAegisStore } from '../store/useAegisStore';

type ModelKey = 'logistic_regression' | 'random_forest' | 'gradient_boosting';

interface TrainingMetric {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
}

interface MetricsPayload {
  training_metrics?: Record<ModelKey, TrainingMetric>;
}

const modelColors: Record<ModelKey, string> = {
  logistic_regression: '#4da6ff',
  random_forest: '#00ff88',
  gradient_boosting: '#ffaa00',
};

export default function Analytics() {
  const { liveAccuracy, metricsHistory } = useAegisStore();
  const [trainingMetrics, setTrainingMetrics] = useState<Record<ModelKey, TrainingMetric> | null>(null);

  useEffect(() => {
    const run = async () => {
      try {
        const metrics = await apiFetch<MetricsPayload>('/api/metrics');
        if (metrics.training_metrics) {
          setTrainingMetrics(metrics.training_metrics);
        }
      } catch {
        // Keep analytics page usable when backend auth/session is unavailable.
      }
    };
    run();
  }, []);

  const chartData = useMemo(
    () =>
      metricsHistory.map((entry) => ({
        ts: new Date(entry.ts).toLocaleTimeString(),
        lrAcc: entry.accuracy.logistic_regression,
        rfAcc: entry.accuracy.random_forest,
        gbAcc: entry.accuracy.gradient_boosting,
        lrFnr: entry.fnr.logistic_regression,
        rfFnr: entry.fnr.random_forest,
        gbFnr: entry.fnr.gradient_boosting,
        lrFpr: entry.fpr.logistic_regression,
        rfFpr: entry.fpr.random_forest,
        gbFpr: entry.fpr.gradient_boosting,
      })),
    [metricsHistory],
  );

  return (
    <div className="p-6 h-full flex flex-col gap-6 overflow-auto">
      <h1 className="font-display text-2xl text-text-primary font-bold tracking-wide">Analytics</h1>

      <div className="bg-bg-surface border border-bg-border rounded-lg p-5">
        <div className="font-display font-bold text-sm tracking-widest uppercase mb-4">Training Evaluation — CICIDS2017 Dataset</div>
        <div className="grid grid-cols-3 gap-4 text-xs font-mono">
          {(['logistic_regression', 'random_forest', 'gradient_boosting'] as ModelKey[]).map((model) => (
            <div key={model} className="border border-bg-border rounded p-3 bg-bg-raised">
              <div className="text-text-primary mb-2">{model.replaceAll('_', ' ')}</div>
              <div className="space-y-1 text-text-secondary">
                <div>accuracy: {trainingMetrics ? formatPercent(trainingMetrics[model].accuracy) : '--'}</div>
                <div>precision: {trainingMetrics ? formatPercent(trainingMetrics[model].precision) : '--'}</div>
                <div>recall: {trainingMetrics ? formatPercent(trainingMetrics[model].recall) : '--'}</div>
                <div>f1: {trainingMetrics ? formatPercent(trainingMetrics[model].f1) : '--'}</div>
                <div>roc-auc: {trainingMetrics ? formatPercent(trainingMetrics[model].roc_auc) : '--'}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-4 gap-3 mt-4">
          <img src="/figures/confusion_matrix_logistic_regression.png" className="border border-bg-border rounded" alt="Logistic confusion matrix" />
          <img src="/figures/confusion_matrix_random_forest.png" className="border border-bg-border rounded" alt="Random forest confusion matrix" />
          <img src="/figures/confusion_matrix_gradient_boosting.png" className="border border-bg-border rounded" alt="Gradient boosting confusion matrix" />
          <img src="/figures/feature_importance_rf.png" className="border border-bg-border rounded" alt="Feature importance" />
        </div>
      </div>

      <div className="bg-bg-surface border border-bg-border rounded-lg p-5 space-y-4">
        <div className="font-display font-bold text-sm tracking-widest uppercase">Live Simulation Metrics</div>

        <div className="grid grid-cols-3 gap-4 h-56">
          <MetricChart title="Live Accuracy" data={chartData} keys={['lrAcc', 'rfAcc', 'gbAcc']} />
          <MetricChart title="Live False Negative Rate" data={chartData} keys={['lrFnr', 'rfFnr', 'gbFnr']} danger />
          <MetricChart title="Live False Positive Rate" data={chartData} keys={['lrFpr', 'rfFpr', 'gbFpr']} />
        </div>

        <div className="grid grid-cols-3 gap-3 text-xs font-mono">
          {(['logistic_regression', 'random_forest', 'gradient_boosting'] as ModelKey[]).map((key) => (
            <div key={key} className="border border-bg-border rounded p-3 bg-bg-raised text-text-secondary">
              <div className="text-text-primary mb-1">{key.replaceAll('_', ' ')}</div>
              <div>training recall: {trainingMetrics ? formatPercent(trainingMetrics[key].recall) : '--'}</div>
              <div>live recall: {formatPercent(liveAccuracy[key].recall)}</div>
            </div>
          ))}
        </div>

        <ModelAgreementPanel />
      </div>
    </div>
  );
}

function MetricChart({
  title,
  data,
  keys,
  danger = false,
}: {
  title: string;
  data: Array<Record<string, string | number>>;
  keys: ['lrAcc' | 'lrFnr' | 'lrFpr', 'rfAcc' | 'rfFnr' | 'rfFpr', 'gbAcc' | 'gbFnr' | 'gbFpr'];
  danger?: boolean;
}) {
  const [lrKey, rfKey, gbKey] = keys;

  return (
    <div className="border border-bg-border rounded p-3 bg-bg-raised">
      <div className="text-xs font-mono text-text-secondary mb-2">{title}</div>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={data}>
          <XAxis dataKey="ts" hide />
          <YAxis domain={[0, 1]} tick={{ fill: '#6b7280', fontSize: 10 }} />
          <Tooltip
            formatter={(value: number) => `${(value * 100).toFixed(1)}%`}
            contentStyle={{ background: '#0a0b0f', border: '1px solid #1a1d27', color: '#e8eaf2', fontFamily: 'IBM Plex Mono' }}
          />
          <Line dot={false} type="monotone" dataKey={lrKey} stroke={danger ? '#ff3a3a' : modelColors.logistic_regression} strokeWidth={2} />
          <Line dot={false} type="monotone" dataKey={rfKey} stroke={danger ? '#ff7a7a' : modelColors.random_forest} strokeWidth={2} />
          <Line dot={false} type="monotone" dataKey={gbKey} stroke={danger ? '#ffaaaa' : modelColors.gradient_boosting} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
