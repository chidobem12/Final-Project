import { create } from 'zustand';

export type ThreatLevel = 'NOMINAL' | 'ELEVATED' | 'HIGH' | 'CRITICAL';

export interface ThreatEvent {
  event_id: string;
  timestamp: string;
  source_ip: string;
  destination_ip: string;
  destination_port: number;
  protocol: 'TCP' | 'UDP' | 'ICMP';
  prediction: 'ATTACK' | 'NORMAL';
  attack_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE';
  risk_score: number;
  confidence: number;
  model_votes: {
    logistic_regression: { prediction: number; confidence: number };
    random_forest: { prediction: number; confidence: number };
    gradient_boosting: { prediction: number; confidence: number };
  };
  top_features?: Array<{ name: string; score: number }>;
  bytes_transferred: number;
  flow_duration_ms: number;
  true_label?: string;
}

export interface Incident {
  id: string;
  title: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM';
  status: 'OPEN' | 'INVESTIGATING' | 'RESOLVED' | 'FALSE_POSITIVE';
  attack_type: string;
  source_ip: string;
  created_at: string;
  updated_at: string;
  event_ids: string[];
  notes: string;
  assigned_to?: string;
  resolved_at?: string;
  resolution_note?: string;
}

export interface NetworkNode {
  id: string;
  type: 'internal' | 'external' | 'gateway';
  threatCount: number;
  lastSeen: number;
  isUnderAttack: boolean;
  attackType?: string;
  totalEvents: number;
}

export interface NetworkEdge {
  id: string;
  source: string;
  target: string;
  lastSeen: number;
  isAttack: boolean;
}

export interface AegisUser {
  name: string;
  email: string;
  role: string;
}

interface LiveModelMetric {
  accuracy: number;
  missRate: number;
  falsePositiveRate: number;
  recall: number;
}

interface AegisStore {
  wsConnected: boolean;
  wsReconnectAttempt: number;
  lastEventTime: number;
  reconnectRecoveredAt: number | null;

  events: ThreatEvent[];
  addEvent: (event: ThreatEvent) => void;

  eventsPerMinute: number;
  threatRatePercent: number;
  threatLevel: ThreatLevel;
  activeAttackTypes: string[];
  lastUpdatedSecondsAgo: number;

  networkNodes: Map<string, NetworkNode>;
  networkEdges: NetworkEdge[];
  updateNode: (ip: string, event: ThreatEvent) => void;

  liveAccuracy: {
    logistic_regression: LiveModelMetric;
    random_forest: LiveModelMetric;
    gradient_boosting: LiveModelMetric;
    agreementRate: number;
  };
  metricsHistory: {
    ts: number;
    accuracy: Record<'logistic_regression' | 'random_forest' | 'gradient_boosting', number>;
    fnr: Record<'logistic_regression' | 'random_forest' | 'gradient_boosting', number>;
    fpr: Record<'logistic_regression' | 'random_forest' | 'gradient_boosting', number>;
    agreementRate: number;
  }[];
  recomputeStats: () => void;

  incidents: Incident[];
  addIncident: (incident: Incident) => void;
  updateIncident: (id: string, updates: Partial<Incident>) => void;
  unresolvedCount: number;

  user: AegisUser | null;
  token: string | null;
  setAuth: (user: AegisUser, token: string) => void;
  clearAuth: () => void;

  soundEnabled: boolean;
  simulationPaused: boolean;
  setSoundEnabled: (value: boolean) => void;
  setSimulationPaused: (value: boolean) => void;

  selectedEventId: string | null;
  setSelectedEventId: (eventId: string | null) => void;

  setConnectionState: (connected: boolean, reconnectAttempt?: number) => void;
}

const MODEL_KEYS = ['logistic_regression', 'random_forest', 'gradient_boosting'] as const;

const emptyMetric = (): LiveModelMetric => ({
  accuracy: 0,
  missRate: 0,
  falsePositiveRate: 0,
  recall: 0,
});

export function computeThreatLevel(threatRatePercent: number): ThreatLevel {
  if (threatRatePercent < 10) return 'NOMINAL';
  if (threatRatePercent < 25) return 'ELEVATED';
  if (threatRatePercent < 50) return 'HIGH';
  return 'CRITICAL';
}

const isInternalIp = (ip: string): boolean => {
  if (ip.startsWith('10.')) return true;
  if (ip.startsWith('192.168.')) return true;
  const second = Number(ip.split('.')[1] ?? '-1');
  return ip.startsWith('172.') && second >= 16 && second <= 31;
};

const nodeTypeForIp = (ip: string): NetworkNode['type'] => {
  if (ip === '192.168.1.1') return 'gateway';
  return isInternalIp(ip) ? 'internal' : 'external';
};

const initialSound = localStorage.getItem('aegis_sound_enabled') === 'true';
const initialToken = localStorage.getItem('aegis_token');
const initialUserRaw = localStorage.getItem('aegis_user');
const initialUser = initialUserRaw ? (JSON.parse(initialUserRaw) as AegisUser) : null;

export const useAegisStore = create<AegisStore>((set, get) => ({
  wsConnected: false,
  wsReconnectAttempt: 0,
  lastEventTime: 0,
  reconnectRecoveredAt: null,

  events: [],
  addEvent: (event) =>
    set((state) => {
      const dedupedExisting = state.events.filter((existing) => existing.event_id !== event.event_id);
      const nextEvents = [event, ...dedupedExisting].slice(0, 500);
      const now = Date.now();

      const nextNodes = new Map(state.networkNodes);
      const existingGateway = Array.from(nextNodes.values()).find((node) => node.type === 'gateway');
      const applyNode = (ip: string) => {
        const existing = nextNodes.get(ip);
        const underAttack = event.prediction === 'ATTACK' && (ip === event.source_ip || ip === event.destination_ip);
        const inferredType =
          ip === '192.168.1.1'
            ? 'gateway'
            : !existingGateway && !existing && isInternalIp(ip)
              ? 'gateway'
              : nodeTypeForIp(ip);
        const updated: NetworkNode = {
          id: ip,
          type: inferredType,
          threatCount: (existing?.threatCount ?? 0) + (underAttack ? 1 : 0),
          lastSeen: now,
          isUnderAttack: underAttack,
          attackType: underAttack ? event.attack_type : existing?.attackType,
          totalEvents: (existing?.totalEvents ?? 0) + 1,
        };
        nextNodes.set(ip, updated);
      };

      applyNode(event.source_ip);
      applyNode(event.destination_ip);

      const edgeId = `${event.source_ip}->${event.destination_ip}`;
      const nextEdges = [
        {
          id: edgeId,
          source: event.source_ip,
          target: event.destination_ip,
          lastSeen: now,
          isAttack: event.prediction === 'ATTACK',
        },
        ...state.networkEdges.filter((edge) => edge.id !== edgeId),
      ].slice(0, 1200);

      return {
        events: nextEvents,
        networkNodes: nextNodes,
        networkEdges: nextEdges,
        lastEventTime: now,
      };
    }),

  eventsPerMinute: 0,
  threatRatePercent: 0,
  threatLevel: 'NOMINAL',
  activeAttackTypes: [],
  lastUpdatedSecondsAgo: 0,

  networkNodes: new Map<string, NetworkNode>(),
  networkEdges: [],
  updateNode: (ip, event) =>
    set((state) => {
      const nextNodes = new Map(state.networkNodes);
      const existing = nextNodes.get(ip);
      const underAttack = event.prediction === 'ATTACK';
      nextNodes.set(ip, {
        id: ip,
        type: nodeTypeForIp(ip),
        threatCount: (existing?.threatCount ?? 0) + (underAttack ? 1 : 0),
        lastSeen: Date.now(),
        isUnderAttack: underAttack,
        attackType: underAttack ? event.attack_type : existing?.attackType,
        totalEvents: (existing?.totalEvents ?? 0) + 1,
      });
      return { networkNodes: nextNodes };
    }),

  liveAccuracy: {
    logistic_regression: emptyMetric(),
    random_forest: emptyMetric(),
    gradient_boosting: emptyMetric(),
    agreementRate: 0,
  },
  metricsHistory: [],
  recomputeStats: () => {
    const { events, lastEventTime, metricsHistory } = get();
    const now = Date.now();
    const oneMinuteAgo = now - 60000;
    const recentMinute = events.filter((event) => new Date(event.timestamp).getTime() >= oneMinuteAgo);
    const attackMinute = recentMinute.filter((event) => event.prediction === 'ATTACK');

    const activeTypes = Array.from(new Set(attackMinute.map((event) => event.attack_type))).slice(0, 8);
    const threatRatePercent = recentMinute.length > 0 ? (attackMinute.length / recentMinute.length) * 100 : 0;

    const withTruth = events.filter((event) => event.true_label).slice(0, 500);
    const computeMetricForModel = (modelKey: (typeof MODEL_KEYS)[number]): LiveModelMetric => {
      if (withTruth.length === 0) return emptyMetric();

      let correct = 0;
      let falsePositives = 0;
      let falseNegatives = 0;
      let actualBenign = 0;
      let actualAttack = 0;

      withTruth.forEach((event) => {
        const predictedAttack = event.model_votes?.[modelKey]?.prediction === 1;
        const actualAttackEvent = event.true_label !== 'Normal';
        if (predictedAttack === actualAttackEvent) correct += 1;
        if (predictedAttack && !actualAttackEvent) falsePositives += 1;
        if (!predictedAttack && actualAttackEvent) falseNegatives += 1;
        if (actualAttackEvent) actualAttack += 1;
        else actualBenign += 1;
      });

      const accuracy = correct / withTruth.length;
      const missRate = actualAttack > 0 ? falseNegatives / actualAttack : 0;
      const falsePositiveRate = actualBenign > 0 ? falsePositives / actualBenign : 0;
      const recall = actualAttack > 0 ? (actualAttack - falseNegatives) / actualAttack : 0;

      return { accuracy, missRate, falsePositiveRate, recall };
    };

    const logistic = computeMetricForModel('logistic_regression');
    const randomForest = computeMetricForModel('random_forest');
    const gradientBoosting = computeMetricForModel('gradient_boosting');

    let agreementMatches = 0;
    withTruth.forEach((event) => {
      const votes = MODEL_KEYS.map((key) => event.model_votes?.[key]?.prediction);
      if (votes.every((vote) => vote === votes[0])) agreementMatches += 1;
    });
    const agreementRate = withTruth.length > 0 ? agreementMatches / withTruth.length : 0;

    const nextHistory = [
      ...metricsHistory,
      {
        ts: now,
        accuracy: {
          logistic_regression: logistic.accuracy,
          random_forest: randomForest.accuracy,
          gradient_boosting: gradientBoosting.accuracy,
        },
        fnr: {
          logistic_regression: logistic.missRate,
          random_forest: randomForest.missRate,
          gradient_boosting: gradientBoosting.missRate,
        },
        fpr: {
          logistic_regression: logistic.falsePositiveRate,
          random_forest: randomForest.falsePositiveRate,
          gradient_boosting: gradientBoosting.falsePositiveRate,
        },
        agreementRate,
      },
    ].filter((entry) => now - entry.ts <= 60000);

    set({
      eventsPerMinute: recentMinute.length,
      threatRatePercent,
      threatLevel: computeThreatLevel(threatRatePercent),
      activeAttackTypes: activeTypes,
      lastUpdatedSecondsAgo: lastEventTime ? Math.floor((now - lastEventTime) / 1000) : 0,
      liveAccuracy: {
        logistic_regression: logistic,
        random_forest: randomForest,
        gradient_boosting: gradientBoosting,
        agreementRate,
      },
      metricsHistory: nextHistory,
    });
  },

  incidents: [],
  addIncident: (incident) =>
    set((state) => {
      const deduped = [incident, ...state.incidents.filter((entry) => entry.id !== incident.id)].sort((a, b) =>
        b.created_at.localeCompare(a.created_at),
      );
      return {
        incidents: deduped,
        unresolvedCount: deduped.filter((entry) => entry.status === 'OPEN' || entry.status === 'INVESTIGATING').length,
      };
    }),
  updateIncident: (id, updates) =>
    set((state) => {
      const updated = state.incidents.map((incident) =>
        incident.id === id ? { ...incident, ...updates, updated_at: new Date().toISOString() } : incident,
      );
      return {
        incidents: updated,
        unresolvedCount: updated.filter((entry) => entry.status === 'OPEN' || entry.status === 'INVESTIGATING').length,
      };
    }),
  unresolvedCount: 0,

  user: initialUser,
  token: initialToken,
  setAuth: (user, token) => {
    localStorage.setItem('aegis_token', token);
    localStorage.setItem('aegis_user', JSON.stringify(user));
    set({ user, token });
  },
  clearAuth: () => {
    localStorage.removeItem('aegis_token');
    localStorage.removeItem('aegis_user');
    set({ user: null, token: null });
  },

  soundEnabled: initialSound,
  simulationPaused: false,
  setSoundEnabled: (value) => {
    localStorage.setItem('aegis_sound_enabled', String(value));
    set({ soundEnabled: value });
  },
  setSimulationPaused: (value) => set({ simulationPaused: value }),

  selectedEventId: null,
  setSelectedEventId: (eventId) => set({ selectedEventId: eventId }),

  setConnectionState: (connected, reconnectAttempt = 0) =>
    set((state) => ({
      wsConnected: connected,
      wsReconnectAttempt: reconnectAttempt,
      reconnectRecoveredAt: connected && !state.wsConnected ? Date.now() : state.reconnectRecoveredAt,
    })),
}));
