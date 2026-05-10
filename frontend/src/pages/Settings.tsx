import { useRef, useState } from 'react';
import { Download, Upload } from 'lucide-react';

import { apiFetch, apiUpload } from '../lib/api';
import { useAegisStore } from '../store/useAegisStore';

type DownloadKey = 'csv' | 'metrics' | null;

interface UploadResult {
  filename: string;
  total_rows: number;
  attacks_detected: number;
  normal_classified: number;
  attack_rate: number;
  results: Array<{
    row: number;
    prediction: 'ATTACK' | 'NORMAL';
    attack_type: string;
    severity: string;
    risk_score: number;
    confidence: number;
    model_votes: Record<string, { prediction: number; confidence: number }>;
    top_features: Array<{ name: string; score: number }>;
  }>;
}

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
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

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

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const result = await apiUpload<UploadResult>('/api/upload/csv', formData);
      setUploadResult(result);
    } catch {
      // handled by toast or silent
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = '';
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

      <div className="bg-bg-surface border border-bg-border rounded-lg p-6">
        <h2 className="font-display font-bold text-sm tracking-widest uppercase mb-6 border-b border-bg-border pb-2">CSV Analysis</h2>
        <div className="flex items-center gap-4">
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            onChange={handleFileUpload}
            className="hidden"
            id="csv-upload"
          />
          <label
            htmlFor="csv-upload"
            className="flex items-center space-x-2 px-4 py-2 bg-bg-raised border border-bg-border rounded font-mono text-sm cursor-pointer hover:bg-bg-raised/80"
          >
            <Upload size={16} />
            <span>{uploading ? 'Analyzing...' : 'Choose CSV'}</span>
          </label>
          {uploadResult && (
            <span className="text-xs text-text-secondary font-mono">{uploadResult.filename} — {uploadResult.total_rows} rows</span>
          )}
        </div>

        {uploadResult && (
          <div className="mt-4 space-y-4">
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-bg-raised border border-bg-border rounded p-3">
                <div className="text-xs text-text-secondary uppercase">Total Rows</div>
                <div className="text-lg font-mono text-text-primary">{uploadResult.total_rows}</div>
              </div>
              <div className="bg-bg-raised border border-bg-border rounded p-3">
                <div className="text-xs text-text-secondary uppercase">Attacks</div>
                <div className="text-lg font-mono text-accent-threat">{uploadResult.attacks_detected}</div>
              </div>
              <div className="bg-bg-raised border border-bg-border rounded p-3">
                <div className="text-xs text-text-secondary uppercase">Normal</div>
                <div className="text-lg font-mono text-accent-primary">{uploadResult.normal_classified}</div>
              </div>
              <div className="bg-bg-raised border border-bg-border rounded p-3">
                <div className="text-xs text-text-secondary uppercase">Attack Rate</div>
                <div className="text-lg font-mono text-accent-warning">{(uploadResult.attack_rate * 100).toFixed(1)}%</div>
              </div>
            </div>

            <div className="max-h-64 overflow-auto border border-bg-border rounded">
              <table className="w-full text-xs font-mono">
                <thead className="sticky top-0 bg-bg-surface">
                  <tr className="border-b border-bg-border text-text-secondary">
                    <th className="text-left p-2">#</th>
                    <th className="text-left p-2">Prediction</th>
                    <th className="text-left p-2">Severity</th>
                    <th className="text-right p-2">Risk</th>
                    <th className="text-right p-2">Confidence</th>
                    <th className="text-left p-2">Attack Type</th>
                  </tr>
                </thead>
                <tbody>
                  {uploadResult.results.map((r) => (
                    <tr key={r.row} className="border-b border-bg-border hover:bg-bg-raised">
                      <td className="p-2 text-text-secondary">{r.row}</td>
                      <td className={`p-2 ${r.prediction === 'ATTACK' ? 'text-accent-threat' : 'text-accent-primary'}`}>
                        {r.prediction}
                      </td>
                      <td className="p-2 text-text-secondary">{r.severity}</td>
                      <td className="p-2 text-right text-text-primary">{r.risk_score}</td>
                      <td className="p-2 text-right text-text-primary">{(r.confidence * 100).toFixed(1)}%</td>
                      <td className="p-2 text-text-secondary">{r.attack_type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
