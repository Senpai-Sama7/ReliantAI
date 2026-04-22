import { useEffect, useState, useCallback, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import api, { type Dispatch, type DashboardMetrics, type SSEEvent } from '../../services/api';
import { useDispatchStream } from '../../hooks/useDispatchStream';
import { useToast } from '../../hooks/useToast';
import ToastContainer from '../../components/ToastContainer';
import DispatchDetailModal from '../../components/DispatchDetailModal';
import BillingPanel from './BillingPanel';
import {
  LogOut, RefreshCw, AlertCircle, CheckCircle, Clock, TrendingUp,
  Phone, MapPin, User, Activity, DollarSign, CreditCard, Search,
  Wifi, WifiOff, Loader2, Filter, X, Bell, Zap, Wrench,
} from 'lucide-react';

// ── Sub-components ─────────────────────────────────────────────

interface StatCardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  sub?: string;
  color?: 'gold' | 'green' | 'red' | 'blue';
  pulse?: boolean;
}

function StatCard({ label, value, icon, sub, color = 'gold', pulse }: StatCardProps) {
  const colorMap: Record<string, string> = {
    gold:  'border-genh-gold/30 text-genh-gold',
    green: 'border-green-500/30 text-green-400',
    red:   'border-red-500/30 text-red-400',
    blue:  'border-blue-500/30 text-blue-400',
  };
  return (
    <div
      className={`p-5 border ${colorMap[color]} bg-genh-charcoal/50 relative overflow-hidden`}
      style={{ clipPath: 'polygon(0 0, calc(100% - 14px) 0, 100% 14px, 100% 100%, 0 100%)' }}
    >
      {pulse && (
        <span className="absolute top-2 right-2 flex h-2.5 w-2.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500" />
        </span>
      )}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-label mb-1.5 opacity-60 text-xs">{label}</p>
          <p className="font-display text-3xl text-genh-white">{value}</p>
          {sub && <p className="text-xs text-genh-gray mt-1 font-body">{sub}</p>}
        </div>
        <div className={`p-2 bg-genh-black/40 ${colorMap[color]}`}>{icon}</div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cfg: Record<string, { cls: string; icon: React.ReactNode }> = {
    complete:    { cls: 'text-green-400 bg-green-400/10 border-green-400/30', icon: <CheckCircle className="w-3 h-3" /> },
    pending:     { cls: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30', icon: <Clock className="w-3 h-3" /> },
    queued:      { cls: 'text-blue-400 bg-blue-400/10 border-blue-400/30', icon: <Activity className="w-3 h-3" /> },
    in_progress: { cls: 'text-purple-400 bg-purple-400/10 border-purple-400/30', icon: <Loader2 className="w-3 h-3 animate-spin" /> },
    emergency:   { cls: 'text-red-400 bg-red-400/10 border-red-400/30', icon: <AlertCircle className="w-3 h-3" /> },
    cancelled:   { cls: 'text-genh-gray/60 bg-genh-gray/10 border-genh-gray/20', icon: <X className="w-3 h-3" /> },
    error:       { cls: 'text-red-400 bg-red-400/10 border-red-400/30', icon: <AlertCircle className="w-3 h-3" /> },
  };
  const c = cfg[status.toLowerCase()] ?? cfg.queued;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-body uppercase tracking-wider border ${c.cls}`}>
      {c.icon}{status}
    </span>
  );
}

function ConnectionPill({ state }: { state: string }) {
  const isConnected = state === 'connected';
  const isReconnecting = state === 'reconnecting';
  return (
    <div className={`flex items-center gap-1.5 text-xs font-body px-2.5 py-1 border ${
      isConnected ? 'text-green-400 border-green-400/30 bg-green-400/5'
      : isReconnecting ? 'text-yellow-400 border-yellow-400/30 bg-yellow-400/5'
      : 'text-genh-gray border-genh-white/10'
    }`}>
      {isConnected ? <Wifi className="w-3 h-3" />
       : isReconnecting ? <Loader2 className="w-3 h-3 animate-spin" />
       : <WifiOff className="w-3 h-3" />}
      <span className="hidden sm:inline">{isConnected ? 'Live' : isReconnecting ? 'Reconnecting' : 'Offline'}</span>
    </div>
  );
}

function EmptyState({ hasFilters }: { hasFilters: boolean }) {
  return (
    <tr>
      <td colSpan={6} className="px-6 py-16 text-center">
        <div className="flex flex-col items-center gap-3">
          {hasFilters ? (
            <>
              <Search className="w-8 h-8 text-genh-gray/40" />
              <p className="text-genh-gray font-body">No dispatches match your filters.</p>
            </>
          ) : (
            <>
              <Zap className="w-8 h-8 text-genh-gray/40" />
              <p className="text-genh-gray font-body">No dispatches yet.</p>
              <p className="text-genh-gray/60 text-xs">
                Dispatches from SMS, WhatsApp, or the API will appear here in real time.
              </p>
            </>
          )}
        </div>
      </td>
    </tr>
  );
}

// ── Main Dashboard ─────────────────────────────────────────────

export default function AdminDashboard() {
  const { logout } = useAuth();
  const { toasts, toast, dismiss } = useToast();

  const [dispatches, setDispatches] = useState<Dispatch[]>([]);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [selectedDispatch, setSelectedDispatch] = useState<Dispatch | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterUrgency, setFilterUrgency] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [hasNewEmergency, setHasNewEmergency] = useState(false);

  // Stable ref so SSE handler never triggers reconnects when toast identity changes
  const toastRef = useRef(toast);
  toastRef.current = toast;

  const handleSSEEvent = useCallback((event: SSEEvent) => {
    if (event.type === 'metrics') {
      setMetrics(event.data);
    } else if (event.type === 'dispatch_created') {
      toastRef.current(`New dispatch: ${(event.data.issue ?? '').slice(0, 60)}`, 'info', 6000);
      api.getDispatches(50).then(setDispatches).catch(() => null);
    } else if (event.type === 'dispatch_completed') {
      toastRef.current('Dispatch completed', 'success');
      setDispatches(prev =>
        prev.map(d => d.dispatch_id === event.data.run_id ? { ...d, status: 'complete' } : d),
      );
    } else if (event.type === 'dispatch_error') {
      toastRef.current(`Dispatch failed: ${event.data.error.slice(0, 80)}`, 'error', 8000);
      setDispatches(prev =>
        prev.map(d => d.dispatch_id === event.data.run_id ? { ...d, status: 'error' } : d),
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const { connectionState, liveMetrics } = useDispatchStream(handleSSEEvent);
  const displayMetrics = liveMetrics ?? metrics;

  useEffect(() => {
    if (displayMetrics && displayMetrics.today_emergency > 0) setHasNewEmergency(true);
  }, [displayMetrics]);

  const loadData = useCallback(async (silent = false) => {
    if (!silent) setIsLoading(true);
    try {
      const [dispatchData, metricsData] = await Promise.all([
        api.getDispatches(50),
        api.getMetrics(),
      ]);
      setDispatches(dispatchData);
      setMetrics(metricsData);
      setLastRefresh(new Date());
    } catch {
      toastRef.current('Failed to load data. Check your connection.', 'error');
    } finally {
      setIsLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // ⌘R keyboard shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'r') {
        e.preventDefault();
        loadData(true);
        toastRef.current('Data refreshed', 'success', 2000);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [loadData]);

  // Debounced search
  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    const hasFilter = searchQuery || filterStatus || filterUrgency;
    if (!hasFilter) {
      api.getDispatches(50).then(setDispatches).catch(() => null);
      return;
    }
    searchTimer.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const result = await api.searchDispatches({
          q: searchQuery, status: filterStatus, urgency: filterUrgency, limit: 100,
        });
        setDispatches(result.results);
      } catch {
        toastRef.current('Search failed', 'error', 3000);
      } finally {
        setIsSearching(false);
      }
    }, 300);
    return () => { if (searchTimer.current) clearTimeout(searchTimer.current); };
  }, [searchQuery, filterStatus, filterUrgency]);

  const clearFilters = () => { setSearchQuery(''); setFilterStatus(''); setFilterUrgency(''); };
  const hasFilters = Boolean(searchQuery || filterStatus || filterUrgency);

  const handleDispatchUpdated = (updated: Dispatch) => {
    setDispatches(prev => prev.map(d => d.dispatch_id === updated.dispatch_id ? updated : d));
    if (selectedDispatch?.dispatch_id === updated.dispatch_id) setSelectedDispatch(updated);
    toast('Dispatch updated', 'success');
  };

  return (
    <div className="min-h-screen bg-genh-black text-genh-white">
      <ToastContainer toasts={toasts} onDismiss={dismiss} />

      {/* Emergency banner */}
      {hasNewEmergency && (
        <div className="bg-red-900/80 border-b border-red-500/50 px-6 py-2 flex items-center justify-between">
          <div className="flex items-center gap-2 text-red-200 text-sm font-body">
            <AlertCircle className="w-4 h-4 animate-pulse" />
            <strong>{displayMetrics?.today_emergency} emergency dispatch{displayMetrics?.today_emergency !== 1 ? 'es' : ''} today</strong>
            {' '}— review immediately
          </div>
          <button onClick={() => setHasNewEmergency(false)} className="text-red-300 hover:text-red-100 transition-colors" aria-label="Dismiss">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header */}
      <header className="border-b border-genh-white/10 bg-genh-black/90 sticky top-0 z-20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-genh-gold shrink-0" style={{ clipPath: 'polygon(50% 0%, 100% 100%, 0% 100%)' }} />
            <h1 className="font-display text-lg text-genh-white uppercase tracking-tight hidden sm:block">
              Dispatch Command
            </h1>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <ConnectionPill state={connectionState} />
            <button
              onClick={() => { loadData(true); toast('Refreshed', 'success', 1500); }}
              className="p-1.5 text-genh-gray hover:text-genh-white transition-colors"
              aria-label="Refresh (⌘R)" title="Refresh (⌘R)"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <span className="text-genh-gray/40 text-xs hidden md:block">{lastRefresh.toLocaleTimeString()}</span>
            <button
              onClick={() => logout()}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-genh-white/20 text-genh-gray hover:text-genh-white hover:border-genh-gold/50 transition-all font-body text-xs"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:block">Logout</span>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8 py-6 space-y-6">

        {/* Stats grid */}
        {displayMetrics && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <StatCard label="Total" value={displayMetrics.total} icon={<Activity className="w-4 h-4" />} />
            <StatCard label="Today" value={displayMetrics.today_count} icon={<Zap className="w-4 h-4" />} color="blue" />
            <StatCard label="Pending" value={displayMetrics.pending_count} icon={<Clock className="w-4 h-4" />} color="blue" />
            <StatCard label="Completed" value={displayMetrics.completed_count} icon={<CheckCircle className="w-4 h-4" />} color="green" />
            <StatCard
              label="Emergencies"
              value={displayMetrics.emergency_count}
              icon={<AlertCircle className="w-4 h-4" />}
              sub={`${displayMetrics.emergency_pct}% of total`}
              color="red"
              pulse={displayMetrics.today_emergency > 0}
            />
            <StatCard
              label="Today Emergency"
              value={displayMetrics.today_emergency}
              icon={<Bell className="w-4 h-4" />}
              color={displayMetrics.today_emergency > 0 ? 'red' : 'gold'}
              pulse={displayMetrics.today_emergency > 0}
            />
          </div>
        )}

        {/* Dispatch table */}
        <div className="border border-genh-white/10 bg-genh-charcoal/10">
          <div className="px-4 sm:px-6 py-4 border-b border-genh-white/10 flex flex-col sm:flex-row sm:items-center gap-3">
            <h2 className="font-display text-base text-genh-white uppercase tracking-tight shrink-0">
              Dispatches
              {hasFilters && (
                <span className="ml-2 text-xs text-genh-gold normal-case font-body">
                  ({dispatches.length} results)
                </span>
              )}
            </h2>
            <div className="flex-1 flex items-center gap-2 flex-wrap">
              {/* Search */}
              <div className="relative flex-1 min-w-[160px] max-w-xs">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-genh-gray/60 pointer-events-none" />
                <input
                  type="text"
                  placeholder="Search…"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full bg-genh-black border border-genh-white/15 text-genh-white text-xs px-8 py-1.5 placeholder:text-genh-gray/40 focus:outline-none focus:border-genh-gold/50 transition-colors"
                  aria-label="Search dispatches"
                />
                {isSearching && <Loader2 className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-genh-gold animate-spin" />}
              </div>
              <select
                value={filterStatus}
                onChange={e => setFilterStatus(e.target.value)}
                className="bg-genh-black border border-genh-white/15 text-genh-white text-xs px-2 py-1.5 focus:outline-none focus:border-genh-gold/50"
                aria-label="Filter by status"
              >
                <option value="">All status</option>
                <option value="queued">Queued</option>
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="complete">Complete</option>
                <option value="error">Error</option>
                <option value="cancelled">Cancelled</option>
              </select>
              <select
                value={filterUrgency}
                onChange={e => setFilterUrgency(e.target.value)}
                className="bg-genh-black border border-genh-white/15 text-genh-white text-xs px-2 py-1.5 focus:outline-none focus:border-genh-gold/50"
                aria-label="Filter by urgency"
              >
                <option value="">All urgency</option>
                <option value="emergency">Emergency</option>
                <option value="urgent">Urgent</option>
                <option value="standard">Standard</option>
              </select>
              {hasFilters && (
                <button
                  onClick={clearFilters}
                  className="flex items-center gap-1 text-xs text-genh-gray hover:text-genh-white transition-colors"
                  aria-label="Clear filters"
                >
                  <Filter className="w-3 h-3" /><X className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[600px]">
              <thead>
                <tr className="border-b border-genh-white/10">
                  {['Status', 'Customer', 'Issue', 'Urgency', 'Tech / ETA', 'Time'].map(h => (
                    <th key={h} className="text-left px-4 sm:px-6 py-3 text-label text-xs opacity-60 font-normal">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr><td colSpan={6} className="px-6 py-12 text-center"><Loader2 className="w-6 h-6 text-genh-gold animate-spin mx-auto" /></td></tr>
                ) : dispatches.length === 0 ? (
                  <EmptyState hasFilters={hasFilters} />
                ) : dispatches.map(d => (
                  <tr
                    key={d.dispatch_id}
                    onClick={() => setSelectedDispatch(d)}
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') setSelectedDispatch(d); }}
                    className={`border-b border-genh-white/5 hover:bg-genh-white/5 transition-colors cursor-pointer ${
                      d.urgency?.toLowerCase() === 'emergency' ? 'bg-red-950/10' : ''
                    }`}
                    role="button"
                    tabIndex={0}
                    aria-label={`View dispatch from ${d.customer_name || 'unknown'}`}
                  >
                    <td className="px-4 sm:px-6 py-3"><StatusBadge status={d.status} /></td>
                    <td className="px-4 sm:px-6 py-3">
                      <div className="flex items-center gap-1.5 text-genh-white">
                        <User className="w-3.5 h-3.5 text-genh-gray shrink-0" />
                        <span className="truncate max-w-[120px]">{d.customer_name || 'Unknown'}</span>
                      </div>
                      {d.customer_phone && (
                        <div className="flex items-center gap-1 text-genh-gray text-xs mt-0.5">
                          <Phone className="w-3 h-3" />{d.customer_phone}
                        </div>
                      )}
                    </td>
                    <td className="px-4 sm:px-6 py-3">
                      <p className="text-genh-white/90 max-w-[200px] truncate">{d.issue_summary || '—'}</p>
                      {d.address && (
                        <div className="flex items-center gap-1 text-genh-gray text-xs mt-0.5">
                          <MapPin className="w-3 h-3 shrink-0" /><span className="truncate max-w-[180px]">{d.address}</span>
                        </div>
                      )}
                    </td>
                    <td className="px-4 sm:px-6 py-3">
                      <span className={`text-xs ${d.urgency?.toLowerCase() === 'emergency' ? 'text-red-400 font-semibold' : 'text-genh-gray'}`}>
                        {d.urgency?.toLowerCase() === 'emergency' && <AlertCircle className="w-3 h-3 inline mr-1" />}
                        {d.urgency || 'Standard'}
                      </span>
                    </td>
                    <td className="px-4 sm:px-6 py-3 text-xs">
                      <div className="flex items-center gap-1 text-genh-gray">
                        <Wrench className="w-3 h-3" />
                        <span>{d.tech_name || <em className="opacity-40">Unassigned</em>}</span>
                      </div>
                      {d.eta && <div className="text-genh-gold/80 mt-0.5">{d.eta}</div>}
                    </td>
                    <td className="px-4 sm:px-6 py-3">
                      <span className="text-genh-gray text-xs whitespace-nowrap">
                        {new Date(d.created_at).toLocaleString(undefined, {
                          month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
                        })}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-6 py-2 border-t border-genh-white/5 text-xs text-genh-gray/50 font-body">
            Click any row to view full details · Edit assignment · See state timeline
          </div>
        </div>

        {/* Quick actions */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button onClick={() => { loadData(true); toast('Refreshed', 'success', 1500); }}
            className="p-5 border border-genh-white/10 bg-genh-charcoal/20 hover:border-genh-gold/50 transition-all text-left group">
            <RefreshCw className="w-5 h-5 text-genh-gold mb-2 group-hover:rotate-180 transition-transform duration-500" />
            <h3 className="font-display text-xs text-genh-white uppercase">Refresh</h3>
            <p className="text-genh-gray text-xs font-body mt-0.5">⌘R also works</p>
          </button>
          <a href="/" className="p-5 border border-genh-white/10 bg-genh-charcoal/20 hover:border-genh-gold/50 transition-all text-left">
            <TrendingUp className="w-5 h-5 text-genh-gold mb-2" />
            <h3 className="font-display text-xs text-genh-white uppercase">Website</h3>
            <p className="text-genh-gray text-xs font-body mt-0.5">Customer-facing site</p>
          </a>
          <button onClick={() => document.getElementById('billing-section')?.scrollIntoView({ behavior: 'smooth' })}
            className="p-5 border border-genh-white/10 bg-genh-charcoal/20 hover:border-genh-gold/50 transition-all text-left">
            <DollarSign className="w-5 h-5 text-genh-gold mb-2" />
            <h3 className="font-display text-xs text-genh-white uppercase">Revenue</h3>
            <p className="text-genh-gray text-xs font-body mt-0.5">Billing & customers</p>
          </button>
          <div className="p-5 border border-genh-white/10 bg-genh-charcoal/20">
            <Activity className="w-5 h-5 text-genh-gold mb-2" />
            <h3 className="font-display text-xs text-genh-white uppercase">System</h3>
            <p className={`text-xs font-body mt-0.5 flex items-center gap-1.5 ${connectionState === 'connected' ? 'text-green-400' : 'text-yellow-400'}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${connectionState === 'connected' ? 'bg-green-400 animate-pulse' : 'bg-yellow-400'}`} />
              {connectionState === 'connected' ? 'Live stream active' : 'Reconnecting…'}
            </p>
          </div>
        </div>

        {/* Billing */}
        <div id="billing-section" className="scroll-mt-8">
          <div className="flex items-center gap-3 mb-5">
            <CreditCard className="w-5 h-5 text-genh-gold" />
            <h2 className="font-display text-xl text-genh-white uppercase tracking-tight">
              Billing & Customer Management
            </h2>
          </div>
          <BillingPanel />
        </div>
      </main>

      {/* Detail modal */}
      {selectedDispatch && (
        <DispatchDetailModal
          dispatch={selectedDispatch}
          onClose={() => setSelectedDispatch(null)}
          onUpdated={handleDispatchUpdated}
          onError={msg => toast(msg, 'error')}
        />
      )}
    </div>
  );
}
