import { classNames } from '../../utils/formatters';
import type { DocumentPriority, DocumentStatus } from '../../types/document';
import { getStatusLabel, getPriorityLabel } from '../../utils/formatters';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'accent' | 'danger' | 'warning' | 'info';
  size?: 'sm' | 'md';
  className?: string;
}

export function Badge({ children, variant = 'default', size = 'sm', className }: BadgeProps) {
  const variants = {
    default: 'bg-border/50 text-text-secondary',
    accent: 'bg-accent/10 text-accent',
    danger: 'bg-danger/10 text-danger',
    warning: 'bg-warning/10 text-warning',
    info: 'bg-status-review/10 text-status-review',
  };
  const sizes = {
    sm: 'px-2 py-0.5 text-[11px]',
    md: 'px-2.5 py-1 text-xs',
  };

  return (
    <span className={classNames(
      'inline-flex items-center font-medium rounded-md',
      variants[variant], sizes[size], className
    )}>
      {children}
    </span>
  );
}

export function StatusBadge({ status, size = 'sm' }: { status: DocumentStatus; size?: 'sm' | 'md' }) {
  const variantMap: Record<DocumentStatus, BadgeProps['variant']> = {
    pending: 'default', processing: 'info', review: 'warning',
    completed: 'accent', escalated: 'danger',
  };
  return <Badge variant={variantMap[status]} size={size}>{getStatusLabel(status)}</Badge>;
}

export function PriorityBadge({ priority, size = 'sm' }: { priority: DocumentPriority; size?: 'sm' | 'md' }) {
  const variantMap: Record<DocumentPriority, BadgeProps['variant']> = {
    critical: 'danger', high: 'warning', medium: 'default', low: 'default',
  };
  return <Badge variant={variantMap[priority]} size={size}>{getPriorityLabel(priority)}</Badge>;
}
