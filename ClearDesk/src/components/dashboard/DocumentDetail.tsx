import { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { PriorityBadge, StatusBadge } from '../ui/Badge';
import { useDocuments } from '../../contexts/DocumentContext';
import { getTeamMembers } from '../../utils/settings';
import { formatDateTime, formatCurrency, classNames } from '../../utils/formatters';
import { FileText, User, AlertTriangle, CheckCircle, Clock, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react';

interface DocumentDetailProps {
  isOpen: boolean;
  onClose: () => void;
}

export function DocumentDetail({ isOpen, onClose }: DocumentDetailProps) {
  const { selectedDocument, updateDocument, deleteDocument, selectDocument, filteredDocuments } = useDocuments();

  const [lang, setLang] = useState<'en' | 'es'>('en');

  if (!selectedDocument) return null;

  const idx = filteredDocuments.findIndex(d => d.id === selectedDocument.id);
  const hasNext = idx < filteredDocuments.length - 1;
  const hasPrev = idx > 0;

  const handleStatusChange = (status: typeof selectedDocument.status) => {
    updateDocument(selectedDocument.id, { status });
  };

  const handleDelete = () => {
    deleteDocument(selectedDocument.id);
    onClose();
  };

  const selectClass = 'w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-border-hover';

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl" title={selectedDocument.originalName}>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Info */}
        <div className="lg:col-span-2 space-y-5">
          {/* Status row */}
          <div className="flex items-center gap-2">
            <StatusBadge status={selectedDocument.status} size="md" />
            <PriorityBadge priority={selectedDocument.priority} size="md" />
            {selectedDocument.isEscalated && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs bg-danger/10 text-danger">
                <AlertTriangle className="w-3 h-3" /> Escalated
              </span>
            )}
          </div>

          {/* Extracted Data */}
          {selectedDocument.extractedData && (
            <div className="border border-border rounded-lg divide-y divide-border">
              {[
                ['Customer', selectedDocument.extractedData.customerName],
                ['Invoice', selectedDocument.extractedData.invoiceNumber],
                ['Amount', selectedDocument.extractedData.amount != null ? formatCurrency(selectedDocument.extractedData.amount, selectedDocument.extractedData.currency || undefined) : null],
                ['Invoice Date', selectedDocument.extractedData.invoiceDate],
                ['Due Date', selectedDocument.extractedData.dueDate],
                ['Account', selectedDocument.extractedData.accountNumber],
                ['Confidence', selectedDocument.extractedData.confidence != null ? `${Math.round(selectedDocument.extractedData.confidence * 100)}%` : null],
              ].filter(([, v]) => v).map(([label, value]) => (
                <div key={label as string} className="flex justify-between px-4 py-2.5">
                  <span className="text-xs text-text-secondary uppercase tracking-wider">{label}</span>
                  <span className="text-sm text-text-primary font-mono">{value}</span>
                </div>
              ))}
            </div>
          )}

          {/* Escalation Reasons */}
          {selectedDocument.escalationReasons?.length ? (
            <div className="border border-danger/20 rounded-lg p-4 space-y-2">
              <p className="text-xs uppercase tracking-wider text-danger flex items-center gap-1.5">
                <AlertTriangle className="w-3 h-3" /> Escalation Reasons
              </p>
              {selectedDocument.escalationReasons.map((r, i) => (
                <p key={i} className="text-sm text-text-secondary">{r.description}</p>
              ))}
            </div>
          ) : null}

          {/* Summary */}
          {selectedDocument.notes && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs uppercase tracking-wider text-text-secondary">Summary</p>
                {selectedDocument.summaryEs && (
                  <div className="flex rounded-md border border-border overflow-hidden text-xs">
                    <button onClick={() => setLang('en')} className={classNames('px-2.5 py-1 transition-colors', lang === 'en' ? 'bg-accent/15 text-accent' : 'text-text-secondary hover:text-text-primary')}>EN</button>
                    <button onClick={() => setLang('es')} className={classNames('px-2.5 py-1 transition-colors border-l border-border', lang === 'es' ? 'bg-accent/15 text-accent' : 'text-text-secondary hover:text-text-primary')}>ES</button>
                  </div>
                )}
              </div>
              <p className="text-sm text-text-secondary bg-surface rounded-lg p-3 border border-border">
                {lang === 'es' && selectedDocument.summaryEs ? selectedDocument.summaryEs : selectedDocument.notes}
              </p>
            </div>
          )}

          {/* Navigation */}
          <div className="flex items-center justify-between pt-4 border-t border-border">
            <Button variant="ghost" size="sm" onClick={() => hasPrev && selectDocument(filteredDocuments[idx - 1].id)} disabled={!hasPrev}>
              <ChevronLeft className="w-4 h-4 mr-1" /> Prev
            </Button>
            <span className="text-xs text-text-secondary">{idx + 1} of {filteredDocuments.length}</span>
            <Button variant="ghost" size="sm" onClick={() => hasNext && selectDocument(filteredDocuments[idx + 1].id)} disabled={!hasNext}>
              Next <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="space-y-5">
          {/* Assign */}
          <div>
            <p className="text-xs uppercase tracking-wider text-text-secondary mb-2 flex items-center gap-1.5">
              <User className="w-3 h-3" /> Assign To
            </p>
            <select
              value={selectedDocument.assignee || ''}
              onChange={(e) => updateDocument(selectedDocument.id, { assignee: e.target.value || undefined })}
              className={selectClass}
            >
              <option value="">Unassigned</option>
              {getTeamMembers().map(name => (
                <option key={name} value={name}>{name}</option>
              ))}
            </select>
          </div>

          {/* Status */}
          <div>
            <p className="text-xs uppercase tracking-wider text-text-secondary mb-2">Update Status</p>
            <div className="space-y-1">
              {(['pending', 'processing', 'review', 'completed', 'escalated'] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => handleStatusChange(s)}
                  className={classNames(
                    'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors',
                    selectedDocument.status === s
                      ? 'bg-accent/10 text-accent'
                      : 'text-text-secondary hover:text-text-primary hover:bg-surface'
                  )}
                >
                  {s === 'completed' && <CheckCircle className="w-3.5 h-3.5 inline mr-2" />}
                  {s === 'escalated' && <AlertTriangle className="w-3.5 h-3.5 inline mr-2" />}
                  {s === 'pending' && <Clock className="w-3.5 h-3.5 inline mr-2" />}
                  {s === 'processing' && <Clock className="w-3.5 h-3.5 inline mr-2" />}
                  {s === 'review' && <FileText className="w-3.5 h-3.5 inline mr-2" />}
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Timeline */}
          <div>
            <p className="text-xs uppercase tracking-wider text-text-secondary mb-2">Timeline</p>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-text-secondary">Created</span><span className="text-text-primary text-xs">{formatDateTime(selectedDocument.createdAt)}</span></div>
              <div className="flex justify-between"><span className="text-text-secondary">Updated</span><span className="text-text-primary text-xs">{formatDateTime(selectedDocument.updatedAt)}</span></div>
              {selectedDocument.processedAt && (
                <div className="flex justify-between"><span className="text-text-secondary">Processed</span><span className="text-text-primary text-xs">{formatDateTime(selectedDocument.processedAt)}</span></div>
              )}
            </div>
          </div>

          {/* Delete */}
          <Button variant="danger" size="sm" className="w-full" onClick={handleDelete} leftIcon={<Trash2 className="w-3.5 h-3.5" />}>
            Delete Document
          </Button>
        </div>
      </div>
    </Modal>
  );
}
