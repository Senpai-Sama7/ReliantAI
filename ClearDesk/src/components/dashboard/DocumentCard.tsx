import { FileText, AlertTriangle } from 'lucide-react';
import type { Document } from '../../types/document';
import { PriorityBadge, StatusBadge } from '../ui/Badge';
import { formatRelativeTime, formatCurrency, truncateText, classNames, getDocumentTypeLabel } from '../../utils/formatters';

interface DocumentCardProps {
  document: Document;
  onClick?: () => void;
  style?: React.CSSProperties;
}

export function DocumentCard({ document, onClick, style }: DocumentCardProps) {
  const hasEscalation = document.isEscalated && document.escalationReasons?.length;

  return (
    <div
      onClick={onClick}
      style={style}
      className={classNames(
        'bg-surface border border-border rounded-lg p-4 cursor-pointer transition-all duration-200',
        'hover:border-border-hover hover:-translate-y-0.5',
        'animate-fade-up'
      )}
    >
      {/* Top row: type + badges */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-text-secondary" />
          <span className="text-[11px] uppercase tracking-wider text-text-secondary">
            {getDocumentTypeLabel(document.type)}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          {hasEscalation && <AlertTriangle className="w-3.5 h-3.5 text-danger" />}
          <PriorityBadge priority={document.priority} />
        </div>
      </div>

      {/* Filename */}
      <h4 className="text-sm font-medium text-text-primary mb-1 truncate">
        {truncateText(document.originalName, 40)}
      </h4>

      {/* Customer + Amount */}
      {document.extractedData?.customerName && (
        <p className="text-xs text-text-secondary truncate">{document.extractedData.customerName}</p>
      )}
      {document.extractedData?.amount != null && (
        <p className="font-mono text-sm font-medium text-text-primary mt-2">
          {formatCurrency(document.extractedData.amount, document.extractedData.currency || undefined)}
        </p>
      )}

      {/* Footer: status + time */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
        <StatusBadge status={document.status} />
        <span className="text-[11px] text-text-secondary">{formatRelativeTime(document.createdAt)}</span>
      </div>
    </div>
  );
}
