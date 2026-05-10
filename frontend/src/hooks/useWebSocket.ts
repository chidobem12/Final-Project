import { useEffect, useRef } from 'react';
import toast from 'react-hot-toast';

import { audioSystem } from '../lib/audioAlerts';
import { useAegisStore } from '../store/useAegisStore';

export function useWebSocket() {
    const addEvent = useAegisStore((state) => state.addEvent);
const setConnectionState = useAegisStore((state) => state.setConnectionState);
    const recomputeStats = useAegisStore((state) => state.recomputeStats);
    const soundEnabled = useAegisStore((state) => state.soundEnabled);

    const ws = useRef<WebSocket | null>(null);
    const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const reconnectAttempt = useRef(0);
    const maxReconnectAttempts = 5;

    useEffect(() => {
        const statsInterval = setInterval(() => {
            recomputeStats();
        }, 5000);

        const connect = () => {
            ws.current = new WebSocket('ws://localhost:8000/ws/threats');

            ws.current.onopen = () => {
                const wasReconnecting = reconnectAttempt.current > 0;
                setConnectionState(true, reconnectAttempt.current);
                reconnectAttempt.current = 0;

                if (wasReconnecting && soundEnabled) {
                    audioSystem.playConnectionRestored();
                }
            };

            ws.current.onmessage = (socketEvent) => {
                try {
                    const message = JSON.parse(socketEvent.data);
if (message.type === 'threat_event' && message.event) {
                        addEvent(message.event);
                        if (
                            soundEnabled &&
                            message.event.prediction === 'ATTACK' &&
                            (message.event.severity === 'CRITICAL' || message.event.severity === 'HIGH')
                        ) {
                            audioSystem.playAlert(message.event.severity);
                        }
                    }
                } catch {
                    // Ignore malformed payloads.
                }
            };

            ws.current.onclose = () => {
                reconnectAttempt.current += 1;
                setConnectionState(false, reconnectAttempt.current);

                if (reconnectAttempt.current <= maxReconnectAttempts) {
                    reconnectTimer.current = setTimeout(connect, 3000);
                }
            };
        };

        connect();

        return () => {
            clearInterval(statsInterval);
            if (reconnectTimer.current) {
                clearTimeout(reconnectTimer.current);
            }
            ws.current?.close();
        };
    }, [addEvent, recomputeStats, setConnectionState, soundEnabled]);
}
