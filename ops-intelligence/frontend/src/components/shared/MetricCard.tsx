import { ReactNode } from 'react'

interface Props {
  label: string
  value: string | number
  sub?: string
  icon?: ReactNode
  accent?: 'blue' | 'green' | 'amber' | 'red' | 'purple'
}

const ACCENT_MAP = {
  blue: 'text-blue-400',
  green: 'text-green-400',
  amber: 'text-amber-400',
  red: 'text-red-400',
  purple: 'text-purple-400',
}

export default function MetricCard({ label, value, sub, icon, accent = 'blue' }: Props) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-4 flex flex-col gap-1">
      <div className="flex items-center gap-2 text-[var(--text-secondary)] text-xs uppercase tracking-wide">
        {icon && <span className={ACCENT_MAP[accent]}>{icon}</span>}
        {label}
      </div>
      <div className={`text-2xl font-bold ${ACCENT_MAP[accent]}`}>{value}</div>
      {sub && <div className="text-xs text-[var(--text-secondary)]">{sub}</div>}
    </div>
  )
}
