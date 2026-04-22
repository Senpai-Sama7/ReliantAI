import { useEffect, useState } from 'react'
import { AlertTriangle, Plus, ChevronRight } from 'lucide-react'
import { incidentsApi } from '../../api/client'
import StatusBadge from '../shared/StatusBadge'
import MetricCard from '../shared/MetricCard'
import PhaseTracker from '../shared/PhaseTracker'

const PHASES = ['triage', 'evidence', 'containment', 'investigation', 'mitigation', 'stabilization']
const SEVERITIES = ['SEV-1', 'SEV-2', 'SEV-3', 'SEV-4']

interface Incident {
  id: string
  title: string
  severity: string
  phase: string
  status: string
  blast_radius: string
  root_cause: string | null
  timeline: Array<{ phase: string; ts: string; note: string }>
  created_at: string
  resolved_at: string | null
}

interface Stats { active_count: number; resolved_count: number; sev1_active: number }

export default function IncidentPanel() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [selected, setSelected] = useState<Incident | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ title: '', severity: 'SEV-2', blast_radius: '' })
  const [phaseNote, setPhaseNote] = useState('')
  const [resolveNote, setResolveNote] = useState('')
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    const [inc, st] = await Promise.all([incidentsApi.list(), incidentsApi.stats()])
    setIncidents(inc.data)
    setStats(st.data)
    setLoading(false)
  }

  useEffect(() => { refresh() }, [])

  const handleCreate = async () => {
    if (!form.title.trim()) return
    await incidentsApi.create(form)
    setForm({ title: '', severity: 'SEV-2', blast_radius: '' })
    setShowCreate(false)
    refresh()
  }

  const nextPhase = (inc: Incident) => {
    const idx = PHASES.indexOf(inc.phase)
    return idx < PHASES.length - 1 ? PHASES[idx + 1] : null
  }

  const handleAdvance = async (inc: Incident) => {
    const next = nextPhase(inc)
    if (!next) return
    await incidentsApi.advancePhase(inc.id, next, phaseNote)
    setPhaseNote('')
    const updated = await incidentsApi.get(inc.id)
    setSelected(updated.data)
    refresh()
  }

  const handleResolve = async (inc: Incident) => {
    if (!resolveNote.trim()) return
    await incidentsApi.resolve(inc.id, resolveNote)
    setResolveNote('')
    setSelected(null)
    refresh()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AlertTriangle className="text-red-400" size={22} />
          <div>
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Incident War Room</h2>
            <p className="text-xs text-[var(--text-secondary)]">6-phase incident commander protocol</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/20 border border-red-500/30 text-red-400 text-sm hover:bg-red-500/30 transition-colors"
        >
          <Plus size={14} /> New Incident
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-3">
          <MetricCard label="Active" value={stats.active_count} accent="red" />
          <MetricCard label="SEV-1 Active" value={stats.sev1_active} accent="red" sub="Critical severity" />
          <MetricCard label="Resolved" value={stats.resolved_count} accent="green" />
        </div>
      )}

      {/* Create form */}
      {showCreate && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 space-y-3">
          <p className="text-sm font-medium text-amber-400">Open New Incident</p>
          <input
            className="w-full rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
            placeholder="Incident title (e.g. Checkout API returning 500s)"
            value={form.title}
            onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
          />
          <div className="flex gap-3">
            <select
              className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              value={form.severity}
              onChange={e => setForm(f => ({ ...f, severity: e.target.value }))}
            >
              {SEVERITIES.map(s => <option key={s}>{s}</option>)}
            </select>
            <input
              className="flex-1 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
              placeholder="Blast radius (who is affected?)"
              value={form.blast_radius}
              onChange={e => setForm(f => ({ ...f, blast_radius: e.target.value }))}
            />
          </div>
          <div className="flex gap-2">
            <button onClick={handleCreate} className="px-4 py-1.5 rounded-lg bg-red-500/30 border border-red-500/50 text-red-300 text-sm hover:bg-red-500/40 transition-colors">
              Open Incident
            </button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-1.5 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] text-sm">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Incident list */}
      {loading ? (
        <div className="text-center text-[var(--text-secondary)] py-8">Loading incidents...</div>
      ) : incidents.length === 0 ? (
        <div className="text-center text-[var(--text-secondary)] py-8 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          No incidents. System healthy.
        </div>
      ) : (
        <div className="space-y-2">
          {incidents.map(inc => (
            <button
              key={inc.id}
              onClick={() => setSelected(selected?.id === inc.id ? null : inc)}
              className="w-full text-left rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-4 hover:border-blue-500/40 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <StatusBadge value={inc.severity} />
                  <StatusBadge value={inc.status} />
                  <span className="text-sm font-medium text-[var(--text-primary)]">{inc.title}</span>
                </div>
                <ChevronRight size={14} className="text-[var(--text-secondary)]" />
              </div>
              <PhaseTracker phases={PHASES} currentPhase={inc.phase} />
            </button>
          ))}
        </div>
      )}

      {/* Detail panel */}
      {selected && (
        <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-5 space-y-4">
          <div className="flex items-center gap-3">
            <StatusBadge value={selected.severity} size="md" />
            <h3 className="font-semibold text-[var(--text-primary)]">{selected.title}</h3>
          </div>

          <PhaseTracker phases={PHASES} currentPhase={selected.phase} />

          {selected.blast_radius && (
            <p className="text-sm text-[var(--text-secondary)]">
              <span className="text-amber-400">Blast radius:</span> {selected.blast_radius}
            </p>
          )}

          {/* Timeline */}
          <div className="space-y-2">
            <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wide">Timeline</p>
            {selected.timeline.map((t, i) => (
              <div key={i} className="flex gap-3 text-sm">
                <span className="text-[var(--text-secondary)] shrink-0">{new Date(t.ts).toLocaleTimeString()}</span>
                <StatusBadge value={t.phase} />
                <span className="text-[var(--text-secondary)]">{t.note}</span>
              </div>
            ))}
          </div>

          {/* Actions */}
          {selected.status === 'active' && (
            <div className="space-y-3 pt-2 border-t border-[var(--border)]">
              {nextPhase(selected) && (
                <div className="flex gap-2">
                  <input
                    className="flex-1 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
                    placeholder={`Note for ${nextPhase(selected)} phase...`}
                    value={phaseNote}
                    onChange={e => setPhaseNote(e.target.value)}
                  />
                  <button
                    onClick={() => handleAdvance(selected)}
                    className="px-3 py-1.5 rounded-lg bg-blue-500/30 border border-blue-500/50 text-blue-300 text-sm hover:bg-blue-500/40 transition-colors whitespace-nowrap"
                  >
                    → {nextPhase(selected)}
                  </button>
                </div>
              )}
              <div className="flex gap-2">
                <input
                  className="flex-1 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
                  placeholder="Root cause (required to resolve)..."
                  value={resolveNote}
                  onChange={e => setResolveNote(e.target.value)}
                />
                <button
                  onClick={() => handleResolve(selected)}
                  className="px-3 py-1.5 rounded-lg bg-green-500/30 border border-green-500/50 text-green-300 text-sm hover:bg-green-500/40 transition-colors"
                >
                  Resolve
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
