import { useEffect, useMemo, useRef, useState } from 'react';
import * as d3 from 'd3';
import toast from 'react-hot-toast';
import clsx from 'clsx';

import { apiFetch } from '../lib/api';
import { useAegisStore } from '../store/useAegisStore';

interface ScenarioSummary {
  scenario_name: string;
  duration_seconds: number;
  events_generated: number;
  events_flagged: number;
  detection_rate: number;
}

interface ScenarioCard {
  id: string;
  name: string;
  description: string;
  duration: number;
  eps: number;
  attackType: string;
}

const scenarios: ScenarioCard[] = [
  { id: 'ddos_flood', name: 'DDoS Flood', description: 'Volumetric flood against ingress services', duration: 30, eps: 50, attackType: 'DDoS' },
  { id: 'credential_stuffing', name: 'Credential Stuffing', description: 'Mass login attempts from distributed botnet', duration: 20, eps: 30, attackType: 'Brute Force' },
  { id: 'ransomware_outbreak', name: 'Ransomware Lateral', description: 'Internal lateral movement and encryption prep', duration: 45, eps: 20, attackType: 'Infiltration' },
  { id: 'apt_intrusion', name: 'APT Intrusion', description: 'Low-and-slow reconnaissance', duration: 60, eps: 2, attackType: 'Infiltration' },
  { id: 'insider_exfiltration', name: 'Insider Exfiltration', description: 'Large data transfer to untrusted endpoint', duration: 25, eps: 5, attackType: 'Exfiltration' },
];

export default function ThreatMap() {
  const { networkNodes, networkEdges } = useAegisStore();
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [showSimModal, setShowSimModal] = useState(false);
  const [activeScenario, setActiveScenario] = useState<ScenarioCard | null>(null);
  const [scenarioStartedAt, setScenarioStartedAt] = useState<number | null>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; content: string } | null>(null);
  const [clock, setClock] = useState(0);

  const nodeList = useMemo(() => Array.from(networkNodes.values()), [networkNodes]);
  const edgeList = useMemo(() => networkEdges.slice(0, 400), [networkEdges]);

  useEffect(() => {
    if (!activeScenario) return;
    const interval = setInterval(() => setClock((value) => value + 1), 1000);
    return () => clearInterval(interval);
  }, [activeScenario]);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;
    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const nodes = nodeList.map((node) => ({ ...node })) as Array<{
      id: string;
      type: 'internal' | 'external' | 'gateway';
      threatCount: number;
      lastSeen: number;
      isUnderAttack: boolean;
      attackType?: string;
      totalEvents: number;
      x?: number;
      y?: number;
      fx?: number | null;
      fy?: number | null;
    }>;

    const links = edgeList
      .filter((edge) => nodes.some((node) => node.id === edge.source) && nodes.some((node) => node.id === edge.target))
      .map((edge) => ({ ...edge }));

    const simulation = d3
      .forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-260))
      .force('center', d3.forceCenter(width / 2, height / 2));

    const linkLayer = svg.append('g');
    const nodeLayer = svg.append('g');
    const labelLayer = svg.append('g');

    const now = Date.now();

    linkLayer
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', (edge) => (edge.isAttack ? 'var(--accent-threat)' : 'var(--text-secondary)'))
      .attr('stroke-opacity', (edge) => {
        const age = now - edge.lastSeen;
        if (edge.isAttack) return age < 4000 ? 0.9 : 0.2;
        return 0.2;
      })
      .attr('stroke-width', (edge) => (edge.isAttack ? 2 : 1))
      .attr('stroke-dasharray', (edge) => (edge.isAttack ? '8 6' : ''))
      .attr('class', (edge) => (edge.isAttack ? 'threat-edge' : ''));

    const shape = d3
      .symbol<{ type: 'internal' | 'external' | 'gateway' }>()
      .size(180)
      .type((d) => {
        if (d.type === 'gateway') return d3.symbolSquare;
        if (d.type === 'external') return d3.symbolTriangle;
        return d3.symbolCircle;
      });

    const node = nodeLayer
      .selectAll('path')
      .data(nodes)
      .join('path')
      .attr('d', (d) => shape(d as any) || '')
      .attr('fill', (d) => {
        if (d.isUnderAttack) return 'var(--accent-threat)';
        if (d.threatCount > 0) return 'var(--accent-warning)';
        return 'var(--accent-primary)';
      })
      .attr('opacity', (d) => (Date.now() - d.lastSeen > 60000 ? 0.3 : 1))
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        setTooltip({
          x: event.offsetX,
          y: event.offsetY,
          content: `${d.id} | ${d.type.toUpperCase()} | total ${d.totalEvents} | threats ${d.threatCount} | ${d.attackType ?? 'no recent attack'}`,
        });
      })
      .call(
        d3
          .drag<any, any>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }),
      );

    const label = labelLayer
      .selectAll('text')
      .data(nodes)
      .join('text')
      .text((d) => (d.type === 'internal' ? 'INT' : d.type === 'external' ? 'EXT' : 'GW'))
      .attr('fill', 'var(--text-secondary)')
      .attr('font-size', 10)
      .attr('font-family', 'IBM Plex Mono')
      .attr('text-anchor', 'middle')
      .attr('dy', 20);

    simulation.on('tick', () => {
      linkLayer
        .selectAll('line')
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('transform', (d: any) => `translate(${d.x}, ${d.y})`);
      label.attr('x', (d: any) => d.x).attr('y', (d: any) => d.y);
    });

    return () => {
      simulation.stop();
    };
  }, [edgeList, nodeList]);

  const triggerScenario = async (scenario: ScenarioCard) => {
    if (activeScenario) return;
    setActiveScenario(scenario);
    setScenarioStartedAt(Date.now());
    setShowSimModal(false);

    try {
      await apiFetch('/api/simulate/attack', {
        method: 'POST',
        body: JSON.stringify({ scenario_id: scenario.id }),
      });

      setTimeout(async () => {
        const summary = await apiFetch<ScenarioSummary>('/api/simulate/stop', { method: 'POST' });
        toast.success(`${summary.scenario_name} ended — ${summary.events_generated} events, ${(summary.detection_rate * 100).toFixed(1)}% flagged`);
        setActiveScenario(null);
        setScenarioStartedAt(null);
      }, scenario.duration * 1000);
    } catch {
      setActiveScenario(null);
      setScenarioStartedAt(null);
    }
  };

  const abortScenario = async () => {
    const summary = await apiFetch<ScenarioSummary>('/api/simulate/stop', { method: 'POST' });
    toast(`${summary.scenario_name} ended — ${summary.events_generated} events generated`);
    setActiveScenario(null);
    setScenarioStartedAt(null);
  };

  const progress = activeScenario && scenarioStartedAt ? Math.min(100, ((Date.now() - scenarioStartedAt) / (activeScenario.duration * 1000)) * 100) : 0;

  return (
    <div className="p-6 h-full flex flex-col space-y-4">
      <h1 className="font-display text-2xl text-text-primary font-bold tracking-wide">Network Threat Map</h1>

      <div className="flex-1 flex space-x-6 min-h-0">
        <div className="flex-1 bg-bg-surface border border-bg-border rounded-lg relative overflow-hidden" ref={containerRef}>
          <svg ref={svgRef} className="w-full h-full" />

          {tooltip && (
            <div style={{ left: tooltip.x + 12, top: tooltip.y + 12 }} className="absolute text-xs font-mono bg-bg-void border border-bg-border rounded px-2 py-1 max-w-xs">
              {tooltip.content}
            </div>
          )}

          {activeScenario && (
            <div className="absolute top-4 right-4 bg-accent-threat/20 border border-accent-threat text-accent-threat px-4 py-2 rounded font-mono text-xs">
              SCENARIO ACTIVE: {activeScenario.name}
            </div>
          )}
        </div>

        <div className="w-80 flex flex-col space-y-4">
          <div className="bg-bg-surface border border-bg-border rounded-lg p-6">
            <h3 className="font-display font-bold uppercase text-sm mb-4 border-b border-bg-border pb-2">Simulation Control</h3>
            <button
              onClick={() => setShowSimModal(true)}
              disabled={!!activeScenario}
              className="w-full bg-accent-threat text-bg-void font-bold font-display uppercase tracking-widest py-3 rounded disabled:opacity-50"
            >
              Trigger Attack
            </button>
            {activeScenario && (
              <>
                <div className="mt-3 h-2 w-full bg-bg-raised rounded overflow-hidden">
                  <div className="h-full bg-accent-warning" style={{ width: `${progress}%` }} />
                </div>
                <button onClick={abortScenario} className="w-full mt-3 border border-bg-border text-text-secondary font-mono text-xs py-2 rounded hover:text-text-primary">
                  ABORT
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {showSimModal && (
        <div className="fixed inset-0 z-50 bg-bg-void/80 backdrop-blur-sm flex items-center justify-center">
          <div className="bg-bg-surface border border-accent-threat/50 w-[620px] rounded-lg overflow-hidden">
            <div className="p-4 border-b border-bg-border flex justify-between items-center bg-accent-threat/5">
              <h2 className="font-display font-bold text-accent-threat tracking-widest">SELECT SCENARIO</h2>
              <button onClick={() => setShowSimModal(false)} className="text-text-secondary hover:text-text-primary">✕</button>
            </div>

            <div className="p-4 grid grid-cols-1 gap-3 max-h-[60vh] overflow-y-auto">
              {scenarios.map((scenario) => (
                <button
                  key={scenario.id}
                  onClick={() => triggerScenario(scenario)}
                  disabled={!!activeScenario}
                  className={clsx(
                    'p-4 rounded border text-left transition-colors',
                    activeScenario
                      ? 'opacity-50 border-bg-border bg-bg-raised cursor-not-allowed'
                      : 'border-bg-border hover:border-accent-threat/50 hover:bg-bg-raised',
                  )}
                >
                  <div className="font-mono font-bold text-text-primary mb-1">{scenario.name}</div>
                  <div className="text-xs text-text-secondary mb-2">{scenario.description}</div>
                  <div className="text-[11px] font-mono text-text-secondary flex gap-4">
                    <span>Duration {scenario.duration}s</span>
                    <span>Expected EPS {scenario.eps}</span>
                    <span className="text-accent-warning">{scenario.attackType}</span>
                  </div>
                  {activeScenario && <div className="mt-2 text-[11px] text-text-secondary">Scenario active</div>}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
      <div className="hidden">{clock}</div>
    </div>
  );
}
