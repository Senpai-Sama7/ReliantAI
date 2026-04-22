interface Props {
  value: string
  size?: 'sm' | 'md'
}

const COLORS: Record<string, string> = {
  // incident phases / statuses
  active: 'bg-red-500/20 text-red-400 border border-red-500/30',
  resolved: 'bg-green-500/20 text-green-400 border border-green-500/30',
  triage: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
  evidence: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
  containment: 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
  investigation: 'bg-purple-500/20 text-purple-400 border border-purple-500/30',
  mitigation: 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30',
  stabilization: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
  // severity
  'SEV-1': 'bg-red-600/30 text-red-300 border border-red-600/40 font-bold',
  'SEV-2': 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
  'SEV-3': 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
  'SEV-4': 'bg-gray-500/20 text-gray-400 border border-gray-500/30',
  // pipeline
  healthy: 'bg-green-500/20 text-green-400 border border-green-500/30',
  degraded: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
  failed: 'bg-red-500/20 text-red-400 border border-red-500/30',
  unknown: 'bg-gray-500/20 text-gray-400 border border-gray-500/30',
  // risk
  low: 'bg-green-500/20 text-green-400 border border-green-500/30',
  medium: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
  high: 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
  critical: 'bg-red-600/30 text-red-300 border border-red-600/40',
  // debt status / perf status
  open: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
  in_progress: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
  // api governance
  green: 'bg-green-500/20 text-green-400 border border-green-500/30',
  yellow: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
  red: 'bg-red-500/20 text-red-400 border border-red-500/30',
  completed: 'bg-green-500/20 text-green-400 border border-green-500/30',
}

export default function StatusBadge({ value, size = 'sm' }: Props) {
  const cls = COLORS[value] ?? 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
  const padding = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm'
  return (
    <span className={`inline-flex items-center rounded-full font-medium ${padding} ${cls}`}>
      {value.replace('_', ' ')}
    </span>
  )
}
