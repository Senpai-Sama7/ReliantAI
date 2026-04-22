import { useEffect, useState } from 'react'
import { GitBranch, Plus } from 'lucide-react'
import { pipelinesApi } from '../../api/client'
import StatusBadge from '../shared/StatusBadge'
import MetricCard from '../shared/MetricCard'

const PHASES = ['ingestion', 'transformation', 'delivery', 'monitoring']
const STATUSES = ['healthy', 'degraded', 'failed', 'unknown']

interface Pipeline {
  id: string
  name: string
  status: string
  quality_score: number
  cost_per_record: number
  records_per_day: number
  sla_minutes: number
  phase: string
  last_run: string | null
}

interface Stats {
  total: number
  healthy: number
  degraded: number
  failed: number
  avg_quality_score: number
  sla_breaches: Pipeline[]
}

export default function PipelinePanel() {
  const [pipelines, setPipelines] = useState<Pipeline[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({
    name: '', status: 'healthy', quality_score: '100',
    cost_per_record: '0', records_per_day: '0', sla_minutes: '60', phase: 'ingestion'
  })
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    const [pl, st] = await Promise.all([pipelinesApi.list(), pipelinesApi.stats()])
    setPipelines(pl.data)
    setStats(st.data)
    setLoading(false)
  }

  useEffect(() => { refresh() }, [])

  const handleCreate = async () => {
    if (!form.name.trim()) return
    await pipelinesApi.create({
      name: form.name,
      status: form.status,
      quality_score: parseFloat(form.quality_score),
      cost_per_record: parseFloat(form.cost_per_record),
      records_per_day: parseInt(form.records_per_day),
      sla_minutes: parseInt(form.sla_minutes),
      phase: form.phase,
    })
    setForm({ name: '', status: 'healthy', quality_score: '100', cost_per_record: '0', records_per_day: '0', sla_minutes: '60', phase: 'ingestion' })
    setShowCreate(false)
    refresh()
  }

  function qualityColor(score: number) {
    if (score >= 99) return 'text-green-400'
    if (score >= 95) return 'text-amber-400'
    return 'text-red-400'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <GitBranch className="text-green-400" size={22} />
          <div>
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Pipeline Health Map</h2>
            <p className="text-xs text-[var(--text-secondary)]">Data pipeline architect — quality & cost monitoring</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-green-500/20 border border-green-500/30 text-green-400 text-sm hover:bg-green-500/30 transition-colors"
        >
          <Plus size={14} /> Register Pipeline
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard label="Total Pipelines" value={stats.total} accent="blue" />
          <MetricCard label="Healthy" value={stats.healthy} accent="green" />
          <MetricCard label="Degraded / Failed" value={`${stats.degraded} / ${stats.failed}`} accent="amber" />
          <MetricCard label="Avg Quality" value={`${stats.avg_quality_score}%`} accent={stats.avg_quality_score >= 99 ? 'green' : 'amber'} />
        </div>
      )}

      {stats && stats.sla_breaches.length > 0 && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
          <p className="text-sm font-medium text-amber-400 mb-2">SLA Breaches (quality &lt; 95%)</p>
          {stats.sla_breaches.map(p => (
            <div key={p.id} className="flex items-center justify-between text-sm py-1">
              <span className="text-[var(--text-primary)]">{p.name}</span>
              <span className="text-red-400">{p.quality_score.toFixed(1)}%</span>
            </div>
          ))}
        </div>
      )}

      {showCreate && (
        <div className="rounded-xl border border-green-500/30 bg-green-500/10 p-4 space-y-3">
          <p className="text-sm font-medium text-green-400">Register Pipeline</p>
          <input
            className="w-full rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
            placeholder="Pipeline name"
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          />
          <div className="grid grid-cols-3 gap-3">
            <select className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
              {STATUSES.map(s => <option key={s}>{s}</option>)}
            </select>
            <select className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              value={form.phase} onChange={e => setForm(f => ({ ...f, phase: e.target.value }))}>
              {PHASES.map(p => <option key={p}>{p}</option>)}
            </select>
            <input type="number" className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              placeholder="Quality score %" value={form.quality_score} onChange={e => setForm(f => ({ ...f, quality_score: e.target.value }))} />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <input type="number" className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              placeholder="Cost per record ($)" value={form.cost_per_record} onChange={e => setForm(f => ({ ...f, cost_per_record: e.target.value }))} />
            <input type="number" className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              placeholder="Records/day" value={form.records_per_day} onChange={e => setForm(f => ({ ...f, records_per_day: e.target.value }))} />
            <input type="number" className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              placeholder="SLA (minutes)" value={form.sla_minutes} onChange={e => setForm(f => ({ ...f, sla_minutes: e.target.value }))} />
          </div>
          <div className="flex gap-2">
            <button onClick={handleCreate} className="px-4 py-1.5 rounded-lg bg-green-500/30 border border-green-500/50 text-green-300 text-sm hover:bg-green-500/40 transition-colors">Add</button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-1.5 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] text-sm">Cancel</button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center text-[var(--text-secondary)] py-8">Loading pipelines...</div>
      ) : pipelines.length === 0 ? (
        <div className="text-center text-[var(--text-secondary)] py-8 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          No pipelines registered.
        </div>
      ) : (
        <div className="space-y-2">
          {pipelines.map(p => (
            <div key={p.id} className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <StatusBadge value={p.status} />
                  <span className="text-sm font-medium text-[var(--text-primary)]">{p.name}</span>
                  <StatusBadge value={p.phase} />
                </div>
                <span className={`text-sm font-bold ${qualityColor(p.quality_score)}`}>
                  {p.quality_score.toFixed(1)}%
                </span>
              </div>
              <div className="flex gap-4 text-xs text-[var(--text-secondary)]">
                <span>{p.records_per_day.toLocaleString()} records/day</span>
                {p.cost_per_record > 0 && <span>${p.cost_per_record.toFixed(4)}/record</span>}
                <span>SLA: {p.sla_minutes}min</span>
                {p.last_run && <span>Last: {new Date(p.last_run).toLocaleString()}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
