import { useEffect, useState } from 'react'
import { ArrowRight, Plus, Shield } from 'lucide-react'
import { migrationsApi } from '../../api/client'
import StatusBadge from '../shared/StatusBadge'
import MetricCard from '../shared/MetricCard'
import PhaseTracker from '../shared/PhaseTracker'

const PHASES = ['scope', 'risk', 'architecture', 'rollback', 'validation', 'execution', 'completed']
const RISK_LEVELS = ['low', 'medium', 'high', 'critical']

interface Migration {
  id: string
  name: string
  phase: string
  risk_level: string
  rollback_ready: number
  zero_downtime: number
  kill_switch: number
  validation_pct: number
  started_at: string | null
  completed_at: string | null
  created_at: string
}

interface Stats {
  active: number
  completed: number
  high_risk_active: number
  missing_rollback_plan: number
  phase_distribution: Record<string, number>
}

export default function MigrationPanel() {
  const [migrations, setMigrations] = useState<Migration[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [selected, setSelected] = useState<Migration | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', risk_level: 'medium' })
  const [advanceForm, setAdvanceForm] = useState({
    phase: '', rollback_ready: false, kill_switch: false, validation_pct: ''
  })
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    const [migs, st] = await Promise.all([migrationsApi.list(), migrationsApi.stats()])
    setMigrations(migs.data)
    setStats(st.data)
    setLoading(false)
  }

  useEffect(() => { refresh() }, [])

  const handleCreate = async () => {
    if (!form.name.trim()) return
    await migrationsApi.create(form)
    setForm({ name: '', risk_level: 'medium' })
    setShowCreate(false)
    refresh()
  }

  const handleAdvance = async (mig: Migration) => {
    if (!advanceForm.phase) return
    await migrationsApi.advancePhase(mig.id, {
      phase: advanceForm.phase,
      rollback_ready: advanceForm.rollback_ready,
      kill_switch: advanceForm.kill_switch,
      validation_pct: parseFloat(advanceForm.validation_pct || '0'),
    })
    const updated = await migrationsApi.get(mig.id)
    setSelected(updated.data)
    setAdvanceForm({ phase: '', rollback_ready: false, kill_switch: false, validation_pct: '' })
    refresh()
  }

  const nextPhase = (mig: Migration) => {
    const idx = PHASES.indexOf(mig.phase)
    return idx < PHASES.length - 1 ? PHASES[idx + 1] : null
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ArrowRight className="text-purple-400" size={22} />
          <div>
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Migration Command Center</h2>
            <p className="text-xs text-[var(--text-secondary)]">Migration strategist — zero-downtime enforcement</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-500/20 border border-purple-500/30 text-purple-400 text-sm hover:bg-purple-500/30 transition-colors"
        >
          <Plus size={14} /> New Migration
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard label="Active" value={stats.active} accent="purple" />
          <MetricCard label="High Risk" value={stats.high_risk_active} accent="red" sub="High + critical risk" />
          <MetricCard label="No Rollback Plan" value={stats.missing_rollback_plan} accent="amber" />
          <MetricCard label="Completed" value={stats.completed} accent="green" />
        </div>
      )}

      {showCreate && (
        <div className="rounded-xl border border-purple-500/30 bg-purple-500/10 p-4 space-y-3">
          <p className="text-sm font-medium text-purple-400">New Migration</p>
          <input
            className="w-full rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
            placeholder="Migration name (e.g. Postgres 14 → 16 upgrade)"
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          />
          <select
            className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
            value={form.risk_level}
            onChange={e => setForm(f => ({ ...f, risk_level: e.target.value }))}
          >
            {RISK_LEVELS.map(r => <option key={r}>{r}</option>)}
          </select>
          <div className="flex gap-2">
            <button onClick={handleCreate} className="px-4 py-1.5 rounded-lg bg-purple-500/30 border border-purple-500/50 text-purple-300 text-sm hover:bg-purple-500/40 transition-colors">Create</button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-1.5 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] text-sm">Cancel</button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center text-[var(--text-secondary)] py-8">Loading migrations...</div>
      ) : migrations.length === 0 ? (
        <div className="text-center text-[var(--text-secondary)] py-8 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          No migrations tracked.
        </div>
      ) : (
        <div className="space-y-2">
          {migrations.map(mig => (
            <div key={mig.id}>
              <button
                onClick={() => setSelected(selected?.id === mig.id ? null : mig)}
                className="w-full text-left rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-4 hover:border-purple-500/40 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <StatusBadge value={mig.risk_level} />
                    <span className="text-sm font-medium text-[var(--text-primary)]">{mig.name}</span>
                    {mig.rollback_ready ? (
                      <span className="text-xs text-green-400 flex items-center gap-1"><Shield size={10} /> rollback ready</span>
                    ) : (
                      <span className="text-xs text-amber-400">⚠ no rollback plan</span>
                    )}
                  </div>
                  {mig.validation_pct > 0 && (
                    <span className="text-xs text-blue-400">{mig.validation_pct.toFixed(0)}% validated</span>
                  )}
                </div>
                <PhaseTracker phases={PHASES} currentPhase={mig.phase} />
              </button>

              {selected?.id === mig.id && mig.phase !== 'completed' && (
                <div className="mt-1 rounded-xl border border-purple-500/30 bg-purple-500/10 p-4 space-y-3">
                  <p className="text-xs font-medium text-purple-400 uppercase tracking-wide">Advance Phase</p>
                  <div className="flex flex-wrap gap-3 items-center">
                    <select
                      className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--text-primary)]"
                      value={advanceForm.phase}
                      onChange={e => setAdvanceForm(f => ({ ...f, phase: e.target.value }))}
                    >
                      <option value="">Select next phase</option>
                      {nextPhase(mig) && <option value={nextPhase(mig)!}>{nextPhase(mig)}</option>}
                    </select>
                    <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                      <input type="checkbox" checked={advanceForm.rollback_ready}
                        onChange={e => setAdvanceForm(f => ({ ...f, rollback_ready: e.target.checked }))} />
                      Rollback ready
                    </label>
                    <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                      <input type="checkbox" checked={advanceForm.kill_switch}
                        onChange={e => setAdvanceForm(f => ({ ...f, kill_switch: e.target.checked }))} />
                      Kill switch armed
                    </label>
                    <input
                      type="number"
                      className="w-28 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--text-primary)]"
                      placeholder="Validation %"
                      value={advanceForm.validation_pct}
                      onChange={e => setAdvanceForm(f => ({ ...f, validation_pct: e.target.value }))}
                    />
                    <button onClick={() => handleAdvance(mig)} className="px-3 py-1.5 rounded-lg bg-purple-500/30 border border-purple-500/50 text-purple-300 text-sm hover:bg-purple-500/40 transition-colors">
                      Advance
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
