import type { DeploymentStatus } from '../lib/types';

const STATUS_STYLES: Record<DeploymentStatus, string> = {
  live: 'bg-green-600 text-green-50',
  deploying: 'bg-blue-600 text-blue-50 animate-pulse',
  failed: 'bg-red-600 text-red-50',
  pending: 'bg-yellow-600 text-yellow-50',
};

interface DeploymentStatusBadgeProps {
  status: DeploymentStatus;
  size?: 'sm' | 'md';
}

export default function DeploymentStatusBadge({ status, size = 'sm' }: DeploymentStatusBadgeProps) {
  const sizeClass = size === 'md' ? 'px-3 py-1 text-sm' : 'px-2 py-1 text-xs';
  return (
    <span className={`inline-flex items-center rounded font-semibold capitalize ${sizeClass} ${STATUS_STYLES[status]}`}>
      {status === 'deploying' && (
        <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-white animate-ping" />
      )}
      {status}
    </span>
  );
}
