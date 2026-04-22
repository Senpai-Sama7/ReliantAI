import { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { useDocuments } from '../../contexts/DocumentContext';
import { format } from 'date-fns';
import { Copy, Download, CheckCircle } from 'lucide-react';

interface ExportPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ExportPanel({ isOpen, onClose }: ExportPanelProps) {
  const { filteredDocuments } = useDocuments();
  const [copied, setCopied] = useState(false);

  const docs = filteredDocuments;
  const completed = docs.filter(d => d.status === 'completed').length;
  const escalated = docs.filter(d => d.status === 'escalated').length;
  const pending = docs.filter(d => d.status === 'pending' || d.status === 'processing').length;

  const reportText = `CLEARDESK — SUMMARY REPORT
Generated: ${format(new Date(), 'MMM d, yyyy h:mm a')}

OVERVIEW
  Total Documents: ${docs.length}
  Completed: ${completed}
  Pending: ${pending}
  Escalated: ${escalated}

DOCUMENTS
${docs.map(d =>
  `  ${d.originalName} | ${d.status} | ${d.priority} | ${d.extractedData?.customerName || '—'} | ${d.extractedData?.amount != null ? '$' + d.extractedData.amount.toLocaleString() : '—'}`
).join('\n') || '  No documents'}
`;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(reportText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([reportText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cleardesk-report-${format(new Date(), 'yyyy-MM-dd')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCSV = () => {
    const esc = (v: unknown) => { const s = String(v ?? ''); return s.includes(',') || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s; };
    const header = 'Name,Status,Priority,Type,Customer,Amount,Invoice,Created\n';
    const rows = docs.map(d =>
      [d.originalName, d.status, d.priority, d.type, d.extractedData?.customerName || '', d.extractedData?.amount || '', d.extractedData?.invoiceNumber || '', d.createdAt].map(esc).join(',')
    ).join('\n');
    const blob = new Blob([header + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cleardesk-export-${format(new Date(), 'yyyy-MM-dd')}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Export Report" size="lg">
      <div className="space-y-5">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Total', value: docs.length },
            { label: 'Completed', value: completed },
            { label: 'Escalated', value: escalated },
          ].map(s => (
            <div key={s.label} className="bg-surface border border-border rounded-lg p-3 text-center">
              <p className="font-mono text-xl font-semibold text-text-primary">{s.value}</p>
              <p className="text-[11px] uppercase tracking-wider text-text-secondary">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Preview */}
        <div className="bg-bg border border-border rounded-lg p-4 max-h-48 overflow-y-auto scrollbar-thin">
          <pre className="text-xs text-text-secondary whitespace-pre-wrap font-mono">{reportText}</pre>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-border">
          <Button variant="secondary" onClick={handleCopy} leftIcon={copied ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />} className="flex-1">
            {copied ? 'Copied' : 'Copy'}
          </Button>
          <Button variant="secondary" onClick={handleDownload} leftIcon={<Download className="w-4 h-4" />} className="flex-1">
            Download TXT
          </Button>
          <Button variant="primary" onClick={handleCSV} leftIcon={<Download className="w-4 h-4" />} className="flex-1">
            Export CSV
          </Button>
        </div>
      </div>
    </Modal>
  );
}
