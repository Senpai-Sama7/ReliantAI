import { useEffect, useState } from 'react'
import { Zap, Plus } from 'lucide-react'
import { performanceApi } from '../../api/client'
import StatusBadge from '../shared/StatusBadge'
import MetricCard from '../shared/MetricCard'

interface PerfItem {
  id: string
  service: string
  metric: string
  current_value: number
  baseline_value: number
  unit: string
  bottleneck: string
  root_cause: string | null
  status: string
  created_at: string
}

interface Stats {
  open: number
  resolved: number
  worst_offenders: PerfItem[]
  services_affected: string[]
}

function degradationPct(item: PerfItem) {
  if (item.baseline_value === 0) return 0
  return Math.abs(item.current_value - item.baseline_value) / item.baseline_value * 100
}

export default function PerformancePanel() {
  const [items, setItems] = useState<PerfItem[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [resolveId, setResolveId] = useState<string | null>(null)
  const [resolveNote, setResolveNote] = useState('')
  const [form, setForm] = useState({
    service: '', metric: '', current_value: '', baseline_value: '', unit: 'ms', bottleneck: ''
  })
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    const [its, st] = await Promise.all([performanceApi.list(), performanceApi.stats()])
    setItems(its.data)
    setStats(st.data)
    setLoading(false)
  }

  useEffect(() => { refresh() }, [])

  const handleCreate = async () => {
    if (!form.service || !form.metric || !form.current_value || !form.baseline_value) return
    await performanceApi.create({
      service: form.service,
      metric: form.metric,
      current_value: parseFloat(form.current_value),
      baseline_value: parseFloat(form.baseline_value),
      unit: form.unit,
      bottleneck: form.bottleneck,
    })
    setForm({ service: '', metric: '', current_value: '', baseline_value: '', unit: 'ms', bottleneck: '' })
    setShowCreate(false)
    refresh()
  }

  const handleResolve = async (id: string) => {
    if (!resolveNote.trim()) return
    await performanceApi.resolve(id, resolveNote)
    setResolveId(null)
    setResolveNote('')
    refresh()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Zap className="text-amber-400" size={22} />
          <div>
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Performance Registry</h2>
            <p className="text-xs text-[var(--text-secondary)]">Performance surgeon — bottleneck tracking</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-400 text-sm hover:bg-amber-500/30 transition-colors"
        >
          <Plus size={14} /> Log Issue
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-3 gap-3">
          <MetricCard label="Open Issues" value={stats.open} accent="amber" />
          <MetricCard label="Services Affected" value={stats.services_affected.length} accent="red" />
          <MetricCard label="Resolved" value={stats.resolved} accent="green" />
        </div>
      )}

      {stats && stats.worst_offenders.length > 0 && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 space-y-2">
          <p className="text-sm font-medium text-red-400 mb-2">Worst Offenders</p>
          {stats.worst_offenders.map(item => (
            <div key={item.id} className="flex items-center justify-between text-sm">
              <span className="text-[var(--text-primary)]">{item.service} — {item.metric}</span>
              <span className="text-red-400 font-medium">+{degradationPct(item).toFixed(0)}% degraded</span>
            </div>
          ))}
        </div>
      )}

      {showCreate && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 space-y-3">
          <p className="text-sm font-medium text-amber-400">Log Performance Issue</p>
          <div className="grid grid-cols-2 gap-3">
            <input className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
              placeholder="Service name" value={form.service} onChange={e => setForm(f => ({ ...f, service: e.target.value }))} />
            <input className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
              placeholder="Metric (e.g. p99_latency)" value={form.metric} onChange={e => setForm(f => ({ ...f, metric: e.target.value }))} />
            <input type="number" className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              placeholder="Current value" value={form.current_value} onChange={e => setForm(f => ({ ...f, current_value: e.target.value }))} />
            <input type="number" className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              placeholder="Baseline value" value={form.baseline_value} onChange={e => setForm(f => ({ ...f, baseline_value: e.target.value }))} />
            <input className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              placeholder="Unit (ms, rps, MB...)" value={form.unit} onChange={e => setForm(f => ({ ...f, unit: e.target.value }))} />
            <input className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
              placeholder="Suspected bottleneck" value={form.bottleneck} onChange={e => setForm(f => ({ ...f, bottleneck: e.target.value }))} />
          </div>
          <div className="flex gap-2">
            <button onClick={handleCreate} className="px-4 py-1.5 rounded-lg bg-amber-500/30 border border-amber-500/50 text-amber-300 text-sm hover:bg-amber-500/40 transition-colors">Log</button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-1.5 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] text-sm">Cancel</button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center text-[var(--text-secondary)] py-8">Loading performance data...</div>
      ) : items.length === 0 ? (
        <div className="text-center text-[var(--text-secondary)] py-8 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          No performance issues tracked.
        </div>
      ) : (
        <div className="space-y-2">
          {items.map(item => (
            <div key={item.id} className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-4 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <StatusBadge value={item.status} />
                  <span className="text-sm font-medium text-[var(--text-primary)]">{item.service}</span>
                  <span className="text-xs text-[var(--text-secondary)]">— {item.metric}</span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <span className="text-[var(--text-secondary)]">{item.baseline_value}{item.unit}</span>
                  <span className="text-red-400 font-medium">{item.current_value}{item.unit}</span>
                  <span className="text-amber-400 text-xs">+{degradationPct(item).toFixed(0)}%</span>
                </div>
              </div>
              {item.bottleneck && (
                <p className="text-xs text-[var(--text-secondary)]">Bottleneck: {item.bottleneck}</p>
              )}
              {item.root_cause && (
                <p className="text-xs text-green-400">Root cause: {item.root_cause}</p>
              )}
              {item.status === 'open' && (
                resolveId === item.id ? (
                  <div className="flex gap-2 mt-2">
                    <input
                      className="flex-1 rounded-lg bg-[var(--bg-base)] border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
                      placeholder="Root cause..."
                      value={resolveNote}
                      onChange={e => setResolveNote(e.target.value)}
                    />
                    <button onClick={() => handleResolve(item.id)} className="px-3 py-1.5 rounded-lg bg-green-500/30 border border-green-500/50 text-green-300 text-sm">Resolve</button>
                    <button onClick={() => setResolveId(null)} className="px-3 py-1.5 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] text-sm">Cancel</button>
                  </div>
                ) : (
                  <button onClick={() => setResolveId(item.id)} className="text-xs px-2 py-0.5 rounded border border-green-500/30 text-green-400 hover:bg-green-500/20 transition-colors">
                    Mark resolved
                  </button>
                )
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
