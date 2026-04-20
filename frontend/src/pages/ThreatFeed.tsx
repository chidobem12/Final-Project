import { useEffect, useMemo, useState } from 'react';
import clsx from 'clsx';
import { format } from 'date-fns';

import { useAegisStore, type ThreatEvent } from '../store/useAegisStore';

export default function ThreatFeed() {
  const {
    events,
    wsConnected,
    selectedEventId,
    setSelectedEventId,
    simulationPaused,
    setSimulationPaused,
  } = useAegisStore();

  const [selectedEvent, setSelectedEvent] = useState<ThreatEvent | null>(null);
  const [frozenEvents, setFrozenEvents] = useState<ThreatEvent[]>([]);

  useEffect(() => {
    if (!selectedEventId) return;
    const found = events.find((event) => event.event_id === selectedEventId) ?? null;
    setSelectedEvent(found);
  }, [events, selectedEventId]);

  const displayEvents = simulationPaused ? frozenEvents : events;

  const attackRows = useMemo(() => events.filter((event) => event.prediction === 'ATTACK').length, [events]);

  const togglePause = () => {
    if (simulationPaused) {
      setSimulationPaused(false);
      return;
    }
    setFrozenEvents(events);
    setSimulationPaused(true);
  };

  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'text-accent-threat bg-accent-threat/10 border-accent-threat/30';
      case 'HIGH':
        return 'text-accent-warning bg-accent-warning/10 border-accent-warning/30';
      case 'MEDIUM':
        return 'text-accent-info bg-accent-info/10 border-accent-info/30';
      default:
        return 'text-text-primary bg-bg-raised border-bg-border';
    }
  };

  const setEventSelection = (event: ThreatEvent) => {
    setSelectedEvent(event);
    setSelectedEventId(event.event_id);
  };

  const truthIsAttack = selectedEvent?.true_label && selectedEvent.true_label !== 'Normal';
  const modelPredAttack = selectedEvent?.prediction === 'ATTACK';
  const modelCorrect = selectedEvent ? truthIsAttack === modelPredAttack : false;

  return (
    <div className="p-6 h-full flex flex-col space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="font-display text-2xl text-text-primary font-bold tracking-wide">Threat Feed</h1>
        <button
          onClick={togglePause}
          className={clsx(
            'px-4 py-2 rounded font-mono text-sm border transition-colors',
            simulationPaused
              ? 'border-accent-warning text-accent-warning bg-accent-warning/10'
              : 'border-bg-border text-text-secondary hover:text-text-primary hover:bg-bg-raised',
          )}
        >
          {simulationPaused ? 'RESUME FEED' : 'PAUSE FEED'}
        </button>
      </div>

      <div className="flex-1 flex space-x-6 min-h-0">
        <div className="flex-1 bg-bg-surface border border-bg-border rounded-lg flex flex-col overflow-hidden relative">
          {!wsConnected && (
            <div className="absolute top-0 left-0 right-0 z-10 bg-accent-warning/15 text-accent-warning text-xs font-mono px-3 py-2">
              FEED PAUSED — Reconnecting...
            </div>
          )}

          <div className="grid grid-cols-12 gap-2 p-3 border-b border-bg-border text-xs font-semibold tracking-wider text-text-secondary uppercase">
            <div className="col-span-1">Time</div>
            <div className="col-span-2">Event ID</div>
            <div className="col-span-2">Source</div>
            <div className="col-span-2">Destination</div>
            <div className="col-span-1">Proto</div>
            <div className="col-span-1">Risk</div>
            <div className="col-span-2">Type</div>
            <div className="col-span-1 text-right">Sev</div>
          </div>

          <div className="flex-1 overflow-auto bg-bg-void/50">
            {displayEvents.map((event) => (
              <button
                key={event.event_id}
                onClick={() => setEventSelection(event)}
                className={clsx(
                  'w-full text-left grid grid-cols-12 gap-2 p-3 border-b border-bg-border/50 text-xs font-mono items-center hover:bg-bg-raised transition-colors',
                  event.prediction === 'ATTACK' ? 'text-accent-warning' : 'text-text-secondary',
                  selectedEvent?.event_id === event.event_id && 'bg-bg-raised',
                )}
              >
                <div className="col-span-1 opacity-70">{format(new Date(event.timestamp), 'HH:mm:ss')}</div>
                <div className="col-span-2 truncate">{event.event_id}</div>
                <div className="col-span-2 text-text-primary">{event.source_ip}</div>
                <div className="col-span-2 text-text-primary">{event.destination_ip}:{event.destination_port}</div>
                <div className="col-span-1">{event.protocol}</div>
                <div className="col-span-1">{event.risk_score}</div>
                <div className="col-span-2 truncate">{event.attack_type}</div>
                <div className="col-span-1 text-right">
                  <span className={clsx('px-2 py-0.5 rounded border', getSeverityStyle(event.severity))}>{event.severity}</span>
                </div>
              </button>
            ))}

            {displayEvents.length === 0 && (
              <div className="h-full flex items-center justify-center text-text-secondary font-mono text-sm">Waiting for events...</div>
            )}
          </div>

          <div className="border-t border-bg-border px-3 py-2 text-xs font-mono text-text-secondary">
            Total attack rows: {attackRows}
          </div>
        </div>

        {selectedEvent && (
          <div className="w-96 overflow-y-auto bg-bg-surface border border-bg-border rounded-lg p-6 flex flex-col">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="font-display font-bold text-lg mb-1">{selectedEvent.attack_type}</h3>
                <div className="font-mono text-xs text-text-secondary">ID: {selectedEvent.event_id}</div>
              </div>
              <span className={clsx('px-3 py-1 text-xs font-bold font-mono rounded border', getSeverityStyle(selectedEvent.severity))}>
                {selectedEvent.severity}
              </span>
            </div>

            <div className="space-y-5">
              <div>
                <div className="text-xs uppercase text-text-secondary mb-2">Routing Context</div>
                <div className="font-mono text-xs text-text-primary space-y-1">
                  <div>{selectedEvent.source_ip} → {selectedEvent.destination_ip}:{selectedEvent.destination_port}</div>
                  <div>Protocol: {selectedEvent.protocol}</div>
                  <div>Flow Duration: {selectedEvent.flow_duration_ms.toFixed(1)}ms</div>
                </div>
              </div>

              <div>
                <div className="text-xs uppercase text-text-secondary mb-2">Ground Truth</div>
                <div className="font-mono text-xs flex items-center gap-2">
                  <span>{selectedEvent.true_label ?? 'Unknown'}</span>
                  {selectedEvent.true_label && (
                    <span className={clsx('px-2 py-0.5 rounded border', modelCorrect ? 'text-accent-primary border-accent-primary/40' : 'text-accent-threat border-accent-threat/40')}>
                      {modelCorrect ? 'CORRECT' : 'WRONG'}
                    </span>
                  )}
                </div>
              </div>

              <div>
                <div className="text-xs uppercase text-text-secondary mb-2">Feature Drivers</div>
                {!selectedEvent.top_features || selectedEvent.top_features.length === 0 ? (
                  <div className="text-xs font-mono text-text-secondary">Feature explanation unavailable</div>
                ) : (
                  <div className="space-y-2">
                    {selectedEvent.top_features.map((feature) => (
                      <div key={feature.name} className="space-y-1">
                        <div className="flex justify-between text-[11px] font-mono text-text-secondary">
                          <span>{feature.name}</span>
                          <span>{(feature.score * 100).toFixed(1)}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-bg-raised rounded overflow-hidden">
                          <div className="h-full bg-accent-info" style={{ width: `${Math.max(4, feature.score * 100)}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
