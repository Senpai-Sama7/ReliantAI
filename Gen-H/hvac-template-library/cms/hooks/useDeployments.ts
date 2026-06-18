import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchDeployments } from '../lib/api';
import type { Deployment, DeploymentStatus } from '../lib/types';

const ACTIVE_STATUSES: DeploymentStatus[] = ['pending', 'deploying'];
const POLL_INTERVAL_MS = 5000;

interface UseDeploymentsOptions {
  statusFilter?: DeploymentStatus | 'all';
  limit?: number;
  poll?: boolean;
}

export function useDeployments(options: UseDeploymentsOptions = {}) {
  const { statusFilter = 'all', limit, poll = true } = options;
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const mountedRef = useRef(true);

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const status = statusFilter === 'all' ? undefined : statusFilter;
      const data = await fetchDeployments(status);
      if (!mountedRef.current) return;
      setDeployments(limit ? data.slice(0, limit) : data);
      setError(null);
      setLastUpdated(new Date());
    } catch (err) {
      if (!mountedRef.current) return;
      setError(err instanceof Error ? err.message : 'Failed to load deployments');
    } finally {
      if (mountedRef.current && !silent) setLoading(false);
    }
  }, [statusFilter, limit]);

  useEffect(() => {
    mountedRef.current = true;
    load();
    return () => {
      mountedRef.current = false;
    };
  }, [load]);

  useEffect(() => {
    if (!poll) return;

    const hasActive = deployments.some((d) => ACTIVE_STATUSES.includes(d.status));
    if (!hasActive) {
      setIsPolling(false);
      return;
    }

    setIsPolling(true);
    const interval = setInterval(() => load(true), POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [deployments, poll, load]);

  return {
    deployments,
    loading,
    error,
    lastUpdated,
    isPolling,
    refresh: () => load(true),
  };
}
