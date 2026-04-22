import { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import api, { type Dispatch, type DashboardMetrics } from '../../services/api';
import { 
  LogOut, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  TrendingUp,
  Phone,
  MapPin,
  User,
  Activity
} from 'lucide-react';

interface StatCardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  trend?: string;
  color?: 'gold' | 'green' | 'red' | 'blue';
}

function StatCard({ label, value, icon, trend, color = 'gold' }: StatCardProps) {
  const colorClasses = {
    gold: 'border-genh-gold/30 text-genh-gold',
    green: 'border-green-500/30 text-green-400',
    red: 'border-red-500/30 text-red-400',
    blue: 'border-blue-500/30 text-blue-400',
  };

  return (
    <div 
      className={`p-6 border ${colorClasses[color]} bg-genh-charcoal/50`}
      style={{ clipPath: 'polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 0 100%)' }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-label mb-2 opacity-70">{label}</p>
          <p className="font-display text-3xl text-genh-white">{value}</p>
          {trend && (
            <p className="text-xs text-genh-gray mt-1 font-body">{trend}</p>
          )}
        </div>
        <div className="p-2 bg-genh-black/50">
          {icon}
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { color: string; icon: React.ReactNode }> = {
    complete: { 
      color: 'text-green-400 bg-green-400/10 border-green-400/30', 
      icon: <CheckCircle className="w-3 h-3" /> 
    },
    pending: { 
      color: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30', 
      icon: <Clock className="w-3 h-3" /> 
    },
    queued: { 
      color: 'text-blue-400 bg-blue-400/10 border-blue-400/30', 
      icon: <Activity className="w-3 h-3" /> 
    },
    emergency: { 
      color: 'text-red-400 bg-red-400/10 border-red-400/30', 
      icon: <AlertCircle className="w-3 h-3" /> 
    },
  };

  const config = statusConfig[status.toLowerCase()] || statusConfig.queued;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-body uppercase tracking-wider border ${config.color}`}>
      {config.icon}
      {status}
    </span>
  );
}

export default function AdminDashboard() {
  const { logout } = useAuth();
  const [dispatches, setDispatches] = useState<Dispatch[]>([]);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [dispatchesData, metricsData] = await Promise.all([
        api.getDispatches(50),
        api.getMetrics(),
      ]);
      setDispatches(dispatchesData);
      setMetrics(metricsData);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="min-h-screen bg-genh-black">
      {/* Header */}
      <header className="border-b border-genh-white/10 bg-genh-charcoal/30 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 md:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="font-display text-xl text-genh-white uppercase tracking-tight">
                GEN-H
              </span>
              <span className="text-genh-gray text-sm font-body">|</span>
              <span className="text-genh-gray text-sm font-body">
                Dispatch Control
              </span>
            </div>

            <div className="flex items-center gap-4">
              <button
                onClick={loadData}
                disabled={isLoading}
                className="flex items-center gap-2 px-4 py-2 text-genh-gray hover:text-genh-gold transition-colors font-body text-sm"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 border border-genh-white/20 text-genh-gray hover:text-genh-white hover:border-genh-gold transition-all font-body text-sm"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 md:px-8 py-8">
        {/* Stats Grid */}
        {metrics && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatCard
              label="Total Dispatches"
              value={metrics.total_dispatches}
              icon={<Activity className="w-5 h-5" />}
              trend="All time"
            />
            <StatCard
              label="Pending"
              value={metrics.pending_count}
              icon={<Clock className="w-5 h-5" />}
              color="blue"
            />
            <StatCard
              label="Completed"
              value={metrics.completed_count}
              icon={<CheckCircle className="w-5 h-5" />}
              color="green"
            />
            <StatCard
              label="Emergencies"
              value={`${metrics.emergency_pct}%`}
              icon={<AlertCircle className="w-5 h-5" />}
              trend={`${metrics.emergency_count} total`}
              color="red"
            />
          </div>
        )}

        {/* Dispatches Table */}
        <div className="border border-genh-white/10 bg-genh-charcoal/20">
          <div className="px-6 py-4 border-b border-genh-white/10 flex items-center justify-between">
            <h2 className="font-display text-lg text-genh-white uppercase tracking-tight">
              Recent Dispatches
            </h2>
            <span className="text-genh-gray text-xs font-body">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-genh-white/10">
                  <th className="text-left px-6 py-3 text-label">Status</th>
                  <th className="text-left px-6 py-3 text-label">Customer</th>
                  <th className="text-left px-6 py-3 text-label">Issue</th>
                  <th className="text-left px-6 py-3 text-label">Urgency</th>
                  <th className="text-left px-6 py-3 text-label">Time</th>
                </tr>
              </thead>
              <tbody>
                {dispatches.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-genh-gray font-body">
                      {isLoading ? 'Loading...' : 'No dispatches found'}
                    </td>
                  </tr>
                ) : (
                  dispatches.map((dispatch) => (
                    <tr 
                      key={dispatch.dispatch_id}
                      className="border-b border-genh-white/5 hover:bg-genh-white/5 transition-colors"
                    >
                      <td className="px-6 py-4">
                        <StatusBadge status={dispatch.status} />
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4 text-genh-gray" />
                          <span className="text-genh-white font-body text-sm">
                            {dispatch.customer_name || 'Unknown'}
                          </span>
                        </div>
                        {dispatch.customer_phone && (
                          <div className="flex items-center gap-2 mt-1">
                            <Phone className="w-3 h-3 text-genh-gray" />
                            <span className="text-genh-gray font-body text-xs">
                              {dispatch.customer_phone}
                            </span>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-genh-white font-body text-sm max-w-xs truncate">
                          {dispatch.issue_summary || 'No description'}
                        </p>
                        {dispatch.address && (
                          <div className="flex items-center gap-2 mt-1">
                            <MapPin className="w-3 h-3 text-genh-gray" />
                            <span className="text-genh-gray font-body text-xs truncate max-w-xs">
                              {dispatch.address}
                            </span>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`font-body text-sm ${
                          dispatch.urgency?.toLowerCase() === 'emergency' 
                            ? 'text-red-400' 
                            : 'text-genh-gray'
                        }`}>
                          {dispatch.urgency || 'Standard'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-genh-gray font-body text-xs">
                          {new Date(dispatch.created_at).toLocaleString()}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={loadData}
            className="p-6 border border-genh-white/10 bg-genh-charcoal/20 hover:border-genh-gold/50 transition-all text-left group"
          >
            <RefreshCw className="w-6 h-6 text-genh-gold mb-3 group-hover:rotate-180 transition-transform duration-500" />
            <h3 className="font-display text-sm text-genh-white uppercase tracking-tight">
              Refresh Data
            </h3>
            <p className="text-genh-gray text-xs font-body mt-1">
              Reload dispatches and metrics
            </p>
          </button>

          <a
            href="/"
            className="p-6 border border-genh-white/10 bg-genh-charcoal/20 hover:border-genh-gold/50 transition-all text-left"
          >
            <TrendingUp className="w-6 h-6 text-genh-gold mb-3" />
            <h3 className="font-display text-sm text-genh-white uppercase tracking-tight">
              View Website
            </h3>
            <p className="text-genh-gray text-xs font-body mt-1">
              Return to customer-facing site
            </p>
          </a>

          <div className="p-6 border border-genh-white/10 bg-genh-charcoal/20">
            <Activity className="w-6 h-6 text-genh-gold mb-3" />
            <h3 className="font-display text-sm text-genh-white uppercase tracking-tight">
              System Status
            </h3>
            <p className="text-green-400 text-xs font-body mt-1 flex items-center gap-2">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              API Connected
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
