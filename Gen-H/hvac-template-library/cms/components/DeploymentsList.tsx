import Link from 'next/link';
import { useState } from 'react';
import DeploymentStatusBadge from './DeploymentStatusBadge';
import { useDeployments } from '../hooks/useDeployments';
import type { DeploymentStatus } from '../lib/types';

const STATUS_FILTERS: Array<{ value: DeploymentStatus | 'all'; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'deploying', label: 'Deploying' },
  { value: 'live', label: 'Live' },
  { value: 'failed', label: 'Failed' },
];

interface DeploymentsListProps {
  limit?: number;
  showFilters?: boolean;
  showViewAll?: boolean;
  title?: string;
}

function formatDate(value: string) {
  return new Date(value).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function DeploymentCard({ deployment }: { deployment: ReturnType<typeof useDeployments>['deployments'][number] }) {
  return (
    <div className="rounded-lg border border-slate-600 bg-slate-700/80 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="truncate font-mono text-sm text-white">{deployment.domain}</p>
          {(deployment.company_name || deployment.template_name) && (
            <p className="mt-1 truncate text-xs text-slate-400">
              {[deployment.company_name, deployment.template_name].filter(Boolean).join(' · ')}
            </p>
          )}
        </div>
        <DeploymentStatusBadge status={deployment.status} />
      </div>
      <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
        <span>{formatDate(deployment.created_at)}</span>
        <Link href={`/deployments/${deployment.id}`} className="font-medium text-blue-400 hover:text-blue-300">
          View →
        </Link>
      </div>
    </div>
  );
}

export default function DeploymentsList({
  limit,
  showFilters = false,
  showViewAll = false,
  title = 'Deployments',
}: DeploymentsListProps) {
  const [statusFilter, setStatusFilter] = useState<DeploymentStatus | 'all'>('all');
  const { deployments, loading, error, lastUpdated, isPolling, refresh } = useDeployments({
    statusFilter,
    limit,
    poll: true,
  });

  return (
    <section>
      <div className="mb-4 flex flex-col gap-3 sm:mb-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold sm:text-2xl">
            {title}
            {!loading && <span className="ml-2 text-base font-normal text-slate-400">({deployments.length})</span>}
          </h2>
          {lastUpdated && (
            <p className="mt-1 text-xs text-slate-500">
              Updated {lastUpdated.toLocaleTimeString()}
              {isPolling && <span className="ml-2 text-blue-400">· Live polling</span>}
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => refresh()}
            className="rounded-lg border border-slate-600 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700"
          >
            Refresh
          </button>
          {showViewAll && (
            <Link
              href="/deployments"
              className="rounded-lg bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-600"
            >
              View all
            </Link>
          )}
        </div>
      </div>

      {showFilters && (
        <div className="mb-4 flex gap-2 overflow-x-auto pb-1">
          {STATUS_FILTERS.map(({ value, label }) => (
            <button
              key={value}
              type="button"
              onClick={() => setStatusFilter(value)}
              className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium transition ${
                statusFilter === value
                  ? 'bg-purple-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      )}

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 animate-pulse rounded-lg bg-slate-700/60" />
          ))}
        </div>
      )}

      {!loading && error && (
        <div className="rounded-lg border border-red-800 bg-red-950/40 p-4 text-sm text-red-300">
          {error}
          <button type="button" onClick={() => refresh()} className="ml-3 underline hover:text-red-200">
            Retry
          </button>
        </div>
      )}

      {!loading && !error && deployments.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-600 p-8 text-center text-slate-400">
          <p>No deployments found.</p>
          <Link href="/deployments/create" className="mt-2 inline-block text-sm text-purple-400 hover:text-purple-300">
            Create your first deployment →
          </Link>
        </div>
      )}

      {!loading && !error && deployments.length > 0 && (
        <>
          {/* Mobile cards */}
          <div className="space-y-3 md:hidden">
            {deployments.map((deployment) => (
              <DeploymentCard key={deployment.id} deployment={deployment} />
            ))}
          </div>

          {/* Desktop table */}
          <div className="hidden overflow-hidden rounded-lg bg-slate-700 md:block">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px]">
                <thead className="bg-slate-800">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Domain</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Company</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Created</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {deployments.map((deployment) => (
                    <tr key={deployment.id} className="border-t border-slate-600 hover:bg-slate-600/80">
                      <td className="px-4 py-3 font-mono text-sm">{deployment.domain}</td>
                      <td className="px-4 py-3 text-sm text-slate-300">{deployment.company_name ?? '—'}</td>
                      <td className="px-4 py-3">
                        <DeploymentStatusBadge status={deployment.status} />
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-400">{formatDate(deployment.created_at)}</td>
                      <td className="px-4 py-3">
                        <Link href={`/deployments/${deployment.id}`} className="text-sm text-blue-400 hover:text-blue-300">
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
