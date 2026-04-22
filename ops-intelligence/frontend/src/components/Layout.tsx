import { ReactNode, useEffect, useState } from 'react'
import { globalApi } from '../api/client'
import {
  AlertTriangle, TrendingDown, Cloud, GitBranch,
  Zap, ArrowRight, Link, Activity, DollarSign,
} from 'lucide-react'

const NAV = [
  { id: 'revenue',      label: 'Revenue',      icon: DollarSign,    color: 'text-green-400'  },
  { id: 'incidents',    label: 'Incidents',    icon: AlertTriangle, color: 'text-red-400'    },
  { id: 'debt',         label: 'Tech Debt',    icon: TrendingDown,  color: 'text-amber-400'  },
  { id: 'costs',        label: 'Cloud Costs',  icon: Cloud,         color: 'text-blue-400'   },
  { id: 'pipelines',    label: 'Pipelines',    icon: GitBranch,     color: 'text-green-400'  },
  { id: 'performance',  label: 'Performance',  icon: Zap,           color: 'text-amber-400'  },
  { id: 'migrations',   label: 'Migrations',   icon: ArrowRight,    color: 'text-purple-400' },
  { id: 'api',          label: 'API Contracts',icon: Link,          color: 'text-cyan-400'   },
]

interface Summary {
  incidents: { active: number; sev1: number }
  debt: { open_items: number; annual_interest: number }
  costs: { monthly_total: number; savings_available: number }
  pipelines: { total: number; failed: number }
  performance: { open_issues: number }
  migrations: { active: number; high_risk: number }
  api_governance: { contracts: number; breaking: number }
}

interface Props {
  active: string
  onNav: (id: string) => void
  children: ReactNode
}

export default function Layout({ active, onNav, children }: Props) {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [online, setOnline] = useState<boolean | null>(null)

  useEffect(() => {
    globalApi.health()
      .then(() => setOnline(true))
      .catch(() => setOnline(false))
    globalApi.summary()
      .then(r => setSummary(r.data))
      .catch(() => {})

    const t = setInterval(() => {
      globalApi.summary().then(r => setSummary(r.data)).catch(() => {})
    }, 30000)
    return () => clearInterval(t)
  }, [])

  function badge(id: string): number | null {
    if (!summary) return null
    if (id === 'incidents') return summary.incidents.active
    if (id === 'debt') return summary.debt.open_items
    if (id === 'pipelines') return summary.pipelines.failed
    if (id === 'performance') return summary.performance.open_issues
    if (id === 'migrations') return summary.migrations.high_risk
    if (id === 'api') return summary.api_governance.breaking
    return null
  }

  return (
    <div className="min-h-screen flex" style={{ background: 'var(--bg-base)' }}>
      {/* Sidebar */}
      <aside className="w-56 shrink-0 border-r border-[var(--border)] flex flex-col" style={{ background: 'var(--bg-panel)' }}>
        {/* Logo */}
        <div className="px-4 py-5 border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <Activity size={18} className="text-blue-400" />
            <span className="text-sm font-semibold text-[var(--text-primary)]">Ops Intelligence</span>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-0.5">ReliantAI Platform</p>
        </div>

        {/* Status */}
        <div className="px-4 py-2 border-b border-[var(--border)]">
          <div className="flex items-center gap-2 text-xs">
            <span className={`w-2 h-2 rounded-full ${online === true ? 'bg-green-400' : online === false ? 'bg-red-400' : 'bg-gray-400'}`} />
            <span className="text-[var(--text-secondary)]">
              {online === null ? 'Connecting...' : online ? 'Backend online' : 'Backend offline'}
            </span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-2 space-y-0.5">
          {NAV.map(item => {
            const Icon = item.icon
            const b = badge(item.id)
            const isActive = active === item.id
            return (
              <button
                key={item.id}
                onClick={() => onNav(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-[var(--bg-card)] text-[var(--text-primary)]'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--bg-card)] hover:text-[var(--text-primary)]'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Icon size={15} className={isActive ? item.color : 'text-[var(--text-secondary)]'} />
                  {item.label}
                </div>
                {b !== null && b > 0 && (
                  <span className="text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/30 rounded-full px-1.5 py-0.5">
                    {b}
                  </span>
                )}
              </button>
            )
          })}
        </nav>

        {/* Summary footer */}
        {summary && (
          <div className="p-4 border-t border-[var(--border)] space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-secondary)]">Monthly cloud</span>
              <span className="text-blue-400">${summary.costs.monthly_total.toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-secondary)]">Savings avail.</span>
              <span className="text-green-400">${summary.costs.savings_available.toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-secondary)]">Debt interest/yr</span>
              <span className="text-amber-400">${summary.debt.annual_interest.toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
            </div>
          </div>
        )}
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto p-6">
        {children}
      </main>
    </div>
  )
}
