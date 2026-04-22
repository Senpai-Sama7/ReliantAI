import { useEffect, useState } from 'react'
import { TrendingDown, Plus, DollarSign } from 'lucide-react'
import { debtApi } from '../../api/client'
import StatusBadge from '../shared/StatusBadge'
import MetricCard from '../shared/MetricCard'

interface DebtItem {
  id: string
  name: string
  description: string
  interest_per_year: number
  principal_cost: number
  roi: number
  status: string
  created_at: string
}

interface Stats {
  open_items: number
  total_annual_interest: number
  total_principal: number
  avg_roi_pct: number
  payback_months: number | null
}

function fmt(n: number) {
  return n >= 1000 ? `$${(n / 1000).toFixed(1)}k` : `$${n.toFixed(0)}`
}

function roiColor(roi: number) {
  if (roi >= 200) return 'text-green-400'
  if (roi >= 100) return 'text-amber-400'
  return 'text-red-400'
}

export default function DebtROIPanel() {
  const [items, setItems] = useState<DebtItem[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', interest_per_year: '', principal_cost: '' })
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    const [its, st] = await Promise.all([debtApi.list(), debtApi.stats()])
    setItems(its.data)
    setStats(st.data)
    setLoading(false)
  }

  useEffect(() => { refresh() }, [])

  const handleCreate = async () => {
    if (!form.name.trim() || !form.interest_per_year || !form.principal_cost) return
    await debtApi.create({
      name: form.name,
      description: form.description,
      interest_per_year: parseFloat(form.interest_per_year),
      principal_cost: parseFloat(form.principal_cost),
    })
    setForm({ name: '', description: '', interest_per_year: '', principal_cost: '' })
    setShowCreate(false)
    refresh()
  }

  const updateStatus = async (id: string, status: string) => {
    await debtApi.updateStatus(id, status)
    refresh()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <TrendingDown className="text-amber-400" size={22} />
          <div>
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Tech Debt ROI Board</h2>
            <p className="text-xs text-[var(--text-secondary)]">Sorted by ROI — highest first</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-400 text-sm hover:bg-amber-500/30 transition-colors"
        >
          <Plus size={14} /> Add Debt Item
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard label="Open Items" value={stats.open_items} accent="amber" />
          <MetricCard label="Annual Interest" value={fmt(stats.total_annual_interest)} sub="Cost if not fixed" accent="red" />
          <MetricCard label="Payback Cost" value={fmt(stats.total_principal)} sub="To fix everything" accent="blue" />
          <MetricCard
            label="Avg ROI"
            value={`${stats.avg_roi_pct.toFixed(0)}%`}
            sub={stats.payback_months ? `${stats.payback_months}mo payback` : undefined}
            accent={stats.avg_roi_pct >= 100 ? 'green' : 'amber'}
          />
        </div>
      )}

      {showCreate && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 space-y-3">
          <p className="text-sm font-medium text-amber-400">Add Debt Item</p>
          <input
            className="w-full rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
            placeholder="Debt name (e.g. Duplicated auth code in 3 places)"
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          />
          <input
            className="w-full rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
            placeholder="Description"
            value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
          />
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-[var(--text-secondary)] mb-1 block">Annual interest ($) — cost if NOT fixed</label>
              <input
                type="number"
                className="w-full rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
                placeholder="e.g. 12000"
                value={form.interest_per_year}
                onChange={e => setForm(f => ({ ...f, interest_per_year: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-xs text-[var(--text-secondary)] mb-1 block">Principal ($) — cost to fix</label>
              <input
                type="number"
                className="w-full rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
                placeholder="e.g. 8000"
                value={form.principal_cost}
                onChange={e => setForm(f => ({ ...f, principal_cost: e.target.value }))}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleCreate} className="px-4 py-1.5 rounded-lg bg-amber-500/30 border border-amber-500/50 text-amber-300 text-sm hover:bg-amber-500/40 transition-colors">
              Add Item
            </button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-1.5 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] text-sm">
              Cancel
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center text-[var(--text-secondary)] py-8">Loading debt items...</div>
      ) : items.length === 0 ? (
        <div className="text-center text-[var(--text-secondary)] py-8 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          No debt items tracked yet.
        </div>
      ) : (
        <div className="space-y-2">
          {items.map((item, i) => (
            <div key={item.id} className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <span className="text-xs text-[var(--text-secondary)] w-5 pt-0.5">#{i + 1}</span>
                  <div>
                    <p className="text-sm font-medium text-[var(--text-primary)]">{item.name}</p>
                    {item.description && (
                      <p className="text-xs text-[var(--text-secondary)] mt-0.5">{item.description}</p>
                    )}
                    <div className="flex items-center gap-3 mt-2 text-xs">
                      <span className="text-red-400">Interest: {fmt(item.interest_per_year)}/yr</span>
                      <span className="text-blue-400">Principal: {fmt(item.principal_cost)}</span>
                      <span className={`font-bold ${roiColor(item.roi)}`}>ROI: {item.roi.toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <StatusBadge value={item.status} />
                  {item.status === 'open' && (
                    <button
                      onClick={() => updateStatus(item.id, 'in_progress')}
                      className="text-xs px-2 py-0.5 rounded border border-blue-500/30 text-blue-400 hover:bg-blue-500/20 transition-colors"
                    >
                      Start
                    </button>
                  )}
                  {item.status === 'in_progress' && (
                    <button
                      onClick={() => updateStatus(item.id, 'resolved')}
                      className="text-xs px-2 py-0.5 rounded border border-green-500/30 text-green-400 hover:bg-green-500/20 transition-colors"
                    >
                      Done
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
