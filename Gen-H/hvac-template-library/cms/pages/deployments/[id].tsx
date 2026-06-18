import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import DashboardLayout from '../../components/DashboardLayout';
import DeploymentStatusBadge from '../../components/DeploymentStatusBadge';
import { fetchDeployment, triggerDeployment } from '../../lib/api';
import type { Deployment } from '../../lib/types';

const POLL_INTERVAL_MS = 3000;

export default function DeploymentDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const deploymentId = typeof id === 'string' ? id : null;

  const [deployment, setDeployment] = useState<Deployment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deploying, setDeploying] = useState(false);
  const mountedRef = useRef(true);

  const load = useCallback(async (silent = false) => {
    if (!deploymentId) return;
    if (!silent) setLoading(true);
    try {
      const data = await fetchDeployment(deploymentId);
      if (mountedRef.current) {
        setDeployment(data);
        setError(null);
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : 'Failed to load deployment');
      }
    } finally {
      if (mountedRef.current && !silent) setLoading(false);
    }
  }, [deploymentId]);

  useEffect(() => {
    mountedRef.current = true;
    if (deploymentId) load();
    return () => {
      mountedRef.current = false;
    };
  }, [deploymentId, load]);

  useEffect(() => {
    if (!deployment || !['pending', 'deploying'].includes(deployment.status)) return;
    const interval = setInterval(() => load(true), POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [deployment, load]);

  const handleDeploy = async () => {
    if (!deploymentId) return;
    setDeploying(true);
    setError(null);
    try {
      const updated = await triggerDeployment(deploymentId);
      setDeployment(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Deploy failed');
    } finally {
      setDeploying(false);
    }
  };

  const canDeploy = deployment && ['pending', 'failed'].includes(deployment.status);

  return (
    <DashboardLayout
      title={deployment?.domain ?? 'Deployment'}
      subtitle={deployment ? `${deployment.company_name ?? 'Company'} · ${deployment.template_name ?? 'Template'}` : undefined}
      actions={
        canDeploy ? (
          <button
            type="button"
            onClick={handleDeploy}
            disabled={deploying}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold hover:bg-blue-700 disabled:opacity-60"
          >
            {deploying ? 'Starting…' : 'Deploy to Production'}
          </button>
        ) : undefined
      }
    >
      {loading && <div className="h-48 animate-pulse rounded-lg bg-slate-700/60" />}

      {!loading && error && (
        <div className="rounded-lg border border-red-800 bg-red-950/40 p-4 text-sm text-red-300">{error}</div>
      )}

      {!loading && deployment && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <InfoCard label="Status">
            <DeploymentStatusBadge status={deployment.status} size="md" />
          </InfoCard>
          <InfoCard label="Domain">
            <a
              href={`https://${deployment.domain}`}
              target="_blank"
              rel="noopener noreferrer"
              className="break-all font-mono text-sm text-blue-400 hover:text-blue-300"
            >
              {deployment.domain}
            </a>
          </InfoCard>
          <InfoCard label="Created">{new Date(deployment.created_at).toLocaleString()}</InfoCard>
          {deployment.deployment_date && (
            <InfoCard label="Deployed">{new Date(deployment.deployment_date).toLocaleString()}</InfoCard>
          )}
          {deployment.status === 'deploying' && (
            <div className="sm:col-span-2 lg:col-span-3 rounded-lg border border-blue-800 bg-blue-950/30 p-4 text-sm text-blue-200">
              Deployment in progress — this page refreshes automatically every few seconds.
            </div>
          )}
        </div>
      )}
    </DashboardLayout>
  );
}

function InfoCard({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-slate-600 bg-slate-700/80 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <div className="mt-2 text-sm text-slate-200">{children}</div>
    </div>
  );
}
