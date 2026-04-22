import { useEffect, useState } from 'react'
import { Cloud, Plus, TrendingUp } from 'lucide-react'
import { costsApi } from '../../api/client'
import MetricCard from '../shared/MetricCard'
import StatusBadge from '../shared/StatusBadge'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const CATEGORIES = ['compute', 'storage', 'transfer', 'database', 'other']
const CAT_COLORS: Record<string, string> = {
  compute: '#4f8ef7',
  storage: '#3ecf8e',
  transfer: '#f59e0b',
  database: '#a78bfa',
  other: '#6b7280',
}

interface Snapshot {
  id: string
  service_name: string
  monthly_cost: number
  savings_opportunity: number
  category: string
  notes: string
  recorded_at: string
}

interface Stats {
  total_monthly_cost: number
  total_savings_opportunity: number
  service_count: number
  by_category: Record<string, { cost: number; savings: number; count: number }>
  top_savings_opportunities: Snapshot[]
  savings_pct: number
}

function fmt(n: number) { return `$${n.toLocaleString('en-US', { maximumFractionDigits: 0 })}` }

export default function CloudCostPanel() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [snapshots, setSnapshots] = useState<Snapshot[]>([])
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ service_name: '', monthly_cost: '', savings_opportunity: '', category: 'compute', notes: '' })
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    const [st, sn] = await Promise.all([costsApi.stats(), costsApi.list()])
    setStats(st.data)
    setSnapshots(sn.data)
    setLoading(false)
  }

  useEffect(() => { refresh() }, [])

  const handleCreate = async () => {
    if (!form.service_name.trim() || !form.monthly_cost) return
    await costsApi.create({
      service_name: form.service_name,
      monthly_cost: parseFloat(form.monthly_cost),
      savings_opportunity: parseFloat(form.savings_opportunity || '0'),
      category: form.category,
      notes: form.notes,
    })
    setForm({ service_name: '', monthly_cost: '', savings_opportunity: '', category: 'compute', notes: '' })
    setShowCreate(false)
    refresh()
  }

  const chartData = stats
    ? Object.entries(stats.by_category).map(([cat, v]) => ({
        name: cat,
        cost: Math.round(v.cost),
        savings: Math.round(v.savings),
      }))
    : []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Cloud className="text-blue-400" size={22} />
          <div>
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Cloud Cost Optimizer</h2>
            <p className="text-xs text-[var(--text-secondary)]">FinOps auditor — track & eliminate waste</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-500/20 border border-blue-500/30 text-blue-400 text-sm hover:bg-blue-500/30 transition-colors"
        >
          <Plus size={14} /> Add Service
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard label="Monthly Spend" value={fmt(stats.total_monthly_cost)} accent="blue" />
          <MetricCard label="Savings Available" value={fmt(stats.total_savings_opportunity)} sub={`${stats.savings_pct}% of spend`} accent="green" />
          <MetricCard label="Services Tracked" value={stats.service_count} accent="purple" />
          <MetricCard label="Annual Waste" value={fmt(stats.total_savings_opportunity * 12)} sub="If optimizations applied" accent="amber" />
        </div>
      )}

      {/* Chart */}
      {chartData.length > 0 && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
          <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wide mb-4">Spend by Category</p>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={chartData} barSize={28}>
              <XAxis dataKey="name" tick={{ fill: '#8b8fa8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#8b8fa8', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}`} />
              <Tooltip
                contentStyle={{ background: '#22263a', border: '1px solid #2e3347', borderRadius: 8, color: '#e8eaf0' }}
                formatter={(v: number) => [`$${v.toLocaleString()}`, '']}
              />
              <Bar dataKey="cost" radius={[4, 4, 0, 0]}>
                {chartData.map(entry => (
                  <Cell key={entry.name} fill={CAT_COLORS[entry.name] ?? '#6b7280'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Top savings */}
      {stats && stats.top_savings_opportunities.length > 0 && (
        <div className="rounded-xl border border-green-500/30 bg-green-500/10 p-4 space-y-3">
          <div className="flex items-center gap-2 text-green-400 text-sm font-medium">
            <TrendingUp size={14} /> Top Savings Opportunities
          </div>
          {stats.top_savings_opportunities.map(s => (
            <div key={s.id} className="flex items-center justify-between text-sm">
              <span className="text-[var(--text-primary)]">{s.service_name}</span>
              <div className="flex items-center gap-3">
                <span className="text-[var(--text-secondary)]">{fmt(s.monthly_cost)}/mo</span>
                <span className="text-green-400 font-medium">save {fmt(s.savings_opportunity)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {showCreate && (
        <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-4 space-y-3">
          <p className="text-sm font-medium text-blue-400">Add Cost Snapshot</p>
          <div className="grid grid-cols-2 gap-3">
            <input
              className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
              placeholder="Service name"
              value={form.service_name}
              onChange={e => setForm(f => ({ ...f, service_name: e.target.value }))}
            />
            <select
              className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              value={form.category}
              onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
            >
              {CATEGORIES.map(c => <option key={c}>{c}</option>)}
            </select>
            <input
              type="number"
              className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              placeholder="Monthly cost ($)"
              value={form.monthly_cost}
              onChange={e => setForm(f => ({ ...f, monthly_cost: e.target.value }))}
            />
            <input
              type="number"
              className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              placeholder="Savings opportunity ($)"
              value={form.savings_opportunity}
              onChange={e => setForm(f => ({ ...f, savings_opportunity: e.target.value }))}
            />
          </div>
          <input
            className="w-full rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
            placeholder="Notes (optional)"
            value={form.notes}
            onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
          />
          <div className="flex gap-2">
            <button onClick={handleCreate} className="px-4 py-1.5 rounded-lg bg-blue-500/30 border border-blue-500/50 text-blue-300 text-sm hover:bg-blue-500/40 transition-colors">
              Add
            </button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-1.5 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] text-sm">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* All snapshots */}
      {!loading && snapshots.length > 0 && (
        <div className="space-y-2">
          {snapshots.map(s => (
            <div key={s.id} className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] px-4 py-3 flex items-center justify-between text-sm">
              <div className="flex items-center gap-3">
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ background: CAT_COLORS[s.category] ?? '#6b7280' }}
                />
                <span className="text-[var(--text-primary)]">{s.service_name}</span>
                <StatusBadge value={s.category} />
              </div>
              <div className="flex items-center gap-4 text-xs">
                <span className="text-[var(--text-secondary)]">{fmt(s.monthly_cost)}/mo</span>
                {s.savings_opportunity > 0 && (
                  <span className="text-green-400">↓ {fmt(s.savings_opportunity)} possible</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
