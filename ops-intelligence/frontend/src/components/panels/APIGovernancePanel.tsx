import { useEffect, useState } from 'react'
import { Link, Plus, CheckCircle, XCircle } from 'lucide-react'
import { apiGovernanceApi } from '../../api/client'
import StatusBadge from '../shared/StatusBadge'
import MetricCard from '../shared/MetricCard'

const METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

interface Contract {
  id: string
  endpoint: string
  version: string
  method: string
  service: string
  breaking_changes: number
  doc_complete: number
  consistency_score: number
  last_checked: string | null
  notes: string
  created_at: string
}

interface Stats {
  total_contracts: number
  services: string[]
  breaking_changes_count: number
  undocumented_count: number
  low_consistency_count: number
  avg_consistency_score: number
  health: string
}

export default function APIGovernancePanel() {
  const [contracts, setContracts] = useState<Contract[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [checkId, setCheckId] = useState<string | null>(null)
  const [checkForm, setCheckForm] = useState({ breaking_changes: '0', doc_complete: false, consistency_score: '100' })
  const [form, setForm] = useState({ endpoint: '', version: 'v1', method: 'GET', service: '', notes: '' })
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    const [ct, st] = await Promise.all([apiGovernanceApi.list(), apiGovernanceApi.stats()])
    setContracts(ct.data)
    setStats(st.data)
    setLoading(false)
  }

  useEffect(() => { refresh() }, [])

  const handleCreate = async () => {
    if (!form.endpoint.trim() || !form.service.trim()) return
    await apiGovernanceApi.create(form)
    setForm({ endpoint: '', version: 'v1', method: 'GET', service: '', notes: '' })
    setShowCreate(false)
    refresh()
  }

  const handleCheck = async (id: string) => {
    await apiGovernanceApi.check(id, {
      breaking_changes: parseInt(checkForm.breaking_changes),
      doc_complete: checkForm.doc_complete,
      consistency_score: parseFloat(checkForm.consistency_score),
    })
    setCheckId(null)
    setCheckForm({ breaking_changes: '0', doc_complete: false, consistency_score: '100' })
    refresh()
  }

  const methodColors: Record<string, string> = {
    GET: 'text-green-400', POST: 'text-blue-400', PUT: 'text-amber-400',
    PATCH: 'text-purple-400', DELETE: 'text-red-400',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link className="text-cyan-400" size={22} />
          <div>
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">API Governance Portal</h2>
            <p className="text-xs text-[var(--text-secondary)]">API contract enforcer — prevent breaking changes</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 text-sm hover:bg-cyan-500/30 transition-colors"
        >
          <Plus size={14} /> Register Contract
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard label="Total Contracts" value={stats.total_contracts} accent="blue" />
          <MetricCard
            label="Breaking Changes"
            value={stats.breaking_changes_count}
            accent={stats.breaking_changes_count > 0 ? 'red' : 'green'}
          />
          <MetricCard label="Undocumented" value={stats.undocumented_count} accent="amber" />
          <MetricCard
            label="Avg Consistency"
            value={`${stats.avg_consistency_score.toFixed(0)}%`}
            accent={stats.avg_consistency_score >= 90 ? 'green' : 'amber'}
          />
        </div>
      )}

      {stats && (
        <div className={`rounded-xl border p-3 flex items-center gap-3 ${
          stats.health === 'green'
            ? 'border-green-500/30 bg-green-500/10'
            : stats.health === 'yellow'
            ? 'border-amber-500/30 bg-amber-500/10'
            : 'border-red-500/30 bg-red-500/10'
        }`}>
          {stats.health === 'green'
            ? <CheckCircle size={16} className="text-green-400" />
            : <XCircle size={16} className="text-red-400" />}
          <div className="text-sm">
            <span className={stats.health === 'green' ? 'text-green-400' : stats.health === 'yellow' ? 'text-amber-400' : 'text-red-400'}>
              API Health: {stats.health.toUpperCase()}
            </span>
            <span className="text-[var(--text-secondary)] ml-2">
              {stats.services.length} services — {stats.total_contracts} contracts tracked
            </span>
          </div>
        </div>
      )}

      {showCreate && (
        <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-4 space-y-3">
          <p className="text-sm font-medium text-cyan-400">Register API Contract</p>
          <div className="grid grid-cols-2 gap-3">
            <input className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
              placeholder="/api/endpoint" value={form.endpoint} onChange={e => setForm(f => ({ ...f, endpoint: e.target.value }))} />
            <input className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
              placeholder="Service name" value={form.service} onChange={e => setForm(f => ({ ...f, service: e.target.value }))} />
            <select className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              value={form.method} onChange={e => setForm(f => ({ ...f, method: e.target.value }))}>
              {METHODS.map(m => <option key={m}>{m}</option>)}
            </select>
            <input className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              placeholder="Version (v1, v2...)" value={form.version} onChange={e => setForm(f => ({ ...f, version: e.target.value }))} />
          </div>
          <input className="w-full rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
            placeholder="Notes" value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
          <div className="flex gap-2">
            <button onClick={handleCreate} className="px-4 py-1.5 rounded-lg bg-cyan-500/30 border border-cyan-500/50 text-cyan-300 text-sm hover:bg-cyan-500/40 transition-colors">Register</button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-1.5 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] text-sm">Cancel</button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center text-[var(--text-secondary)] py-8">Loading contracts...</div>
      ) : contracts.length === 0 ? (
        <div className="text-center text-[var(--text-secondary)] py-8 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          No API contracts registered.
        </div>
      ) : (
        <div className="space-y-2">
          {contracts.map(c => (
            <div key={c.id} className={`rounded-xl border bg-[var(--bg-card)] p-4 space-y-2 ${
              c.breaking_changes > 0 ? 'border-red-500/40' : 'border-[var(--border)]'
            }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-bold ${methodColors[c.method] ?? 'text-[var(--text-secondary)]'}`}>{c.method}</span>
                  <span className="text-sm font-mono text-[var(--text-primary)]">{c.endpoint}</span>
                  <StatusBadge value={c.version} />
                  <span className="text-xs text-[var(--text-secondary)]">{c.service}</span>
                </div>
                <div className="flex items-center gap-2">
                  {c.doc_complete
                    ? <CheckCircle size={14} className="text-green-400" title="Documented" />
                    : <XCircle size={14} className="text-amber-400" title="Undocumented" />}
                  <span className={`text-xs font-medium ${c.consistency_score >= 90 ? 'text-green-400' : 'text-amber-400'}`}>
                    {c.consistency_score.toFixed(0)}%
                  </span>
                  {c.breaking_changes > 0 && (
                    <span className="text-xs text-red-400 font-medium">{c.breaking_changes} breaking</span>
                  )}
                </div>
              </div>
              {c.notes && <p className="text-xs text-[var(--text-secondary)]">{c.notes}</p>}
              <div className="flex items-center gap-2">
                {checkId === c.id ? (
                  <div className="flex flex-wrap gap-2 items-center">
                    <input type="number" className="w-24 rounded bg-[var(--bg-base)] border border-[var(--border)] px-2 py-1 text-xs text-[var(--text-primary)]"
                      placeholder="Breaking changes" value={checkForm.breaking_changes}
                      onChange={e => setCheckForm(f => ({ ...f, breaking_changes: e.target.value }))} />
                    <label className="flex items-center gap-1 text-xs text-[var(--text-secondary)]">
                      <input type="checkbox" checked={checkForm.doc_complete}
                        onChange={e => setCheckForm(f => ({ ...f, doc_complete: e.target.checked }))} />
                      Documented
                    </label>
                    <input type="number" className="w-24 rounded bg-[var(--bg-base)] border border-[var(--border)] px-2 py-1 text-xs text-[var(--text-primary)]"
                      placeholder="Consistency %" value={checkForm.consistency_score}
                      onChange={e => setCheckForm(f => ({ ...f, consistency_score: e.target.value }))} />
                    <button onClick={() => handleCheck(c.id)} className="px-2 py-1 rounded border border-cyan-500/40 text-cyan-400 text-xs hover:bg-cyan-500/20">Save</button>
                    <button onClick={() => setCheckId(null)} className="px-2 py-1 rounded border border-[var(--border)] text-[var(--text-secondary)] text-xs">Cancel</button>
                  </div>
                ) : (
                  <button onClick={() => setCheckId(c.id)} className="text-xs px-2 py-0.5 rounded border border-[var(--border)] text-[var(--text-secondary)] hover:border-cyan-500/40 hover:text-cyan-400 transition-colors">
                    Run check
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
