import { useDocuments } from '../../contexts/DocumentContext';
import { FileText, CheckCircle, AlertTriangle, Clock } from 'lucide-react';

export function StatsOverview() {
  const { state } = useDocuments();
  const { documents } = state;

  const stats = [
    { label: 'Total', value: documents.length, icon: FileText },
    { label: 'Pending', value: documents.filter(d => d.status === 'pending' || d.status === 'processing').length, icon: Clock },
    { label: 'Completed', value: documents.filter(d => d.status === 'completed').length, icon: CheckCircle },
    { label: 'Escalated', value: documents.filter(d => d.status === 'escalated').length, icon: AlertTriangle },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {stats.map((s) => {
        const Icon = s.icon;
        return (
          <div key={s.label} className="bg-surface border border-border rounded-lg p-4 transition-colors hover:border-border-hover">
            <div className="flex items-center justify-between mb-3">
              <Icon className="w-4 h-4 text-text-secondary" />
            </div>
            <p className="font-mono text-2xl font-semibold text-text-primary">{s.value}</p>
            <p className="text-[11px] uppercase tracking-wider text-text-secondary mt-1">{s.label}</p>
          </div>
        );
      })}
    </div>
  );
}
