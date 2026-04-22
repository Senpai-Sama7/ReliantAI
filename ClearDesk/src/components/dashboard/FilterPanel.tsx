import { Search, X, Download } from 'lucide-react';
import { useDocuments } from '../../contexts/DocumentContext';
import { Button } from '../ui/Button';

interface FilterPanelProps {
  onExport?: () => void;
}

export function FilterPanel({ onExport }: FilterPanelProps) {
  const { state, setFilters, clearFilters } = useDocuments();
  const { filters } = state;

  const hasActiveFilters =
    filters.status !== 'all' || filters.type !== 'all' ||
    filters.priority !== 'all' || filters.searchQuery;

  const selectClass = 'bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary appearance-none focus:outline-none focus:border-border-hover cursor-pointer';

  return (
    <div className="flex flex-col lg:flex-row lg:items-center gap-3 mb-6">
      {/* Search */}
      <div className="relative flex-1 max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
        <input
          type="text"
          placeholder="Filter documents…"
          value={filters.searchQuery || ''}
          onChange={(e) => setFilters({ searchQuery: e.target.value })}
          className="w-full pl-9 pr-8 py-2 bg-surface border border-border rounded-lg text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-border-hover"
        />
        {filters.searchQuery && (
          <button onClick={() => setFilters({ searchQuery: '' })} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary">
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Dropdowns */}
      <select value={filters.status} onChange={(e) => setFilters({ status: e.target.value as typeof filters.status })} className={selectClass}>
        <option value="all">All Status</option>
        <option value="pending">Pending</option>
        <option value="processing">Processing</option>
        <option value="review">In Review</option>
        <option value="completed">Completed</option>
        <option value="escalated">Escalated</option>
      </select>

      <select value={filters.type} onChange={(e) => setFilters({ type: e.target.value as typeof filters.type })} className={selectClass}>
        <option value="all">All Types</option>
        <option value="invoice">Invoice</option>
        <option value="statement">Statement</option>
        <option value="payment_confirmation">Payment</option>
        <option value="dispute">Dispute</option>
        <option value="credit_note">Credit Note</option>
      </select>

      <select value={filters.priority} onChange={(e) => setFilters({ priority: e.target.value as typeof filters.priority })} className={selectClass}>
        <option value="all">All Priority</option>
        <option value="critical">Critical</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>

      {hasActiveFilters && (
        <Button variant="ghost" size="sm" onClick={clearFilters} leftIcon={<X className="w-3.5 h-3.5" />}>Clear</Button>
      )}

      <div className="lg:ml-auto">
        <Button variant="secondary" size="sm" onClick={onExport} leftIcon={<Download className="w-3.5 h-3.5" />}>Export</Button>
      </div>
    </div>
  );
}
