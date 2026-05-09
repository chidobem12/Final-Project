import { useEffect, useMemo, useState } from 'react';
import clsx from 'clsx';

import { apiFetch } from '../lib/api';
import { formatRelativeSeconds } from '../lib/formatters';
import { useAegisStore, type Incident } from '../store/useAegisStore';

const statusStyle: Record<Incident['status'], string> = {
  OPEN: 'bg-accent-threat/20 text-accent-threat border-accent-threat/40',
  INVESTIGATING: 'bg-accent-warning/20 text-accent-warning border-accent-warning/40',
  RESOLVED: 'bg-accent-primary/20 text-accent-primary border-accent-primary/40',
  FALSE_POSITIVE: 'bg-bg-raised text-text-secondary border-bg-border line-through',
};

export default function Incidents() {
  const { incidents, addIncident, updateIncident, user, setSelectedEventId } = useAegisStore();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiFetch<Incident[]>('/api/incidents');
        data.forEach((incident) => addIncident(incident));
        if (data.length > 0 && !selectedId) setSelectedId(data[0].id);
      } catch {
        // Silent if unauthorized or unavailable.
      }
    };
    load();
  }, [addIncident, selectedId]);

  const selected = useMemo(() => incidents.find((entry) => entry.id === selectedId) ?? null, [incidents, selectedId]);

  const persistUpdate = async (id: string, updates: Partial<Incident>) => {
    setSaving(true);
    updateIncident(id, updates);
    try {
      await apiFetch<Incident>(`/api/incidents/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 h-full">
      <div className="grid grid-cols-10 gap-6 h-full">
        <div className="col-span-4 border border-bg-border rounded bg-bg-surface overflow-auto">
          {incidents.map((incident) => (
            <button
              key={incident.id}
              onClick={() => setSelectedId(incident.id)}
              className={clsx('w-full text-left p-4 border-b border-bg-border hover:bg-bg-raised', selectedId === incident.id && 'bg-bg-raised')}
            >
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-text-primary">{incident.id}</span>
                <span className={clsx('px-2 py-0.5 rounded border', statusStyle[incident.status])}>{incident.status}</span>
              </div>
              <div className="mt-2 text-sm text-text-primary">{incident.attack_type}</div>
              <div className="text-xs text-text-secondary mt-1">{formatRelativeSeconds(incident.created_at)}</div>
            </button>
          ))}
        </div>

        <div className="col-span-6 border border-bg-border rounded bg-bg-surface p-5 overflow-auto">
          {!selected && <div className="text-text-secondary font-mono text-sm">Select an incident</div>}
          {selected && (
            <div className="space-y-5">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className={clsx('font-display text-xl', selected.status === 'FALSE_POSITIVE' && 'line-through text-text-secondary')}>
                    {selected.title}
                  </h2>
                  <div className="text-xs text-text-secondary font-mono mt-1">{selected.source_ip} • {selected.attack_type}</div>
                </div>
                <select
                  value={selected.status}
                  onChange={(e) => persistUpdate(selected.id, { status: e.target.value as Incident['status'] })}
                  className="bg-bg-raised border border-bg-border rounded px-2 py-1 text-xs font-mono"
                  disabled={saving}
                >
                  <option>OPEN</option>
                  <option>INVESTIGATING</option>
                  <option>RESOLVED</option>
                  <option>FALSE_POSITIVE</option>
                </select>
              </div>

              <div className="text-xs text-text-secondary font-mono">Timeline: {selected.created_at} → {selected.updated_at}</div>

              <div>
                <div className="text-xs uppercase text-text-secondary mb-2">Linked Events</div>
                <div className="space-y-1">
                  {selected.event_ids.map((eventId) => (
                    <button
                      key={eventId}
                      className="text-left text-xs font-mono text-accent-info hover:underline"
                      onClick={() => {
                        setSelectedEventId(eventId);
                        window.location.href = '/feed';
                      }}
                    >
                      {eventId}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <div className="text-xs uppercase text-text-secondary mb-2">Notes</div>
                <textarea
                  value={selected.notes}
                  onChange={(e) => updateIncident(selected.id, { notes: e.target.value })}
                  onBlur={() => persistUpdate(selected.id, { notes: selected.notes })}
                  className="w-full h-32 bg-bg-raised border border-bg-border rounded p-2 text-xs font-mono"
                />
              </div>

              <div className="flex gap-3">
                <button
                  className="px-3 py-2 rounded border border-bg-border text-xs font-mono"
                  onClick={() => persistUpdate(selected.id, { assigned_to: user?.name ?? 'SOC Analyst' })}
                >
                  Assign to me
                </button>
                <button
                  className="px-3 py-2 rounded border border-bg-border text-xs font-mono text-text-secondary"
                  onClick={() => persistUpdate(selected.id, { status: 'FALSE_POSITIVE' })}
                >
                  Mark as False Positive
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
