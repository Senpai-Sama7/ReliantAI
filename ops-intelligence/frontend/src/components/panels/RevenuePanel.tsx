import { useEffect, useState, useCallback } from 'react'
import { DollarSign, TrendingUp, Users, Plus, RefreshCw } from 'lucide-react'
import axios from 'axios'
import MetricCard from '../shared/MetricCard'
import StatusBadge from '../shared/StatusBadge'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, FunnelChart, Funnel, LabelList, Cell,
} from 'recharts'

const api = axios.create({ baseURL: '/api/revenue' })

interface FunnelData {
  funnel: Record<string, { count: number; value: number }>
  pipeline_value: number
  total_leads: number
}

interface RevSummary {
  total_revenue: number
  total_events: number
  by_product: Record<string, number>
  pipeline_value: number
  pricing: { hvac_per_dispatch: number; enterprise_monthly: number; dj_per_booking: number }
}

interface IncomeHealth {
  status: string
  signals: Array<{ severity: string; message: string }>
  revenue_30d: number
  revenue_7d: number
  pipeline_value: number
  overdue_invoices: number
}

interface Lead {
  id: string
  company: string
  contact_name: string
  phone: string
  city: string
  lead_score: number
  product_line: string
  deal_value: number
  stage: string
  last_contacted: string | null
}

const STAGES = ['new', 'contacted', 'interested', 'demo', 'negotiating', 'won', 'lost']
const FUNNEL_COLORS = ['#4f8ef7', '#3ecf8e', '#f59e0b', '#a78bfa', '#f97316', '#22c55e', '#ef4444']

function fmt(n: number) {
  if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`
  if (n >= 1000) return `$${(n / 1000).toFixed(1)}k`
  return `$${n.toFixed(0)}`
}

function scoreColor(score: number) {
  if (score >= 80) return 'text-red-400'
  if (score >= 60) return 'text-amber-400'
  return 'text-green-400'
}

function scorePriority(score: number) {
  if (score >= 80) return '🔴 NOW'
  if (score >= 60) return '🟡 HIGH'
  return '🟢 MED'
}

export default function RevenuePanel() {
  const [funnel, setFunnel] = useState<FunnelData | null>(null)
  const [summary, setSummary] = useState<RevSummary | null>(null)
  const [health, setHealth] = useState<IncomeHealth | null>(null)
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [showEventForm, setShowEventForm] = useState(false)
  const [eventForm, setEventForm] = useState({
    event_type: 'dispatch', product_line: 'hvac', amount: '', description: ''
  })

  const refresh = useCallback(async () => {
    const [f, s, h, l] = await Promise.all([
      api.get('/funnel'),
      api.get('/summary'),
      api.get('/health'),
      api.get('/leads?limit=20'),
    ])
    setFunnel(f.data)
    setSummary(s.data)
    setHealth(h.data)
    setLeads(l.data)
    setLoading(false)
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const advanceStage = async (lead: Lead, stage: string) => {
    await api.post(`/leads/${lead.id}/stage`, { stage })
    refresh()
  }

  const recordEvent = async () => {
    if (!eventForm.amount) return
    await api.post('/events', {
      event_type: eventForm.event_type,
      product_line: eventForm.product_line,
      amount: parseFloat(eventForm.amount),
      description: eventForm.description,
    })
    setShowEventForm(false)
    setEventForm({ event_type: 'dispatch', product_line: 'hvac', amount: '', description: '' })
    refresh()
  }

  const funnelChartData = funnel
    ? STAGES.filter(s => s !== 'lost').map((stage, i) => ({
        name: stage,
        value: funnel.funnel[stage]?.count ?? 0,
        dollarValue: funnel.funnel[stage]?.value ?? 0,
        fill: FUNNEL_COLORS[i],
      }))
    : []

  const productChartData = summary
    ? Object.entries(summary.by_product).map(([product, total]) => ({ product, total }))
    : []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <DollarSign className="text-green-400" size={22} />
          <div>
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Revenue Intelligence</h2>
            <p className="text-xs text-[var(--text-secondary)]">Autonomous e2e income — lead to cash</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={refresh} className="p-1.5 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
            <RefreshCw size={14} />
          </button>
          <button
            onClick={() => setShowEventForm(!showEventForm)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-green-500/20 border border-green-500/30 text-green-400 text-sm hover:bg-green-500/30 transition-colors"
          >
            <Plus size={14} /> Record Revenue
          </button>
        </div>
      </div>

      {/* Income health banner */}
      {health && health.status !== 'healthy' && (
        <div className={`rounded-xl border p-4 space-y-2 ${
          health.status === 'at_risk'
            ? 'border-red-500/40 bg-red-500/10'
            : 'border-amber-500/40 bg-amber-500/10'
        }`}>
          <p className={`text-sm font-medium ${health.status === 'at_risk' ? 'text-red-400' : 'text-amber-400'}`}>
            {health.status === 'at_risk' ? '🚨 Income At Risk' : '⚠️ Income Warning'}
          </p>
          {health.signals.map((s, i) => (
            <p key={i} className="text-xs text-[var(--text-secondary)]">
              {s.severity === 'HIGH' ? '🔴' : '🟡'} {s.message}
            </p>
          ))}
        </div>
      )}

      {/* KPI row */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard label="Revenue (30d)" value={fmt(summary.total_revenue)} accent="green" />
          <MetricCard label="Pipeline Value" value={fmt(summary.pipeline_value)} sub="Active deals" accent="blue" />
          <MetricCard label="Dispatch Rate" value={`$${summary.pricing.hvac_per_dispatch}/job`} accent="amber" />
          <MetricCard
            label="Income Health"
            value={health?.status === 'healthy' ? '✅ Healthy' : health?.status === 'warning' ? '⚠️ Warning' : '🚨 At Risk'}
            accent={health?.status === 'healthy' ? 'green' : 'red'}
          />
        </div>
      )}

      {/* Record revenue event */}
      {showEventForm && (
        <div className="rounded-xl border border-green-500/30 bg-green-500/10 p-4 space-y-3">
          <p className="text-sm font-medium text-green-400">Record Revenue Event</p>
          <div className="grid grid-cols-2 gap-3">
            <select className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              value={eventForm.event_type} onChange={e => setEventForm(f => ({ ...f, event_type: e.target.value }))}>
              <option value="dispatch">Dispatch</option>
              <option value="subscription">Subscription</option>
              <option value="booking">Booking</option>
              <option value="renewal">Renewal</option>
              <option value="payment">Payment</option>
            </select>
            <select className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              value={eventForm.product_line} onChange={e => setEventForm(f => ({ ...f, product_line: e.target.value }))}>
              <option value="hvac">HVAC</option>
              <option value="enterprise">Enterprise</option>
              <option value="dj">DJ</option>
              <option value="other">Other</option>
            </select>
            <input type="number" className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)]"
              placeholder="Amount ($)" value={eventForm.amount} onChange={e => setEventForm(f => ({ ...f, amount: e.target.value }))} />
            <input className="rounded-lg bg-[var(--bg-card)] border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
              placeholder="Description" value={eventForm.description} onChange={e => setEventForm(f => ({ ...f, description: e.target.value }))} />
          </div>
          <div className="flex gap-2">
            <button onClick={recordEvent} className="px-4 py-1.5 rounded-lg bg-green-500/30 border border-green-500/50 text-green-300 text-sm hover:bg-green-500/40 transition-colors">Record</button>
            <button onClick={() => setShowEventForm(false)} className="px-4 py-1.5 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] text-sm">Cancel</button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Lead funnel */}
        {funnelChartData.length > 0 && (
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
            <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wide mb-3">
              Lead Funnel — {funnel?.total_leads} total
            </p>
            <div className="space-y-1.5">
              {funnelChartData.map(stage => (
                <div key={stage.name} className="flex items-center gap-3">
                  <span className="text-xs text-[var(--text-secondary)] w-20 shrink-0">{stage.name}</span>
                  <div className="flex-1 bg-[var(--bg-base)] rounded h-5 overflow-hidden">
                    <div
                      className="h-full rounded transition-all"
                      style={{
                        width: `${funnel ? Math.max(4, (stage.value / Math.max(1, funnel.total_leads)) * 100) : 0}%`,
                        background: stage.fill,
                        opacity: 0.8,
                      }}
                    />
                  </div>
                  <span className="text-xs text-[var(--text-secondary)] w-8 text-right">{stage.value}</span>
                  {stage.dollarValue > 0 && (
                    <span className="text-xs text-green-400 w-16 text-right">{fmt(stage.dollarValue)}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Revenue by product */}
        {productChartData.length > 0 && (
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
            <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wide mb-3">Revenue by Product (30d)</p>
            <ResponsiveContainer width="100%" height={140}>
              <BarChart data={productChartData} barSize={40}>
                <XAxis dataKey="product" tick={{ fill: '#8b8fa8', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8b8fa8', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}`} />
                <Tooltip
                  contentStyle={{ background: '#22263a', border: '1px solid #2e3347', borderRadius: 8, color: '#e8eaf0' }}
                  formatter={(v: number) => [`$${v.toFixed(2)}`, 'Revenue']}
                />
                <Bar dataKey="total" fill="#3ecf8e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Top leads by score */}
      {!loading && leads.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wide flex items-center gap-2">
              <Users size={12} /> Top Leads by Score
            </p>
            <p className="text-xs text-[var(--text-secondary)]">
              Run <code className="text-blue-400">python tools/lead_pipeline.py</code> to import new leads
            </p>
          </div>
          {leads.map(lead => (
            <div key={lead.id} className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-3 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-xs font-mono shrink-0">{scorePriority(lead.lead_score)}</span>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-[var(--text-primary)] truncate">{lead.company}</p>
                  <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
                    {lead.city && <span>{lead.city}</span>}
                    {lead.phone && <span>{lead.phone}</span>}
                    <StatusBadge value={lead.product_line} />
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className={`text-sm font-bold ${scoreColor(lead.lead_score)}`}>{lead.lead_score.toFixed(0)}</span>
                <span className="text-xs text-green-400">{fmt(lead.deal_value)}/yr</span>
                <StatusBadge value={lead.stage} />
                {lead.stage === 'new' && (
                  <button
                    onClick={() => advanceStage(lead, 'contacted')}
                    className="text-xs px-2 py-0.5 rounded border border-blue-500/30 text-blue-400 hover:bg-blue-500/20 transition-colors whitespace-nowrap"
                  >
                    Mark contacted
                  </button>
                )}
                {lead.stage === 'contacted' && (
                  <button
                    onClick={() => advanceStage(lead, 'interested')}
                    className="text-xs px-2 py-0.5 rounded border border-green-500/30 text-green-400 hover:bg-green-500/20 transition-colors whitespace-nowrap"
                  >
                    Interested →
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && leads.length === 0 && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-8 text-center space-y-3">
          <p className="text-[var(--text-secondary)]">No leads imported yet.</p>
          <div className="text-sm text-[var(--text-secondary)] font-mono bg-[var(--bg-base)] rounded p-3 text-left">
            <p className="text-blue-400 mb-1"># Import Lindy AI leads:</p>
            <p>cd ops-intelligence</p>
            <p>python tools/lead_pipeline.py --dry-run   # preview</p>
            <p>python tools/lead_pipeline.py             # import</p>
          </div>
        </div>
      )}
    </div>
  )
}
