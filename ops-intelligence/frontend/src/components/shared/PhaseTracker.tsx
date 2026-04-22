interface Props {
  phases: string[]
  currentPhase: string
}

export default function PhaseTracker({ phases, currentPhase }: Props) {
  const current = phases.indexOf(currentPhase)
  return (
    <div className="flex items-center gap-1 flex-wrap">
      {phases.map((phase, i) => {
        const done = i < current
        const active = i === current
        return (
          <div key={phase} className="flex items-center gap-1">
            <div
              className={`px-2 py-0.5 rounded text-xs font-medium ${
                active
                  ? 'bg-blue-500/30 text-blue-300 border border-blue-500/50'
                  : done
                  ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                  : 'bg-[var(--bg-card)] text-[var(--text-secondary)] border border-[var(--border)]'
              }`}
            >
              {done && <span className="mr-1">✓</span>}
              {phase}
            </div>
            {i < phases.length - 1 && (
              <span className="text-[var(--border)] text-xs">→</span>
            )}
          </div>
        )
      })}
    </div>
  )
}
