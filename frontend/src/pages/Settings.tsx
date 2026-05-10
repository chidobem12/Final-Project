import { useState } from 'react';
import { Download } from 'lucide-react';

import { apiFetch } from '../lib/api';
import { useAegisStore } from '../store/useAegisStore';

type DownloadKey = 'csv' | 'metrics' | null;

const toCsv = (rows: Record<string, unknown>[]) => {
  if (rows.length === 0) return '';
  const headers = Array.from(
    rows.reduce((set, row) => {
      Object.keys(row).forEach((key) => set.add(key));
      return set;
    }, new Set<string>()),
  );

  const encode = (value: unknown) => {
    const text = typeof value === 'string' ? value : JSON.stringify(value ?? '');
    return `"${text.replaceAll('"', '""')}"`;
  };

  const lines = [headers.join(',')];
  rows.forEach((row) => {
    lines.push(headers.map((header) => encode(row[header])).join(','));
  });
  return lines.join('\n');
};

const downloadBlob = (fileName: string, content: string, contentType: string) => {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(url);
};

export default function Settings() {
  const { events, soundEnabled, setSoundEnabled } = useAegisStore();
  const [loading, setLoading] = useState<DownloadKey>(null);

  const stamp = new Date().toISOString().replaceAll(':', '-');

  const downloadCsv = async () => {
    setLoading('csv');
    try {
      downloadBlob(`aegis_events_${stamp}.csv`, toCsv(events as unknown as Record<string, unknown>[]), 'text/csv;charset=utf-8');
    } finally {
      setLoading(null);
    }
  };

  const downloadMetrics = async () => {
    setLoading('metrics');
    try {
      const metrics = await apiFetch('/api/metrics');
      downloadBlob(`aegis_metrics_${stamp}.json`, JSON.stringify(metrics, null, 2), 'application/json;charset=utf-8');
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="p-6 h-full flex flex-col space-y-6 max-w-5xl mx-auto w-full">
      <h1 className="font-display text-2xl text-text-primary font-bold tracking-wide">System Configuration</h1>

      <div className="bg-bg-surface border border-bg-border rounded-lg p-6">
        <h2 className="font-display font-bold text-sm tracking-widest uppercase mb-6 border-b border-bg-border pb-2">Alerting</h2>
        <button
          type="button"
          onClick={() => setSoundEnabled(!soundEnabled)}
          className="px-4 py-2 rounded border border-bg-border font-mono text-sm text-text-secondary hover:text-text-primary"
        >
          Sound Alerts: {soundEnabled ? 'ON' : 'OFF'}
        </button>
      </div>

      <div className="bg-bg-surface border border-bg-border rounded-lg p-6">
        <h2 className="font-display font-bold text-sm tracking-widest uppercase mb-6 border-b border-bg-border pb-2">Data Management</h2>
        <div className="flex gap-4 flex-wrap">
          <button
            disabled={loading !== null}
            onClick={downloadCsv}
            className="flex items-center space-x-2 px-4 py-2 bg-bg-raised border border-bg-border rounded font-mono text-sm disabled:opacity-60"
          >
            <Download size={16} />
            <span>{loading === 'csv' ? 'Generating...' : 'Download Full Event Log (CSV)'}</span>
          </button>

          <button
            disabled={loading !== null}
            onClick={downloadMetrics}
            className="flex items-center space-x-2 px-4 py-2 bg-bg-raised border border-bg-border rounded font-mono text-sm disabled:opacity-60"
          >
            <Download size={16} />
            <span>{loading === 'metrics' ? 'Generating...' : 'Download Metrics Profile (JSON)'}</span>
          </button>

        </div>
      </div>
    </div>
  );
}
