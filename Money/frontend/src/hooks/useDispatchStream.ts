// Real-time dispatch stream hook via Server-Sent Events
import { useEffect, useRef, useState, useCallback } from 'react';
import api, { type DashboardMetrics, type SSEEvent } from '../services/api';

export type ConnectionState = 'connecting' | 'connected' | 'reconnecting' | 'error';

interface UseDispatchStreamResult {
  connectionState: ConnectionState;
  lastEvent: SSEEvent | null;
  liveMetrics: DashboardMetrics | null;
}

export function useDispatchStream(
  onDispatchEvent?: (event: SSEEvent) => void,
): UseDispatchStreamResult {
  const [connectionState, setConnectionState] = useState<ConnectionState>('connecting');
  const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null);
  const [liveMetrics, setLiveMetrics] = useState<DashboardMetrics | null>(null);

  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closeStream = useRef<(() => void) | null>(null);
  const retryCount = useRef(0);
  // Stable ref so `connect` never needs to be recreated when the callback changes
  const callbackRef = useRef(onDispatchEvent);
  callbackRef.current = onDispatchEvent;

  const connect = useCallback(() => {
    setConnectionState(retryCount.current > 0 ? 'reconnecting' : 'connecting');

    const close = api.openStream(
      (event) => {
        retryCount.current = 0;
        setConnectionState('connected');
        setLastEvent(event);

        if (event.type === 'metrics') {
          setLiveMetrics(event.data);
        }
        callbackRef.current?.(event);
      },
      () => {
        // SSE error — exponential backoff reconnect
        retryCount.current += 1;
        setConnectionState('reconnecting');
        const backoff = Math.min(1000 * 2 ** retryCount.current, 30_000);
        reconnectTimer.current = setTimeout(connect, backoff);
      },
    );

    closeStream.current = close;
    // connect itself has no external deps — it only reads the stable callbackRef
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    connect();
    return () => {
      closeStream.current?.();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    };
  }, [connect]);

  return { connectionState, lastEvent, liveMetrics };
}
